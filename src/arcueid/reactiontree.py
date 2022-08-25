import asyncio
import datetime
import enum
import math
from collections.abc import Sequence
from collections import OrderedDict
from typing import Union, Optional, Any, Callable

import discord
from dataclasses import dataclass


__all__ = [
    'TreeNode',
    'pagignate',
    'displayTree'
]


EDIT_CONTENT = Union[
    Optional[str],
    Optional[discord.Embed],
    list[discord.Embed],
    list[Union[discord.Attachment, discord.File]],
    bool,
    Optional[float],
    Optional[discord.AllowedMentions],
    Optional[discord.ui.View]
]

EMOTE = Union[discord.Emoji, discord.Reaction, discord.PartialEmoji, str]

DO_NOT_INCLUDE = object()


class TreeNode:
    def __init__(self, *transitions: 'Transition', value: Any = DO_NOT_INCLUDE, **content: EDIT_CONTENT) -> None:
        self.value = value
        self.content = content

        self.transitionTable: OrderedDict[str, Transition] = OrderedDict()
        self.emoteTable: OrderedDict[str, EMOTE] = OrderedDict()

        self.addTransitions(*transitions)

    def addTransition(self, emote: EMOTE, node: Optional['TreeNode'], callback: Callable[[], bool] = lambda: True) -> None:
        transition = Transition(emote, node, callback)

        self.addTransitions(transition)

    def addTransitions(self, *transitions: 'Transition') -> None:
        for transition in transitions:
            emoteName = str(transition.emote)

            if emoteName in self.transitionTable:
                raise ValueError(f'Multiple transitions found for emote: {transition.emote}')

            self.transitionTable[emoteName] = transition
            self.emoteTable[emoteName] = transition.emote

    async def display(self, target: Union[discord.abc.Messageable, discord.Message], send: bool = False) -> discord.Message:
        if send:
            match target:
                case discord.abc.Messageable():
                    return await target.send(**self.content)
                case discord.Message():
                    return await target.reply(**self.content)
                case _:
                    raise TypeError(f'Target of incorrect type: {type(target)}')
        else:
            if not isinstance(target, discord.Message):
                raise TypeError(f'Target of incorrect type: {type(target)}')

            await target.edit(**self.content)

            return target

    async def perform(self, client: discord.Client, target: Union[discord.abc.Messageable, discord.Message], *allowedUsers: discord.abc.User, timeout: Optional[float] = None, send: bool = False) -> 'NextAction':
        message = await self.display(target, send=send)

        await message.clear_reactions()

        for emote in self.emoteTable:
            await message.add_reaction(emote)

        try:
            reaction, user = await client.wait_for('reaction_add', timeout=timeout, check=self.reactionCheck(message, allowedUsers, *self.transitionTable))

            transition = self.transitionTable[str(reaction.emoji)]

            return NextAction(Result.SUCCESS, self.value, user, transition.node if transition.callback() else None)
        except asyncio.TimeoutError:
            return NextAction(Result.TIMEOUT, self.value)
        except KeyError:
            return NextAction(Result.FAILURE, self.value)

    @classmethod
    def reactionCheck(cls, message: discord.Message, allowedUsers: Optional[tuple[discord.abc.User]], *allowedEmotes: str) -> Callable[[EMOTE, discord.abc.User], bool]:
        if allowedEmotes is not None:
            users = set(allowedUsers)
        else:
            users = set()
        emotes = set(allowedEmotes)

        def check(reaction: EMOTE, user: discord.abc.User) -> bool:
            return reaction.message == message and str(reaction.emoji) in emotes and (len(users) == 0 or user in users)

        return check


@dataclass
class Transition:
    emote: EMOTE
    node: Optional[TreeNode]
    callback: Callable[[], bool] = lambda: True


class Result(enum.Enum):
    SUCCESS = 'success',
    FAILURE = 'failure',
    TIMEOUT = 'timeout'


@dataclass(frozen=True)
class NextAction:
    result: Result
    value: Any = DO_NOT_INCLUDE
    user: Optional[discord.abc.User] = None
    node: Optional[TreeNode] = None


def pagignate(title: str, color: Union[discord.Color, int], options: Sequence[str], countPerPage: int, url: Optional[str] = None, timestamp: Optional[datetime.datetime] = None) -> TreeNode:
    nodes = []

    pages = math.ceil(len(options) / countPerPage)

    while len(options) >= countPerPage:
        current = options[:countPerPage]
        options = options[countPerPage:]

        embed = discord.Embed(title=title + f' ({len(nodes) + 1} / {pages})', color=color, url=url, timestamp=timestamp, description='\n'.join(current))

        nodes.append(TreeNode(embed=embed))

    for i, node in enumerate(nodes):
        if i > 0:  # Can go backwards so add first and back
            node.addTransition('⏪', nodes[0])
            node.addTransition('◀️', nodes[i - 1])
        if i < len(nodes) - 1:  # Can go forwards so add last and forward
            node.addTransition('▶️', nodes[i + 1])
            node.addTransition('⏩', nodes[-1])

        node.addTransition('🚫', None)

    return nodes[0]


async def displayTree(client: discord.Client, target: Union[discord.abc.Messageable, discord.Message], node: TreeNode, allowedUsers: Optional[tuple[discord.abc.User]] = None, timeout: Optional[float] = None, deleteAfter: Optional[float] = None) -> tuple[tuple[discord.abc.User, Any], ...]:
    values: list[tuple[discord.abc.User, Any]] = []

    message: discord.Message

    message = await node.display(target, send=True)

    displaying = True

    while displaying:
        action = await node.perform(client, message, *allowedUsers, timeout=timeout)

        if action.node is None or action.result is not Result.SUCCESS:
            displaying = False

        if action.value is not DO_NOT_INCLUDE:
            values.append((action.user, action.value))

        node = action.node

    await message.clear_reactions()

    if deleteAfter is not None:
        await message.delete(delay=deleteAfter)

    return tuple(values)
