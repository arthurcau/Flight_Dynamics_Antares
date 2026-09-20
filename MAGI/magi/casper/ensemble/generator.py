"""
Ensemble Cube Generator for MAGI and RocketPy.

Orchestrates synthetic 5D atmospheric ensemble cubes (member, time, pressure_level, latitude, longitude)
combining horizontal spatial tiling, isobaric vertical profiles, and EOF stochastic perturbations.
"""

from typing import Dict, List, Optional, Union
import datetime
import numpy as np
import pandas as pd
import xarray as xr


class EnsembleGenerator:
    """
    Generates physically consistent atmospheric ensembles compatible with MAGI and RocketPy.
    """

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.seed = self.config.get("seed", 42069)
        self.num_members = self.config.get("members", 31)
        self.rng = np.random.default_rng(self.seed)

        # Default standard pressure levels (hPa)
        self.pressure_levels = self.config.get("pressure_levels", [
            1000, 975, 950, 925, 900, 850, 800, 750, 700, 650, 600,
            550, 500, 450, 400, 350, 300, 250, 200, 150, 100, 70, 50, 30, 20, 10
        ])

        # Spatial grid configuration around launch site
        spatial = self.config.get("spatial", {})
        self.radius_deg = spatial.get("radius_deg", 0.5)
        self.res_deg = spatial.get("resolution_deg", 0.25)

    def _create_spatial_grid(self, center_lat: float, center_lon: float):
        """Create local latitude and longitude coordinate arrays."""
        lats = np.arange(center_lat - self.radius_deg, center_lat + self.radius_deg + self.res_deg / 2, self.res_deg)
        lons = np.arange(center_lon - self.radius_deg, center_lon + self.radius_deg + self.res_deg / 2, self.res_deg)
        return lats, lons

    def create_empty_cube(self, times, lats, lons, members) -> xr.Dataset:
        """
        Create an empty Atmospheric Ensemble Cube (xarray.Dataset) with CF metadata.
        """
        ds = xr.Dataset(
            coords={
                "member": members,
                "time": times,
                "pressure_level": self.pressure_levels,
                "latitude": lats,
                "longitude": lons
            }
        )
        ds.pressure_level.attrs["units"] = "hPa"
        ds.latitude.attrs["units"] = "degrees_north"
        ds.longitude.attrs["units"] = "degrees_east"
        return ds

    def generate_synthetic_ensemble(
        self,
        nominal_profile: dict,
        cov_matrix: Optional[np.ndarray],
        center_lat: float,
        center_lon: float,
        valid_time: Union[pd.Timestamp, np.datetime64, datetime.datetime]
    ) -> xr.Dataset:
        """
        Generate a synthetic ensemble dataset from a nominal profile and a covariance matrix.

        Parameters
        ----------
        nominal_profile : dict
            Dictionary or DataFrame containing vertical profiles at `self.pressure_levels`.
        cov_matrix : np.ndarray, optional
            Multivariate covariance matrix from reanalysis or historical data.
        center_lat : float
            Launch site latitude in degrees.
        center_lon : float
            Launch site longitude in degrees.
        valid_time : Timestamp-like
            Valid time for the atmospheric forecast.

        Returns
        -------
        xr.Dataset
            5D xarray Dataset containing variables: temperature, geopotential_height,
            u_wind, v_wind, and specific_humidity.
        """
        lats, lons = self._create_spatial_grid(center_lat, center_lon)
        times = [valid_time]
        members = np.arange(self.num_members)

        ds = self.create_empty_cube(times, lats, lons, members)

        nz = len(self.pressure_levels)
        shape = (self.num_members, len(times), nz, len(lats), len(lons))

        ds["temperature"] = (("member", "time", "pressure_level", "latitude", "longitude"), np.zeros(shape))
        ds["geopotential_height"] = (("member", "time", "pressure_level", "latitude", "longitude"), np.zeros(shape))
        ds["u_wind"] = (("member", "time", "pressure_level", "latitude", "longitude"), np.zeros(shape))
        ds["v_wind"] = (("member", "time", "pressure_level", "latitude", "longitude"), np.zeros(shape))
        ds["specific_humidity"] = (("member", "time", "pressure_level", "latitude", "longitude"), np.zeros(shape))

        ds["temperature"].attrs.update({"units": "K", "standard_name": "air_temperature"})
        ds["geopotential_height"].attrs.update({"units": "m", "standard_name": "geopotential_height"})
        ds["u_wind"].attrs.update({"units": "m s-1", "standard_name": "eastward_wind"})
        ds["v_wind"].attrs.update({"units": "m s-1", "standard_name": "northward_wind"})
        ds["specific_humidity"].attrs.update({"units": "kg kg-1", "standard_name": "specific_humidity"})

        from .synthetic import SyntheticEnsembleGenerator

        generator = SyntheticEnsembleGenerator(self.rng, self.pressure_levels)
        member_profiles = generator.generate(nominal_profile, cov_matrix, self.num_members)

        for idx, m in enumerate(members):
            prof = member_profiles[idx]
            # Fast vectorized broadcast along spatial dimensions
            ds["u_wind"][m, 0, :, :, :] = prof["u_wind"][:, None, None]
            ds["v_wind"][m, 0, :, :, :] = prof["v_wind"][:, None, None]
            ds["temperature"][m, 0, :, :, :] = prof["temperature"][:, None, None]
            ds["geopotential_height"][m, 0, :, :, :] = prof["geopotential_height"][:, None, None]
            if "specific_humidity" in prof:
                ds["specific_humidity"][m, 0, :, :, :] = prof["specific_humidity"][:, None, None]

        return ds
