from models import PokemonComparison, PokemonSummary


def compare_pokemon(
    first: PokemonSummary,
    second: PokemonSummary,
) -> PokemonComparison:
    stat_names = dict.fromkeys(
        [stat.name for stat in first.stats] + [stat.name for stat in second.stats]
    )
    winners: dict[str, str] = {}
    for stat_name in stat_names:
        first_value = first.stat(stat_name)
        second_value = second.stat(stat_name)
        if first_value == second_value:
            winners[stat_name] = "tie"
        else:
            winners[stat_name] = first.name if first_value > second_value else second.name

    if first.total_stats == second.total_stats:
        winners["total"] = "tie"
    else:
        winners["total"] = (
            first.name if first.total_stats > second.total_stats else second.name
        )

    return PokemonComparison(
        first=first,
        second=second,
        stat_winners=winners,
        total_first=first.total_stats,
        total_second=second.total_stats,
    )
