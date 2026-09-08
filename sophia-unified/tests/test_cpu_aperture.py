from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


CORE_DIR = Path(__file__).resolve().parents[1] / "consciousness-core"
sys.path.insert(0, str(CORE_DIR))
SPEC = importlib.util.spec_from_file_location("cpu_aperture", CORE_DIR / "cpu_aperture.py")
assert SPEC is not None
assert SPEC.loader is not None
cpu = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = cpu
SPEC.loader.exec_module(cpu)


def sample_observation() -> cpu.CPUObservation:
    return cpu.CPUObservation(
        "DESKTOP-VFN5S46",
        12,
        {
            "attention_pressure_ppm": 740_000,
            "cpu_frequency_ppm": 920_000,
            "cpu_load_ppm": 620_000,
            "memory_pressure_ppm": 520_000,
            "power_pressure_ppm": 680_000,
            "thermal_pressure_ppm": 250_000,
        },
        provenance=("powercfg-report", "perf-counter-sample"),
    )


def test_cpu_aperture_fans_metrics_into_semantic_domains() -> None:
    receipt = cpu.cpu_aperture_receipt(sample_observation())

    assert receipt["kind"] == "cpu_aperture_receipt_v1"
    assert receipt["boundary_law"] == "cpu_is_an_aperture_not_an_overclock_command"
    assert receipt["hardware_mutation"] is False
    assert receipt["semantic_claims_introduced"] is False
    assert len(receipt["frame_observations"]) == len(cpu.DEFAULT_CPU_FRAMES)
    assert "sha256:" in receipt["receipt_cid"]
    assert "sha256:" in receipt["opte_receipt_cid"]

    states = {
        item["frame"]["name"]: item["pressure"]["state"]
        for item in receipt["frame_observations"]
    }
    assert states["clock-rhythm"] == "choked"
    assert states["thermal-skin"] == "laminar"


def test_home_base_teleport_links_fanout_back_to_centre() -> None:
    home = cpu.CPUHomeBase(name="mims_memo_home", anchor="centre_jewel")
    receipt = cpu.cpu_aperture_receipt(sample_observation(), home_base=home)

    teleport = receipt["home_base_teleport"]
    assert receipt["home_base_cid"] == home.cid
    assert teleport["home_base_cid"] == home.cid
    assert teleport["literal_transport"] is False
    assert teleport["network_route"] is False
    assert teleport["semantic_address_reconciliation"] is True
    assert any(link["relation"] == "opte:returns_to_home_base" for link in receipt["links"])

    html = cpu.glyph_link_projection(receipt)
    assert 'data-sophia-organ="cpu-aperture"' in html
    assert f'data-home-base="{home.cid}"' in html
    assert "home ⇄ sha256:" in html


def test_cpu_aperture_is_replayable_for_equivalent_metric_order() -> None:
    first = cpu.cpu_aperture_receipt(sample_observation())
    second = cpu.cpu_aperture_receipt(
        cpu.CPUObservation(
            "DESKTOP-VFN5S46",
            12,
            dict(reversed(list(sample_observation().metrics.items()))),
            provenance=tuple(reversed(sample_observation().provenance)),
        )
    )

    assert first == second
    assert first["receipt_cid"] == second["receipt_cid"]
    assert first["invariant"] == second["invariant"]


def test_cpu_aperture_rejects_float_metrics() -> None:
    try:
        cpu.CPUObservation("host", 1, {"cpu_load_ppm": 12.5}).to_primitive()
    except Exception as exc:
        assert "CPU_APERTURE_INT_REQUIRED" in str(exc)
    else:
        raise AssertionError("float metric should have been rejected")
