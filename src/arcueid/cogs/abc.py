from abc import abstractmethod
from logging import Logger
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

    async def __ainit__(self) -> None:
        ...
    
    @property
    def logger(self) -> Logger:
        return self.bot.logger

    @property
    @abstractmethod
    def color(self) -> Optional[discord.Color]:
        return None

    @property
    @abstractmethod
    def author(self) -> str:
        return ''
