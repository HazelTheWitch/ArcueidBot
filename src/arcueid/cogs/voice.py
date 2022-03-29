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
    @comms.command(aliases=('connect',))
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
    async def alarm(self, ctx: ArcContext, hour: int, minute: int, timezone: str) -> None:
        try:
            tz = pytz.timezone(timezone)
        except pytz.UnknownTimeZoneError:
            await ctx.replyEmbed('Invalid Timezone', f'The timezone "{timezone}" you entered is not valid.')
            return

        if not (0 <= hour < 24):
            await ctx.replyEmbed('Invalid Hour', f'The hour "{hour}" you entered is not valid.')
            return

        if not (0 <= minute < 60):
            await ctx.replyEmbed('Invalid Minute', f'The hour "{minute}" you entered is not valid.')
            return

        voice = ctx.author.voice

        if voice is None or voice.channel is None:
            await ctx.replyEmbed('Voice Channel Error', 'You are not in a voice channel so I can not play an alarm.')
            return

        currentVC = self.bot.getCurrentVC(ctx.guild)

        if currentVC is not None:
            await currentVC.disconnect()

        await voice.channel.connect()

        now = pytz.timezone('US/Pacific').localize(datetime.now()).astimezone(tz)

        targetTime = tz.localize(datetime(now.year, now.month, now.day, hour, minute))

        if targetTime < now:
            targetTime += timedelta(days=1)

        seconds = (targetTime - now).total_seconds()

        await asyncio.sleep(seconds)

        with importlib.resources.path('arcueid.data', 'alarm.wav') as sourcePath:
            print(sourcePath)

            source = discord.FFmpegPCMAudio(str(sourcePath.resolve()))

            currentVC = self.bot.getCurrentVC(ctx.guild)

            currentVC.play(source)

            await ctx.replyEmbed('Alarm Up', 'Your alarm has been triggered!')

    @property
    def color(self) -> Optional[discord.Color]:
        return discord.Color(0x4287f5)
