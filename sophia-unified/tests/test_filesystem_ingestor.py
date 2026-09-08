from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRIDGE_DIR = ROOT / "bridge"
SPEC = importlib.util.spec_from_file_location("ingestor", BRIDGE_DIR / "ingestor.py")
assert SPEC is not None
assert SPEC.loader is not None
ingestor = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ingestor
SPEC.loader.exec_module(ingestor)


def topology_for(path: Path):
    return ingestor.IngestTopology.from_base(path)


def read_events(path: Path) -> list[dict[str, object]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def test_process_carrier_writes_canonical_event_without_payload_leak(tmp_path: Path) -> None:
    topology = topology_for(tmp_path)
    ingestor.initialise_filesystem(topology)
    carrier = topology.inbox_dir / "secret.txt"
    carrier.write_text("this payload stays out of the event", encoding="utf-8")

    event = ingestor.process_carrier(carrier, topology=topology, archive=False)
    events = read_events(topology.events_file)

    expected_hash = hashlib.sha256("this payload stays out of the event".encode("utf-8")).hexdigest()
    assert len(events) == 1
    assert events[0] == event
    assert event["kind"] == "sophia_filesystem_event_v1"
    assert event["event_cid"].startswith("sha256:")
    assert event["observation"]["raw_payload_sha256"] == expected_hash
    assert event["observation"]["raw_payload_cid"] == f"sha256:{expected_hash}"
    assert "this payload stays out" not in topology.events_file.read_text(encoding="utf-8")


def test_ingestion_is_replayable_for_same_carrier_and_epoch(tmp_path: Path) -> None:
    roots = [tmp_path / "a", tmp_path / "b"]
    lines: list[str] = []
    cids: list[str] = []
    for root in roots:
        topology = topology_for(root)
        ingestor.initialise_filesystem(topology)
        carrier = topology.inbox_dir / "flibberdy.txt"
        carrier.write_bytes(b"flibberdy\n")
        event = ingestor.process_carrier(carrier, topology=topology, archive=False)
        cids.append(str(event["event_cid"]))
        lines.append(topology.events_file.read_text(encoding="utf-8"))

    assert cids[0] == cids[1]
    assert lines[0] == lines[1]


def test_sidecar_can_mark_symbolic_and_archive_inside_base(tmp_path: Path) -> None:
    topology = topology_for(tmp_path)
    ingestor.initialise_filesystem(topology)
    carrier = topology.inbox_dir / "sigil.carrier"
    carrier.write_bytes(b"\x00\x01\x02")
    sidecar = topology.inbox_dir / "sigil.carrier.meta.json"
    sidecar.write_text('{"evidence_class":"SYMBOLIC"}', encoding="utf-8")

    event = ingestor.process_carrier(carrier, topology=topology, archive=True)

    assert event["evidence_class"] == "SYMBOLIC"
    assert event["carrier_disposition"] == "archive_requested"
    assert not carrier.exists()
    assert not sidecar.exists()
    assert len(list(topology.archive_dir.iterdir())) == 2


def test_ingest_once_ignores_temp_hidden_and_sidecar_files(tmp_path: Path) -> None:
    topology = topology_for(tmp_path)
    ingestor.initialise_filesystem(topology)
    (topology.inbox_dir / ".hidden.txt").write_text("hidden", encoding="utf-8")
    (topology.inbox_dir / "partial.tmp").write_text("temp", encoding="utf-8")
    (topology.inbox_dir / "lonely.meta.json").write_text("{}", encoding="utf-8")
    (topology.inbox_dir / "real.json").write_text("{}", encoding="utf-8")

    events = ingestor.ingest_once(topology=topology, archive=False, stable_checks=1, stable_interval_ms=0)

    assert len(events) == 1
    assert events[0]["observation"]["raw_filename"] == "real.json"
