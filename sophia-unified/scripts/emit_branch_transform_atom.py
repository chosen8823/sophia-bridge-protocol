"""Emit a deterministic GitHub branch transform atom.

Each GitHub branch can be treated as a temporary engine chamber when a workflow
runner checks it out.  This script turns that branch/run context into a
content-addressed atom that can be uploaded as a workflow artifact or consumed
by a later central aggregator.

The atom is intentionally small: no clock, random source, filesystem crawl,
network request, or secret-bearing context is required.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


Primitive = None | bool | int | str | list["Primitive"] | dict[str, "Primitive"]


class BranchAtomError(ValueError):
    """Stable machine-readable error for invalid branch atom state."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _normalise(value: Any) -> Primitive:
    if value is None or isinstance(value, bool | int | str):
        return value
    if isinstance(value, float):
        raise BranchAtomError("BRANCH_ATOM_FLOAT_REJECTED", "floats are not canonical branch atom state")
    if isinstance(value, bytes):
        raise BranchAtomError("BRANCH_ATOM_BYTES_REJECTED", "bytes must be encoded before atom emission")
    if isinstance(value, tuple | list):
        return [_normalise(item) for item in value]
    if isinstance(value, Mapping):
        out: dict[str, Primitive] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise BranchAtomError("BRANCH_ATOM_KEY_REJECTED", "canonical maps require string keys")
            out[key] = _normalise(item)
        return out
    raise BranchAtomError("BRANCH_ATOM_VALUE_REJECTED", f"unsupported canonical value: {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        _normalise(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def cid_for(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _require_text(name: str, value: str) -> str:
    value = value.strip()
    if not value:
        raise BranchAtomError("BRANCH_ATOM_FIELD_REQUIRED", f"{name} must not be empty")
    return value


def _safe_ref_name(ref_name: str) -> str:
    return ref_name.replace("\\", "/").strip("/")


def build_branch_transform_atom(
    *,
    repository: str,
    ref: str,
    ref_name: str,
    sha: str,
    event_name: str,
    workflow: str,
    runner_os: str,
    test_conclusion: str,
) -> dict[str, Primitive]:
    """Build the branch-local atom emitted by one ephemeral runner engine."""

    material = {
        "kind": "github_branch_transform_atom_v1",
        "schema_version": "0.1.0",
        "repository": _require_text("repository", repository),
        "ref": _require_text("ref", ref),
        "ref_name": _safe_ref_name(_require_text("ref_name", ref_name)),
        "sha": _require_text("sha", sha),
        "event_name": _require_text("event_name", event_name),
        "workflow": _require_text("workflow", workflow),
        "runner_engine": {
            "kind": "github_hosted_ephemeral_vm",
            "os": _require_text("runner_os", runner_os),
            "persistence": "ephemeral_per_job",
        },
        "central_transform": {
            "target": "sophia_central_transform_atom",
            "relation": "opte:branch_engine_reports_to_central_atom",
            "mode": "artifact_receipt",
        },
        "test_conclusion": _require_text("test_conclusion", test_conclusion),
        "membrane_lifecycle": ["CHECKOUT", "TEST", "EMIT", "UPLOAD", "RETURN"],
    }
    return {
        **material,
        "branch_atom_cid": cid_for(
            {
                "repository": material["repository"],
                "ref": material["ref"],
                "ref_name": material["ref_name"],
                "sha": material["sha"],
            }
        ),
        "transform_atom_cid": cid_for(material),
    }


def write_atom(atom: Mapping[str, Primitive], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(atom))


def _main() -> int:
    parser = argparse.ArgumentParser(description="Emit a Sophia GitHub branch transform atom")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--ref-name", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--event-name", required=True)
    parser.add_argument("--workflow", required=True)
    parser.add_argument("--runner-os", required=True)
    parser.add_argument("--test-conclusion", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    atom = build_branch_transform_atom(
        repository=args.repo,
        ref=args.ref,
        ref_name=args.ref_name,
        sha=args.sha,
        event_name=args.event_name,
        workflow=args.workflow,
        runner_os=args.runner_os,
        test_conclusion=args.test_conclusion,
    )
    write_atom(atom, args.out)
    print(json.dumps(atom, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
