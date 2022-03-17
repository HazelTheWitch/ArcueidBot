from dataclasses import dataclass

from enum import Enum, auto


__all__ = [
    'LoadedCogs',
    'ExitStatus'
]


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
