import datetime
import discord
import asyncio
import traceback
from discord.ext import commands
from discord import app_commands
from typing import Optional
from utils import parse_time_to_seconds


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
        placeholder="How long should the voting last for (eg. 2d, 6h, 30mins etc)",
    )

    def __init__(
        self,
        *,
        channel: discord.TextChannel,
        ping_role_id: Optional[int] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.channel = channel
        self.ping_role_id = ping_role_id

    async def on_submit(self, interaction: discord.Interaction):
        time_to_sleep = parse_time_to_seconds(self.duration.value)

        embed = discord.Embed(
            title=f"{self.agenda.value} Meet",
            description=f"Please vote for the time you'd like this meeting to be held at.\nThe voting ends <t:{(datetime.datetime.now() + datetime.timedelta(seconds=time_to_sleep+3)).timestamp():.0f}:R>\n\n",  # Add +3 seconds to account for latency
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

        sent_message = await self.channel.send(
            f"<@&{self.ping_role_id}>" if self.ping_role_id else "@everyone",
            embed=embed,
            allowed_mentions=discord.AllowedMentions.all(),
        )

        await interaction.response.send_message(
            f"The voting has begun in {self.channel.mention}!",
            ephemeral=True,
        )

        # Add reaction emojis for voting options
        for i in range(len(options)):
            emoji = chr(0x1F1E6 + i)
            await sent_message.add_reaction(emoji)

        await asyncio.sleep(time_to_sleep)

        sent_message = await self.channel.fetch_message(sent_message.id)
        reactions = sent_message.reactions

        # Calculate the winner (option with the most reactions)
        max_reactions = 0
        winning_options = []
        tie = False

        for i, reaction in enumerate(reactions):
            vote_count = reaction.count - 1  # Remove the bot's reaction
            if vote_count > max_reactions:
                max_reactions = vote_count
                winning_options = [options[i]]
                tie = False
            elif vote_count == max_reactions and vote_count != 0:
                winning_options.append(options[i])
                tie = True

        if winning_options and not tie:
            await sent_message.reply(
                f"The members have decided that the meeting will be held at `{winning_options[0]}` with {max_reactions} votes!"
            )
        elif tie:
            await sent_message.reply(
                f"It's a tie! Multiple timings have the same number of votes: {', '.join(winning_options)}"
            )
        else:
            await sent_message.reply(
                "Nobody voted, looks like the members have stopped caring :("
            )

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        await interaction.response.send_message(
            "Oops! Something went wrong.", ephemeral=True
        )

        traceback.print_exception(type(error), error, error.__traceback__)


class Meetings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def project_autocomplete(
        self, interaction: discord.Interaction, current: str
    ):
        projects = await self.bot.db.list_all_projects()
        if "Senate" in [r.name for r in interaction.user.roles]:
            return [
                app_commands.Choice(name=p.title, value=p.title)
                for p in projects
                if current.lower() in p.title.lower()
            ]
        else:
            return [
                app_commands.Choice(name=p.title, value=p.title)
                for p in projects
                if p.role in [r.id for r in interaction.user.roles]
                and current.lower() in p.title.lower()
            ]

    @app_commands.command(
        name="schedule-meet-voting",
        description="Makes the members vote on the date and time they prefer for a meet!",
    )
    @app_commands.describe(
        channel="The channel to post the message in. Defaults to #announcements",
        project="Select a project to hold the meeting for. Defaults to an all members meet. (@everyone)",
    )
    @app_commands.autocomplete(
        project=project_autocomplete,
    )
    async def schedule_meet_voting(
        self,
        interaction: discord.Interaction,
        channel: Optional[discord.TextChannel] = None,
        project: Optional[str] = None,
    ):
        if "Senate" not in [r.name for r in interaction.user.roles] and project is None:
            return await interaction.response.send_message(
                "You can't schedule a meeting for all members, please select a project.",
                ephemeral=True,
            )

        if project is None:
            channel = channel or discord.utils.get(
                interaction.guild.channels, name="announcements"
            )
            if channel is None:
                return await interaction.response.send_message(
                    "Announcements channel not found, please select a channel."
                )
        else:
            project_obj = await self.bot.db.fetch_project(project)
            if project_obj.role not in [
                r.id for r in interaction.user.roles
            ] and "Senate" not in [r.name for r in interaction.user.roles]:
                await interaction.response.send_message(
                    f"You don't have permission to create meetings under `{project}`.",
                    ephemeral=True,
                )
                return
            channel = self.bot.get_channel(
                project_obj.channel
            ) or await interaction.guild.fetch_channel(project_obj.channel)

        await interaction.response.send_modal(
            createMeeting(
                channel=channel, ping_role_id=project_obj.role if project else None
            )
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Meetings(bot))
