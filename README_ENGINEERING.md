# Antares Flight Dynamics — Engineering Hardening Log

This document summarizes the comprehensive restructuring and hardening of the Antares Flight Dynamics architecture on the `Experimental` branch. 

## 1. MAGI Integration (Phase B)
- **Strict Data Contract:** Added `AtmosphericProfile` in `source/antares_fd/environment/atmosphere.py`. Automatically validates profiles for missing data (NaN/Inf), strictly monotonic altitudes, and positive pressures/temperatures.
- **Single Source of Truth Adapter:** `MAGI/interface.py` now serves as the only bridge between the flight dynamics software and the meteorological system. 
- **Explicit Fallback:** Silently falling back to `standard_atmosphere` when MAGI fails is **disabled**. Simulation completely halts and throws an `AtmosphereUnavailableError` unless `fallback.enabled: true` is explicitly configured in `environment.yaml`.

## 2. Shared Monte Carlo Core (Phase C)
- **Engine Refactoring:** Replaced duplicate, project-level Monte Carlo loops with a unified, shared engine at `source/antares_fd/simulation/monte_carlo.py`.
- **Dynamic Configuration Mapping:** `monte_carlo.yaml` now directly injects uncertainties (standard deviations and factors) into RocketPy's native `StochasticEnvironment`, `StochasticSolidMotor`, `StochasticRocket`, and `StochasticFlight` classes.
- **Random Seed Control:** Enforces strict integer random seeds across `np.random` and `random` globally for reproducible dispersion fields.

## 3. Dispersion Analysis (Phase D)
- **Mathematical Integrity:** Replaced arbitrary radius calculations with rigorous bivariate normal covariance mathematics (`calculate_covariance_ellipse` in `source/antares_fd/simulation/statistics.py`).
- **Probability Containment:** Ellipses are generated using exact Chi-Square distribution critical values for 2 degrees of freedom (e.g. 50%, 90%, 95%, 99%).
- **Automated Plotting:** Generates `dispersion_plot_{run_id}.pdf` automatically containing scatter impacts and geometric ellipses with physical axes tracking.

## 4. Testing Structure (Phase E)
- **CI Readiness:** Test suite fully splits `tests/unit/` and `tests/integration/`. 
- **Mock Sandboxing:** Tests now utilize Pytest's `tmp_path` fixture to dynamically test YAML orchestration without polluting the repository with actual PDF/KML files.
- **Fail-Fast Validation Check:** Added `test_config.py` ensuring the orchestrator aggressively catches missing variables (like `vehicle.name` or `inertia`).

## 5. Traceability and Outputs (Phase F & G)
- **Isolated Artifacts:** Both Nominal and Monte Carlo simulations no longer dump PDF/KML files into the raw project root. All outputs are systematically placed in `results/<rocket>/<run_timestamp>_<rocket>_<scenario>/`.
- **Reproducibility Manifests:** Every simulation writes a `manifest.yaml` alongside the PDFs. It locks in:
  - Exact simulation timestamp (UTC)
  - Git commit hash
  - Git worktree dirtiness
  - Successful/Failed cases (for MC)
  - Random Seed (for MC)
- **CI Pipeline:** Added `.github/workflows/ci.yml` that checks out the repository, caches MAGI's offline data database, and strictly enforces the Pytest execution layer.

> *End of Engineering Hardening.*
