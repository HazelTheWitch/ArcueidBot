from typing import Optional

import discord
import discord.ext.commands as comms

from .abc import ACog

from ..context import ArcContext
from ..helper import plural


__all__ = [
    'FFXIVCog'
]


class FFXIVCog(ACog):
    @property
    def color(self) -> Optional[discord.Color]:
        return discord.Color(0xd834eb)

    @property
    def author(self) -> str:
        return 'Harlot#0001'
