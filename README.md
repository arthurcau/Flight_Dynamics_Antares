# Antares Flight Dynamics

Welcome to the canonical repository for **Antares Rocket Design Team** flight simulation work. 

This repository is built using **Python and RocketPy**. It is designed to support multiple rockets concurrently, sharing common simulation code and tests while keeping physical rocket parameters strictly separate in configuration files.

---

## 🏗️ Repository Architecture

The repository is structured to separate *software logic* from *physical engineering data*:

* **`Source/`**: Contains `antares_fd`, the core reusable software package. It answers: *"How do we simulate?"* (Builders, numerical solvers, results processing).
* **`Projects/`**: Contains rocket-specific data. It answers: *"What are we simulating?"* (YAML configurations, aerodynamic tables, and motor files for specific rockets like `Neblina_1` or `Andorinha`).
* **`Tests/`**: Contains verification code to ensure the software behaves correctly (unit tests, physical sanity tests, and regression tests).
* **`Docs/`**: Engineering and software documentation explaining why the software is designed this way.
* **`Scripts/`**: Miscellaneous utilities and execution scripts.
* **`MAGI/`**: Specialized tooling/submodules.

---

## 🚀 How to Create a New Rocket Project

Do not duplicate the core simulation engine!

To start simulating a new rocket:
1. Copy the canonical template directory `Projects/00_Copy_This/` and rename it to your new rocket's name (e.g., `Projects/My_Rocket/`).
2. Update the YAML files inside `Projects/My_Rocket/config/` (`vehicle.yaml`, `recovery.yaml`, `launch.yaml`, etc.) with your specific engineering data.
3. Run the thin entry point `Projects/My_Rocket/simulations/nominal.py`. The script will automatically load your configuration and orchestrate the flight simulation using the shared `antares_fd` core package.

---

## ⚙️ Engineering Principles & Rules

### 1. Configuration Philosophy
Physical parameters **must** live in YAML configuration files, never hard-coded in Python scripts. If an engineering value has not yet been defined by the team, use `null` rather than inventing an arbitrary value. The software is designed to fail fast and explicitly tell you what is missing.

### 2. SI Units Policy
The canonical internal unit system is **SI**:
* **length**: `m`
* **mass**: `kg`
* **time**: `s`
* **velocity**: `m/s`
* **force**: `N`
* **pressure**: `Pa`
* **angle**: `deg` (or explicitly `rad`)

Do not silently mix units.

### 3. Coordinate Convention
The canonical longitudinal coordinate convention is **nose-to-tail**:
```text
Nose tip
 x = 0
   |
   | +x
   v
 Tail
```
Therefore, $x$ increases from the nose to the tail. This applies to the center of gravity, center of pressure, fin positions, and motor mounts.

### 4. No Silent Failures
The simulation follows a strict "fail-fast" principle. If a configuration is missing, out-of-bounds, or physically impossible, the simulation will raise an explicit error rather than silently continuing with incorrect data. A successful simulation run does not automatically mean the simulation is physically correct—it still requires rigorous engineering review.

---

## 🛠️ Development & Testing

We use `pytest` for automated verification. To run the tests, execute:
```bash
PYTHONPATH=Source python3 -m pytest Tests/
```

* **Unit Tests**: Verify the logic of the `antares_fd` components.
* **Sanity Tests**: Check for physically impossible scenarios (e.g., negative mass, drogue deploying before launch).
* **Regression Tests**: Track software changes against frozen baseline outputs.
