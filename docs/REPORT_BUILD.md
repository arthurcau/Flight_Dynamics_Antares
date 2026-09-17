# Automated report build

The renderer has two modes:

* A simulation campaign passes immutable `FlightMetrics` and writes the final
  vector report alongside its campaign artifacts.
* `antares-fd report <run_id> --project neblina_1` reads the existing
  `master_metrics.json` and canonical Parquet tables. It does not rerun
  RocketPy, MAGI, or Monte Carlo.

After generation, run:

Invoke `python -m antares_fd.reporting.qa <path-to-report.pdf> --figures
<campaign>/plots`. The QA
check records page count, required headings, blank-page state, vector figure
inventory, and whether page rasterization tools are available. PNG previews
are accepted only when a PDF sibling exists.

The nominal campaign entry point is `monte_carlo.py`. Files named
`monte_carlo_failure.py` are explicit failure-mode campaigns and are never
selected as nominal by filename ordering.
