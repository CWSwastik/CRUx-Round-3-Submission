import os
import time

import discord
from discord import Intents
from discord.ext import commands

import platform
from colorama import Back, Style, Fore

try:
    import dotenv
except ImportError:
    pass
else:
    dotenv.load_dotenv(".env")


class Config:
    def __init__(self):
        self.bot_token = os.environ["TOKEN"]
        self.bot_prefix = os.environ.get("PREFIX", ["t!"])


class CruxTaskBot(commands.Bot):
    def __init__(self):
        self.config = Config()

        intents = Intents.default()
        intents.members = True

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

    async def setup_hook(self) -> None:
        for file in os.listdir("cogs"):
            if file.endswith(".py") and not file.startswith("_"):
                name = file[:-3]
                await self.load_extension(name=f"cogs.{name}")

        await self.load_extension("jishaku")

    async def on_ready(self):
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

    async def run_async(self, func, *args, **kwargs):
        return await self.loop.run_in_executor(None, func, *args, **kwargs)