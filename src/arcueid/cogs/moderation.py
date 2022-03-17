from typing import Optional

import discord

from .abc import ACog
from ..context import ArcContext

__all__ = [
    'ModCog'
]


class ModCog(ACog):
    async def cog_check(self, ctx: ArcContext) -> bool:
        return ctx.channel.permissions_for(ctx.author).administrator or ctx.author == ctx.guild.owner

    @property
    def color(self) -> Optional[discord.Color]:
        return discord.Color(0x037ffc)
