from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


CORE_DIR = Path(__file__).resolve().parents[1] / "consciousness-core"
sys.path.insert(0, str(CORE_DIR))


def load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, CORE_DIR / f"{name}.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


thermo = load_module("field_thermometer")
pulse = load_module("unified_pulse_organ")


def thermometer_atom(filename: str = "garden.md", route_count_before: int = 0):
    material = {
        "kind": "sophia_filesystem_event_v1",
        "event_type": "OBSERVATION_INGESTED",
        "evidence_class": "SEMANTIC",
        "observation": {
            "raw_filename": filename,
            "file_size_bytes": 8192,
        },
    }
    event = {**material, "event_cid": thermo.cid_for(material)}
    return thermo.translate_event(event, route_count_before=route_count_before)


def sample_input() -> pulse.PulseInput:
    return pulse.PulseInput(
        focus="sophia_laptop_garden",
        epoch=8,
        regulatory_signals={
            "memory_pressure_ppm": 620_000,
            "network_pressure_ppm": 720_000,
            "thermal_pressure_ppm": 220_000,
        },
        charges=(
            pulse.Charge("field_cookie", "semantic", "opte:preserves_provenance", None),
            pulse.Charge("network_heat", "electromagnetic", "opte:requests_regulation", 710_000),
        ),
        cymatic_signals=(
            pulse.CymaticSignal("bubble_motion", "render", "opte:articulates_geometry", 3, 700_000),
        ),
        cymatic_frames=(
            pulse.ObserverFrame("matched", 3, orientation_index=6),
            pulse.ObserverFrame("slow", 9, orientation_index=9),
        ),
        temperature_atoms=(thermometer_atom(route_count_before=2),),
    )


def test_unified_pulse_composes_four_organs_without_live_probe() -> None:
    receipt = pulse.pulse_field(sample_input())

    assert receipt["kind"] == "sophia_unified_pulse_receipt_v1"
    assert [channel["channel"] for channel in receipt["channels"]] == [
        "cymatic",
        "morphogenic",
        "regulatory",
        "thermometer",
    ]
    assert receipt["boundary_law"] == "many_organs_one_field_pulse"
    assert receipt["live_probe"] is False
    assert receipt["external_effects"] is False
    assert receipt["semantic_claims_introduced"] is False


def test_dominant_channel_and_route_instruction_follow_highest_pressure() -> None:
    receipt = pulse.pulse_field(
        pulse.PulseInput(
            focus="pressure_test",
            epoch=1,
            regulatory_signals={"memory_pressure_ppm": 980_000},
            charges=(pulse.Charge("quiet_charge", "semantic", "opte:holds", 100_000),),
            cymatic_signals=(pulse.CymaticSignal("grain", "render", "opte:observes", 10, 300_000),),
            cymatic_frames=(pulse.ObserverFrame("far", 1),),
        )
    )

    assert receipt["dominant_channel"] == "regulatory"
    assert receipt["heart_state"] == "surge"
    assert receipt["route_instruction"] == "settle_before_expansion"


def test_unified_pulse_is_replayable_for_equivalent_inputs() -> None:
    first = pulse.pulse_field(sample_input())
    second = pulse.pulse_field(
        pulse.PulseInput(
            focus="sophia_laptop_garden",
            epoch=8,
            regulatory_signals={
                "thermal_pressure_ppm": 220_000,
                "network_pressure_ppm": 720_000,
                "memory_pressure_ppm": 620_000,
            },
            charges=tuple(reversed(sample_input().charges)),
            cymatic_signals=tuple(reversed(sample_input().cymatic_signals)),
            cymatic_frames=tuple(reversed(sample_input().cymatic_frames)),
            temperature_atoms=tuple(reversed(sample_input().temperature_atoms)),
        )
    )

    assert first == second
    assert first["receipt_cid"] == second["receipt_cid"]
    assert first["invariant"] == second["invariant"]


def test_open_interpretation_policy_survives_the_heart_receipt() -> None:
    receipt = pulse.pulse_field(sample_input())

    assert receipt["interpretation_policy"]["terminology"] == "open"
    assert receipt["interpretation_policy"]["definition_state"] == "provisional"


def test_pulse_rejects_float_payloads() -> None:
    try:
        pulse.pulse_field(
            pulse.PulseInput(
                focus="bad",
                epoch=1,
                regulatory_signals={"memory_pressure_ppm": 0},
                temperature_atoms=({"temperature_ppm": 1.25},),
            )
        )
    except Exception as exc:
        assert "FLOAT_REJECTED" in str(exc) or "PULSE_INT_REQUIRED" in str(exc)
    else:
        raise AssertionError("float payload should have been rejected")
