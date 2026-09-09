import os
import pytest
import numpy as np
import pandas as pd
import xarray as xr
import datetime
import sys

# Add root to sys path to allow importing magi
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from magi.casper.ensemble.generator import EnsembleGenerator
from magi.casper.export.rocketpy import RocketPyEnsembleExporter, MAGI_ROCKETPY_MAPPING

@pytest.fixture
def dummy_ensemble_ds():
    config = {
        "members": 5,
        "seed": 42,
        "pressure_levels": [1000, 900, 800, 500, 200, 10],
        "spatial": {"radius_deg": 0.5, "resolution_deg": 0.5}
    }
    generator = EnsembleGenerator(config=config)
    
    nominal_profile = {
        "u_wind": np.array([5.0, 6.0, 10.0, 20.0, 30.0, 50.0]),
        "v_wind": np.array([2.0, 2.0, 3.0, 5.0, 10.0, 15.0]),
        "temperature": np.array([300.0, 290.0, 280.0, 250.0, 220.0, 220.0]),
        "geopotential_height": np.array([100.0, 1000.0, 2000.0, 5500.0, 12000.0, 30000.0])
    }
    
    valid_time = pd.Timestamp("2026-08-08 12:00:00").to_datetime64()
    ds = generator.generate_synthetic_ensemble(nominal_profile, cov_matrix=None, center_lat=-22.0, center_lon=-48.0, valid_time=valid_time)
    return ds

def test_ensemble_generator(dummy_ensemble_ds):
    ds = dummy_ensemble_ds
    
    # 1. Dimensions
    assert set(ds.dims) == {"member", "time", "pressure_level", "latitude", "longitude"}
    assert ds.sizes["member"] == 5
    assert ds.sizes["time"] == 1
    assert ds.sizes["pressure_level"] == 6
    assert ds.sizes["latitude"] == 3
    assert ds.sizes["longitude"] == 3
    
    # 2. Variables
    for var in ["temperature", "geopotential_height", "u_wind", "v_wind"]:
        assert var in ds.variables
        assert not np.isnan(ds[var].values).any()
        
    # 3. Units
    assert ds["temperature"].attrs["units"] == "K"
    assert ds["geopotential_height"].attrs["units"] == "m"
    assert ds["u_wind"].attrs["units"] == "m s-1"
    assert ds["v_wind"].attrs["units"] == "m s-1"
    assert ds["pressure_level"].attrs["units"] == "hPa"
    assert ds["latitude"].attrs["units"] == "degrees_north"
    assert ds["longitude"].attrs["units"] == "degrees_east"
    
    # 4. Vertical consistency
    hgt = ds["geopotential_height"].isel(member=0, time=0, latitude=1, longitude=1).values
    # Check monotonicity of HGT (should increase with index as pressure decreases)
    assert np.all(np.diff(hgt) > 0)
    
def test_rocketpy_exporter(dummy_ensemble_ds, tmp_path):
    out_file = tmp_path / "test_ensemble.nc"
    exporter = RocketPyEnsembleExporter(config={"compression_level": 4})
    exporter.export(dummy_ensemble_ds, str(out_file), naming="native")
    
    assert out_file.exists()
    
    # Reload and check
    ds_reloaded = xr.open_dataset(str(out_file))
    assert "time" in ds_reloaded.coords
    assert "pressure_level" in ds_reloaded.coords
    assert ds_reloaded.attrs.get("title") == "MAGI Atmospheric Ensemble"
    assert ds_reloaded["temperature"].shape == (5, 1, 6, 3, 3)
    
    ds_reloaded.close()

def test_rocketpy_exporter_gefs_naming(dummy_ensemble_ds, tmp_path):
    out_file = tmp_path / "test_ensemble_gefs.nc"
    exporter = RocketPyEnsembleExporter()
    exporter.export(dummy_ensemble_ds, str(out_file), naming="gefs")
    
    ds_reloaded = xr.open_dataset(str(out_file))
    
    # Check renamed dimensions/variables
    assert "ens" in ds_reloaded.dims
    assert "lev" in ds_reloaded.dims
    assert "tmpprs" in ds_reloaded.variables
    assert "hgtprs" in ds_reloaded.variables
    
    ds_reloaded.close()

try:
    import rocketpy
    ROCKETPY_AVAILABLE = True
except ImportError:
    ROCKETPY_AVAILABLE = False

@pytest.mark.skipif(not ROCKETPY_AVAILABLE, reason="RocketPy is not installed")
def test_rocketpy_integration(dummy_ensemble_ds, tmp_path):
    from rocketpy import Environment
    
    out_file = tmp_path / "rocketpy_magi.nc"
    exporter = RocketPyEnsembleExporter()
    exporter.export(dummy_ensemble_ds, str(out_file), naming="native")
    
    env = Environment(
        latitude=-22.0,
        longitude=-48.0,
        elevation=450
    )
    
    env.set_atmospheric_model(
        type="Ensemble",
        file=str(out_file),
        dictionary=MAGI_ROCKETPY_MAPPING
    )
    
    assert hasattr(env, "num_ensemble_members") or hasattr(env, "ensemble_members")
    
    env.select_ensemble_member(0)
    u0 = env.wind_velocity_x(1000)
    
    env.select_ensemble_member(1)
    u1 = env.wind_velocity_x(1000)
    
    assert np.isfinite(u0)
    assert np.isfinite(u1)
    assert u0 != u1
