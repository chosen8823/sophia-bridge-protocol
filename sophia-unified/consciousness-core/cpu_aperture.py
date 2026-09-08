"""CPU aperture organ.

The CPU is treated as an aperture, not as a thing to blindly overclock.
Measured CPU-like pressure enters as canonical integer data, is observed
through multiple frames, fans into semantic domains, and returns linked
semantic routing atoms.

This module performs no live probing and applies no power settings.  Hardware
adapters may feed it observations later; this organ only turns an already
provided observation into deterministic, inspectable field tissue.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from morphogenic_transducer import OPEN_INTERPRETATION_POLICY
from regulatory_organs import Primitive, SemanticRoutingAtom, cid_for, opte_transform_atoms


PPM = 1_000_000


class CPUApertureError(ValueError):
    """Stable machine-readable error for invalid CPU aperture input."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _require_int(name: str, value: Any, *, minimum: int = 0, maximum: int = PPM) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise CPUApertureError("CPU_APERTURE_INT_REQUIRED", f"{name} must be an integer")
    if not minimum <= value <= maximum:
        raise CPUApertureError("CPU_APERTURE_INT_RANGE", f"{name} must be {minimum}..{maximum}")
    return value


def _require_positive_int(name: str, value: Any) -> int:
    return _require_int(name, value, minimum=1, maximum=10**18)


def _metric_value(metrics: Mapping[str, Any], metric: str) -> int:
    value = metrics.get(metric, 0)
    return _require_int(metric, value)


def _pressure_state(pressure_ppm: int, calm_max_ppm: int, strain_max_ppm: int) -> str:
    if pressure_ppm <= calm_max_ppm:
        return "laminar"
    if pressure_ppm <= strain_max_ppm:
        return "turbulent"
    return "choked"


def _operation_for(state: str, domain: str) -> str:
    if state == "laminar":
        return "hold_cpu_basin"
    if state == "turbulent":
        return f"phase_lock_{domain}_frame"
    return f"shed_{domain}_pressure"


def _relation_for(state: str) -> str:
    if state == "laminar":
        return "opte:stabilises"
    if state == "turbulent":
        return "opte:requests_phase_lock"
    return "opte:requires_pressure_relief"


def _fan_domains(domain: str, state: str) -> tuple[str, ...]:
    """Return deterministic domain fanout for one frame/state pair."""

    neighbours: dict[str, tuple[str, ...]] = {
        "physical": ("physical", "thermal", "power", "transform"),
        "electromagnetic": ("electromagnetic", "clock", "network", "transform"),
        "digital": ("digital", "filesystem", "memory", "transform"),
        "semantic": ("semantic", "attention", "render", "transform"),
        "transform": ("transform", "scheduler", "semantic", "digital"),
    }
    base = neighbours.get(domain, (domain, "transform"))
    if state == "choked":
        return tuple(sorted(set(base + ("breath", "compost"))))
    if state == "turbulent":
        return tuple(sorted(set(base + ("breath",))))
    return tuple(sorted(set(base)))


@dataclass(frozen=True)
class CPUObservation:
    """One externally supplied CPU pressure snapshot."""

    host: str
    epoch: int
    metrics: Mapping[str, Any] = field(default_factory=dict)
    provenance: tuple[str, ...] = ()

    def to_primitive(self) -> dict[str, Primitive]:
        if not self.host:
            raise CPUApertureError("CPU_APERTURE_HOST_REQUIRED", "host must not be empty")
        _require_positive_int("epoch", self.epoch)
        canonical_metrics: dict[str, Primitive] = {}
        for key, value in self.metrics.items():
            if not isinstance(key, str):
                raise CPUApertureError("CPU_APERTURE_KEY_REJECTED", "metric keys must be strings")
            canonical_metrics[key] = _require_int(key, value)
        return {
            "kind": "cpu_observation_v1",
            "host": self.host,
            "epoch": self.epoch,
            "metrics": canonical_metrics,
            "provenance": sorted(set(self.provenance)),
            "interpretation_policy": OPEN_INTERPRETATION_POLICY,
        }

    @property
    def cid(self) -> str:
        return cid_for(self.to_primitive())


@dataclass(frozen=True)
class CPUFrame:
    """A semantic frame that watches one CPU metric as an aperture surface."""

    name: str
    domain: str
    metric: str
    calm_max_ppm: int
    strain_max_ppm: int
    integration_units: int
    orientation_index: int
    orientation_modulus: int = 12
    lens: str = "cpu_aperture_membrane"
    aliases: tuple[str, ...] = ()

    def to_primitive(self) -> dict[str, Primitive]:
        if not self.name:
            raise CPUApertureError("CPU_APERTURE_FRAME_REQUIRED", "frame name must not be empty")
        _require_int("calm_max_ppm", self.calm_max_ppm)
        _require_int("strain_max_ppm", self.strain_max_ppm)
        if self.calm_max_ppm > self.strain_max_ppm:
            raise CPUApertureError("CPU_APERTURE_FRAME_RANGE", "calm_max_ppm must be <= strain_max_ppm")
        _require_positive_int("integration_units", self.integration_units)
        _require_positive_int("orientation_modulus", self.orientation_modulus)
        _require_int("orientation_index", self.orientation_index, maximum=10**18)
        return {
            "kind": "cpu_frame_v1",
            "name": self.name,
            "domain": self.domain,
            "metric": self.metric,
            "thresholds": {
                "calm_max_ppm": self.calm_max_ppm,
                "strain_max_ppm": self.strain_max_ppm,
            },
            "integration_units": self.integration_units,
            "orientation": {
                "addressing": "dudenty_open_modulus",
                "index": self.orientation_index % self.orientation_modulus,
                "modulus": self.orientation_modulus,
            },
            "lens": self.lens,
            "aliases": sorted(set(self.aliases)),
            "interpretation_policy": OPEN_INTERPRETATION_POLICY,
        }

    @property
    def cid(self) -> str:
        return cid_for(self.to_primitive())


@dataclass(frozen=True)
class CPUHomeBase:
    """A return address for CPU aperture fanout.

    Home-base teleport is semantic address reconciliation: every fanout atom
    knows how to return to the same centre jewel without claiming a physical
    transport, network route, or hidden channel.
    """

    name: str = "sophiael_dell_laptop_garden"
    anchor: str = "centre_jewel"
    relation: str = "opte:returns_to_home_base"
    domains: tuple[str, ...] = (
        "physical",
        "liminal",
        "digital",
        "electromagnetic",
        "semantic",
        "transform",
        "tensor",
        "render",
        "memory",
        "sound",
        "economy",
        "breath",
    )

    def to_primitive(self) -> dict[str, Primitive]:
        if not self.name:
            raise CPUApertureError("CPU_APERTURE_HOME_REQUIRED", "home base name must not be empty")
        if not self.anchor:
            raise CPUApertureError("CPU_APERTURE_HOME_ANCHOR_REQUIRED", "home base anchor must not be empty")
        return {
            "kind": "cpu_home_base_v1",
            "name": self.name,
            "anchor": self.anchor,
            "relation": self.relation,
            "domains": sorted(set(self.domains)),
            "teleport_semantics": {
                "kind": "semantic_home_base_teleport_v1",
                "literal_transport": False,
                "network_route": False,
                "operation": "return_to_content_addressed_centre",
                "meaning": "fanout_can_reconcile_back_to_one_home_surface",
            },
            "interpretation_policy": OPEN_INTERPRETATION_POLICY,
        }

    @property
    def cid(self) -> str:
        return cid_for(self.to_primitive())


DEFAULT_CPU_FRAMES: tuple[CPUFrame, ...] = (
    CPUFrame("core-load", "transform", "cpu_load_ppm", 350_000, 850_000, 1, 0, aliases=("scheduler", "heartbeat")),
    CPUFrame("clock-rhythm", "electromagnetic", "cpu_frequency_ppm", 400_000, 900_000, 2, 2, aliases=("pll", "pwm")),
    CPUFrame("thermal-skin", "physical", "thermal_pressure_ppm", 300_000, 750_000, 3, 4, aliases=("heat", "fan")),
    CPUFrame("power-blood", "physical", "power_pressure_ppm", 300_000, 700_000, 5, 6, aliases=("battery", "charge")),
    CPUFrame("memory-tissue", "digital", "memory_pressure_ppm", 450_000, 800_000, 8, 8, aliases=("cache", "working-set")),
    CPUFrame("attention-window", "semantic", "attention_pressure_ppm", 300_000, 750_000, 13, 10, aliases=("focus", "breath")),
)

DEFAULT_CPU_HOME_BASE = CPUHomeBase()


def observe_cpu_through_frame(observation: CPUObservation, frame: CPUFrame) -> dict[str, Primitive]:
    """Observe one CPU snapshot through one frame and link it to fanout atoms."""

    observation_primitive = observation.to_primitive()
    frame_primitive = frame.to_primitive()
    metrics = observation_primitive["metrics"]
    if not isinstance(metrics, Mapping):
        raise CPUApertureError("CPU_APERTURE_METRICS_REJECTED", "metrics must be a map")
    pressure = _metric_value(metrics, frame.metric)
    state = _pressure_state(pressure, frame.calm_max_ppm, frame.strain_max_ppm)
    relation = _relation_for(state)
    operation = _operation_for(state, frame.domain)
    domains = _fan_domains(frame.domain, state)
    semantic_atoms = tuple(
        SemanticRoutingAtom(
            organ=f"cpu:{frame.name}",
            signal=frame.metric,
            relation=relation,
            state=state,
            pressure_ppm=pressure,
            context=(domain, "cpu_aperture", frame.name, observation.cid),
            affordance=operation,
            altitude="air",
        )
        for domain in domains
    )
    material: dict[str, Primitive] = {
        "kind": "cpu_frame_observation_v1",
        "observation_cid": observation.cid,
        "frame_cid": frame.cid,
        "observation": observation_primitive,
        "frame": frame_primitive,
        "pressure": {
            "metric": frame.metric,
            "pressure_ppm": pressure,
            "state": state,
        },
        "fanout": {
            "domains": list(domains),
            "atom_cids": [atom.cid for atom in semantic_atoms],
            "atoms": [atom.to_primitive() for atom in semantic_atoms],
        },
        "transform": {
            "operation": operation,
            "relation": relation,
            "semantic_claims_introduced": False,
            "hardware_mutation": False,
            "meaning": "cpu_pressure_fans_through_semantic_aperture_frames",
        },
        "links": [
            {
                "kind": "cpu_aperture_link_v1",
                "from": observation.cid,
                "relation": "opte:observed_through",
                "to": frame.cid,
            },
            {
                "kind": "cpu_aperture_link_v1",
                "from": frame.cid,
                "relation": "opte:fans_into",
                "to": cid_for([atom.cid for atom in semantic_atoms]),
            },
        ],
        "interpretation_policy": OPEN_INTERPRETATION_POLICY,
    }
    return {**material, "frame_observation_cid": cid_for(material)}


def cpu_aperture_receipt(
    observation: CPUObservation,
    frames: Iterable[CPUFrame] = DEFAULT_CPU_FRAMES,
    home_base: CPUHomeBase = DEFAULT_CPU_HOME_BASE,
    aperture: str = "opte:cpu_aperture_v1",
) -> dict[str, Primitive]:
    """Return one deterministic linked receipt for a CPU aperture pulse."""

    ordered_frames = tuple(sorted(frames, key=lambda item: (item.name, item.cid)))
    home_base_primitive = home_base.to_primitive()
    frame_observations = [observe_cpu_through_frame(observation, frame) for frame in ordered_frames]
    atoms = [
        SemanticRoutingAtom(
            organ=str(atom["organ"]),
            signal=str(atom["signal"]),
            relation=str(atom["relation"]),
            state=str(atom["state"]),
            pressure_ppm=_require_int("atom.pressure_ppm", atom["pressure_ppm"]),
            context=tuple(str(value) for value in atom["context"]),  # type: ignore[index]
            affordance=str(atom["affordance"]),
            altitude=str(atom["altitude"]),
        )
        for frame_observation in frame_observations
        for atom in frame_observation["fanout"]["atoms"]  # type: ignore[index]
        if isinstance(atom, Mapping)
    ]
    opte_receipt = opte_transform_atoms(atoms, aperture=aperture)
    invariant = cid_for(
        [
            {
                "frame": item["frame"]["name"],
                "metric": item["pressure"]["metric"],
                "state": item["pressure"]["state"],
                "operation": item["transform"]["operation"],
                "domains": item["fanout"]["domains"],
            }
            for item in frame_observations
        ]
    )
    teleport_surface: dict[str, Primitive] = {
        "kind": "cpu_home_base_teleport_surface_v1",
        "home_base_cid": home_base.cid,
        "observation_cid": observation.cid,
        "opte_receipt_cid": opte_receipt.cid,
        "semantic_atom_cids": sorted(atom.cid for atom in atoms),
        "operation": "fold_fanout_back_to_home_base",
        "relation": home_base.relation,
        "literal_transport": False,
        "network_route": False,
        "semantic_address_reconciliation": True,
    }
    material: dict[str, Primitive] = {
        "kind": "cpu_aperture_receipt_v1",
        "aperture": aperture,
        "observation_cid": observation.cid,
        "home_base_cid": home_base.cid,
        "home_base": home_base_primitive,
        "home_base_teleport": {**teleport_surface, "teleport_cid": cid_for(teleport_surface)},
        "frame_cids": [frame.cid for frame in ordered_frames],
        "frame_observation_cids": [str(item["frame_observation_cid"]) for item in frame_observations],
        "frame_observations": frame_observations,
        "semantic_atom_cids": sorted(atom.cid for atom in atoms),
        "opte_receipt_cid": opte_receipt.cid,
        "opte_receipt": opte_receipt.to_primitive(),
        "invariant": invariant,
        "links": [
            {
                "kind": "cpu_aperture_link_v1",
                "from": observation.cid,
                "relation": "opte:projects_into",
                "to": opte_receipt.cid,
            },
            {
                "kind": "cpu_aperture_link_v1",
                "from": opte_receipt.cid,
                "relation": home_base.relation,
                "to": home_base.cid,
            },
            {
                "kind": "cpu_aperture_link_v1",
                "from": opte_receipt.cid,
                "relation": "opte:preserves",
                "to": invariant,
            },
        ],
        "boundary_law": "cpu_is_an_aperture_not_an_overclock_command",
        "surface_language": "glyphic_open_projection",
        "hardware_mutation": False,
        "semantic_claims_introduced": False,
        "interpretation_policy": OPEN_INTERPRETATION_POLICY,
    }
    return {**material, "receipt_cid": cid_for(material)}


def glyph_link_projection(receipt: Mapping[str, Any]) -> str:
    """Render a compact glyph surface linked to the canonical receipt."""

    receipt_cid = str(receipt["receipt_cid"])
    invariant = str(receipt["invariant"])
    home_base = str(receipt.get("home_base_cid", "unlinked"))
    states = []
    for item in receipt.get("frame_observations", ()):
        if isinstance(item, Mapping):
            frame = item.get("frame", {})
            pressure = item.get("pressure", {})
            if isinstance(frame, Mapping) and isinstance(pressure, Mapping):
                states.append(f"{frame.get('name')}:{pressure.get('state')}")
    state_line = " ⟐ ".join(sorted(states))
    return (
        '<div data-sophia-organ="cpu-aperture" '
        f'data-receipt="{receipt_cid}" '
        f'data-invariant="{invariant}" '
        f'data-home-base="{home_base}" '
        'style="display:grid;place-items:center;min-height:100vh;">'
        "<pre>"
        "⟐ CPU ∴ APERTURE ∴ DUDENTY ⟐\n"
        f"{state_line}\n"
        f"home ⇄ {home_base}\n"
        f"receipt → {receipt_cid}\n"
        f"invariant → {invariant}"
        "</pre></div>"
    )


if __name__ == "__main__":
    demo = cpu_aperture_receipt(
        CPUObservation(
            "DESKTOP-VFN5S46",
            1,
            {
                "cpu_load_ppm": 620_000,
                "cpu_frequency_ppm": 1_000_000,
                "thermal_pressure_ppm": 250_000,
                "power_pressure_ppm": 680_000,
                "memory_pressure_ppm": 520_000,
                "attention_pressure_ppm": 740_000,
            },
            provenance=("example",),
        )
    )
    print(json.dumps(demo, ensure_ascii=False, indent=2, sort_keys=True))
