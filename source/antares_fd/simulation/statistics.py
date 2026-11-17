"""Statistical geometry helpers used by flight-dispersion plots."""

import numpy as np
from scipy.stats import chi2

def calculate_covariance_ellipse(x: np.ndarray, y: np.ndarray, probability: float):
    """
    Calculates a 2D probability containment ellipse for a given probability.
    Assumes a bivariate normal distribution.

    Args:
        x: Array of x coordinates (e.g. East).
        y: Array of y coordinates (e.g. North).
        probability: Desired containment probability (e.g. 0.95 for 95%).

    Returns:
        dict: Containing 'center' (x, y), 'width', 'height', 'angle' (in degrees),
              and the calculated 'chi2_val'.
    """
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if x.ndim != 1 or y.ndim != 1 or x.shape != y.shape or x.size < 2:
        raise ValueError("x and y must be arrays of equal length with at least 2 points.")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("Coordinates must contain only finite values.")

    if not (0 < probability < 1):
        raise ValueError("Probability must be between 0 and 1.")

    # Calculate covariance matrix
    coords = np.vstack((x, y))
    cov = np.cov(coords)
    mean_x = np.mean(x)
    mean_y = np.mean(y)

    # Eigenvalues and eigenvectors
    eigvals, eigvecs = np.linalg.eigh(cov)
    # A covariância amostral é semidefinida positiva. Arredondamentos podem
    # produzir autovalores negativos da ordem do erro de máquina em retas.
    tolerance = 16 * np.finfo(float).eps * max(1.0, float(np.max(np.abs(eigvals))))
    if eigvals.min() < -tolerance:
        raise ValueError("Coordinate covariance is not positive semidefinite.")
    eigvals = np.maximum(eigvals, 0.0)

    # Sort eigenvalues/vectors descending
    order = eigvals.argsort()[::-1]
    eigvals = eigvals[order]
    eigvecs = eigvecs[:, order]

    # Calculate chi-square quantile for 2 degrees of freedom
    # d^2 = chi^2_2(p)
    chi2_val = chi2.ppf(probability, 2)

    # Ellipse dimensions
    width = 2 * np.sqrt(chi2_val * eigvals[0])
    height = 2 * np.sqrt(chi2_val * eigvals[1])

    # Rotation angle
    angle = np.degrees(np.arctan2(eigvecs[1, 0], eigvecs[0, 0]))

    return {
        "center": (mean_x, mean_y),
        "width": width,
        "height": height,
        "angle": angle,
        "chi2_val": chi2_val
    }
