"""
Unit tests for AtmosphericScoring in MAGI.
"""

import pytest
import numpy as np
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scoring import AtmosphericScoring
from state_manager import MagiState
from casper import MagiSchema


def _make_dummy_stats(z_grid):
    nz = len(z_grid)
    df_stats = pd.DataFrame({
        "altitude_agl_m": z_grid,
        # Calm surface, stronger winds aloft
        "wind_speed_mps_median": np.linspace(3.0, 15.0, nz),
        "wind_speed_mps_p90": np.linspace(6.0, 25.0, nz),
        "wind_speed_mps_p99": np.linspace(10.0, 35.0, nz),
        "wind_shear_s_1_median": np.full(nz, 0.005),
        "wind_shear_s_1_p90": np.full(nz, 0.015),
        "wind_shear_s_1_p99": np.full(nz, 0.025),
    })
    return df_stats


def _make_dummy_member(z_grid, wind_speed_scale=1.0, shear_scale=1.0):
    nz = len(z_grid)
    df = MagiSchema.create_empty(nz)
    df["altitude_agl_m"] = z_grid
    df["wind_speed_mps"] = np.linspace(3.0, 15.0, nz) * wind_speed_scale
    df["wind_shear_s_1"] = np.full(nz, 0.005) * shear_scale
    df["quality_flag"] = "VALID"
    return df


def test_atmospheric_scoring_favourable():
    z_grid = np.arange(0, 3000, 100)
    df_stats = _make_dummy_stats(z_grid)
    members = [_make_dummy_member(z_grid, wind_speed_scale=0.9) for _ in range(5)]

    score, score_class = AtmosphericScoring.calculate_score(
        members, df_stats, z_grid,
        operational_state=MagiState.CURRENT_FORECAST,
        weather_score=8.0,
        data_quality_score=9.0
    )

    assert score is not None
    assert score >= 80.0
    assert score_class == "EXPLORATORY_ATMOSPHERIC_INDEX"


def test_atmospheric_scoring_surface_wind_penalty():
    z_grid = np.arange(0, 3000, 100)
    df_stats = _make_dummy_stats(z_grid)

    # Moderate calm profile
    members_calm = [_make_dummy_member(z_grid, wind_speed_scale=0.8) for _ in range(3)]
    score_calm, _ = AtmosphericScoring.calculate_score(
        members_calm, df_stats, z_grid,
        weather_score=5.0, data_quality_score=5.0
    )

    # Profile with high surface wind (15 m/s at surface where P99 is 10 m/s)
    members_severe_surface = []
    for _ in range(3):
        m = _make_dummy_member(z_grid, wind_speed_scale=0.8)
        # Spike surface wind
        m.loc[m["altitude_agl_m"] <= 200, "wind_speed_mps"] = 25.0
        members_severe_surface.append(m)

    score_severe, _ = AtmosphericScoring.calculate_score(
        members_severe_surface, df_stats, z_grid,
        weather_score=5.0, data_quality_score=5.0
    )

    assert score_calm is not None
    assert score_severe is not None
    # Surface wind spike must significantly depress score due to altitude weighting
    assert score_calm - score_severe > 10.0


def test_atmospheric_scoring_unavailable_conditions():
    z_grid = np.arange(0, 3000, 100)
    df_stats = _make_dummy_stats(z_grid)
    members = [_make_dummy_member(z_grid) for _ in range(3)]

    # Empty ensemble
    assert AtmosphericScoring.calculate_score([], df_stats, z_grid)[0] is None

    # Disallowed operational state
    assert AtmosphericScoring.calculate_score(
        members, df_stats, z_grid, operational_state="UNVERIFIED_STATE"
    )[0] is None

    # Invalid weather score bounds
    assert AtmosphericScoring.calculate_score(
        members, df_stats, z_grid, weather_score=-1.0
    )[0] is None

    # Altitude grid length mismatch
    z_wrong = np.arange(0, 2000, 100)
    assert AtmosphericScoring.calculate_score(
        members, df_stats, z_wrong
    )[0] is None
