"""Covariance validation shared by both synthetic-ensemble interfaces."""

import numpy as np


def covariance_factor(covariance, size):
    """Return L with L L.T = covariance, rejecting indefinite input.

    The eigensystem is evaluated in correlation coordinates, so roundoff
    tolerances do not compare humidity variance with wind variance in SI.
    Only eigenvalues within 1e-10 of zero (relative to the spectrum) may be
    rounded to zero. This is a numerical tolerance, not physical regularization.
    """
    cov = np.asarray(covariance, dtype=float)
    if cov.shape != (size, size) or not np.isfinite(cov).all():
        raise ValueError(f"Covariance must be a finite ({size}, {size}) matrix")
    variance = np.diag(cov)
    if np.any(variance < 0):
        raise ValueError("Covariance has negative variances")
    scale = np.sqrt(variance)
    active = scale > 0
    if np.any(cov[~active] != 0) or np.any(cov[:, ~active] != 0):
        raise ValueError("Zero-variance variables must have zero covariance")
    factor = np.zeros_like(cov)
    if not active.any():
        return factor
    corr = cov[np.ix_(active, active)] / np.outer(scale[active], scale[active])
    if not np.allclose(corr, corr.T, rtol=0, atol=1e-12):
        raise ValueError("Covariance must be symmetric")
    eigenvalues, eigenvectors = np.linalg.eigh((corr + corr.T) / 2)
    tolerance = 1e-10 * max(1.0, np.max(np.abs(eigenvalues)))
    if eigenvalues.min() < -tolerance:
        raise ValueError("Covariance is not positive semidefinite")
    factor[np.ix_(active, active)] = scale[active, None] * (eigenvectors * np.sqrt(np.maximum(eigenvalues, 0)))
    return factor
