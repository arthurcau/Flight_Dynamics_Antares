# Neblina 1 model history and comparison boundary

`model_variants.yaml` is the authoritative status record for four distinct
models. The repository currently has no verifiable frozen preflight input set,
no verified as-flown input set, and no identified postflight parameter changes.
The runnable current YAML is therefore `NEBLINA1_CURRENT_MODEL_REFERENCE` only.
Its predictions cannot be reported as preflight accuracy or as-flown validation.

The current launch YAML calls its time **planned** (2026-09-03 10:30 BRT), while
the MAGI configuration requests 2026-09-03 15:00 BRT. The actual flight date,
launch time and weather remain unverified. Local Git history includes Neblina
configurations from September 8 onward, but without the actual flight date or
a dated preflight freeze it does not establish which inputs preceded flight.

`antares_fd.validation.reference.run_current_reference` snapshots the YAML,
motor and Cd files into a new output directory, runs the existing RocketPy
builders, and archives `simulated_timeseries.parquet`, the full sampled MAGI
`atmosphere_profile.parquet`, scalar `flight_metrics.json`, and a manifest with
hashes and software versions. The archive labels every result `MODELED` and
`REFERENCE_ONLY`. It excludes `FlightMetrics.validation`; the unsupported
project-specific landing coordinates were removed from the metrics extractor,
so reports show field validation as unavailable. It refuses to overwrite an
output directory or substitute standard atmosphere for MAGI.
The current processing version is `current-model-reference-v3`; the artifact
schema version remains `1`. Processing-v3 archives save the MAGI
specific-humidity input used by the moist-air density model. Replay rebuilds
the environment through the same profile builder, so derived density, sound
speed, and viscosity are not silently replaced with independent sampled
curves. Legacy moist-air archives without humidity retain their archived
derived curves and are marked as an approximate replay.

For a new current-reference run, this command prevents a live weather fetch.
It requires the matching existing MAGI cache entry; if absent, it fails:

```bash
PYTHONPATH=source:. MPLCONFIGDIR=/tmp/antares_mpl_reference .venv/bin/python - <<'PY'
from datetime import datetime, timezone
from pathlib import Path
import requests
from antares_fd.validation.models import load_model_variants
from antares_fd.validation.reference import run_current_reference

def offline(*args, **kwargs):
    raise OSError("Live weather fetch disabled")

requests.get = offline
project = Path("projects/neblina_1").resolve()
variant = load_model_variants(project / "reconstruction/model_variants.yaml")[
    "NEBLINA1_CURRENT_MODEL_REFERENCE"
]
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
print(run_current_reference(
    project, variant, Path("results/neblina_1") / f"{stamp}_current_model_reference"
))
PY
```

After a reference run exists, replay it without MAGI access using its immutable
input snapshot and archived atmospheric profile:

```bash
PYTHONPATH=source:. .venv/bin/python - <<'PY'
from datetime import datetime, timezone
from pathlib import Path
from antares_fd.validation.reference import replay_archived_reference

archive = Path("results/neblina_1/<reference-directory>")
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
print(replay_archived_reference(
    archive, Path("results/neblina_1") / f"{stamp}_current_model_replay"
))
PY
```

Replay verifies the original model-input and output hashes before it runs and
records whether the source and replay worktree fingerprints match. It compares
states at common physical times by linearly interpolating replay values onto
the source time grid inside the shared time interval; it does not extrapolate.
Atmosphere samples and scalar metrics are compared separately. The declared
`rtol=1e-9, atol=1e-9` is a strict software repeatability threshold, not a
physical model-accuracy or telemetry-uncertainty limit. A mismatch remains in
the artifact with per-channel maximum and RMS differences; it is never tuned
away. Older archives without a worktree fingerprint cannot establish same-code
replay. Generating a new reference still needs the matching MAGI cache or
another explicitly sourced profile.

The wheel packages both `MAGI.magi.*` and `magi.*` imports, but its current
metadata does not declare runtime dependencies. Install the repository's
`requirements.txt` separately when using the wheel outside the project
environment.

`antares_fd.validation.residuals.compare_time_series` is the comparison
contract. Callers must supply observed `record_index`, a single telemetry
`segment_id`, observed and simulated times, and an `Alignment` containing an
independently observed event, evidence, both event-clock times, and time
uncertainty. A `ComparisonBasis` must also establish equal units and coordinate
frames with evidence. It preserves missing observed values and forbids
interpolation between segments or beyond the simulated time range. No Neblina 1
residual has been generated from the present marked flight section because its
start is not an established ignition or first-motion time and the BMP channels'
vertical reference is unknown.

Canonical Monte Carlo artifacts use non-negative zero-based `case_id` values,
with any accompanying RocketPy `index` required to agree. The Antares serial
adapter converts RocketPy's incremented monitor count at export; stock
parallel logs carry the already-zero-based `index`, which the artifact
boundary promotes to `case_id`. Resume parses nonblank JSONL records strictly,
validates input and output IDs, and resumes only a contiguous completed prefix. Sparse IDs,
duplicate IDs, conflicting fields, malformed lines, and mismatched canonical
artifacts stop an append instead of being shifted or inferred from row counts.
Blank lines do not count as simulations. Older one-based serial logs need an
explicit migration before they can be resumed.
