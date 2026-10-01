# Neblina 1 project files

This folder contains the Neblina 1 vehicle inputs and the project-specific
entry points used by the shared `antares_fd` package. The YAML and data files
describe the **current model**; their presence alone does not establish that
they are the frozen preflight inputs or the as-flown configuration.

| Folder | Purpose | Guide |
| --- | --- | --- |
| `config/` | Launch, vehicle, motor, recovery, requirements, atmosphere, and uncertainty inputs. | [`config/README.md`](config/README.md) |
| `aero/` | Mach-dependent power-on and power-off drag tables. | [`aero/README.md`](aero/README.md) |
| `motors/` | RASP `.eng` thrust files. | [`motors/README.md`](motors/README.md) |
| `simulations/` | Small executable adapters and raw-flight plotting utility. | [`simulations/README.md`](simulations/README.md) |
| `telemetry/` | Dataset metadata and the raw-data audit contract. | [`telemetry/README.md`](telemetry/README.md) |
| `reconstruction/` | Model-variant status, reconstruction guidance, and Neblina 2 heritage. | [`reconstruction/README.md`](reconstruction/README.md) |

The reusable RocketPy builders, scenario definitions, campaign lifecycle,
Monte Carlo processing, and reporting code live in `source/antares_fd/`.
Project scripts should stay thin and pass the selected project configuration
to those shared functions.

The analysis notes and directory guides were reviewed and documented by Cau.
