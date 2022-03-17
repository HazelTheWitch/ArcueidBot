from typing import Optional

import discord
import discord.ext.commands as comms

from .abc import ACog

from ..context import ArcContext
from ..datastructures import ExitStatus
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

    @comms.group()
    async def cogs(self, ctx: ArcContext) -> None:
        if ctx.invoked_subcommand is not None:
            return

        cogs = list(sorted(self.bot.cogs))

        await ctx.replyEmbed(f'Currently Loaded {plural(len(cogs), "Cog", "Cogs")}', ', '.join(cogs))

    @cogs.command()
    @comms.cooldown(rate=1, per=30)
    async def reload(self, ctx: ArcContext) -> None:
        data = self.bot.loadCogs(True)

        embed = ctx.generateEmbed('Cogs Reloaded', f'{plural(data.total, "cog", "cogs")} changed.')

        embed.add_field(name='Removed', value=str(data.removed), inline=True)
        embed.add_field(name='Reloaded', value=str(data.reloaded), inline=True)
        embed.add_field(name='Loaded', value=str(data.loaded), inline=True)

        await ctx.reply(embed=embed)

    @comms.command(aliases=('close', 'logout'))
    async def exit(self, ctx: ArcContext) -> None:
        await ctx.replyEmbed('Exiting', 'Logging off. ♥')

        self.bot.exitStatus = ExitStatus.EXIT

        await self.bot.close()

    @comms.command(aliases=('reload',))
    async def restart(self, ctx: ArcContext, reload: bool = True) -> None:
        await ctx.replyEmbed('Restarting', f'Restarting {"with" if reload else "without"} reloading.')

        self.bot.exitStatus = ExitStatus.RESTART if reload else ExitStatus.RESTART_NO_RELOAD

        await self.bot.close()

    @property
    def color(self) -> Optional[discord.Color]:
        return discord.Color(0xfcba03)
