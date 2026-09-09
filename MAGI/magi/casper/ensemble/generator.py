import xarray as xr
import numpy as np
import pandas as pd
import datetime

class EnsembleGenerator:
    """
    Generates physically consistent atmospheric ensembles compatible with MAGI and RocketPy.
    """
    def __init__(self, config=None):
        self.config = config or {}
        self.seed = self.config.get("seed", 42069)
        self.num_members = self.config.get("members", 31)
        self.rng = np.random.default_rng(self.seed)
        
        # Default pressure levels from config, or sensible defaults
        self.pressure_levels = self.config.get("pressure_levels", [
            1000, 975, 950, 925, 900, 850, 800, 750, 700, 650, 600, 
            550, 500, 450, 400, 350, 300, 250, 200, 150, 100, 70, 50, 30, 20, 10
        ])
        
        # Spatial config
        spatial = self.config.get("spatial", {})
        self.radius_deg = spatial.get("radius_deg", 0.5)
        self.res_deg = spatial.get("resolution_deg", 0.25)
        
    def _create_spatial_grid(self, center_lat, center_lon):
        """Creates a local latitude/longitude grid."""
        lats = np.arange(center_lat - self.radius_deg, center_lat + self.radius_deg + self.res_deg/2, self.res_deg)
        lons = np.arange(center_lon - self.radius_deg, center_lon + self.radius_deg + self.res_deg/2, self.res_deg)
        return lats, lons
        
    def create_empty_cube(self, times, lats, lons, members):
        """
        Creates an empty Atmospheric Ensemble Cube (xarray.Dataset) with correct coordinates and dimensions.
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
        # Add metadata for coords
        ds.pressure_level.attrs["units"] = "hPa"
        ds.latitude.attrs["units"] = "degrees_north"
        ds.longitude.attrs["units"] = "degrees_east"
        return ds
        
    def generate_synthetic_ensemble(self, nominal_profile, cov_matrix, center_lat, center_lon, valid_time):
        """
        Generates a synthetic ensemble from a nominal profile and a covariance matrix.
        Uses PCA/EOF approach on the covariance matrix to perturb the profile.
        nominal_profile: a dict or dataframe with variables at self.pressure_levels
        """
        lats, lons = self._create_spatial_grid(center_lat, center_lon)
        times = [valid_time]
        members = np.arange(self.num_members)
        
        ds = self.create_empty_cube(times, lats, lons, members)
        
        # We assume nominal_profile has T, HGT, U, V interpolated to the pressure_levels
        # and cov_matrix is for state vector [U, V, T, q] (as in MELCHIOR) or similar.
        # For simplicity in this base implementation, we do a basic EOF/PCA perturbation.
        
        # Let's say nz is the number of pressure levels.
        nz = len(self.pressure_levels)
        
        # Define empty arrays for the 5D variables
        shape = (self.num_members, len(times), nz, len(lats), len(lons))
        
        # Initialize variables
        ds["temperature"] = (("member", "time", "pressure_level", "latitude", "longitude"), np.zeros(shape))
        ds["geopotential_height"] = (("member", "time", "pressure_level", "latitude", "longitude"), np.zeros(shape))
        ds["u_wind"] = (("member", "time", "pressure_level", "latitude", "longitude"), np.zeros(shape))
        ds["v_wind"] = (("member", "time", "pressure_level", "latitude", "longitude"), np.zeros(shape))
        
        # Add units and standard names
        ds["temperature"].attrs.update({"units": "K", "standard_name": "air_temperature"})
        ds["geopotential_height"].attrs.update({"units": "m", "standard_name": "geopotential_height"})
        ds["u_wind"].attrs.update({"units": "m s-1", "standard_name": "eastward_wind"})
        ds["v_wind"].attrs.update({"units": "m s-1", "standard_name": "northward_wind"})
        
        from .synthetic import SyntheticEnsembleGenerator
        
        generator = SyntheticEnsembleGenerator(self.rng, self.pressure_levels)
        member_profiles = generator.generate(nominal_profile, cov_matrix, self.num_members)
        
        for idx, m in enumerate(members):
            prof = member_profiles[idx]
            
            # Broadcast to spatial grid
            for i_lat, lat in enumerate(lats):
                for i_lon, lon in enumerate(lons):
                    ds["u_wind"][m, 0, :, i_lat, i_lon] = prof["u_wind"]
                    ds["v_wind"][m, 0, :, i_lat, i_lon] = prof["v_wind"]
                    ds["temperature"][m, 0, :, i_lat, i_lon] = prof["temperature"]
                    ds["geopotential_height"][m, 0, :, i_lat, i_lon] = prof["geopotential_height"]
                    
        return ds
