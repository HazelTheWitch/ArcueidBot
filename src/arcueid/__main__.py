import json
import logging
from pathlib import Path

import click

from .settings import Settings
from .bot import ArcBot


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

    bot = ArcBot(data, VERBOSITY[min(verbose, 3)])

    bot.launch()


if __name__ == '__main__':
    launch()
