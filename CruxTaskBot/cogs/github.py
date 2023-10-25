import asyncio
import aiohttp
import discord
from io import StringIO
from discord.ext import commands
from discord import app_commands
from utils.models import Project, Task
from typing import List, Optional
from utils import generate_documentation, extract_github_file_content


class Github(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

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

        github_api_url = f"https://api.github.com/users/{github_username}/events"

        async with aiohttp.ClientSession() as session:
            async with session.get(github_api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        # Filter and display pull requests and issues events
                        activity = [
                            event
                            for event in data
                            if event["type"] in ["PullRequestEvent", "IssuesEvent"]
                        ]
                        if activity:
                            activity_message = (
                                "Recent GitHub Activity for "
                                + github_username
                                + ":\n\n"
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
                else:
                    await interaction.response.send_message(
                        f"Failed to fetch data from GitHub API (Status code: {response.status})."
                    )

    # create a command that takes a github repo file url and creates documentation for that file using open ai and sends it as a .MD file
    @app_commands.command(
        name="generate-docs",
        description="Create documentation for a GitHub repository file!",
    )
    @app_commands.describe(
        github_file_url="The GitHub URL to create documentation for",
    )
    async def generate_docs(
        self,
        interaction: discord.Interaction,
        github_file_url: str,
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

        async with aiohttp.ClientSession() as session:
            file_content = await extract_github_file_content(session, github_file_url)
            if file_content is not None:
                await interaction.response.defer()
                generated_documentation = await generate_documentation(file_content)
                markdown_file_content = f"# Documentation for {github_file_url}\n\n{generated_documentation}"

                await interaction.followup.send(
                    file=discord.File(
                        StringIO(markdown_file_content), filename="documentation.md"
                    )
                )
            else:
                await interaction.response.send_message(
                    "Failed to fetch GitHub file content."
                )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Github(bot))
