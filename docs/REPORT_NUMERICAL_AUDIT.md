# Antares Flight Dynamics Numerical Audit

This audit records the numerical inconsistencies found before the report
renderer overhaul. Values below are from the archived campaign artifact
`results/neblina_1/2026-09-17T050740Z_neblina_1_campaign` and the source files
listed in each row. Paths are repository relative so the report never exposes
the local Windows workspace.

| Displayed value | Expected/reference | Source function/data | Units | Root cause | Fix | Test |
|---|---|---|---|---|---|---|
| Nominal apogee 2605.1 | Nominal AGL 2605.1; ASL 3100.1 | `analysis.metrics.extract_flight_metrics`; `master_metrics.json` | m | Correct nominal extraction, but MC canonicalizer copied RocketPy ASL `apogee` into `apogee_agl`. | `_output_frame` preserves ASL and subtracts each case elevation. | UQ pipeline regression covers ASL-to-AGL conversion. |
| MC P50 apogee 3096.2 | Comparable AGL near nominal, subject to declared uncertainty | `simulation.uq_pipeline._output_frame`; `outputs.parquet` | m | The archived outputs were built from a campaign whose `apogee` was ASL, then labeled AGL. | Canonical AGL derivation from case elevation; new reports label both references. | `test_output_frame_converts_asl_to_agl`. |
| Nominal rail exit 26.37 vs MC 56.9 | Same ascent vehicle/model until any failure event | `simulation.campaign.run_project_campaign`; `simulation.monte_carlo_failure.execute_monte_carlo` | m/s | The archived runner selected the failure implementation, whose old path changed the returned trajectory to ballistic descent after 200 m AGL and patched only selected fields. | The project entry point now uses the shared canonical runner with explicit scenario IDs; only the `ballistic` override uses the ballistic continuation. | `test_campaign_prefers_nominal_monte_carlo`; scenario campaign integration. |
| MC touchdown -70.2 m/s | Touchdown speed is positive `abs(Vz)`; signed Vz remains separate | RocketPy export `impact_velocity`; `_output_frame` | m/s | Failure campaign exported signed vertical velocity and the report called it speed. | Preserve `touchdown_velocity_signed`; canonical `touchdown_velocity = abs(...)`. | `test_output_frame_normalizes_touchdown_speed`. |
| MC flight time ~72.9 s | Nominal recovery flight ~112.7 s | `monte_carlo_failure.py` ballistic continuation | s | Recovery was intentionally removed from the failure trajectory but the output was stored in the nominal campaign artifact. | Separate nominal and failure scenario IDs; no silent scenario substitution. The corrected nominal/main-at-apogee/only-reefing runner retains recovery objects. | Campaign selection regression. |
| `Initial T/W = 0.00` | `T/W at t=0` may be zero; ignition T/W is the useful launch metric | `analysis.metrics.extract_flight_metrics` | dimensionless | Thrust is zero at solver time zero before ignition. | Add `ignition_tw`, retain raw t=0 value, and label both. | `test_metrics_exposes_ignition_tw` (integration fixture). |
| `Max Total Acceleration = 12.5 g` from raw 12.5 | 12.5 g is the converted canonical value | `analysis.metrics`; report tables | m/s² vs g | The canonical metric already converts by `g0`; the old table was ambiguous rather than physically wrong. | Unit-bearing labels and SI-to-display conversion rules are centralized. | Table/report QA. |
| `vehicle_mass` / `site_elevation` warnings | Vehicle dry mass nominal 21.186 kg; site elevation nominal 495 m | `config/uncertainties.yaml`; `SamplingPlan` | kg, m | Registry pointers were `vehicle.mass` and `environment.elevation`, neither matches the project schema; normal distributions had no declared mean. | Correct pointers and declare explicit means; no inference from a missing path. | `test_sampling_plan_declared_nominals`. |
| `max AoA ~60.8 deg` while AoA at Max-Q ~0 deg | Report raw and valid-window maxima separately | `analysis.metrics` | deg | Raw post-rail extraction included low-speed recovery/apogee transition values outside the aerodynamic analysis window. | Configured window: rail exit to apogee, minimum Q and speed floors; report the window and both values. | Metrics window regression. |

The archived campaign is therefore classified as a failure-mode/ASL-labeling
artifact and is not directly comparable with the nominal deterministic result.
The corrected renderer exposes that state instead of hiding it with visual
polish. Existing archived physics are not silently rewritten; a new campaign
is required to regenerate corrected stochastic outputs.
