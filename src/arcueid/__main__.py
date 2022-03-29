import asyncio
import contextlib
import logging
import sys
from importlib import reload
from pathlib import Path

import click

from .datastructures import ExitStatus, PassthroughInfo
from .settings import Settings
from . import bot as abot


__all__ = [
    'generateSettings',
    'launch'
]


VERBOSITY = [
    logging.ERROR,
    logging.WARNING,
    logging.INFO,
    logging.DEBUG
]


@contextlib.contextmanager
def eventLoop():
    loop = asyncio.new_event_loop()

    asyncio.set_event_loop(loop)

    yield loop


@click.command()
@click.argument('path', type=click.Path(writable=True, dir_okay=False))
@click.argument('token', type=str)
def generateSettings(path: str, token: str) -> None:
    settingsPath = Path(path)

    data = Settings(token)

    data.save(settingsPath)


@click.command()
@click.argument('path', type=click.Path(readable=True, dir_okay=False, exists=True))
@click.option('-v', '--verbose', count=True)
def launch(path: str, verbose: int) -> None:
    settingsPath = Path(path)

    data = Settings.load(settingsPath)

    verbosity = VERBOSITY[min(verbose, 3)]

    logger = logging.getLogger('arcueid')
    logger.setLevel(verbosity)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))

    logger.addHandler(handler)

    with eventLoop() as loop:
        loop.run_until_complete(mainLoop(data,))


async def mainLoop(data: Settings) -> None:
    passthrough = PassthroughInfo()

    while True:
        bot = abot.ArcBot(data, passthrough)

        try:
            await bot.launch()
        except KeyboardInterrupt:
            await bot.close()
            return

        passthrough = bot.passthrough

        # Have to include .value for some godforsaken reason
        match bot.exitStatus.value:
            case ExitStatus.EXIT.value:
                return
            case ExitStatus.RESTART.value:
                reload(abot)
            case ExitStatus.RESTART_NO_RELOAD.value:
                pass


if __name__ == '__main__':
    launch()
