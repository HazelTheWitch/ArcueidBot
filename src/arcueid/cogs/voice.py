import asyncio
import importlib.resources
from datetime import datetime, timedelta
from typing import Optional

import discord
import discord.ext.commands as comms
import pytz

from .abc import ACog

from ..context import ArcContext
from ..helper import plural


__all__ = [
    'VoiceCog'
]


class VoiceCog(ACog):
    @comms.command(aliases=('connect', 'follow', 'come', 'omghi'))
    async def join(self, ctx: ArcContext) -> None:
        voice = ctx.author.voice

        if voice is None or voice.channel is None:
            await ctx.replyEmbed('Connect Failed', 'You are not in a voice channel so I can not join you.')
            return

        currentVC = self.bot.getCurrentVC(ctx.guild)

        if currentVC is not None:
            await currentVC.disconnect()

        await voice.channel.connect()

        await ctx.replyEmbed('Voice Connected', 'Successfully connected to your voice channel.')

    @comms.command(aliases=('disconnect',))
    async def leave(self, ctx: ArcContext) -> None:
        vc = self.bot.getCurrentVC(ctx.guild)

        if vc is None:
            await ctx.replyEmbed('Disconnect Failed', 'Not currently connected to a voice channel.')
            return

        await vc.disconnect()

        await ctx.replyEmbed('Voice Disconnected', 'Successfully disconnected from the voice channel.')

    @comms.command(aliases=('move',))
    # TODO: Add @comms.require_permissions(move_members=True) and figure out why it wont work
    async def drag(self, ctx: ArcContext) -> None:
        voice = ctx.author.voice

        if voice is None or voice.channel is None:
            await ctx.replyEmbed('Drag Error', 'You are not in a voice channel so I can not drag you.')
            return

        toVC = voice.channel
        fromVClient = self.bot.getCurrentVC(ctx.guild)

        if toVC == fromVClient.channel:
            await ctx.replyEmbed('Drag Error', 'Can not drag to and from the same channel, try moving to a new channel '
                                               'and trying again.')
            return

        dragged = 0

        for member in fromVClient.channel.members:
            if member != self.bot.user:
                await member.move_to(toVC)
                dragged += 1

        await fromVClient.disconnect()

        await ctx.replyEmbed(f'{plural(dragged, "User", "Users")} Dragged', 'Dragged '
                                                                            f'**{plural(dragged, "user", "users")}** '
                                                                            'from '
                                                                            f'**{fromVClient.channel.name}** to '
                                                                            f'**{toVC.name}**')

    @comms.command()
    async def voiceInfo(self, ctx: ArcContext) -> None:
        voice = ctx.author.voice

        if voice is None or voice.channel is None:
            await ctx.replyEmbed('Voice Info Error', 'You are not in a voice channel so I can not perform this command for you.')
            return

        await ctx.replyEmbed('Voice Info', f'**{len(voice.channel.members)}** members.')

    @comms.command()
    async def borrow(self, ctx: ArcContext, target: discord.Member) -> None:
        toVClient = ctx.author.voice
        fromVClient = target.voice

        if toVClient is None or toVClient.channel is None:
            await ctx.replyEmbed('Borrow Error', 'You are not in a voice channel so I have no target.')
            return

        if fromVClient is None or fromVClient.channel is None:
            await ctx.replyEmbed('Borrow Error', 'They are not in a voice channel so I have no source.')
            return

        toVC = toVClient.channel

        await fromVClient.channel.connect()

        await asyncio.sleep(0.5)

        await target.move_to(toVC, reason=f'{ctx.author} is borrowing them lol')

    @comms.command()
    async def unborrow(self, ctx: ArcContext, target: discord.Member) -> None:
        targetVc = self.bot.getCurrentVC(ctx.guild)

        await target.move_to(targetVc.channel)
        await targetVc.disconnect()

    @property
    def color(self) -> Optional[discord.Color]:
        return discord.Color(0x4287f5)

    @property
    def author(self) -> str:
        return 'Harlot#0001'
