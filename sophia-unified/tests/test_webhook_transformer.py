from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


CORE_DIR = Path(__file__).resolve().parents[1] / "consciousness-core"
sys.path.insert(0, str(CORE_DIR))
SPEC = importlib.util.spec_from_file_location("webhook_transformer", CORE_DIR / "webhook_transformer.py")
assert SPEC is not None
assert SPEC.loader is not None
webhook_transformer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = webhook_transformer
SPEC.loader.exec_module(webhook_transformer)


def test_webhook_transform_is_deterministic() -> None:
    event = webhook_transformer.WebhookAtomInput(
        source="prometheus",
        event_type="sensor-kit",
        payload={"prompt": "watch network packets", "sensor": "wifi", "count": 3},
    )

    first = webhook_transformer.transform_webhook(event)
    second = webhook_transformer.transform_webhook(event)

    assert first == second
    assert first["altitude"] == "air"
    assert first["settlement_surface"] == "ground"
    assert first["organ_receipt"]["kind"] == "opte_regulatory_receipt_v1"
    assert first["signals"]["network_pressure_ppm"] > 0


def test_webhook_direct_sensor_signals_override_derived_pressure() -> None:
    event = webhook_transformer.WebhookAtomInput(
        source="sensor-kit",
        event_type="pressure",
        payload={"note": "quiet"},
        signals={"network_pressure_ppm": 999_999},
    )

    transformed = webhook_transformer.transform_webhook(event)

    assert transformed["signals"]["network_pressure_ppm"] == 999_999


def test_webhook_rejects_float_payload() -> None:
    event = webhook_transformer.WebhookAtomInput(
        source="bad-sensor",
        event_type="float",
        payload={"pressure": 0.5},
    )

    with pytest.raises(Exception):
        webhook_transformer.transform_webhook(event)
