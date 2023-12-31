import discord
import datetime
from io import StringIO
from discord.ext import commands
from discord import app_commands
from utils.models import Project
from typing import List, Optional
from urllib.parse import urlparse
from utils.views import Paginator
from utils import generate_documentation, extract_github_file_content


class Github(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="github-activity",
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
        data = await self.bot.gh.get(endpoint)
        if data:
            activity = [
                event
                for event in data
                if event["type"] in ["PullRequestEvent", "IssuesEvent", "PushEvent"]
            ]

            if activity:
                embeds = []

                for event in activity:
                    emb = discord.Embed(
                        title="Recent GitHub Activity for " + github_username,
                        color=discord.Color.random(),
                    )
                    event_type = event["type"]
                    repo_name = event["repo"]["name"]
                    created_at = datetime.datetime.fromisoformat(event["created_at"])
                    emb.description = f"**Event Type:** {event_type}\n"
                    emb.add_field(
                        name="Repository",
                        value=f"[{repo_name}](https://github.com/{repo_name})",
                        inline=False,
                    )
                    emb.add_field(
                        name="Created",
                        value=f"<t:{created_at.timestamp():.0f}:R>",
                        inline=False,
                    )

                    if event_type == "PullRequestEvent":
                        pull_request_title = event["payload"]["pull_request"]["title"]
                        pull_request_action = event["payload"]["action"]
                        emb.add_field(
                            name="Pull Request",
                            value=f"{pull_request_action} - {pull_request_title}",
                            inline=False,
                        )

                    if event_type == "IssuesEvent":
                        issue_title = event["payload"]["issue"]["title"]
                        issue_action = event["payload"]["action"]
                        emb.add_field(
                            name="Issue",
                            value=f"{issue_action} - {issue_title}",
                            inline=False,
                        )

                    if event_type == "PushEvent":
                        commits = event["payload"]["commits"]
                        if commits:
                            commit_messages = "\n".join(
                                [commit["message"] for commit in commits]
                            )
                            emb.add_field(
                                name="Commits", value=commit_messages, inline=False
                            )

                    embeds.append(emb)

                embeds[0].set_footer(text=f"Page 1 of {len(embeds)}")
                await interaction.response.send_message(
                    embed=embeds[0], view=Paginator(interaction, embeds)
                )
            else:
                await interaction.response.send_message(
                    f"No recent GitHub activity found for `{github_username}`."
                )
        else:
            await interaction.response.send_message(
                f"No data found for `{github_username}`."
            )

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
            self.bot.gh.session, github_file_url
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
                await self.bot.gh.create_branch(project.github_url, "bot-docs")
                res = await self.bot.gh.add_file_to_branch(
                    project.github_url, "bot-docs", fp, markdown_file_content
                )
                await interaction.followup.send(
                    f"Documentation pushed to [bot-docs]({res[-1]['content']['html_url']}) branch!"
                )

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
            if current.lower() in project.title.lower()
        ]

    @app_commands.command(
        name="track-project-github",
        description="Track a project's GitHub repository!",
    )
    @app_commands.describe(project="The Project to setup tracking for")
    @app_commands.autocomplete(
        project=project_autocomplete,
    )
    @app_commands.checks.has_role("Senate")
    async def track_project_github(
        self,
        interaction: discord.Interaction,
        project: str,
    ):
        """
        This command sets up tracking the GitHub repository of a project.
        """

        projects = await self.bot.db.list_all_projects()
        matching_projects = [p for p in projects if p.title == project]
        if not matching_projects:
            return await interaction.response.send_message(
                f"Project with title {project} not found!"
            )

        project = matching_projects[0]
        await interaction.response.defer()

        if project.webhook_id is not None:
            return await interaction.followup.send(
                f"Tracking already setup for {project.title} with id={project.webhook_id}!"
            )

        res = await self.setup_webhook_for_project(project)
        if res[0]:
            await interaction.followup.send(
                f"Tracking setup for {project.title} with id={res[1]}!"
            )
        else:
            await interaction.followup.send(
                f"Failed to setup tracking for {project.title}, response={res[1]} {res[2]}!"
            )

    async def setup_webhook_for_project(self, project: Project):
        repository_path = urlparse(project.github_url).path
        endpoint = f"/repos{repository_path}/hooks"

        data = await self.bot.gh.post(
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
        await self.bot.db.set_project_webhook_id(project.id, webhook_id)
        return True, webhook_id


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Github(bot))
