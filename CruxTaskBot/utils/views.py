import discord
from typing import List


class Paginator(discord.ui.View):
    def __init__(
        self,
        interaction: discord.Interaction,
        pages: List[discord.Embed],
        timeout: float | None = 180,
    ):
        self.interaction = interaction
        self.pages = pages
        self.index = 1
        super().__init__(timeout=timeout)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == self.interaction.user:
            return True
        else:
            emb = discord.Embed(
                description=f"Only the author of the command can perform this action.",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=emb, ephemeral=True)
            return False

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.blurple, disabled=True)
    async def previous(self, interaction: discord.Interaction, button: discord.Button):
        self.index -= 1
        await self.edit_page(interaction)

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.blurple)
    async def next(self, interaction: discord.Interaction, button: discord.Button):
        self.index += 1
        await self.edit_page(interaction)

    async def edit_page(self, interaction: discord.Interaction):
        emb = self.pages[self.index - 1]
        emb.set_footer(text=f"Page {self.index} of {len(self.pages)}")
        self.update_buttons()
        await interaction.response.edit_message(embed=emb, view=self)

    async def on_timeout(self):
        message = await self.interaction.original_response()
        await message.edit(view=None)  # remove buttons on timeout

    def update_buttons(self):
        self.children[0].disabled = self.index == 1
        self.children[1].disabled = self.index == len(self.pages)
