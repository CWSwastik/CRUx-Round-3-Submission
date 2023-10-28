from discord.ext import commands
from utils.models import Task, User

import asyncio
import datetime
from email.message import EmailMessage
import aiosmtplib


class Reminders(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.smtp_client = aiosmtplib.SMTP(
            hostname=self.bot.config.smtp_host,
            port=self.bot.config.smtp_port,
            username=self.bot.config.email_id,
            password=self.bot.config.email_password,
        )

    async def send_mail(self, to_email: str, subject: str, content: str):
        message = EmailMessage()
        message["From"] = self.bot.config.email_id
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(content)

        await self.smtp_client.send_message(message)

    def construct_email_message(self, task: Task, user: User) -> str:
        time_until_deadline = task.deadline - datetime.datetime.now()
        deadline_message = ""
        if time_until_deadline.days > 0:
            deadline_message += f"{time_until_deadline.days} day(s) "

        hours, remainder = divmod(time_until_deadline.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        deadline_message += f"{hours} hour(s) {minutes} minute(s)"

        message = (
            f"Hi {user.name},\n\n"
            f"This is a reminder to let you know that you have a task with the following details:\n"
            f"Title: {task.title}\n"
            f"Description: {task.description}\n"
            f"Deadline: {task.deadline}\n"
            f"Time left until the deadline: {deadline_message}\n\n"
            f"Please make sure to complete the task on time. If you have any questions or need assistance, "
            f"feel free to reach out.\n\n"
            f"Best regards,\n"
            f"Crux Task Bot"
        )
        return message

    async def post_email_reminders(self):
        for project in await self.bot.db.list_all_projects():
            for task in await self.bot.db.list_project_tasks(project.id):
                if (
                    task.reminder is not None
                    and datetime.timedelta(seconds=0)
                    < task.deadline - datetime.datetime.now()
                    < datetime.timedelta(seconds=task.reminder)
                    and task.status != "Completed"
                ):
                    user = await self.bot.db.fetch_user(task.assignee)
                    if not user:  # user didn't set email
                        continue

                    subject = "Crux Task Deadline Reminder"
                    message = self.construct_email_message(task, user)

                    await self.send_mail(user.email, subject, message)
                    await self.bot.db.set_task_reminder(task.id, None)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.smtp_client.connect()
        await asyncio.sleep(5)  # Wait for database to be ready
        while True:
            await self.post_email_reminders()
            await asyncio.sleep(60 * 60)  # Check every hour


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Reminders(bot))
