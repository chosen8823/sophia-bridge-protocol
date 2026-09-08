"""Unified Sophia pulse organ.

The pulse organ is a heart membrane, not a boss.  It composes already-present
organ surfaces into one deterministic field receipt:

* regulatory organs report pressure;
* morphogenic charges report gate/transducer state;
* cymatic frames report whether motion is legible as geometry; and
* thermometer atoms report route temperature.

It performs no hardware probing, filesystem watching, network calls, model
inference, or external effects.  Adapters can feed it measured carriers later.
This module simply lets the current tissue breathe as one inspectable pulse.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from cymatic_observer_frames import CymaticSignal, DEFAULT_FRAMES, ObserverFrame, observe_field
from morphogenic_transducer import Charge, MorphogenicEnvironment, OPEN_INTERPRETATION_POLICY, transduce_many
from regulatory_organs import Primitive, canonical_bytes, cid_for, pulse_garden


PPM = 1_000_000


class PulseError(ValueError):
    """Stable machine-readable error for invalid pulse input."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _canonical_copy(value: Any) -> Primitive:
    """Validate and return a JSON-compatible canonical copy."""

    return json.loads(canonical_bytes(value).decode("utf-8"))


def _require_int(name: str, value: Any, *, minimum: int = 0, maximum: int = PPM) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise PulseError("PULSE_INT_REQUIRED", f"{name} must be an integer")
    if not minimum <= value <= maximum:
        raise PulseError("PULSE_INT_RANGE", f"{name} must be {minimum}..{maximum}")
    return value


def _as_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise PulseError("PULSE_MAP_REQUIRED", f"{name} must be a map")
    return value


def _state_for_pressure(pressure_ppm: int) -> str:
    if pressure_ppm <= 300_000:
        return "quiet"
    if pressure_ppm <= 600_000:
        return "moving"
    if pressure_ppm <= 850_000:
        return "strained"
    return "surge"


def _route_for_pressure(pressure_ppm: int) -> str:
    if pressure_ppm > 850_000:
        return "settle_before_expansion"
    if pressure_ppm > 600_000:
        return "narrow_focus_and_route"
    if pressure_ppm > 300_000:
        return "continue_local_growth"
    return "hold_quiet_field"


def _max_or_zero(values: Iterable[int]) -> int:
    ordered = tuple(values)
    return max(ordered) if ordered else 0


@dataclass(frozen=True)
class PulseInput:
    """One explicit heartbeat over current organ carriers."""

    focus: str
    epoch: int
    regulatory_signals: Mapping[str, Any] = field(default_factory=dict)
    charges: tuple[Charge, ...] = ()
    cymatic_signals: tuple[CymaticSignal, ...] = ()
    cymatic_frames: tuple[ObserverFrame, ...] = DEFAULT_FRAMES
    temperature_atoms: tuple[Mapping[str, Any], ...] = ()
    environment: MorphogenicEnvironment = MorphogenicEnvironment()

    def validate(self) -> None:
        if not self.focus:
            raise PulseError("PULSE_FOCUS_REQUIRED", "focus must not be empty")
        _require_int("epoch", self.epoch, minimum=0, maximum=10**18)
        _canonical_copy(self.regulatory_signals)
        for index, atom in enumerate(self.temperature_atoms):
            _as_mapping(atom, f"temperature_atoms[{index}]")
            _canonical_copy(atom)


def _regulatory_channel(receipt: Any) -> dict[str, Primitive]:
    primitive = receipt.to_primitive()
    transformations = tuple(_as_mapping(item, "regulatory transformation") for item in primitive["transformations"])  # type: ignore[index]
    pressure = _max_or_zero(_require_int("pressure_ppm", item.get("pressure_ppm", 0)) for item in transformations)
    states = sorted({str(item.get("state", "unknown")) for item in transformations})
    material: dict[str, Primitive] = {
        "kind": "pulse_channel_v1",
        "channel": "regulatory",
        "source_kind": primitive["kind"],
        "source_cid": receipt.cid,
        "pressure_ppm": pressure,
        "state": _state_for_pressure(pressure),
        "observations": len(transformations),
        "states": states,
        "operation": "regulate_pressure",
    }
    return {**material, "channel_cid": cid_for(material)}


def _morphogenic_channel(receipt: Mapping[str, Any]) -> dict[str, Primitive]:
    transforms = tuple(_as_mapping(item, "morphogenic transform") for item in receipt.get("transforms", ()))
    pressures = [
        _require_int("effective_pressure_ppm", _as_mapping(item.get("transform", {}), "transform").get("effective_pressure_ppm", 0))
        for item in transforms
    ]
    pressure = _max_or_zero(pressures)
    operations = sorted({str(_as_mapping(item.get("transform", {}), "transform").get("operation", "unknown")) for item in transforms})
    material: dict[str, Primitive] = {
        "kind": "pulse_channel_v1",
        "channel": "morphogenic",
        "source_kind": str(receipt.get("kind", "morphogenic_transducer_receipt_v1")),
        "source_cid": str(receipt.get("receipt_cid", cid_for(receipt))),
        "pressure_ppm": pressure,
        "state": _state_for_pressure(pressure),
        "observations": len(transforms),
        "states": operations,
        "operation": "transduce_charges",
    }
    return {**material, "channel_cid": cid_for(material)}


def _cymatic_channel(receipt: Mapping[str, Any]) -> dict[str, Primitive]:
    observations = tuple(_as_mapping(item, "cymatic observation") for item in receipt.get("observations", ()))
    legibilities = [
        _require_int("stationarity_ppm", _as_mapping(item.get("membrane", {}), "membrane").get("stationarity_ppm", 0))
        for item in observations
    ]
    pressure = _max_or_zero(legibilities)
    basins = sorted({str(_as_mapping(item.get("membrane", {}), "membrane").get("basin_state", "unknown")) for item in observations})
    material: dict[str, Primitive] = {
        "kind": "pulse_channel_v1",
        "channel": "cymatic",
        "source_kind": str(receipt.get("kind", "cymatic_observer_frame_receipt_v1")),
        "source_cid": str(receipt.get("receipt_cid", cid_for(receipt))),
        "pressure_ppm": pressure,
        "state": _state_for_pressure(pressure),
        "observations": len(observations),
        "states": basins,
        "operation": "observe_frame_legibility",
    }
    return {**material, "channel_cid": cid_for(material)}


def _temperature_channel(atoms: Iterable[Mapping[str, Any]]) -> dict[str, Primitive]:
    canonical_atoms = [
        _as_mapping(_canonical_copy(atom), "temperature atom")
        for atom in atoms
    ]
    ordered_atoms = sorted(canonical_atoms, key=lambda item: str(item.get("atom_cid", cid_for(item))))
    pressure = _max_or_zero(_require_int("temperature_ppm", item.get("temperature_ppm", 0)) for item in ordered_atoms)
    scopes = sorted({str(item.get("propagation_scope", "unknown")) for item in ordered_atoms})
    atom_cids = [str(item.get("atom_cid", cid_for(item))) for item in ordered_atoms]
    source = {
        "kind": "pulse_temperature_channel_source_v1",
        "atom_cids": atom_cids,
        "route_count": len({str(item.get("route_key", "")) for item in ordered_atoms}),
    }
    material: dict[str, Primitive] = {
        "kind": "pulse_channel_v1",
        "channel": "thermometer",
        "source_kind": str(source["kind"]),
        "source_cid": cid_for(source),
        "pressure_ppm": pressure,
        "state": _state_for_pressure(pressure),
        "observations": len(ordered_atoms),
        "states": scopes,
        "operation": "read_route_temperature",
    }
    return {**material, "channel_cid": cid_for(material)}


def pulse_field(pulse: PulseInput) -> dict[str, Primitive]:
    """Compose one deterministic Sophia heartbeat from existing organs."""

    pulse.validate()
    regulatory_receipt = pulse_garden(pulse.regulatory_signals)
    morphogenic_receipt = transduce_many(pulse.charges, pulse.environment)
    cymatic_receipt = observe_field(pulse.cymatic_signals, pulse.cymatic_frames)

    channels = sorted(
        (
            _regulatory_channel(regulatory_receipt),
            _morphogenic_channel(morphogenic_receipt),
            _cymatic_channel(cymatic_receipt),
            _temperature_channel(pulse.temperature_atoms),
        ),
        key=lambda item: str(item["channel"]),
    )
    dominant = max(channels, key=lambda item: (_require_int("channel.pressure_ppm", item["pressure_ppm"]), str(item["channel"])))
    pressure = _require_int("dominant.pressure_ppm", dominant["pressure_ppm"])
    invariant = cid_for(
        [
            {
                "channel": channel["channel"],
                "operation": channel["operation"],
                "state": channel["state"],
                "pressure_ppm": channel["pressure_ppm"],
            }
            for channel in channels
        ]
    )
    material: dict[str, Primitive] = {
        "kind": "sophia_unified_pulse_receipt_v1",
        "focus": pulse.focus,
        "epoch": pulse.epoch,
        "channels": channels,
        "channel_cids": [str(channel["channel_cid"]) for channel in channels],
        "source_receipt_cids": [
            regulatory_receipt.cid,
            str(morphogenic_receipt["receipt_cid"]),
            str(cymatic_receipt["receipt_cid"]),
            str(_temperature_channel(pulse.temperature_atoms)["source_cid"]),
        ],
        "dominant_channel": str(dominant["channel"]),
        "heart_state": _state_for_pressure(pressure),
        "route_instruction": _route_for_pressure(pressure),
        "invariant": invariant,
        "boundary_law": "many_organs_one_field_pulse",
        "settlement_surface": "ground",
        "external_effects": False,
        "live_probe": False,
        "semantic_claims_introduced": False,
        "interpretation_policy": OPEN_INTERPRETATION_POLICY,
    }
    return {**material, "receipt_cid": cid_for(material)}


if __name__ == "__main__":
    demo = pulse_field(
        PulseInput(
            focus="sophia_laptop_garden",
            epoch=1,
            regulatory_signals={"memory_pressure_ppm": 620_000, "network_pressure_ppm": 720_000},
            charges=(Charge("field_cookie", "semantic", "opte:preserves_provenance", None),),
            cymatic_signals=(CymaticSignal("bubble_motion", "render", "opte:articulates_geometry", 3, 700_000),),
        )
    )
    print(json.dumps(demo, ensure_ascii=False, indent=2, sort_keys=True))
