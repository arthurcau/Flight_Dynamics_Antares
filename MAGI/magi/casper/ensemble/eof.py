"""
EOF (Empirical Orthogonal Functions) and Principal Component Analysis for MAGI.

Provides spectral decomposition and perturbation routines for vertical atmospheric
state vectors: [u(z), v(z), T(z), q(z)]^T.
"""

from typing import Dict, List, Optional, Tuple, Union
import numpy as np


def compute_covariance(df_nominal, altitude_grid):
    """
    Interface hook for covariance computation.
    
    In the MAGI architecture, full climatological covariance estimation is performed
    by MELCHIOR using Ledoit-Wolf shrinkage.
    """
    try:
        from MAGI.melchior import Melchior
    except ImportError:
        from melchior import Melchior
    melchior = Melchior()
    return melchior.calculate_multivariate_covariance(df_nominal, altitude_grid)


def apply_eof_perturbation(
    nominal_profile: Dict[str, np.ndarray],
    cov_matrix: Optional[np.ndarray],
    rng: np.random.Generator,
    nz: int,
    num_members: int
) -> Optional[List[Tuple[np.ndarray, np.ndarray, np.ndarray, Optional[np.ndarray]]]]:
    """
    Apply EOF/PCA-based stochastic perturbations to a nominal vertical atmospheric profile.
    
    Perturbs state vector X = [u, v, T, q]^T (or [u, v, T]^T if 3-variable covariance is provided)
    using the spectral decomposition of the covariance matrix:
        Sigma = V * Lambda * V^T
        perturbation = V * sqrt(Lambda) * xi,  where xi ~ N(0, I)
    
    Parameters
    ----------
    nominal_profile : dict
        Dictionary containing baseline 1D profiles for keys:
        - "u_wind": Eastward wind component (m/s), shape (nz,)
        - "v_wind": Northward wind component (m/s), shape (nz,)
        - "temperature": Absolute air temperature (K), shape (nz,)
        - "specific_humidity": (Optional) Specific humidity (kg/kg), shape (nz,)
    cov_matrix : np.ndarray, optional
        Multivariate covariance matrix of shape (dim, dim), where dim >= 3 * nz.
        If dim >= 4 * nz, specific humidity perturbations are explicitly computed.
    rng : np.random.Generator
        NumPy random number generator for reproducible sampling.
    nz : int
        Number of vertical grid levels.
    num_members : int
        Number of perturbed ensemble members to generate.
        
    Returns
    -------
    list of tuple or None
        List of length `num_members`, where each entry is a tuple:
        (u_pert, v_pert, t_pert, q_pert) with shapes (nz,).
        If covariance is invalid or missing, returns None.
    """
    if cov_matrix is None or cov_matrix.shape[0] < 3 * nz:
        return None

    dim = cov_matrix.shape[0]
    has_moisture = (dim >= 4 * nz)

    # Enforce exact matrix symmetry before eigenvalue decomposition
    sym_cov = (cov_matrix + cov_matrix.T) / 2.0
    eigenvalues, eigenvectors = np.linalg.eigh(sym_cov)
    
    # Regularize eigenvalues (numerical jitter floor to prevent negative variances)
    eigenvalues = np.maximum(eigenvalues, 0.0)
    scale = np.sqrt(eigenvalues)

    u_nom = np.asarray(nominal_profile.get("u_wind", np.zeros(nz)), dtype=float)
    v_nom = np.asarray(nominal_profile.get("v_wind", np.zeros(nz)), dtype=float)
    t_nom = np.asarray(nominal_profile.get("temperature", np.full(nz, 280.0)), dtype=float)
    q_nom = np.asarray(nominal_profile.get("specific_humidity", np.zeros(nz)), dtype=float) if has_moisture else None

    # Sample standard normal coefficients: shape (dim, num_members)
    coeffs = rng.standard_normal((dim, num_members))
    perturbations = eigenvectors @ (scale[:, None] * coeffs)

    member_profiles = []
    for m in range(num_members):
        pert_m = perturbations[:, m]
        u_m = u_nom + pert_m[0:nz]
        v_m = v_nom + pert_m[nz:2 * nz]
        # Physically bound temperature to avoid unphysical absolute zero or negative temperatures
        t_m = np.maximum(t_nom + pert_m[2 * nz:3 * nz], 150.0)

        if has_moisture and q_nom is not None:
            # Specific humidity is bounded: non-negative and physically plausible (< 0.05 kg/kg)
            q_m = np.clip(q_nom + pert_m[3 * nz:4 * nz], 0.0, 0.05)
        else:
            q_m = None

        member_profiles.append((u_m, v_m, t_m, q_m))

    return member_profiles
