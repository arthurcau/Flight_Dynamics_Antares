import importlib.util
from pathlib import Path

import pandas as pd
import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py"
)
SPEC = importlib.util.spec_from_file_location("neblina_flight_comparison", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
_peak_aligned_residuals = MODULE._peak_aligned_residuals
_model_snapshot_comparison = MODULE._model_snapshot_comparison
_verify_reference_artifacts = MODULE._verify_reference_artifacts


def test_peak_aligned_residuals_interpolates_model_and_does_not_extrapolate():
    observed = pd.DataFrame({
        "record_index": [10, 11, 12, 13, 14],
        "source_line_number": [100, 101, 102, 103, 104],
        "block_elapsed_s": [0.0, 1.0, 1.5, 2.0, 4.0],
        "bmp1_rel_alt_m": [0.0, 10.0, 7.0, -1.0, -5.0],
        "bmp2_rel_alt_m": [0.0, 10.0, 7.0, -1.0, -5.0],
    })
    simulated = pd.DataFrame({
        "time_s": [0.0, 1.0, 2.0],
        "altitude_agl_m": [0.0, 10.0, 0.0],
    })

    residuals, summary = _peak_aligned_residuals(
        observed,
        simulated,
        {"apogee_time": 1.0, "apogee_agl": 10.0},
    )

    interpolated = residuals.loc[
        residuals["record_index"].eq(12) & residuals["channel"].eq("bmp2_rel_alt_m")
    ].iloc[0]
    outside = residuals.loc[
        residuals["record_index"].eq(14) & residuals["channel"].eq("bmp2_rel_alt_m")
    ].iloc[0]
    assert interpolated["modeled_peak_relative_altitude_m"] == -5.0
    assert interpolated["observed_minus_modeled_m"] == 2.0
    assert outside["comparison_status"] == "OUTSIDE_MODEL_TIME_DOMAIN"
    assert pd.isna(outside["modeled_peak_relative_altitude_m"])
    assert summary["bmp2_rel_alt_m"]["outside_model_time_domain_count"] == 1
    post_peak = summary["bmp2_rel_alt_m"]["conditional_peak_aligned_residuals"]["post_peak"]
    assert post_peak["maximum_positive_residual_m"] == 2.0
    assert post_peak["first_negative_after_last_positive_time_s"] == 1.0


def test_model_snapshot_comparison_flags_different_dirty_worktrees():
    reference = {
        "git": {"working_tree_snapshot_sha256": "reference-snapshot"},
        "configuration_hashes": {"vehicle.yaml": "same-config"},
    }
    campaign = {
        "git": {"working_tree_snapshot_sha256": "campaign-snapshot"},
        "configuration_hashes": {"vehicle.yaml": "same-config"},
    }

    comparison = _model_snapshot_comparison(reference, campaign)

    assert comparison["status"] == "MODEL_SNAPSHOT_MISMATCH"
    assert comparison["configuration_hashes_match"] is True


def test_reference_artifact_verification_covers_metrics_and_rejects_mutation(tmp_path):
    artifact = tmp_path / "flight_metrics.json"
    artifact.write_text('{"apogee_agl": 1000}\n', encoding="utf-8")
    manifest = {"output_hashes": {"flight_metrics.json": MODULE.sha256_file(artifact)}}

    assert _verify_reference_artifacts(
        tmp_path, manifest, ("flight_metrics.json",),
    )["flight_metrics.json"] == manifest["output_hashes"]["flight_metrics.json"]

    artifact.write_text('{"apogee_agl": 1001}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="checksum mismatch: flight_metrics.json"):
        _verify_reference_artifacts(tmp_path, manifest, ("flight_metrics.json",))
