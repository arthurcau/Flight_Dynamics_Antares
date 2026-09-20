import datetime
import pandas as pd
import pytest
from MAGI.balthasar import Balthasar
from MAGI.interface import get_atmospheric_profile, get_atmospheric_ensemble


def test_balthasar_safe_replace_year():
    leap_date = pd.Timestamp("2024-02-29 12:00:00+00:00")
    # 2023 is non-leap year -> should gracefully return Feb 28
    replaced_2023 = Balthasar._safe_replace_year(leap_date, 2023)
    assert replaced_2023.year == 2023
    assert replaced_2023.month == 2
    assert replaced_2023.day == 28

    # 2020 is leap year -> should keep Feb 29
    replaced_2020 = Balthasar._safe_replace_year(leap_date, 2020)
    assert replaced_2020.year == 2020
    assert replaced_2020.month == 2
    assert replaced_2020.day == 29


def test_balthasar_forecast_horizon():
    b = Balthasar()
    past_date = pd.Timestamp("2023-05-10 12:00:00+00:00")
    future_date = pd.Timestamp.now(tz="UTC") + pd.Timedelta(days=45)
    assert not b._is_beyond_forecast_horizon(past_date)
    assert b._is_beyond_forecast_horizon(future_date)


def test_balthasar_resolve_historical_years():
    b = Balthasar()
    # Explicit years should be respected
    years = b._resolve_historical_years(pd.Timestamp("2027-09-03T14:30:00Z"), explicit_years=[2022, 2024])
    assert years == [2022, 2024]

    # Automatic years should start at 2021
    auto_years = b._resolve_historical_years(pd.Timestamp("2027-09-03T14:30:00Z"))
    assert auto_years[0] == 2021
    assert len(auto_years) >= 4


def test_get_atmospheric_profile_future_date():
    # Calling get_atmospheric_profile with future flight date 2027-09-03
    profile = get_atmospheric_profile(
        latitude=-21.9430528,
        longitude=-48.9540861,
        elevation=420.0,
        target_date_str="2027-09-03T17:30:00Z",
        max_altitude_agl_m=1000,
        vertical_step_m=100
    )
    assert profile is not None
    assert len(profile.altitude_asl_m) > 0
    assert profile.source_type == "historical_surrogate"
    assert "historical_reference_year" in profile.metadata
    assert "target_date_utc" in profile.metadata


def test_get_atmospheric_ensemble_future_date():
    # Calling get_atmospheric_ensemble with future flight date and explicit historical years
    ensemble = get_atmospheric_ensemble(
        latitude=-21.9430528,
        longitude=-48.9540861,
        elevation=420.0,
        target_date_str="2027-09-03T17:30:00Z",
        time_window_minutes=0,
        historical_years=[2022, 2023],
        max_altitude_agl_m=1000,
        vertical_step_m=100
    )
    assert len(ensemble) == 2
    assert ensemble[0].source_type == "historical_multi_year_ensemble"
    assert int(ensemble[0].metadata["historical_reference_year"]) == 2022
    assert int(ensemble[1].metadata["historical_reference_year"]) == 2023
