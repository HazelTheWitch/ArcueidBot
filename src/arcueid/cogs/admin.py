import random
from typing import Optional

import discord
import discord.ext.commands as comms

from .abc import ACog
from ..context import ArcContext
from ..datastructures import ExitStatus, MessageData
from ..helper import plural
from ..reactiontree import pagignate
from .. import VERSION

__all__ = [
    'AdminCog'
]


class AdminCog(ACog):
    async def cog_check(self, ctx: ArcContext) -> bool:
        return await self.bot.is_owner(ctx.author)

    @comms.command(aliases=('ping',))
    async def latency(self, ctx: ArcContext) -> None:
        await ctx.replyEmbed('Current Latency', f'Current latency is {int(self.bot.latency * 1000)} ms.')

    @comms.group()
    async def cogs(self, ctx: ArcContext) -> None:
        if ctx.invoked_subcommand is not None:
            return

        cogs = list(sorted(self.bot.cogs))

        await ctx.replyEmbed(f'Currently Loaded {plural(len(cogs), "Cog", "Cogs")}', ', '.join(cogs))

    @comms.command(aliases=('close', 'logout'))
    async def exit(self, ctx: ArcContext) -> None:
        await ctx.replyEmbed('Exiting', 'Logging off. ♥')

        self.bot.exitStatus = ExitStatus.EXIT

        await self.bot.close()

    @comms.command(aliases=('reload',))
    async def restart(self, ctx: ArcContext, reload: bool = True) -> None:
        msg = await ctx.replyEmbed('Restarting', f'Restarting {"with" if reload else "without"} reloading.')

        self.bot.passthrough.restartMessage = MessageData.fromMessage(msg)

        self.bot.exitStatus = ExitStatus.RESTART if reload else ExitStatus.RESTART_NO_RELOAD

        await self.bot.close()

    @comms.command()
    async def sync(self, ctx: ArcContext, onlyGuild: bool = False) -> None:
        message = await ctx.replyEmbed('Syncing', 'Syncing slash commands with Discord '
                                                  f'{"in **" + ctx.guild.name + "**" if onlyGuild else "globally"}.')

        if onlyGuild:
            await self.bot.tree.sync(guild=ctx.guild)
        else:
            await self.bot.tree.sync()

        await message.add_reaction('♥')

    @comms.group()
    async def test(self, ctx: ArcContext) -> None:
        if ctx.invoked_subcommand is not None:
            return

        embed = ctx.generateEmbed('Test Information', None)

        embed.add_field(name='Version', value='.'.join(map(str, VERSION)))
        embed.add_field(name='Available Subcommands', value=len(self.test.commands))

        await ctx.reply(embed=embed)

    @test.command()
    async def pagignation(self, ctx: ArcContext, items: int, perPage: int) -> None:
        def randomItem(length: int) -> str:
            return ''.join(random.sample('0123456789ABCDEF', length))

        selectedItems = [randomItem(8) for _ in range(items)]

        node = pagignate('Test Pagignation', self.color, selectedItems, perPage)

        await self.bot.replyTree(ctx.message, node, 60)

    @property
    def color(self) -> Optional[discord.Color]:
        return discord.Color(0xfcba03)

    @property
    def author(self) -> str:
        return 'Harlot#0001'
