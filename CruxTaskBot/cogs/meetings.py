import discord
import asyncio
import traceback
from discord.ext import commands
from discord import app_commands
from typing import Optional


class createMeeting(discord.ui.Modal, title="Create Meeting"):
    agenda = discord.ui.TextInput(
        label="Agenda",
        placeholder="What is this meeting about...",
    )

    timings = discord.ui.TextInput(
        label="Enter the list of possible meeting timings",
        style=discord.TextStyle.long,
        placeholder="For example:\n24/10/2023 10:00\n24/10/2023 15:00",
        max_length=300,
    )

    duration = discord.ui.TextInput(
        label="Vote Duration",
        placeholder="How long should the voting last for (in seconds)...",
    )

    def __init__(self, *, channel: discord.TextChannel, **kwargs) -> None:
        super().__init__(**kwargs)
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"{self.agenda.value} Meet",
            description="Please vote for the time you'd like this meeting to be held at.\n\n",
            color=discord.Color.random(),
        )

        options = self.timings.value.split("\n")
        if len(options) < 2 or len(options) > 9:
            await interaction.response.send_message(
                f"Please provide 2 to 9 options for the vote.!",
                ephemeral=True,
            )
            return

        for i, option in enumerate(options):
            emoji = chr(0x1F1E6 + i)  # Emoji for voting options (A, B, C, ...)
            embed.description += f"{emoji} {option}\n"

        sent_message = await self.channel.send("@everyone", embed=embed)

        await interaction.response.send_message(
            f"The message has been sent to {self.channel.mention}!",
            ephemeral=True,
        )

        # Add reaction emojis for voting options
        for i in range(len(options)):
            emoji = chr(0x1F1E6 + i)
            await sent_message.add_reaction(emoji)

        time_to_sleep = int(self.duration.value)  # Improve parsing of this duration
        await asyncio.sleep(time_to_sleep)  # TODO: Improve this, use database

        sent_message = await self.channel.fetch_message(sent_message.id)
        reactions = sent_message.reactions

        # Calculate the winner (option with the most reactions)
        max_reactions = 0
        winning_option = None
        for i, reaction in enumerate(reactions):
            if reaction.count > max_reactions:
                max_reactions = reaction.count
                winning_option = options[i]

        if winning_option is not None:
            await self.channel.send(
                f"The winner is: {winning_option} with {max_reactions} votes!"
            )  # TODO: Add no winner, tie message

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        await interaction.response.send_message(
            "Oops! Something went wrong.", ephemeral=True
        )

        # Make sure we know what the error actually is
        traceback.print_exception(type(error), error, error.__traceback__)


class Meetings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="schedule_meet_voting",
        description="Makes the members vote on the date and time they prefer for a meet!",
    )
    @app_commands.describe(
        channel="The channel to post the message in. Defaults to #announcements"
    )
    async def schedule_meet_voting(
        self, interaction: discord.Interaction, channel: Optional[discord.TextChannel]
    ):
        channel = channel or discord.utils.get(
            interaction.guild.channels, name="announcements"
        )
        if channel is None:
            await interaction.response.send_message(
                "Announcements channel not found, please select a channel."
            )
        # TODO: Check permissions before sending
        await interaction.response.send_modal(createMeeting(channel=channel))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Meetings(bot))
