from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any
from urllib.parse import urlparse

import httpx

from app.models import (
    EvolutionChain,
    PokemonStat,
    PokemonSuggestion,
    PokemonSummary,
    TypeMatchup,
    TypeSummary,
)

POKEAPI_BASE_URL = "https://pokeapi.co/api/v2"
_IDENTIFIER = re.compile(r"^[a-z0-9-]+$")
_POKEMON_INDEX_PATH = "/pokemon-species?limit=100000&offset=0"


class PokeApiError(RuntimeError):
    """Base error raised by the small PokeAPI adapter."""


class PokeApiNotFound(PokeApiError):
    """Raised when PokeAPI does not know a requested resource."""

    def __init__(
        self,
        message: str,
        *,
        resource: str | None = None,
        suggestions: list[PokemonSuggestion] | None = None,
    ) -> None:
        super().__init__(message)
        self.resource = resource
        self.suggestions = suggestions or []


def normalize_identifier(value: str) -> str:
    ascii_value = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )
    normalized = re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")
    if not normalized or not _IDENTIFIER.fullmatch(normalized):
        raise PokeApiError(f"Invalid Pokémon or type name: {value!r}")
    return normalized


class PokeApiClient:
    def __init__(
        self,
        *,
        timeout: float = 10.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._pokemon_names: list[str] | None = None
        self.http = httpx.Client(
            base_url=POKEAPI_BASE_URL,
            timeout=timeout,
            transport=transport,
            headers={"User-Agent": "pokemon-professor/0.1"},
        )

    def close(self) -> None:
        self.http.close()

    def __enter__(self) -> PokeApiClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def get_pokemon(self, name: str) -> PokemonSummary:
        pokemon = normalize_identifier(name)
        try:
            payload = self._get(f"/pokemon/{pokemon}")
        except PokeApiNotFound as error:
            suggestions = self.search_pokemon(pokemon, limit=3, cutoff=0.7)
            if suggestions:
                candidates = ", ".join(item.name for item in suggestions)
                raise PokeApiNotFound(
                    f"PokeAPI does not know {pokemon!r}. Did you mean: {candidates}?",
                    resource=pokemon,
                    suggestions=suggestions,
                ) from error
            raise
        return PokemonSummary(
            id=payload["id"],
            name=payload["name"],
            types=[
                item["type"]["name"]
                for item in sorted(payload["types"], key=lambda item: item["slot"])
            ],
            height=payload["height"],
            weight=payload["weight"],
            base_experience=payload.get("base_experience"),
            stats=[
                PokemonStat(name=item["stat"]["name"], value=item["base_stat"])
                for item in payload["stats"]
            ],
            abilities=[
                item["ability"]["name"]
                for item in sorted(payload["abilities"], key=lambda item: item["slot"])
                if not item.get("is_hidden", False)
            ],
        )

    def search_pokemon(
        self,
        query: str,
        *,
        limit: int = 5,
        cutoff: float = 0.55,
    ) -> list[PokemonSuggestion]:
        """Rank Pokémon names locally using an in-memory PokeAPI species index."""
        normalized_query = normalize_identifier(query)
        compact_query = normalized_query.replace("-", "")
        suggestions = []
        for name in self._get_pokemon_names():
            compact_name = name.replace("-", "")
            score = SequenceMatcher(None, compact_query, compact_name).ratio()
            if compact_name.startswith(compact_query) or compact_query.startswith(compact_name):
                score = min(1.0, score + 0.08)
            if score >= cutoff:
                suggestions.append(PokemonSuggestion(name=name, score=round(score, 3)))
        return sorted(suggestions, key=lambda item: (-item.score, item.name))[:limit]

    def _get_pokemon_names(self) -> list[str]:
        if self._pokemon_names is None:
            payload = self._get(_POKEMON_INDEX_PATH)
            self._pokemon_names = [item["name"] for item in payload["results"]]
        return self._pokemon_names

    def get_type(self, type_name: str) -> TypeSummary:
        name = normalize_identifier(type_name)
        payload = self._get(f"/type/{name}")
        relations = payload["damage_relations"]

        def names(key: str) -> list[str]:
            return sorted(item["name"] for item in relations[key])

        return TypeSummary(
            name=payload["name"],
            double_damage_to=names("double_damage_to"),
            half_damage_to=names("half_damage_to"),
            no_damage_to=names("no_damage_to"),
            double_damage_from=names("double_damage_from"),
            half_damage_from=names("half_damage_from"),
            no_damage_from=names("no_damage_from"),
        )

    def get_type_matchup(
        self,
        attacker_type: str,
        defender_types: list[str],
    ) -> TypeMatchup:
        attacker = self.get_type(attacker_type)
        defenders = [normalize_identifier(item) for item in defender_types]
        multiplier = 1.0
        for defender in defenders:
            if defender in attacker.no_damage_to:
                multiplier = 0.0
                break
            if defender in attacker.double_damage_to:
                multiplier *= 2
            elif defender in attacker.half_damage_to:
                multiplier *= 0.5
        return TypeMatchup(
            attacker_type=attacker.name,
            defender_types=defenders,
            multiplier=multiplier,
        )

    def get_weaknesses(self, pokemon: PokemonSummary | str) -> dict[str, float]:
        summary = self.get_pokemon(pokemon) if isinstance(pokemon, str) else pokemon
        multiplier_by_type: dict[str, float] = {}
        for defender_type in summary.types:
            relations = self.get_type(defender_type)
            candidates = (
                set(relations.double_damage_from)
                | set(relations.half_damage_from)
                | set(relations.no_damage_from)
                | set(multiplier_by_type)
            )
            for attacker in candidates:
                current = multiplier_by_type.get(attacker, 1.0)
                if attacker in relations.no_damage_from:
                    multiplier_by_type[attacker] = 0.0
                elif attacker in relations.double_damage_from:
                    multiplier_by_type[attacker] = current * 2
                elif attacker in relations.half_damage_from:
                    multiplier_by_type[attacker] = current * 0.5
                else:
                    multiplier_by_type.setdefault(attacker, current)
        return dict(
            sorted(
                (
                    (type_name, multiplier)
                    for type_name, multiplier in multiplier_by_type.items()
                    if multiplier > 1
                ),
                key=lambda item: (-item[1], item[0]),
            )
        )

    def get_evolution_chain(self, name: str) -> EvolutionChain:
        pokemon = normalize_identifier(name)
        species = self._get(f"/pokemon-species/{pokemon}")
        chain_payload = self._get_url(species["evolution_chain"]["url"])
        paths = self._evolution_paths(chain_payload["chain"])
        return EvolutionChain(pokemon=pokemon, paths=paths)

    def _evolution_paths(self, node: dict[str, Any]) -> list[list[str]]:
        name = node["species"]["name"]
        children = node.get("evolves_to", [])
        if not children:
            return [[name]]
        return [[name, *path] for child in children for path in self._evolution_paths(child)]

    def _get_url(self, url: str) -> dict[str, Any]:
        parsed = urlparse(url)
        expected = urlparse(POKEAPI_BASE_URL)
        if parsed.scheme != expected.scheme or parsed.netloc != expected.netloc:
            raise PokeApiError("PokeAPI returned an unexpected external URL")
        path = parsed.path.removeprefix("/api/v2")
        return self._get(path)

    def _get(self, path: str) -> dict[str, Any]:
        try:
            response = self.http.get(path)
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            if error.response.status_code == 404:
                resource = path.rstrip("/").split("/")[-1]
                raise PokeApiNotFound(
                    f"PokeAPI does not know {resource!r}",
                    resource=resource,
                ) from error
            raise PokeApiError(
                f"PokeAPI returned HTTP {error.response.status_code}"
            ) from error
        except httpx.HTTPError as error:
            raise PokeApiError(f"Could not reach PokeAPI: {error}") from error

        return response.json()
