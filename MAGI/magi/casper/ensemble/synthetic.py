import numpy as np
import xarray as xr
from .eof import apply_eof_perturbation

class SyntheticEnsembleGenerator:
    """
    Generates synthetic ensemble members using historical atmospheric error statistics.
    """
    def __init__(self, rng, pressure_levels):
        self.rng = rng
        self.pressure_levels = pressure_levels
        self.nz = len(pressure_levels)

    def generate(self, nominal_profile, cov_matrix, num_members):
        """
        Generates num_members physically realistic perturbations.
        Returns a list of dictionaries containing U, V, T, HGT arrays for each member.
        """
        # Try EOF approach
        perturbations = apply_eof_perturbation(nominal_profile, cov_matrix, self.rng, self.nz, num_members)
        
        u_nom = np.array(nominal_profile.get("u_wind", np.zeros(self.nz)))
        v_nom = np.array(nominal_profile.get("v_wind", np.zeros(self.nz)))
        t_nom = np.array(nominal_profile.get("temperature", np.full(self.nz, 280.0)))
        hgt_nom = np.array(nominal_profile.get("geopotential_height", np.linspace(0, 30000, self.nz)))
        
        members = []
        if perturbations is not None:
            for u_m, v_m, t_m in perturbations:
                hgt_m = self._calculate_hydrostatic_height(hgt_nom[0], t_m)
                members.append({
                    "u_wind": u_m,
                    "v_wind": v_m,
                    "temperature": t_m,
                    "geopotential_height": hgt_m
                })
        else:
            # Fallback to vertical correlation model
            L = 10.0 # Correlation length in pressure indices
            cov_z = np.exp(-np.abs(np.arange(self.nz)[:, None] - np.arange(self.nz)[None, :]) / L)
            L_chol = np.linalg.cholesky(cov_z + 1e-6 * np.eye(self.nz))
            
            for _ in range(num_members):
                u_m = u_nom + L_chol @ self.rng.standard_normal(self.nz) * 2.0
                v_m = v_nom + L_chol @ self.rng.standard_normal(self.nz) * 2.0
                t_m = t_nom + L_chol @ self.rng.standard_normal(self.nz) * 1.0
                hgt_m = self._calculate_hydrostatic_height(hgt_nom[0], t_m)
                
                members.append({
                    "u_wind": u_m,
                    "v_wind": v_m,
                    "temperature": t_m,
                    "geopotential_height": hgt_m
                })
        return members
        
    def _calculate_hydrostatic_height(self, h0, t_profile):
        """
        Calculates geopotential height using the hypsometric equation for physical consistency.
        """
        hgt = np.zeros(self.nz)
        hgt[0] = h0
        Rd = 287.05
        g = 9.80665
        for i in range(1, self.nz):
            p1 = self.pressure_levels[i-1]
            p2 = self.pressure_levels[i]
            T_avg = (t_profile[i] + t_profile[i-1]) / 2.0
            if p1 > 0 and p2 > 0:
                dz = (Rd * T_avg / g) * np.log(p1 / p2)
                hgt[i] = hgt[i-1] + dz
            else:
                hgt[i] = hgt[i-1]
        return hgt
