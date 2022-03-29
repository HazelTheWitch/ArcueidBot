from datetime import datetime
from typing import Optional

import discord
import discord.ext.commands as comms
import pytz as pytz

from .abc import ACog

from ..context import ArcContext
from ..datastructures import ExitStatus, MessageData
from ..helper import plural


__all__ = [
    'AdminCog'
]


class AdminCog(ACog):
    async def cog_check(self, ctx: ArcContext) -> bool:
        return await self.bot.is_owner(ctx.author)

    @comms.command(aliases=('ping',))
    async def latency(self, ctx: ArcContext) -> None:
        await ctx.replyEmbed('Current Latency', f'Current latency is {int(self.bot.latency * 1000)} ms.')

    @comms.command()
    async def joy(self, ctx: ArcContext) -> None:
        now = pytz.timezone('US/Pacific').localize(datetime.now())

        target = pytz.timezone('US/Pacific').localize(datetime(2022, 5, 28))

        difference = target - now

        days = difference.days
        hours = difference.seconds // 3600
        minutes = (difference.seconds // 60) % 60

        await ctx.replyEmbed('Time Until Joy', f'{days} days, {hours} hours, {minutes} minutes')

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

    @property
    def color(self) -> Optional[discord.Color]:
        return discord.Color(0xfcba03)
