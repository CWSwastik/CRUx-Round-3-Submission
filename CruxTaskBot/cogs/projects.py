import discord
from discord.ext import commands
from discord import app_commands
from utils.models import Project, Task


class Projects(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="create_project",
        description="Create a project!",
    )
    @app_commands.describe(
        title="Project title",
        role="The role that will be pinged for this project",
        channel="The channel that will be used for this project",
        github_url="The github url for this project",
        description="The description for this project",
    )
    async def create_project(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        role: discord.Role,
        channel: discord.TextChannel,
        github_url: str,
    ):
        project = Project(
            title=title,
            role=role.id,
            channel=channel.id,
            github_url=github_url,
            description=description,
        )
        await self.bot.db.create_project(project)
        await interaction.response.send_message("Project created.")

    @app_commands.command(
        name="view_projects",
        description="View all projects!",
    )
    async def view_projects(self, interaction: discord.Interaction):
        projects = await self.bot.db.list_all_projects()
        projects = [p.title for p in projects]
        await interaction.response.send_message(
            "Active projects:" + ", ".join(projects)
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Projects(bot))
