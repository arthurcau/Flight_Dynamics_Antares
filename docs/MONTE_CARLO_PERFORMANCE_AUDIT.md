# Monte Carlo performance audit

The repository already contains local measurements from the Neblina model.
They were taken on the configured Windows interpreter with six workers:

| run | cases | simulation time | total time | peak process tree | retained paths | input log |
|---|---:|---:|---:|---:|---:|---:|
| legacy baseline | 24 | 21.49 s | 23.98 s | 1854 MiB | 24 | 345.8 MB |
| compact executor | 24 | 15.27 s | 17.54 s | 1012 MiB | 6 | 90.8 kB |
| compact executor | 1500 | 180.80 s | 183.09 s | 1784 MiB | 9 | 5.7 MB |
| current verification | 12 | 22.72 s | 31.13 s | 993 MiB | 5 | 45.4 kB |

The compact path reduced the measured 24 case runtime by 27% and the peak
working set by 46%. It also reduced the input log by more than three orders of
magnitude. The 1,500 case run shows that process startup and RocketPy object
construction remain material costs; this is why worker reuse and immutable
worker initialization are the next profiling targets.

The benchmark script is
`tests/integration/benchmark_monte_carlo_memory.py`. It should be run locally
for N=10, 50 and 100 and worker counts 1, 2, 4 and the conservative automatic
limit before an official campaign. Wall clock thresholds are intentionally
not enforced in CI because hardware and atmospheric cache state vary.

No solver tolerance was relaxed. The current optimization removes redundant
function exports and full trajectory retention from the campaign path while
preserving scalar RocketPy outputs.
