from __future__ import annotations

from typing import Any

from langchain_core.tools import BaseTool, tool

from comparison import compare_pokemon as build_comparison
from pokeapi import PokeApiClient


def build_tools(client: PokeApiClient) -> list[BaseTool]:
    @tool
    def get_pokemon(name: str) -> dict[str, Any]:
        """Get normalized PokeAPI facts for one Pokémon."""
        return client.get_pokemon(name).model_dump()

    @tool
    def get_type(type_name: str) -> dict[str, Any]:
        """Get offensive and defensive damage relations for one Pokémon type."""
        return client.get_type(type_name).model_dump()

    @tool
    def compare_pokemon(first: str, second: str) -> dict[str, Any]:
        """Compare the base stats and types of two Pokémon."""
        comparison = build_comparison(
            client.get_pokemon(first),
            client.get_pokemon(second),
        )
        return comparison.model_dump()

    @tool
    def get_evolution_chain(name: str) -> dict[str, Any]:
        """Get every evolution path that contains the requested Pokémon species."""
        return client.get_evolution_chain(name).model_dump()

    @tool
    def get_type_matchup(attacker_type: str, defender_types: list[str]) -> dict[str, Any]:
        """Calculate the damage multiplier for one attacking type against defender types."""
        return client.get_type_matchup(attacker_type, defender_types).model_dump()

    return [
        get_pokemon,
        get_type,
        compare_pokemon,
        get_evolution_chain,
        get_type_matchup,
    ]
