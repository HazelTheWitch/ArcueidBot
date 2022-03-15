import importlib
import logging
import sys
from importlib import import_module
from inspect import getmembers
from typing import Coroutine, Any

import discord
import discord.ext.commands as comms

from .cogs.abc import ACog
from .context import ArcContext
from .datastructures import LoadedCogs
from .settings import Settings

__all__ = [
    'ArcBot'
]


class ArcBot(comms.Bot):
    def __init__(self, settings: Settings, level: int) -> None:
        super().__init__(comms.when_mentioned_or('arc.'))

        self.settings = settings

        self.logger = logging.getLogger('arcueid')
        self.logger.setLevel(level)

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))

        self.logger.addHandler(handler)

        self.cogModule = import_module('.cogs', 'arcueid')

        self.logger.info(self.loadCogs(False))

    def loadCogs(self, reload: bool = True) -> LoadedCogs:
        removed = set(self.cogs)

        for name in removed:
            self.remove_cog(name)
            self.logger.debug(f'Removed cog: {name}')

        if reload:
            self.cogModule = importlib.reload(self.cogModule)
            self.logger.debug('Reloaded cogs module')

        for name, cog in getmembers(self.cogModule):
            if hasattr(cog, '__mro__') and ACog in cog.mro():
                self.add_cog(cog(self))
                self.logger.debug(f'Added cog: {name}')

        loaded = set(self.cogs)

        return LoadedCogs.fromRemovedLoaded(removed, loaded)

    async def get_context(self, message: discord.Message, *, cls: comms.Context = ArcContext) -> ArcContext:
        return await super().get_context(message, cls=cls)

    async def on_ready(self) -> None:
        self.logger.info('Arcueid Ready')

    def launch(self) -> None:
        self.run(self.settings.token)
