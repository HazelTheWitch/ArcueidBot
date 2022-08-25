from typing import Optional, Awaitable, Any, Coroutine, Callable
import random

import discord
import discord.ext.commands as comms
import discord.ext.tasks as tasks

from .abc import ACog

from ..context import ArcContext
from ..helper import plural


__all__ = [
    'GeneralCog'
]


class GeneralCog(ACog):
    def __init__(self, bot: 'ArcBot') -> None:
        super().__init__(bot)

        self.statusCallbacks: list[Callable[[], Coroutine[Any, Any, str]]] = [
            self.commandsStatus,
            self.guildsStatus
        ]
        self.currentStatusCallback = 0

        self.updateStatus.start()

    def cog_unload(self) -> None:
        self.updateStatus.stop()

    async def commandsStatus(self) -> str:
        return f'with {len(self.bot.commands)} commands.'

    async def guildsStatus(self) -> str:
        return f'in {len(self.bot.guilds)} guilds.'

    @comms.command()
    async def invite(self, ctx: ArcContext) -> None:
        params: discord.AppInstallParams = ctx.bot.application.install_params

        embed = ctx.generateEmbed('Invite Link', 'Here is my invite link, thanks for supporting me!', url=self.bot.generateInviteURL(params.permissions, params.scopes))

        await ctx.reply(embed=embed, mention_author=False)

    @tasks.loop(minutes=5)
    async def updateStatus(self) -> None:
        game = discord.Game(await self.statusCallbacks[self.currentStatusCallback]())
        await self.bot.change_presence(status=discord.Status.online, activity=game)
        self.currentStatusCallback = (self.currentStatusCallback + 1) % len(self.statusCallbacks)

    @comms.command()
    async def decide(self, ctx: ArcContext, count: int = 1) -> None:
        things = (
            'League of Legends',
            'TFT',
            'Anime',
            'FFXIV',
            'It Takes Two',
            'We Were Here Forever',
            'Portal 2',
            'Terraria',
            'Minecraft',
            'Elden Ring',
            '20 Minutes Till Dawn',
            'Slay the Spire',
            'Stardew Valley',
            'FTL: Faster than Light',
            'Unrailed'
        )

        await ctx.replyEmbed('Here is what I decided', ', '.join(random.sample(things, count)))

    @property
    def color(self) -> Optional[discord.Color]:
        return discord.Color(0x50cca7)

    @property
    def author(self) -> str:
        return 'Harlot#0001'
