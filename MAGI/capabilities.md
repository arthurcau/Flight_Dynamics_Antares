# MAGI Vertical Atmospheric Model
*(Formerly known as Neblina) - Stage 2 Architecture*

MAGI is an advanced atmospheric and thermodynamic modeling tool designed to provide highly accurate, altitude-dependent meteorological parameters and probabilistic uncertainty profiles for engineering, aerospace, and environmental applications.

MAGI is strictly divided into three complementary, independent Python subsystems. The Jupyter Notebook (`MAGI_App.ipynb`) serves only as an orchestration and visualization frontend. All internal atmospheric data traverses the subsystems mapped to a rigid universal schema (`MagiSchema`).

---

## 1. MELCHIOR-1 (Historical Climatology Subsystem)
*Module: `melchior.py`*

Processes long-term meteorological records, generates statistical distributions, and builds multivariable mathematical covariances of the atmosphere over time.

### Core Functions & Features:
- **Historical Data Fetching**: Retrieves local historical climate cache (or ERA5 reanalysis).
- **Statistical Profiles**: Calculates percentiles (10, 25, 75, 90), median, mean, and circular statistics for wind direction.
- **Multivariate Covariance & Shrinkage**: Extracts a unified state vector $\mathbf{x} = [u, v, T, q]^T$ for valid historical profiles. Applies Ledoit-Wolf Shrinkage regularization to compute a robust covariance matrix describing how orthogonal winds, temperature, and specific humidity physically correlate across all vertical altitudes.

---

## 2. BALTHASAR-2 (Operational Meteorological Data Subsystem)
*Module: `balthasar.py`*

Acquires and caches current deterministic forecasts, observation reports, and probabilistic ensembles.

### Core Functions & Features:
- **Cascading Ensemble Fetcher**: Dynamically checks Open-Meteo Ensemble API models (e.g., ECMWF IFS, GFS). Evaluates if the API provides a complete vertical state (pressure, temperature, orthogonal winds, humidity, geopotential height).
- **Deterministic Fallback**: If full ensemble vertical profiles are unavailable, the subsystem automatically falls back to a deterministic profile and flags the operational mode to trigger Synthetic Ensemble generation in CASPER.
- **Aviation Reports**: Integrates with AviationWeather APIs to pull real-time METAR and TAF reports for ground truth validation.

---

## 3. CASPER-3 (Atmospheric Synthesis and Validation Subsystem)
*Module: `casper.py`*

The physics engine. Interpolates profiles, verifies physical consistency, computes thermodynamics, and produces probabilistic synthetic members.

### Core Functions & Features:
- **Strict Interpolation & Boundaries**: Uses `PchipInterpolator` without extrapolation. Data requested beyond the forecast's vertical ceiling is strictly rejected (padded as `NaN` and flagged `OUT_OF_VERTICAL_RANGE`).
- **Surface Layer Scenarios**: Automatically models the boundary layer beneath the lowest available forecast using configurable roughness hypotheses (`OPEN_TERRAIN`, `VEGETATED_TERRAIN`, `ROUGH_RURAL`), scaling wind vectors via a neutral logarithmic profile.
- **Synthetic Ensembles (Karhunen-Loève)**: When deterministic profiles are passed (due to missing real ensembles), CASPER performs Eigendecomposition on MELCHIOR's multivariable covariance matrix. It injects Gaussian random coefficients to generate hundreds of physically realistic, vertically-correlated synthetic atmospheric profiles.
- **Hydrostatic Diagnostic**: Performs a rigorous layer-by-layer physics validation calculating the normalized residual $\varepsilon_h = \frac{| dp/dz + \rho g |}{\rho g}$. Throws warnings if hydrostatic failure limits are breached across consecutive layers.
- **Thermodynamic Re-derivation**: Calculates precise air density using virtual temperature and specific humidity, reconstructing dependents accurately after synthetic perturbations.

---

## Core Infrastructure
- **MagiSchema**: The rigorous, single internal data standard containing precisely tracked fields (`valid_time_utc`, `u_east_mps`, `v_north_mps`, `quality_flag`, `ensemble_member`, `generation_method`, etc.). All subsystems enforce this schema.
- **PyTest Integration**: Comprehensive unit tests covering vector ENU conversions, density physics, indexing, and end-to-end integration across subsystems.
