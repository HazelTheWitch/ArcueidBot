from typing import Optional

import discord
import discord.ext.commands as comms

from .abc import ACog

from ..context import ArcContext
from ..helper import plural


__all__ = [
    'ImagesCog'
]


class ImagesCog(ACog):
    @comms.command()
    def toGif(self, ctx: ArcContext) -> None:
        ...

    @property
    def color(self) -> Optional[discord.Color]:
        return discord.Color(0xd834eb)
