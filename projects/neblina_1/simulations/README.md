# Neblina 1 simulation entry points

These files are launchers and small project-specific tools. They locate the
Neblina 1 project, load its YAML configuration, and call shared implementation
in `source/antares_fd/simulation`. Keep vehicle-building and campaign logic in
that package so individual project scripts do not drift apart.

## Files

| File | What it runs | Notes |
| --- | --- | --- |
| `nominal.py` | The configured nominal flight. | Calls `execute_scenario` with the default `nominal` scenario. |
| `balistic.py` | Ballistic descent with recovery disabled. | The historical filename is misspelled; the campaign maps it to scenario ID `ballistic`. |
| `main_at_apogee.py` | Main parachute at apogee. | Scenario overrides live in `simulation/scenarios.py`. |
| `only_reefing.py` | Reefed stage followed by the configured main stage. | The reefing fraction comes from `config/recovery.yaml`. |
| `monte_carlo.py` | Stochastic flight cases. | Calls the shared failure-aware runner; `ANTARES_MC_SCENARIO` selects the configured scenario. |
| `monte_carlo_failure.py` | Stochastic flight cases. | Also calls the shared failure-aware runner; retained as a direct failure-campaign launcher. |
| `run_all.py` | One consolidated project campaign. | The campaign runner selects declared entry points and writes a shared results directory. |
| `plot_flight_data.py` | Plots the raw telemetry log. | Uses acquisition order and clock segments; it does not simulate a flight or edit the source log. |

The campaign runner does not execute every Python file in this directory. It
selects the declared deterministic entry points and at most one Monte Carlo
launcher. The plotting utility is not a flight case. The former separation
example was removed because it used an assumed mass change before launch.
See `source/antares_fd/simulation/campaign.py` for the exact
selection list and execution order.

## Running a script

Run commands from the repository root so project inputs and generated results
resolve consistently:

```bash
PYTHONPATH=source:. .venv/bin/python projects/neblina_1/simulations/nominal.py
PYTHONPATH=source:. .venv/bin/python projects/neblina_1/simulations/main_at_apogee.py
PYTHONPATH=source:. .venv/bin/python projects/neblina_1/simulations/only_reefing.py
PYTHONPATH=source:. .venv/bin/python projects/neblina_1/simulations/balistic.py
PYTHONPATH=source:. .venv/bin/python projects/neblina_1/simulations/monte_carlo.py
PYTHONPATH=source:. .venv/bin/python projects/neblina_1/simulations/run_all.py
```

To select a stochastic scenario explicitly, set `ANTARES_MC_SCENARIO` to a
registered ID such as `nominal`, `main_at_apogee`, `only_reefing`, `ballistic`,
or `drogue_only`. The shared runner validates the name. `run_all.py` is the
entry point for consolidated reporting; individual scripts may produce their
own run artifacts under the ignored `results/` tree.

The telemetry plotter defaults to the ignored raw log path and creates a new
PDF under `results/neblina_1/`:

```bash
PYTHONPATH=source:. .venv/bin/python projects/neblina_1/simulations/plot_flight_data.py --help
```

Do not place plots or processed telemetry beside or over the raw source file.

Review notes and explanatory docstrings in this directory were written by Cau.
