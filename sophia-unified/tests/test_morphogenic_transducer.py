from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


CORE_DIR = Path(__file__).resolve().parents[1] / "consciousness-core"
sys.path.insert(0, str(CORE_DIR))
SPEC = importlib.util.spec_from_file_location("morphogenic_transducer", CORE_DIR / "morphogenic_transducer.py")
assert SPEC is not None
assert SPEC.loader is not None
morph = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = morph
SPEC.loader.exec_module(morph)


def test_proto_metric_charge_is_preserved_not_rejected() -> None:
    transform = morph.transduce_charge(
        morph.Charge(
            name="body_device_tandem_unknown",
            realm="liminal",
            relation="opte:seeks_shape",
            magnitude_ppm=None,
            tags=("gesture", "sensor"),
            aliases=("chargor", "transform", "transistor"),
        )
    )

    assert transform["charge"]["metric_state"] == "proto_metric"
    assert transform["charge"]["interpretation_policy"]["terminology"] == "open"
    assert transform["charge"]["interpretation_policy"]["allows_reinterpretation"] is True
    assert transform["charge"]["aliases"] == ["chargor", "transform", "transistor"]
    assert transform["transistor"]["gate_state"] == "deictic_open"
    assert transform["transistor"]["rejects_ambiguity"] is False
    assert transform["transform"]["operation"] == "preserve_proto_metric"
    assert transform["transform"]["rigidity"] == "fluid"


def test_specified_charge_can_self_constrain_without_rejection() -> None:
    environment = morph.MorphogenicEnvironment(capacity_ppm=500_000, noise_ppm=150_000)
    transform = morph.transduce_charge(
        morph.Charge("network_pressure", "electromagnetic", "opte:requests_regulation", 900_000),
        environment,
    )

    assert transform["transistor"]["gate_state"] == "self_constraining"
    assert transform["transform"]["operation"] == "compost_excess_then_route"
    assert transform["transistor"]["retractable_projection"] is True


def test_terminology_remains_open_in_transform_receipt() -> None:
    receipt = morph.transduce_many(
        [
            morph.Charge(
                "term_that_is_not_done_becoming",
                "semantic",
                "opte:seeks_interpretation",
                None,
                aliases=("elephants_toes", "chargor"),
            )
        ]
    )

    transform = receipt["transforms"][0]
    assert transform["interpretation_policy"]["definition_state"] == "provisional"
    assert transform["interpretation_policy"]["collapse_requires"] == "explicit_local_use_or_material_mark"


def test_transducer_receipt_is_deterministic_and_ordered() -> None:
    charges = [
        morph.Charge("zeta", "semantic", "opte:relates", 100_000),
        morph.Charge("alpha", "semantic", "opte:relates", None),
    ]

    first = morph.transduce_many(charges)
    second = morph.transduce_many(reversed(charges))

    assert first == second
    assert [item["charge"]["name"] for item in first["transforms"]] == ["alpha", "zeta"]
    assert first["boundary_law"] == "form_constrains_itself_inside_environment"


def test_invalid_float_is_rejected_by_canonical_cid() -> None:
    try:
        morph.cid_for({"bad": 1.25})
    except Exception as exc:
        assert "FLOAT_REJECTED" in str(exc)
    else:
        raise AssertionError("float should have been rejected")
