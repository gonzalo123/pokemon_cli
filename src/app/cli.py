from __future__ import annotations

import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from app.agent import (
    ask_agent,
    ask_mock,
    explain_comparison,
    mock_comparison_explanation,
    refine_battle_prediction,
)
from app.battle import predict_battle
from app.comparison import compare_pokemon
from app.config import Settings
from app.llm import LlmConfigurationError
from app.models import PokemonSummary
from app.pokeapi import PokeApiClient, PokeApiError, PokeApiNotFound
from app.render import render_battle, render_comparison, render_pokemon

console = Console()


@click.group()
def cli() -> None:
    """A small Pokémon professor backed by PokeAPI."""


@cli.command()
@click.argument("name")
def pokemon(name: str) -> None:
    """Show deterministic PokeAPI facts for one Pokémon."""
    settings = Settings()
    try:
        with _client(settings) as client:
            render_pokemon(_resolve_pokemon(client, name), console)
    except PokeApiError as error:
        raise click.ClickException(str(error)) from error


@cli.command()
@click.argument("query")
@click.option("--limit", default=5, show_default=True, type=click.IntRange(1, 20))
def search(query: str, limit: int) -> None:
    """Find Pokémon names with deterministic fuzzy matching."""
    settings = Settings()
    try:
        with _client(settings) as client:
            suggestions = client.search_pokemon(query, limit=limit, cutoff=0)
            if not suggestions:
                raise click.ClickException(f"No Pokémon names found for {query!r}")
            for suggestion in suggestions:
                console.print(
                    f"[bold cyan]{suggestion.name}[/] "
                    f"[dim]{suggestion.score:.0%} similarity[/]"
                )
    except PokeApiError as error:
        raise click.ClickException(str(error)) from error


@cli.command()
@click.argument("first")
@click.argument("second")
@click.option("--explain", is_flag=True, help="Add a short reasoning-layer explanation.")
@click.option("--mock", is_flag=True, help="Explain locally without calling an LLM.")
def compare(first: str, second: str, explain: bool, mock: bool) -> None:
    """Compare two Pokémon using their PokeAPI base stats."""
    if mock and not explain:
        raise click.UsageError("--mock only has an effect together with --explain")
    settings = Settings()
    try:
        with _client(settings) as client:
            comparison = compare_pokemon(
                _resolve_pokemon(client, first),
                _resolve_pokemon(client, second),
            )
            render_comparison(comparison, console)
            if explain:
                text = (
                    mock_comparison_explanation(comparison)
                    if mock
                    else explain_comparison(comparison, settings)
                )
                console.print(Panel(text, title="Professor's note", border_style="cyan"))
    except (PokeApiError, LlmConfigurationError) as error:
        raise click.ClickException(str(error)) from error


@cli.command()
@click.argument("first")
@click.argument("second")
@click.option("--mock", is_flag=True, help="Use deterministic local reasoning only.")
def battle(first: str, second: str, mock: bool) -> None:
    """Make an intentionally simplified battle prediction."""
    settings = Settings()
    try:
        with _client(settings) as client:
            first_pokemon = _resolve_pokemon(client, first)
            second_pokemon = _resolve_pokemon(client, second)
            prediction = predict_battle(first_pokemon, second_pokemon, client)
            if not mock:
                prediction = refine_battle_prediction(
                    prediction,
                    first_pokemon.model_dump(),
                    second_pokemon.model_dump(),
                    settings,
                )
            render_battle(first_pokemon, second_pokemon, prediction, console)
    except (PokeApiError, LlmConfigurationError) as error:
        raise click.ClickException(str(error)) from error


@cli.command()
@click.argument("question")
@click.option("--mock", is_flag=True, help="Answer common questions without an LLM.")
def ask(question: str, mock: bool) -> None:
    """Let an agent choose controlled PokeAPI tools to answer a question."""
    settings = Settings()
    try:
        with _client(settings) as client:
            answer = ask_mock(question, client) if mock else ask_agent(question, client, settings)
            console.print(Panel(answer, title="Professor Oak", border_style="green"))
    except (PokeApiError, LlmConfigurationError, ValueError) as error:
        raise click.ClickException(str(error)) from error


def _client(settings: Settings) -> PokeApiClient:
    return PokeApiClient(timeout=settings.pokeapi_timeout)


def _resolve_pokemon(
    client: PokeApiClient,
    name: str,
    *,
    interactive: bool | None = None,
) -> PokemonSummary:
    should_prompt = sys.stdin.isatty() if interactive is None else interactive
    candidate = name
    while True:
        try:
            return client.get_pokemon(candidate)
        except PokeApiNotFound as error:
            if not should_prompt or not error.suggestions:
                raise

            best = error.suggestions[0]
            message = Text()
            message.append(f"I couldn't find {error.resource!r}.\n\n")
            message.append("Best match: ", style="bold")
            message.append(best.name.title(), style="bold cyan")
            message.append(f"  ({best.score:.0%} similarity)", style="dim")
            console.print(Panel(message, title="Pokémon not found", border_style="yellow"))

            answer = Prompt.ask(
                f"Press [bold]Enter[/] to use [cyan]{best.name.title()}[/], "
                "type another name, or [bold]q[/] to cancel",
                default=best.name,
                show_default=False,
                console=console,
            ).strip()
            if answer.lower() in {"q", "quit", "cancel"}:
                raise click.Abort from error
            candidate = answer or best.name


if __name__ == "__main__":
    cli()
