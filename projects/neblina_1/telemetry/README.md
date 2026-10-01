# Neblina 1 telemetry

The shared `antares_fd.telemetry` code audits telemetry logs; vehicle-specific
source paths and channel provenance live here. Raw files stay in the existing
ignored `data/flight_data/` location. Keep each original file byte-for-byte
unchanged and do not copy audit output over raw data. The tracked
`metadata/dataset.yaml` declares the local raw path, source header, channels,
units as documented by their labels, sensor identity limits, measurement
origin, calibration status, and known coordinate frames. The current
inventory also records the hashes of the pre-existing PDF and PNG plots as
related generated files; they are not parsed as telemetry inputs.
The `metadata/README.md` guide explains how to maintain that dataset contract.

Place additional original Neblina 1 flight files in `data/flight_data/`, then
update the tracked dataset metadata to reference them. The `data/` tree is
ignored by Git, so large or sensitive source data are not added to the
repository. The metadata and each audit manifest record SHA-256 checksums.
Share original files through the project's approved external storage and
verify their checksums against the manifest; do not substitute processed data
for the source file.

Run the audit from the repository root:

```bash
.venv/bin/python -m antares_fd.cli telemetry audit neblina_1
```

Or, when the console script is installed:

```bash
antares-fd telemetry audit neblina_1
```

The command writes a new run directory under
`results/neblina_1/<run-id>_telemetry_audit/`; it refuses to overwrite an
existing run directory. `--source` can point to a verified copy of the raw
log, and `--output` can select a different output directory.

Machine-readable artifacts are canonical:

- `telemetry_manifest.json`: input/config checksums, software and Git
  provenance, and checksums/schema for the generated artifacts.
- `telemetry_inventory.json`: input inventory, channel provenance, parser
  issues, GPS classification, timebase summary, and documented flag rules.
- `telemetry_samples.parquet`: long-form values, raw tokens, source line
  numbers, timestamps, channel provenance, and value status.
- `telemetry_segments.parquet`: one row per numeric record with
  `record_index`, `source_line_number`, `segment_id`, `raw_time`, and
  `segment_elapsed_s`. A segment begins when a finite clock reading decreases
  relative to the preceding finite reading, even across missing clock rows.
  No global corrected time is inferred, and a clock reset is not presumed.
- `sensor_calibration_manifest.json`: sensor and channel inventory with
  explicit `UNKNOWN` model, scale, offset, and hardware range where evidence
  is absent. A header unit label does not prove calibration.
- `channel_statistics.parquet`, `timebase_diagnostics.parquet`, and
  `sensor_quality_flags.parquet`: numeric summaries and explicit diagnostics.
- `telemetry_quality_report.md`: human-readable rendering from the canonical
  JSON and Parquet artifacts.

The audit never edits raw files or converts channel values, filters,
interpolates, synchronizes, or corrects timestamps. Time intervals remain in
the declared source unit; frequency is computed only when that unit has a
supported SI scale. A quality flag marks a data condition, not a physical
explanation. `MISSING_VALUES` marks explicit
blank/NaN tokens. `TIMESTAMP_GAP` uses a heuristic threshold above the modal
interval; `TIMESTAMP_BACKWARD_JUMP` and `NON_MONOTONIC_TIME` mark observed
decreases without assigning a cause, and
`DUPLICATE_TIMESTAMP` marks equal adjacent times. `POSSIBLE_SATURATION`
requires three adjacent samples repeating an observed extreme without claiming
a hardware limit; `STUCK_CHANNEL` identifies constant finite values without
concluding failure. `LARGE_DISCONTINUITY` marks adjacent changes above that
channel's 99.5th percentile of nonzero changes, excluding the time channel and
intervals across gaps, resets, or missing samples. `GPS_INVALID` means
coordinate channels are present but contain no in-range latitude/longitude
pair; `GPS_COORDINATE_PAIRS_INTERMITTENT` means some records have in-range
pairs and others do not. An in-range pair does not establish a GPS fix because
fix-quality data and the coordinate datum are not recorded.
`UNIT_UNKNOWN`, `UNIT_ASSUMED`, and `FRAME_UNKNOWN` preserve unresolved
metadata. `TIME_UNIT_UNSUPPORTED` means a declared clock unit cannot be
converted to seconds by the supported unit map, so frequency is left
uncomputed. Parser and numeric-token issues are separately flagged and
retained with source-line references in the inventory.

The inventory also records marked sections that exactly repeat an earlier
contiguous block of raw channel tokens. The present `DADOS DE VÔO` section is
an exact 86-row repeat of an earlier block. The audit retains both copies and
labels the mechanism unknown; it does not choose one as the flight. The
whole-file modal sample interval and gap count span multiple acquisition
regimes and are diagnostic only. Analyze rates within an appropriate segment
and scientifically justified flight window.

Future calibrated or aligned datasets should be written as separate derived
artifacts and retain the source SHA-256, channel lineage, conversion details,
and MEASURED / DERIVED / INFERRED status. Later analyses should load the
audited Parquet dataset and its metadata rather than editing or reparsing the
raw source ad hoc.

## Compare the retained flight trace with RocketPy

From the repository root, run:

```bash
.venv/bin/python projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py
```

The script verifies the raw log checksum but reads the audited samples,
duplicate mapping, saved current-reference trajectory, archived atmosphere,
and saved Monte Carlo case inputs/outputs for analysis. It writes a new
timestamped directory under `results/neblina_1/` and refuses to overwrite an
existing output directory. The script currently points to the audit,
reconstruction, model-reference, and Monte Carlo runs named in its constants;
change those inputs only when selecting a separately identified set of
artifacts.

The flight section is compared in source order. Gyroscope components are
plotted as raw header-labeled rates because sensor calibration, mounting, and
frame mapping are unknown; they do not constitute reconstructed attitude.
Altitude shape is shown relative to each trace's peak, with an explicit
warning that this does not validate event timing. Monte Carlo apogee is
recomputed using each case's realized RocketPy elevation. The archived MAGI
profile is a candidate model input, not observed launch weather; actual
weather correlation is unavailable without the actual launch time and a
measured trajectory reference.
