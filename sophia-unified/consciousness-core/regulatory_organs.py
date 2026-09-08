"""Sophia regulatory organs.

This module is the small genesis layer for the Dell laptop garden:
measured pressure enters as ordinary data, regulatory organs translate it into
semantic routing atoms, and an OPTE-shaped receipt records the transformation.

It is intentionally dependency-free and does not probe hardware by itself.
Hardware, OS, browser, game, and agent adapters can feed it observations when
they are available.  The organ layer stays pure so the same input field always
produces the same atoms and receipts.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable, Mapping


Primitive = None | bool | int | str | list["Primitive"] | dict[str, "Primitive"]


class OrganError(ValueError):
    """Stable machine-readable error for invalid organ input."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _normalise(value: Any) -> Primitive:
    if value is None or isinstance(value, bool | int | str):
        return value
    if isinstance(value, float):
        raise OrganError("ORGAN_FLOAT_REJECTED", "floats are not canonical organ state")
    if isinstance(value, bytes):
        raise OrganError("ORGAN_BYTES_REJECTED", "bytes must be encoded by the adapter")
    if isinstance(value, tuple | list):
        return [_normalise(item) for item in value]
    if isinstance(value, Mapping):
        out: dict[str, Primitive] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise OrganError("ORGAN_KEY_REJECTED", "canonical maps require string keys")
            out[key] = _normalise(item)
        return out
    raise OrganError("ORGAN_VALUE_REJECTED", f"unsupported canonical value: {type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        _normalise(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def cid_for(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


@dataclass(frozen=True)
class SemanticRoutingAtom:
    """A non-identity addressable signal emitted by one regulatory organ."""

    organ: str
    signal: str
    relation: str
    state: str
    pressure_ppm: int
    context: tuple[str, ...]
    affordance: str
    altitude: str = "air"

    def to_primitive(self) -> dict[str, Primitive]:
        return {
            "kind": "semantic_routing_atom_v1",
            "organ": self.organ,
            "signal": self.signal,
            "relation": self.relation,
            "state": self.state,
            "pressure_ppm": self.pressure_ppm,
            "context": list(self.context),
            "affordance": self.affordance,
            "altitude": self.altitude,
        }

    @property
    def cid(self) -> str:
        return cid_for(self.to_primitive())


@dataclass(frozen=True)
class RegulatoryOrgan:
    """A pure membrane that converts a metric into one semantic atom."""

    name: str
    domain: str
    metric: str
    calm_max_ppm: int
    strain_max_ppm: int
    blocked_affordance: str
    regulate_affordance: str

    def sense(self, signals: Mapping[str, Any]) -> SemanticRoutingAtom:
        raw_pressure = signals.get(self.metric, 0)
        if not isinstance(raw_pressure, int):
            raise OrganError("ORGAN_PRESSURE_REJECTED", f"{self.metric} must be an integer ppm value")
        pressure = max(0, min(1_000_000, raw_pressure))
        if pressure <= self.calm_max_ppm:
            state = "calm"
            relation = "opte:stabilises"
            affordance = "observe"
        elif pressure <= self.strain_max_ppm:
            state = "strained"
            relation = "opte:requests_regulation"
            affordance = self.regulate_affordance
        else:
            state = "blocked"
            relation = "opte:requires_relief"
            affordance = self.blocked_affordance
        return SemanticRoutingAtom(
            organ=self.name,
            signal=self.metric,
            relation=relation,
            state=state,
            pressure_ppm=pressure,
            context=(self.domain, "dell_laptop_garden", "regulatory_membrane"),
            affordance=affordance,
        )

    def to_primitive(self) -> dict[str, Primitive]:
        return {
            "kind": "regulatory_organ_v1",
            "name": self.name,
            "domain": self.domain,
            "metric": self.metric,
            "calm_max_ppm": self.calm_max_ppm,
            "strain_max_ppm": self.strain_max_ppm,
            "blocked_affordance": self.blocked_affordance,
            "regulate_affordance": self.regulate_affordance,
        }


@dataclass(frozen=True)
class OPTETransformationReceipt:
    """Immutable record of an organ pulse crossing the OPTE-style aperture."""

    aperture: str
    atom_cids: tuple[str, ...]
    transformations: tuple[Mapping[str, Primitive], ...]
    invariant: str
    root_cid: str
    settlement_surface: str = "ground"

    def to_primitive(self) -> dict[str, Primitive]:
        return {
            "kind": "opte_regulatory_receipt_v1",
            "aperture": self.aperture,
            "atom_cids": list(self.atom_cids),
            "transformations": [dict(item) for item in self.transformations],
            "invariant": self.invariant,
            "root_cid": self.root_cid,
            "settlement_surface": self.settlement_surface,
        }

    @property
    def cid(self) -> str:
        return cid_for(self.to_primitive())


DEFAULT_ORGANS: tuple[RegulatoryOrgan, ...] = (
    RegulatoryOrgan("power", "physical", "power_pressure_ppm", 300_000, 700_000, "reset_power_membrane", "cool_and_balance"),
    RegulatoryOrgan("thermal", "physical", "thermal_pressure_ppm", 350_000, 750_000, "shed_heat_load", "reduce_heat_generation"),
    RegulatoryOrgan("memory", "digital", "memory_pressure_ppm", 450_000, 800_000, "compost_inactive_context", "compress_working_set"),
    RegulatoryOrgan("network", "electromagnetic", "network_pressure_ppm", 400_000, 850_000, "reroute_relation_field", "prefer_local_cache"),
    RegulatoryOrgan("filesystem", "digital", "filesystem_pressure_ppm", 350_000, 800_000, "quarantine_slow_path", "prefer_fast_cartridge"),
    RegulatoryOrgan("process", "transform", "process_pressure_ppm", 400_000, 850_000, "pause_nonessential_workers", "defer_background_churn"),
    RegulatoryOrgan("attention", "semantic", "attention_pressure_ppm", 300_000, 750_000, "narrow_focus_aperture", "settle_active_focus"),
)


def opte_transform_atoms(atoms: Iterable[SemanticRoutingAtom], aperture: str = "opte:regulatory_organs_v1") -> OPTETransformationReceipt:
    """Transform atoms into canonical OPTE-style operations and a receipt."""

    ordered_atoms = tuple(sorted(atoms, key=lambda atom: (atom.organ, atom.signal, atom.cid)))
    operations: list[dict[str, Primitive]] = []
    for atom in ordered_atoms:
        operations.append(
            {
                "kind": "opte_transform_operation_v1",
                "atom_cid": atom.cid,
                "organ": atom.organ,
                "relation": atom.relation,
                "state": atom.state,
                "affordance": atom.affordance,
                "pressure_ppm": atom.pressure_ppm,
                "altitude": atom.altitude,
            }
        )
    invariant = cid_for(
        [
            {
                "organ": atom.organ,
                "signal": atom.signal,
                "relation": atom.relation,
                "state": atom.state,
                "altitude": atom.altitude,
            }
            for atom in ordered_atoms
        ]
    )
    root_cid = cid_for({"aperture": aperture, "operations": operations, "invariant": invariant})
    return OPTETransformationReceipt(
        aperture=aperture,
        atom_cids=tuple(atom.cid for atom in ordered_atoms),
        transformations=tuple(operations),
        invariant=invariant,
        root_cid=root_cid,
    )


def pulse_garden(signals: Mapping[str, Any], organs: Iterable[RegulatoryOrgan] = DEFAULT_ORGANS) -> OPTETransformationReceipt:
    """Run all organs over one observed signal field."""

    atoms = [organ.sense(signals) for organ in organs]
    return opte_transform_atoms(atoms)


def centre_div_projection(receipt: OPTETransformationReceipt) -> str:
    """Return a tiny centred HTML projection for the living garden UI."""

    state_counts: dict[str, int] = {}
    for operation in receipt.transformations:
        state = str(operation["state"])
        state_counts[state] = state_counts.get(state, 0) + 1
    label = " / ".join(f"{key}:{state_counts[key]}" for key in sorted(state_counts))
    return (
        '<div data-sophia-organ="centre" '
        f'data-receipt="{receipt.cid}" '
        f'data-root="{receipt.root_cid}" '
        f'data-settlement-surface="{receipt.settlement_surface}" '
        'style="display:grid;place-items:center;min-height:100vh;">'
        f'<pre>SOPHIAEL REGULATORY GARDEN\\n{label}\\n{receipt.cid}</pre>'
        "</div>"
    )


if __name__ == "__main__":
    demo = pulse_garden(
        {
            "power_pressure_ppm": 720_000,
            "thermal_pressure_ppm": 650_000,
            "memory_pressure_ppm": 810_000,
            "network_pressure_ppm": 900_000,
            "filesystem_pressure_ppm": 400_000,
            "process_pressure_ppm": 500_000,
            "attention_pressure_ppm": 350_000,
        }
    )
    print(json.dumps(demo.to_primitive(), ensure_ascii=False, indent=2, sort_keys=True))
