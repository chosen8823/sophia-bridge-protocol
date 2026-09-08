"""Webhook-to-semantic-atom transformer.

The webhook transformer is a computator membrane: it receives ordinary JSON
events from tools such as Prometheus, local scripts, browser hooks, or sensor
kits; derives a small pressure field; and passes that field through the
regulatory organs so OPTE-shaped receipts can carry the event forward.

The module is pure.  It does not open sockets, call web APIs, inspect the file
system, or execute prompts.  The API gateway is responsible for transport.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from regulatory_organs import Primitive, canonical_bytes, cid_for, pulse_garden


DIRECT_SIGNAL_KEYS = frozenset(
    {
        "power_pressure_ppm",
        "thermal_pressure_ppm",
        "memory_pressure_ppm",
        "network_pressure_ppm",
        "filesystem_pressure_ppm",
        "process_pressure_ppm",
        "attention_pressure_ppm",
    }
)

KEYWORD_SIGNALS: tuple[tuple[str, str], ...] = (
    ("battery", "power_pressure_ppm"),
    ("charger", "power_pressure_ppm"),
    ("acpi", "power_pressure_ppm"),
    ("thermal", "thermal_pressure_ppm"),
    ("temperature", "thermal_pressure_ppm"),
    ("heat", "thermal_pressure_ppm"),
    ("memory", "memory_pressure_ppm"),
    ("ram", "memory_pressure_ppm"),
    ("network", "network_pressure_ppm"),
    ("wifi", "network_pressure_ppm"),
    ("packet", "network_pressure_ppm"),
    ("webhook", "network_pressure_ppm"),
    ("filesystem", "filesystem_pressure_ppm"),
    ("file", "filesystem_pressure_ppm"),
    ("onedrive", "filesystem_pressure_ppm"),
    ("process", "process_pressure_ppm"),
    ("worker", "process_pressure_ppm"),
    ("index", "process_pressure_ppm"),
    ("prompt", "attention_pressure_ppm"),
    ("code", "attention_pressure_ppm"),
    ("sensor", "attention_pressure_ppm"),
    ("error", "attention_pressure_ppm"),
)


@dataclass(frozen=True)
class WebhookAtomInput:
    """A transport-neutral webhook observation."""

    source: str
    event_type: str
    payload: Mapping[str, Any]
    signals: Mapping[str, Any] | None = None

    def to_primitive(self) -> dict[str, Primitive]:
        return {
            "kind": "webhook_atom_input_v1",
            "source": self.source,
            "event_type": self.event_type,
            "payload": _as_primitive_mapping(self.payload),
            "signals": _as_primitive_mapping(self.signals or {}),
        }

    @property
    def cid(self) -> str:
        return cid_for(self.to_primitive())


def _as_primitive_mapping(value: Mapping[str, Any]) -> dict[str, Primitive]:
    # `cid_for` performs the full canonical validation.  This round-trip keeps
    # the helper small while rejecting floats, bytes, non-string keys, and
    # arbitrary objects through the shared organ canonicaliser.
    import json

    raw = canonical_bytes(dict(value))
    decoded = json.loads(raw.decode("utf-8"))
    if not isinstance(decoded, dict):
        raise TypeError("canonical mapping did not decode to a dict")
    return decoded


def _keyword_text(value: Any) -> str:
    if isinstance(value, Mapping):
        return " ".join([str(key) + " " + _keyword_text(item) for key, item in value.items()])
    if isinstance(value, list | tuple):
        return " ".join(_keyword_text(item) for item in value)
    return str(value)


def derive_pressure_signals(event: WebhookAtomInput) -> dict[str, int]:
    """Derive deterministic organ pressure from one webhook observation."""

    payload_primitive = event.to_primitive()["payload"]
    payload_size = len(canonical_bytes(payload_primitive))
    text = f"{event.source} {event.event_type} {_keyword_text(payload_primitive)}".lower()
    signals = {
        "power_pressure_ppm": 0,
        "thermal_pressure_ppm": 0,
        "memory_pressure_ppm": min(1_000_000, payload_size * 64),
        "network_pressure_ppm": min(1_000_000, payload_size * 48),
        "filesystem_pressure_ppm": 0,
        "process_pressure_ppm": 0,
        "attention_pressure_ppm": min(1_000_000, payload_size * 32),
    }

    for keyword, signal in KEYWORD_SIGNALS:
        hits = text.count(keyword)
        if hits:
            signals[signal] = min(1_000_000, signals[signal] + hits * 120_000)

    for key, value in (event.signals or {}).items():
        if key in DIRECT_SIGNAL_KEYS:
            if not isinstance(value, int):
                raise TypeError(f"{key} must be an integer ppm value")
            signals[key] = max(0, min(1_000_000, value))

    return signals


def transform_webhook(event: WebhookAtomInput) -> dict[str, Primitive]:
    """Transform a webhook observation into a semantic atom receipt."""

    signals = derive_pressure_signals(event)
    organ_receipt = pulse_garden(signals)
    projection = {
        "kind": "webhook_atom_transform_v1",
        "input_cid": event.cid,
        "payload_cid": cid_for(event.to_primitive()["payload"]),
        "source": event.source,
        "event_type": event.event_type,
        "signals": signals,
        "organ_receipt": organ_receipt.to_primitive(),
        "organ_receipt_cid": organ_receipt.cid,
        "altitude": "air",
        "settlement_surface": "ground",
    }
    return {
        **projection,
        "transform_cid": cid_for(projection),
    }
