# Funções de projects

[Índice e convenções](README.md)

## `projects/00_Copy_This/simulations/balistic.py`

Run the canonical ballistic scenario using this project's YAML data.

### `main`

[Implementação: projects/00_Copy_This/simulations/balistic.py:12](../../projects/00_Copy_This/simulations/balistic.py#L12)

```python
main()
```

Execute o cenário balistic com a configuração do projeto.

Localiza o projeto por __file__, carrega YAMLs e chama o orquestrador
compartilhado. Retorna Flight e grava os artefatos previstos pelo executor;
não define constantes físicas adicionais neste ponto de entrada.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `execute_scenario(load_project_config(PROJECT_DIR), PROJECT_DIR, scenario_id='ballistic')`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `execute_scenario`
- `load_project_config`

## `projects/00_Copy_This/simulations/main_at_apogee.py`

Run the canonical main_at_apogee scenario using this project's YAML data.

### `main`

[Implementação: projects/00_Copy_This/simulations/main_at_apogee.py:12](../../projects/00_Copy_This/simulations/main_at_apogee.py#L12)

```python
main()
```

Execute o cenário main_at_apogee com a configuração do projeto.

Localiza o projeto por __file__, carrega YAMLs e chama o orquestrador
compartilhado. Retorna Flight e grava os artefatos previstos pelo executor;
não define constantes físicas adicionais neste ponto de entrada.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `execute_scenario(load_project_config(PROJECT_DIR), PROJECT_DIR, scenario_id='main_at_apogee')`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `execute_scenario`
- `load_project_config`

## `projects/00_Copy_This/simulations/monte_carlo.py`

Thin entry point for Monte Carlo Simulation.

### `main`

[Implementação: projects/00_Copy_This/simulations/monte_carlo.py:16](../../projects/00_Copy_This/simulations/monte_carlo.py#L16)

```python
main()
```

Execute a campanha Monte Carlo definida pelos YAMLs do projeto.

Carrega a configuração e delega ao executor compartilhado. A rotina gera
artefatos de campanha; erros de entrada e simulação são propagados.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `print`
- `load_project_config`
- `execute_monte_carlo`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

## `projects/00_Copy_This/simulations/nominal.py`

ANTARES FLIGHT DYNAMICS
Nominal Flight Simulation

### `main`

[Implementação: projects/00_Copy_This/simulations/nominal.py:17](../../projects/00_Copy_This/simulations/nominal.py#L17)

```python
main()
```

Execute o cenário nominal com a configuração do projeto.

Localiza o projeto por __file__, carrega YAMLs e chama o orquestrador
compartilhado. Retorna Flight e grava os artefatos previstos pelo executor;
não define constantes físicas adicionais neste ponto de entrada.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `flight`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `Path(__file__).resolve`
- `Path`
- `load_project_config`
- `execute_scenario`

## `projects/00_Copy_This/simulations/only_reefing.py`

Run the canonical only_reefing scenario using this project's YAML data.

### `main`

[Implementação: projects/00_Copy_This/simulations/only_reefing.py:12](../../projects/00_Copy_This/simulations/only_reefing.py#L12)

```python
main()
```

Execute o cenário only_reefing com a configuração do projeto.

Localiza o projeto por __file__, carrega YAMLs e chama o orquestrador
compartilhado. Retorna Flight e grava os artefatos previstos pelo executor;
não define constantes físicas adicionais neste ponto de entrada.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `execute_scenario(load_project_config(PROJECT_DIR), PROJECT_DIR, scenario_id='only_reefing')`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `execute_scenario`
- `load_project_config`

## `projects/00_Copy_This/simulations/run_all.py`

ANTARES FLIGHT DYNAMICS
Unified Campaign Runner - Template Project.

Executes all flight simulation scenarios in this folder (deterministic + Monte Carlo)
and generates a single, consolidated results directory with a single master engineering PDF report.

### `main`

[Implementação: projects/00_Copy_This/simulations/run_all.py:22](../../projects/00_Copy_This/simulations/run_all.py#L22)

```python
main()
```

Execute a campanha consolidada do projeto.

Delega ao controlador compartilhado a seleção dos cenários, organização
de resultados e geração de relatório. Os YAMLs fornecem os dados físicos.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `Path(__file__).resolve`
- `Path`
- `run_project_campaign`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

## `projects/andorinha/simulations/balistic.py`

Run the canonical ballistic scenario using this project's YAML data.

### `main`

[Implementação: projects/andorinha/simulations/balistic.py:12](../../projects/andorinha/simulations/balistic.py#L12)

```python
main()
```

Execute o cenário balistic com a configuração do projeto.

Localiza o projeto por __file__, carrega YAMLs e chama o orquestrador
compartilhado. Retorna Flight e grava os artefatos previstos pelo executor;
não define constantes físicas adicionais neste ponto de entrada.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `execute_scenario(load_project_config(PROJECT_DIR), PROJECT_DIR, scenario_id='ballistic')`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `execute_scenario`
- `load_project_config`

## `projects/andorinha/simulations/main_at_apogee.py`

Run the canonical main_at_apogee scenario using this project's YAML data.

### `main`

[Implementação: projects/andorinha/simulations/main_at_apogee.py:12](../../projects/andorinha/simulations/main_at_apogee.py#L12)

```python
main()
```

Execute o cenário main_at_apogee com a configuração do projeto.

Localiza o projeto por __file__, carrega YAMLs e chama o orquestrador
compartilhado. Retorna Flight e grava os artefatos previstos pelo executor;
não define constantes físicas adicionais neste ponto de entrada.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `execute_scenario(load_project_config(PROJECT_DIR), PROJECT_DIR, scenario_id='main_at_apogee')`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `execute_scenario`
- `load_project_config`

## `projects/andorinha/simulations/monte_carlo.py`

Thin entry point for Monte Carlo Simulation.

### `main`

[Implementação: projects/andorinha/simulations/monte_carlo.py:16](../../projects/andorinha/simulations/monte_carlo.py#L16)

```python
main()
```

Execute a campanha Monte Carlo definida pelos YAMLs do projeto.

Carrega a configuração e delega ao executor compartilhado. A rotina gera
artefatos de campanha; erros de entrada e simulação são propagados.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `print`
- `load_project_config`
- `execute_monte_carlo`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

## `projects/andorinha/simulations/nominal.py`

ANTARES FLIGHT DYNAMICS
Nominal Flight Simulation

### `main`

[Implementação: projects/andorinha/simulations/nominal.py:17](../../projects/andorinha/simulations/nominal.py#L17)

```python
main()
```

Execute o cenário nominal com a configuração do projeto.

Localiza o projeto por __file__, carrega YAMLs e chama o orquestrador
compartilhado. Retorna Flight e grava os artefatos previstos pelo executor;
não define constantes físicas adicionais neste ponto de entrada.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `flight`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `Path(__file__).resolve`
- `Path`
- `load_project_config`
- `execute_scenario`

## `projects/andorinha/simulations/only_reefing.py`

Run the canonical only_reefing scenario using this project's YAML data.

### `main`

[Implementação: projects/andorinha/simulations/only_reefing.py:12](../../projects/andorinha/simulations/only_reefing.py#L12)

```python
main()
```

Execute o cenário only_reefing com a configuração do projeto.

Localiza o projeto por __file__, carrega YAMLs e chama o orquestrador
compartilhado. Retorna Flight e grava os artefatos previstos pelo executor;
não define constantes físicas adicionais neste ponto de entrada.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `execute_scenario(load_project_config(PROJECT_DIR), PROJECT_DIR, scenario_id='only_reefing')`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `execute_scenario`
- `load_project_config`

## `projects/neblina_1/simulations/balistic.py`

Run the canonical ballistic scenario using this project's YAML data.

The filename keeps a historical misspelling; the campaign runner maps it to
the canonical ``ballistic`` scenario ID. Review notes by Cau.

### `main`

[Implementação: projects/neblina_1/simulations/balistic.py:16](../../projects/neblina_1/simulations/balistic.py#L16)

```python
main()
```

Load Neblina 1 inputs and run the ballistic scenario.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `execute_scenario(load_project_config(PROJECT_DIR), PROJECT_DIR, scenario_id='ballistic')`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `execute_scenario`
- `load_project_config`

## `projects/neblina_1/simulations/main_at_apogee.py`

Run the main-at-apogee recovery scenario from the project configuration.

The shared scenario registry disables the drogue and triggers the main at
apogee. Review notes by Cau.

### `main`

[Implementação: projects/neblina_1/simulations/main_at_apogee.py:16](../../projects/neblina_1/simulations/main_at_apogee.py#L16)

```python
main()
```

Load Neblina 1 inputs and run the main-at-apogee scenario.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `execute_scenario(load_project_config(PROJECT_DIR), PROJECT_DIR, scenario_id='main_at_apogee')`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `execute_scenario`
- `load_project_config`

## `projects/neblina_1/simulations/monte_carlo.py`

Launch the configured Neblina 1 Monte Carlo campaign.

The shared runner reads ``ANTARES_MC_SCENARIO`` (default: ``nominal``) and
owns sampling, resume checks, outputs, and reporting. Review notes by Cau.

### `main`

[Implementação: projects/neblina_1/simulations/monte_carlo.py:18](../../projects/neblina_1/simulations/monte_carlo.py#L18)

```python
main()
```

Load project YAML and hand the run to the shared Monte Carlo engine.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `print`
- `load_project_config`
- `execute_monte_carlo`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

## `projects/neblina_1/simulations/monte_carlo_failure.py`

Launch the failure-aware Monte Carlo engine for Neblina 1.

The scenario and sample policy come from shared Antares code and project YAML;
this file only resolves the project directory and starts that runner. Review
notes by Cau.

### `main`

[Implementação: projects/neblina_1/simulations/monte_carlo_failure.py:20](../../projects/neblina_1/simulations/monte_carlo_failure.py#L20)

```python
main()
```

Load the project configuration and execute its stochastic campaign.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `print`
- `load_project_config`
- `execute_monte_carlo`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

## `projects/neblina_1/simulations/nominal.py`

ANTARES FLIGHT DYNAMICS
Run Neblina 1's nominal flight configuration.

The shared orchestrator applies the nominal scenario to a copy of the loaded
configuration, builds the RocketPy objects, runs the flight, and writes the
standard results. Review notes by Cau.

### `main`

[Implementação: projects/neblina_1/simulations/nominal.py:23](../../projects/neblina_1/simulations/nominal.py#L23)

```python
main()
```

Build and run the nominal Neblina 1 flight, returning the RocketPy flight.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `flight`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `Path(__file__).resolve`
- `Path`
- `load_project_config`
- `execute_scenario`

## `projects/neblina_1/simulations/only_reefing.py`

Run the configured two-stage reefing recovery scenario.

The shared scenario registry uses a reduced-area reefed stage near apogee and
the configured main parachute for the later descent. Review notes by Cau.

### `main`

[Implementação: projects/neblina_1/simulations/only_reefing.py:16](../../projects/neblina_1/simulations/only_reefing.py#L16)

```python
main()
```

Load Neblina 1 inputs and run the only-reefing scenario.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `execute_scenario(load_project_config(PROJECT_DIR), PROJECT_DIR, scenario_id='only_reefing')`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `execute_scenario`
- `load_project_config`

## `projects/neblina_1/simulations/plot_flight_data.py`

Plot the raw Neblina flight telemetry log in acquisition order.

The log contains ESP32 boot messages before the CSV header.  This script finds
the header automatically, loads every telemetry column, and writes a PDF with
one overview page and one detailed page per sensor group.  Missing values are
kept as gaps in the curves instead of being interpolated.

Example:
    .venv/bin/python projects/neblina_1/simulations/plot_flight_data.py

Use ``--log`` and ``--output`` to plot a different log or choose a new PDF
destination. The horizontal axis is sample order because clock segments cannot
be stitched into one elapsed-time axis from the available evidence. Review
notes by Cau.

### `find_csv_header`

[Implementação: projects/neblina_1/simulations/plot_flight_data.py:115](../../projects/neblina_1/simulations/plot_flight_data.py#L115)

```python
find_csv_header(log_path: Path) -> int
```

Return the zero-based line number of the telemetry CSV header.

**Entradas e tipos declarados**

- `log_path: Path`

**Retornos/yields explícitos**

- `find_csv_header_line(log_path, header_channel='time_ms') - 1`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `find_csv_header_line`

### `load_telemetry`

[Implementação: projects/neblina_1/simulations/plot_flight_data.py:120](../../projects/neblina_1/simulations/plot_flight_data.py#L120)

```python
load_telemetry(log_path: Path) -> pd.DataFrame
```

Load the CSV portion of the raw log without dropping or reordering rows.

**Entradas e tipos declarados**

- `log_path: Path`

**Retornos/yields explícitos**

- `data`

**Exceções lançadas explicitamente**

- `ValueError("A coluna obrigatória 'time_ms' não foi encontrada.")`
- `ValueError(f'Nenhuma amostra numérica encontrada em: {log_path}')`

**Colaboradores chamados diretamente**

- `parse_telemetry_log`
- `parsed.to_wide_frame`
- `ValueError`
- `segment_timebase`
- `timebase['segment_id'].to_numpy`

### `_segments`

[Implementação: projects/neblina_1/simulations/plot_flight_data.py:142](../../projects/neblina_1/simulations/plot_flight_data.py#L142)

```python
_segments(data: pd.DataFrame) -> Iterable[tuple[int, pd.DataFrame]]
```

Yield each contiguous clock segment without joining reset boundaries.

**Entradas e tipos declarados**

- `data: pd.DataFrame`

**Retornos/yields explícitos**

- `(int(segment_id), segment_data)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `data.groupby`
- `int`

### `plot_group`

[Implementação: projects/neblina_1/simulations/plot_flight_data.py:148](../../projects/neblina_1/simulations/plot_flight_data.py#L148)

```python
plot_group(ax: plt.Axes, data: pd.DataFrame, columns: tuple[str, ...], ylabel: str) -> None
```

Plot one group of signals, preserving NaNs and counter resets.

**Entradas e tipos declarados**

- `ax: plt.Axes`
- `data: pd.DataFrame`
- `columns: tuple[str, ...]`
- `ylabel: str`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `plt.rcParams['axes.prop_cycle'].by_key`
- `enumerate`
- `len`
- `LINE_LABELS.get`
- `_segments`
- `values.notna().any`
- `values.notna`
- `ax.plot`
- `data['segment'].diff().fillna(0).gt`
- `data['segment'].diff().fillna`
- `data['segment'].diff`
- `ax.axvline`
- `ax.text`
- `ax.set_ylabel`
- `ax.grid`
- `ax.margins`
- `ax.get_legend_handles_labels`
- `ax.legend`
- `min`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `make_figure`

[Implementação: projects/neblina_1/simulations/plot_flight_data.py:220](../../projects/neblina_1/simulations/plot_flight_data.py#L220)

```python
make_figure(data: pd.DataFrame, *, overview: bool=False) -> plt.Figure
```

Build the overview or detailed figure.

**Entradas e tipos declarados**

- `data: pd.DataFrame`
- `overview: bool`

**Retornos/yields explícitos**

- `figure`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `len`
- `plt.subplots`
- `axes.ravel`
- `figure.suptitle`
- `zip`
- `plot_group`
- `axis.set_title`
- `axis.set_visible`
- `axis.set_xlabel`
- `figure.tight_layout`
- `axes_flat[0].set_xlabel`

### `write_plots`

[Implementação: projects/neblina_1/simulations/plot_flight_data.py:252](../../projects/neblina_1/simulations/plot_flight_data.py#L252)

```python
write_plots(data: pd.DataFrame, output_path: Path, *, source_path: Path, repo_root: Path | None=None) -> Path
```

Write new plot artifacts while guarding the immutable raw source.

**Entradas e tipos declarados**

- `data: pd.DataFrame`
- `output_path: Path`
- `source_path: Path`
- `repo_root: Path | None`

**Retornos/yields explícitos**

- `overview_path`

**Exceções lançadas explicitamente**

- `ValueError('Plot results directory must not be a symlink')`
- `ValueError('Plot artifacts must be written beneath the repository results/ directory')`
- `ValueError('Plot output cannot be the raw source')`
- `ValueError('Plot overview cannot be the raw source')`
- `FileExistsError('Plot artifact already exists; choose a new output path')`

**Colaboradores chamados diretamente**

- `Path(repo_root or PROJECT_ROOT).resolve`
- `Path`
- `results_root.is_symlink`
- `ValueError`
- `output_path.is_absolute`
- `output_path.resolve`
- `results_root.resolve`
- `output_path.is_relative_to`
- `source_path.resolve`
- `output_path.with_name`
- `overview_path.resolve`
- `output_path.exists`
- `overview_path.exists`
- `FileExistsError`
- `output_path.parent.mkdir`
- `PdfPages`
- `make_figure`
- `overview_figure.savefig`
- `pdf.savefig`
- `plt.close`
- `make_figure_for_group`

### `make_figure_for_group`

[Implementação: projects/neblina_1/simulations/plot_flight_data.py:296](../../projects/neblina_1/simulations/plot_flight_data.py#L296)

```python
make_figure_for_group(data: pd.DataFrame, group: tuple[str, tuple[str, ...], str, str]) -> plt.Figure
```

Build one detailed PDF page for a sensor group.

**Entradas e tipos declarados**

- `data: pd.DataFrame`
- `group: tuple[str, tuple[str, ...], str, str]`

**Retornos/yields explícitos**

- `figure`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `plt.subplots`
- `plot_group`
- `axis.set_title`
- `axis.set_xlabel`
- `figure.tight_layout`
- `figure.canvas.manager.set_window_title`

### `parse_args`

[Implementação: projects/neblina_1/simulations/plot_flight_data.py:312](../../projects/neblina_1/simulations/plot_flight_data.py#L312)

```python
parse_args() -> argparse.Namespace
```

Parse the optional raw-log and PDF destination paths.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `parser.parse_args()`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `argparse.ArgumentParser`
- `parser.add_argument`
- `parser.parse_args`

### `main`

[Implementação: projects/neblina_1/simulations/plot_flight_data.py:330](../../projects/neblina_1/simulations/plot_flight_data.py#L330)

```python
main() -> None
```

Load the raw log, preserve its segments, and write new plots.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `parse_args`
- `load_telemetry`
- `datetime.now(timezone.utc).strftime`
- `datetime.now`
- `write_plots`
- `int`
- `data['segment'].max`
- `print`
- `len`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

## `projects/neblina_1/simulations/run_all.py`

ANTARES FLIGHT DYNAMICS
Unified Campaign Runner - Neblina 1.

The shared campaign runner selects declared entry points, executes the
deterministic cases before Monte Carlo, and collects their artifacts under one
results directory. Review notes by Cau.

### `main`

[Implementação: projects/neblina_1/simulations/run_all.py:23](../../projects/neblina_1/simulations/run_all.py#L23)

```python
main()
```

Start one consolidated campaign for the Neblina 1 simulations folder.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `Path(__file__).resolve`
- `Path`
- `run_project_campaign`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

## `projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py`

Compare the retained Neblina 1 telemetry section with saved RocketPy runs.

The script reads the raw file only to verify its checksum. Analysis uses the
audited Parquet artifacts, preserves acquisition order, and writes new files
only under results/. It does not infer an absolute flight time or attitude.

Run from the repository root with:

    .venv/bin/python projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py

Review notes by Cau.

### `sha256_file`

[Implementação: projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py:55](../../projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py#L55)

```python
sha256_file(path: Path) -> str
```

Return a file digest without changing the source.

**Entradas e tipos declarados**

- `path: Path`

**Retornos/yields explícitos**

- `digest.hexdigest()`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `hashlib.sha256`
- `path.open`
- `iter`
- `digest.update`
- `digest.hexdigest`

### `_read_json`

[Implementação: projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py:64](../../projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py#L64)

```python
_read_json(path: Path) -> dict[str, Any]
```

Leia um documento JSON da evidência de comparação.

Desserializa path em UTF-8 e retorna o objeto. Erros de leitura ou sintaxe
são propagados para não aceitar artefatos de entrada inválidos.

**Entradas e tipos declarados**

- `path: Path`

**Retornos/yields explícitos**

- `value`

**Exceções lançadas explicitamente**

- `ValueError(f'Expected a JSON object in {path}')`

**Colaboradores chamados diretamente**

- `path.open`
- `json.load`
- `isinstance`
- `ValueError`

### `_load_primary_trace`

[Implementação: projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py:77](../../projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py#L77)

```python
_load_primary_trace() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]
```

Select the original records referenced by the exact repeated section.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `(primary, wide, {'raw_sha256_before': raw_hash_before, 'source_record_count': int(len(source_ids)), 'source_record_index_first': int(min(source_ids)), 'source_record_index_last': int(max(source_ids)), 'source_line_first': int(timestamps['source_line_number'].min()), 'source_line_last': int(timestamps['source_line_number'].max()), 'clock_segment_id': int(timestamps['segment_id'].iloc[0]), 'elapsed_from_first_sample_s': float(wide['block_elapsed_s'].iloc[-1]), 'median_sample_interval_s': float(wide['raw_time_ms'].diff().median() / 1000.0), 'maximum_sample_interval_s': float(wide['raw_time_ms'].diff().max() / 1000.0), 'intervals_over_2s': int((wide['raw_time_ms'].diff() > 2000).sum()), 'whole_dataset': {'declared_channel_count': int(len(inventory['header_channels'])), 'numeric_record_count': int(inventory['record_count']), 'parse_issue_count': int(inventory['parse_issue_count']), 'timestamp_backward_jump_count': int(inventory['timebase']['timestamp_backward_jump_count']), 'clock_segment_count': int(inventory['timebase']['segment_count']), 'gps_status': inventory['gps']['status'], 'gps_in_range_coordinate_pair_count': int(inventory['gps']['in_range_coordinate_pair_count'])}})`

**Exceções lançadas explicitamente**

- `ValueError('Raw telemetry checksum does not match its audit manifest')`
- `ValueError('Telemetry inventory was generated from a different raw source')`
- `ValueError(f'Audited input artifact checksum mismatch: {artifact_name}')`
- `ValueError('Observed-section artifact was derived from a different raw source')`
- `ValueError('Observed-section artifact references a different telemetry audit')`
- `ValueError('Observed-section duplicate mapping failed its recorded checksum')`
- `ValueError('Repeated-section provenance does not identify unique source records')`
- `ValueError('Audited samples do not point to the verified raw source')`
- `ValueError('Not all source records from the repeated section are available')`
- `ValueError(f'Required channel is absent from the audited section: {channel}')`
- `ValueError('Elapsed time conversion requires the documented ms header label')`
- `ValueError(f'Altitude plot requires the documented metre header label: {channel}')`
- `ValueError(f'Angular-rate plot requires the documented deg/s header label: {channel}')`
- `ValueError('The selected section has missing or duplicate clock records')`
- `ValueError('Selected section crosses clock segments; no elapsed-time axis is justified')`
- `ValueError('Selected section contains a backward clock jump')`

**Colaboradores chamados diretamente**

- `_read_json`
- `sha256_file`
- `ValueError`
- `inventory.get`
- `observed_manifest.get`
- `pd.read_parquet`
- `repeated['is_exact_duplicate_copy'].astype`
- `duplicate_rows['duplicate_of_record_index'].dropna().astype`
- `duplicate_rows['duplicate_of_record_index'].dropna`
- `len`
- `source_records.nunique`
- `set`
- `source_records.tolist`
- `long['source_sha256'].dropna().unique`
- `long['source_sha256'].dropna`
- `long.loc[long['record_index'].isin(source_ids)].copy`
- `long['record_index'].isin`
- `primary['record_index'].nunique`
- `primary.drop_duplicates('canonical_channel_name').set_index`
- `primary.drop_duplicates`
- `primary.loc[primary['canonical_channel_name'].eq('time_ms'), ['record_index', 'numeric_value', 'source_line_number']].drop_duplicates('record_index').merge(segments[['record_index', 'segment_id', 'raw_time']], on='record_index', how='left', validate='one_to_one').sort_values`
- `primary.loc[primary['canonical_channel_name'].eq('time_ms'), ['record_index', 'numeric_value', 'source_line_number']].drop_duplicates('record_index').merge`
- `primary.loc[primary['canonical_channel_name'].eq('time_ms'), ['record_index', 'numeric_value', 'source_line_number']].drop_duplicates`
- `primary['canonical_channel_name'].eq`
- `timestamps['segment_id'].nunique`
- `timestamps['numeric_value'].diff().dropna().lt(0).any`
- `timestamps['numeric_value'].diff().dropna().lt`
- `timestamps['numeric_value'].diff().dropna`
- `timestamps['numeric_value'].diff`
- `primary.merge`
- `timestamps.set_index`
- `primary['record_index'].map`
- `float`
- `primary.sort_values`
- `primary.pivot(index='record_index', columns='canonical_channel_name', values='numeric_value').sort_index`
- `primary.pivot`
- `timestamps.set_index('record_index').rename`
- `record_metadata.join`
- `wide.reset_index`
- `int`
- `min`
- `max`
- `timestamps['source_line_number'].min`
- `timestamps['source_line_number'].max`
- `wide['raw_time_ms'].diff().median`
- `wide['raw_time_ms'].diff`
- `wide['raw_time_ms'].diff().max`
- `(wide['raw_time_ms'].diff() > 2000).sum`

### `_gyro_summary`

[Implementação: projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py:184](../../projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py#L184)

```python
_gyro_summary(wide: pd.DataFrame) -> dict[str, dict[str, Any]]
```

Resuma as velocidades angulares registradas sem inferir orientação.

Seleciona canais de giroscópio em wide e calcula estatísticas finitas
por sensor. A saída é diagnóstico do registro, sem integração em atitude.

**Entradas e tipos declarados**

- `wide: pd.DataFrame`

**Retornos/yields explícitos**

- `summary`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `pd.to_numeric(wide[channel], errors='coerce').dropna`
- `pd.to_numeric`
- `values.value_counts`
- `int`
- `len`
- `float`
- `values.min`
- `values.max`
- `values.abs().max`
- `values.abs`
- `values.abs().gt(100).sum`
- `values.abs().gt`

### `_input_pairing_diagnostics`

[Implementação: projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py:206](../../projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py#L206)

```python
_input_pairing_diagnostics(cases: pd.DataFrame) -> dict[str, dict[str, Any]]
```

Check whether declared sample values match the values logged by RocketPy.

**Entradas e tipos declarados**

- `cases: pd.DataFrame`

**Retornos/yields explícitos**

- `diagnostics`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `cases[[sampled, realized]].apply(pd.to_numeric, errors='coerce').dropna`
- `cases[[sampled, realized]].apply`
- `int`
- `len`
- `paired[sampled].eq(paired[realized]).sum`
- `paired[sampled].eq`
- `float`
- `paired[sampled].corr`
- `difference.mean`
- `difference.abs().max`
- `difference.abs`

### `_model_snapshot_comparison`

[Implementação: projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py:231](../../projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py#L231)

```python
_model_snapshot_comparison(reference_manifest: dict[str, Any], campaign_manifest: dict[str, Any]) -> dict[str, Any]
```

Compare hashes das entradas de referência e da campanha Monte Carlo.

Percorre os manifestos e identifica correspondências ou divergências
para impedir que modelos diferentes sejam tratados como a mesma execução.

**Entradas e tipos declarados**

- `reference_manifest: dict[str, Any]`
- `campaign_manifest: dict[str, Any]`

**Retornos/yields explícitos**

- `{'status': status, 'reference_working_tree_snapshot_sha256': reference_snapshot, 'monte_carlo_working_tree_snapshot_sha256': campaign_snapshot, 'configuration_hashes_match': reference_manifest.get('configuration_hashes') == campaign_manifest.get('configuration_hashes')}`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `reference_manifest.get('git', {}).get`
- `reference_manifest.get`
- `campaign_manifest.get('git', {}).get`
- `campaign_manifest.get`

### `_verify_reference_artifacts`

[Implementação: projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py:258](../../projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py#L258)

```python
_verify_reference_artifacts(reference_dir: Path, manifest: dict[str, Any], artifact_names: tuple[str, ...]) -> dict[str, str]
```

Verify every reference artifact before it contributes to the analysis.

**Entradas e tipos declarados**

- `reference_dir: Path`
- `manifest: dict[str, Any]`
- `artifact_names: tuple[str, ...]`

**Retornos/yields explícitos**

- `verified_hashes`

**Exceções lançadas explicitamente**

- `ValueError(f'RocketPy reference manifest has no hash for {artifact_name}')`
- `ValueError(f'RocketPy reference artifact checksum mismatch: {artifact_name}')`

**Colaboradores chamados diretamente**

- `manifest.get('output_hashes', {}).get`
- `manifest.get`
- `ValueError`
- `sha256_file`

### `_mc_apogee`

[Implementação: projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py:275](../../projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py#L275)

```python
_mc_apogee() -> tuple[pd.DataFrame, dict[str, Any]]
```

Carregue os casos Monte Carlo e a evidência de apogeu da campanha escolhida.

Lê os caminhos configurados no script, preserva IDs e metadados
e prepara as tabelas usadas na comparação com telemetria.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `(joined, summary)`

**Exceções lançadas explicitamente**

- `ValueError('Monte Carlo case IDs must be unique')`
- `ValueError('Saved Monte Carlo inputs and outputs do not contain the same case IDs')`
- `ValueError('Some Monte Carlo cases lack their realized RocketPy elevation')`
- `ValueError('Saved Monte Carlo output count disagrees with the scenario manifest')`
- `ValueError('Saved Monte Carlo failure count disagrees with the scenario manifest')`

**Colaboradores chamados diretamente**

- `pd.read_parquet`
- `inputs['case_id'].duplicated().any`
- `inputs['case_id'].duplicated`
- `outputs['case_id'].duplicated().any`
- `outputs['case_id'].duplicated`
- `ValueError`
- `set`
- `list`
- `dict.fromkeys`
- `outputs.merge`
- `joined['rocketpy_elevation'].isna().any`
- `joined['rocketpy_elevation'].isna`
- `joined['apogee_agl_recomputed'].astype`
- `joined['apogee'].astype`
- `yaml.safe_load`
- `(CAMPAIGN_DIR / 'scenarios/nominal/manifest.yaml').read_text`
- `len`
- `(CAMPAIGN_DIR / 'scenarios/nominal/mc_sim.inputs.txt').read_text`
- `input_log.count`
- `int`
- `_input_pairing_diagnostics`
- `float`
- `values.mean`
- `values.std`
- `values.min`
- `values.quantile`
- `values.median`
- `values.max`
- `asl_values.min`
- `asl_values.quantile`
- `asl_values.median`
- `asl_values.max`
- `joined['stored_agl_minus_recomputed_m'].dropna`
- `difference.abs().max`
- `difference.abs`

### `_weather_plot`

[Implementação: projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py:356](../../projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py#L356)

```python
_weather_plot(profile: pd.DataFrame, provenance: dict[str, Any], output: Path) -> None
```

Desenhe o perfil meteorológico candidato e sua proveniência.

Usa profile e provenance para os eixos e rótulos e grava output.
A figura descreve a hipótese atmosférica, sem validá-la como medição do voo.

**Entradas e tipos declarados**

- `profile: pd.DataFrame`
- `provenance: dict[str, Any]`
- `output: Path`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `np.hypot`
- `plt.subplots`
- `wind_axis.plot`
- `wind_axis.set_xlabel`
- `wind_axis.set_ylabel`
- `wind_axis.legend`
- `wind_axis.grid`
- `density_axis.plot`
- `density_axis.set_xlabel`
- `density_axis.legend`
- `density_axis.grid`
- `provenance.get`
- `figure.suptitle`
- `figure.tight_layout`
- `figure.savefig`
- `plt.close`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `_telemetry_plot`

[Implementação: projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py:386](../../projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py#L386)

```python
_telemetry_plot(wide: pd.DataFrame, output: Path) -> None
```

Desenhe altitudes e velocidades angulares do registro original.

Usa wide sem unir segmentos de relógio e grava a figura em output.
Não modifica o arquivo bruto nem presume calibração dos sensores.

**Entradas e tipos declarados**

- `wide: pd.DataFrame`
- `output: Path`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `plt.subplots`
- `altitude_axis.plot`
- `altitude_axis.set_ylabel`
- `altitude_axis.legend`
- `altitude_axis.grid`
- `altitude_axis.set_title`
- `zip`
- `axis.plot`
- `axis.set_ylabel`
- `channel.replace`
- `axis.grid`
- `axes[1].set_title`
- `axes[-1].set_xlabel`
- `figure.suptitle`
- `figure.subplots_adjust`
- `figure.savefig`
- `plt.close`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `_peak_aligned_residuals`

[Implementação: projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py:423](../../projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py#L423)

```python
_peak_aligned_residuals(wide: pd.DataFrame, simulated: pd.DataFrame, metrics: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, dict[str, Any]]]
```

Compare a forma das altitudes após alinhamento declarado pelos picos.

Usa wide, simulated e metrics para selecionar suporte temporal comum
e calcular resíduos. O alinhamento é diagnóstico de forma, não
identificação independente de eventos ou validação absoluta de trajetória.

**Entradas e tipos declarados**

- `wide: pd.DataFrame`
- `simulated: pd.DataFrame`
- `metrics: dict[str, Any]`

**Retornos/yields explícitos**

- `(residuals, summary)`

**Exceções lançadas explicitamente**

- `ValueError('RocketPy reference time series must be strictly increasing')`

**Colaboradores chamados diretamente**

- `float`
- `wide['bmp2_rel_alt_m'].idxmax`
- `simulated['time_s'].to_numpy`
- `simulated['altitude_agl_m'].to_numpy`
- `np.all`
- `np.diff`
- `ValueError`
- `wide[channel].idxmax`
- `wide.iterrows`
- `np.interp`
- `rows.append`
- `int`
- `pd.DataFrame`
- `residuals.loc[residuals['comparison_status'].eq('PEAK_ALIGNED_WITHIN_MODEL_DOMAIN')].copy`
- `residuals['comparison_status'].eq`
- `valid['channel'].eq`
- `channel_rows['observed_peak_relative_time_s'].lt`
- `channel_rows['observed_peak_relative_time_s'].gt`
- `channel_rows.loc[mask, 'observed_minus_modeled_m'].astype`
- `len`
- `values.mean`
- `np.sqrt`
- `np.mean`
- `np.square`
- `phase_rows['observed_minus_modeled_m'].idxmax`
- `phase_rows.sort_values`
- `phase_rows['observed_minus_modeled_m'].gt(0).any`
- `phase_rows['observed_minus_modeled_m'].gt`
- `phase_rows.loc[phase_rows['observed_minus_modeled_m'].gt(0), 'observed_peak_relative_time_s'].min`
- `phase_rows.loc[phase_rows['observed_minus_modeled_m'].gt(0), 'observed_peak_relative_time_s'].max`
- `phase_rows['observed_peak_relative_time_s'].gt`
- `phase_rows['observed_minus_modeled_m'].lt`
- `phase_rows.loc[phase_rows['observed_peak_relative_time_s'].gt(phase_summary['last_positive_residual_time_s']) & phase_rows['observed_minus_modeled_m'].lt(0), 'observed_peak_relative_time_s'].min`
- `residuals.loc[residuals['channel'].eq(channel), 'comparison_status'].eq('OUTSIDE_MODEL_TIME_DOMAIN').sum`
- `residuals.loc[residuals['channel'].eq(channel), 'comparison_status'].eq`
- `residuals['channel'].eq`

### `_peak_aligned_plot`

[Implementação: projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py:533](../../projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py#L533)

```python
_peak_aligned_plot(residuals: pd.DataFrame, simulated: pd.DataFrame, metrics: dict[str, Any], output: Path) -> None
```

Desenhe a comparação de forma com alinhamento pelos picos.

Recebe resíduos já calculados, série simulada e métricas; grava output
com rótulos de referência e domínio da comparação.

**Entradas e tipos declarados**

- `residuals: pd.DataFrame`
- `simulated: pd.DataFrame`
- `metrics: dict[str, Any]`
- `output: Path`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `float`
- `plt.subplots`
- `axis.plot`
- `residuals['channel'].eq`
- `axis.scatter`
- `axis.axvline`
- `axis.axhline`
- `axis.set_xlabel`
- `axis.set_ylabel`
- `axis.set_title`
- `axis.grid`
- `axis.legend`
- `figure.tight_layout`
- `figure.savefig`
- `plt.close`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `_residual_plot`

[Implementação: projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py:572](../../projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py#L572)

```python
_residual_plot(residuals: pd.DataFrame, output: Path) -> None
```

Desenhe os resíduos de altitude no suporte temporal válido.

Usa residuals sem atravessar segmentos de aquisição ou extrapolar
a série simulada; salva a figura em output.

**Entradas e tipos declarados**

- `residuals: pd.DataFrame`
- `output: Path`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `plt.subplots`
- `residuals['comparison_status'].eq`
- `valid['channel'].eq`
- `axis.scatter`
- `axis.axvline`
- `axis.axhline`
- `axis.set_xlabel`
- `axis.set_ylabel`
- `axis.set_title`
- `axis.grid`
- `axis.legend`
- `figure.tight_layout`
- `figure.savefig`
- `plt.close`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `_mc_plot`

[Implementação: projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py:601](../../projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py#L601)

```python
_mc_plot(cases: pd.DataFrame, wide: pd.DataFrame, output: Path) -> None
```

Compare a distribuição simulada de apogeu com picos de altitude registrados.

Usa cases e wide para o histograma e marcadores de observação.
Grava output mantendo explícita a diferença entre altura relativa e absoluta.

**Entradas e tipos declarados**

- `cases: pd.DataFrame`
- `wide: pd.DataFrame`
- `output: Path`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `float`
- `wide[channel].max`
- `plt.subplots`
- `zip`
- `axis.hist`
- `cases[column].dropna`
- `enumerate`
- `axis.axvline`
- `axis.set_xlabel`
- `axis.set_title`
- `axis.grid`
- `axis.legend`
- `axes[0].set_ylabel`
- `figure.suptitle`
- `figure.tight_layout`
- `figure.savefig`
- `plt.close`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `_package_version`

[Implementação: projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py:638](../../projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py#L638)

```python
_package_version(name: str) -> str | None
```

Consulte a versão instalada de uma dependência usada na comparação.

Retorna o texto da versão quando disponível e indicação de ausência
quando a distribuição não é encontrada; não instala pacotes.

**Entradas e tipos declarados**

- `name: str`

**Retornos/yields explícitos**

- `version(name)`
- `None`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `version`

### `run`

[Implementação: projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py:650](../../projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py#L650)

```python
run(output_dir: Path) -> Path
```

Produza um pacote de diagnóstico entre telemetria e Monte Carlo.

Verifica entradas e hashes, compara modelos, monta séries e resíduos
e grava tabelas, figuras, JSON e relatório em output_dir.
Conserva os limites de inferência e não altera a evidência bruta.

**Entradas e tipos declarados**

- `output_dir: Path`

**Retornos/yields explícitos**

- `output_dir`

**Exceções lançadas explicitamente**

- `ValueError('Comparison artifacts must be written beneath results/')`
- `RuntimeError('Raw telemetry changed while comparison was running')`

**Colaboradores chamados diretamente**

- `(REPO_ROOT / 'results').resolve`
- `output_dir.is_absolute`
- `output_dir.resolve`
- `output_dir.is_relative_to`
- `ValueError`
- `_load_primary_trace`
- `_read_json`
- `_verify_reference_artifacts`
- `yaml.safe_load`
- `(CAMPAIGN_DIR / 'config_snapshot/config/launch.yaml').read_text`
- `reference_manifest.get`
- `pd.read_parquet`
- `_mc_apogee`
- `_model_snapshot_comparison`
- `_peak_aligned_residuals`
- `output_dir.mkdir`
- `long_trace.to_parquet`
- `_telemetry_plot`
- `residuals.to_parquet`
- `_peak_aligned_plot`
- `_residual_plot`
- `_weather_plot`
- `_mc_plot`
- `wide[channel].idxmax`
- `float`
- `int`
- `max`
- `peaks.values`
- `datetime.fromisoformat(f"{config_date['date']}T{config_date['time']}").replace`
- `datetime.fromisoformat`
- `ZoneInfo`
- `planned_datetime_local.astimezone`
- `weather_provenance['valid_time_utc'].replace`
- `datetime.now(timezone.utc).isoformat`
- `datetime.now`
- `sha256_file`
- `_gyro_summary`
- `campaign_manifest.get`
- `config_date.get`
- `planned_datetime_utc.isoformat`
- `(weather_valid_time - planned_datetime_utc).total_seconds`
- `subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=REPO_ROOT, check=True, capture_output=True, text=True).stdout.strip`
- `subprocess.run`
- `bool`
- `subprocess.run(['git', 'status', '--porcelain'], cwd=REPO_ROOT, check=True, capture_output=True, text=True).stdout.strip`
- `sys.version.split`
- `_package_version`
- `Path(__file__).resolve`
- `Path`
- `RuntimeError`
- `analysis_path.write_text`
- `json.dumps`
- `report_path.write_text`
- `_render_report`
- `sorted`
- `output_dir.iterdir`
- `path.is_file`
- `path.stat`
- `(output_dir / 'artifact_manifest.json').write_text`

### `_render_report`

[Implementação: projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py:855](../../projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py#L855)

```python
_render_report(data: dict[str, Any]) -> str
```

Converta os resultados canônicos da comparação em relatório Markdown.

Lê somente data, organiza métricas, proveniência e limitações
e retorna texto sem executar novamente a análise física.

**Entradas e tipos declarados**

- `data: dict[str, Any]`

**Retornos/yields explícitos**

- `f"# Neblina 1 telemetry and Monte Carlo comparison\n\n## What was compared\n\nThe raw file \`{data['source']['raw_file']}\` was read only for a SHA-256 check. Its hash before and after processing is \`{data['source']['raw_sha256_before']}\`. The analysis uses the audited Parquet samples and retains source record and line numbers. The exact repeated 86-record \`DADOS DE VÔO\` copy was not counted twice; its original source records were selected using the audit's duplicate mapping.\n\nThe retained trace contains {time['source_record_count']} records from source lines {time['source_line_first']}–{time['source_line_last']}. Device-clock time spans {time['elapsed_from_first_sample_s']:.2f} s from the first selected record; median sample interval is {time['median_sample_interval_s']:.2f} s, maximum interval is {time['maximum_sample_interval_s']:.2f} s, and {time['intervals_over_2s']} intervals exceed 2 s. This is a block-local device-clock axis, not a verified time since ignition.\n\nThe whole-file audit found {data['dataset_inventory']['declared_channel_count']} declared channels, {data['dataset_inventory']['numeric_record_count']:,} numeric records, {data['dataset_inventory']['parse_issue_count']} non-sample/parse-issue lines, {data['dataset_inventory']['timestamp_backward_jump_count']} backward clock jumps across {data['dataset_inventory']['clock_segment_count']} segments, and {data['dataset_inventory']['gps_in_range_coordinate_pair_count']} in-range GPS coordinate pairs (\`{data['dataset_inventory']['gps_status']}\`). The audit retains source order and clock segments; it does not assign reset causes or stitch a global time axis.\n\n## Recorded altitude and attitude observability\n\nThe two onboard-derived altitude channels peak at {peaks['bmp1_rel_alt_m']['recorded_max_m']:.2f} m (BMP1) and {peaks['bmp2_rel_alt_m']['recorded_max_m']:.2f} m (BMP2), both at record {peaks['bmp1_rel_alt_m']['record_index']} / source line {peaks['bmp1_rel_alt_m']['source_line_number']}. The channels agree within {abs(peaks['bmp1_rel_alt_m']['recorded_max_m'] - peaks['bmp2_rel_alt_m']['recorded_max_m']):.2f} m at that sample. These are measured onboard-derived channel values; their vertical reference and calibration are unknown.\n\nAbsolute attitude cannot be reconstructed defensibly from the available metadata. The figure \`altitude_and_raw_angular_rates.png\` therefore plots raw, header-labeled gyro channels as sample markers. It does not integrate them into Euler angles. Both MPU y-axis channels contain {gyro['mpu1_gy_dps']['most_repeated_value_count']} repeats of the recorded value {gyro['mpu1_gy_dps']['most_repeated_value']:.3f} deg/s, and {gyro['mpu1_gy_dps']['count_absolute_value_over_100']} samples exceed 100 deg/s in magnitude. This is consistent with possible clipping or a special code, but sensor range and encoding are unknown. Fast oscillations cannot be evaluated from these sparse data and gaps; the plot does not establish stability or instability.\n\nBoth barometric altitude channels have usable finite readings in this section, though their reference/calibration is unknown. Gyroscope channels are present, while their axis mapping and calibration are unknown. Accelerometer channels are recorded with header unit \`g\` but are not used to infer inertial acceleration or orientation. GPS is present in the file but has no valid coordinate pair.\n\n## RocketPy comparison\n\nThe saved deterministic reference predicts {data['rocketpy_reference']['apogee_agl_m']:.1f} m AGL at {data['rocketpy_reference']['apogee_time_s_from_model_ignition']:.2f} s after model ignition. Its manifest labels it \`{data['rocketpy_reference']['status']}\` and \`{data['rocketpy_reference']['validation_status']}\`; it is a current reference, not a recovered frozen preflight or as-flown model. The deterministic reference and Monte Carlo campaign have \`{data['model_snapshot_comparison']['status']}\` (\`{data['model_snapshot_comparison']['reference_working_tree_snapshot_sha256']}\` vs \`{data['model_snapshot_comparison']['monte_carlo_working_tree_snapshot_sha256']}\`), even though their recorded configuration hashes match: the simulation code snapshots differ. The deterministic marker is therefore omitted from the Monte Carlo histogram; treat the reference run and campaign distribution as separate contextual results.\n\nThe saved Monte Carlo contains {mc['successful_cases']} successful debug cases and {mc['failed_cases']} failures. Corrected AGL is recomputed case by case as RocketPy ASL apogee minus the realized \`rocketpy_elevation\`; this avoids the stale derived \`apogee_agl\` values in the existing output artifact. The corrected distribution has median {stats['median']:.1f} m, 5th–95th percentile {stats['p05']:.1f}–{stats['p95']:.1f} m, and observed sample range {stats['minimum']:.1f}–{stats['maximum']:.1f} m.\n\nThe archived \`outputs.parquet\` AGL column differs from that per-case recomputation by up to {legacy_difference:.2f} m; the old run artifact was left untouched. For each case, the logged RocketPy elevation is compared with the declared \`site_elevation\` sample, and the other available sampled inputs are compared with their \`rocketpy_\` log fields in \`comparison.json\`. Those per-case values do not match (for site elevation, Pearson correlation is {mc['declared_vs_rocketpy_logged_input_pairing']['site_elevation']['pearson_correlation']:+.3f}); interpret apogee as a run-level distribution, not as paired input-to-output sensitivity evidence. Its text input log contains {infinity_count} \`Infinity\` tokens, which are not valid standard JSON numbers and need a separate artifact-format fix.\n\nIf the onboard relative-altitude maximum is treated as AGL, the larger sensor peak is {mc['sensor_peak_minus_mc_max_if_sensor_is_agl_m']:+.1f} m above the largest of these 50 simulated cases and {mc['sensor_peak_minus_mc_p95_if_sensor_is_agl_m']:+.1f} m above their 95th percentile; it is {mc['deterministic_reference_peak_difference_if_sensor_is_agl_m']:+.1f} m above the separate deterministic reference result. If the same channel is treated as ASL, it lies inside the Monte Carlo sample range ({mc['apogee_asl_m']['minimum']:.1f}–{mc['apogee_asl_m']['maximum']:.1f} m) and is {mc['deterministic_reference_peak_difference_if_sensor_is_asl_m']:+.1f} m above the deterministic reference ASL apogee. This datum choice changes the apparent agreement, so these are conditional magnitude comparisons, not a statistically defensible rejection: the sample is small, the sensor datum is unknown, the two model snapshots differ, and the current model's uncertainty assumptions are not a calibrated flight-specific distribution. The companion plot shows both interpretations separately.\n\n\`peak_aligned_altitude_shape.png\` subtracts each measured channel's own peak and aligns that peak to the modelled apogee. This removes the unknown vertical offset and clock origin for a shape-only view. Alignment is imposed for plotting, so it cannot validate apogee timing or event-time accuracy. For BMP2 within the overlapping model-time domain, ascent residual mean/RMSE are {residual['ascent']['mean_bias_m']:+.1f}/{residual['ascent']['rmse_m']:.1f} m and post-peak mean/RMSE are {residual['post_peak']['mean_bias_m']:+.1f}/{residual['post_peak']['rmse_m']:.1f} m, with residual defined as observed minus modeled altitude relative to each peak. The first post-peak sample at +{residual['post_peak']['first_post_peak_sample_time_s']:.2f} s has residual {residual['post_peak']['first_post_peak_sample_residual_m']:+.1f} m; the residual is positive by +{residual['post_peak']['first_positive_residual_time_s']:.2f} s, reaches {residual['post_peak']['maximum_positive_residual_m']:.1f} m at +{residual['post_peak']['time_of_maximum_positive_residual_s']:.2f} s, stays positive through +{residual['post_peak']['last_positive_residual_time_s']:.2f} s, and is negative again at +{residual['post_peak']['first_negative_after_last_positive_time_s']:.2f} s. RocketPy's configured main deployment is +{data['rocketpy_reference']['main_deployment_time_s_after_apogee']:.2f} s after its apogee. The change in residual trend occurs near this modeled recovery transition, which makes recovery timing and descent rate worth reviewing; telemetry does not directly show deployment, so this is not evidence of a cause. Positive post-peak residual means the recorded channel remains higher than the model at the same peak-relative time. These are conditional diagnostics: model values are linearly sampled, while measured samples are not interpolated or extrapolated. The telemetry is sparse and likely affected by altimeter response.\n\n## Weather and limitations\n\nThe saved atmosphere is a cached deterministic Open-Meteo GFS Seamless profile valid at \`{data['weather']['candidate_profile_provenance'].get('valid_time_utc', 'unknown')}\`. It is the model input candidate available in the current reference, not an observation of weather during the actual flight. The launch configuration records \`{data['flight_clock']['planned_launch_datetime'].get('date')}\` at \`{data['flight_clock']['planned_launch_datetime'].get('time')}\` as \`{data['flight_clock']['planned_launch_datetime'].get('status')}\`; converted to UTC, that planned time is \`{data['weather']['planned_launch_time_utc']}\`. The archived profile is valid {data['weather']['candidate_profile_minus_planned_time_hours']:+.1f} hours from the planned launch time. No verified actual launch timestamp ties the device counter to that weather profile. GPS coordinates are unavailable, and airspeed/attitude are not observable with the documented metadata. Weather correlation is therefore \`NOT_ASSESSABLE\`; no causal or correlational claim is made.\n\nThe Monte Carlo reuses one archived deterministic base atmosphere profile across 50 debug cases; its configuration also perturbs the x/y wind components per case (factor standard deviation 0.2, with an additional 1 m/s x-component standard deviation). It does not retain each case's time history and compares apogee only. These perturbations are model inputs, not measured flight weather or a time-matched weather ensemble. The raw telemetry remains ignored by Git and unchanged; PyCharm's orange file color reflects that Git-ignored status, not an inability to read the file.\n\n## Artifacts\n\n- \`primary_flight_trace.parquet\`: source-linked selected records and channels, with block-local elapsed time added.\n- \`altitude_and_raw_angular_rates.png\`: recorded altitude and uncalibrated gyro channels.\n- \`peak_aligned_altitude_shape.png\`: explicitly peak-aligned shape comparison.\n- \`peak_aligned_shape_residuals.parquet\` and \`peak_aligned_altitude_residuals.png\`: conditional shape residuals within the modeled time domain.\n- \`mc_apogee_vs_recorded_peaks.png\`: separate conditional AGL and ASL interpretations.\n- \`candidate_weather_profile.png\`: archived candidate atmosphere profile.\n- \`comparison.json\` and \`artifact_manifest.json\`: findings, provenance, and hashes.\n\nReproduce with:\n\n\`\`\`bash\n.venv/bin/python projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py\n\`\`\`\n"`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `mc.get('legacy_stored_agl_artifact_difference_m', {}).get`
- `mc.get`
- `mc.get('input_log_nonstandard_json_numeric_tokens', {}).get`
- `abs`
- `data['weather']['candidate_profile_provenance'].get`
- `data['flight_clock']['planned_launch_datetime'].get`

### `main`

[Implementação: projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py:923](../../projects/neblina_1/telemetry/compare_flight_to_monte_carlo.py#L923)

```python
main() -> None
```

Execute o diagnóstico de comparação a partir da linha de comando.

Interpreta o diretório de saída, chama run e informa os produtos gerados.
Falhas de integridade ou leitura são propagadas ao processo chamador.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `argparse.ArgumentParser`
- `parser.add_argument`
- `parser.parse_args`
- `datetime.now(timezone.utc).strftime`
- `datetime.now`
- `print`
- `run`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).
