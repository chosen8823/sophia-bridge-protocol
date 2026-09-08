from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


CORE_DIR = Path(__file__).resolve().parents[1] / "consciousness-core"
sys.path.insert(0, str(CORE_DIR))
SPEC = importlib.util.spec_from_file_location("file_hydrator", CORE_DIR / "file_hydrator.py")
assert SPEC is not None
assert SPEC.loader is not None
file_hydrator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = file_hydrator
SPEC.loader.exec_module(file_hydrator)


def test_file_hydration_is_deterministic_and_ordered() -> None:
    files = [
        file_hydrator.FileSignal("zeta/field.md", ".md", 5_000, 100, tags=("field",)),
        file_hydrator.FileSignal("alpha/organs.py", ".py", 8_000, 200, tags=("code",)),
    ]

    first = file_hydrator.hydrate_files(files)
    second = file_hydrator.hydrate_files(reversed(files))

    assert first == second
    assert first["settlement_surface"] == "ground"
    assert first["altitude"] == "air"
    assert [atom["path_hint"] for atom in first["atoms"]] == ["alpha/organs.py", "zeta/field.md"]


def test_unknown_file_becomes_self_adapting_residual() -> None:
    atom = file_hydrator.hydrate_file(
        file_hydrator.FileSignal("mystery/seed.carrier", ".carrier", 144, tags=("seed",))
    )

    assert atom["relation"] == "opte:seeks_aperture"
    assert atom["state"] == "airborne_residual"
    assert atom["compatibility"]["fallback"] == "hold_as_residual"
    assert "aperture_match" in atom["compatibility"]["requires"]


def test_from_path_uses_metadata_without_file_content(tmp_path: Path) -> None:
    sample = tmp_path / "secret.txt"
    sample.write_text("this text should not appear in the atom", encoding="utf-8")

    signal = file_hydrator.from_path(sample, root=tmp_path)
    atom = file_hydrator.hydrate_file(signal)

    assert signal.path_hint == "secret.txt"
    assert atom["suffix"] == ".txt"
    assert "this text should not appear" not in str(atom)
