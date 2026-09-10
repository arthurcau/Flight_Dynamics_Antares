import pytest
import numpy as np
import datetime
from antares_fd.environment.atmosphere import AtmosphericProfile
from antares_fd.config.exceptions import ConfigurationError

def test_atmospheric_profile_validation_success():
    profile = AtmosphericProfile(
        altitude_asl_m=np.array([400, 500, 600]),
        pressure_pa=np.array([96000, 95000, 94000]),
        temperature_k=np.array([290, 289, 288]),
        wind_u_mps=np.array([2.0, 2.5, 3.0]),
        wind_v_mps=np.array([1.0, 1.0, 1.2]),
        source="Test",
        source_type="deterministic",
        model="TestModel",
        run_time_utc=None,
        valid_time_utc=datetime.datetime.utcnow(),
        latitude_deg=0.0,
        longitude_deg=0.0,
        member_id=None
    )
    assert len(profile.altitude_asl_m) == 3

def test_atmospheric_profile_validation_length_mismatch():
    with pytest.raises(ConfigurationError):
        AtmosphericProfile(
            altitude_asl_m=np.array([400, 500]),
            pressure_pa=np.array([96000, 95000, 94000]), # Mismatch
            temperature_k=np.array([290, 289]),
            wind_u_mps=np.array([2.0, 2.5]),
            wind_v_mps=np.array([1.0, 1.0]),
            source="Test",
            source_type="deterministic",
            model="TestModel",
            run_time_utc=None,
            valid_time_utc=datetime.datetime.utcnow(),
            latitude_deg=0.0,
            longitude_deg=0.0,
            member_id=None
        )

def test_atmospheric_profile_validation_nan():
    with pytest.raises(ConfigurationError):
        AtmosphericProfile(
            altitude_asl_m=np.array([400, 500]),
            pressure_pa=np.array([96000, np.nan]), # NaN value
            temperature_k=np.array([290, 289]),
            wind_u_mps=np.array([2.0, 2.5]),
            wind_v_mps=np.array([1.0, 1.0]),
            source="Test",
            source_type="deterministic",
            model="TestModel",
            run_time_utc=None,
            valid_time_utc=datetime.datetime.utcnow(),
            latitude_deg=0.0,
            longitude_deg=0.0,
            member_id=None
        )

def test_atmospheric_profile_validation_monotonic():
    with pytest.raises(ConfigurationError):
        AtmosphericProfile(
            altitude_asl_m=np.array([500, 400]), # Non-monotonic
            pressure_pa=np.array([95000, 96000]),
            temperature_k=np.array([289, 290]),
            wind_u_mps=np.array([2.5, 2.0]),
            wind_v_mps=np.array([1.0, 1.0]),
            source="Test",
            source_type="deterministic",
            model="TestModel",
            run_time_utc=None,
            valid_time_utc=datetime.datetime.utcnow(),
            latitude_deg=0.0,
            longitude_deg=0.0,
            member_id=None
        )
