from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


CORE_DIR = Path(__file__).resolve().parents[1] / "consciousness-core"
sys.path.insert(0, str(CORE_DIR))
SPEC = importlib.util.spec_from_file_location("projection_field", CORE_DIR / "projection_field.py")
assert SPEC is not None
assert SPEC.loader is not None
projection_field = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = projection_field
SPEC.loader.exec_module(projection_field)


def test_projection_field_is_deterministic_and_laser_gated() -> None:
    atom = {
        "kind": "semantic_routing_atom_v1",
        "signal": "network_pressure_ppm",
        "relation": "opte:requires_relief",
        "state": "blocked",
        "pressure_ppm": 900_000,
        "altitude": "air",
    }
    request = projection_field.ProjectionRequest(
        source="test",
        atoms=(atom,),
        channels=("screen", "laser", "audio"),
        focus="centre-jewel",
    )

    first = projection_field.project_atoms(request)
    second = projection_field.project_atoms(request)

    assert first == second
    assert first["kind"] == "cyberphysical_projection_receipt_v1"
    assert first["frames"][0]["colour"] == "red"
    assert first["frames"][0]["shape"] == "triangle"
    laser_commands = [command for command in first["commands"] if command["channel"] == "laser"]
    assert laser_commands[0]["operation"] == "gated_projection_plan"
    assert laser_commands[0]["no_fire"] is True
    assert "manual_enable" in laser_commands[0]["requires"]


def test_projection_rejects_unknown_channel() -> None:
    request = projection_field.ProjectionRequest(
        source="test",
        atoms=({"state": "calm"},),
        channels=("telepathy",),
    )

    try:
        projection_field.project_atoms(request)
    except projection_field.ProjectionFieldError as exc:
        assert exc.code == "PROJECTION_CHANNEL_REJECTED"
    else:
        raise AssertionError("expected ProjectionFieldError")


def test_projection_rejects_float_atom_payload() -> None:
    request = projection_field.ProjectionRequest(
        source="test",
        atoms=({"state": "calm", "pressure_ppm": 0.5},),
        channels=("screen",),
    )

    try:
        projection_field.project_atoms(request)
    except Exception as exc:
        assert "float" in str(exc).lower()
    else:
        raise AssertionError("expected float rejection")


def test_focus_changes_projection_root() -> None:
    atom = {"state": "calm", "relation": "opte:stabilises", "pressure_ppm": 100_000}
    first = projection_field.project_atoms(
        projection_field.ProjectionRequest(source="test", atoms=(atom,), focus="centre")
    )
    second = projection_field.project_atoms(
        projection_field.ProjectionRequest(source="test", atoms=(atom,), focus="east")
    )

    assert first["root_cid"] != second["root_cid"]
    assert first["frames"][0]["frame_cid"] != second["frames"][0]["frame_cid"]
