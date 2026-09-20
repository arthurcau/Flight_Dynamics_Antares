"""
Synthetic atmospheric ensemble generation for MAGI in pressure coordinates.

Applies historical multivariate error statistics to nominal atmospheric profiles
while strictly preserving hydrostatic balance and moist-air buoyancy (virtual temperature).
"""

from typing import Dict, List, Optional, Union
import numpy as np
import xarray as xr
from .eof import apply_eof_perturbation


class SyntheticEnsembleGenerator:
    """
    Generates synthetic ensemble members using historical atmospheric error statistics.
    
    Attributes
    ----------
    rng : np.random.Generator
        Random number generator for stochastic sampling.
    pressure_levels : np.ndarray or list of float
        Isobaric levels (hPa) on which profiles are defined.
    nz : int
        Number of vertical pressure levels.
    """

    # Physical constants (WMO / ICAO Standard Atmosphere)
    RD_J_KG_K = 287.058    # Gas constant for dry air [J / (kg * K)]
    G0_M_S2 = 9.80665      # Standard acceleration of gravity [m / s^2]

    def __init__(self, rng: np.random.Generator, pressure_levels: Union[List[float], np.ndarray]):
        self.rng = rng
        self.pressure_levels = np.asarray(pressure_levels, dtype=float)
        self.nz = len(self.pressure_levels)

    def generate(
        self,
        nominal_profile: Dict[str, np.ndarray],
        cov_matrix: Optional[np.ndarray],
        num_members: int
    ) -> List[Dict[str, np.ndarray]]:
        """
        Generate `num_members` physically consistent vertical profile realizations.

        Parameters
        ----------
        nominal_profile : dict
            Baseline profile containing "u_wind", "v_wind", "temperature",
            "geopotential_height", and optionally "specific_humidity".
        cov_matrix : np.ndarray, optional
            Multivariate covariance matrix from historical reanalysis (MELCHIOR).
        num_members : int
            Number of ensemble members to generate.

        Returns
        -------
        list of dict
            List of member dictionaries containing "u_wind", "v_wind", "temperature",
            "specific_humidity", and "geopotential_height" arrays of shape (nz,).
        """
        perturbations = apply_eof_perturbation(nominal_profile, cov_matrix, self.rng, self.nz, num_members)

        u_nom = np.asarray(nominal_profile.get("u_wind", np.zeros(self.nz)), dtype=float)
        v_nom = np.asarray(nominal_profile.get("v_wind", np.zeros(self.nz)), dtype=float)
        t_nom = np.asarray(nominal_profile.get("temperature", np.full(self.nz, 280.0)), dtype=float)
        hgt_nom = np.asarray(nominal_profile.get("geopotential_height", np.linspace(0, 30000, self.nz)), dtype=float)
        q_nom = np.asarray(nominal_profile.get("specific_humidity", np.zeros(self.nz)), dtype=float)

        members = []
        if perturbations is not None:
            for pert in perturbations:
                if len(pert) == 4:
                    u_m, v_m, t_m, q_m = pert
                else:
                    u_m, v_m, t_m = pert[:3]
                    q_m = q_nom

                # Reconstruct geopotential height hydrostatically using virtual temperature
                hgt_m = self._calculate_hydrostatic_height(hgt_nom[0], t_m, q_profile=q_m)
                members.append({
                    "u_wind": u_m,
                    "v_wind": v_m,
                    "temperature": t_m,
                    "specific_humidity": q_m if q_m is not None else q_nom,
                    "geopotential_height": hgt_m
                })
        else:
            # Fallback to vertical correlation model (exponential covariance along index)
            L = 10.0  # Correlation length in pressure indices
            idx = np.arange(self.nz)
            cov_z = np.exp(-np.abs(idx[:, None] - idx[None, :]) / L)
            L_chol = np.linalg.cholesky(cov_z + 1e-6 * np.eye(self.nz))

            for _ in range(num_members):
                u_m = u_nom + L_chol @ self.rng.standard_normal(self.nz) * 2.0
                v_m = v_nom + L_chol @ self.rng.standard_normal(self.nz) * 2.0
                t_m = np.maximum(t_nom + L_chol @ self.rng.standard_normal(self.nz) * 1.0, 150.0)
                q_pert = L_chol @ self.rng.standard_normal(self.nz) * 0.0005
                q_m = np.clip(q_nom + q_pert, 0.0, 0.05)

                hgt_m = self._calculate_hydrostatic_height(hgt_nom[0], t_m, q_profile=q_m)
                members.append({
                    "u_wind": u_m,
                    "v_wind": v_m,
                    "temperature": t_m,
                    "specific_humidity": q_m,
                    "geopotential_height": hgt_m
                })
        return members

    def _calculate_hydrostatic_height(
        self,
        h0: float,
        t_profile: np.ndarray,
        q_profile: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Calculate geopotential height using the hypsometric equation with virtual temperature.

        Equation:
            dz = (Rd * Tv_layer / g0) * ln(p_lower / p_upper)
            Tv = T * (1 + 0.608 * q)

        Supports both bottom-to-top (decreasing pressure) and top-to-bottom (increasing pressure)
        vertical coordinates, preserving strict physical altitude monotonicity.

        Parameters
        ----------
        h0 : float
            Base geopotential height at level index 0 [m].
        t_profile : np.ndarray
            Temperature profile [K], shape (nz,).
        q_profile : np.ndarray, optional
            Specific humidity profile [kg/kg], shape (nz,).

        Returns
        -------
        np.ndarray
            Hydrostatically integrated geopotential height profile [m], shape (nz,).
        """
        p = np.asarray(self.pressure_levels, dtype=float)
        t = np.asarray(t_profile, dtype=float)
        if self.nz < 2:
            return np.full(self.nz, h0)

        if q_profile is not None:
            q = np.asarray(q_profile, dtype=float)
            tv = t * (1.0 + 0.608 * q)
        else:
            tv = t

        # Layer-average virtual temperature
        tv_mid = 0.5 * (tv[:-1] + tv[1:])

        hgt = np.empty(self.nz, dtype=float)

        # Determine pressure ordering
        if p[0] > p[-1]:
            # Standard bottom-up (surface p[0] down to space p[-1]):
            # p[:-1] > p[1:] => ln(p[:-1] / p[1:]) > 0 => dz > 0
            ratio = np.maximum(p[:-1] / np.maximum(p[1:], 1e-5), 1e-9)
            dz = (self.RD_J_KG_K * tv_mid / self.G0_M_S2) * np.log(ratio)
            hgt[0] = h0
            hgt[1:] = h0 + np.cumsum(dz)
        else:
            # Top-down (space p[0] up to surface p[-1]):
            # p[1:] > p[:-1] => ln(p[1:] / p[:-1]) > 0 => dz > 0
            ratio = np.maximum(p[1:] / np.maximum(p[:-1], 1e-5), 1e-9)
            dz = (self.RD_J_KG_K * tv_mid / self.G0_M_S2) * np.log(ratio)
            hgt[0] = h0
            hgt[1:] = h0 - np.cumsum(dz)

        return hgt
