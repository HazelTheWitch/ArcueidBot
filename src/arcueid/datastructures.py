from dataclasses import dataclass

from enum import Enum, auto


__all__ = [
    'LoadedCogs',
    'ExitStatus',
    'MessageData',
    'PassthroughInfo'
]

from typing import Optional

import discord


@dataclass(frozen=True)
class LoadedCogs:
    removed: int
    reloaded: int
    loaded: int

    @property
    def total(self) -> int:
        return self.removed + self.reloaded + self.loaded

    def __str__(self) -> str:
        return f'{self.removed} old cogs removed, {self.reloaded} cogs reloaded, {self.loaded} new cogs loaded.'

    @classmethod
    def fromRemovedLoaded(cls, removed: set[str], loaded: set[str]) -> 'LoadedCogs':
        reloaded = len(removed.intersection(loaded))

        return cls(len(removed) - reloaded, reloaded, len(loaded) - reloaded)


class ExitStatus(Enum):
    EXIT = auto()
    RESTART = auto()
    RESTART_NO_RELOAD = auto()


@dataclass(frozen=True)
class MessageData:
    channel: int
    message: int

    async def fetchMessage(self, client: discord.Client) -> discord.Message | None:
        channel = client.get_channel(self.channel)
        
        if channel is None or isinstance(channel, discord.StageChannel | discord.CategoryChannel | discord.ForumChannel):
            return None
        
        return await channel.fetch_message(self.message)

    @classmethod
    def fromMessage(cls, msg: discord.Message) -> 'MessageData':
        return cls(msg.guild.id, msg.channel.id, msg.id)


@dataclass
class PassthroughInfo:
    restartMessage: Optional[MessageData] = None
