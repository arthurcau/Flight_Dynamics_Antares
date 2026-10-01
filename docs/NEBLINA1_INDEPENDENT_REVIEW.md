# Neblina 1 reconstruction independent review

Review date: 2026-09-27  
Scope: telemetry integrity and event semantics, RocketPy replay and atmosphere
inputs, aerodynamic observability, Monte Carlo provenance and lifecycle,
results-path safety, packaging, tests, and performance claims.

## Findings

| Severity | Finding | Disposition |
| --- | --- | --- |
| CRITICAL | None found. | No unresolved critical item. |
| MAJOR | Earlier Monte Carlo manifests did not hash the dirty worktree or snapshot referenced thrust/Cd files. | Fixed by reusing the project model-input collector and worktree fingerprint; focused tests verify both. |
| MAJOR | Raw campaign/project IDs and symlinks could direct archive or resume operations outside `results/`. | Fixed with component validation, resolved containment checks, symlink rejection, and CLI guards. |
| MAJOR | Missing or corrupt campaign manifests could be rewritten as `COMPLETE`; corrupt batch data could be silently skipped. | Fixed: archiving requires a recognized terminal state and resume raises on unreadable batches; failure/partial status remains intact. |
| MINOR | Campaign ZIP creation could overwrite an existing archive or target its own source tree. | Fixed by exclusive creation, destination containment, and source-tree exclusion. |
| MINOR | Wheel metadata does not declare runtime dependencies. | Documented: wheel users must separately install the repository `requirements.txt`. |
| MINOR | Monte Carlo JSONL consumers could silently omit malformed/non-finite values; tables could substitute zero for absent metrics. | Fixed with one strict shared JSONL reader across resume, sensitivity, chart, table, and report paths. Errors include source lines; summaries expose per-metric N, reject non-scalar/overflowed values, and input/output pairing requires equal row counts. LaTeX and text fallback are tested. |
| MAJOR | Monte Carlo resume relied on row counts or index-base guesses and did not restore RocketPy's paired input/output logs and loaded-simulation counter consistently. | Fixed with shared `simulation/monte_carlo_resume.py`: canonical non-negative zero-based IDs, strict paired logs, gap/duplicate rejection, both log lists restored, and `num_of_loaded_sims` restored. Both nominal and failure entrypoints use the helper. The nominal path also avoids starting a campaign manager when every requested case is already present. |
| MAJOR | Invalid/all-null Monte Carlo metrics could produce misleading summaries or crash percentile reporting; sensitivity statistics could overflow or pair values from different valid rows. | Fixed with shared finite scalar validation and stable summary statistics, null summaries for zero valid observations, and pairwise finite-row sensitivity with reported sample counts. |
| MINOR | Sparse terminal failure outputs could be rejected as an invalid resume prefix before missing case IDs were reported as failures. | Fixed: terminal failure classification accepts sparse successes and reports the missing IDs; resume remains restricted to a contiguous prefix. |
| MINOR | The earlier v4 replay pair was described as matching the current worktree after a later test and documentation edit changed the snapshot. | Clarified: v4 remains a valid exact replay of its own recorded snapshot. A new final pair is generated below after the closing source, test, and documentation edits. |
| QUESTION | `1e-9` replay tolerance had no physical-accuracy basis. | Kept as a strict software-repeatability threshold and explicitly separated from telemetry/model accuracy. |

The follow-up independent Monte Carlo review found no unresolved CRITICAL or
MAJOR findings in the case-ID, resume, terminal-failure, or sensitivity fixes.
It initially noted that nominal `execute_monte_carlo` had no completed-archive
entrypoint test. `test_nominal_entrypoint_skips_workers_for_a_fully_restored_campaign`
now exercises that branch with RocketPy builders stubbed: it verifies restored
input/output records and count, proves simulation and manager startup are
skipped, and checks the completed manifest.

## Verification evidence

The final full repository test suite completed with **206 passed, 47 warnings,
and 4 subtests; no failures** in 63.43 seconds. The warnings remain visible,
including RocketPy and multiprocessing notices, numerical-library
deprecations, and the fixture's unstable-rocket warning. The focused nominal
resume tests completed with **7 passed**. `compileall` and `git diff --check`
also passed. The warnings were not suppressed or removed.

A final wheel was built and installed into a fresh temporary target. Imports
passed for Antares core, telemetry, validation, Monte Carlo resume, and both
supported MAGI package paths. The wheel still does not declare runtime
dependencies; wheel users must install the repository `requirements.txt`
separately.

## Reproducibility evidence

The final processing-v3 exact-worktree pair is
`results/neblina_1/current_model_reference_v5_final_20260927` and
`results/neblina_1/current_model_replay_v5_final_20260927`. It is generated
after the final source, test, and documentation edits in this review. The two
manifests record the same worktree snapshot; `replay_comparison.json` is the
machine-readable numerical authority. This checks software replay only and
does not validate the model against the flight. Earlier v3/v4 checkpoints are
historical snapshots, not fingerprints of the final reviewed worktree.

## Unresolved limitations

- Flight-derived apogee time, absolute altitude alignment, a measured velocity
  vector, and coast-phase Cd remain unobservable from the available sensors.
- Full stochastic replay is not established because case-specific MAGI
  atmosphere/member inputs are not yet archived with each Monte Carlo case.
- Live Open-Meteo fetch was not part of verification; the reference used the
  existing MAGI cache with network access explicitly disabled. The full
  RocketPy multiprocessing integration suite passed when run with the local
  manager socket permission required by its backend.

Independent review found no unresolved CRITICAL, MAJOR, MINOR, or QUESTION
items in the reviewed contracts after clarifying the earlier replay's snapshot
scope. The scientific validation status remains `NOT_YET_VALIDATED`.
