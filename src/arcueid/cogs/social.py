from dataclasses import dataclass
from subprocess import TimeoutExpired
from typing import Iterator, Optional, Union, TYPE_CHECKING

import discord
import discord.ext.commands as comms

from collections import defaultdict
from dataclasses import dataclass

from arcueid.reactiontree import pagignate_embeds

from .abc import ACog
from ..context import ArcContext
from ..helper import plural

if TYPE_CHECKING:
    from ..bot import ArcBot

__all__ = [
    'SocialCog'
]

GROUP = dict[int, 'VoicePressence']

@dataclass(frozen=True)
class Group:
    channel: Union[discord.VoiceChannel, discord.StageChannel]
    pressences: list['VoicePressence']

    @classmethod
    def from_dict(cls, channel: Union[discord.VoiceChannel, discord.StageChannel], group: GROUP) -> Optional['Group']:
        if len(group.values()) == 0:
            return None

        return cls(channel, [
            pressence for pressence in group.values()
        ])
    
    @property
    def mute(self) -> int:
        return sum([1 if p.mute else 0 for p in self.pressences])
    
    @property
    def deaf(self) -> int:
        return sum([1 if p.deaf else 0 for p in self.pressences])
    
    @property
    def afk(self) -> int:
        return sum([1 if p.afk else 0 for p in self.pressences])
    
    @property
    def members(self) -> Iterator[discord.Member]:
        return iter([p.member for p in self.pressences])
    
    @property
    def total(self) -> int:
        return len(self.pressences)
    
    @property
    def active(self) -> int:
        return self.total - self.afk

    
    @property
    def streams(self) -> int:
        return sum([1 if p.streaming else 0 for p in self.pressences])

    
    @property
    def videos(self) -> int:
        return sum([1 if p.video else 0 for p in self.pressences])


@dataclass(frozen=True)
class VoicePressence:
    member: discord.Member
    deaf: bool
    mute: bool
    afk: bool
    streaming: bool
    video: bool

    def __repr__(self) -> str:
        return f'Pressence({str(self.member)}, mute={self.mute}, deaf={self.deaf}, afk={self.afk}, streaming={self.streaming}, video={self.video})'

    @classmethod
    def from_voice_state(cls, member: discord.Member, voice: discord.VoiceState) -> Optional['VoicePressence']:
        if voice.channel is None:
            return None
        
        return cls(
            member,
            voice.deaf or voice.self_deaf,
            voice.mute or voice.self_mute,
            voice.afk,
            voice.self_stream,
            voice.self_video,
        )


class SocialCog(ACog):
    def __init__(self, bot: 'ArcBot') -> None:
        super().__init__(bot)

        self.voice_channels: defaultdict[int, GROUP] = defaultdict(dict)
    
    async def __ainit__(self) -> None:
        self.bot.logger.debug("Begin loading voice states into memory.")

        for guild in self.bot.guilds:
            self.logger.debug(f"  On guild {guild}")
            for vc in guild.voice_channels:
                self.logger.debug(f"    On VoiceChannel {vc}")
                for id, voice_state in vc.voice_states.items():
                    member = guild.get_member(id)

                    self.logger.debug(f"      On Member {member}")

                    pressence = VoicePressence.from_voice_state(member, voice_state)

                    if pressence is not None:
                        self.voice_channels[vc.id][id] = pressence

        self.bot.logger.debug("Completed loading voice states into memory.")

    @comms.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        old_group: Optional[GROUP] = None
        new_group: Optional[GROUP] = None

        if before.channel is not None:
            old_group = self.voice_channels[before.channel.id]
            old_group.pop(member.id, None)
        if after.channel is not None:
            new_group = self.voice_channels[after.channel.id]

            new = VoicePressence.from_voice_state(member, after)

            if new is not None:
                new_group[member.id] = new
    
    def get_member_group(self, member: discord.Member) -> Optional[GROUP]:
        for group in self.voice_channels.values():
            if member.id in group:
                return group
        
        return None

    async def get_visisble_groups(self, member: discord.Member) -> list[Group]:
        groups = []

        for channel_id, group in self.voice_channels.items():
            channel = self.bot.get_channel(channel_id)

            if channel.guild.get_member(member.id) is not None and channel.permissions_for(member).connect:
                group = Group.from_dict(channel, group)
                if group is not None:
                    groups.append(group)
        
        return groups
    
    async def generate_embed_from_group(self, ctx: ArcContext, group: GROUP) -> discord.Embed:
        ctx.generateEmbed()

    @comms.group()
    async def groups(self, ctx: ArcContext) -> None:
        if ctx.invoked_subcommand is not None:
            return
    
    @groups.command()
    async def available(self, ctx: ArcContext) -> None:
        groups = await self.get_visisble_groups(ctx.author)

        embeds = []

        for group in groups:
            embed = ctx.generateEmbed(f'{group.channel.name} ({len(embeds)+1} / {len(groups)})', f"In the server **{group.channel.guild.name}**.\nUsers in the voice channel: ```{', '.join(map(str, group.members))}```\nClick the title of this embed to go there!", url=group.channel.jump_url)

            embed.add_field(name="Users", value=group.total, inline=True)
            embed.add_field(name="Active", value=group.active, inline=True)
            embed.add_field(name="Muted", value=group.mute, inline=True)
            embed.add_field(name="Deafened", value=group.deaf, inline=True)
            embed.add_field(name="AFK", value=group.afk, inline=True)
            embed.add_field(name="Streams", value=group.streams, inline=True)
            embed.add_field(name="Videos", value=group.videos, inline=True)
            
            embeds.append(embed)
        
        await self.bot.displayTree(ctx.channel, pagignate_embeds(embeds), (ctx.author,), timeout=60)

    @property
    def color(self) -> Optional[discord.Color]:
        return discord.Color(0x39a9bd)

    @property
    def author(self) -> str:
        return 'Harlot#0001'
