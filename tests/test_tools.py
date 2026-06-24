from agent import ask_mock
from tools import build_tools


def test_get_pokemon_tool_returns_normalized_data(client) -> None:
    tools = {item.name: item for item in build_tools(client)}

    result = tools["get_pokemon"].invoke({"name": "CHARIZARD"})

    assert result["name"] == "charizard"
    assert result["types"] == ["fire", "flying"]
    assert result["abilities"] == ["blaze"]


def test_type_matchup_tool_returns_compact_multiplier(client) -> None:
    tools = {item.name: item for item in build_tools(client)}

    result = tools["get_type_matchup"].invoke(
        {"attacker_type": "fire", "defender_types": ["grass", "poison"]}
    )

    assert result == {
        "attacker_type": "fire",
        "defender_types": ["grass", "poison"],
        "multiplier": 2.0,
    }


def test_evolution_chain_keeps_branches(client) -> None:
    tools = {item.name: item for item in build_tools(client)}

    result = tools["get_evolution_chain"].invoke({"name": "eevee"})

    assert result["paths"] == [["eevee", "vaporeon"], ["eevee", "jolteon"]]


def test_mock_question_uses_real_tool_data_without_llm(client) -> None:
    answer = ask_mock("Which Pokémon is faster, Gengar or Alakazam?", client)

    assert "Alakazam is faster" in answer
    assert "Gengar: 110" in answer
    assert "Alakazam: 120" in answer
