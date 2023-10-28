import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

import os
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_credentials():
    """
    Gets valid user credentials from token.json if it exists, otherwise prompts the user to log in.

    Args:
        None
    Returns:
        google.oauth2.credentials.Credentials: Google Calendar API credentials
    """

    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds


def create_event(
    credentials: Credentials, summary: str, description: str, start: str, end: str
) -> str:
    """
    Creates an event in the user's Google Calendar.

    Args:
        credentials (google.oauth2.credentials.Credentials): Google Calendar API credentials
        summary (str): The title of the event
        description (str): The description of the event
        start (str): The start time of the event
        end (str): The end time of the event

    Returns:
        str: The link to the event
    """
    service = build("calendar", "v3", credentials=credentials)

    event_details = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start, "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end, "timeZone": "Asia/Kolkata"},
    }

    event = service.events().insert(calendarId="primary", body=event_details).execute()
    return event.get("htmlLink")


class GoogleCalendar(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.creds = get_credentials()

    async def task_autocomplete(self, interaction: discord.Interaction, current: str):
        """
        Autocomplete for the task argument of the add_to_calendar command.
        Lets users select a task from the list of their tasks.

        Args:
            interaction (discord.Interaction): The interaction object
            current (str): The current input

        Returns:
            List[app_commands.Choice]: The list of choices
        """

        tasks = await self.bot.db.list_user_tasks(interaction.user.id)
        projects = await self.bot.db.list_all_projects()

        choices = []
        for task in tasks:
            if current.lower() in task.title.lower():
                project = [p for p in projects if p.id == task.project_id][0]
                formatted_task_title = project.title + " - " + task.title
                task_value = f"{task.project_id}:{task.id}"
                choices.append(
                    app_commands.Choice(name=formatted_task_title, value=task_value)
                )

        return choices

    @app_commands.command(
        name="add-to-calendar",
        description="Add a task to your calendar!",
    )
    @app_commands.describe(
        task="The task to add to your calendar",
    )
    @app_commands.autocomplete(
        task=task_autocomplete,
    )
    async def add_to_calendar(self, interaction: discord.Interaction, task: str):
        """
        This command allows users to add a task to their google calendar.
        """

        tasks = await self.bot.db.list_user_tasks(interaction.user.id)

        if task not in [f"{t.project_id}:{t.id}" for t in tasks]:
            await interaction.response.send_message(
                f"You don't have a task with the title {task}!", ephemeral=True
            )
            return

        task = [t for t in tasks if f"{t.project_id}:{t.id}" == task][0]

        await interaction.response.defer()  # Defer the response to avoid timeout

        start_time = task.deadline - datetime.timedelta(hours=1)
        end_time = task.deadline

        # add ist timezone to start_time and end_time
        tz_IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        start_time = start_time.replace(tzinfo=tz_IST)
        end_time = end_time.replace(tzinfo=tz_IST)

        event_link = await self.bot.run_async(
            create_event,
            self.creds,
            f"Task Deadline for {task.title}",
            task.description,
            start_time.isoformat(),
            end_time.isoformat(),
        )

        await interaction.followup.send(
            f"Task `{task.title}` added to your calendar! [Click here](<{event_link}>) to view the event.",
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GoogleCalendar(bot))
