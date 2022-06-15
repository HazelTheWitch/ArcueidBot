from abc import abstractmethod
from typing import TYPE_CHECKING, Optional

import discord
import discord.ext.commands as comms

if TYPE_CHECKING:
    from ..bot import ArcBot


__all__ = [
    'ACog'
]


class ACog(comms.Cog):
    def __init__(self, bot: 'ArcBot') -> None:
        self.bot: 'ArcBot' = bot

    @property
    @abstractmethod
    def color(self) -> Optional[discord.Color]:
        return None
