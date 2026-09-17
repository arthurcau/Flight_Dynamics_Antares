# Stochastic Analysis Audit — Neblina 1

**Audit scope:** repository state at the start of the multi-scenario stochastic
analysis extension.

**Reference entry point:**
`projects/neblina_1/simulations/run_all.py`

## Executive finding

The project already contains useful building blocks for RocketPy execution,
scalar `FlightMetrics`, Parquet storage, convergence, confidence intervals,
landing ellipses, sensitivity, and vector report output. The implementation is
not yet a complete paired multi-scenario campaign. The main gaps are
orchestration and traceability: the CLI loops over scenario names but the
campaign object is single-scenario, the nominal and failure Monte Carlo paths
are separate, shared sampled inputs are not injected into each scenario, and
the report discovers only a subset of the artifacts produced by the analysis
layer.

## Capability matrix

| Capability | State | Primary implementation | Artifact | Test coverage | Report use |
|---|---|---|---|---|---|
| Deterministic nominal flight | Implemented | `simulation/orchestrator.py`, `simulations/nominal.py` | RocketPy flight object; report metrics | Unit and integration builder tests | Implemented |
| Main at apogee deterministic case | Implemented as script override | `simulations/main_at_apogee.py` | Flight object only | No dedicated scenario regression | Partial |
| Only reefing deterministic case | Implemented as script override | `simulations/only_reefing.py` | Flight object only | No dedicated scenario regression | Partial |
| Ballistic/failure deterministic case | Implemented separately | `simulations/balistic.py`, `simulation/monte_carlo_failure.py` | Legacy text/JSON outputs | Partial integration coverage | Partial |
| Canonical scenario IDs | Partial | `simulation/campaign.py`, environment variables | Inconsistent labels and paths | No canonical registry test | Partial |
| RocketPy stochastic models | Implemented | `simulation/monte_carlo.py` | `mc_sim.*.txt` | Legacy integration tests | Partial |
| Shared input sampling | Partial | `simulation/uncertainty.py` | `samples/inputs.parquet` in canonical campaigns | Sampling unit tests | Not consistently consumed |
| Paired scenario realizations | Missing | `analysis/scenario_uq.py` only joins existing tables | No campaign-level paired artifact | Post-processing unit test only | Missing |
| Deterministic case seeds | Partial | `simulation/monte_carlo_failure.py` producer patch | Seed field in some artifacts | No serial/parallel equivalence test | Missing |
| Scenario-specific Monte Carlo | Partial | failure path plus scenario environment variable | Single scenario tables | No equivalent tests for all required scenarios | Partial |
| Resumable campaign | Partial | `simulation/uq_campaign.py`, failure path | Batch Parquet files | Batch storage test; no end-to-end resume proof | Partial |
| Compact scalar storage | Implemented in canonical path | `simulation/uq_storage.py`, `uq_pipeline.py` | Parquet statistics and outputs | Storage tests | Partial |
| Complete statistics | Partial | `analysis/uq.py`, `analysis/scenario_uq.py` | `statistics.parquet` | Synthetic statistics tests | Partial |
| Quantile confidence | Implemented | `analysis/uq.py` | `confidence.parquet` | Edge-case probability tests | Missing |
| Landing covariance ellipses | Implemented | `analysis/uq.py` | Embedded summary; no canonical `ellipses.parquet` | Chi-square unit test | Partial |
| Empirical spatial surface | Partial | `analysis/scenario_uq.py` | In-memory dictionary only | Missing | Missing |
| ECDF/distribution plots | Partial | `uq_pipeline.py`, legacy plotters | Limited PDF plot set | Missing vector-specific regression | Partial |
| Sensitivity | Partial | `analysis/uq.py` | `sensitivity.parquet` | Missing scenario comparison tests | Partial |
| Tail analysis | Partial | `analysis/uq.py` | `tail_analysis.parquet` | Synthetic tail test | Missing per-scenario integration |
| Requirement probability | Partial | `analysis/uq.py`, `analysis/compliance.py` | `compliance.parquet` in canonical path | Missing exact per-scenario matrix test | Partial |
| MAGI ensemble propagation | Partial | `environment/atmosphere.py`, sampling registry | Member ID can be sampled; full profiles are not injected per case | Missing | Partial |
| Vector engineering figures | Partial | `reporting/theme.py`, `uq_pipeline.py` | PDF figures in selected paths | Existing report QA is structural only | Partial |
| Report generation without physics rerun | Implemented for artifact mode | `reporting/pdf_report.py` | PDF | No full artifact-only regression | Implemented |
| Visual QA at rendered-page level | Partial | `reporting/qa.py` | Structural report manifest | Rasterizer detection only | Missing clipping/overlap detection |

## Source inspection results

### Nominal and deterministic scenarios

`execute_scenario` builds the environment, motor, vehicle, recovery system, and
flight from one `ProjectConfig`. The three required recovery cases are
currently implemented by mutating a loaded configuration in separate scripts.
That works for a one-off deterministic run, but it does not provide a typed
scenario definition or a shared override that can be reused by Monte Carlo,
metrics, paired comparisons, and the report.

### Existing Monte Carlo paths

`simulation/monte_carlo.py` uses RocketPy's `StochasticEnvironment`,
`StochasticSolidMotor`, `StochasticRocket`, and `StochasticFlight` directly.
It seeds global NumPy and Python random state and exports RocketPy text files.
It has no canonical scenario campaign object and no authoritative per-scenario
Parquet result set.

`simulation/monte_carlo_failure.py` adds a deterministic-seed producer and a
canonical post-processing path, but its failure implementation removes all
parachutes after a hard-coded 200 m descent point. That is a ballistic
continuation, not a general Main-at-Apogee or Only-Reefing implementation.
The two implementations therefore cannot be treated as interchangeable.

### Artifacts and report discovery

`MonteCarloCampaign` creates campaign metadata, configuration snapshots,
sample Parquet, batches, and canonical scalar tables. `finalize_campaign_analysis`
creates statistics, convergence, confidence, sensitivity, compliance, tail,
representative-case, and a small set of PDF plots.

The current report renderer reads a single campaign root. It does not yet
discover a `scenarios/<scenario_id>/` tree or paired-comparison artifacts, so a
CLI loop over scenarios cannot produce a complete comparable report.

### Requirements and MAGI

The requirements analysis and MAGI adapters exist, but they need to be wired
to the same canonical scenario summary. The current uncertainty registry uses
explicit means for the main physical quantities, which is correct for avoiding
silent inference, but the legacy `monte_carlo.yaml` and registry schemas still
coexist. Their semantics must be validated before an official campaign.

## Required implementation sequence

1. Add a typed canonical scenario registry and shared recovery overrides.
2. Add a `StochasticScenarioCampaign` that owns one immutable input table and
   one scenario campaign per configured scenario.
3. Make scenario execution use the same case IDs, seeds, and sample metadata,
   then persist paired deltas and comparability status.
4. Extend post-processing to emit per-scenario ellipses, empirical surfaces,
   ECDF-ready statistics, exact confidence, convergence, sensitivity, tails,
   requirements, and representative cases.
5. Update CLI and `run_all.py` so `--all-scenarios` is one campaign operation,
   not a sequence of unrelated campaigns.
6. Update report artifact discovery and visual QA only after canonical data are
   correct.

## Acceptance baseline

No official 10,000-case campaign should be declared statistically verified
until the following are true:

- the three required scenario IDs are present;
- the shared sample table is immutable and reused;
- valid and failed case counts are reported per scenario;
- paired comparison is either proven or explicitly marked unpaired;
- ascent consistency checks pass for identical post-ascent recovery failures;
- all mandatory metrics have scenario-specific convergence states;
- requirement probabilities include exact confidence bounds;
- report generation consumes artifacts without rerunning RocketPy or MAGI.

## Implementation update — 2026-09-17

The first implementation phase completed the shared campaign path. The
canonical scenario IDs are now `nominal`, `main_at_apogee`, and
`only_reefing`; one immutable `samples/inputs.parquet` is reused by the three
scenario directories; and paired deltas are written under
`paired_comparison/`. The scenario builders apply explicit recovery overrides
to deep copies of the project configuration, so deterministic and stochastic
execution use the same physical builder.

The scalar post-processing path now writes per-scenario statistics, exact
order-statistics quantile intervals, convergence checkpoints, sensitivity,
compliance, tails, representative cases, covariance ellipses, empirical
landing surfaces, ECDFs, applicability, and vector PDF figures. The report
renderer consumes these saved artifacts and records `physics_rerun: false`.

The hard-coded provenance claims in the original report were removed. Input
quality rows are derived from the YAML configuration and missing evidence is
reported as `UNKNOWN`; no instrument resolution is converted into an
uncertainty. Full configuration hashes are retained in campaign manifests.

A 50-case-per-scenario debug campaign completed with 150 trajectories, zero
failed cases, a shared seed/sample population, and a paired comparison of 50
case IDs. The generated report contained 18 pages and no structural blank
pages. Page rasterization was not completed in this environment because no
`pdftoppm`, `mutool`, Ghostscript, ImageMagick, or PyMuPDF renderer is
installed; the report manifest therefore correctly marks visual QA as
incomplete rather than claiming that clipping and overlap were inspected.

Remaining acceptance gaps are official 10,000–20,000-case execution,
scenario-specific convergence evidence at that scale, flight validation data,
and an official vector logo asset. The repository currently has an official
PNG logo only; the required asset and fallback behavior are documented in
`docs/REPORT_ASSET_REQUIREMENTS.md`.
