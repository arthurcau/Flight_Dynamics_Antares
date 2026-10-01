"""Model-history claims must stay separate from runnable model inputs."""

from pathlib import Path

import pytest

from antares_fd.validation.models import load_model_variants, parse_model_variants


MANIFEST = Path(__file__).resolve().parents[2] / "projects/neblina_1/reconstruction/model_variants.yaml"


def test_neblina_manifest_does_not_claim_unrecovered_models_are_runnable():
    variants = load_model_variants(MANIFEST)

    assert variants["NEBLINA1_PREFLIGHT_RECONSTRUCTION"].status == "PARTIALLY_RECONSTRUCTED_PREFLIGHT_MODEL"
    assert variants["NEBLINA1_AS_FLOWN"].status == "BLOCKED_BY_MISSING_METADATA"
    assert variants["NEBLINA1_POSTFLIGHT_RECONSTRUCTION"].status == "NOT_YET_VALIDATED"
    assert all(not variants[name].runnable for name in (
        "NEBLINA1_PREFLIGHT_RECONSTRUCTION", "NEBLINA1_AS_FLOWN", "NEBLINA1_POSTFLIGHT_RECONSTRUCTION"
    ))
    assert variants["NEBLINA1_CURRENT_MODEL_REFERENCE"].runnable
    assert variants["NEBLINA1_CURRENT_MODEL_REFERENCE"].role == "CURRENT_REFERENCE"


def test_preflight_rejects_postflight_identification():
    data = {
        "schema_version": 1,
        "project": "test",
        "variants": [{
            "id": "PREFLIGHT", "role": "PREFLIGHT", "status": "COMPLETE",
            "runnable": True, "configuration": "project_current_yaml",
            "evidence": [{"claim": "historical input", "origin": "POSTFLIGHT_IDENTIFIED", "source": "test"}],
            "missing_evidence": [], "identified_changes": [],
        }],
    }
    with pytest.raises(ValueError, match="POSTFLIGHT_IDENTIFIED"):
        parse_model_variants(data)


def test_postflight_change_requires_uncertainty_and_fit_effect():
    data = {
        "schema_version": 1,
        "project": "test",
        "variants": [{
            "id": "POSTFLIGHT", "role": "POSTFLIGHT", "status": "NOT_YET_VALIDATED",
            "runnable": False, "configuration": None,
            "evidence": [], "missing_evidence": ["calibration evidence"],
            "identified_changes": [{"parameter": "drag", "previous_value": 0.5, "new_value": 0.4}],
        }],
    }
    with pytest.raises(ValueError, match="identified_changes"):
        parse_model_variants(data)


def test_duplicate_variant_ids_are_rejected():
    item = {
        "id": "PREFLIGHT", "role": "PREFLIGHT", "status": "PARTIALLY_RECONSTRUCTED_PREFLIGHT_MODEL",
        "runnable": False, "configuration": None,
        "evidence": [], "missing_evidence": ["historical config"], "identified_changes": [],
    }
    with pytest.raises(ValueError, match="Duplicate"):
        parse_model_variants({"schema_version": 1, "project": "test", "variants": [item, item]})


def test_complete_model_requires_runnable_configuration():
    item = {
        "id": "PREFLIGHT", "role": "PREFLIGHT", "status": "COMPLETE",
        "runnable": False, "configuration": None,
        "evidence": [], "missing_evidence": [], "identified_changes": [],
    }
    with pytest.raises(ValueError, match="COMPLETE"):
        parse_model_variants({"schema_version": 1, "project": "test", "variants": [item]})
