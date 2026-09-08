from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


CORE_DIR = Path(__file__).resolve().parents[1] / "consciousness-core"
sys.path.insert(0, str(CORE_DIR))
SPEC = importlib.util.spec_from_file_location("cymatic_observer_frames", CORE_DIR / "cymatic_observer_frames.py")
assert SPEC is not None
assert SPEC.loader is not None
cym = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = cym
SPEC.loader.exec_module(cym)


def test_matching_frame_locks_motion_as_geometry() -> None:
    observation = cym.observe_signal_through_frame(
        cym.CymaticSignal(
            "bubble_motion",
            "render",
            "opte:articulates_geometry",
            grain_period_units=100,
            energy_ppm=800_000,
        ),
        cym.ObserverFrame("matched_membrane", integration_units=100, damping_ppm=25_000),
    )

    assert observation["timescale"]["ratio_ppm"] == 1_000_000
    assert observation["membrane"]["band"] == "quasi_stationary"
    assert observation["membrane"]["basin_state"] == "attractor_lock"
    assert observation["transform"]["operation"] == "articulate_geometry"
    assert observation["transform"]["semantic_claims_introduced"] is False


def test_fast_and_slow_frames_do_not_fake_lock() -> None:
    signal = cym.CymaticSignal(
        "granular_flux",
        "semantic",
        "opte:seeks_shape",
        grain_period_units=100,
        energy_ppm=500_000,
    )

    fast = cym.observe_signal_through_frame(signal, cym.ObserverFrame("too_fast", integration_units=20))
    slow = cym.observe_signal_through_frame(signal, cym.ObserverFrame("too_slow", integration_units=300))

    assert fast["membrane"]["band"] == "under_integrated_grain"
    assert fast["membrane"]["basin_state"] == "granular_residue"
    assert fast["transform"]["operation"] == "retain_residue"
    assert slow["membrane"]["band"] == "over_integrated_envelope"
    assert slow["membrane"]["basin_state"] == "envelope_memory"
    assert slow["transform"]["operation"] == "compress_envelope"


def test_dudenty_orientation_is_modular_and_interpretation_stays_open() -> None:
    frame = cym.ObserverFrame(
        "dozenial_or_dudenty_window",
        integration_units=12,
        orientation_index=26,
        orientation_modulus=20,
        aliases=("clock", "dudenty", "dozenial"),
    )
    primitive = frame.to_primitive()

    assert primitive["orientation"]["addressing"] == "dudenty_open_modulus"
    assert primitive["orientation"]["index"] == 6
    assert primitive["orientation"]["modulus"] == 20
    assert primitive["aliases"] == ["clock", "dozenial", "dudenty"]
    assert primitive["interpretation_policy"]["terminology"] == "open"


def test_observer_field_receipt_is_deterministic_and_ordered() -> None:
    signals = [
        cym.CymaticSignal("zeta", "semantic", "opte:relates", 2, 400_000),
        cym.CymaticSignal("alpha", "semantic", "opte:relates", 1, 600_000),
    ]
    frames = [
        cym.ObserverFrame("slow", 3, orientation_index=4),
        cym.ObserverFrame("fast", 1, orientation_index=2),
    ]

    first = cym.observe_field(signals, frames)
    second = cym.observe_field(reversed(signals), reversed(frames))

    assert first == second
    assert [item["signal"]["name"] for item in first["observations"]] == ["alpha", "alpha", "zeta", "zeta"]
    assert [item["frame"]["name"] for item in first["observations"]] == ["fast", "slow", "fast", "slow"]
    assert first["boundary_law"] == "match_observer_time_to_transformation_time"
    assert first["semantic_claims_introduced"] is False


def test_invalid_float_signal_is_rejected() -> None:
    try:
        cym.CymaticSignal("bad", "semantic", "opte:bad", 1.5, 100_000).to_primitive()
    except Exception as exc:
        assert "CYMATIC_INT_REQUIRED" in str(exc)
    else:
        raise AssertionError("float period should have been rejected")
