import pytest

from app.pokeapi import PokeApiNotFound, normalize_identifier


def test_identifier_normalization() -> None:
    assert normalize_identifier(" Mr Mime ") == "mr-mime"
    assert normalize_identifier("Pikáchu!") == "pikachu"


def test_unknown_pokemon_has_clear_error(client) -> None:
    with pytest.raises(PokeApiNotFound, match="missingno"):
        client.get_pokemon("missingno")


def test_misspelled_pokemon_suggests_closest_name(client) -> None:
    with pytest.raises(PokeApiNotFound, match=r"Did you mean: charizard") as captured:
        client.get_pokemon("charizrad")

    assert captured.value.resource == "charizrad"
    assert captured.value.suggestions[0].name == "charizard"


def test_similarity_search_is_deterministic(client) -> None:
    suggestions = client.search_pokemon("venasaur", limit=2)

    assert suggestions[0].name == "venusaur"
    assert suggestions[0].score > 0.8


def test_species_index_only_lives_in_memory(client) -> None:
    client.search_pokemon("charizrad")

    assert client._pokemon_names is not None
    assert "charizard" in client._pokemon_names
