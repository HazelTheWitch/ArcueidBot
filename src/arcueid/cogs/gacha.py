from math import ceil, floor
from typing import Optional

import discord
import discord.ext.commands as comms

from .abc import ACog

from ..context import ArcContext
from ..helper import plural

import pygsheets

import random
import statistics


__all__ = [
    'GachaCog'
]

class CharacterSimulation:
    def __init__(self, starting_pity: int = 0, starting_guaranteed: bool = False) -> None:
        self.won_5050 = not starting_guaranteed
        self.pull_number = self.total = self.starting = starting_pity

    @property
    def probability(self) -> float:
        if self.pull_number < 74:
            return 0.006
        if self.pull_number >= 90:
            return 1
        else:
            return 0.006 + 0.06 * (self.pull_number - 73)

    def pull(self) -> tuple[bool, bool]:
        self.pull_number += 1
        self.total += 1

        if random.random() < self.probability:
            if self.won_5050:
                return True, random.random() < 0.5
            else:
                return True, True
        else:
            return False, False

    def c(self, n: int) -> int:
        copies = 0

        while copies < n + 1:
            five_star, correct = self.pull()

            if five_star:
                self.pull_number = 0

                if correct:
                    copies += 1
                    self.won_5050 = True
                else:
                    self.won_5050 = False
        
        return self.total - self.starting


class WeaponSimulation:
    def __init__(self, pity: int, lost_previous_75_25: bool, fate_points: int) -> None:
        self.total_pulls = 0
        self.pity = pity
        self.lost_previous_75_25 = lost_previous_75_25
        self.fate_points = fate_points
    
    @property
    def probability(self) -> float:
        return min(1, 0.007 + 0.07 * max(0, self.pity - 62))
    
    def pull(self) -> bool:
        five_star, target = False, False

        if random.random() < self.probability:  # is a 5 star
            five_star = True
            if self.fate_points >= 2:  # guaranteed is target
                target = True
            else:
                if self.lost_previous_75_25:  # is a 50 / 50 for the target one
                    target = random.random() < 0.5
                    self.lost_previous_75_25 = False
                else:  # is a 75 / 25 for a 50 / 50
                    if random.random() < 0.75:  # is a 50 / 50 now
                        target = random.random() < 0.5
                        self.lost_previous_75_25 = False
                    else:
                        self.lost_previous_75_25 = True

        self.pity += 1
        self.total_pulls += 1

        if five_star:
            self.pity = 0

            if target:
                self.fate_points = 0
            else:
                self.fate_points += 1

        return five_star and target
    
    def r(self, copies: int) -> int:
        current = 0

        while current < copies:
            if self.pull():
                current += 1

        return self.total_pulls


def c(n: int, starting_pity: int, lost_previous_50_50: bool) -> int:
    sim = CharacterSimulation(starting_pity, lost_previous_50_50)
    return sim.c(n)

def r(n: int, starting_pity: int, lost_previous_75_25: bool, fate_points: int) -> int:
    sim = WeaponSimulation(starting_pity, lost_previous_75_25, fate_points)
    return sim.r(n)


def optimal(pulls: int) -> float:
    primos = pulls * 160
    total = 0.0

    for gained, cost in [(6480+1600, 99.99), (3280+600, 49.99), (1980+260, 29.99), (980+110, 14.99), (300+30, 4.99)]:
        amount = primos // gained

        total += amount * cost
        primos -= amount * gained
    
    total += ceil(primos / 60) * 0.99

    return total


class GachaCog(ACog):
    async def __ainit__(self) -> None:
        self.gc = pygsheets.authorize(service_file=self.bot.settings.google_credentials)

        print(self.gc)

    @comms.command()
    async def spent(self, ctx: ArcContext) -> None:
        sheet = self.gc.open_by_key("175PMTH9KkWQfL08VLPvrZaBJfeFArToYZztikW2ky1U")

        summary: pygsheets.Worksheet = sheet.worksheet()

        total = summary.get_value("B1")
        per_day = summary.get_value("B2")
        duration = summary.get_value("B4")

        embed = ctx.generateEmbed("Money Spent on Gacha", f"<@186185272302501888> has spent {total} on gacha.")

        embed.add_field(name="Total", value=total)
        embed.add_field(name="Total Time", value=f"{duration} weeks")
        embed.add_field(name="Per Day", value=per_day)

        await ctx.reply(embed=embed)
    
    # @comms.hybrid_command()
    # async def pulls_old(self, ctx: ArcContext,
    #     copies: int = comms.parameter(default=1, description="the target constellation level of the character"),
    #     starting_pity: int = comms.parameter(default=0, description="the pity you start at"),
    #     lost_previous: bool = comms.parameter(default=False, description="whether or not the previous 50/50 or 75/25 was lost"),
    #     units: str = comms.parameter(default="Pulls", description="what units to return the data in"),
    #     banner: str = comms.parameter(default="Character", description="which banner type to simulate"),
    #     fate_points: int = comms.parameter(default=0, description="the number of fate points you start with, useless with regards to the character banner")) -> None:
    #     """Calculates the number of pulls to obtain a specific constellation level of a 5* character"""
    #     if units not in ["Pulls", "Optimal USD", "Minimal USD"]:
    #         await ctx.replyEmbed("Invalid Units", f"{units} is not a valid unit type.")
    #         return

    #     if banner not in ["Character", "Weapon"]:
    #         await ctx.replyEmbed("Invalid Banner", f"{banner} is not a valid banner.")
    #         return

    #     match banner:
    #         case "Weapon":
    #             copies = min(max(copies, 1), 5)
    #         case "Character":
    #             copies = min(max(copies, 1), 7)

    #     def convert(value: int) -> float:
    #         match units:
    #             case "Pulls":
    #                 return float(value)
    #             case "Minimal USD":
    #                 return optimal(value)
    #             case "Optimal USD":
    #                 return 99.99 * value * 160 / 8080
    #         return -1

    #     async with ctx.typing():
    #         match banner:
    #             case "Character":
    #                 data = [convert(c(copies - 1, starting_pity, lost_previous)) for _ in range(10000)]
    #             case "Weapon":
    #                 data = [convert(r(copies, starting_pity, lost_previous, fate_points)) for _ in range(10000)]
    #             case _:
    #                 data = []

    #         lines = []

    #         lines.append(f"Average: {sum(data) / len(data):.2f}")
    #         lines.append(f"Standard Deviation: {statistics.stdev(data):.2f}")
    #         lines.append(f"Percentiles:")

    #         for i, value in enumerate(statistics.quantiles(data, n=10)):
    #             lines.append(f"    {(i + 1) * 10}: {value:.2f}")

    #         lines.append(f"    99: {statistics.quantiles(data, n=100)[-1]:.2f}")

    #         block = '\n'.join(lines)

    #         await ctx.replyEmbed(f"Pulls to get **{copies}** copies on the {banner} banner", f"Copies: **{copies}**, Banner: **{banner}**, Starting Pity: **{starting_pity}**, Guaranteed: **{lost_previous}**, Units: **{units}**, Fate Points: **{fate_points}**\n```{block}```")
    
    # @pulls_old.autocomplete('units')
    # async def units_autocomplete(self, interaction: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    #     choices = ["Pulls", "Optimal USD", "Minimal USD"]

    #     return [discord.app_commands.Choice(name=choice, value=choice) for choice in choices if current.lower() in choice.lower()]
    
    # @pulls_old.autocomplete('banner')
    # async def banner_autocomplete(self, interaction: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    #     choices = ["Character", "Weapon"]

    #     return [discord.app_commands.Choice(name=choice, value=choice) for choice in choices if current.lower() in choice.lower()]

    @property
    def color(self) -> Optional[discord.Color]:
        return discord.Color(0xd834eb)

    @property
    def author(self) -> str:
        return 'Harlot#0001'
