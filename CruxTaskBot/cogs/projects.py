import asyncio
import datetime
import discord
from discord.ext import commands
from discord import app_commands
from utils import is_valid_github_repo_url
from utils.models import Project, Task
from typing import List, Optional


# TODO: Permissions check
class Projects(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="create-project",
        description="Create a new project!",
    )
    @app_commands.describe(
        title="Project title",
        description="The description for this project",
        role="The role that will be pinged for this project",
        channel="The channel that will be used for this project",
        github_url="The github repo url for this project",
    )
    @app_commands.checks.has_role("Senate")
    async def create_project(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        github_url: str,
        role: Optional[discord.Role],
        channel: Optional[discord.TextChannel],
    ):
        """
        This command allows users with the 'Senate' role to create a project.
        If the 'role' and 'channel' are not provided, this command creates them.
        The project details are stored in a database.
        """

        if not is_valid_github_repo_url(github_url):
            await interaction.response.send_message(
                "Please enter a valid GitHub repository URL.",
                ephemeral=True,
            )
            return

        if role is None:
            role = await interaction.guild.create_role(name=title)
        if channel is None:
            channel = await interaction.guild.create_text_channel(name=title)

        project = Project(
            title=title,
            role=role.id,
            channel=channel.id,
            github_url=github_url,
            description=description,
        )
        await self.bot.db.create_project(project)
        await interaction.response.send_message(
            f"Project `{title}` created. The {role.mention} role and {channel.mention} channel will be used for this project."
        )

    @app_commands.command(
        name="view-projects",
        description="View the active projects!",
    )
    async def view_projects(self, interaction: discord.Interaction):
        """
        This command allows users to view a list of active projects.
        """
        projects = await self.bot.db.list_all_projects()
        embed = discord.Embed(title="Active Projects", color=discord.Color.random())
        embed.description = ""
        for p in projects:
            embed.description += f"[{p.title}]({p.github_url}) - {p.description}\n"

        await interaction.response.send_message(embed=embed)

    async def project_autocomplete(
        self, interaction: discord.Interaction, current: str
    ):
        projects = await self.bot.db.list_all_projects()
        if "Senate" in [r.name for r in interaction.user.roles]:
            return [
                app_commands.Choice(name=p.title, value=str(p.id)) for p in projects
            ]
        else:
            return [
                app_commands.Choice(name=p.title, value=str(p.id))
                for p in projects
                if p.role in [r.id for r in interaction.user.roles]
            ]

    # create task command
    @app_commands.command(
        name="create_task",
        description="Create a task!",
    )
    @app_commands.describe(
        title="Task title",
        description="The description for this task",
        project="The project for this task",
        deadline="The deadline for this task",  # TODO: Parse this into a datetime object
        domain="The domain for this task",
        assignee="The assignee for this task",
    )
    @app_commands.autocomplete(
        project=project_autocomplete,
    )
    async def create_task(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        project: int,
        deadline: int,
        domain: str,
        assignee: discord.Member,
    ):
        task = Task(
            title=title,
            description=description,
            project_id=project,
            deadline=datetime.datetime.fromtimestamp(deadline),
            status="Assigned",
            domain=domain,
            assignee=assignee.id,
        )
        await self.bot.db.create_task(task)
        await interaction.response.send_message("Task created.")

    # View tasks command
    # TODO: Beautify this
    @app_commands.command(
        name="view_tasks",
        description="View all tasks!",
    )
    @app_commands.describe(
        project="The project to view all tasks for.",
    )
    @app_commands.autocomplete(
        project=project_autocomplete,
    )
    async def view_tasks(self, interaction: discord.Interaction, project: int):
        tasks = await self.bot.db.list_project_tasks(project)
        final_response = self.create_task_list(tasks, interaction.guild)
        await interaction.response.send_message(final_response)

    def create_task_list(self, tasks: List[Task], guild: discord.Guild) -> str:
        organized_tasks = {}

        for task in tasks:
            domain_name = task.domain
            member_name = guild.get_member(task.assignee).display_name

            if domain_name not in organized_tasks:
                organized_tasks[domain_name] = {}

            if member_name not in organized_tasks[domain_name]:
                organized_tasks[domain_name][member_name] = []

            organized_tasks[domain_name][member_name].append(task)

        response_message = []

        for domain, members in organized_tasks.items():
            response_message.append(f"## __{domain}__")
            for member, member_tasks in members.items():
                response_message.append(f"> **{member}**")
                for task in member_tasks:
                    response_message.append(
                        f"> - {task.title} - {task.deadline} - {task.status}"
                    )
                response_message.append("")

        final_response = "\n".join(response_message)
        return final_response

    # Send task list for every project to its channel
    async def send_task_list_for_every_project(self):
        projects = await self.bot.db.list_all_projects()
        for project in projects:
            tasks = await self.bot.db.list_project_tasks(project.id)
            channel = self.bot.get_channel(project.channel)
            final_response = self.create_task_list(tasks, channel.guild)
            await channel.send(final_response)

    # On ready, check how long it is from midnight and sleep until then
    # when its midnight ruun the send_task_list_for_every_project function
    # and then sleep until midnight again
    @commands.Cog.listener()
    async def on_ready(self):
        now = datetime.datetime.now()
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if now > midnight:
            midnight += datetime.timedelta(days=1)

        time_to_sleep = (midnight - now).total_seconds()
        await asyncio.sleep(time_to_sleep)

        while True:
            await self.send_task_list_for_every_project()
            await asyncio.sleep(86400)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Projects(bot))
