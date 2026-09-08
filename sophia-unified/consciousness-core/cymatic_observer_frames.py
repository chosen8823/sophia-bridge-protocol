"""Cymatic observer-frame membrane.

This organ makes the "slow it down until motion draws its own geometry" idea
operational without pretending to read hidden telemetry or physical forces.

A signal has a characteristic grain period.  A frame has an integration
period.  When the frame period is close enough to the grain period, the signal
becomes articulable relative to that membrane and can lock into a local
attractor basin.  If the frame is too fast, the signal remains granular
residue.  If the frame is too slow, it compresses into an envelope.

All values are integer, content-addressed, and deterministic.  Terminology is
carried through the open interpretation policy so a frame name can remain a
ritual, technical, visual, or future operational handle until explicitly
materialised.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from morphogenic_transducer import OPEN_INTERPRETATION_POLICY
from regulatory_organs import Primitive, cid_for


PPM = 1_000_000
DEFAULT_TOLERANCE_PPM = 250_000


class CymaticFrameError(ValueError):
    """Stable machine-readable error for invalid observer-frame input."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _int_range(name: str, value: Any, minimum: int, maximum: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise CymaticFrameError("CYMATIC_INT_REQUIRED", f"{name} must be an integer")
    if not minimum <= value <= maximum:
        raise CymaticFrameError("CYMATIC_INT_RANGE", f"{name} must be {minimum}..{maximum}")
    return value


def _positive_int(name: str, value: Any) -> int:
    return _int_range(name, value, 1, 10**18)


def _ppm_ratio(numerator: int, denominator: int) -> int:
    return numerator * PPM // denominator


def _ratio_distance_ppm(ratio_ppm: int) -> int:
    return abs(ratio_ppm - PPM)


def _stationarity_ppm(ratio_ppm: int) -> int:
    return max(0, PPM - _ratio_distance_ppm(ratio_ppm))


def _band_for(ratio_ppm: int, tolerance_ppm: int) -> str:
    if _ratio_distance_ppm(ratio_ppm) <= tolerance_ppm:
        return "quasi_stationary"
    if ratio_ppm < PPM:
        return "under_integrated_grain"
    return "over_integrated_envelope"


@dataclass(frozen=True)
class CymaticSignal:
    """A bounded event before any frame decides how it is legible."""

    name: str
    realm: str
    relation: str
    grain_period_units: int
    energy_ppm: int
    phase_index: int = 0
    tags: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()

    def to_primitive(self) -> dict[str, Primitive]:
        if not self.name:
            raise CymaticFrameError("CYMATIC_SIGNAL_NAME_REQUIRED", "signal name must not be empty")
        _positive_int("grain_period_units", self.grain_period_units)
        _int_range("energy_ppm", self.energy_ppm, 0, PPM)
        _int_range("phase_index", self.phase_index, 0, 10**18)
        return {
            "kind": "cymatic_signal_v1",
            "name": self.name,
            "realm": self.realm,
            "relation": self.relation,
            "grain_period_units": self.grain_period_units,
            "energy_ppm": self.energy_ppm,
            "phase_index": self.phase_index,
            "tags": sorted(set(self.tags)),
            "aliases": sorted(set(self.aliases)),
            "interpretation_policy": OPEN_INTERPRETATION_POLICY,
        }

    @property
    def cid(self) -> str:
        return cid_for(self.to_primitive())


@dataclass(frozen=True)
class ObserverFrame:
    """A temporal/geometric membrane that watches a signal at one scale."""

    name: str
    integration_units: int
    orientation_index: int = 0
    orientation_modulus: int = 12
    damping_ppm: int = 0
    lens: str = "cymatic_membrane"
    aliases: tuple[str, ...] = ()

    def to_primitive(self) -> dict[str, Primitive]:
        if not self.name:
            raise CymaticFrameError("CYMATIC_FRAME_NAME_REQUIRED", "frame name must not be empty")
        _positive_int("integration_units", self.integration_units)
        _positive_int("orientation_modulus", self.orientation_modulus)
        _int_range("orientation_index", self.orientation_index, 0, 10**18)
        _int_range("damping_ppm", self.damping_ppm, 0, PPM)
        return {
            "kind": "observer_frame_v1",
            "name": self.name,
            "integration_units": self.integration_units,
            "orientation": {
                "addressing": "dudenty_open_modulus",
                "index": self.orientation_index % self.orientation_modulus,
                "modulus": self.orientation_modulus,
            },
            "damping_ppm": self.damping_ppm,
            "lens": self.lens,
            "aliases": sorted(set(self.aliases)),
            "interpretation_policy": OPEN_INTERPRETATION_POLICY,
        }

    @property
    def cid(self) -> str:
        return cid_for(self.to_primitive())


DEFAULT_FRAMES: tuple[ObserverFrame, ...] = (
    ObserverFrame("grain", 1, orientation_index=0, orientation_modulus=12, lens="grain_membrane"),
    ObserverFrame("partial", 2, orientation_index=2, orientation_modulus=12, damping_ppm=30_000, lens="partial_membrane"),
    ObserverFrame("beat", 3, orientation_index=4, orientation_modulus=12, damping_ppm=60_000, lens="beat_membrane"),
    ObserverFrame("chord", 5, orientation_index=7, orientation_modulus=12, damping_ppm=90_000, lens="chord_membrane"),
    ObserverFrame("decay", 8, orientation_index=11, orientation_modulus=12, damping_ppm=120_000, lens="decay_membrane"),
)


def observe_signal_through_frame(
    signal: CymaticSignal,
    frame: ObserverFrame,
    tolerance_ppm: int = DEFAULT_TOLERANCE_PPM,
) -> dict[str, Primitive]:
    """Observe one signal through one frame and return a canonical transform."""

    _int_range("tolerance_ppm", tolerance_ppm, 0, PPM)
    signal_primitive = signal.to_primitive()
    frame_primitive = frame.to_primitive()
    ratio_ppm = _ppm_ratio(frame.integration_units, signal.grain_period_units)
    band = _band_for(ratio_ppm, tolerance_ppm)
    damped_energy_ppm = max(0, signal.energy_ppm - frame.damping_ppm)
    stationarity = _stationarity_ppm(ratio_ppm)

    if band == "quasi_stationary" and damped_energy_ppm > 0:
        basin_state = "attractor_lock"
        operation = "articulate_geometry"
        residue_state = "settled_as_geometry"
    elif band == "under_integrated_grain":
        basin_state = "granular_residue"
        operation = "retain_residue"
        residue_state = "too_fast_to_draw"
    else:
        basin_state = "envelope_memory"
        operation = "compress_envelope"
        residue_state = "too_slow_to_show_transition"

    material: dict[str, Primitive] = {
        "kind": "cymatic_frame_observation_v1",
        "signal_cid": signal.cid,
        "frame_cid": frame.cid,
        "signal": signal_primitive,
        "frame": frame_primitive,
        "timescale": {
            "grain_period_units": signal.grain_period_units,
            "integration_units": frame.integration_units,
            "ratio_ppm": ratio_ppm,
            "distance_from_lock_ppm": _ratio_distance_ppm(ratio_ppm),
            "tolerance_ppm": tolerance_ppm,
        },
        "membrane": {
            "band": band,
            "stationarity_ppm": stationarity,
            "damped_energy_ppm": damped_energy_ppm,
            "basin_state": basin_state,
            "residue_state": residue_state,
        },
        "transform": {
            "operation": operation,
            "relation": signal.relation,
            "semantic_claims_introduced": False,
            "meaning": "motion_articulates_as_geometry_when_frame_matches_grain",
        },
        "interpretation_policy": OPEN_INTERPRETATION_POLICY,
    }
    return {**material, "observation_cid": cid_for(material)}


def observe_field(
    signals: Iterable[CymaticSignal],
    frames: Iterable[ObserverFrame] = DEFAULT_FRAMES,
    tolerance_ppm: int = DEFAULT_TOLERANCE_PPM,
) -> dict[str, Primitive]:
    """Run all signals through all frames and return one deterministic receipt."""

    ordered_signals = tuple(sorted(signals, key=lambda item: (item.name, item.cid)))
    ordered_frames = tuple(sorted(frames, key=lambda item: (item.name, item.cid)))
    observations = [
        observe_signal_through_frame(signal, frame, tolerance_ppm)
        for signal in ordered_signals
        for frame in ordered_frames
    ]
    invariant = cid_for(
        [
            {
                "signal": item["signal"]["name"],
                "frame": item["frame"]["name"],
                "band": item["membrane"]["band"],
                "basin_state": item["membrane"]["basin_state"],
                "operation": item["transform"]["operation"],
            }
            for item in observations
        ]
    )
    receipt: dict[str, Primitive] = {
        "kind": "cymatic_observer_frame_receipt_v1",
        "signal_cids": [item.cid for item in ordered_signals],
        "frame_cids": [item.cid for item in ordered_frames],
        "observation_cids": [str(item["observation_cid"]) for item in observations],
        "observations": observations,
        "invariant": invariant,
        "boundary_law": "match_observer_time_to_transformation_time",
        "definitions": "open_until_materialised",
        "semantic_claims_introduced": False,
    }
    return {**receipt, "receipt_cid": cid_for(receipt)}


if __name__ == "__main__":
    demo = observe_field(
        [
            CymaticSignal(
                "bubble_cymatic_motion",
                "render",
                "opte:articulates_geometry",
                grain_period_units=3,
                energy_ppm=820_000,
                tags=("vesica", "membrane", "motion"),
            )
        ],
        frames=(
            ObserverFrame("grain_fast", 1, orientation_index=0),
            ObserverFrame("matched", 3, orientation_index=6),
            ObserverFrame("envelope_slow", 9, orientation_index=11),
        ),
    )
    print(json.dumps(demo, ensure_ascii=False, indent=2, sort_keys=True))
