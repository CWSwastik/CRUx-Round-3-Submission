import enum
import asyncio
import datetime
import discord
from discord.ext import commands
from discord import app_commands
from utils import is_valid_github_repo_url
from utils.models import Project, Task
from typing import List, Literal, Optional
from dateutil import parser as date_parser
from utils import parse_time_to_seconds


class Domains(enum.Enum):
    Frontend = "Frontend"
    Backend = "Backend"
    Database = "Database"
    Web = "Web"
    App = "App"
    Automation = "Automation"
    Design = "Design"
    Video = "Video"
    Audio = "Audio"
    Art = "Art"
    Other = "Other"


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
            f"Project `{title}` created. The {role.mention} role and {channel.mention} channel will be used for this project. Please run `/track-project-github` to setup github updates for this project and `/create-task` to create tasks for this project."
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
            return [app_commands.Choice(name=p.title, value=p.title) for p in projects]
        else:
            return [
                app_commands.Choice(name=p.title, value=p.title)
                for p in projects
                if p.role in [r.id for r in interaction.user.roles]
            ]

    # create task command
    @app_commands.command(
        name="create-task",
        description="Create a task under a project and domain!",
    )
    @app_commands.describe(
        title="Task title",
        description="The description for this task",
        project="The project for this task",
        domain="The domain for this task",
        deadline="The deadline for this task",
        assignee="The assignee for this task",
        reminder="How long before the deadline to send a reminder for this task",
    )
    @app_commands.autocomplete(
        project=project_autocomplete,
    )
    async def create_task(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        project: str,
        domain: Domains,
        deadline: str,
        assignee: discord.Member,
        reminder: Optional[str] = None,
    ):
        """
        This command creates a task under a given project and domain.
        """

        try:
            deadline_datetime = date_parser.parse(deadline)
        except ValueError:
            return await interaction.response.send_message(
                "Invalid 'deadline' format. Please enter a valid date and time.",
                ephemeral=True,
            )

        if reminder is not None:
            reminder = parse_time_to_seconds(reminder)
        else:
            reminder = 2 * 24 * 60 * 60  # 2 Days

        project_obj = await self.bot.db.fetch_project(project)
        if project_obj is None:
            await interaction.response.send_message(
                f"Project `{project}` not found.",
                ephemeral=True,
            )
            return

        if project_obj.role not in [
            r.id for r in interaction.user.roles
        ] and "Senate" not in [r.name for r in interaction.user.roles]:
            await interaction.response.send_message(
                f"You don't have permission to create tasks under `{project}`.",
                ephemeral=True,
            )
            return

        task = Task(
            title=title,
            description=description,
            project_id=project_obj.id,
            deadline=deadline_datetime,
            status="Assigned",
            domain=domain.value,
            assignee=assignee.id,
            reminder=reminder,
        )
        await self.bot.db.create_task(task)
        await interaction.response.send_message(
            f"Task `{title}` under `{project_obj.title}:{domain.value}` created and assigned to {assignee.mention} with deadline: <t:{deadline_datetime.timestamp():.0f}>."
        )

    async def task_autocomplete(self, interaction: discord.Interaction, current: str):
        tasks = await self.bot.db.list_user_tasks(interaction.user.id)
        projects = await self.bot.db.list_all_projects()

        choices = []
        for task in tasks:
            if current in task.title:
                project = [p for p in projects if p.id == task.project_id][0]
                formatted_task_title = project.title + " - " + task.title
                task_value = f"{task.project_id}:{task.id}"
                choices.append(
                    app_commands.Choice(name=formatted_task_title, value=task_value)
                )

        return choices

    # Update task status command
    @app_commands.command(
        name="update-task-status",
        description="Update the status of a task!",
    )
    @app_commands.describe(
        task="The task to update the status for",
        status="The new status for this task",
    )
    @app_commands.autocomplete(
        task=task_autocomplete,
    )
    async def update_task_status(
        self,
        interaction: discord.Interaction,
        task: str,
        status: Literal["Assigned", "In Progress", "Completed"],
    ):
        """
        This command updates the status of a given task.
        """

        tasks = await self.bot.db.list_user_tasks(interaction.user.id)

        if task not in [f"{t.project_id}:{t.id}" for t in tasks]:
            await interaction.response.send_message(
                f"You don't have a task with the title {task}!", ephemeral=True
            )
            return

        task = [t for t in tasks if f"{t.project_id}:{t.id}" == task][0]

        await self.bot.db.set_task_status(task.id, status)
        await interaction.response.send_message(
            f"Task `{task.title}` updated with status `{status}`."
        )

    # Displays tasks for a user command
    @app_commands.command(
        name="view-tasks",
        description="View your tasks!",
    )
    async def view_tasks(self, interaction: discord.Interaction):
        # display the users tasks in an embed with the deadline as a discord timestamp

        tasks = await self.bot.db.list_user_tasks(interaction.user.id)
        projects = await self.bot.db.list_all_projects()

        if not tasks:
            await interaction.response.send_message(
                "No tasks found for you.", ephemeral=True
            )
            return

        embed = discord.Embed(title="Your Tasks", color=discord.Color.random())
        embed.description = ""
        for task in tasks:
            project = [p for p in projects if p.id == task.project_id][0]
            embed.description += f"- {project.title} - {task.title} - <t:{task.deadline.timestamp():.0f}:R> - {task.status}\n"

        await interaction.response.send_message(embed=embed)

    # View tasks command
    @app_commands.command(
        name="view-task-sheet",
        description="View the task sheet for a project!",
    )
    @app_commands.describe(
        project="The project to view the task sheet for.",
    )
    @app_commands.autocomplete(
        project=project_autocomplete,
    )
    async def view_task_sheet(self, interaction: discord.Interaction, project: str):
        """
        This command displays the task list for a given project.
        """

        project_obj = await self.bot.db.fetch_project(project)
        if project_obj.role not in [
            r.id for r in interaction.user.roles
        ] and "Senate" not in [r.name for r in interaction.user.roles]:
            await interaction.response.send_message(
                f"You don't have permission to view tasks under `{project}`.",
                ephemeral=True,
            )
            return

        tasks = await self.bot.db.list_project_tasks(project_title=project)
        if not tasks:
            await interaction.response.send_message(
                f"No tasks found for project `{project}`.",
                ephemeral=True,
            )
            return
        final_response = f"# {project}\n" + self.create_task_sheet(tasks)
        await interaction.response.send_message(
            final_response, allowed_mentions=discord.AllowedMentions.none()
        )

    def create_task_sheet(self, tasks: List[Task]) -> str:
        """
        Create an organized task sheet for display based on provided tasks.
        """
        organized_tasks = {}

        for task in tasks:
            domain_name = task.domain
            member_name = f"<@{task.assignee}>"

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
                        f"> - {task.title} - <t:{task.deadline.timestamp():.0f}> - {task.status}"
                    )
                response_message.append("")

        final_response = "\n".join(response_message)
        return final_response or "No tasks to display for this project."

    async def send_task_list_for_every_project(self):
        """
        Send task list for every project to its channel.
        """
        projects = await self.bot.db.list_all_projects()
        for project in projects:
            tasks = await self.bot.db.list_project_tasks(project.id)
            channel = self.bot.get_channel(project.channel)
            final_response = f"# {project.title}\n" + self.create_task_sheet(tasks)
            await channel.send(
                final_response, allowed_mentions=discord.AllowedMentions.none()
            )

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
