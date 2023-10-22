import datetime
import discord
from discord.ext import commands
from discord import app_commands
from utils.models import Project, Task


# TODO: Permissions check
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

    # create task command
    @app_commands.command(
        name="create_task",
        description="Create a task!",
    )
    @app_commands.describe(
        title="Task title",
        description="The description for this task",
        project_id="The project id for this task",  # TODO: Make this a dropdown
        deadline="The deadline for this task",  # TODO: Parse this into a datetime object
        domain="The domain for this task",
        assignee="The assignee for this task",
    )
    async def create_task(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        project_id: int,
        deadline: int,
        domain: str,
        assignee: discord.Member,
    ):
        task = Task(
            title=title,
            description=description,
            project_id=project_id,
            deadline=datetime.datetime.fromtimestamp(deadline),
            status="Assigned",
            domain=domain,
            assignee=assignee.id,
        )
        await self.bot.db.create_task(task)
        await interaction.response.send_message("Task created.")

    # View tasks command
    @app_commands.command(
        name="view_tasks",
        description="View all tasks!",
    )
    @app_commands.describe(
        project_id="The project id for this task",
    )
    async def view_tasks(self, interaction: discord.Interaction, project_id: int):
        tasks = await self.bot.db.list_project_tasks(project_id)
        organized_tasks = {}

        for task in tasks:
            domain_name = task.domain
            member_name = interaction.guild.get_member(task.assignee).display_name

            if domain_name not in organized_tasks:
                organized_tasks[domain_name] = {}

            if member_name not in organized_tasks[domain_name]:
                organized_tasks[domain_name][member_name] = []

            organized_tasks[domain_name][member_name].append(task)

        response_message = []

        for domain, members in organized_tasks.items():
            response_message.append(f"{domain}")
            for member, member_tasks in members.items():
                response_message.append(f"    {member}")
                for task in member_tasks:
                    response_message.append(
                        f"        {task.id}. {task.title} - {task.deadline} - {task.status}"
                    )

        final_response = "\n".join(response_message)
        await interaction.response.send_message(final_response)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Projects(bot))
