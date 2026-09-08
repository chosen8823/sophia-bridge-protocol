from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "emit_branch_transform_atom.py"
SPEC = importlib.util.spec_from_file_location("emit_branch_transform_atom", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
branch_atom = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = branch_atom
SPEC.loader.exec_module(branch_atom)


BASE = {
    "repository": "chosen8823/sophia-bridge-protocol",
    "ref": "refs/heads/codex/demo",
    "ref_name": "codex/demo",
    "sha": "abc123",
    "event_name": "push",
    "workflow": "Sophia Branch Transform Atom",
    "runner_os": "Linux",
    "test_conclusion": "success",
}


def test_branch_transform_atom_is_deterministic() -> None:
    first = branch_atom.build_branch_transform_atom(**BASE)
    second = branch_atom.build_branch_transform_atom(**dict(reversed(BASE.items())))

    assert first == second
    assert first["kind"] == "github_branch_transform_atom_v1"
    assert first["runner_engine"]["persistence"] == "ephemeral_per_job"
    assert first["central_transform"]["relation"] == "opte:branch_engine_reports_to_central_atom"


def test_branch_transform_atom_changes_when_sha_changes() -> None:
    first = branch_atom.build_branch_transform_atom(**BASE)
    changed = branch_atom.build_branch_transform_atom(**{**BASE, "sha": "def456"})

    assert first["branch_atom_cid"] != changed["branch_atom_cid"]
    assert first["transform_atom_cid"] != changed["transform_atom_cid"]


def test_branch_atom_rejects_noncanonical_float() -> None:
    try:
        branch_atom.cid_for({"bad": 1.25})
    except branch_atom.BranchAtomError as exc:
        assert exc.code == "BRANCH_ATOM_FLOAT_REJECTED"
    else:
        raise AssertionError("float should have been rejected")


def test_write_atom_uses_canonical_json(tmp_path: Path) -> None:
    atom = branch_atom.build_branch_transform_atom(**BASE)
    output = tmp_path / "atom.json"

    branch_atom.write_atom(atom, output)

    decoded = json.loads(output.read_text(encoding="utf-8"))
    assert decoded == atom
    assert "\n" not in output.read_text(encoding="utf-8")
