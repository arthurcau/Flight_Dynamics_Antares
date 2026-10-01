# Neblina 1 reconstruction performance profile

The telemetry audit and CLI import path were measured before and after the
targeted changes on the same checkout, interpreter, and ignored flight log.
These are end-to-end measurements from one machine, not CI thresholds or
portable guarantees.

| Workflow | Before | After | Change |
| --- | ---: | ---: | ---: |
| Real telemetry audit wall time | 19.71 s | 5.22 s | 73.5% lower |
| Real telemetry audit peak RSS | 767,096 KB | 614,988 KB | 19.8% lower |
| `antares_fd.cli` import wall time | 9.05 s | 0.24 s | 97.3% lower |
| `antares_fd.cli` import peak RSS | 222,088 KB | 12,444 KB | 94.4% lower |

The measured audit sequence identified two actual costs: iterating a
10,264-record pandas frame as row Series, and eagerly importing Monte Carlo
and RocketPy reporting components for a telemetry-only command. Positional
record iteration lowered the audit to 9.77 s / 631,756 KB. Sharing neutral
atomic storage primitives and lazy-loading command-specific modules lowered
the final audit to 5.22 s / 614,988 KB and the CLI import to 0.24 s / 12,444
KB. Five numeric Parquet outputs, the inventory and calibration JSON, and the
Markdown report were byte-for-byte or value-for-value equivalent across the
measured variants. The raw SHA-256 stayed unchanged. No solver tolerances or
trajectory equations were altered.

One offline reference/replay probe took 1.85 s and 1.86 s end to end on this
machine. RocketPy integration itself took 1.20 s and 1.12 s, as recorded in
the respective manifests. Each trajectory contained 550 samples; each MAGI
profile contained 601 altitude rows including specific humidity. The
reference and replay directories occupied 124,796 and 135,610 bytes. These
are single-run observations, not a benchmark distribution; peak RSS was not
measured for these two workflows. Replay did not reuse a live MAGI request.
The existing Monte Carlo profile and memory measurements remain in
[`MONTE_CARLO_PERFORMANCE_AUDIT.md`](MONTE_CARLO_PERFORMANCE_AUDIT.md);
they are not mixed with telemetry parser timings.

No performance change was made to numerical integration, filtering,
uncertainty sampling, or report plotting: no bottleneck or safe equivalence
case for those paths was established by this campaign. Performance numbers
should be re-measured on Neblina 2 hardware and representative campaign sizes.
