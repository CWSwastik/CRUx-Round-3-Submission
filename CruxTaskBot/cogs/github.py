import base64
import discord
from io import StringIO
from discord.ext import commands
from discord import app_commands
from utils.models import Project, Task
from typing import List, Optional
from urllib.parse import urlparse
from utils import generate_documentation, extract_github_file_content
from utils.github import GithubAPIError, GithubRequestsManager


# TODO: Permissions check
class Github(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.gh = GithubRequestsManager(
            self.bot.config.github_app_id,
            self.bot.config.github_private_key,
            self.bot.config.github_installation_id,
            self.bot.session,
        )

    # TODO: Imporve display of activity
    @app_commands.command(
        name="github_activity",
        description="View recent GitHub activity for a user!",
    )
    @app_commands.describe(
        github_username="The GitHub username to view activity for",
        member="The user to view activity for",
    )
    async def github_activity(
        self,
        interaction: discord.Interaction,
        github_username: Optional[str],
        member: Optional[discord.Member],
    ):
        if github_username is not None:
            pass
        elif member is not None:
            user = await self.bot.db.fetch_user(member.id)
            if user:
                github_username = user.github
            else:
                await interaction.response.send_message(
                    f"{member.mention} has not set their GitHub username yet. Please use `/github_activity <their_github_username>` to view activity for this user.",
                    ephemeral=True,
                )
                return
        else:
            user = await self.bot.db.fetch_user(interaction.user.id)
            if user:
                github_username = user.github
            else:
                await interaction.response.send_message(
                    f"You have not set your GitHub username yet. Please use `/github_activity <your_github_username>` to view your activity.",
                    ephemeral=True,
                )
                return

        endpoint = f"/users/{github_username}/events"
        data = await self.gh.get(endpoint)
        if data:
            activity = [
                event
                for event in data
                if event["type"] in ["PullRequestEvent", "IssuesEvent", "PushEvent"]
            ]
            if activity:
                activity_message = (
                    "Recent GitHub Activity for " + github_username + ":\n\n"
                )
                for event in activity:
                    event_type = event["type"]
                    repo_name = event["repo"]["name"]
                    created_at = event["created_at"]
                    activity_message += f"Type: {event_type}\nRepository: {repo_name}\nCreated At: {created_at}\n\n"
                await interaction.response.send_message(activity_message)
            else:
                await interaction.response.send_message(
                    f"No recent GitHub activity found for `{github_username}`."
                )
        else:
            await interaction.response.send_message(
                f"No data found for `{github_username}`."
            )

    # TODO: Check if it works for organizations
    @app_commands.command(
        name="generate-docs",
        description="Create documentation for a GitHub repository file!",
    )
    @app_commands.describe(
        github_file_url="The GitHub URL to create documentation for",
        automatically_push_to_github="Whether to automatically push the generated documentation to the bot docs branch of the github repo",
    )
    async def generate_docs(
        self,
        interaction: discord.Interaction,
        github_file_url: str,
        automatically_push_to_github: bool = True,
    ):
        if not github_file_url.startswith(
            "https://raw.githubusercontent.com"
        ) and github_file_url.startswith("https://github.com"):
            github_file_url = github_file_url.replace(
                "https://github.com", "https://raw.githubusercontent.com"
            ).replace("/blob/", "/")
        else:
            await interaction.response.send_message(
                "Invalid GitHub URL. Please use a URL that points to a raw file on GitHub."
            )
            return

        file_content = await extract_github_file_content(
            self.gh.session, github_file_url
        )
        if file_content is not None:
            await interaction.response.defer()
            generated_documentation = await generate_documentation(file_content)
            markdown_file_content = (
                f"# Documentation for {github_file_url}\n\n{generated_documentation}"
            )

            await interaction.followup.send(
                file=discord.File(
                    StringIO(markdown_file_content), filename="documentation.md"
                )
            )
        else:
            return await interaction.response.send_message(
                "Failed to fetch GitHub file content."
            )

        if automatically_push_to_github:
            # check if file is a project repo
            projects = await self.bot.db.list_all_projects()
            repo_parts = urlparse(github_file_url).path.split("/")
            repository_name = "/".join(repo_parts[1:3])

            # convert name of code file to markdown file (main.py/js/any ext -> main_docs.md)
            fname = repo_parts[-1].partition(".")[0]
            fname = fname + "_docs.md"
            repo_parts[-1] = fname
            fp = "/".join(repo_parts[4:])

            project = [p for p in projects if repository_name in p.github_url]
            if project:
                project = project[0]
                await self.create_branch(project, "bot-docs")
                res = await self.add_file_to_branch(
                    project, "bot-docs", fp, markdown_file_content
                )
                await interaction.followup.send(
                    f"Documentation pushed to [bot-docs]({res[-1]['content']['html_url']}) branch!"
                )

    async def create_branch(self, project: Project, branch_name: str):
        repository_path = urlparse(project.github_url).path
        endpoint = f"/repos{repository_path}/branches"

        data = await self.gh.get(endpoint)

        if not data:
            return False, "No branches found!"

        branches = [branch["name"] for branch in data]
        if branch_name in branches:
            return True, "Branch already exists!"

        endpoint = f"/repos{repository_path}/git/refs"
        response = await self.gh.post(
            endpoint,
            data={
                "ref": f"refs/heads/{branch_name}",
                "sha": data[0]["commit"]["sha"],
            },
        )

        return True, "Branch created!", response

    # TODO: Test if it works in directories
    async def add_file_to_branch(
        self, project: Project, branch_name: str, file_path: str, content: str
    ):
        """
        This function adds a file to a branch in a GitHub repository. If it already exists it will be overwritten.
        """

        repository_path = urlparse(project.github_url).path
        endpoint = f"/repos{repository_path}/contents/{file_path}"
        content = base64.b64encode(content.encode()).decode()
        try:
            data = await self.gh.get(endpoint, params={"ref": branch_name})
            sha = data["sha"]

            response = await self.gh.put(
                endpoint,
                data={
                    "message": f"Update {file_path}",
                    "content": content,
                    "sha": sha,
                    "branch": branch_name,
                },
            )

            return True, "File updated!", response
        except GithubAPIError as e:
            if e.response_status_code != 404:
                raise e

            endpoint = f"/repos{repository_path}/contents/{file_path}"
            response = await self.gh.put(
                endpoint,
                data={
                    "message": f"Create {file_path}",
                    "content": content,
                    "branch": branch_name,
                },
            )

            return True, "File created!", response

    async def project_autocomplete(
        self, interaction: discord.Interaction, current: str
    ):
        projects = await self.bot.db.list_all_projects()
        return [
            app_commands.Choice(
                name=project.title,
                value=project.title,
            )
            for project in projects
            if current in project.title
        ]

    @app_commands.command(
        name="track_project",
        description="Track a GitHub repository!",
    )
    @app_commands.describe(project="The Project to setup tracking for")
    @app_commands.autocomplete(
        project=project_autocomplete,
    )
    @app_commands.checks.has_role("Senate")
    async def track_project(
        self,
        interaction: discord.Interaction,
        project: str,
    ):
        """
        This command sets up tracking the GitHub repository of a project.
        """

        projects = await self.bot.db.list_all_projects()
        matching_projects = [p for p in projects if p.title == project]
        if matching_projects:
            project = matching_projects[0]
            await interaction.response.defer()
            res = await self.setup_webhook_for_project(project)
            if res[0]:
                await interaction.followup.send(
                    f"Tracking setup for {project.title} with id={res[1]}!"
                )
            else:
                await interaction.followup.send(
                    f"Failed to setup tracking for {project.title}, response={res[1]} {res[2]}!"
                )
        else:
            await interaction.response.send_message(
                f"Project with title {project} not found!"
            )

    async def setup_webhook_for_project(self, project: Project):
        repository_path = urlparse(project.github_url).path
        endpoint = f"/repos{repository_path}/hooks"

        data = await self.gh.post(
            endpoint=endpoint,
            data={
                "name": "web",
                "active": True,
                "events": ["issues", "pull_request", "push", "ping"],
                "config": {
                    "url": self.bot.config.webserver_url + "/webhook",
                    "content_type": "json",
                },
            },
        )

        webhook_id = data["id"]
        # TODO: Store this in database
        return True, webhook_id


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Github(bot))
