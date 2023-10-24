import discord
from discord import app_commands
from discord.ext import commands
from utils.models import User
from typing import Optional

import asyncio
import datetime
from email.message import EmailMessage
import aiosmtplib


class Reminders(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # TODO: Change this to use only 1 session
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

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(5)  # Wait for database to be ready
        while True:
            for project in await self.bot.db.list_all_projects():
                for task in await self.bot.db.list_project_tasks(project.id):
                    if task.reminder is not None and datetime.timedelta(
                        seconds=0
                    ) < task.deadline - datetime.datetime.now() < datetime.timedelta(
                        seconds=task.reminder
                    ):
                        user = await self.bot.db.fetch_user(task.assignee)
                        if user:
                            # TODO: send better email
                            await self.send_mail(
                                user.email,
                                "Deadline Reminder",
                                f"You have a task {task.title} due in {task.deadline - datetime.datetime.now()}",
                            )

                            await self.bot.db.set_task_reminder(task.id, None)

            await asyncio.sleep(60 * 60)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Reminders(bot))
