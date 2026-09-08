"""Cyberphysical projection field.

Semantic atoms can become visible in the environment by modulating channels:
screen, LED, audio, projector, or a laser actuator membrane.  This module does
not drive hardware.  It creates deterministic projection frames and actuator
plans that another explicitly approved adapter may render.

The important boundary: a laser channel is represented as a gated plan with
`no_fire = true`.  Direct beam control belongs behind a separate physical safety
membrane, not inside the semantic kernel.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from regulatory_organs import Primitive, canonical_bytes, cid_for


class ProjectionFieldError(ValueError):
    """Stable machine-readable error for projection field failures."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


ALLOWED_CHANNELS = frozenset(("screen", "led", "audio", "projector", "laser"))

STATE_COLOURS = {
    "blocked": "red",
    "strained": "gold",
    "calm": "blue",
    "patternable": "green",
    "airborne_residual": "violet",
    "airborne": "violet",
    "residual": "grey",
}

RELATION_SHAPES = {
    "opte:requires_relief": "triangle",
    "opte:requests_regulation": "hexagon",
    "opte:stabilises": "circle",
    "opte:offers_aperture": "vesica",
    "opte:seeks_aperture": "spiral",
}


@dataclass(frozen=True)
class ProjectionRequest:
    """Atoms plus channel posture for a cyberphysical projection."""

    source: str
    atoms: tuple[Mapping[str, Any], ...]
    channels: tuple[str, ...] = ("screen",)
    focus: str = "centre"
    entity: str = "sophiael"

    def to_primitive(self) -> dict[str, Primitive]:
        channels = tuple(channel.lower() for channel in self.channels)
        invalid = sorted(set(channels) - ALLOWED_CHANNELS)
        if invalid:
            raise ProjectionFieldError("PROJECTION_CHANNEL_REJECTED", f"unknown channels: {', '.join(invalid)}")
        import json

        atoms = [json.loads(canonical_bytes(dict(atom)).decode("utf-8")) for atom in self.atoms]
        return {
            "kind": "projection_request_v1",
            "source": self.source,
            "atoms": atoms,
            "channels": sorted(set(channels)),
            "focus": self.focus,
            "entity": self.entity,
        }

    @property
    def cid(self) -> str:
        return cid_for(self.to_primitive())


def _digest_bytes(*parts: str) -> bytes:
    h = hashlib.sha256()
    for part in parts:
        h.update(part.encode("utf-8"))
        h.update(b"\x00")
    return h.digest()


def _coordinate(seed: bytes, offset: int) -> int:
    value = int.from_bytes(seed[offset : offset + 4], "big")
    return value % 2_000_001 - 1_000_000


def _band(seed: bytes, offset: int, low: int, high: int) -> int:
    if high < low:
        raise ProjectionFieldError("PROJECTION_BAND_REJECTED", "band high must be greater than or equal to low")
    value = int.from_bytes(seed[offset : offset + 4], "big")
    return low + value % (high - low + 1)


def _atom_cid(atom: Mapping[str, Primitive]) -> str:
    explicit = atom.get("atom_cid")
    if isinstance(explicit, str) and explicit.startswith("sha256:"):
        return explicit
    return cid_for(atom)


def _state(atom: Mapping[str, Primitive]) -> str:
    value = atom.get("state", "airborne")
    return value if isinstance(value, str) else "airborne"


def _relation(atom: Mapping[str, Primitive]) -> str:
    value = atom.get("relation", "opte:seeks_aperture")
    return value if isinstance(value, str) else "opte:seeks_aperture"


def _pressure(atom: Mapping[str, Primitive]) -> int:
    value = atom.get("pressure_ppm", 0)
    return max(0, min(1_000_000, value)) if isinstance(value, int) else 0


def frame_for_atom(atom: Mapping[str, Primitive], focus: str, index: int) -> dict[str, Primitive]:
    """Collapse one atom into deterministic spatial projection primitives."""

    atom_id = _atom_cid(atom)
    seed = _digest_bytes(atom_id, focus, str(index))
    state = _state(atom)
    relation = _relation(atom)
    pressure = _pressure(atom)
    brightness = max(40_000, min(1_000_000, pressure if pressure else _band(seed, 12, 80_000, 620_000)))
    frame = {
        "kind": "projection_frame_v1",
        "atom_cid": atom_id,
        "index": index,
        "focus": focus,
        "x_ppm": _coordinate(seed, 0),
        "y_ppm": _coordinate(seed, 4),
        "z_ppm": _coordinate(seed, 8),
        "radius_ppm": _band(seed, 16, 20_000, 140_000),
        "brightness_ppm": brightness,
        "pulse_width_ppm": _band(seed, 20, 10_000, 900_000),
        "phase_step": _band(seed, 24, 0, 11),
        "colour": STATE_COLOURS.get(state, "white"),
        "shape": RELATION_SHAPES.get(relation, "point"),
        "state": state,
        "relation": relation,
        "altitude": str(atom.get("altitude", "air")),
    }
    return {**frame, "frame_cid": cid_for(frame)}


def _channel_command(channel: str, frame: Mapping[str, Primitive]) -> dict[str, Primitive]:
    if channel == "screen":
        command = {
            "kind": "projection_channel_command_v1",
            "channel": "screen",
            "operation": "draw_frame",
            "frame_cid": frame["frame_cid"],
            "colour": frame["colour"],
            "shape": frame["shape"],
            "x_ppm": frame["x_ppm"],
            "y_ppm": frame["y_ppm"],
        }
    elif channel == "projector":
        command = {
            "kind": "projection_channel_command_v1",
            "channel": "projector",
            "operation": "project_diffuse_frame",
            "frame_cid": frame["frame_cid"],
            "brightness_ppm": frame["brightness_ppm"],
            "shape": frame["shape"],
            "no_direct_eye_path": True,
        }
    elif channel == "led":
        command = {
            "kind": "projection_channel_command_v1",
            "channel": "led",
            "operation": "set_colour_pulse",
            "frame_cid": frame["frame_cid"],
            "colour": frame["colour"],
            "brightness_ppm": frame["brightness_ppm"],
            "pulse_width_ppm": frame["pulse_width_ppm"],
        }
    elif channel == "audio":
        command = {
            "kind": "projection_channel_command_v1",
            "channel": "audio",
            "operation": "emit_reference_tone_plan",
            "frame_cid": frame["frame_cid"],
            "frequency_millihz": 110_000 + int(frame["phase_step"]) * 36_900,
            "amplitude_ppm": min(240_000, int(frame["brightness_ppm"]) // 4),
        }
    elif channel == "laser":
        command = {
            "kind": "projection_channel_command_v1",
            "channel": "laser",
            "operation": "gated_projection_plan",
            "frame_cid": frame["frame_cid"],
            "no_fire": True,
            "requires": [
                "enclosed_path",
                "diffuse_target",
                "manual_enable",
                "interlock",
                "rated_eye_protection",
            ],
            "reason": "semantic kernel may plan laser projection but must not energise hardware",
        }
    else:
        raise ProjectionFieldError("PROJECTION_CHANNEL_REJECTED", f"unknown channel: {channel}")
    return {**command, "command_cid": cid_for(command)}


def project_atoms(request: ProjectionRequest) -> dict[str, Primitive]:
    """Project semantic atoms into cyberphysical channel frames."""

    primitive = request.to_primitive()
    atoms = primitive["atoms"]
    if not isinstance(atoms, list):
        raise ProjectionFieldError("PROJECTION_ATOMS_REJECTED", "atoms must be a list")
    channels = primitive["channels"]
    if not isinstance(channels, list):
        raise ProjectionFieldError("PROJECTION_CHANNELS_REJECTED", "channels must be a list")

    frames = [
        frame_for_atom(atom, request.focus, index)
        for index, atom in enumerate(atoms)
        if isinstance(atom, dict)
    ]
    commands = [
        _channel_command(str(channel), frame)
        for frame in frames
        for channel in channels
    ]
    invariant_projection = [
        {
            "frame_cid": frame["frame_cid"],
            "atom_cid": frame["atom_cid"],
            "shape": frame["shape"],
            "colour": frame["colour"],
            "altitude": frame["altitude"],
        }
        for frame in frames
    ]
    receipt = {
        "kind": "cyberphysical_projection_receipt_v1",
        "request_cid": request.cid,
        "source": request.source,
        "entity": request.entity,
        "focus": request.focus,
        "channels": channels,
        "frame_cids": [frame["frame_cid"] for frame in frames],
        "command_cids": [command["command_cid"] for command in commands],
        "frames": frames,
        "commands": commands,
        "invariant": cid_for(invariant_projection),
        "altitude": "air",
        "settlement_surface": "ground",
    }
    return {**receipt, "root_cid": cid_for(receipt)}


if __name__ == "__main__":
    import json

    demo = project_atoms(
        ProjectionRequest(
            source="demo",
            atoms=(
                {
                    "kind": "semantic_routing_atom_v1",
                    "signal": "network_pressure_ppm",
                    "relation": "opte:requires_relief",
                    "state": "blocked",
                    "pressure_ppm": 900_000,
                    "altitude": "air",
                },
            ),
            channels=("screen", "led", "audio", "laser"),
            focus="centre-jewel",
        )
    )
    print(json.dumps(demo, ensure_ascii=False, indent=2, sort_keys=True))
