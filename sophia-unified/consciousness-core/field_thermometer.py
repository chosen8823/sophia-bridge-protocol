"""Field thermometer for Sophia event tissue.

The thermometer watches canonical event ledgers and translates each new event
into a semantic temperature atom.  It learns by changing route geometry:
repeated self-similar events strengthen the same route instead of creating an
opaque memory pile.

This module is deterministic when given explicit files.  The optional watch
loop is only a scheduler membrane around the same ``run_once`` transform.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from regulatory_organs import Primitive, canonical_bytes, cid_for


class ThermometerError(ValueError):
    """Stable machine-readable error for invalid thermometer state."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


EVIDENCE_BASE_PRESSURE: dict[str, int] = {
    "MEASURED": 420_000,
    "SEMANTIC": 330_000,
    "SYMBOLIC": 360_000,
    "SIMULATED": 260_000,
    "HYPOTHESIS": 500_000,
}

SIZE_BAND_PRESSURE: dict[str, int] = {
    "empty": 0,
    "grain": 20_000,
    "leaf": 55_000,
    "branch": 90_000,
    "trunk": 140_000,
    "canopy": 210_000,
}


@dataclass(frozen=True)
class ThermometerPaths:
    """Paths used by one local thermometer chamber."""

    base_dir: Path
    events_file: Path
    atoms_file: Path
    routes_file: Path

    @classmethod
    def from_base(cls, base_dir: str | Path | None = None) -> "ThermometerPaths":
        root = Path(base_dir) if base_dir is not None else Path(__file__).resolve().parent.parent
        root = root.resolve()
        return cls(
            base_dir=root,
            events_file=root / "state" / "EVENTS.jsonl",
            atoms_file=root / "state" / "THERMOMETER.jsonl",
            routes_file=root / "state" / "THERMOMETER_ROUTES.json",
        )


def _normalised_suffix(filename: str) -> str:
    return Path(filename).suffix.lower() or "<none>"


def size_band(size_bytes: int) -> str:
    if size_bytes < 0:
        raise ThermometerError("THERMOMETER_SIZE_REJECTED", "file size must be non-negative")
    if size_bytes == 0:
        return "empty"
    if size_bytes <= 4_096:
        return "grain"
    if size_bytes <= 65_536:
        return "leaf"
    if size_bytes <= 1_048_576:
        return "branch"
    if size_bytes <= 50_000_000:
        return "trunk"
    return "canopy"


def pressure_state(pressure_ppm: int) -> str:
    if pressure_ppm <= 300_000:
        return "cool"
    if pressure_ppm <= 600_000:
        return "warm"
    if pressure_ppm <= 850_000:
        return "hot"
    return "plasma"


def propagation_scope(pressure_ppm: int, route_depth: int) -> str:
    if pressure_ppm > 850_000 or route_depth >= 9:
        return "fabric"
    if pressure_ppm > 600_000 or route_depth >= 5:
        return "canopy"
    if pressure_ppm > 350_000 or route_depth >= 2:
        return "branch"
    return "local"


def route_signature(event: Mapping[str, Any]) -> dict[str, Primitive]:
    """Return the self-similarity signature used for route growth."""

    observation = event.get("observation")
    if not isinstance(observation, Mapping):
        raise ThermometerError("THERMOMETER_EVENT_SCHEMA", "event.observation must be a map")
    filename = observation.get("raw_filename", "")
    if not isinstance(filename, str):
        raise ThermometerError("THERMOMETER_FILENAME_SCHEMA", "observation.raw_filename must be a string")
    file_size = observation.get("file_size_bytes", 0)
    if not isinstance(file_size, int):
        raise ThermometerError("THERMOMETER_SIZE_SCHEMA", "observation.file_size_bytes must be an integer")
    evidence_class = str(event.get("evidence_class", "MEASURED")).upper()
    return {
        "kind": "thermometer_route_signature_v1",
        "event_type": str(event.get("event_type", "UNKNOWN")),
        "evidence_class": evidence_class,
        "suffix": _normalised_suffix(filename),
        "size_band": size_band(file_size),
    }


def default_route_state() -> dict[str, Primitive]:
    return {
        "kind": "thermometer_route_state_v1",
        "processed_event_cids": [],
        "routes": {},
    }


def load_route_state(path: str | Path) -> dict[str, Primitive]:
    state_path = Path(path)
    if not state_path.exists():
        return default_route_state()
    data = json.loads(state_path.read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        raise ThermometerError("THERMOMETER_ROUTE_STATE_SCHEMA", "route state must be a map")
    if data.get("kind") != "thermometer_route_state_v1":
        raise ThermometerError("THERMOMETER_ROUTE_STATE_KIND", "route state kind is not supported")
    processed = data.get("processed_event_cids")
    routes = data.get("routes")
    if not isinstance(processed, list) or not isinstance(routes, Mapping):
        raise ThermometerError("THERMOMETER_ROUTE_STATE_SCHEMA", "route state is missing processed events or routes")
    return {
        "kind": "thermometer_route_state_v1",
        "processed_event_cids": sorted(str(item) for item in processed),
        "routes": dict(routes),
    }


def write_route_state(path: str | Path, state: Mapping[str, Primitive]) -> None:
    state_path = Path(path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = state_path.with_suffix(state_path.suffix + ".tmp")
    temp_path.write_bytes(canonical_bytes(state))
    temp_path.replace(state_path)


def read_events(path: str | Path) -> tuple[dict[str, Primitive], ...]:
    events_path = Path(path)
    if not events_path.exists():
        return ()
    events: list[dict[str, Primitive]] = []
    with events_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            decoded = json.loads(text)
            if not isinstance(decoded, Mapping):
                raise ThermometerError("THERMOMETER_EVENT_SCHEMA", f"event line {line_number} is not a map")
            events.append(dict(decoded))
    return tuple(events)


def translate_event(
    event: Mapping[str, Any],
    *,
    route_count_before: int,
) -> dict[str, Primitive]:
    """Translate one event into a semantic temperature atom."""

    event_cid = str(event.get("event_cid", cid_for(event)))
    signature = route_signature(event)
    route_key = cid_for(signature)
    evidence_class = str(signature["evidence_class"])
    band = str(signature["size_band"])
    route_depth = min(12, route_count_before + 1)
    pressure = min(
        1_000_000,
        EVIDENCE_BASE_PRESSURE.get(evidence_class, EVIDENCE_BASE_PRESSURE["MEASURED"])
        + SIZE_BAND_PRESSURE[band]
        + min(250_000, route_count_before * 25_000),
    )
    material = {
        "kind": "field_thermometer_atom_v1",
        "source_event_cid": event_cid,
        "route_key": route_key,
        "route_signature": signature,
        "relation": "opte:reinforces_self_similar_route" if route_count_before else "opte:opens_temperature_route",
        "state": pressure_state(pressure),
        "temperature_ppm": pressure,
        "route_depth": route_depth,
        "propagation_scope": propagation_scope(pressure, route_depth),
        "translation": "event_carrier_to_semantic_temperature",
        "affordance": "route_self_similar_data",
        "settlement_surface": "ground",
    }
    return {**material, "atom_cid": cid_for(material)}


def grow_routes(
    events: tuple[Mapping[str, Any], ...],
    route_state: Mapping[str, Primitive],
) -> tuple[dict[str, Primitive], dict[str, Primitive]]:
    """Translate unseen events and return new atoms plus updated route tissue."""

    processed = set(str(item) for item in route_state.get("processed_event_cids", []))
    routes_raw = route_state.get("routes", {})
    if not isinstance(routes_raw, Mapping):
        raise ThermometerError("THERMOMETER_ROUTE_STATE_SCHEMA", "routes must be a map")
    routes: dict[str, dict[str, Primitive]] = {
        str(key): dict(value) for key, value in routes_raw.items() if isinstance(value, Mapping)
    }

    atoms: list[dict[str, Primitive]] = []
    for event in events:
        event_cid = str(event.get("event_cid", cid_for(event)))
        if event_cid in processed:
            continue
        signature = route_signature(event)
        route_key = cid_for(signature)
        current = routes.get(
            route_key,
            {
                "kind": "thermometer_route_v1",
                "route_key": route_key,
                "signature": signature,
                "count": 0,
                "last_atom_cid": None,
            },
        )
        count_before = int(current.get("count", 0))
        atom = translate_event(event, route_count_before=count_before)
        atoms.append(atom)
        routes[route_key] = {
            "kind": "thermometer_route_v1",
            "route_key": route_key,
            "signature": signature,
            "count": count_before + 1,
            "last_atom_cid": atom["atom_cid"],
        }
        processed.add(event_cid)

    new_state = {
        "kind": "thermometer_route_state_v1",
        "processed_event_cids": sorted(processed),
        "routes": {key: routes[key] for key in sorted(routes)},
    }
    return tuple(atoms), new_state


def append_atoms(path: str | Path, atoms: tuple[Mapping[str, Primitive], ...]) -> None:
    atoms_path = Path(path)
    atoms_path.parent.mkdir(parents=True, exist_ok=True)
    with atoms_path.open("a", encoding="utf-8", newline="\n") as handle:
        for atom in atoms:
            handle.write(canonical_bytes(atom).decode("utf-8"))
            handle.write("\n")


def run_once(paths: ThermometerPaths) -> dict[str, Primitive]:
    """Translate all unseen events from the ledger and persist route growth."""

    events = read_events(paths.events_file)
    route_state = load_route_state(paths.routes_file)
    atoms, new_state = grow_routes(events, route_state)
    append_atoms(paths.atoms_file, atoms)
    write_route_state(paths.routes_file, new_state)
    receipt = {
        "kind": "field_thermometer_receipt_v1",
        "events_seen": len(events),
        "atoms_emitted": len(atoms),
        "route_count": len(new_state["routes"]),
        "atoms": [atom["atom_cid"] for atom in atoms],
        "route_state_cid": cid_for(new_state),
        "atoms_file": paths.atoms_file.as_posix(),
        "routes_file": paths.routes_file.as_posix(),
    }
    return {**receipt, "receipt_cid": cid_for(receipt)}


def watch(paths: ThermometerPaths, *, poll_interval_ms: int = 1000, max_cycles: int | None = None) -> None:
    """Run the thermometer as a bounded or continuous watch loop."""

    if poll_interval_ms < 0:
        raise ThermometerError("THERMOMETER_POLL_REJECTED", "poll_interval_ms must be non-negative")
    cycle = 0
    while max_cycles is None or cycle < max_cycles:
        cycle += 1
        receipt = run_once(paths)
        if receipt["atoms_emitted"]:
            print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
        if max_cycles is None or cycle < max_cycles:
            time.sleep(poll_interval_ms / 1000)


def _main() -> int:
    parser = argparse.ArgumentParser(description="Run the Sophia field thermometer")
    parser.add_argument("--base-dir", default=None)
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--poll-interval-ms", type=int, default=1000)
    parser.add_argument("--max-cycles", type=int, default=None)
    args = parser.parse_args()

    paths = ThermometerPaths.from_base(args.base_dir)
    if args.watch:
        watch(paths, poll_interval_ms=args.poll_interval_ms, max_cycles=args.max_cycles)
    else:
        print(json.dumps(run_once(paths), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
