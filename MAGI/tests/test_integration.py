import pytest
import numpy as np
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from casper import MagiSchema, CasperPhysics, CasperProcessor
from melchior import Melchior
from balthasar import Balthasar

def test_schema_creation():
    df = MagiSchema.create_empty(5)
    assert len(df) == 5
    assert "valid_time_utc" in df.columns
    assert "density_kgm3" in df.columns

def test_speed_dir_to_uv():
    # Wind from 90 (East) -> going West
    # U should be negative, V should be 0
    u, v = CasperPhysics.speed_dir_to_uv(10, 90)
    assert np.isclose(u, -10.0)
    assert np.isclose(v, 0.0)
    
    # Wind from 180 (South) -> going North
    # U should be 0, V should be positive
    u, v = CasperPhysics.speed_dir_to_uv(10, 180)
    assert np.isclose(u, 0.0)
    assert np.isclose(v, 10.0)

def test_uv_to_speed_dir():
    # U = -10 (going West), V = 0
    # Wind is FROM East (90)
    spd, dir_from = CasperPhysics.uv_to_speed_dir(-10.0, 0.0)
    assert np.isclose(spd, 10.0)
    assert np.isclose(dir_from, 90.0)

def test_density_calculation():
    # Standard atmosphere at sea level roughly: 101325 Pa, 288.15 K, dry air (0% RH)
    # Density should be ~1.225
    rho = CasperPhysics.calc_density(101325, 288.15, 0.0)
    assert np.isclose(rho, 1.225, atol=0.01)

def test_melchior_integration():
    melchior = Melchior(elevation_msl=450)
    df_hist = melchior.fetch_historical_data()
    # It might be empty if cache doesn't exist, but if it doesn't fail, we're good.
    MagiSchema.validate(df_hist)

def test_balthasar_integration():
    balthasar = Balthasar(elevation_msl=450)
    df_curr, is_real = balthasar.fetch_operational_forecast()
    # In fallback mock, df_curr is the dataframe
    if is_real:
        MagiSchema.validate(df_curr[0])
    else:
        MagiSchema.validate(df_curr)

def test_casper_interpolation():
    df_raw = MagiSchema.create_empty(2)
    df_raw['altitude_agl_m'] = [0, 1000]
    df_raw['temperature_k'] = [300, 290]
    df_raw['pressure_pa'] = [100000, 90000]
    df_raw['u_east_mps'] = [5, 10]
    df_raw['v_north_mps'] = [0, 0]
    df_raw['relative_humidity_pct'] = [50, 50]
    df_raw['valid_time_utc'] = pd.to_datetime('2026-07-19T12:00:00Z')
    df_raw['generation_time_utc'] = pd.to_datetime('2026-07-19T10:00:00Z')
    df_raw['data_source'] = 'test'
    df_raw['data_type'] = 'synthetic'
    df_raw['model_name'] = 'test_model'
    df_raw['ensemble_member'] = 'control'
    
    processor = CasperProcessor(elevation_msl=450)
    grid = np.arange(0, 1001, 100)
    df_interp = processor.interpolate_profile(df_raw, grid)
    
    assert len(df_interp) == 11
    MagiSchema.validate(df_interp)
    assert 'VALID' in df_interp['quality_flag'].values
    assert not df_interp['density_kgm3'].isna().any()
    assert not df_interp['wind_shear_s_1'].isna().any()
