import pytest
from pydantic import ValidationError

from app.models import BattlePrediction, PokemonStat, PokemonSummary


def test_summary_exposes_stats_and_total() -> None:
    pokemon = PokemonSummary(
        id=25,
        name="pikachu",
        types=["electric"],
        height=4,
        weight=60,
        base_experience=112,
        stats=[PokemonStat(name="speed", value=90), PokemonStat(name="hp", value=35)],
        abilities=["static"],
    )

    assert pokemon.stat("speed") == 90
    assert pokemon.stat("missing") == 0
    assert pokemon.total_stats == 125


def test_battle_confidence_is_bounded() -> None:
    with pytest.raises(ValidationError):
        BattlePrediction(
            winner="pikachu",
            confidence=1.2,
            reasons=[],
            caveats=[],
            recommended_attack_types=[],
        )
