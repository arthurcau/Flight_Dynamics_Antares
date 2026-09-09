import warnings
import xarray as xr
import numpy as np
import pandas as pd
import datetime
import os

MAGI_ROCKETPY_MAPPING = {
    "time": "time",
    "latitude": "latitude",
    "longitude": "longitude",
    "level": "pressure_level",
    "ensemble": "member",

    "temperature": "temperature",
    "surface_geopotential_height": None,
    "geopotential_height": "geopotential_height",
    "geopotential": None,
    "u_wind": "u_wind",
    "v_wind": "v_wind",
}

class RocketPyEnsembleExporter:
    """
    Exports MAGI xarray ensembles to a RocketPy-compatible NetCDF format.
    """
    def __init__(self, config=None):
        self.config = config or {}

    def validate_dataset(self, ds: xr.Dataset):
        """
        Validates the dataset for RocketPy compatibility and physical sanity.
        """
        expected_dims = {"member", "time", "pressure_level", "latitude", "longitude"}
        missing_dims = expected_dims - set(ds.dims)
        if missing_dims:
            raise ValueError(f"Missing required dimensions: {missing_dims}")

        pressures = ds.pressure_level.to_index()
        if not (pressures.is_monotonic_decreasing or pressures.is_monotonic_increasing):
            raise ValueError("pressure_level coordinate must be strictly monotonic")

        if not (-90 <= ds.latitude.min() <= 90 and -90 <= ds.latitude.max() <= 90):
            raise ValueError("latitude coordinate out of bounds [-90, 90]")
        
        required_vars = ["temperature", "geopotential_height", "u_wind", "v_wind"]
        for var in required_vars:
            if var not in ds.variables:
                raise ValueError(f"Missing required variable: {var}")
            
            if ds[var].isnull().any():
                warnings.warn(f"Variable {var} contains NaNs. RocketPy might interpolate or fail.")
        return True

    def export(self, ensemble_ds: xr.Dataset, filename: str, naming: str = "native"):
        self.validate_dataset(ensemble_ds)
        ds_out = ensemble_ds.copy()

        if naming == "gefs":
            rename_dict = {
                "member": "ens",
                "pressure_level": "lev",
                "latitude": "lat",
                "longitude": "lon",
                "temperature": "tmpprs",
                "geopotential_height": "hgtprs",
                "u_wind": "ugrdprs",
                "v_wind": "vgrdprs"
            }
            rename_dict = {k: v for k, v in rename_dict.items() if k in ds_out.dims or k in ds_out.variables}
            ds_out = ds_out.rename(rename_dict)

        # Global metadata
        ds_out.attrs.update({
            "title": "MAGI Atmospheric Ensemble",
            "institution": "MAGI",
            "source": "MAGI-CASPER",
            "generation_method": "Synthetic / Operational Ensemble",
            "history": f"Generated {datetime.datetime.now(datetime.UTC).isoformat()}",
            "Conventions": "CF-1.8",
            "MAGI_version": "3.0.0",
        })

        encoding = {}
        for var in ds_out.data_vars:
            encoding[var] = {"zlib": True, "complevel": self.config.get("compression_level", 4)}

        # Setting proper units for CF time encoding to avoid the '6 minutes' or similar bugs
        # when read by other tools (like netCDF4 in RocketPy)
        if "time" in ds_out.coords:
            encoding["time"] = {
                "units": "hours since 1970-01-01 00:00:00",
                "calendar": "proleptic_gregorian",
                "dtype": "float64" # Ensuring it is a double-precision float to avoid rounding
            }

        ds_out.to_netcdf(filename, encoding=encoding)
        return filename

def export_rocketpy_ensemble(ensemble, output="MAGI_ensemble.nc", horizon_hours=168, timestep_hours=1):
    """
    Exports a list of MAGI DataFrames to a RocketPy-compatible NetCDF ensemble file.
    It generates a temporal evolution over 'horizon_hours'.
    """
    if not ensemble:
        raise ValueError("No ensemble members provided.")
        
    # Standardize and extract single timestamp logic for generating evolution
    df0 = ensemble[0]
    df0 = df0.dropna(subset=['pressure_pa', 'temperature_k', 'u_east_mps', 'v_north_mps'])
    
    if 'valid_time_utc' not in df0.columns:
        raise ValueError("Missing valid_time_utc in ensemble members.")
    
    # We take the base time from the first member
    base_time = pd.to_datetime(df0['valid_time_utc'].iloc[0]).tz_localize(None)
    
    # Generate continuous time axis
    num_timestamps = int(round(horizon_hours / timestep_hours)) + 1
    # Use pd.Timedelta to support float values for timestep_hours (e.g., 30 seconds = 30/3600 hours)
    step_delta = pd.Timedelta(hours=timestep_hours)
    time_array = pd.date_range(start=base_time, periods=num_timestamps, freq=step_delta)
    
    pressure_levels = df0['pressure_pa'].values / 100.0 # Convert Pa to hPa
    
    nz = len(pressure_levels)
    num_members = len(ensemble)
    nt = len(time_array)
    
    # Center lat/lon defaults if not present
    center_lat = df0['latitude'].iloc[0] if 'latitude' in df0.columns else -21.895
    center_lon = df0['longitude'].iloc[0] if 'longitude' in df0.columns else -48.966
    
    # Grid de pelo menos 10km de raio (~0.1 graus = 11.1km)
    delta_deg = 0.1
    lat_array = np.array([center_lat - delta_deg, center_lat, center_lat + delta_deg])
    lon_array = np.array([center_lon - delta_deg, center_lon, center_lon + delta_deg])
    
    nx = len(lon_array)
    ny = len(lat_array)
    
    shape = (num_members, nt, nz, ny, nx)
    
    # Preallocate numpy arrays
    temp_arr = np.zeros(shape)
    hgt_arr = np.zeros(shape)
    u_arr = np.zeros(shape)
    v_arr = np.zeros(shape)
    
    for i, df in enumerate(ensemble):
        df_valid = df.dropna(subset=['pressure_pa', 'temperature_k', 'u_east_mps', 'v_north_mps'])
        
        t_prof = df_valid['temperature_k'].values
        u_prof = df_valid['u_east_mps'].values
        v_prof = df_valid['v_north_mps'].values
        if 'altitude_msl_m' in df_valid.columns:
            z_prof = df_valid['altitude_msl_m'].values
        else:
            z_prof = df_valid['altitude_agl_m'].values
            
        for t_idx in range(nt):
            temp_arr[i, t_idx, :, :, :] = t_prof[:, None, None]
            u_arr[i, t_idx, :, :, :] = u_prof[:, None, None]
            v_arr[i, t_idx, :, :, :] = v_prof[:, None, None]
            hgt_arr[i, t_idx, :, :, :] = z_prof[:, None, None]
            
    ds = xr.Dataset(
        coords={
            "member": np.arange(num_members),
            "time": time_array,
            "pressure_level": pressure_levels,
            "latitude": lat_array,
            "longitude": lon_array
        }
    )
    
    ds.pressure_level.attrs["units"] = "hPa"
    ds.latitude.attrs["units"] = "degrees_north"
    ds.longitude.attrs["units"] = "degrees_east"
    
    ds["temperature"] = (("member", "time", "pressure_level", "latitude", "longitude"), temp_arr)
    ds["geopotential_height"] = (("member", "time", "pressure_level", "latitude", "longitude"), hgt_arr)
    ds["u_wind"] = (("member", "time", "pressure_level", "latitude", "longitude"), u_arr)
    ds["v_wind"] = (("member", "time", "pressure_level", "latitude", "longitude"), v_arr)
            
    # Add units
    ds["temperature"].attrs.update({"units": "K"})
    ds["geopotential_height"].attrs.update({"units": "m"})
    ds["u_wind"].attrs.update({"units": "m/s"})
    ds["v_wind"].attrs.update({"units": "m/s"})
    
    ds.attrs['forecast_horizon_hours'] = horizon_hours
    ds.attrs['temporal_resolution_hours'] = timestep_hours
    ds.attrs['ensemble_members'] = num_members
    ds.attrs['forecast_reference_time'] = base_time.isoformat()
    
    exporter = RocketPyEnsembleExporter()
    exported_file = exporter.export(ds, output)
    
    # 8. reabrir o arquivo e 9. validar novamente
    ds_reopen = xr.open_dataset(exported_file)
    t_vals = ds_reopen.time.values
    
    if len(t_vals) < 2:
        if horizon_hours > 0:
            raise ValueError(f"Expected multiple timestamps, got {len(t_vals)}")
    else:
        # Check total duration in nanoseconds
        # t_vals is datetime64[ns], so subtracting them gives timedelta64[ns].
        # .astype('timedelta64[ns]') ensures the unit is ns before extracting the int value.
        total_duration_ns = int(np.timedelta64(t_vals[-1] - t_vals[0], 'ns').astype('timedelta64[ns]').astype(int))
        expected_duration_ns = pd.Timedelta(hours=horizon_hours).value
        
        # We allow a small float error tolerance by comparing nanoseconds
        if abs(total_duration_ns - expected_duration_ns) > 1e6: # 1 ms tolerance
            raise ValueError(f"Round-trip time validation failed. Expected {horizon_hours}h duration, got {total_duration_ns} ns")
            
        # Check step size
        step_ns = int(np.timedelta64(t_vals[1] - t_vals[0], 'ns').astype('timedelta64[ns]').astype(int))
        expected_step_ns = pd.Timedelta(hours=timestep_hours).value
        if abs(step_ns - expected_step_ns) > 1e6:
            raise ValueError(f"Round-trip time step validation failed. Expected {timestep_hours}h, got {step_ns} ns")

    return exported_file

def dataframes_to_rocketpy_dataset(*args, **kwargs):
    raise DeprecationWarning("Use export_rocketpy_ensemble instead.")
