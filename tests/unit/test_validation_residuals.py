"""Time-resolved comparison uses explicit anchors and a single observed segment."""

import numpy as np
import pytest

from antares_fd.validation.residuals import Alignment, ComparisonBasis, compare_time_series


def _alignment():
    return Alignment(
        segment_id=2,
        observed_anchor_time_s=10.0,
        simulated_anchor_time_s=0.0,
        event="first_motion",
        evidence="two independent telemetry channels",
        uncertainty_s=0.1,
    )


def _basis():
    return ComparisonBasis(
        observed_unit="m", simulated_unit="m",
        observed_frame="AGL", simulated_frame="AGL",
        observed_unit_status="DOCUMENTED", evidence="surveyed common launch-pad datum",
    )


def test_residuals_interpolate_simulation_with_explicit_anchor():
    result = compare_time_series(
        observed_time_s=np.array([10.0, 10.5, 11.0]),
        observed_segment_id=np.array([2, 2, 2]),
        observed_values=np.array([0.0, 5.0, 10.0]),
        simulated_time_s=np.array([0.0, 1.0]),
        simulated_values=np.array([0.0, 12.0]),
        observed_record_index=[10, 11, 12],
        alignment=_alignment(),
        basis=_basis(),
        quantity="altitude_agl_m",
        observed_origin="DERIVED",
    )
    assert result["model_time_s"].tolist() == [0.0, 0.5, 1.0]
    assert result["record_index"].tolist() == [10, 11, 12]
    assert result["residual_simulated_minus_observed"].tolist() == [0.0, 1.0, 2.0]
    assert result.attrs["alignment_event"] == "first_motion"
    assert result.attrs["observed_origin"] == "DERIVED"


def test_residuals_reject_cross_segment_join():
    with pytest.raises(ValueError, match="single observed segment"):
        compare_time_series(
            [10, 11], [2, 3], [0, 1], [0, 1], [0, 1],
            observed_record_index=[10, 11],
            alignment=_alignment(), basis=_basis(), quantity="altitude_agl_m", observed_origin="DERIVED",
        )


def test_residuals_reject_extrapolation_and_invalid_origin():
    with pytest.raises(ValueError, match="extrapolation"):
        compare_time_series(
            [10, 12], [2, 2], [0, 1], [0, 1], [0, 1],
            observed_record_index=[10, 11],
            alignment=_alignment(), basis=_basis(), quantity="altitude_agl_m", observed_origin="DERIVED",
        )
    with pytest.raises(ValueError, match="observed_origin"):
        compare_time_series(
            [10, 11], [2, 2], [0, 1], [0, 1], [0, 1],
            observed_record_index=[10, 11],
            alignment=_alignment(), basis=_basis(), quantity="altitude_agl_m", observed_origin="MODELED",
        )


def test_residuals_preserve_missing_observations_as_nan():
    result = compare_time_series(
        [10, 11], [2, 2], [0, np.nan], [0, 1], [0, 2],
        observed_record_index=[10, 11],
        alignment=_alignment(), basis=_basis(), quantity="altitude_agl_m", observed_origin="DERIVED",
    )
    assert np.isnan(result["residual_simulated_minus_observed"].iloc[1])


def test_residuals_reject_duplicate_acquisition_ids():
    with pytest.raises(ValueError, match="observed_record_index"):
        compare_time_series(
            [10, 11], [2, 2], [0, 1], [0, 1], [0, 1],
            observed_record_index=[10, 10],
            alignment=_alignment(), basis=_basis(), quantity="altitude_agl_m", observed_origin="DERIVED",
        )


def test_residuals_reject_noninteger_segment_ids():
    with pytest.raises(ValueError, match="segment_id"):
        compare_time_series(
            [10, 11], [2.0, 2.0], [0, 1], [0, 1], [0, 1],
            observed_record_index=[10, 11],
            alignment=_alignment(), basis=_basis(), quantity="altitude_agl_m", observed_origin="DERIVED",
        )


def test_residuals_reject_unknown_vertical_reference():
    with pytest.raises(ValueError, match="frame"):
        ComparisonBasis(
            observed_unit="m", simulated_unit="m",
            observed_frame="UNKNOWN_VERTICAL_REFERENCE", simulated_frame="AGL",
            observed_unit_status="HEADER_LABEL", evidence="raw BMP column header only",
        )
