import importlib
import logging
from inspect import getmembers
from typing import Optional, Type, Any, Union

import discord
import discord.ext.commands as comms

from . import cogs
from .cogs.abc import ACog
from .context import ArcContext
from .datastructures import LoadedCogs, ExitStatus, PassthroughInfo
from .settings import Settings
from .reactiontree import displayTree, TreeNode

__all__ = [
    'ArcBot'
]


class ArcBot(comms.Bot):
    def __init__(self, settings: Settings, passthrough: PassthroughInfo) -> None:
        super().__init__(command_prefix=comms.when_mentioned,
                         status=discord.Status.idle,
                         intents=discord.Intents.default() | discord.Intents(members=True))

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

    def generateInviteURL(self, permissions: discord.Permissions, scopes: list[str]) -> str:
        scopeString = '%20'.join(scopes)
        return f'https://discord.com/api/oauth2/authorize?client_id={self.application.id}' \
               f'&permissions={permissions.value}&scope={scopeString}'

    async def replyTree(self, message: discord.Message, node: TreeNode, timeout: Optional[float] = None) -> tuple[tuple[discord.abc.User, Any], ...]:
        return await self.displayTree(message, node, allowedUsers=(message.author,), timeout=timeout)

    async def displayTree(self, target: Union[discord.abc.Messageable, discord.Message], node: TreeNode, allowedUsers: Optional[tuple[discord.abc.User]] = None, timeout: Optional[float] = None) -> tuple[tuple[discord.abc.User, Any], ...]:
        return await displayTree(self, target, node, allowedUsers=allowedUsers, timeout=timeout)
