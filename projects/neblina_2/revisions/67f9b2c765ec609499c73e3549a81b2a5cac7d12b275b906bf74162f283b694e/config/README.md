# Neblina 1 configuration

The YAML files in this directory are the inputs loaded by `load_project_config`.
They describe the repository's current model. They are not a dated preflight
snapshot or a verified as-flown record unless their provenance says so.

| File | Owns |
| --- | --- |
| `launch.yaml` | Launch site, planned date/time, rail geometry, and initial conditions. |
| `environment.yaml` | MAGI target date/time, sampling window, and fallback policy. |
| `vehicle.yaml` | Geometry, reference quantities, mass properties, aerodynamic tables, and surfaces. |
| `motor.yaml` | Motor type, thrust-file path, grain and nozzle geometry, and motor mass properties. |
| `recovery.yaml` | Parachute devices, triggers, descent settings, and reefing configuration. |
| `monte_carlo.yaml` | Legacy Monte Carlo count, execution profile, and stochastic settings consumed by the direct RocketPy runner. |
| `uncertainties.yaml` | Provenance-aware uncertainty registry used to pre-generate cases for failure-aware campaigns. |
| `requirements.yaml` | Metric limits and requirement provenance used by requirement reporting. |

Deterministic scenarios apply named overrides to a copy of the loaded project
configuration in `source/antares_fd/simulation/scenarios.py`. The YAML files
remain the base inputs; a scenario does not rewrite them. Model-input snapshots
and hashes are recorded by the campaign/reference artifact code.

Uncertainty entries are not all measured distributions. Check each entry's
`provenance` before treating its bounds or spread as evidence. The Neblina 1
heritage review marks several existing values as legacy assumptions because
one flight cannot establish a population variance.

Configuration notes were reviewed and written by Cau.
