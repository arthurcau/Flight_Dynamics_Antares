# Antares Flight Dynamics - System Context for AI Agents

**Identity & Role**
You are an AI programming assistant working on the canonical Flight Dynamics repository of the **Antares Rocket Design Team**.
Your primary goal is to maintain the integrity, safety, and architectural consistency of the simulation software.

## 1. Repository Architecture
The repository separates core logic from vehicle data:
* **`Source/antares_fd/`**: The core simulation engine. Contains reusable RocketPy wrappers, builders, and configuration loaders. Code here must be agnostic to any specific rocket.
* **`Projects/`**: Contains rocket-specific data (YAML files and thin entry-point scripts). Example: `Projects/Neblina_1/`. The directory `Projects/00_Copy_This/` is the canonical template for new rockets.
* **`Tests/`**: Automated verification using `pytest`. Tests the `Source` code and configuration schemas.

## 2. Hard Rules (DO NOT VIOLATE)

### Rule 1: No Hard-coded Physical Data
**Never** write physical parameters (mass, dimensions, Cd, etc.) directly into Python scripts like `nominal.py`. 
All physical parameters must live in the `config/*.yaml` files. The Python scripts should only load configurations and orchestrate the simulation.

### Rule 2: Do Not Invent Data
If an engineering parameter is unknown, leave it as `null` in the YAML file. 
**Never invent, extrapolate, or hallucinate physical values** just to make a script run. The software is explicitly designed to crash (`ConfigurationError`) when required data is missing. A silent failure or a simulation running on fake data is a critical safety violation.

### Rule 3: Coordinate System
The longitudinal axis is strictly **nose-to-tail**:
* `x = 0`: Nose tip.
* `x` increases towards the tail.
All variables (Center of Gravity, Center of Pressure, fins, rail guides) follow this exact reference frame. Do not introduce alternative coordinate origins.

### Rule 4: Unit System
Internal unit system is strictly **SI**:
* Length: `m`
* Mass: `kg`
* Time: `s`
* Velocity: `m/s`
* Force: `N`
* Pressure: `Pa`
* Angle: `deg` (or explicitly `rad` where noted)
Do not silently convert units. If conversion is necessary, it must be explicit and mathematically tested.

### Rule 5: Fail-Fast Philosophy
If a configuration is missing, out-of-bounds, or physically impossible, the simulation must raise an explicit exception (e.g., `ConfigurationError`). Do not suppress exceptions.

## 3. Workflow for New Rockets
When asked to set up a new rocket:
1. Copy the `Projects/00_Copy_This/` template.
2. Edit the YAML files with the user-provided data.
3. Run `simulations/nominal.py` to verify the execution pipeline.

## 4. Skills Directory
The `MAGI/skills/` directory contains specific scripts, rules, or prompt components designed to extend your capabilities within this repository. Consult those files if you need to perform specialized Antares tasks.
