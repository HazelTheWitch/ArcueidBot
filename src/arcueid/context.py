import discord
import discord.ext.commands as comms


__all__ = [
    'ArcContext'
]


class ArcContext(comms.Context):
    """Extended Arcueid Command Context."""
    def generateEmbed(self, title: str, description: str) -> discord.Embed:
        """Generate a thememed Discord embed"""

        color = getattr(self.cog, 'color', discord.Color(self.bot.settings.theme))

        if color is None:
            color = discord.Color(self.bot.settings.theme)

        return discord.Embed(title=title, description=description, color=color)

    async def replyEmbed(self, title: str, description: str) -> None:
        """Reply using a themed Discord embed"""
        await self.reply(embed=self.generateEmbed(title, description))
