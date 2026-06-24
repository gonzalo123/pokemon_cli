from __future__ import annotations

from typing import Any

import httpx
import pytest

from app.pokeapi import PokeApiClient


def pokemon_payload(
    name: str,
    pokemon_id: int,
    types: list[str],
    stats: dict[str, int],
) -> dict[str, Any]:
    return {
        "id": pokemon_id,
        "name": name,
        "types": [
            {"slot": position, "type": {"name": type_name}}
            for position, type_name in enumerate(types, start=1)
        ],
        "height": 17,
        "weight": 905,
        "base_experience": 240,
        "stats": [
            {"base_stat": value, "stat": {"name": stat_name}}
            for stat_name, value in stats.items()
        ],
        "abilities": [
            {"slot": 1, "is_hidden": False, "ability": {"name": "blaze"}},
            {"slot": 3, "is_hidden": True, "ability": {"name": "solar-power"}},
        ],
    }


POKEMON = {
    "charizard": pokemon_payload(
        "charizard",
        6,
        ["fire", "flying"],
        {
            "hp": 78,
            "attack": 84,
            "defense": 78,
            "special-attack": 109,
            "special-defense": 85,
            "speed": 100,
        },
    ),
    "venusaur": pokemon_payload(
        "venusaur",
        3,
        ["grass", "poison"],
        {
            "hp": 80,
            "attack": 82,
            "defense": 83,
            "special-attack": 100,
            "special-defense": 100,
            "speed": 80,
        },
    ),
    "gengar": pokemon_payload(
        "gengar",
        94,
        ["ghost", "poison"],
        {
            "hp": 60,
            "attack": 65,
            "defense": 60,
            "special-attack": 130,
            "special-defense": 75,
            "speed": 110,
        },
    ),
    "alakazam": pokemon_payload(
        "alakazam",
        65,
        ["psychic"],
        {
            "hp": 55,
            "attack": 50,
            "defense": 45,
            "special-attack": 135,
            "special-defense": 95,
            "speed": 120,
        },
    ),
}

TYPE_RELATIONS = {
    "fire": {
        "double_damage_to": ["grass"],
        "half_damage_to": ["fire", "water"],
        "no_damage_to": [],
        "double_damage_from": ["water"],
        "half_damage_from": ["grass", "fire"],
        "no_damage_from": [],
    },
    "flying": {
        "double_damage_to": ["grass"],
        "half_damage_to": [],
        "no_damage_to": [],
        "double_damage_from": ["electric"],
        "half_damage_from": ["grass"],
        "no_damage_from": ["ground"],
    },
    "grass": {
        "double_damage_to": ["water"],
        "half_damage_to": ["fire", "flying"],
        "no_damage_to": [],
        "double_damage_from": ["fire", "flying"],
        "half_damage_from": ["water", "electric"],
        "no_damage_from": [],
    },
    "poison": {
        "double_damage_to": ["grass"],
        "half_damage_to": ["poison"],
        "no_damage_to": [],
        "double_damage_from": ["psychic", "ground"],
        "half_damage_from": ["grass", "poison"],
        "no_damage_from": [],
    },
}


@pytest.fixture
def client() -> PokeApiClient:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.startswith("/api/v2/pokemon/"):
            name = path.rstrip("/").split("/")[-1]
            payload = POKEMON.get(name)
        elif path == "/api/v2/pokemon-species":
            payload = {
                "results": [
                    {"name": name, "url": f"https://pokeapi.co/api/v2/pokemon/{name}/"}
                    for name in POKEMON
                ]
            }
        elif path.startswith("/api/v2/type/"):
            name = path.rstrip("/").split("/")[-1]
            relations = TYPE_RELATIONS.get(name)
            payload = (
                {
                    "name": name,
                    "damage_relations": {
                        key: [{"name": item} for item in values]
                        for key, values in relations.items()
                    },
                }
                if relations
                else None
            )
        elif path == "/api/v2/pokemon-species/eevee":
            payload = {
                "evolution_chain": {
                    "url": "https://pokeapi.co/api/v2/evolution-chain/67/"
                }
            }
        elif path == "/api/v2/evolution-chain/67/":
            payload = {
                "chain": {
                    "species": {"name": "eevee"},
                    "evolves_to": [
                        {"species": {"name": "vaporeon"}, "evolves_to": []},
                        {"species": {"name": "jolteon"}, "evolves_to": []},
                    ],
                }
            }
        else:
            payload = None
        if payload is None:
            return httpx.Response(404, request=request, json={"detail": "Not found"})
        return httpx.Response(200, request=request, json=payload)

    api_client = PokeApiClient(transport=httpx.MockTransport(handler))
    yield api_client
    api_client.close()
