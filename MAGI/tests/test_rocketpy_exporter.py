import pytest
import xarray as xr
import pandas as pd
import numpy as np
import os
import datetime

from casper import MagiSchema
from magi.casper.export.rocketpy import export_rocketpy_ensemble, MAGI_ROCKETPY_MAPPING

def _create_mock_ensemble(num_members=5):
    """Creates a mock ensemble for testing"""
    ensemble = []
    base_time = pd.Timestamp("2026-08-08 12:00:00")
    for i in range(num_members):
        df = MagiSchema.create_empty(10)
        df['valid_time_utc'] = base_time
        df['pressure_pa'] = np.linspace(100000, 10000, 10)
        df['temperature_k'] = 288.15 - np.linspace(0, 50, 10)
        df['u_east_mps'] = np.random.uniform(5, 20, 10)
        df['v_north_mps'] = np.random.uniform(-5, 10, 10)
        df['altitude_msl_m'] = np.linspace(0, 10000, 10)
        df['latitude'] = -22.0
        df['longitude'] = -47.0
        ensemble.append(df)
    return ensemble

def test_export_case_a(tmp_path):
    ensemble = _create_mock_ensemble()
    output_path = tmp_path / "test_a.nc"
    
    export_rocketpy_ensemble(ensemble, output=str(output_path), horizon_hours=24, timestep_hours=1)
    
    ds = xr.open_dataset(output_path)
    assert len(ds.time) == 25
    
    diff_ns = np.timedelta64(ds.time.values[-1] - ds.time.values[0], 'ns')
    assert diff_ns == np.timedelta64(24, 'h')

def test_export_case_b(tmp_path):
    ensemble = _create_mock_ensemble()
    output_path = tmp_path / "test_b.nc"
    
    export_rocketpy_ensemble(ensemble, output=str(output_path), horizon_hours=168, timestep_hours=1)
    
    ds = xr.open_dataset(output_path)
    assert len(ds.time) == 169
    
    diff_ns = np.timedelta64(ds.time.values[-1] - ds.time.values[0], 'ns')
    assert diff_ns == np.timedelta64(168, 'h')

def test_export_case_c(tmp_path):
    ensemble = _create_mock_ensemble()
    output_path = tmp_path / "test_c.nc"
    
    export_rocketpy_ensemble(ensemble, output=str(output_path), horizon_hours=168, timestep_hours=3)
    
    ds = xr.open_dataset(output_path)
    assert len(ds.time) == 57
    
    diff_ns = np.timedelta64(ds.time.values[-1] - ds.time.values[0], 'ns')
    assert diff_ns == np.timedelta64(168, 'h')

def test_export_case_d(tmp_path):
    ensemble = _create_mock_ensemble()
    output_path = tmp_path / "test_d.nc"
    
    export_rocketpy_ensemble(ensemble, output=str(output_path), horizon_hours=168, timestep_hours=6)
    
    ds = xr.open_dataset(output_path)
    assert len(ds.time) == 29
    
    diff_ns = np.timedelta64(ds.time.values[-1] - ds.time.values[0], 'ns')
    assert diff_ns == np.timedelta64(168, 'h')
    
    # Check dimensions and variables
    assert "member" in ds.dims
    assert "time" in ds.dims
    assert "pressure_level" in ds.dims
    assert "temperature" in ds.variables
    assert "u_wind" in ds.variables
    assert "v_wind" in ds.variables

def test_rocketpy_integration(tmp_path):
    """
    Test real integration with RocketPy, if installed.
    """
    try:
        from rocketpy import Environment
    except ImportError:
        pytest.skip("RocketPy is not installed.")
        
    ensemble = _create_mock_ensemble(num_members=3)
    output_path = tmp_path / "rocketpy_integration.nc"
    
    export_rocketpy_ensemble(ensemble, output=str(output_path), horizon_hours=168, timestep_hours=1)
    
    env = Environment(latitude=-22.0, longitude=-47.0, elevation=0)
    
    base_time = datetime.datetime(2026, 8, 8, 12, 0)
    env.set_date((2026, 8, 8, 12))
    
    env.set_atmospheric_model(
        type="Ensemble",
        file=str(output_path),
        dictionary=MAGI_ROCKETPY_MAPPING
    )
    
    # Test member selection
    env.select_ensemble_member(0)
    assert env.get_temperature(0) > 0 # Should return a finite value
    
    env.select_ensemble_member(1)
    assert env.get_temperature(5000) > 0
    
    # Test +120h datetime
    env.set_date((2026, 8, 13, 12))
    env.set_atmospheric_model(
        type="Ensemble",
        file=str(output_path),
        dictionary=MAGI_ROCKETPY_MAPPING
    )
    env.select_ensemble_member(2)
    assert env.get_temperature(1000) > 0
