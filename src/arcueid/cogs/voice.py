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
        if not isinstance(ctx.author, discord.Member):
            await ctx.replyEmbed('Connect Failed', 'You are not in a voice channel so I can not join you.')
            return

        voice = ctx.author.voice

        if voice is None or voice.channel is None:
            await ctx.replyEmbed('Connect Failed', 'You are not in a voice channel so I can not join you.')
            return

        currentVC = self.bot.getCurrentVC(ctx.author.guild)

        if currentVC is not None:
            await currentVC.disconnect()

        await voice.channel.connect()

        await ctx.replyEmbed('Voice Connected', 'Successfully connected to your voice channel.')

    @comms.command(aliases=('disconnect',))
    async def leave(self, ctx: ArcContext) -> None:
        if not isinstance(ctx.author, discord.Member):
            await ctx.replyEmbed('Disconnect Failed', 'Not currently connected to a voice channel.')
            return

        vc = self.bot.getCurrentVC(ctx.author.guild)

        if vc is None:
            await ctx.replyEmbed('Disconnect Failed', 'Not currently connected to a voice channel.')
            return

        await vc.disconnect()

        await ctx.replyEmbed('Voice Disconnected', 'Successfully disconnected from the voice channel.')

    @comms.command(aliases=('move',))
    @comms.has_guild_permissions(move_members=True)
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
    @comms.has_guild_permissions(move_members=True)
    async def trigger(self, ctx: ArcContext, target: discord.Member) -> None:
        if not isinstance(ctx.author, discord.Member):
            await ctx.replyEmbed('Trigger Error', 'You are not in a voice channel so I can not create a trigger for you.')
            return

        voice = ctx.author.voice

        if voice is None or voice.channel is None:
            await ctx.replyEmbed('Trigger Error', 'You are not in a voice channel so I can not create a trigger for you.')
            return

        to_channel = voice.channel

        target_voice = target.voice

        if target_voice:
            await target.move_to(to_channel, reason=f"trigger by {ctx.author}")
            await ctx.replyEmbed("Trigger Activated", "The trigger set up was activated")
            return

        def check(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> bool:
            if member != target:
                return False
            
            if after.channel is not None:
                return True
            
            return False

        target, _, _ = self.bot.wait_for("voice_stateee_update", check=check)

        target_voice = target.voice

        if target_voice:
            await target.move_to(to_channel, reason=f"trigger by {ctx.author}")
            await ctx.replyEmbed("Trigger Activated", "The trigger set up was activated")
            return
        else:
            await ctx.replyEmbed("Could not Trigger", "The trigger set up could not be activated", error=True)
            return

    @comms.command()
    async def voiceInfo(self, ctx: ArcContext) -> None:
        if not isinstance(ctx.author, discord.Member):
            await ctx.replyEmbed('Voice Info Error', 'You are not in a voice channel so I can not perform this command for you.')
            return
        
        voice = ctx.author.voice

        if voice is None or voice.channel is None:
            await ctx.replyEmbed('Voice Info Error', 'You are not in a voice channel so I can not perform this command for you.')
            return

        await ctx.replyEmbed('Voice Info', f'**{len(voice.channel.members)}** members.')

    @comms.command()
    @comms.has_guild_permissions(move_members=True)
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
    @comms.has_guild_permissions(move_members=True)
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
