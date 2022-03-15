import traceback
from typing import Optional, cast, Type

import discord
import discord.ext.commands as comms

from .abc import ACog

from ..context import ArcContext

__all__ = [
    'ErrorHandlingCog'
]


class ErrorHandlingCog(ACog):
    @comms.Cog.listener()
    async def on_command_error(self, ctx: ArcContext, error: comms.CommandError) -> None:
        if ctx.errorHandled:
            return

        match error:
            case comms.CommandNotFound():
                return  # Avoid spamming on every Arcueid Ping
            case comms.CommandOnCooldown():
                title = 'Command on Cooldown'
                description = 'This command is on cooldown please try again in ' \
                              f'{round(cast(comms.CommandOnCooldown, error).retry_after, 1)} seconds.'
            case comms.MissingPermissions():
                title = 'Missing Permissions'
                description = 'You are missing required permissions to run the given command.'
            case comms.UserInputError():
                title = 'User Input Error'
                description = 'Something about your input was wrong, please check and try again.'
            case comms.CheckFailure():
                title = 'Check Failure'
                description = 'You are not allowed to use this command, if you believe this is in error contact an ' \
                              'administrator.'
            case _:
                title = f'Command Error ({type(error).__name__})'
                description = 'Something went wrong with the command you entered. '\
                              f'```{"".join(traceback.format_exception(cast(Type[BaseException], error), limit=1))}```' \
                              'Please contact Harlot#0001 about this.'

        await ctx.replyEmbed(title=title, description=description, error=True)

    @property
    def color(self) -> Optional[discord.Color]:
        return discord.Color(0xff1717)
