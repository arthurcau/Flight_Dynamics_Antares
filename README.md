<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/Antares_Logo_white.png">
    <source media="(prefers-color-scheme: light)" srcset="docs/Antares_Logo_black.png">
    <img alt="Antares Logo" src="docs/Antares_Logo_white.png">
  </picture>
</p>

<br>

[![Documentation Status](https://readthedocs.org/projects/rocketpyalpha/badge/?version=latest)](https://docs.rocketpy.org/en/latest/?badge=latest)
[![PyPI](https://img.shields.io/pypi/v/rocketpy.svg?color=g)](https://pypi.org/project/rocketpy/)
[![Conda Version](https://img.shields.io/conda/v/conda-forge/rocketpy.svg?color=g)](https://anaconda.org/conda-forge/rocketpy)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Contributors](https://img.shields.io/github/contributors/arthurcau/Flight_Dynamics_Antares.svg)](https://github.com/arthurcau/Flight_Dynamics_Antares/graphs/contributors)
[![Instagram](https://img.shields.io/badge/Instagram-E4405F?style=flat&logo=instagram&logoColor=white)](https://www.instagram.com/antaresunicamp)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/adm-foguetemodelismo-569a09294)

# Antares Flight Dynamics

Canonical repository for flight simulation and dynamics at the Antares Rocket Design Team.

**Primeiro acesso?** Leia o [onboarding em português](docs/ONBOARDING.md):
instalação, mapa dos arquivos, primeiro voo, campanhas, resultados e contribuição.

A versão 0.2 inclui uma **estação gráfica local**. Depois de instalar o ambiente:

```bash
antares-fd doctor
antares-fd gui
```

Na estação, crie projetos, registre componentes, importe OpenRocket com relatório
de cobertura, valide entradas, execute voos e consulte histórico e resultados.
Veja [o guia da GUI e da CLI](docs/GUI.md), [a manutenção](docs/MANUTENCAO.md),
[como contribuir](CONTRIBUTING.md) e [as responsabilidades de continuidade](MAINTAINERS.md).
O [Neblina 2](projects/neblina_2/README.md) está cadastrado como projeto preliminar,
aguardando o arquivo OpenRocket e os dados físicos ainda ausentes.

Antares Foguetemodelismo is an extracurricular program at the University of Campinas (Unicamp) dedicated
to competing in national and international aerospace challenges. Founded in 2014 within the School of Mechanical
Engineering (FEM), the team initially focused on national competitions. In 2017, the group underwent a strategic
transformation, refreshing its visual identity and shifting its focus toward high-performance rocketry. Composed of
a multidisciplinary body of undergraduate students, the group places a high priority on technical excellence through
scientific research and amateur rocket design in order to spark interest in the aerospace industry, and grow critical
interpersonal skills including teamwork, leadership, and project management in addition to technical engineering.

Built on Python and RocketPy. The architecture separates the simulation engine from rocket-specific data, allowing multiple vehicles to be simulated using the exact same validated code base.

## Architecture

- `source/`: Reusable software. Defines *how* we simulate. Contains the `antares_fd` core package (builders, solvers, utilities).
- `projects/`: Vehicle data. Defines *what* we simulate. Contains YAML configurations, aerodynamic tables, and motor files for specific rockets (e.g., `Neblina_1`, `Andorinha`).
- `tests/`: Software verification. Unit tests, physical sanity checks, and regressions.
- `docs/`: Technical documentation and engineering rationale.
- `scripts/`: Automation and execution utilities.
- `MAGI/`: Specialized tooling.

The [notebook and Python script catalog](docs/CATALOGO_NOTEBOOKS_E_SCRIPTS.md)
maps the historical notebooks to the current execution scripts, describes their
inputs and outputs, and records the differences found during the repository audit.

## Creating a New Rocket

> 💡 **Novo na equipe?** Comece pelo [guia de onboarding](docs/ONBOARDING.md)
> ou consulte o [roteiro rápido](docs/COMO_USAR.md).

Do not copy the simulation engine. To add a new vehicle:

1. Run `antares-fd project new My_Rocket --from 00_Copy_This`, or use the GUI.
2. Complete its engineering inputs and record their sources; retain unknown values as `null`.
3. Run `antares-fd validate My_Rocket` and resolve errors.
4. Run `antares-fd run My_Rocket --scenario nominal`.

The CLI and GUI freeze inputs before integrating. Existing project scripts remain
available for compatibility; new projects use the shared application services.

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
.venv/bin/python -m pytest tests/ MAGI/tests/
```

A [referência funcional](docs/referencia_funcoes/README.md) documenta as funções,
métodos e auxiliares locais do código de execução. O [relatório de revisão](docs/REVISAO_CODIGO_2026-11-16.md)
registra correções, exclusões, testes e a aplicação das diretrizes NASA/JPL.
