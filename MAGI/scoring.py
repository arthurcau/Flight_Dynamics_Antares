"""
Exploratory atmospheric favorability score for aerospace and flight dynamics operations.

WARNING: This module provides atmospheric comparison and diagnostic ranking only.
It does NOT constitute launch authorization.
"""

from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

try:
    from MAGI.state_manager import MagiState
except ImportError:
    from state_manager import MagiState


class AtmosphericScoring:
    """
    Computes an exploratory atmospheric favorability score (0 to 100) for launch operations.
    
    The score evaluates:
    1. Wind speed profile against historical local percentiles (P50, P90, P99) [up to 35 pts]
    2. Wind shear profile against historical local percentiles [up to 25 pts]
    3. Forecast ensemble spread / uncertainty (P90 - P10) [up to 20 pts]
    4. Weather model score & data quality score [up to 20 pts]
    
    Vertical profiles are evaluated level-by-level with a composite formula:
    - 50% weight on the column-averaged profile (weighted towards the surface layer).
    - 50% weight on the critical worst-layer condition (weakest-link principle for rocketry:
      e.g., surface rail exit or transonic shear peak).
    """

    ANALYSIS_TOP_AGL_M = 6000
    DEFAULT_CALIBRATION = {"spread_limits_mps": [2.0, 5.0, 10.0]}

    @staticmethod
    def calculate_score(
        df_ensemble: List[pd.DataFrame],
        df_stats: pd.DataFrame,
        z_grid: Union[List[float], np.ndarray],
        *,
        operational_state: Optional[str] = None,
        calibration: Optional[dict] = None,
        weather_score: Optional[float] = None,
        data_quality_score: Optional[float] = None
    ) -> Tuple[Optional[float], str]:
        """
        Calculate the atmospheric favorability index.

        Parameters
        ----------
        df_ensemble : list of pd.DataFrame
            List of forecast profile DataFrames (must include nominal and/or ensemble members).
            Each DataFrame must contain 'altitude_agl_m', 'wind_speed_mps', 'wind_shear_s_1'.
        df_stats : pd.DataFrame
            Historical climatology statistics indexed by or containing 'altitude_agl_m'
            with median, p90, and p99 columns for wind speed and wind shear.
        z_grid : array-like
            Target vertical altitude grid AGL [m].
        operational_state : str, optional
            Operational pipeline state from StateManager.
        calibration : dict, optional
            Calibration dict containing 'spread_limits_mps' (3 strictly increasing floats).
        weather_score : float, optional
            Precipitation / convective weather quality input (0..10, default 5.0).
        data_quality_score : float, optional
            Data provenance / sensor quality input (0..10, default 5.0).

        Returns
        -------
        score : float or None
            Composite favorability score from 0.0 to 100.0 (None if unavailable).
        score_class : str
            Diagnostic classification string ("EXPLORATORY_ATMOSPHERIC_INDEX" or
            "ATMOSPHERIC_SCORE_UNAVAILABLE").
        """
        unavailable = (None, "ATMOSPHERIC_SCORE_UNAVAILABLE")

        if calibration is None:
            calibration = AtmosphericScoring.DEFAULT_CALIBRATION
        if weather_score is None:
            weather_score = 5.0
        if data_quality_score is None:
            data_quality_score = 5.0
        if operational_state is None:
            operational_state = MagiState.CURRENT_FORECAST

        allowed_states = {MagiState.CURRENT_FORECAST, MagiState.CACHED_FORECAST, MagiState.DEGRADED_DATA}
        if (
            len(df_ensemble or []) < 1
            or df_stats is None
            or df_stats.empty
            or not calibration
            or operational_state not in allowed_states
            or weather_score is None
            or data_quality_score is None
        ):
            return unavailable

        if not all(np.isfinite(value) and 0 <= value <= 10 for value in (weather_score, data_quality_score)):
            return unavailable

        z = np.asarray(z_grid, dtype=float)
        mask = (z >= 0) & (z <= AtmosphericScoring.ANALYSIS_TOP_AGL_M)
        if not mask.any():
            return unavailable

        z_eval = z[mask]
        winds, shears = [], []
        accepted_flags = {
            "VALID",
            "SYNTHETIC_MODEL",
            "SYNTHETIC_SURFACE_LAYER",
            "API_PROFILE",
            "HYDROSTATIC_WARNING",
        }

        for frame in df_ensemble:
            if len(frame) != len(z) or not np.array_equal(frame.altitude_agl_m.to_numpy(), z):
                return unavailable
            if "quality_flag" in frame and not frame.loc[mask, "quality_flag"].isin(accepted_flags).all():
                return unavailable
            wind = frame.wind_speed_mps.to_numpy(dtype=float)[mask]
            shear = frame.wind_shear_s_1.to_numpy(dtype=float)[mask]
            if not np.isfinite(wind).all() or not np.isfinite(shear).all():
                return unavailable
            winds.append(wind)
            shears.append(shear)

        winds_arr = np.asarray(winds)   # shape: (num_members, n_levels)
        shears_arr = np.asarray(shears) # shape: (num_members, n_levels)

        # Reindex historical stats to evaluation grid
        if "altitude_agl_m" in df_stats.columns:
            stats = df_stats.set_index("altitude_agl_m").reindex(z_eval)
        else:
            stats = df_stats.reindex(z_eval)

        # Baseline weather and sensor quality score (0..20 pts)
        score = float(weather_score + data_quality_score)

        # Height weighting: w(z) emphasizes surface rail exit (0-500m) while maintaining
        # awareness of transonic/max-Q and upper troposphere
        weights = 0.5 + 0.5 * np.exp(-z_eval / 1000.0)
        weight_sum = np.sum(weights)

        # Evaluate Wind Speed and Wind Shear
        for var_name, data_arr, max_pts, mid_pts in (
            ("wind_speed_mps", winds_arr, 35.0, 20.0),
            ("wind_shear_s_1", shears_arr, 25.0, 15.0),
        ):
            columns = [f"{var_name}_{stat}" for stat in ("median", "p90", "p99")]
            if not set(columns) <= set(stats.columns):
                return unavailable

            values = stats[columns].to_numpy(dtype=float)  # shape: (n_levels, 3)
            if not np.isfinite(values).all():
                return unavailable

            # Verify that historical thresholds are strictly increasing at all levels
            if np.any(np.diff(values, axis=1) <= 0):
                return unavailable

            # Conservative representative profile: 75th percentile of the ensemble
            # (or mean/nominal if single member)
            if data_arr.shape[0] > 1:
                cur_profile = np.percentile(data_arr, 75, axis=0)
            else:
                cur_profile = data_arr[0]

            # Level-by-level evaluation
            level_scores = np.empty(len(z_eval), dtype=float)
            for k in range(len(z_eval)):
                thresh_k = values[k]
                level_scores[k] = float(np.interp(cur_profile[k], thresh_k, (max_pts, mid_pts, 0.0)))

            # Composite rocketry score: 50% weighted column average + 50% critical worst layer
            weighted_avg = float(np.sum(level_scores * weights) / weight_sum)
            worst_layer = float(np.min(level_scores))
            score += 0.5 * weighted_avg + 0.5 * worst_layer

        # Evaluate Ensemble Spread / Uncertainty (0..20 pts)
        limits = np.asarray(calibration.get("spread_limits_mps", []), dtype=float)
        if limits.shape != (3,) or not np.isfinite(limits).all() or np.any(np.diff(limits) <= 0):
            return unavailable

        if winds_arr.shape[0] > 1:
            # Spread across ensemble: P90 - P10 along altitude
            spread_profile = np.percentile(winds_arr, 90, axis=0) - np.percentile(winds_arr, 10, axis=0)
            weighted_spread = float(np.sum(spread_profile * weights) / weight_sum)
        else:
            weighted_spread = 0.0

        spread_points = float(np.interp(weighted_spread, limits, (20.0, 5.0, 0.0)))
        score += spread_points

        score = float(np.clip(score, 0.0, 100.0))
        return score, "EXPLORATORY_ATMOSPHERIC_INDEX"
