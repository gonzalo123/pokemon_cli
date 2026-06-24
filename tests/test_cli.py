import click
import pytest

from app import cli as cli_module


def test_enter_accepts_best_pokemon_suggestion(client, monkeypatch) -> None:
    monkeypatch.setattr(cli_module.Prompt, "ask", lambda *args, **kwargs: "charizard")

    pokemon = cli_module._resolve_pokemon(client, "charizrad", interactive=True)

    assert pokemon.name == "charizard"


def test_user_can_type_a_different_pokemon(client, monkeypatch) -> None:
    monkeypatch.setattr(cli_module.Prompt, "ask", lambda *args, **kwargs: "venusaur")

    pokemon = cli_module._resolve_pokemon(client, "charizrad", interactive=True)

    assert pokemon.name == "venusaur"


def test_user_can_cancel_pokemon_correction(client, monkeypatch) -> None:
    monkeypatch.setattr(cli_module.Prompt, "ask", lambda *args, **kwargs: "q")

    with pytest.raises(click.Abort):
        cli_module._resolve_pokemon(client, "charizrad", interactive=True)
