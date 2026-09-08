# Antares Flight Dynamics

Canonical repository for flight simulation and dynamics at the Antares Rocket Design Team.

Built on Python and RocketPy. The architecture separates the simulation engine from rocket-specific data, allowing multiple vehicles to be simulated using the exact same validated code base.

## Architecture

- `Source/`: Reusable software. Defines *how* we simulate. Contains the `antares_fd` core package (builders, solvers, utilities).
- `Projects/`: Vehicle data. Defines *what* we simulate. Contains YAML configurations, aerodynamic tables, and motor files for specific rockets (e.g., `Neblina_1`, `Andorinha`).
- `Tests/`: Software verification. Unit tests, physical sanity checks, and regressions.
- `Docs/`: Technical documentation and engineering rationale.
- `Scripts/`: Automation and execution utilities.
- `MAGI/`: Specialized tooling.

## Creating a New Rocket

Do not copy the simulation engine. To add a new vehicle:

1. Copy the `Projects/00_Copy_This/` directory.
2. Rename it to your vehicle's name (e.g., `Projects/My_Rocket/`).
3. Replace the `null` values in `config/vehicle.yaml`, `recovery.yaml`, and `launch.yaml` with actual engineering data.
4. Run `simulations/nominal.py` to execute the flight.

## Engineering Rules

### 1. Configuration & Data
All physical parameters must reside in YAML files. Do not hard-code values in Python scripts. 

If a parameter is unknown, leave it as `null`. The software is designed to fail explicitly when required data is missing. Do not invent arbitrary physical values just to make the simulation run. 

### 2. Units
The internal standard is strictly SI.
- Length: `m`
- Mass: `kg`
- Time: `s`
- Velocity: `m/s`
- Force: `N`
- Pressure: `Pa`
- Angle: `deg` (or explicitly `rad`)

### 3. Coordinate System
The longitudinal axis is defined as nose-to-tail:
- `x = 0`: Nose tip
- `+x`: Points toward the tail

All longitudinal positions (CG, CP, fin placement, rail guides, motor mount) must follow this convention.

### 4. Software Verification
A simulation that finishes without crashing is not necessarily physically correct. 

The canonical model relies on both automated testing and engineering review. Do not suppress exceptions or ignore fail-fast checks.

## Tests

The repository uses `pytest`. Tests verify the shared `antares_fd` package and validate configurations.

```bash
PYTHONPATH=Source python3 -m pytest Tests/
```
