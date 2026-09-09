import numpy as np

def compute_covariance(df_nominal, altitude_grid):
    """Placeholder for robust covariance computation."""
    # This would typically interface with MELCHIOR
    pass

def apply_eof_perturbation(nominal_profile, cov_matrix, rng, nz, num_members):
    """
    Applies EOF/PCA based perturbation to a nominal profile using a covariance matrix.
    """
    if cov_matrix is not None and cov_matrix.shape[0] == 4 * nz:
        eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
        eigenvalues[eigenvalues < 0] = 0
        
        u_nom = np.array(nominal_profile.get("u_wind", np.zeros(nz)))
        v_nom = np.array(nominal_profile.get("v_wind", np.zeros(nz)))
        t_nom = np.array(nominal_profile.get("temperature", np.full(nz, 280.0)))
        
        perturbations = []
        for _ in range(num_members):
            coeffs = rng.standard_normal(len(eigenvalues))
            perturbation = eigenvectors @ (np.sqrt(eigenvalues) * coeffs)
            u_m = u_nom + perturbation[0:nz]
            v_m = v_nom + perturbation[nz:2*nz]
            t_m = t_nom + perturbation[2*nz:3*nz]
            perturbations.append((u_m, v_m, t_m))
        return perturbations
    return None
