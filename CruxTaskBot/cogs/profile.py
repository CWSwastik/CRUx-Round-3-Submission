import discord
from discord import app_commands
from discord.ext import commands
from utils.models import User
from typing import Optional


class Profile(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    profile = app_commands.Group(
        name="profile", description="Commands related to profiles"
    )

    @profile.command(
        name="set",
        description="Set your profile!",
    )
    @app_commands.describe(
        github="Your GitHub username",
        email="Your email address",
    )
    async def profile_set(
        self, interaction: discord.Interaction, github: str, email: str
    ):
        """
        This command allows users to set their GitHub username and email address.
        The details are stored in a database.
        """

        user = User(
            id=interaction.user.id,
            github=github,
            email=email,
        )

        if await self.bot.db.fetch_user(interaction.user.id):
            await self.bot.db.update_user(user)
        else:
            await self.bot.db.create_user(user)

        await interaction.response.send_message(
            f"Profile set for {interaction.user.mention}!"
        )

    @profile.command(
        name="view",
        description="View someone's profile!",
    )
    @app_commands.describe(
        user="The user to view the profile for",
    )
    async def profile_view(
        self, interaction: discord.Interaction, user: Optional[discord.Member]
    ):
        """
        This command allows users to view the GitHub username and email address of users.
        """
        discord_user = user or interaction.user

        user = await self.bot.db.fetch_user(discord_user.id)
        embed = discord.Embed(
            title=f"{discord_user.display_name}'s Profile",
            color=discord.Color.random(),
        )
        embed.set_thumbnail(url=discord_user.display_avatar.url)

        if user:
            embed.description = f"GitHub: [{user.github}](https://github.com/{user.github})\nEmail: {user.email}"
        else:
            embed.description = "GitHub: Not Set\nEmail: Not Set"

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Profile(bot))
