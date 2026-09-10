import numpy as np
from dataclasses import dataclass
from typing import Optional
import datetime
from antares_fd.config.exceptions import ConfigurationError

@dataclass(frozen=True)
class AtmosphericProfile:
    altitude_asl_m: np.ndarray
    pressure_pa: np.ndarray
    temperature_k: np.ndarray
    wind_u_mps: np.ndarray
    wind_v_mps: np.ndarray

    source: str
    source_type: str
    model: Optional[str]
    run_time_utc: Optional[datetime.datetime]
    valid_time_utc: datetime.datetime
    latitude_deg: float
    longitude_deg: float
    member_id: Optional[str]

    def __post_init__(self):
        # Validate lengths
        n = len(self.altitude_asl_m)
        if n < 2:
            raise ConfigurationError("Atmospheric profile must have at least 2 altitude levels.")
        
        for name, arr in [
            ("pressure_pa", self.pressure_pa),
            ("temperature_k", self.temperature_k),
            ("wind_u_mps", self.wind_u_mps),
            ("wind_v_mps", self.wind_v_mps)
        ]:
            if len(arr) != n:
                raise ConfigurationError(f"Array {name} length ({len(arr)}) does not match altitude length ({n}).")
            
            if np.isnan(arr).any() or np.isinf(arr).any():
                raise ConfigurationError(f"Array {name} contains NaN or Inf values.")

        # Validate monotonicity and duplicates
        if not np.all(np.diff(self.altitude_asl_m) > 0):
            raise ConfigurationError("Altitude array is not strictly monotonically increasing.")

        # Validate physical bounds
        if np.any(self.pressure_pa <= 0):
            raise ConfigurationError("Pressure array contains non-positive values.")
        
        if np.any(self.temperature_k <= 0):
            raise ConfigurationError("Temperature array contains non-positive values.")

