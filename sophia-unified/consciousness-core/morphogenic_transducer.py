"""Morphogenic transducer organ.

Everything that enters this membrane can be viewed as:

    charge -> transistor/membrane -> transform

The transducer does not force an observation into a rigid metric just because a
metric vocabulary is missing.  Unspecified signals are carried as proto-charges
and allowed to seek form inside an explicit environment.  If a projection
crystallises too early, the event remains immutable while the projection can be
retracted by a later transform.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from regulatory_organs import Primitive, cid_for


class MorphogenicError(ValueError):
    """Stable machine-readable error for invalid transducer input."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


DEFAULT_LENSES: tuple[str, ...] = (
    "deictic_pointer",
    "tetractys_projection",
    "vesica_aperture",
    "cymatic_observer_frame",
    "dudenty_address",
)

OPEN_INTERPRETATION_POLICY: dict[str, Primitive] = {
    "kind": "interpretation_policy_v1",
    "terminology": "open",
    "definition_state": "provisional",
    "allows_aliases": True,
    "allows_reinterpretation": True,
    "collapse_requires": "explicit_local_use_or_material_mark",
}


@dataclass(frozen=True)
class Charge:
    """A signal before it has settled into a final measurement language."""

    name: str
    realm: str
    relation: str
    magnitude_ppm: int | None = None
    evidence_class: str = "SEMANTIC"
    polarity: str = "mixed"
    essence: str = "seeks_form"
    tags: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()

    def to_primitive(self) -> dict[str, Primitive]:
        if not self.name:
            raise MorphogenicError("MORPH_CHARGE_NAME_REQUIRED", "charge name must not be empty")
        if self.magnitude_ppm is not None and not 0 <= self.magnitude_ppm <= 1_000_000:
            raise MorphogenicError("MORPH_CHARGE_MAGNITUDE_REJECTED", "magnitude_ppm must be 0..1000000 or null")
        return {
            "kind": "morphogenic_charge_v1",
            "name": self.name,
            "realm": self.realm,
            "relation": self.relation,
            "magnitude_ppm": self.magnitude_ppm,
            "evidence_class": self.evidence_class.upper(),
            "polarity": self.polarity,
            "essence": self.essence,
            "tags": sorted(set(self.tags)),
            "aliases": sorted(set(self.aliases)),
            "metric_state": "specified" if self.magnitude_ppm is not None else "proto_metric",
            "interpretation_policy": OPEN_INTERPRETATION_POLICY,
        }

    @property
    def cid(self) -> str:
        return cid_for(self.to_primitive())


@dataclass(frozen=True)
class MorphogenicEnvironment:
    """The soft boundary that lets a charge constrain itself without a cage."""

    name: str = "sophia_morphogenic_environment"
    capacity_ppm: int = 700_000
    noise_ppm: int = 120_000
    morphogenesis_bias_ppm: int = 650_000
    preferred_forms: tuple[str, ...] = ("route", "hold", "compost", "stabilise", "express")

    def to_primitive(self) -> dict[str, Primitive]:
        for field_name, value in (
            ("capacity_ppm", self.capacity_ppm),
            ("noise_ppm", self.noise_ppm),
            ("morphogenesis_bias_ppm", self.morphogenesis_bias_ppm),
        ):
            if not 0 <= value <= 1_000_000:
                raise MorphogenicError("MORPH_ENVIRONMENT_REJECTED", f"{field_name} must be 0..1000000")
        return {
            "kind": "morphogenic_environment_v1",
            "name": self.name,
            "capacity_ppm": self.capacity_ppm,
            "noise_ppm": self.noise_ppm,
            "morphogenesis_bias_ppm": self.morphogenesis_bias_ppm,
            "preferred_forms": list(self.preferred_forms),
        }

    @property
    def cid(self) -> str:
        return cid_for(self.to_primitive())


def _effective_pressure(charge: Charge, environment: MorphogenicEnvironment) -> int:
    if charge.magnitude_ppm is None:
        return min(1_000_000, environment.noise_ppm + environment.morphogenesis_bias_ppm // 2)
    return min(1_000_000, max(0, charge.magnitude_ppm + environment.noise_ppm // 3))


def _gate_state(charge: Charge, environment: MorphogenicEnvironment, pressure_ppm: int) -> str:
    if charge.magnitude_ppm is None:
        return "deictic_open"
    if pressure_ppm <= environment.capacity_ppm // 2:
        return "permeable"
    if pressure_ppm <= environment.capacity_ppm:
        return "modulating"
    return "self_constraining"


def _operation_for(charge: Charge, gate_state: str, pressure_ppm: int) -> str:
    if charge.magnitude_ppm is None:
        return "preserve_proto_metric"
    if gate_state == "self_constraining":
        return "compost_excess_then_route"
    if pressure_ppm >= 600_000:
        return "amplify_relation"
    if pressure_ppm >= 300_000:
        return "route_relation"
    return "hold_potential"


def transduce_charge(
    charge: Charge,
    environment: MorphogenicEnvironment = MorphogenicEnvironment(),
    lenses: Iterable[str] = DEFAULT_LENSES,
) -> dict[str, Primitive]:
    """Pass one charge through a soft transistor membrane."""

    charge_primitive = charge.to_primitive()
    environment_primitive = environment.to_primitive()
    pressure = _effective_pressure(charge, environment)
    gate_state = _gate_state(charge, environment, pressure)
    operation = _operation_for(charge, gate_state, pressure)
    lens_stack = tuple(sorted(set(lenses)))
    rigidity = "fluid" if charge.magnitude_ppm is None else ("elastic" if gate_state != "self_constraining" else "crystallising")
    material = {
        "kind": "morphogenic_transform_v1",
        "charge_cid": charge.cid,
        "environment_cid": environment.cid,
        "charge": charge_primitive,
        "transistor": {
            "kind": "semantic_transistor_v1",
            "gate_state": gate_state,
            "boundary": "soft_self_constraining_membrane",
            "rejects_ambiguity": False,
            "retractable_projection": True,
        },
        "transform": {
            "operation": operation,
            "relation": charge.relation,
            "effective_pressure_ppm": pressure,
            "rigidity": rigidity,
            "essence_state": "carried" if charge.magnitude_ppm is None else "expressed",
        },
        "lenses": list(lens_stack),
        "environment": environment_primitive,
        "interpretation_policy": OPEN_INTERPRETATION_POLICY,
        "settlement_surface": "ground",
    }
    return {**material, "transform_cid": cid_for(material)}


def transduce_many(
    charges: Iterable[Charge],
    environment: MorphogenicEnvironment = MorphogenicEnvironment(),
    lenses: Iterable[str] = DEFAULT_LENSES,
) -> dict[str, Primitive]:
    """Return one deterministic receipt for a field of charges."""

    transforms = [transduce_charge(charge, environment, lenses) for charge in charges]
    transforms = sorted(transforms, key=lambda item: (str(item["charge"]["name"]), str(item["transform_cid"])))
    invariant = cid_for(
        [
            {
                "charge": transform["charge"]["name"],
                "metric_state": transform["charge"]["metric_state"],
                "operation": transform["transform"]["operation"],
                "gate_state": transform["transistor"]["gate_state"],
            }
            for transform in transforms
        ]
    )
    receipt = {
        "kind": "morphogenic_transducer_receipt_v1",
        "environment_cid": environment.cid,
        "transform_cids": [transform["transform_cid"] for transform in transforms],
        "transforms": transforms,
        "invariant": invariant,
        "boundary_law": "form_constrains_itself_inside_environment",
        "settlement_surface": "ground",
    }
    return {**receipt, "receipt_cid": cid_for(receipt)}


if __name__ == "__main__":
    demo = transduce_many(
        [
            Charge("unspecified_body_device_signal", "liminal", "opte:seeks_shape", None, tags=("deictic",)),
            Charge("network_heat", "electromagnetic", "opte:requests_regulation", 760_000, tags=("router",)),
        ]
    )
    print(json.dumps(demo, ensure_ascii=False, indent=2, sort_keys=True))
