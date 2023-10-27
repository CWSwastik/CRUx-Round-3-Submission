import os
import time

import openai
import discord
import aiohttp
from discord import Intents, app_commands
from discord.ext import commands

import platform
from colorama import Back, Style, Fore

from utils import Database
from utils.github import GithubAPIError, GithubRequestsManager

try:
    import dotenv
except ImportError:
    pass
else:
    dotenv.load_dotenv(".env")


class Config:
    def __init__(self):
        self.bot_token = os.environ["DISCORD_TOKEN"]
        self.bot_prefix = os.environ.get("PREFIX", ["t!"])

        self.email_id = os.environ["EMAIL_ID"]
        self.email_password = os.environ["EMAIL_PASSWORD"]

        self.smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = os.environ.get("SMTP_PORT", 587)

        self.openai_api_key = os.environ["OPENAI_API_KEY"]

        self.webserver_url = os.environ["WEBSERVER_URL"]
        self.github_token = os.environ["GITHUB_TOKEN"]
        self.github_app_id = os.environ["GITHUB_APP_ID"]
        self.github_installation_id = os.environ["GITHUB_INSTALLATION_ID"]

        with open("github_private_key.pem", "r") as f:
            self.github_private_key = f.read()

        openai.api_key = self.openai_api_key


class CruxTaskBot(commands.Bot):
    def __init__(self):
        self.config = Config()
        self.db = Database()
        self.gh = GithubRequestsManager(
            self.bot.config.github_app_id,
            self.bot.config.github_private_key,
            self.bot.config.github_installation_id,
            self.bot.session,
        )

        intents = Intents.default()
        intents.members = True
        intents.message_content = True

        super().__init__(
            command_prefix=self.config.bot_prefix,
            intents=intents,
            case_insensitive=True,
            allowed_mentions=discord.AllowedMentions(
                everyone=False, users=True, roles=False
            ),
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="crux members suffer",
            ),
        )

        self.tree.on_error = self.on_tree_error

    @property
    def session(self) -> aiohttp.ClientSession:
        return self.http._HTTPClient__session

    async def setup_hook(self) -> None:
        for file in os.listdir("cogs"):
            if file.endswith(".py") and not file.startswith("_"):
                name = file[:-3]
                await self.load_extension(name=f"cogs.{name}")

        await self.load_extension("jishaku")

    async def on_ready(self):
        await self.db.create_tables()

        prfx = (
            Back.BLACK
            + Fore.GREEN
            + time.strftime("%H:%M:%S UTC", time.gmtime())
            + Back.RESET
            + Fore.WHITE
            + Style.BRIGHT
        )
        print(prfx + " Logged in as " + Fore.YELLOW + self.user.name)
        print(prfx + " Bot ID " + Fore.YELLOW + str(self.user.id))
        print(prfx + " Discord Version " + Fore.YELLOW + discord.__version__)
        print(prfx + " Python Version " + Fore.YELLOW + str(platform.python_version()))
        synced = await self.tree.sync()
        print(
            prfx + " Slash CMDs Synced " + Fore.YELLOW + str(len(synced)) + " Commands"
        )
        print(Style.RESET_ALL)

    async def run_async(self, func, *args, **kwargs):
        return await self.loop.run_in_executor(None, func, *args, **kwargs)

    async def on_tree_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.CommandOnCooldown):
            return await interaction.response.send_message(
                f"Command is currently on cooldown! Try again in **{error.retry_after:.2f}** seconds!",
                ephemeral=True,
            )
        elif isinstance(error, app_commands.MissingPermissions):
            return await interaction.response.send_message(
                f"You're missing permissions to use this command!", ephemeral=True
            )
        elif isinstance(error, app_commands.MissingRole):
            return await interaction.response.send_message(
                f"To use this command you need the {error.missing_role} role!",
                ephemeral=True,
            )
        elif isinstance(error, app_commands.errors.CommandInvokeError) and isinstance(
            error.original, GithubAPIError
        ):
            if interaction.response.is_done():
                send = interaction.followup.send
            else:
                send = interaction.response.send_message

            return await send(f"Failed to fetch data from GitHub API ({error}).")
        else:
            raise error
