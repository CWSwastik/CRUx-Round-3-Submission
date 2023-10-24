import discord
from discord import app_commands
from discord.ext import commands
from utils.models import User
from typing import Optional

import asyncio
import datetime
from email.message import EmailMessage
import aiosmtplib


# create a Reminders cog that sends reminders to users


class Reminders(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def send_mail(self, to_email: str, subject: str, content: str):
        message = EmailMessage()
        message["From"] = self.bot.config.email_id
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(content)

        await aiosmtplib.send(
            message,
            username=self.bot.config.email_id,
            password=self.bot.config.email_password,
            hostname=self.bot.config.smtp_host,
            port=self.bot.config.smtp_port,
        )

    # run a background task that checks for reminders every hour
    # if a task deadline is in 2 days, send a reminder to the user
    # TODO: FIX THIS!!!!
    @commands.Cog.listener()
    async def on_ready(self):
        while True:
            for project in await self.bot.db.list_all_projects():
                for task in await self.bot.db.list_project_tasks(project.id):
                    if (
                        datetime.timedelta(days=1)
                        < task.deadline - datetime.datetime.now()
                        < datetime.timedelta(days=2)
                    ):
                        user = await self.bot.db.fetch_user(task.assignee)
                        if user:
                            await self.send_mail(
                                user.email,
                                "Deadline Reminder",
                                f"You have a task {task.title} due in {task.deadline - datetime.datetime.now()}",
                            )
                            print(f"EMAIL SENT TO {user.email}")

            await asyncio.sleep(60 * 60)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Reminders(bot))
