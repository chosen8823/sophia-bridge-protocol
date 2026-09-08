from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


CORE_DIR = Path(__file__).resolve().parents[1] / "consciousness-core"
sys.path.insert(0, str(CORE_DIR))
SPEC = importlib.util.spec_from_file_location("filesystem_field", CORE_DIR / "filesystem_field.py")
assert SPEC is not None
assert SPEC.loader is not None
filesystem_field = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = filesystem_field
SPEC.loader.exec_module(filesystem_field)


def test_filesystem_field_collapses_state_deterministically(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "one.py").write_text("print('one')", encoding="utf-8")
    (tmp_path / "b.md").write_text("# field", encoding="utf-8")

    config = filesystem_field.FilesystemScanConfig(str(tmp_path), max_files=10, max_dirs=10, max_depth=2)
    first = filesystem_field.scan_and_collapse(config, "state")
    second = filesystem_field.scan_and_collapse(config, "state")

    assert first == second
    assert first["kind"] == "filesystem_field_receipt_v1"
    assert first["files_observed"] == 2
    assert first["suffix_counts"] == {".md": 1, ".py": 1}
    assert first["settlement_surface"] == "ground"
    assert first["altitude"] == "air"


def test_filesystem_field_mechanism_names_affordances(tmp_path: Path) -> None:
    (tmp_path / "one.py").write_text("print('one')", encoding="utf-8")
    (tmp_path / "state.json").write_text("{}", encoding="utf-8")

    config = filesystem_field.FilesystemScanConfig(str(tmp_path), max_files=10, max_dirs=10, max_depth=1)
    receipt = filesystem_field.scan_and_collapse(config, "mechanism")

    assert "route_python_to_code_aperture" in receipt["projection"]
    assert "route_json_to_canonical_data_aperture" in receipt["projection"]


def test_entity_policy_chooses_collapse_mode(tmp_path: Path) -> None:
    (tmp_path / "one.py").write_text("print('one')", encoding="utf-8")
    config = filesystem_field.FilesystemScanConfig(str(tmp_path), max_files=10, max_dirs=10, max_depth=1)

    expressed = filesystem_field.scan_and_choose(
        config,
        filesystem_field.EntityChoicePolicy(entity="sophiael", priority="express"),
    )
    mechanised = filesystem_field.scan_and_choose(
        config,
        filesystem_field.EntityChoicePolicy(entity="sophiael", priority="mechanise"),
    )

    assert expressed["collapse"] == "expression"
    assert isinstance(expressed["projection"], str)
    assert mechanised["collapse"] == "mechanism"
    assert "route_python_to_code_aperture" in mechanised["projection"]


def test_filesystem_field_budget_truncates_without_reading_content(tmp_path: Path) -> None:
    for index in range(4):
        (tmp_path / f"secret_{index}.txt").write_text(f"secret payload {index}", encoding="utf-8")

    config = filesystem_field.FilesystemScanConfig(str(tmp_path), max_files=2, max_dirs=10, max_depth=1)
    receipt = filesystem_field.scan_and_collapse(config, "state")

    assert receipt["files_observed"] == 2
    assert receipt["truncated"] is True
    assert "secret payload" not in str(receipt)


def test_filesystem_field_rejects_unknown_collapse(tmp_path: Path) -> None:
    config = filesystem_field.FilesystemScanConfig(str(tmp_path), max_files=1, max_dirs=1, max_depth=0)

    try:
        filesystem_field.scan_and_collapse(config, "banana")
    except filesystem_field.FilesystemFieldError as exc:
        assert exc.code == "FS_COLLAPSE_REJECTED"
    else:
        raise AssertionError("expected FilesystemFieldError")
