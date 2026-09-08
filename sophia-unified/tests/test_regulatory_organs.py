from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "consciousness-core" / "regulatory_organs.py"
SPEC = importlib.util.spec_from_file_location("regulatory_organs", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
regulatory_organs = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = regulatory_organs
SPEC.loader.exec_module(regulatory_organs)


def test_garden_pulse_is_deterministic() -> None:
    signals = {
        "power_pressure_ppm": 720_000,
        "thermal_pressure_ppm": 650_000,
        "memory_pressure_ppm": 810_000,
        "network_pressure_ppm": 900_000,
        "filesystem_pressure_ppm": 400_000,
        "process_pressure_ppm": 500_000,
        "attention_pressure_ppm": 350_000,
    }

    first = regulatory_organs.pulse_garden(signals)
    second = regulatory_organs.pulse_garden(dict(reversed(list(signals.items()))))

    assert first.to_primitive() == second.to_primitive()
    assert first.cid == second.cid
    assert len(first.atom_cids) == 7
    assert {item["altitude"] for item in first.transformations} == {"air"}
    assert first.settlement_surface == "ground"


def test_garden_rejects_float_pressure() -> None:
    with pytest.raises(regulatory_organs.OrganError) as exc:
        regulatory_organs.pulse_garden({"power_pressure_ppm": 0.5})

    assert exc.value.code == "ORGAN_PRESSURE_REJECTED"


def test_centre_div_carries_receipt_and_root() -> None:
    receipt = regulatory_organs.pulse_garden({"network_pressure_ppm": 900_000})
    html = regulatory_organs.centre_div_projection(receipt)

    assert 'data-sophia-organ="centre"' in html
    assert 'data-settlement-surface="ground"' in html
    assert receipt.cid in html
    assert receipt.root_cid in html
