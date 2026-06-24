from __future__ import annotations

from dataclasses import dataclass

from models import BattlePrediction, PokemonSummary, TypeMatchup
from pokeapi import PokeApiClient


@dataclass(frozen=True)
class _BattleSide:
    pokemon: PokemonSummary
    best_matchups: list[TypeMatchup]
    score: float

    @property
    def best_multiplier(self) -> float:
        return max(matchup.multiplier for matchup in self.best_matchups)


def predict_battle(
    first: PokemonSummary,
    second: PokemonSummary,
    client: PokeApiClient,
) -> BattlePrediction:
    first_side = _build_side(first, second, client)
    second_side = _build_side(second, first, client)
    winner_side, loser_side = (
        (first_side, second_side)
        if first_side.score >= second_side.score
        else (second_side, first_side)
    )

    score_gap = abs(first_side.score - second_side.score)
    score_total = max(first_side.score + second_side.score, 0.01)
    confidence = min(0.95, 0.55 + (score_gap / score_total) * 0.75)

    reasons = _reasons(winner_side, loser_side)
    recommended = sorted(
        matchup.attacker_type
        for matchup in winner_side.best_matchups
        if matchup.multiplier == winner_side.best_multiplier
    )
    return BattlePrediction(
        winner=winner_side.pokemon.name,
        confidence=round(confidence, 2),
        reasons=reasons,
        caveats=[
            "This is a simplified prediction, not a competitive battle simulation.",
            "Moves, abilities, held items, levels, natures and battle rules are not considered.",
        ],
        recommended_attack_types=recommended,
    )


def _build_side(
    attacker: PokemonSummary,
    defender: PokemonSummary,
    client: PokeApiClient,
) -> _BattleSide:
    matchups = [
        client.get_type_matchup(attacker_type, defender.types)
        for attacker_type in attacker.types
    ]
    best_multiplier = max(matchup.multiplier for matchup in matchups)
    offense = max(attacker.stat("attack"), attacker.stat("special-attack"))
    target_defense = max(
        1,
        (defender.stat("defense") + defender.stat("special-defense")) / 2,
    )
    speed_ratio = attacker.stat("speed") / max(
        1,
        attacker.stat("speed") + defender.stat("speed"),
    )
    score = best_multiplier * 0.5 + (offense / target_defense) * 0.35 + speed_ratio * 0.3
    return _BattleSide(pokemon=attacker, best_matchups=matchups, score=score)


def _reasons(winner: _BattleSide, loser: _BattleSide) -> list[str]:
    reasons: list[str] = []
    best_types = sorted(
        matchup.attacker_type
        for matchup in winner.best_matchups
        if matchup.multiplier == winner.best_multiplier
    )
    if winner.best_multiplier > 1:
        reasons.append(
            f"{', '.join(best_types).title()} attacks have a "
            f"{winner.best_multiplier:g}x type multiplier."
        )
    elif winner.best_multiplier < 1:
        reasons.append(
            f"Its best same-type attacks only have a {winner.best_multiplier:g}x multiplier."
        )
    else:
        reasons.append("Its best same-type attacks do neutral damage.")

    winner_speed = winner.pokemon.stat("speed")
    loser_speed = loser.pokemon.stat("speed")
    if winner_speed > loser_speed:
        reasons.append(
            f"{winner.pokemon.name.title()} is faster ({winner_speed} vs {loser_speed})."
        )
    elif winner_speed < loser_speed:
        reasons.append(
            f"{winner.pokemon.name.title()} is slower, so type and offensive stats "
            "carry the result."
        )

    winner_offense = max(
        winner.pokemon.stat("attack"),
        winner.pokemon.stat("special-attack"),
    )
    loser_offense = max(
        loser.pokemon.stat("attack"),
        loser.pokemon.stat("special-attack"),
    )
    if winner_offense > loser_offense:
        reasons.append(
            f"It also has the higher best offensive stat ({winner_offense} vs {loser_offense})."
        )
    return reasons
