"""Sophia filesystem ingestion membrane.

Implements the carrier lifecycle:

    CONTACT -> HOLD -> INTERPRET -> WRAP -> RETURN

The ingestor is deliberately boring at the kernel boundary.  It watches or
scans a local ``inbox`` directory, computes a raw SHA-256 carrier invariant,
classifies the carrier with deterministic rules, and appends a canonical JSONL
event to ``state/EVENTS.jsonl``.

No UUIDs, wall-clock timestamps, environment-derived identities, floating point
values, or hidden model calls are used in canonical event payloads.  Optional
archival only moves files inside the configured Sophia base directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


Primitive = None | bool | int | str | list["Primitive"] | dict[str, "Primitive"]

EVIDENCE_CLASSES = frozenset({"MEASURED", "SIMULATED", "SEMANTIC", "SYMBOLIC", "HYPOTHESIS"})
IGNORED_SUFFIXES = (".tmp", ".meta.json")


class IngestorError(ValueError):
    """Stable machine-readable error for invalid ingestion state."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _normalise(value: Any) -> Primitive:
    if value is None or isinstance(value, bool | int | str):
        return value
    if isinstance(value, float):
        raise IngestorError("INGEST_FLOAT_REJECTED", "floats are not canonical ingestion state")
    if isinstance(value, bytes):
        raise IngestorError("INGEST_BYTES_REJECTED", "bytes must be represented by a content hash")
    if isinstance(value, tuple | list):
        return [_normalise(item) for item in value]
    if isinstance(value, Mapping):
        out: dict[str, Primitive] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise IngestorError("INGEST_KEY_REJECTED", "canonical maps require string keys")
            out[key] = _normalise(item)
        return out
    raise IngestorError("INGEST_VALUE_REJECTED", f"unsupported canonical value: {type(value).__name__}")


def canonical_json_line(value: Any) -> str:
    """Return compact canonical JSON for one JSONL event."""

    return json.dumps(
        _normalise(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def cid_for(value: Any) -> str:
    """Return the OPTE/Sophia content identity for a primitive payload."""

    payload = canonical_json_line(value).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class IngestTopology:
    """Local filesystem topology for one Sophia ingestion chamber."""

    base_dir: Path
    inbox_dir: Path
    archive_dir: Path
    state_dir: Path
    events_file: Path

    @classmethod
    def from_base(cls, base_dir: str | Path | None = None) -> "IngestTopology":
        root = Path(base_dir) if base_dir is not None else Path(__file__).resolve().parent.parent
        root = root.resolve()
        return cls(
            base_dir=root,
            inbox_dir=root / "inbox",
            archive_dir=root / "archive",
            state_dir=root / "state",
            events_file=root / "state" / "EVENTS.jsonl",
        )


DEFAULT_TOPOLOGY = IngestTopology.from_base()


def initialise_filesystem(topology: IngestTopology = DEFAULT_TOPOLOGY) -> None:
    """Ensure the local ingestion scaffold exists."""

    for directory in (topology.inbox_dir, topology.archive_dir, topology.state_dir):
        directory.mkdir(parents=True, exist_ok=True)
    topology.events_file.touch(exist_ok=True)


def compute_sha256(filepath: str | Path) -> str:
    """Compute the deterministic SHA-256 hash of the raw file carrier."""

    file_path = Path(filepath)
    hasher = hashlib.sha256()
    with file_path.open("rb") as handle:
        while True:
            chunk = handle.read(65_536)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def should_ignore(filepath: str | Path) -> bool:
    """Return true for hidden/temp/metadata files that are not carrier events."""

    name = Path(filepath).name
    return name.startswith(".") or any(name.endswith(suffix) for suffix in IGNORED_SUFFIXES)


def _relative_hint(filepath: Path, root: Path) -> str:
    try:
        return filepath.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return filepath.name


def _read_sidecar(filepath: Path) -> dict[str, Primitive]:
    meta_path = filepath.with_suffix(filepath.suffix + ".meta.json")
    if not meta_path.exists():
        return {
            "kind": "sidecar_status_v1",
            "status": "absent",
            "evidence_class": None,
            "sidecar_cid": None,
        }
    try:
        with meta_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception:
        return {
            "kind": "sidecar_status_v1",
            "status": "invalid_json",
            "evidence_class": None,
            "sidecar_cid": None,
        }
    if not isinstance(data, Mapping):
        return {
            "kind": "sidecar_status_v1",
            "status": "invalid_schema",
            "evidence_class": None,
            "sidecar_cid": None,
        }
    declared = str(data.get("evidence_class", "")).upper()
    return {
        "kind": "sidecar_status_v1",
        "status": "accepted" if declared in EVIDENCE_CLASSES else "ignored",
        "evidence_class": declared if declared in EVIDENCE_CLASSES else None,
        "sidecar_cid": cid_for(data),
    }


def classify_carrier(filepath: str | Path) -> dict[str, Primitive]:
    """Classify a carrier without reading or storing its semantic payload."""

    file_path = Path(filepath)
    sidecar = _read_sidecar(file_path)
    if sidecar["evidence_class"] is not None:
        return {
            "kind": "carrier_classification_v1",
            "evidence_class": sidecar["evidence_class"],
            "source": "sidecar",
            "sidecar": sidecar,
        }

    suffix = file_path.suffix.lower()
    if suffix in {".bin", ".pcap", ".wav", ".raw", ".csv", ".log"}:
        evidence_class = "MEASURED"
    elif suffix in {".json", ".jsonl", ".yaml", ".yml", ".md", ".txt", ".py", ".js", ".ts"}:
        evidence_class = "SEMANTIC"
    elif suffix in {".svg", ".png", ".jpg", ".jpeg", ".gif", ".mp4", ".mov"}:
        evidence_class = "SYMBOLIC"
    else:
        evidence_class = "MEASURED"
    return {
        "kind": "carrier_classification_v1",
        "evidence_class": evidence_class,
        "source": "suffix",
        "sidecar": sidecar,
    }


def wait_for_stable_file(filepath: str | Path, checks: int = 3, interval_ms: int = 100) -> int:
    """Wait until file size is stable for a bounded number of checks."""

    if checks <= 0:
        raise IngestorError("INGEST_CHECKS_REJECTED", "checks must be positive")
    if interval_ms < 0:
        raise IngestorError("INGEST_INTERVAL_REJECTED", "interval_ms must be non-negative")
    file_path = Path(filepath)
    last_size = -1
    stable_count = 0
    while stable_count < checks:
        size = file_path.stat().st_size
        if size == last_size:
            stable_count += 1
        else:
            last_size = size
            stable_count = 1
        if stable_count < checks and interval_ms:
            time.sleep(interval_ms / 1000)
    return last_size


def next_epoch(events_file: str | Path) -> int:
    """Calculate the next deterministic local ledger epoch."""

    path = Path(events_file)
    if not path.exists():
        return 1
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip()) + 1


def wrap_carrier_event(
    filepath: str | Path,
    *,
    topology: IngestTopology = DEFAULT_TOPOLOGY,
    epoch: int | None = None,
    archive_requested: bool = False,
    stable_checks: int = 1,
    stable_interval_ms: int = 0,
) -> dict[str, Primitive]:
    """Build the canonical observation event for one carrier."""

    file_path = Path(filepath)
    if not file_path.is_file():
        raise IngestorError("INGEST_NOT_FILE", f"carrier is not a file: {file_path}")
    if should_ignore(file_path):
        raise IngestorError("INGEST_IGNORED", f"carrier is ignored by policy: {file_path.name}")
    if epoch is None:
        epoch = next_epoch(topology.events_file)
    if epoch <= 0:
        raise IngestorError("INGEST_EPOCH_REJECTED", "epoch must be positive")

    file_size = wait_for_stable_file(file_path, checks=stable_checks, interval_ms=stable_interval_ms)
    payload_hash = compute_sha256(file_path)
    classification = classify_carrier(file_path)
    observation = {
        "kind": "filesystem_observation_v1",
        "observation_cid_material": {
            "source_type": "FILESYSTEM_INGESTOR",
            "collector_node": "local_sophia_ingestor",
            "raw_filename": file_path.name,
            "path_hint": _relative_hint(file_path, topology.inbox_dir),
            "raw_payload_cid": "sha256:" + payload_hash,
            "raw_payload_sha256": payload_hash,
            "file_size_bytes": file_size,
            "evidence_class": classification["evidence_class"],
        },
    }
    observation_cid = cid_for(observation)
    event_material = {
        "kind": "sophia_filesystem_event_v1",
        "event_type": "OBSERVATION_INGESTED",
        "epoch": epoch,
        "membrane_lifecycle": ["CONTACT", "HOLD", "INTERPRET", "WRAP", "RETURN"],
        "membrane_stage": "RETURN",
        "evidence_class": classification["evidence_class"],
        "classification": classification,
        "observation_cid": observation_cid,
        "observation": observation["observation_cid_material"],
        "carrier_disposition": "archive_requested" if archive_requested else "observed_in_place",
    }
    return {**event_material, "event_cid": cid_for(event_material)}


def append_event(event: Mapping[str, Primitive], topology: IngestTopology = DEFAULT_TOPOLOGY) -> None:
    """Append one canonical event to the immutable JSONL ledger."""

    initialise_filesystem(topology)
    with topology.events_file.open("a", encoding="utf-8", newline="\n") as ledger:
        ledger.write(canonical_json_line(event))
        ledger.write("\n")


def _archive_destination(filepath: Path, event_cid: str, topology: IngestTopology) -> Path:
    payload_hash = compute_sha256(filepath)
    safe_event = event_cid.removeprefix("sha256:")[:12]
    return topology.archive_dir / f"{payload_hash[:12]}_{safe_event}_{filepath.name}"


def archive_carrier(filepath: str | Path, event_cid: str, topology: IngestTopology = DEFAULT_TOPOLOGY) -> Path:
    """Move a carrier and optional sidecar into the local archive chamber."""

    initialise_filesystem(topology)
    file_path = Path(filepath)
    destination = _archive_destination(file_path, event_cid, topology)
    if destination.exists():
        raise IngestorError("INGEST_ARCHIVE_COLLISION", f"archive destination already exists: {destination}")
    shutil.move(str(file_path), str(destination))

    meta_path = file_path.with_suffix(file_path.suffix + ".meta.json")
    if meta_path.exists():
        meta_destination = topology.archive_dir / f"{destination.stem}_{meta_path.name}"
        if meta_destination.exists():
            raise IngestorError("INGEST_META_ARCHIVE_COLLISION", f"metadata archive exists: {meta_destination}")
        shutil.move(str(meta_path), str(meta_destination))
    return destination


def process_carrier(
    filepath: str | Path,
    *,
    topology: IngestTopology = DEFAULT_TOPOLOGY,
    archive: bool = False,
    stable_checks: int = 1,
    stable_interval_ms: int = 0,
) -> dict[str, Primitive]:
    """Execute CONTACT/HOLD/INTERPRET/WRAP/RETURN for a single carrier."""

    initialise_filesystem(topology)
    event = wrap_carrier_event(
        filepath,
        topology=topology,
        archive_requested=archive,
        stable_checks=stable_checks,
        stable_interval_ms=stable_interval_ms,
    )
    append_event(event, topology)
    if archive:
        archive_carrier(filepath, str(event["event_cid"]), topology)
    return event


def ingest_once(
    *,
    topology: IngestTopology = DEFAULT_TOPOLOGY,
    archive: bool = False,
    stable_checks: int = 2,
    stable_interval_ms: int = 100,
) -> tuple[dict[str, Primitive], ...]:
    """Process the current inbox once, deterministically ordered by filename."""

    initialise_filesystem(topology)
    events: list[dict[str, Primitive]] = []
    for item in sorted(topology.inbox_dir.iterdir(), key=lambda path: path.name):
        if item.is_file() and not should_ignore(item):
            events.append(
                process_carrier(
                    item,
                    topology=topology,
                    archive=archive,
                    stable_checks=stable_checks,
                    stable_interval_ms=stable_interval_ms,
                )
            )
    return tuple(events)


def start_daemon(
    *,
    topology: IngestTopology = DEFAULT_TOPOLOGY,
    poll_interval_ms: int = 1000,
    max_cycles: int | None = None,
    archive: bool = False,
) -> None:
    """Run a bounded or continuous inbox watcher."""

    if poll_interval_ms < 0:
        raise IngestorError("INGEST_POLL_REJECTED", "poll_interval_ms must be non-negative")
    initialise_filesystem(topology)
    print("[DAEMON] Sophia Filesystem Ingestor active.")
    print(f"[DAEMON] Watching inbox: {topology.inbox_dir.resolve()}")
    print(f"[DAEMON] Appending events: {topology.events_file.resolve()}")

    cycle = 0
    while max_cycles is None or cycle < max_cycles:
        cycle += 1
        try:
            for event in ingest_once(topology=topology, archive=archive):
                print(
                    f"[INGESTED] {event['observation']['raw_filename']} -> "
                    f"{event['evidence_class']} ({event['event_cid']})"
                )
        except IngestorError as exc:
            print(f"[ERROR] {exc.code}: {exc.message}")
        if max_cycles is None or cycle < max_cycles:
            time.sleep(poll_interval_ms / 1000)


def _main() -> int:
    parser = argparse.ArgumentParser(description="Sophia filesystem ingestion daemon")
    parser.add_argument("--base-dir", default=None, help="Sophia base directory; defaults to sophia-unified")
    parser.add_argument("--once", action="store_true", help="process the inbox once and exit")
    parser.add_argument("--archive", action="store_true", help="move carriers into archive/ after ingestion")
    parser.add_argument("--poll-interval-ms", type=int, default=1000)
    args = parser.parse_args()

    topology = IngestTopology.from_base(args.base_dir)
    if args.once:
        for event in ingest_once(topology=topology, archive=args.archive):
            print(canonical_json_line(event))
    else:
        start_daemon(topology=topology, poll_interval_ms=args.poll_interval_ms, archive=args.archive)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
