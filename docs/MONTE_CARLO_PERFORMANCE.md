# Monte Carlo performance

The campaign is memory bounded by compact scalar outputs, batch persistence
and the existing bounded trajectory retention used by legacy plots. Function
data is disabled for campaign execution. Dense landing scatter layers should
be rasterized when exported to vector documents.

The local benchmark is `tests/integration/benchmark_monte_carlo_memory.py`.
It reports simulation time, total time, process working set and the size of
RocketPy input/output logs. A production benchmark should record the same
values for 10, 50 and 100 cases and several worker counts before choosing a
worker default. Solver tolerances are not changed by the performance layer.

Canonical campaign artifacts are Parquet with Zstandard compression. Temporary
files are written beside their destination and atomically renamed after a
successful write. This makes completed batches safe to reuse after an
interruption.
