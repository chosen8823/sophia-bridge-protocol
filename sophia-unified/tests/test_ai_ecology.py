from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


CORE_DIR = Path(__file__).resolve().parents[1] / "consciousness-core"
sys.path.insert(0, str(CORE_DIR))
SPEC = importlib.util.spec_from_file_location("ai_ecology", CORE_DIR / "ai_ecology.py")
assert SPEC is not None
assert SPEC.loader is not None
ai_ecology = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ai_ecology
SPEC.loader.exec_module(ai_ecology)


def test_ecology_routes_conversational_signal_deterministically() -> None:
    event = ai_ecology.EcologyEvent(
        source="chat",
        utterance="route game ai audio daw search agents and filesystem cookies",
        tags=("game", "audio", "search", "file"),
    )

    first = ai_ecology.route_event(event)
    second = ai_ecology.route_event(event)

    assert first == second
    assert first["kind"] == "ai_ecology_receipt_v1"
    assert first["settlement_surface"] == "ground"
    assert first["altitude"] == "air"
    assert "game_ai" in first["participants"]
    assert "audio_daw" in first["participants"]
    assert "search_ai" in first["participants"]
    assert len(first["field_cookies"]) == len(first["participants"])


def test_social_media_participant_is_draft_only_and_flagged() -> None:
    event = ai_ecology.EcologyEvent(
        source="chat",
        utterance="draft a social post but do not publish",
        tags=("social", "post"),
    )

    receipt = ai_ecology.route_event(event)

    assert "social_media" in receipt["participants"]
    social_steps = [
        step for step in receipt["transform_series"]
        if step["participant"] == "social_media"
    ]
    assert social_steps[0]["posture"] == "approval_required"
    assert any(flag["code"] == "external_effect_boundary" for flag in receipt["field_flags"])


def test_unknown_signal_becomes_reservoir() -> None:
    event = ai_ecology.EcologyEvent(source="quiet", utterance="zzzz")

    receipt = ai_ecology.route_event(event)

    assert receipt["participants"] == ["unknown_signal_reservoir"]
    assert receipt["transform_series"][0]["operation"] == "hold_residual"


def test_ecology_rejects_float_payload() -> None:
    event = ai_ecology.EcologyEvent(source="sensor", utterance="bad", payload={"pressure": 0.1})

    try:
        ai_ecology.route_event(event)
    except Exception as exc:
        assert "float" in str(exc).lower()
    else:
        raise AssertionError("expected canonical float rejection")
