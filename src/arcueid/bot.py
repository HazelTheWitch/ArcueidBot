import importlib
import logging
from inspect import getmembers
from typing import Optional, Type

import discord
import discord.ext.commands as comms

from . import cogs
from .cogs.abc import ACog
from .context import ArcContext
from .datastructures import LoadedCogs, ExitStatus, PassthroughInfo
from .settings import Settings

__all__ = [
    'ArcBot'
]


class ArcBot(comms.Bot):
    def __init__(self, settings: Settings, passthrough: PassthroughInfo) -> None:
        super().__init__(command_prefix=comms.when_mentioned,
                         status=discord.Status.idle,
                         intents=discord.Intents.default())

        self.exitStatus = ExitStatus.EXIT

        self.passthrough = passthrough

        self.settings = settings

        self.logger = logging.getLogger('arcueid')

    async def loadCogs(self, reload: bool = True) -> LoadedCogs:
        removed = set(self.cogs)

        for name in removed:
            await self.remove_cog(name)
            self.logger.debug(f'Removed cog: {name}')

        if reload:
            importlib.reload(cogs)

        for name, cog in getmembers(cogs):
            if hasattr(cog, '__mro__') and ACog in cog.mro():
                await self.add_cog(cog(self))
                self.logger.debug(f'Added cog: {name}')

        loaded = set(self.cogs)

        return LoadedCogs.fromRemovedLoaded(removed, loaded)

    async def get_context(self, message: discord.Message, *, cls: Optional[Type[comms.Context]] = None) -> ArcContext:
        return await super().get_context(message, cls=cls or ArcContext)

    async def on_ready(self) -> None:
        self.logger.info(await self.loadCogs(True))

        game = discord.Game(f'with {len(self.commands)} commands')
        await self.change_presence(status=discord.Status.online, activity=game)

        if self.passthrough.restartMessage is not None:
            await (await self.passthrough.restartMessage.fetchMessage(self)).add_reaction('♥')

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

        await self.change_presence(status=discord.Status.invisible)

        await super().close()
