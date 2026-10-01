# Shared flight simulation package

This package owns reusable RocketPy construction and execution logic. A
project's `simulations/*.py` files should load the project configuration and
select a scenario; they should not carry a second copy of vehicle builders or
campaign algorithms.

## Execution paths

For a deterministic flight, a project entry point calls
`simulation.orchestrator.execute_scenario`. The orchestrator applies a named
scenario to a deep copy of the configuration, builds the environment, motor,
vehicle, and recovery system, then delegates integration to `runner.run_flight`.
`results.print_flight_summary` handles the usual run outputs.

For a consolidated campaign, `campaign.run_project_campaign` selects only the
declared scripts, creates one results directory, runs deterministic cases,
then runs the selected Monte Carlo entry point. It restores campaign-related
environment variables when the campaign returns or raises.

The stochastic code has two entry paths. `monte_carlo.execute_monte_carlo`
adapts a configured RocketPy run and its paired JSONL case logs;
`monte_carlo_failure.execute_monte_carlo` first creates a stable sample table,
then records successes and failures against that same case population. The
project wrappers currently route to the failure-aware implementation. The
`case_ids` and `monte_carlo_resume` modules define the zero-based resume
contract; `monte_carlo_patch` adapts profile sampling and vehicle components
without changing RocketPy classes globally.

## Module map

| Module | Responsibility |
| --- | --- |
| `runner.py`, `orchestrator.py` | Translate simulation settings and run one scenario. |
| `scenarios.py` | Canonical scenario IDs and recovery overrides applied to config copies. |
| `campaign.py` | Entry-point selection, shared output directory, case ordering, and combined reporting. |
| `monte_carlo.py`, `monte_carlo_failure.py` | Direct stochastic run and failure-aware frozen-sample run. |
| `monte_carlo_parameters.py`, `monte_carlo_patch.py` | Convert distributions and adapt RocketPy stochastic objects. |
| `uncertainty.py`, `uq_campaign.py` | Parse uncertainty provenance, generate stable samples, and own resumable campaign artifacts. |
| `case_ids.py`, `monte_carlo_resume.py`, `monte_carlo_storage.py` | Validate case identity, restore JSONL logs, and bound retained trajectory data. |
| `uq_pipeline.py`, `uq_storage.py` | Validate campaign rows and write canonical statistics, sensitivity, and report artifacts. |
| `results.py`, `plotters.py`, `report.py` | Render per-flight and Monte Carlo summaries from saved outputs. |
| `statistics.py` | Small numerical helpers used by dispersion plots. |

The JSONL reader and atomic JSON/Parquet writers are shared from
`antares_fd.storage`; the package does not define a second parser or storage
implementation. Generated results belong under the repository's ignored
`results/` directory. A model run is not a telemetry validation unless an
independent comparison contract supplies aligned observations and matching
units and frames.

The code flow and annotations in this package were reviewed by Cau.
