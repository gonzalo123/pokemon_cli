from __future__ import annotations

from pydantic import BaseModel, Field


class PokemonStat(BaseModel):
    name: str
    value: int


class PokemonSummary(BaseModel):
    id: int
    name: str
    types: list[str]
    height: int = Field(description="Height in decimetres, as returned by PokeAPI")
    weight: int = Field(description="Weight in hectograms, as returned by PokeAPI")
    base_experience: int | None
    stats: list[PokemonStat]
    abilities: list[str]

    def stat(self, name: str) -> int:
        return next((stat.value for stat in self.stats if stat.name == name), 0)

    @property
    def total_stats(self) -> int:
        return sum(stat.value for stat in self.stats)


class PokemonComparison(BaseModel):
    first: PokemonSummary
    second: PokemonSummary
    stat_winners: dict[str, str]
    total_first: int
    total_second: int


class TypeSummary(BaseModel):
    name: str
    double_damage_to: list[str]
    half_damage_to: list[str]
    no_damage_to: list[str]
    double_damage_from: list[str]
    half_damage_from: list[str]
    no_damage_from: list[str]


class TypeMatchup(BaseModel):
    attacker_type: str
    defender_types: list[str]
    multiplier: float


class EvolutionChain(BaseModel):
    pokemon: str
    paths: list[list[str]]


class PokemonSuggestion(BaseModel):
    name: str
    score: float = Field(ge=0, le=1)


class BattlePrediction(BaseModel):
    winner: str
    confidence: float = Field(ge=0, le=1)
    reasons: list[str]
    caveats: list[str]
    recommended_attack_types: list[str]
