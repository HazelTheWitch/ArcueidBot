import importlib
import logging
from importlib import import_module
from inspect import getmembers
from typing import Optional

import discord
import discord.ext.commands as comms

from .cogs.abc import ACog
from .context import ArcContext
from .datastructures import LoadedCogs, ExitStatus
from .settings import Settings

__all__ = [
    'ArcBot'
]


class ArcBot(comms.Bot):
    def __init__(self, settings: Settings) -> None:
        super().__init__(comms.when_mentioned_or('arc.'), status=discord.Status.idle)

        self.exitStatus = ExitStatus.EXIT

        self.settings = settings

        self.logger = logging.getLogger('arcueid')

        self.cogModule = import_module('arcueid.cogs', 'arcueid')

        self.logger.info(self.loadCogs(False))

    def loadCogs(self, reload: bool = True) -> LoadedCogs:
        removed = set(self.cogs)

        for name in removed:
            self.remove_cog(name)
            self.logger.debug(f'Removed cog: {name}')

        if reload:
            cogs = importlib.reload(self.cogModule)
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
        await self.change_presence(status=discord.Status.online)
        self.logger.info('Arcueid Ready')

    def getCurrentVC(self, guild: discord.Guild) -> Optional[discord.VoiceClient]:
        for vc in self.voice_clients:
            if vc.channel.guild == guild:
                return vc
        return None

    async def launch(self) -> None:
        await self.start(self.settings.token)

    async def close(self) -> None:
        for guild in self.guilds:
            vc = self.getCurrentVC(guild)

            if vc is not None:
                await vc.disconnect(force=True)

        await super().close()
