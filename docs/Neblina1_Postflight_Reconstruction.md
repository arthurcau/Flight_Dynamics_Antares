# Neblina 1 telemetry reconstruction: evidence and limits

Status: **PARTIAL**. This report records what the available source supports as
of 2026-09-27. It does not treat the current RocketPy run as a preflight
prediction or an as-flown validation.

## Evidence and provenance

The ignored raw source is `data/flight_data/Dados de Vôo Neblina - LASC
2026.log`, 1,206,765 bytes, SHA-256
`e516ee97fcf4c9a38ff25cd66f623a52e06b5132978da04719ad67e9752b098a`.
The audit checks the source hash before and after publication. All output is
written to new directories under ignored `results/neblina_1/`; the original
log remains byte-for-byte unchanged. Audit artifacts contain the source hash,
metadata hash, Git revision, software version, file-level output hashes, raw
tokens, acquisition-order record IDs, original source-line numbers, and a
content hash of the tracked diff plus nonignored untracked files used by the
processing worktree.

The log has 19 declared channels and 10,264 width-correct sample records.
Six post-header lines are not samples: three blank lines, two separators with
the wrong CSV width, and the `DADOS DE VÔO` section marker. They remain in the
inventory with source-line references. The 86 samples after that marker
(records 10178–10263, lines 10243–10328) match records 6412–6497 (lines
6471–6556) exactly across all 19 raw tokens, in the same order. Both blocks
remain in the audit. The duplication mechanism is **UNKNOWN**; these copies
are one recorded sequence, not two independent flights.

## Sensors and time

| Channel family | Recorded status | Interpretation limit |
| --- | --- | --- |
| Device clock | Finite values; four backward jumps | Clock origin, reset/rollover cause, and inter-segment gaps unknown. |
| BMP1/BMP2 | Onboard relative-altitude values in metres by header label | Raw pressure, conversion formula, reference pressure, calibration, and vertical datum absent. |
| MPU1/MPU2 | Accelerometer and gyro tokens with `g` and `deg/s` header labels | Model, scale/bias, mounting, axis transform, filtering and configured hardware ranges absent; repeated ±2 g values during ascent may be clipping. |
| GPS | Four fields present; zero finite coordinate pairs in 10,264 records | No onboard 3-D position or horizontal velocity. |
| Deployment/event | No direct event channel | Recovery and separation times cannot be directly recovered. |

The four backward jumps split the file-order stream into five clock segments
with 136, 66, 1,688, 8,034, and 340 records. The audit saves `raw_time`,
`segment_id`, and segment-local elapsed seconds, using the `time_ms` header
label for the seconds scale. It never sorts or joins segments into a global
clock. The reason for each jump remains unknown. The final marked flight block
lies entirely within segment 4 and spans 133.97 seconds of that counter.
This is a counter span under the header's millisecond label, not a verified
UTC duration.

The boot preamble names ESP-IDF 6.0.1 and has a compile timestamp on 2026-09-25.
That timestamp does not establish the actual flight date. The launch YAML's
2026-09-03 date is explicitly marked **planned**. Neither timestamp is silently
promoted to an as-flown launch record.

## Flight observations

The processed marked section keeps both BMP channels separate. There is no
filter, pressure inversion, corrected altitude, gyro integration, body/world
rotation, gravity subtraction, or 3-D position estimate. Interval vertical
rates are finite secants of onboard relative altitude over each recorded
sample interval, not instantaneous inertial velocity.

Both BMP channels reach their highest **recorded onboard relative altitude**
at record 10242, raw counter 849,710 ms, 26.86 seconds after the first marked
sample: BMP1 3,139.89 m; BMP2 3,144.27 m. This is a directly recorded
relative-altitude extremum, not an inferred physical apogee time. Physical
apogee time is **INSUFFICIENT_OBSERVABILITY** because the onboard conversion,
vertical reference, and sensor transient response are unknown. Within the
marked section, 75 of 85 inter-sample intervals exceed the audit's 270 ms gap
threshold (1.5 times its 180 ms modal interval); those intervals are retained
and flagged. The first post-peak BMP1 sample is 77.22 m lower after a counter
interval labeled 0.55 s; the corresponding secant is not instantaneous
vertical velocity. This abrupt change and the undocumented onboard conversion
limit physical interpretation. No ignition,
liftoff, rail exit, burnout, parachute deployment, or impact timestamp is
reported as observed. Initial marked powered samples repeatedly read −2 g on
both MPU y channels, so powered inertial acceleration is not reconstructed.

The GPS failure and unknown sensor orientation prevent defensible attitude,
world-frame acceleration, horizontal trajectory, and full 6-DOF state recovery.
The audit's calibration manifest records `UNKNOWN` rather than inventing
scale, bias, or range. A pressure-based altitude calculation is **NOT_APPLICABLE**
because pressure samples are absent.

## Model history and RocketPy

`projects/neblina_1/reconstruction/model_variants.yaml` separates the
partially reconstructed preflight model, as-flown model, postflight model,
and runnable **current reference**. The actual flight date and frozen
preflight input set are unverified; current YAML cannot be labeled historical
preflight. The as-flown vehicle mass, setup, motor identity, actual launch time,
and atmosphere are likewise unverified. No postflight parameter has been
identified or substituted into the original configuration.

The labeled current-model reference predicts 2,527.59 m AGL apogee at 23.185 s,
burnout at 6.586 s, rail exit at 0.781 s, maximum Mach 0.665, and maximum
dynamic pressure 28.09 kPa. The run archives all current YAML, motor, and Cd
input hashes, RocketPy 1.13.0, 550 simulated time samples, and the sampled MAGI
profile, including specific humidity for replaying the moist-air density
calculation. Its MAGI input is a cached historical forecast valid at 15:00 BRT on
the *planned* 2026-09-03 date, retrieved on 2026-09-20. The launch YAML time is
10:30 BRT, a 4.5-hour discrepancy. This atmosphere is not a verified actual-day
flight profile. The prior project-specific landing coordinates without
traceable evidence have been removed from `FlightMetrics`; ordinary reports
now label field validation unavailable until measured landing coordinates
with source, time, datum, and uncertainty are supplied.

The recorded BMP peak and the current-reference apogee differ in magnitude,
but they do not share a verified vertical datum, flight-time anchor, or
as-flown inputs. No time-resolved residual or predictive accuracy number is
published. Therefore **when divergence begins and which input dominates it
remain unresolved**. A residual API exists and requires an evidenced clock
anchor, matching units and frame, a single telemetry segment, and original
record IDs before interpolation is allowed.

The 2026-09-26 archived reference predates code-snapshot hashing. Its replay
cannot establish same-code reproducibility. The refreshed pre-v3 2026-09-27
run did have matching source/replay code fingerprints, but its archive omitted
specific humidity and therefore reconstructed the moist-air density as
independent sampled values. That replay remains a **numerical mismatch**, not a
validation result. The processing-v3 reference and replay checkpoints are
saved at `results/neblina_1/current_model_reference_v3_final` and
`results/neblina_1/current_model_replay_v3_final`. After the final report-parser
hardening and independent review, the exact-worktree verification pair is
saved at `results/neblina_1/current_model_reference_v3_reviewed_20260927` and
`results/neblina_1/current_model_replay_v3_reviewed_20260927`. These pairs
record the specific humidity input, matching source/replay worktree
fingerprints, common-time comparison and per-channel residuals. The artifact
`schema_version` remains 1; `v3` names the processing version. Replay uses
linear common-time alignment; its `1e-9` tolerance is a strict software
repeatability threshold, not a physical accuracy limit. The machine-readable
replay artifact is the authority for the final numerical status.

The final exact-current-worktree replay checkpoint is
`results/neblina_1/current_model_reference_v5_final_20260927` and
`results/neblina_1/current_model_replay_v5_final_20260927`. It was generated
after the final source, test, and documentation edits; the two manifests
record the same worktree fingerprint. Its `replay_comparison.json` is the
authority for numerical replay status. This confirms deterministic software
replay only, not agreement with telemetry or predictive accuracy. Earlier
v3/v4 pairs remain valid for their own recorded snapshots, but do not identify
the final reviewed worktree.

## Aerodynamics and uncertainty

The current power-on Cd table covers Mach 0–1.6 with Cd 0.45–0.70; power-off
covers Mach 0–1.6 with Cd 0.46–0.72. Both use linear interpolation and forbid
extrapolation. RocketPy uses a 0.156 m reference diameter, giving a circular
reference area of about 0.01911 m². The source and validation of both curves
are undocumented. No OpenRocket, RASAero, or CFD curve artifact was found in
the project. `antares_fd.reconstruction.aero` defines a source-tagged
`mach,Cd` import contract, checks monotonicity, reference area, power state,
geometry identity, and condition identity, and compares curves only over their
shared Mach domain. Flight-derived curves are excluded until an identification
and uncertainty contract exists. It generates no
external tool output.

Coast-phase Cd is **INSUFFICIENT_OBSERVABILITY**. Drag inversion needs a
defensible air-relative velocity vector (ground velocity minus wind), mass,
density, attitude or force direction, calibrated acceleration, and reference
area. Here GPS failed, actual-day wind is unavailable, MPU orientation and
calibration are unknown, and some ascent readings may clip. Producing a Cd
curve or uncertainty band would invent information. The same limitations
prevent attribution of the apparent apogee difference to drag, thrust, mass,
or weather.

The Monte Carlo `uncertainties.yaml` still labels the launch, drag, mass,
impulse and site-elevation distributions `LEGACY_ASSUMPTION`; this one flight
does not establish new Gaussian sigmas. The Neblina 2 heritage YAML records
what should be measured and how each quantity should be validated before
updating those distributions.

Monte Carlo campaign archives now snapshot every project YAML plus the
project-local thrust curve and file-backed power-on/power-off Cd curves, with
SHA-256 values in the manifest. They also record the shared dirty-worktree
fingerprint. New campaign IDs reserve unique result directories; archive,
resume and report paths are constrained to `results/`, symlink traversal and
archive overwrite are rejected, and failed/partial status is retained. These
changes do not yet prove full replay of every Monte Carlo atmosphere/member
input; do not claim a stochastic campaign is fully reproducible until its
case-specific MAGI inputs are also evidenced.

All Monte Carlo JSONL consumers now use the shared strict reader in
`antares_fd.storage`: malformed rows, non-object values and non-finite numbers
raise errors with the source line. Resume counts, sensitivity calculations,
tables, charts and reports no longer silently drop corrupt records. Summary
tables show per-metric valid sample counts; input/output row-count mismatches
fail before correlation analysis.

## Reproduce

Run from the repository root with the existing project environment:

```bash
sha256sum 'data/flight_data/Dados de Vôo Neblina - LASC 2026.log'
PYTHONPATH=source:. .venv/bin/python -m antares_fd.cli telemetry audit neblina_1
PYTHONPATH=source:. MPLCONFIGDIR=/tmp/antares-mpl .venv/bin/python -m antares_fd.cli telemetry process neblina_1 --audit results/neblina_1/<audit-directory>
sha256sum 'data/flight_data/Dados de Vôo Neblina - LASC 2026.log'
PYTHONPATH=source:. .venv/bin/python -m pytest -q tests/unit/test_telemetry.py tests/unit/test_observed_reconstruction.py tests/unit/test_validation_models.py tests/unit/test_validation_residuals.py
```

The first audit command prints its new directory; replace `<audit-directory>`
with that basename for the process command. It refuses existing output paths.
The model-reference and offline replay commands are in
`projects/neblina_1/reconstruction/README.md`. New analysis outputs carry
input/output hashes, worktree fingerprint, software versions, and methodology
version. The older 2026-09-26 reference has no worktree fingerprint, as noted
above. Offline replay uses only archived model inputs and atmosphere values; it
does not query MAGI. Wheel consumers must install `requirements.txt` separately
because the wheel's metadata currently declares no runtime dependencies.

## Status and required evidence

- Telemetry pipeline: **COMPLETE** for integrity audit; sensor calibration **BLOCKED_BY_MISSING_METADATA**.
- Flight reconstruction: **PARTIAL** for onboard relative altitude and its recorded extremum; physical apogee timing, attitude, and inertial state **INSUFFICIENT_OBSERVABILITY** or **BLOCKED_BY_MISSING_METADATA**.
- Preflight model: **PARTIALLY_RECONSTRUCTED_PREFLIGHT_MODEL**; as-flown model **BLOCKED_BY_MISSING_METADATA**.
- RocketPy validation: **NOT_YET_VALIDATED**; current configuration has a reference run only.
- Aerodynamic identification: **INSUFFICIENT_OBSERVABILITY**; external-curve comparison interface **COMPLETE**, external results absent.
- Neblina 2 heritage baseline: **COMPLETE** as a measurement and modeling plan, pending new evidence.

The minimum missing evidence for quantitative validation is a documented actual
launch date/time and event-clock anchor, archived preflight and as-flown inputs,
the onboard altitude conversion/reference, sensor model/calibration/mounting,
and actual-day atmosphere. Valid flight tracking or a separately measured
velocity/attitude solution is additionally needed for Cd identification.
