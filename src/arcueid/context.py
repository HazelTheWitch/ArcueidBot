from typing import Optional

import discord
import discord.ext.commands as comms


__all__ = [
    'ArcContext'
]


class ArcContext(comms.Context):
    """Extended Arcueid Command Context."""
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.errorHandled = False

    def generateEmbed(self, title: str, description: Optional[str], *,
                      error: bool = False, url: Optional[str] = None) -> discord.Embed:
        """Generate a thememed Discord embed"""
        if error:
            color = discord.Color(0xff1717)
        else:
            color = getattr(self.cog, 'color', discord.Color(self.bot.settings.theme))

            if color is None:
                color = discord.Color(self.bot.settings.theme)

        return discord.Embed(title=title, description=description, color=color, url=url)

    async def replyEmbed(self, title: str, description: str, *, error: bool = False, mention: bool = False) -> discord.Message:
        """Reply using a themed Discord embed"""
        return await self.reply(embed=self.generateEmbed(title, description, error=error), mention_author=mention)
