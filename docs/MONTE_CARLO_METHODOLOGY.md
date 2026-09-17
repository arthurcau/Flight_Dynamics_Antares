# Antares Flight Dynamics - Monte Carlo Methodology

## 1. Introduction
This document describes the design philosophy and architecture of the Antares Flight Dynamics Monte Carlo uncertainty framework. The objective is to rigorously quantify unmodeled physical dispersions to provide actionable probabilistic guarantees for vehicle performance (e.g., apogee, kinetic energy limits, GPS landing drift).

The framework separates *aleatory* uncertainty (true physical variability, like motor thrust variance) from *epistemic* uncertainty (lack of knowledge, like disagreements between OpenRocket and CFD drag coefficients).

## 2. Core Principles
- **No Arbitrary Numbers:** Do not convert ±10% tolerances into standard deviations without measuring or justifying it. Unknown bounds must be explicitly labeled `LEGACY_ASSUMPTION` in their provenance metadata. 
- **Deterministic Sampling:** Random seeds alone are insufficient due to parallel execution and version upgrades. All configurations are pre-sampled into a discrete deterministic `scenarios.csv` table before dispatching to workers.
- **Correlated Flight Sampling:** We do not independently randomize `Cd_power_off` and `Cd_power_on`. They must be fundamentally linked through proper structural biases.
- **Native Atmospheric Ensemble:** Weather uncertainty uses explicit MAGI Native 3D Meteorological Ensemble Members (T, P, XYZ wind), not scalar noise factors multiplied on the nominal wind.

## 3. Propagation of Provenance
Every sampled parameter must be attached to an `UncertaintyRegistry` configuration containing:
- Current statistical implementation (Sigma, Uniform Bounds, Categorical).
- Required Units.
- Physical Metadata (`source`, `confidence`).
- Provenance Types (e.g. `DATA_SUPPORTED`, `LEGACY_ASSUMPTION`, `MEASURED`, `STATIC_FIRE`).

## 4. Convergence & Sensitivity 
The framework is equipped to progressively test batch convergence limits against standard tolerance intervals. Results should output Spearman rank charts determining the strongest sensitivity drivers natively against compliance requirements (e.g., Apogee margin, not just Apogee magnitude). 
Measurements will eventually overwrite all `LEGACY_ASSUMPTIONS`, progressively feeding flight telemetry to continuously calibrate the pipeline.

## 5. Canonical campaign artifacts

The implementation now freezes the input table at `samples/inputs.parquet`,
assigns a case-local `SeedSequence` seed, writes scalar result batches with
Zstandard compression and finalizes `statistics.parquet`,
`convergence.parquet`, `confidence.parquet`, `sensitivity.parquet`,
`compliance.parquet`, `representative_cases.parquet` and `summary.json`.
The report and future Award Brief render these artifacts rather than repeating
the statistical calculations. Missing scalar outputs are represented in
`failures.parquet`.

Official profiles use a 10,000 case minimum and a 20,000 case ceiling. At
least three recent configured checkpoints must satisfy each metric's tolerance
before the campaign is marked converged. A campaign that reaches its ceiling
without that evidence is explicitly marked `COMPLETE_NOT_CONVERGED`.
