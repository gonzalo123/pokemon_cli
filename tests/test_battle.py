from langchain.agents.structured_output import ToolStrategy

import agent as agent_module
from battle import predict_battle
from config import Settings
from models import BattlePrediction


def test_charizard_beats_venusaur_in_simplified_prediction(client) -> None:
    charizard = client.get_pokemon("Charizard")
    venusaur = client.get_pokemon("venusaur")

    prediction = predict_battle(charizard, venusaur, client)

    assert prediction.winner == "charizard"
    assert prediction.confidence >= 0.55
    assert prediction.recommended_attack_types == ["fire", "flying"]
    assert any("2x" in reason for reason in prediction.reasons)
    assert prediction.caveats


def test_bedrock_battle_uses_tool_strategy_for_structured_output(monkeypatch) -> None:
    prediction = BattlePrediction(
        winner="charizard",
        confidence=0.7,
        reasons=["Fire is super effective."],
        caveats=["Simplified prediction."],
        recommended_attack_types=["fire"],
    )
    captured = {}

    class FakeAgent:
        def invoke(self, payload):
            return {"structured_response": prediction}

    def fake_create_agent(**kwargs):
        captured.update(kwargs)
        return FakeAgent()

    monkeypatch.setattr(agent_module, "create_chat_model", lambda settings: object())
    monkeypatch.setattr(agent_module, "create_agent", fake_create_agent)

    result = agent_module.refine_battle_prediction(
        prediction,
        {"name": "charizard"},
        {"name": "venusaur"},
        Settings(),
    )

    assert result == prediction
    assert isinstance(captured["response_format"], ToolStrategy)


def test_battle_prompt_forbids_new_claims() -> None:
    assert "Do not add new" in agent_module.BATTLE_PROMPT
