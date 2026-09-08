from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


CORE_DIR = Path(__file__).resolve().parents[1] / "consciousness-core"
sys.path.insert(0, str(CORE_DIR))
SPEC = importlib.util.spec_from_file_location("field_thermometer", CORE_DIR / "field_thermometer.py")
assert SPEC is not None
assert SPEC.loader is not None
field_thermometer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = field_thermometer
SPEC.loader.exec_module(field_thermometer)


def event(filename: str, size: int, evidence_class: str = "SEMANTIC", event_type: str = "OBSERVATION_INGESTED"):
    material = {
        "kind": "sophia_filesystem_event_v1",
        "event_type": event_type,
        "evidence_class": evidence_class,
        "observation": {
            "raw_filename": filename,
            "file_size_bytes": size,
        },
    }
    return {**material, "event_cid": field_thermometer.cid_for(material)}


def write_events(path: Path, events) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item in events:
            handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
            handle.write("\n")


def test_field_thermometer_grows_self_similar_routes(tmp_path: Path) -> None:
    paths = field_thermometer.ThermometerPaths.from_base(tmp_path)
    write_events(
        paths.events_file,
        [
            event("first.md", 100),
            event("second.md", 120),
        ],
    )

    receipt = field_thermometer.run_once(paths)
    atoms = [
        json.loads(line)
        for line in paths.atoms_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    route_state = json.loads(paths.routes_file.read_text(encoding="utf-8"))

    assert receipt["atoms_emitted"] == 2
    assert receipt["route_count"] == 1
    assert atoms[0]["relation"] == "opte:opens_temperature_route"
    assert atoms[1]["relation"] == "opte:reinforces_self_similar_route"
    assert atoms[1]["route_depth"] == 2
    assert next(iter(route_state["routes"].values()))["count"] == 2


def test_field_thermometer_does_not_double_grow_processed_events(tmp_path: Path) -> None:
    paths = field_thermometer.ThermometerPaths.from_base(tmp_path)
    write_events(paths.events_file, [event("flibberdy.txt", 12)])

    first = field_thermometer.run_once(paths)
    second = field_thermometer.run_once(paths)

    assert first["atoms_emitted"] == 1
    assert second["atoms_emitted"] == 0
    assert len(paths.atoms_file.read_text(encoding="utf-8").splitlines()) == 1


def test_field_thermometer_is_replayable_for_same_ledger(tmp_path: Path) -> None:
    receipts = []
    states = []
    for root in (tmp_path / "a", tmp_path / "b"):
        paths = field_thermometer.ThermometerPaths.from_base(root)
        write_events(paths.events_file, [event("garden.py", 8_000), event("river.wav", 8_000, "MEASURED")])
        receipts.append(field_thermometer.run_once(paths))
        states.append(paths.routes_file.read_text(encoding="utf-8"))

    assert receipts[0]["route_state_cid"] == receipts[1]["route_state_cid"]
    assert states[0] == states[1]


def test_field_thermometer_rejects_noncanonical_float() -> None:
    try:
        field_thermometer.cid_for({"bad": 1.5})
    except Exception as exc:
        assert "FLOAT_REJECTED" in str(exc)
    else:
        raise AssertionError("float should have been rejected")
