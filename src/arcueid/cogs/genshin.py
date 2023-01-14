from abc import ABC, abstractmethod
import bisect
from collections import defaultdict
from dataclasses import dataclass
from typing import Generic, Mapping, TypeVar

from functools import lru_cache
from itertools import count

import discord
import discord.ext.commands as comms

from .abc import ACog

from ..context import ArcContext

__all__ = [
    "GenshinCog"
]


class SimulationState(ABC):
    def meets_goal(self, goal: "SimulationState") -> bool:
        ...


T = TypeVar("T", bound=SimulationState)


class Simulation(ABC, Generic[T]):
    def __init__(self, initial: T) -> None:
        self.states = defaultdict(float)

        self.states[initial] = 1.0
    
    def simulate_to_goal(self, goal: T) -> Mapping[int, float]:
        final = defaultdict(float)

        for i in count():
            if len(self.states) == 0:
                break

            next_states: defaultdict[T, float] = defaultdict(float)

            for state, probability in self.states.items():
                if probability > 0:
                    if state.meets_goal(goal):
                        final[i] += probability
                    else:
                        for next_state, other_probability in self.transition(state).items():
                            next_states[next_state] += probability * other_probability
            
            self.states = next_states
        
        return final
    
    def simulate_steps(self, steps: int) -> Mapping[T, float]:
        for i in range(steps):
            if len(self.states) == 0:
                break

            next_states: defaultdict[T, float] = defaultdict(float)

            for state, probability in self.states.items():
                if probability > 0:
                    for next_state, other_probability in self.transition(state).items():
                        next_states[next_state] += probability * other_probability
            
            self.states = next_states
        
        return self.states

    @abstractmethod
    def transition(self, state: T) -> dict[T, float]:
        ...


@dataclass(frozen=True, unsafe_hash=True)
class CharacterState(SimulationState):
    pity: int
    limited: int
    guaranteed: bool

    def meets_goal(self, goal: "CharacterState") -> bool:
        return self.limited >= goal.limited

    @property
    def no_drop(self) -> 'CharacterState':
        return CharacterState(self.pity + 1, self.limited, self.guaranteed)
    
    @property
    def limited_drop(self) -> 'CharacterState':
        return CharacterState(0, self.limited + 1, False)
    
    @property
    def nonlimited_drop(self) -> 'CharacterState':
        assert not self.guaranteed

        return CharacterState(0, self.limited, True)


class CharacterSimulation(Simulation[CharacterState]):
    def transition(self, state: CharacterState) -> dict[CharacterState, float]:
        five_star_p = min(0.006 + 0.06 * max(0, state.pity - 72), 1.0)

        outputs = {state.no_drop: 1.0 - five_star_p}

        if state.guaranteed:
            outputs[state.limited_drop] = five_star_p
        else:
            outputs[state.limited_drop] = five_star_p * 0.5
            outputs[state.nonlimited_drop] = five_star_p * 0.5
        
        return outputs


@dataclass(frozen=True, unsafe_hash=True)
class WeaponState(SimulationState):
    pity: int
    target: int
    limited_guaranteed: bool
    fate_points: int

    def meets_goal(self, goal: "WeaponState") -> bool:
        return self.target >= goal.target
    
    @property
    def no_drop(self) -> 'WeaponState':
        return WeaponState(self.pity + 1, self.target, self.limited_guaranteed, self.fate_points)
    
    @property
    def target_drop(self) -> 'WeaponState':
        return WeaponState(0, self.target + 1, False, 0)
    
    @property
    def limited_drop(self) -> 'WeaponState':
        return WeaponState(0, self.target, False, self.fate_points + 1)
    
    @property
    def nonlimited_drop(self) -> 'WeaponState':
        return WeaponState(0, self.target, True, self.fate_points + 1)


class WeaponSimulation(Simulation[WeaponState]):
    def transition(self, state: WeaponState) -> dict[WeaponState, float]:
        five_star_p = min(0.007 + 0.07 * max(0, state.pity - 62), 1.0)

        outputs = {state.no_drop: 1.0 - five_star_p}

        if state.fate_points >= 2:
            outputs[state.target_drop] = five_star_p
        else:
            if state.limited_guaranteed:
                outputs[state.target_drop] = five_star_p * 0.5
                outputs[state.limited_drop] = five_star_p * 0.5
            else:
                outputs[state.nonlimited_drop] = five_star_p * 0.25
                outputs[state.target_drop] = five_star_p * 0.75 * 0.5
                outputs[state.limited_drop] = five_star_p * 0.75 * 0.5
        
        return outputs


def to_cumulative(probabilities: Mapping[int, float]) -> Mapping[int, float]:
    cumulative = defaultdict(float)

    for i in range(1, max(probabilities) + 1):
        cumulative[i] += probabilities.get(i, 0) + cumulative[i-1]
    
    return cumulative


class Quantiles:
    def __init__(self, cumulative: Mapping[int, float]) -> None:
        self.probabilities = [cumulative[i] for i in range(max(cumulative))]
    
    def get_quantile(self, quantile: float) -> float:
        assert 0 < quantile <= 1

        index = bisect.bisect(self.probabilities, quantile)

        value = self.probabilities[index] if index + 1 < len(self.probabilities) else 1
        next_value = self.probabilities[index + 1] if index < len(self.probabilities) else 1

        if next_value == value:
            return index

        return (quantile - self.probabilities[index]) / (next_value - self.probabilities[index]) + index


@lru_cache()
def pulls_character(initial: CharacterState, constellations: int) -> Mapping[int, float]:
    sim = CharacterSimulation(initial)
    return sim.simulate_to_goal(CharacterState(0, constellations + 1, False))


@lru_cache()
def pulls_weapon(initial: WeaponState, refinements: int) -> Mapping[int, float]:
    sim = WeaponSimulation(initial)
    return sim.simulate_to_goal(WeaponState(0, refinements, False, 0))


class GenshinCog(ACog):
    @comms.hybrid_group()
    async def pulls(self, ctx: ArcContext) -> None:
        ...
    
    @pulls.command()
    async def character(self, ctx: ArcContext, constellations: int, pull_count: int, starting_pity: int = 0, guaranteed: bool = False) -> None:
        if constellations > 6 or constellations < 0:
            await ctx.replyEmbed("Invalid Constellations", "Input a valid constellation count", error=True)
            return
        
        if pull_count <= 0:
            await ctx.replyEmbed("Invalid Pull Count", "Input a valid pull count", error=True)
            return

        if starting_pity < 0:
            await ctx.replyEmbed("Invalid Starting Pity", "Input a valid starting pity", error=True)
            return

        async with ctx.typing():
            results = pulls_character(CharacterState(starting_pity, 0, guaranteed), constellations)

            cumulative =  to_cumulative(results)
            
            await ctx.replyEmbed(f"Chances of C{constellations} by {pull_count} pulls", f"The chance of getting C{constellations} by {pull_count} pulls is exactly **{cumulative.get(pull_count, 1)*100:.2f}%**")
    
    @pulls.command()
    async def weapon(self, ctx: ArcContext, refinements: int, pull_count: int, starting_pity: int = 0, guaranteed: bool = False, fate_points: int = 0) -> None:
        if refinements > 5 or refinements < 1:
            await ctx.replyEmbed("Invalid Refinements", "Input a valid refinement count", error=True)
            return
        
        if pull_count <= 0:
            await ctx.replyEmbed("Invalid Pull Count", "Input a valid pull count", error=True)
            return
        
        if fate_points > 2 or fate_points < 0:
            await ctx.replyEmbed("Invalid Fate Point Count", "Input a valid fate point count", error=True)
            return

        if starting_pity < 0:
            await ctx.replyEmbed("Invalid Starting Pity", "Input a valid starting pity", error=True)
            return

        async with ctx.typing():
            results = pulls_weapon(WeaponState(starting_pity, 0, guaranteed, fate_points), refinements)

            cumulative =  to_cumulative(results)
            
            await ctx.replyEmbed(f"Chances of R{refinements} by {pull_count} pulls", f"The chance of getting R{refinements} by {pull_count} pulls is exactly **{cumulative.get(pull_count, 1)*100:.2f}%**")
    
    @pulls.command()
    async def combined(self, ctx: ArcContext, constellations: int, refinements: int, pull_count: int, starting_pity_character: int = 0, guaranteed_character: bool = False, starting_pity_weapon: int = 0, guaranteed_weapon: bool = False, fate_points: int = 0):
        if constellations > 6 or constellations < 0:
            await ctx.replyEmbed("Invalid Constellations", "Input a valid constellation count", error=True)
            return
        
        if refinements > 5 or refinements < 1:
            await ctx.replyEmbed("Invalid Refinements", "Input a valid refinement count", error=True)
            return
        
        if pull_count <= 0:
            await ctx.replyEmbed("Invalid Pull Count", "Input a valid pull count", error=True)
            return
        
        if fate_points > 2 or fate_points < 0:
            await ctx.replyEmbed("Invalid Fate Point Count", "Input a valid fate point count", error=True)
            return

        if starting_pity_character < 0:
            await ctx.replyEmbed("Invalid Starting Pity - Character", "Input a valid starting pity - character", error=True)
            return

        if starting_pity_weapon < 0:
            await ctx.replyEmbed("Invalid Starting Pity - Weapon", "Input a valid starting pity - weapon", error=True)
            return

        async with ctx.typing():
            weapon = pulls_weapon(WeaponState(starting_pity_weapon, 0, guaranteed_weapon, fate_points), refinements)
            character = pulls_character(CharacterState(starting_pity_character, 0, guaranteed_character), constellations)

            final = defaultdict(float)

            for w in weapon:
                for c in character:
                    final[w + c] += weapon[w] * character[c]
            
            cumulative = to_cumulative(final)

            await ctx.replyEmbed(f"Chances of C{constellations}R{refinements} by {pull_count} pulls", f"The chance of getting C{constellations}R{refinements} by {pull_count} pulls is exactly **{cumulative.get(pull_count, 1)*100:.2f}%**")
    
    @pulls.command()
    async def percentiles(self, ctx: ArcContext, constellations: int | None = None, refinements: int | None = None):
        if constellations is None and refinements is None:
            await ctx.replyEmbed("Invalid Parameters", "Input either a constellation count or a refinement count or both", error=True)
            return

        if constellations is not None:
            if constellations > 6 or constellations < 0:
                await ctx.replyEmbed("Invalid Constellations", "Input a valid constellation count", error=True)
                return
        
        if refinements is not None:
            if refinements > 5 or refinements < 1:
                await ctx.replyEmbed("Invalid Refinements", "Input a valid refinement count", error=True)
                return

        async with ctx.typing():
            if refinements is not None:
                weapon = pulls_weapon(WeaponState(0, 0, False, 0), refinements)
            else:
                weapon = {0: 1}

            if constellations is not None:
                character = pulls_character(CharacterState(0, 0, False), constellations)
            else:
                character = {0: 1}

            final = defaultdict(float)

            for w in weapon:
                for c in character:
                    final[w + c] += weapon[w] * character[c]
            
            cumulative = to_cumulative(final)

            quantiles = Quantiles(cumulative)

            percentiles = (0.1, 1, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 99, 99.9, 100)
            percentile_values = map(lambda p: quantiles.get_quantile(p / 100), percentiles)

            percentile_summary = "\n".join([f"{percentile}".rjust(4, " ") + f": {value:.2f}" for percentile, value in zip(percentiles, percentile_values)])

            cr_string = (f"C{constellations}" if constellations is not None else "") + (f"R{refinements}" if refinements is not None else "")

            await ctx.replyEmbed(f"Percentiles for {cr_string}", f"```{percentile_summary}```")


    @property
    def color(self) -> discord.Color | None:
        return discord.Color(0xd834eb)

    @property
    def author(self) -> str:
        return 'Harlot#0001'
