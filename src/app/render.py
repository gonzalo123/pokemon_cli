from __future__ import annotations

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.table import Table
from rich.text import Text

from app.models import BattlePrediction, PokemonComparison, PokemonSummary


def render_pokemon(pokemon: PokemonSummary, console: Console) -> None:
    facts = Table.grid(padding=(0, 2))
    facts.add_column(style="bold cyan")
    facts.add_column()
    facts.add_row("ID", f"#{pokemon.id}")
    facts.add_row("Types", " / ".join(item.title() for item in pokemon.types))
    facts.add_row("Height", f"{pokemon.height / 10:g} m")
    facts.add_row("Weight", f"{pokemon.weight / 10:g} kg")
    facts.add_row(
        "Base experience",
        str(pokemon.base_experience) if pokemon.base_experience is not None else "unknown",
    )
    facts.add_row("Abilities", ", ".join(item.title() for item in pokemon.abilities))
    console.print(Panel(facts, title=pokemon.name.title(), border_style="yellow"))

    stats = Table(title="Base stats", box=box.SIMPLE_HEAVY)
    stats.add_column("Stat", style="bold")
    stats.add_column("Value", justify="right")
    stats.add_column("Scale (0-255)", ratio=1)
    for stat in pokemon.stats:
        stats.add_row(
            stat.name.replace("-", " ").title(),
            str(stat.value),
            ProgressBar(total=255, completed=min(stat.value, 255), width=30),
        )
    stats.add_section()
    stats.add_row("Total", str(pokemon.total_stats), "")
    console.print(stats)


def render_comparison(comparison: PokemonComparison, console: Console) -> None:
    first = comparison.first
    second = comparison.second
    table = Table(
        title=f"{first.name.title()} vs {second.name.title()}",
        box=box.ROUNDED,
    )
    table.add_column("Stat", style="bold")
    table.add_column(first.name.title(), justify="right")
    table.add_column(second.name.title(), justify="right")
    table.add_column("Winner")
    table.add_row(
        "Types",
        " / ".join(first.types),
        " / ".join(second.types),
        "—",
    )
    for stat in first.stats:
        winner = comparison.stat_winners[stat.name]
        table.add_row(
            stat.name.replace("-", " ").title(),
            str(stat.value),
            str(second.stat(stat.name)),
            _winner_label(winner),
        )
    table.add_section()
    table.add_row(
        "Total",
        str(comparison.total_first),
        str(comparison.total_second),
        _winner_label(comparison.stat_winners["total"]),
    )
    console.print(table)


def render_battle(
    first: PokemonSummary,
    second: PokemonSummary,
    prediction: BattlePrediction,
    console: Console,
) -> None:
    body = Text()
    body.append("Winner: ", style="bold")
    body.append(f"{prediction.winner.title()}\n", style="bold green")
    body.append("Confidence: ", style="bold")
    body.append(f"{prediction.confidence:.0%}\n\n", style="cyan")
    body.append("Why\n", style="bold")
    for reason in prediction.reasons:
        body.append(f"• {reason}\n")
    body.append("\nRecommended attack types\n", style="bold")
    body.append(", ".join(item.title() for item in prediction.recommended_attack_types))
    body.append("\n\nCaveats\n", style="bold yellow")
    for caveat in prediction.caveats:
        body.append(f"• {caveat}\n", style="dim")
    console.print(
        Panel(
            body,
            title=f"{first.name.title()} vs {second.name.title()}",
            border_style="magenta",
        )
    )


def _winner_label(winner: str) -> str:
    return "Tie" if winner == "tie" else winner.title()
