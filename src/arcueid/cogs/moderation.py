from typing import Optional

import discord
import discord.ext.commands as comms

from .abc import ACog
from ..context import ArcContext

__all__ = [
    'ModCog'
]


class ModCog(ACog):
    async def cog_check(self, ctx: ArcContext) -> bool:
        return ctx.channel.permissions_for(ctx.author).administrator or ctx.author == ctx.guild.owner

    @comms.group(aliases=('server',))
    async def guild(self, ctx: ArcContext) -> None:
        ...

    @guild.command()
    async def info(self, ctx: ArcContext) -> None:
        guild = ctx.guild

        if guild is None:
            await ctx.replyEmbed('Server Error', 'Not currently in a server!')
            return

        embed = ctx.generateEmbed('Server Info', f'Generated information for "**{guild.name}**".')

        embed.add_field(name='Members', value=str(guild.member_count), inline=True)
        embed.add_field(name='Voice Channels', value=str(len(guild.voice_channels)), inline=True)
        embed.add_field(name='Text Channels', value=str(len(guild.text_channels)), inline=True)

        premiumRole = guild.premium_subscriber_role
        premiumRoleName = premiumRole.name if premiumRole is not None else None

        embed.add_field(name='Boosted Tier', value=str(guild.premium_tier), inline=True)
        embed.add_field(name='Booster Count', value=str(guild.premium_subscription_count), inline=True)
        embed.add_field(name='Boost Role Name', value=str(premiumRoleName), inline=True)

        await ctx.reply(embed=embed)

    @property
    def color(self) -> Optional[discord.Color]:
        return discord.Color(0x037ffc)
