# Funções de source

[Índice e convenções](README.md)

## `source/antares_fd/__init__.py`

Antares Flight Dynamics
Canonical package for shared flight simulation code.

Módulo declarativo, ponto de entrada sem funções ou exportação de interfaces; não contém funções próprias.

## `source/antares_fd/analysis/__init__.py`

Analysis subsystem for Antares Flight Dynamics.

Módulo declarativo, ponto de entrada sem funções ou exportação de interfaces; não contém funções próprias.

## `source/antares_fd/analysis/compliance.py`

Engineering Requirements & Compliance Matrix Evaluation.

Evaluates flight metrics against formal aerospace requirements,
range safety standards, and team engineering design guidelines.
Every check is assigned an explicit Requirement ID, Source citation,
Classification, and physical rationale.

### `evaluate_compliance`

[Implementação: source/antares_fd/analysis/compliance.py:27](../../source/antares_fd/analysis/compliance.py#L27)

```python
evaluate_compliance(metrics: Dict[str, Any]) -> List[ComplianceItem]
```

Evaluates a flight's metrics dictionary against safety and performance requirements.

Returns:
    A list of ComplianceItem records with traceable Requirement IDs and Sources.

**Entradas e tipos declarados**

- `metrics: Dict[str, Any]`

**Retornos/yields explícitos**

- `items`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `metrics.get('rail_dynamics', {}).get`
- `metrics.get`
- `items.append`
- `ComplianceItem`
- `metrics.get('mass_and_stability', {}).get`
- `metrics.get('aerodynamic_loads', {}).get`
- `metrics.get('kinematics', {}).get`
- `metrics.get('timeline', {}).get`
- `metrics.get('recovery', {}).get`
- `drogue.get`
- `abs`

## `source/antares_fd/analysis/flight_metrics.py`

Módulo declarativo, ponto de entrada sem funções ou exportação de interfaces; não contém funções próprias.

## `source/antares_fd/analysis/metrics.py`

Flight Metrics Extraction & Engineering Analysis.

Extracts comprehensive performance, kinematic, aerodynamic, stability,
propulsion, and recovery metrics from a RocketPy Flight instance.
Centralized, single-source-of-truth calculation for tables, charts, and compliance.

### `extract_flight_metrics`

[Implementação: source/antares_fd/analysis/metrics.py:21](../../source/antares_fd/analysis/metrics.py#L21)

```python
extract_flight_metrics(flight: Any, config: Optional[Any]=None, project_dir: Optional[Any]=None) -> FlightMetrics
```

Extracts complete quantitative engineering metrics from a simulated Flight.
Every metric is computed exactly once to guarantee consistency across all reports.

**Entradas e tipos declarados**

- `flight: Any`
- `config: Optional[Any]`
- `project_dir: Optional[Any]`

**Retornos/yields explícitos**

- `FlightMetrics(project_name=project_dir.name if project_dir else 'Antares', vehicle_name=getattr(rocket, 'name', 'Rocket'), flight_name=getattr(flight, 'name', 'Flight'), environment_type=getattr(env, 'atmospheric_model_type', 'Atmosphere'), latitude=float(env.latitude), longitude=float(env.longitude), elevation_m=elev, liftoff_time=0.0, rail_exit_time=t_liftoff, burnout_time=t_burnout, apogee_time=t_apogee, flight_duration=t_final, coast_duration=coast_duration, apogee_agl=apogee_agl, apogee_asl=apogee_asl, drift_at_apogee=drift_apogee, landing_east=landing_east, landing_north=landing_north, landing_distance=drift_final, landing_azimuth=landing_azimuth, max_velocity=float(np.max(ts_speed)), max_velocity_time=float(t_eval[np.argmax(ts_speed)]), max_mach=float(np.max(ts_mach)), max_mach_time=t_max_mach, burnout_velocity=float(flight.speed(t_burnout)), rail_exit_velocity=float(flight.out_of_rail_velocity), rail_exit_acceleration=rail_exit_accel, max_total_acceleration=max_tot_accel / g0, max_total_acceleration_time=t_max_tot_accel, max_dynamic_pressure=float(np.max(ts_q)), max_q_time=t_max_q, max_q_altitude=float(flight.z(t_max_q) - elev), max_q_mach=float(flight.mach_number(t_max_q)), peak_valid_q_alpha=peak_qa, peak_valid_q_alpha_time=t_peak_qa, max_angle_of_attack=float(np.max(ts_alpha[aero_mask])) if np.any(aero_mask) else 0.0, angle_of_attack_at_max_q=float(flight.angle_of_attack(t_max_q)), static_margin_liftoff=float(flight.static_margin(0)), static_margin_rail_exit=float(flight.static_margin(t_liftoff)), static_margin_max_q=float(flight.static_margin(t_max_q)), static_margin_burnout=float(flight.static_margin(t_burnout)), minimum_burn_static_margin=sm_min_burn, maximum_static_margin=max_sm, maximum_angular_velocity=float(np.degrees(np.max(ts_omega_mag[ascent_mask]))) if np.any(ascent_mask) else 0.0, motor_name=getattr(motor, 'name', 'SolidMotor'), burnout_mass=float(rocket.total_mass(t_burnout)), total_impulse=float(getattr(motor, 'total_impulse', 0.0)), average_thrust=float(getattr(motor, 'average_thrust', 0.0)), max_thrust=float(getattr(motor, 'max_thrust', 0.0)), propellant_mass=float(getattr(motor, 'propellant_initial_mass', m_liftoff - ts_mass[burn_mask][-1])), initial_tw=initial_tw, rail_exit_tw=rail_exit_tw, peak_tw=peak_tw, average_burn_tw=avg_burn_tw, drogue_deployment_time=drogue_evt.time if drogue_evt else None, main_deployment_time=main_evt.time if main_evt else None, drogue_descent_rate=drogue_evt.steady_sink_rate if drogue_evt else None, main_descent_rate=main_evt.steady_sink_rate if main_evt else None, drogue_event=drogue_evt, main_event=main_evt, touchdown_velocity=v_impact, touchdown_energy=e_kin, validation=validation, timeseries=timeseries, atmosphere=atm_prof, ignition_tw=ignition_tw, aero_analysis_window={'start': 'rail_exit', 'end': 'apogee', 'minimum_dynamic_pressure_pa': min_q, 'minimum_speed_mps': min_speed}, events=EventRegistry(ignition=EventRecord('Ignition', t_ignition, float(flight.z(t_ignition) - elev), float(flight.dynamic_pressure(t_ignition)), float(flight.speed(t_ignition))), first_motion=EventRecord('First motion', 0.0, float(flight.z(0.0) - elev), float(flight.dynamic_pressure(0.0)), float(flight.speed(0.0))), rail_exit=EventRecord('Rail exit', t_liftoff, float(flight.z(t_liftoff) - elev), float(flight.dynamic_pressure(t_liftoff)), float(flight.speed(t_liftoff))), max_acceleration=EventRecord('Max acceleration', t_max_tot_accel, float(flight.z(t_max_tot_accel) - elev), float(flight.dynamic_pressure(t_max_tot_accel)), float(flight.speed(t_max_tot_accel))), max_q=EventRecord('Max-Q', t_max_q, float(flight.z(t_max_q) - elev), float(flight.dynamic_pressure(t_max_q)), float(flight.speed(t_max_q))), max_mach=EventRecord('Max Mach', t_max_mach, float(flight.z(t_max_mach) - elev), float(flight.dynamic_pressure(t_max_mach)), float(ts_speed[max_mach_idx])), burnout=EventRecord('Burnout', t_burnout, float(flight.z(t_burnout) - elev), float(flight.dynamic_pressure(t_burnout)), float(flight.speed(t_burnout))), apogee=EventRecord('Apogee', t_apogee, apogee_agl, float(flight.dynamic_pressure(t_apogee)), float(flight.speed(t_apogee))), drogue_trigger=drogue_evt, drogue_inflation=EventRecord('Drogue inflation', drogue_evt.deploy_time, drogue_evt.altitude_agl, drogue_evt.dynamic_pressure, drogue_evt.speed) if drogue_evt else None, main_trigger=main_evt, main_inflation=EventRecord('Main inflation', main_evt.deploy_time, main_evt.altitude_agl, main_evt.dynamic_pressure, main_evt.speed) if main_evt else None, touchdown=EventRecord('Touchdown', t_final, 0.0, float(flight.dynamic_pressure(t_final)), v_impact)))`

**Exceções lançadas explicitamente**

- `ValueError('Atmospheric profile does not cover a usable altitude range for reporting')`

**Colaboradores chamados diretamente**

- `float`
- `np.linspace`
- `np.concatenate`
- `np.array`
- `flight.z`
- `flight.x`
- `flight.y`
- `flight.vz`
- `flight.speed`
- `flight.mach_number`
- `flight.ax`
- `flight.ay`
- `flight.az`
- `np.sqrt`
- `flight.dynamic_pressure`
- `flight.angle_of_attack`
- `flight.static_margin`
- `np.abs`
- `dict`
- `config.vehicle.get`
- `model_limits.get`
- `window_cfg.get`
- `motor.thrust`
- `rocket.total_mass`
- `rocket.center_of_mass`
- `rocket.cp_position`
- `hasattr`
- `flight.w1`
- `flight.w2`
- `flight.w3`
- `FlightTimeSeries`
- `np.max`
- `np.hypot`
- `np.degrees`
- `np.arctan2`
- `np.any`
- `np.argmax`
- `int`
- `getattr`
- `len`
- `np.mean`
- `p_obj.name.lower`
- `ParachuteEvent`
- `abs`
- `min`
- `np.min`
- `isinstance`
- `atmosphere_meta.get`
- `np.asarray`
- `max`
- `np.isfinite([lower_asl, upper_asl]).all`
- `np.isfinite`
- `ValueError`
- `env.wind_velocity_x`
- `env.wind_velocity_y`
- `env_u.append`
- `env_v.append`
- `env_spd.append`
- `env_dir.append`
- `env_rho.append`
- `env.density`
- `env_sos.append`
- `env.speed_of_sound`
- `AtmosphereProfile`
- `tuple`
- `map`
- `FlightMetrics`
- `EventRegistry`
- `EventRecord`

## `source/antares_fd/analysis/provenance.py`

Provenance, Traceability, Model Quality & Validity Analysis.

Gathers deterministic reproducibility metadata:
- Git repository state (commit, branch, dirty flag)
- Python environment & dependency versions
- Cryptographic SHA-256 hashes of configuration and propulsion files
- Model input source quality classification (Measured vs Estimated)
- Model validity envelope checks

### `compute_file_sha256`

[Implementação: source/antares_fd/analysis/provenance.py:28](../../source/antares_fd/analysis/provenance.py#L28)

```python
compute_file_sha256(filepath: Path) -> Optional[str]
```

Computes SHA-256 hash of a file if it exists.

**Entradas e tipos declarados**

- `filepath: Path`

**Retornos/yields explícitos**

- `None`
- `h.hexdigest()`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `filepath.exists`
- `filepath.is_file`
- `hashlib.sha256`
- `open`
- `f.read`
- `h.update`
- `h.hexdigest`

### `_working_tree_snapshot_sha256`

[Implementação: source/antares_fd/analysis/provenance.py:39](../../source/antares_fd/analysis/provenance.py#L39)

```python
_working_tree_snapshot_sha256(repo_dir: Path) -> str
```

Hash tracked diffs and nonignored untracked files without absolute paths.

**Entradas e tipos declarados**

- `repo_dir: Path`

**Retornos/yields explícitos**

- `digest.hexdigest()`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `hashlib.sha256`
- `subprocess.check_output`
- `str`
- `digest.update`
- `sorted`
- `untracked.split`
- `os.fsdecode`
- `Path`
- `path.is_file`
- `path.read_bytes`
- `digest.hexdigest`

### `get_git_provenance`

[Implementação: source/antares_fd/analysis/provenance.py:66](../../source/antares_fd/analysis/provenance.py#L66)

```python
get_git_provenance(repo_dir: Path) -> Dict[str, str]
```

Extract commit state and a content hash for the exact dirty worktree.

**Entradas e tipos declarados**

- `repo_dir: Path`

**Retornos/yields explícitos**

- `provenance`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=str(repo_dir), stderr=subprocess.DEVNULL, text=True).strip`
- `subprocess.check_output`
- `str`
- `subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=str(repo_dir), stderr=subprocess.DEVNULL, text=True).strip`
- `subprocess.check_output(['git', 'status', '--porcelain'], cwd=str(repo_dir), stderr=subprocess.DEVNULL, text=True).strip`
- `len`
- `_working_tree_snapshot_sha256`

### `_get_package_version`

[Implementação: source/antares_fd/analysis/provenance.py:102](../../source/antares_fd/analysis/provenance.py#L102)

```python
_get_package_version(pkg_name: str) -> str
```

Safely retrieves a package version.

**Entradas e tipos declarados**

- `pkg_name: str`

**Retornos/yields explícitos**

- `importlib.metadata.version(pkg_name)`
- `getattr(mod, '__version__', 'unknown')`
- `'unknown'`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `importlib.metadata.version`
- `__import__`
- `getattr`

### `_read_yaml`

[Implementação: source/antares_fd/analysis/provenance.py:114](../../source/antares_fd/analysis/provenance.py#L114)

```python
_read_yaml(path: Path) -> Dict[str, Any]
```

Read configuration metadata without inventing missing evidence.

**Entradas e tipos declarados**

- `path: Path`

**Retornos/yields explícitos**

- `{}`
- `value if isinstance(value, dict) else {}`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `path.exists`
- `yaml.safe_load`
- `path.read_text`
- `isinstance`

### `_value_at`

[Implementação: source/antares_fd/analysis/provenance.py:125](../../source/antares_fd/analysis/provenance.py#L125)

```python
_value_at(data: Dict[str, Any], *keys: str) -> Any
```

Consulte uma sequência de chaves sem criar dados ausentes.

Percorre os dicionários em data seguindo keys e retorna None quando um nível
não existe ou não é um mapeamento; não modifica a configuração.

**Entradas e tipos declarados**

- `data: Dict[str, Any]`
- `*keys: argumentos posicionais adicionais`

**Retornos/yields explícitos**

- `None`
- `value`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `isinstance`
- `value.get`

### `_display_value`

[Implementação: source/antares_fd/analysis/provenance.py:139](../../source/antares_fd/analysis/provenance.py#L139)

```python
_display_value(value: Any) -> str
```

Converta um valor de proveniência em texto de apresentação.

Dicionários e listas são serializados em JSON ordenado; escalares usam str.
O resultado é apenas visual e não altera a evidência original.

**Entradas e tipos declarados**

- `value: Any`

**Retornos/yields explícitos**

- `'NOT PROVIDED'`
- `str(value)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `str`

### `_repo_relative`

[Implementação: source/antares_fd/analysis/provenance.py:150](../../source/antares_fd/analysis/provenance.py#L150)

```python
_repo_relative(path: Path, project_dir: Path, project_root: Path) -> str
```

Return a stable path suitable for a report.

**Entradas e tipos declarados**

- `path: Path`
- `project_dir: Path`
- `project_root: Path`

**Retornos/yields explícitos**

- `path.resolve().relative_to(base.resolve()).as_posix()`
- `path.name`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `path.resolve().relative_to(base.resolve()).as_posix`
- `path.resolve().relative_to`
- `path.resolve`
- `base.resolve`

### `_provenance_record`

[Implementação: source/antares_fd/analysis/provenance.py:160](../../source/antares_fd/analysis/provenance.py#L160)

```python
_provenance_record(parameter: str, value: Any, unit: str, *, source: Any=None, source_type: Any=None, reference: Any=None, revision: Any=None, method: Any=None, uncertainty: Any=None, semantics: Any=None, confidence: Any=None, notes: Any=None) -> Dict[str, str]
```

Build a row using only explicitly configured provenance.

**Entradas e tipos declarados**

- `parameter: str`
- `value: Any`
- `unit: str`
- `source: Any`
- `source_type: Any`
- `reference: Any`
- `revision: Any`
- `method: Any`
- `uncertainty: Any`
- `semantics: Any`
- `confidence: Any`
- `notes: Any`

**Retornos/yields explícitos**

- `{'parameter': parameter, 'nominal': _display_value(value), 'unit': unit, 'source': _display_value(source), 'classification': _display_value(source_type).upper() if source_type else 'UNKNOWN', 'reference': _display_value(reference), 'revision': _display_value(revision), 'method': _display_value(method), 'uncertainty': _display_value(uncertainty), 'uncertainty_semantics': _display_value(semantics), 'confidence': _display_value(confidence), 'notes': _display_value(notes)}`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `_display_value`
- `_display_value(source_type).upper`

### `_config_input_quality`

[Implementação: source/antares_fd/analysis/provenance.py:182](../../source/antares_fd/analysis/provenance.py#L182)

```python
_config_input_quality(project_dir: Path, project_root: Path) -> List[Dict[str, str]]
```

Extract model-input evidence from the project's YAML files.

**Entradas e tipos declarados**

- `project_dir: Path`
- `project_root: Path`

**Retornos/yields explícitos**

- `rows`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `_read_yaml`
- `vehicle.get`
- `vehicle_data.get`
- `_provenance_record`
- `mass.get`
- `_value_at`
- `rows.append`
- `inertia.get`
- `motor.get`
- `motor_data.get`
- `str`
- `configured_path.exists`
- `_repo_relative`
- `drag.get`
- `model.get`
- `mode.replace('_', ' ').title`
- `mode.replace`
- `launch.get`
- `launch_data.get`
- `rows.extend`
- `site.get`
- `environment.get`
- `environment_data.get`
- `recovery.get('recovery', {}).get`
- `recovery.get`
- `isinstance`
- `device.get`
- `device_prov.get`
- `aero.get`
- `cd_prov.get`

### `collect_reproducibility_data`

[Implementação: source/antares_fd/analysis/provenance.py:284](../../source/antares_fd/analysis/provenance.py#L284)

```python
collect_reproducibility_data(project_dir: Path) -> Dict[str, Any]
```

Collects complete provenance, config hashes, input quality, and validity data.

**Entradas e tipos declarados**

- `project_dir: Path`

**Retornos/yields explícitos**

- `{'git': git_data, 'environment': env_versions, 'config_hashes': config_hashes, 'data_hashes': data_hashes, 'input_quality': input_quality, 'provenance_status': 'CONFIGURED_METADATA_ONLY'}`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `project_dir.resolve`
- `get_git_provenance`
- `platform.python_version`
- `_get_package_version`
- `platform.system`
- `platform.release`
- `config_dir.exists`
- `compute_file_sha256`
- `_read_yaml(config_dir / 'vehicle.yaml').get`
- `_read_yaml`
- `_read_yaml(config_dir / 'motor.yaml').get`
- `motor_data.get`
- `_value_at`
- `referenced_files.items`
- `str`
- `configured_path.exists`
- `_repo_relative`
- `_config_input_quality`

### `evaluate_model_validity`

[Implementação: source/antares_fd/analysis/provenance.py:340](../../source/antares_fd/analysis/provenance.py#L340)

```python
evaluate_model_validity(metrics: FlightMetrics) -> List[Dict[str, str]]
```

Evaluates simulation metrics against physics and aerodynamic model limits.

**Entradas e tipos declarados**

- `metrics: FlightMetrics`

**Retornos/yields explícitos**

- `validity_checks`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `isinstance`
- `metrics.get('kinematics', {}).get`
- `metrics.get`
- `metrics.get('aerodynamic_loads', {}).get`
- `metrics.get('trajectory', {}).get`
- `metrics.get('rail_dynamics', {}).get`

## `source/antares_fd/analysis/requirements.py`

### `EvaluatedRequirement.is_critical`

[Implementação: source/antares_fd/analysis/requirements.py:25](../../source/antares_fd/analysis/requirements.py#L25)

```python
EvaluatedRequirement.is_critical(self) -> bool
```

Informe se o resultado viola um requisito ou o domínio do modelo.

Retorna bool pela associação do status ao conjunto explícito de falhas.
Ausência de avaliação permanece distinta de violação confirmada.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `self.status in ['VIOLATED', 'OUTSIDE GUIDELINE', 'MODEL RANGE EXCEEDED']`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- Nenhuma ocorrência explícita no corpo local.

### `RequirementDB.__init__`

[Implementação: source/antares_fd/analysis/requirements.py:34](../../source/antares_fd/analysis/requirements.py#L34)

```python
RequirementDB.__init__(self, yaml_path: Path)
```

Carregue requisitos e limites de validade de um arquivo YAML.

Lê yaml_path quando existente, indexa requirements e incorpora model_validity
com classificação MODEL_VALIDITY_LIMIT. Arquivo ausente produz base vazia.

**Entradas e tipos declarados**

- `yaml_path: Path`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `yaml_path.exists`
- `open`
- `yaml.safe_load`
- `data['model_validity'].items`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `RequirementDB.evaluate`

[Implementação: source/antares_fd/analysis/requirements.py:52](../../source/antares_fd/analysis/requirements.py#L52)

```python
RequirementDB.evaluate(self, metrics: FlightMetrics) -> List[EvaluatedRequirement]
```

Compare métricas escalares com limites de engenharia rastreáveis.

Para cada requisito, obtém o atributo declarado em metrics e calcula a margem
para >=, <= ou intervalo inclusivo. Margem negativa reprova; tolerância não
mascara violação. Valores ausentes, não finitos ou limites inválidos resultam
em NOT EVALUATED e margem None. Retorna uma lista de EvaluatedRequirement
com valor, limite, unidade, origem e classificação; não modifica metrics.

**Entradas e tipos declarados**

- `metrics: FlightMetrics`

**Retornos/yields explícitos**

- `results`

**Exceções lançadas explicitamente**

- `ValueError('Requirement metric is not finite')`
- `ValueError('Requirement limit is not finite')`
- `ValueError('Requirement interval must be an ordered pair')`

**Colaboradores chamados diretamente**

- `self.requirements.items`
- `req.get`
- `getattr`
- `str(req.get('source_type', 'ENGINEERING_GUIDELINE')).upper`
- `str`
- `results.append`
- `EvaluatedRequirement`
- `math.isfinite`
- `float`
- `ValueError`
- `isinstance`
- `all`
- `len`
- `min`

## `source/antares_fd/analysis/scenario_uq.py`

Scenario stochastic post-processing using common random-number cases.

### `summarize_scenario`

[Implementação: source/antares_fd/analysis/scenario_uq.py:25](../../source/antares_fd/analysis/scenario_uq.py#L25)

```python
summarize_scenario(scenario_id: str, outputs: pd.DataFrame, failures: pd.DataFrame | None=None) -> dict
```

Return the complete applicable scalar summary for one scenario.

**Entradas e tipos declarados**

- `scenario_id: str`
- `outputs: pd.DataFrame`
- `failures: pd.DataFrame | None`

**Retornos/yields explícitos**

- `result`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `pd.DataFrame`
- `distribution_statistics`
- `int`
- `len`
- `float`
- `max`
- `statistics.to_dict`
- `{'landing_east', 'landing_north'}.issubset`
- `landing_dispersion`

### `paired_scenario_comparison`

[Implementação: source/antares_fd/analysis/scenario_uq.py:42](../../source/antares_fd/analysis/scenario_uq.py#L42)

```python
paired_scenario_comparison(frames: Mapping[str, pd.DataFrame], columns: tuple[str, ...]=('apogee_agl', 'flight_duration', 'landing_distance', 'touchdown_velocity', 'touchdown_energy')) -> pd.DataFrame
```

Calculate paired deltas for shared case IDs.

A missing case ID produces an explicit unpaired result. If some cases
failed in one scenario, the common valid subset is retained and marked
partial so the report exposes the reduced comparison population.

**Entradas e tipos declarados**

- `frames: Mapping[str, pd.DataFrame]`
- `columns: tuple[str, ...]`

**Retornos/yields explícitos**

- `pd.DataFrame()`
- `pd.DataFrame([{'comparison_status': 'UNPAIRED / NOT DIRECTLY COMPARABLE'}])`
- `result`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `pd.DataFrame`
- `list`
- `base[['case_id'] + [c for c in columns if c in base]].copy`
- `result.rename`
- `other[['case_id'] + [c for c in columns if c in other]].copy`
- `right.rename`
- `result.merge`
- `pd.to_numeric`
- `set`
- `pd.to_numeric(frame['case_id'], errors='coerce').dropna().astype`
- `pd.to_numeric(frame['case_id'], errors='coerce').dropna`
- `frames.values`
- `bool`
- `all`

### `paired_comparison_statistics`

[Implementação: source/antares_fd/analysis/scenario_uq.py:80](../../source/antares_fd/analysis/scenario_uq.py#L80)

```python
paired_comparison_statistics(paired: pd.DataFrame) -> pd.DataFrame
```

Summarize every paired delta using the same empirical statistics.

**Entradas e tipos declarados**

- `paired: pd.DataFrame`

**Retornos/yields explícitos**

- `pd.DataFrame()`
- `distribution_statistics(paired, columns=columns)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `paired['comparison_status'].isin(valid_statuses).any`
- `paired['comparison_status'].isin`
- `pd.DataFrame`
- `column.startswith`
- `distribution_statistics`

### `deterministic_scenario_consistency`

[Implementação: source/antares_fd/analysis/scenario_uq.py:89](../../source/antares_fd/analysis/scenario_uq.py#L89)

```python
deterministic_scenario_consistency(metrics_by_scenario: Mapping[str, Any], tolerance: Mapping[str, float] | None=None) -> dict[str, Any]
```

Check ascent metrics against nominal for post-ascent recovery cases.

**Entradas e tipos declarados**

- `metrics_by_scenario: Mapping[str, Any]`
- `tolerance: Mapping[str, float] | None`

**Retornos/yields explícitos**

- `{'status': 'NOT AVAILABLE', 'reason': 'nominal deterministic metrics are missing', 'comparisons': []}`
- `{'status': 'PASS' if all((item['status'] == 'CONSISTENT THROUGH ASCENT' for item in comparisons)) else 'SCENARIO CONSISTENCY FAILURE', 'comparisons': comparisons, 'tolerances': tolerance}`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `dict`
- `metrics_by_scenario.get`
- `metrics_by_scenario.items`
- `tolerance.items`
- `getattr`
- `float`
- `np.isfinite`
- `abs`
- `violations.append`
- `comparisons.append`
- `all`

### `empirical_landing_surface`

[Implementação: source/antares_fd/analysis/scenario_uq.py:117](../../source/antares_fd/analysis/scenario_uq.py#L117)

```python
empirical_landing_surface(outputs: pd.DataFrame, bins: int=40) -> dict
```

Return an empirical 2-D occupancy surface, without Gaussian assumptions.

**Entradas e tipos declarados**

- `outputs: pd.DataFrame`
- `bins: int`

**Retornos/yields explícitos**

- `_empirical_landing_surface(outputs, bins=bins)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `_empirical_landing_surface`

## `source/antares_fd/analysis/sensitivity.py`

Monte Carlo Statistical & Sensitivity Analysis.

Computes distributions, percentiles, and input-output correlations
(Tornado analysis) from Monte Carlo campaigns.

### `analyze_monte_carlo_sensitivity`

[Implementação: source/antares_fd/analysis/sensitivity.py:18](../../source/antares_fd/analysis/sensitivity.py#L18)

```python
analyze_monte_carlo_sensitivity(outputs_file: Path, inputs_file: Optional[Path]=None, target_metric: str='apogee') -> Dict[str, Any]
```

Analyzes outputs and stochastic inputs to produce statistical summaries and sensitivity correlations.

Args:
    outputs_file: Path to mc_sim.outputs.txt.
    inputs_file: Optional Path to mc_sim.inputs.txt.
    target_metric: Primary metric for sensitivity analysis ('apogee' or 'impact_distance').

Returns:
    Structured dictionary containing distribution statistics, percentiles, and sensitivity ranking.

**Entradas e tipos declarados**

- `outputs_file: Path`
- `inputs_file: Optional[Path]`
- `target_metric: str`

**Retornos/yields explícitos**

- `{}`
- `{'num_cases': len(df_out), 'statistics': summary_stats, 'sensitivity_target': target_metric, 'sensitivity_ranking': sensitivity_ranking}`

**Exceções lançadas explicitamente**

- `ValueError(f'Monte Carlo input/output record counts differ: {len(in_records)} inputs vs {len(out_records)} outputs')`

**Colaboradores chamados diretamente**

- `outputs_file.exists`
- `read_jsonl_objects`
- `pd.DataFrame`
- `np.sqrt`
- `finite_numeric_series`
- `np.isfinite`
- `len`
- `summarize_finite_values`
- `float`
- `np.percentile`
- `series.min`
- `series.max`
- `ValueError`
- `row.items`
- `isinstance`
- `flat_inputs.append`
- `np.std`
- `stats.pearsonr`
- `stats.spearmanr`
- `np.isnan`
- `sensitivity_ranking.append`
- `abs`
- `int`
- `sensitivity_ranking.sort`

## `source/antares_fd/analysis/uq.py`

Statistical post processing for saved Monte Carlo result tables.

Functions in this module consume pandas tables and never need RocketPy
objects.  They are deliberately small and composable so reports, CLI tools and
future Award Brief renderers use the same calculations.

### `finite_numeric_series`

[Implementação: source/antares_fd/analysis/uq.py:22](../../source/antares_fd/analysis/uq.py#L22)

```python
finite_numeric_series(values: Iterable[Any], metric: str) -> np.ndarray
```

Return aligned finite scalars, preserving nulls as NaN and rejecting bad values.

**Entradas e tipos declarados**

- `values: Iterable[Any]`
- `metric: str`

**Retornos/yields explícitos**

- `np.asarray(validated, dtype=float)`

**Exceções lançadas explicitamente**

- `ValueError(f'Metric {metric!r} contains a non-numeric value')`
- `ValueError(f'Metric {metric!r} contains a value outside finite float range')`
- `ValueError(f'Metric {metric!r} contains a non-finite value')`

**Colaboradores chamados diretamente**

- `validated.append`
- `isinstance`
- `ValueError`
- `float`
- `math.isnan`
- `math.isfinite`
- `np.asarray`

### `finite_numeric_values`

[Implementação: source/antares_fd/analysis/uq.py:44](../../source/antares_fd/analysis/uq.py#L44)

```python
finite_numeric_values(values: Iterable[Any], metric: str) -> np.ndarray
```

Return finite scalar values, preserving nulls as missing and rejecting bad types.

**Entradas e tipos declarados**

- `values: Iterable[Any]`
- `metric: str`

**Retornos/yields explícitos**

- `sample[np.isfinite(sample)]`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `finite_numeric_series`
- `np.isfinite`

### `summarize_finite_values`

[Implementação: source/antares_fd/analysis/uq.py:50](../../source/antares_fd/analysis/uq.py#L50)

```python
summarize_finite_values(values: Iterable[Any], metric: str, *, ddof: int=1) -> tuple[int, float | None, float | None]
```

Compute stable mean and standard deviation without intermediate overflow.

**Entradas e tipos declarados**

- `values: Iterable[Any]`
- `metric: str`
- `ddof: int`

**Retornos/yields explícitos**

- `(count, None, None)`
- `(count, mean, standard_deviation)`

**Exceções lançadas explicitamente**

- `ValueError('ddof must be non-negative')`
- `ValueError(f'Metric {metric!r} summary statistics overflow finite range')`

**Colaboradores chamados diretamente**

- `ValueError`
- `finite_numeric_values`
- `len`
- `math.fsum`
- `float`
- `np.max`
- `np.abs`
- `math.sqrt`
- `math.isfinite`

### `_numeric`

[Implementação: source/antares_fd/analysis/uq.py:79](../../source/antares_fd/analysis/uq.py#L79)

```python
_numeric(values: Iterable[Any]) -> np.ndarray
```

Extraia os escalares finitos para os cálculos estatísticos internos.

Delega a finite_numeric_values, preservando a rejeição de dados inválidos
e retornando um vetor NumPy, sem substituir ausências por zero.

**Entradas e tipos declarados**

- `values: Iterable[Any]`

**Retornos/yields explícitos**

- `finite_numeric_values(values, 'analysis input')`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `finite_numeric_values`

### `distribution_statistics`

[Implementação: source/antares_fd/analysis/uq.py:88](../../source/antares_fd/analysis/uq.py#L88)

```python
distribution_statistics(frame: pd.DataFrame, columns: Sequence[str] | None=None) -> pd.DataFrame
```

Return one typed row per output and standard engineering percentiles.

**Entradas e tipos declarados**

- `frame: pd.DataFrame`
- `columns: Sequence[str] | None`

**Retornos/yields explícitos**

- `pd.DataFrame(rows)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `list`
- `frame.select_dtypes`
- `finite_numeric_values`
- `str`
- `summarize_finite_values`
- `row.update`
- `rows.append`
- `float`
- `np.min`
- `np.max`
- `len`
- `stats.skew`
- `stats.kurtosis`
- `np.percentile`
- `pd.DataFrame`

### `quantile_confidence_interval`

[Implementação: source/antares_fd/analysis/uq.py:120](../../source/antares_fd/analysis/uq.py#L120)

```python
quantile_confidence_interval(values: Iterable[Any], quantile: float, confidence: float=0.95) -> tuple[float, float]
```

Exact order-statistics interval for a population quantile.

The interval is formed from binomial order statistics, which does not
assume a Gaussian output distribution.  Endpoints are observed sample
values and therefore have an honest resolution at small sample counts.

**Entradas e tipos declarados**

- `values: Iterable[Any]`
- `quantile: float`
- `confidence: float`

**Retornos/yields explícitos**

- `(float('nan'), float('nan'))`
- `(float(sample[lower_rank - 1]), float(sample[upper_rank - 1]))`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `np.sort`
- `_numeric`
- `len`
- `float`
- `np.clip`
- `int`
- `stats.binom.ppf`
- `stats.binom.isf`
- `max`
- `min`

### `probability_confidence_interval`

[Implementação: source/antares_fd/analysis/uq.py:139](../../source/antares_fd/analysis/uq.py#L139)

```python
probability_confidence_interval(successes: int, trials: int, confidence: float=0.95) -> tuple[float, float]
```

Two-sided exact Clopper-Pearson interval for a binomial probability.

**Entradas e tipos declarados**

- `successes: int`
- `trials: int`
- `confidence: float`

**Retornos/yields explícitos**

- `(float('nan'), float('nan'))`
- `(lower, upper)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `float`
- `max`
- `min`
- `int`
- `stats.beta.ppf`

### `one_sided_lower_bound`

[Implementação: source/antares_fd/analysis/uq.py:150](../../source/antares_fd/analysis/uq.py#L150)

```python
one_sided_lower_bound(successes: int, trials: int, confidence: float=0.95) -> float
```

Exact one-sided lower confidence bound for a compliance probability.

**Entradas e tipos declarados**

- `successes: int`
- `trials: int`
- `confidence: float`

**Retornos/yields explícitos**

- `float('nan')`
- `0.0`
- `float(stats.beta.ppf(1.0 - (1.0 - confidence), successes, trials - successes + 1))`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `float`
- `max`
- `min`
- `int`
- `stats.beta.ppf`

### `landing_dispersion`

[Implementação: source/antares_fd/analysis/uq.py:160](../../source/antares_fd/analysis/uq.py#L160)

```python
landing_dispersion(frame: pd.DataFrame, confidence_levels: Sequence[float]=(0.5, 0.8, 0.9, 0.95, 0.99)) -> dict[str, Any]
```

Calculate ENU covariance and correctly scaled two-dimensional ellipses.

**Entradas e tipos declarados**

- `frame: pd.DataFrame`
- `confidence_levels: Sequence[float]`

**Retornos/yields explícitos**

- `{'count': 0, 'warning': 'landing coordinates unavailable'}`
- `{'count': int(len(points)), 'mean_east': float(mean[0]), 'mean_north': float(mean[1]), 'median_east': float(np.median(points[:, 0])), 'median_north': float(np.median(points[:, 1])), 'covariance': covariance.tolist(), 'ellipses': ellipses, 'warning': warning}`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `frame[[east_name, north_name]].apply(pd.to_numeric, errors='coerce').dropna().to_numpy`
- `frame[[east_name, north_name]].apply(pd.to_numeric, errors='coerce').dropna`
- `frame[[east_name, north_name]].apply`
- `len`
- `points.mean`
- `np.cov`
- `np.zeros`
- `np.asarray(covariance, dtype=float).reshape`
- `np.asarray`
- `np.linalg.eigh`
- `np.argsort`
- `np.maximum`
- `float`
- `np.degrees`
- `np.arctan2`
- `np.sqrt`
- `stats.chi2.ppf`
- `str`
- `np.linalg.norm`
- `stats.skew`
- `np.linalg.matrix_rank`
- `int`
- `np.median`
- `covariance.tolist`

### `empirical_landing_surface`

[Implementação: source/antares_fd/analysis/uq.py:202](../../source/antares_fd/analysis/uq.py#L202)

```python
empirical_landing_surface(frame: pd.DataFrame, bins: int=40) -> dict[str, Any]
```

Return an empirical occupancy density for ENU landing coordinates.

**Entradas e tipos declarados**

- `frame: pd.DataFrame`
- `bins: int`

**Retornos/yields explícitos**

- `{'status': 'NOT APPLICABLE'}`
- `{'status': 'INSUFFICIENT DATA'}`
- `{'status': 'AVAILABLE', 'method': 'empirical_2d_histogram', 'density': density.tolist(), 'probability': probability.tolist(), 'east_edges': east_edges.tolist(), 'north_edges': north_edges.tolist(), 'sample_count': int(len(points)), 'definition': 'empirical occupancy density; no Gaussian assumption'}`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `{'landing_east', 'landing_north'}.issubset`
- `frame[['landing_east', 'landing_north']].apply(pd.to_numeric, errors='coerce').dropna().to_numpy`
- `frame[['landing_east', 'landing_north']].apply(pd.to_numeric, errors='coerce').dropna`
- `frame[['landing_east', 'landing_north']].apply`
- `len`
- `np.histogram2d`
- `density.tolist`
- `probability.tolist`
- `east_edges.tolist`
- `north_edges.tolist`
- `int`

### `empirical_containment_levels`

[Implementação: source/antares_fd/analysis/uq.py:221](../../source/antares_fd/analysis/uq.py#L221)

```python
empirical_containment_levels(surface: Mapping[str, Any], levels: Sequence[float]=(0.5, 0.8, 0.9, 0.95, 0.99)) -> pd.DataFrame
```

Compute highest-density histogram thresholds for empirical contours.

**Entradas e tipos declarados**

- `surface: Mapping[str, Any]`
- `levels: Sequence[float]`

**Retornos/yields explícitos**

- `pd.DataFrame()`
- `pd.DataFrame(rows)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `surface.get`
- `pd.DataFrame`
- `np.asarray`
- `np.argsort`
- `density.ravel`
- `np.cumsum`
- `probability.ravel`
- `int`
- `np.searchsorted`
- `float`
- `min`
- `len`
- `rows.append`

### `ecdf`

[Implementação: source/antares_fd/analysis/uq.py:239](../../source/antares_fd/analysis/uq.py#L239)

```python
ecdf(frame: pd.DataFrame, column: str) -> pd.DataFrame
```

Return the empirical CDF for one output column.

**Entradas e tipos declarados**

- `frame: pd.DataFrame`
- `column: str`

**Retornos/yields explícitos**

- `pd.DataFrame(columns=['value', 'probability'])`
- `pd.DataFrame({'value': values, 'probability': np.arange(1, len(values) + 1, dtype=float) / len(values)})`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `pd.DataFrame`
- `np.sort`
- `_numeric`
- `len`
- `np.arange`

### `convergence_table`

[Implementação: source/antares_fd/analysis/uq.py:249](../../source/antares_fd/analysis/uq.py#L249)

```python
convergence_table(frame: pd.DataFrame, checkpoints: Sequence[int], criteria: Mapping[str, Mapping[str, float]], window: int=3) -> pd.DataFrame
```

Evaluate output-specific stability using existing result prefixes.

**Entradas e tipos declarados**

- `frame: pd.DataFrame`
- `checkpoints: Sequence[int]`
- `criteria: Mapping[str, Mapping[str, float]]`
- `window: int`

**Retornos/yields explícitos**

- `pd.DataFrame(rows)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `sorted`
- `int`
- `criteria.items`
- `criterion.get`
- `rows.append`
- `_numeric`
- `len`
- `str(criterion.get('derived', '')).startswith`
- `str`
- `landing_dispersion(prefix).get('ellipses', {}).get`
- `landing_dispersion(prefix).get`
- `landing_dispersion`
- `derived.endswith`
- `float`
- `ellipse.get`
- `np.quantile`
- `np.mean`
- `values.append`
- `max`
- `zip`
- `abs`
- `np.finfo`
- `changes.append`
- `all`
- `reversed`
- `row.get`
- `pd.DataFrame`

### `sensitivity_stability_table`

[Implementação: source/antares_fd/analysis/uq.py:297](../../source/antares_fd/analysis/uq.py#L297)

```python
sensitivity_stability_table(inputs: pd.DataFrame, outputs: pd.DataFrame, checkpoints: Sequence[int], output: str, top_k: int=5, window: int=3) -> pd.DataFrame
```

Track top-driver overlap and rank agreement across existing prefixes.

**Entradas e tipos declarados**

- `inputs: pd.DataFrame`
- `outputs: pd.DataFrame`
- `checkpoints: Sequence[int]`
- `output: str`
- `top_k: int`
- `window: int`

**Retornos/yields explícitos**

- `pd.DataFrame(rows)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `sorted`
- `int`
- `len`
- `spearman_sensitivity`
- `local.sort_values`
- `local['input'].tolist`
- `rankings.append`
- `rows.append`
- `','.join`
- `max`
- `zip`
- `set`
- `overlaps.append`
- `agreements.append`
- `float`
- `stats.spearmanr`
- `first.index`
- `second.index`
- `all`
- `pd.DataFrame`

### `_align_case_frames`

[Implementação: source/antares_fd/analysis/uq.py:329](../../source/antares_fd/analysis/uq.py#L329)

```python
_align_case_frames(inputs: pd.DataFrame, outputs: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]
```

Align stochastic inputs and outputs by immutable case ID.

RocketPy may preserve a one-based log index while the canonical artifact
uses zero-based case IDs.  Positional concatenation or boolean masks based
on those unrelated indexes can silently associate the wrong input with an
output, or raise Pandas' ``Unalignable boolean Series`` error.  Case ID is
the only valid join key for campaign analysis.

**Entradas e tipos declarados**

- `inputs: pd.DataFrame`
- `outputs: pd.DataFrame`

**Retornos/yields explícitos**

- `(left.loc[common].reset_index(), right.loc[common].reset_index())`
- `(inputs.reset_index(drop=True).iloc[:count].copy(), outputs.reset_index(drop=True).iloc[:count].copy())`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `inputs.drop_duplicates('case_id', keep='last').set_index`
- `inputs.drop_duplicates`
- `outputs.drop_duplicates('case_id', keep='last').set_index`
- `outputs.drop_duplicates`
- `left.index.intersection`
- `left.loc[common].reset_index`
- `right.loc[common].reset_index`
- `min`
- `len`
- `inputs.reset_index(drop=True).iloc[:count].copy`
- `inputs.reset_index`
- `outputs.reset_index(drop=True).iloc[:count].copy`
- `outputs.reset_index`

### `conditional_tail_analysis`

[Implementação: source/antares_fd/analysis/uq.py:347](../../source/antares_fd/analysis/uq.py#L347)

```python
conditional_tail_analysis(inputs: pd.DataFrame, outputs: pd.DataFrame, metric: str, quantile: float=0.99, upper: bool=True) -> pd.DataFrame
```

Compare input distributions in an extreme output tail with all cases.

**Entradas e tipos declarados**

- `inputs: pd.DataFrame`
- `outputs: pd.DataFrame`
- `metric: str`
- `quantile: float`
- `upper: bool`

**Retornos/yields explícitos**

- `pd.DataFrame()`
- `pd.DataFrame(rows).sort_values('mean_shift', key=lambda values: values.abs(), ascending=False) if rows else pd.DataFrame()`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `_align_case_frames`
- `pd.DataFrame`
- `pd.to_numeric`
- `output_values.quantile`
- `inputs.select_dtypes`
- `full.where`
- `np.isfinite`
- `full.loc[selected.to_numpy()].dropna`
- `selected.to_numpy`
- `full.dropna`
- `rows.append`
- `float`
- `full.mean`
- `tail.mean`
- `int`
- `len`
- `full.notna().sum`
- `full.notna`
- `pd.DataFrame(rows).sort_values`

### `spearman_sensitivity`

[Implementação: source/antares_fd/analysis/uq.py:369](../../source/antares_fd/analysis/uq.py#L369)

```python
spearman_sensitivity(inputs: pd.DataFrame, outputs: pd.DataFrame, output_columns: Sequence[str]) -> pd.DataFrame
```

Return rank correlations as evidence of association, never causality.

**Entradas e tipos declarados**

- `inputs: pd.DataFrame`
- `outputs: pd.DataFrame`
- `output_columns: Sequence[str]`

**Retornos/yields explícitos**

- `result`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `_align_case_frames`
- `inputs.join`
- `outputs.drop`
- `inputs.select_dtypes`
- `pd.to_numeric`
- `x.notna`
- `y.notna`
- `valid.sum`
- `x[valid].nunique`
- `stats.spearmanr`
- `rows.append`
- `float`
- `int`
- `pd.DataFrame`
- `result.groupby('output')['coefficient'].transform`
- `result.groupby`

### `compliance_analysis`

[Implementação: source/antares_fd/analysis/uq.py:392](../../source/antares_fd/analysis/uq.py#L392)

```python
compliance_analysis(frame: pd.DataFrame, requirements: Mapping[str, Mapping[str, Any]], confidence: float=0.95) -> pd.DataFrame
```

Evaluate per-case margins and exact probability confidence bounds.

**Entradas e tipos declarados**

- `frame: pd.DataFrame`
- `requirements: Mapping[str, Mapping[str, Any]]`
- `confidence: float`

**Retornos/yields explícitos**

- `pd.DataFrame(rows)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `requirements.items`
- `requirement.get`
- `pd.to_numeric`
- `float`
- `isinstance`
- `np.minimum`
- `margin.dropna`
- `int`
- `(valid >= 0).sum`
- `len`
- `probability_confidence_interval`
- `one_sided_lower_bound`
- `valid.idxmin`
- `rows.append`
- `np.percentile`
- `valid.min`
- `pd.DataFrame`

## `source/antares_fd/application/__init__.py`

Serviços locais compartilhados pela CLI e pela interface gráfica.

Módulo declarativo, ponto de entrada sem funções ou exportação de interfaces; não contém funções próprias.

## `source/antares_fd/application/cli.py`

Comandos estáveis de projeto, validação, execução, datasets e GUI.

### `register_commands`

[Implementação: source/antares_fd/application/cli.py:14](../../source/antares_fd/application/cli.py#L14)

```python
register_commands(subparsers)
```

Registre a API de aplicação na mesma árvore argparse dos comandos legados.

**Entradas e tipos declarados**

- `subparsers: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `subparsers.add_parser`
- `project.add_subparsers`
- `project_sub.add_parser`
- `new.add_argument`
- `project_sub.add_parser(name).add_argument`
- `restore.add_argument`
- `migrate.add_argument`
- `subparsers.add_parser('validate', help='validar sem consultar rede ou integrar').add_argument`
- `run.add_argument`
- `gui.add_argument`
- `importer.add_argument`
- `components.add_argument`
- `datasets.add_subparsers`
- `dataset_sub.add_parser`
- `add.add_argument`
- `results.add_subparsers`
- `result_sub.add_parser('list').add_argument`
- `result_sub.add_parser`
- `child.add_argument`
- `compare.add_argument`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `handle_command`

[Implementação: source/antares_fd/application/cli.py:75](../../source/antares_fd/application/cli.py#L75)

```python
handle_command(args, root: Path) -> int | None
```

Despache comandos novos; None deixa o fluxo legado da CLI continuar.

Erros de entrada geram JSON e código 2; validação e integridade usam código
1 quando há pendências. Falhas científicas durante execução ficam no manifesto.

**Entradas e tipos declarados**

- `args: tipo não anotado; ver contrato acima`
- `root: Path`

**Retornos/yields explícitos**

- `None`
- `code`
- `2`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `_dispatch`
- `isinstance`
- `result.get`
- `print`
- `json.dumps`
- `plain`
- `str`
- `type`

### `_dispatch`

[Implementação: source/antares_fd/application/cli.py:97](../../source/antares_fd/application/cli.py#L97)

```python
_dispatch(args, root: Path, store_class)
```

Execute uma operação de aplicação sem duplicar lógica de cálculo ou persistência.

**Entradas e tipos declarados**

- `args: tipo não anotado; ver contrato acima`
- `root: Path`
- `store_class: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `doctor(root)`
- `{'status': 'closed'}`
- `store.list()`
- `store.create(args.project, args.source)`
- `store.read(args.project)`
- `store.history(args.project)`
- `store.restore(args.project, args.revision, args.expected_revision)`
- `migrate_project(root, args.project, apply=args.apply)`
- `validate_project(root, args.project)`
- `execute_run(root, args.project, scenario=args.scenario, mode=args.mode, profile=args.profile, samples=args.samples, workers=args.workers, report=not args.no_report, run_id=args.run_id, managed=args.managed)`
- `import_design(root, args.project, args.file.read_bytes(), args.expected_revision)`
- `mass_properties(store.read(args.project)['config'].get('components', {}))`
- `read_catalog(root)`
- `verify_catalog(root)`
- `register_dataset(root, args.id, args.path, kind=args.kind, owner=args.owner, source=args.source, project=args.project)`
- `list_runs(root, args.project)`
- `read_run(root, args.project, args.run_id)`
- `verify_run(root, args.project, args.run_id)`
- `{'runs': selected, 'same_revision': len(revisions) == 1 if None not in revisions and revisions else None, 'notice': 'Comparação descritiva; verificar cenários, unidades e hipóteses antes de atribuir causas.'}`

**Exceções lançadas explicitamente**

- `ValueError('Uma das execuções selecionadas não foi encontrada.')`

**Colaboradores chamados diretamente**

- `doctor`
- `serve`
- `store_class`
- `store.list`
- `store.create`
- `store.read`
- `store.history`
- `store.restore`
- `migrate_project`
- `validate_project`
- `execute_run`
- `import_design`
- `args.file.read_bytes`
- `mass_properties`
- `store.read(args.project)['config'].get`
- `read_catalog`
- `verify_catalog`
- `register_dataset`
- `list_runs`
- `read_run`
- `verify_run`
- `len`
- `set`
- `ValueError`
- `row.get`

## `source/antares_fd/application/datasets.py`

Catálogo institucional de evidências: hashes, localização, responsáveis e verificação.

### `read_catalog`

[Implementação: source/antares_fd/application/datasets.py:15](../../source/antares_fd/application/datasets.py#L15)

```python
read_catalog(root: Path) -> dict
```

Leia metadados versionáveis sem tentar baixar ou substituir os arquivos brutos.

**Entradas e tipos declarados**

- `root: Path`

**Retornos/yields explícitos**

- `catalog`

**Exceções lançadas explicitamente**

- `ValueError('Catálogo deve declarar schema_version 1 e datasets como lista.')`
- `ValueError('Entrada de catálogo incompleta ou inválida.')`

**Colaboradores chamados diretamente**

- `contained`
- `path.exists`
- `read_mapping`
- `catalog.get`
- `isinstance`
- `ValueError`
- `any`
- `row.get`

### `register_dataset`

[Implementação: source/antares_fd/application/datasets.py:27](../../source/antares_fd/application/datasets.py#L27)

```python
register_dataset(root: Path, dataset_id: str, relative: str, *, kind: str, owner: str, source: str, project: str | None=None) -> dict
```

Registre uma evidência local por hash e responsável, sem mover ou editar sua origem.

O arquivo precisa estar contido no workspace. Mesmo ID com conteúdo diferente
é recusado; a verificação futura pode ocorrer mesmo com o bruto indisponível.

**Entradas e tipos declarados**

- `root: Path`
- `dataset_id: str`
- `relative: str`
- `kind: str`
- `owner: str`
- `source: str`
- `project: str | None`

**Retornos/yields explícitos**

- `entry`

**Exceções lançadas explicitamente**

- `ValueError('Informe tipo, responsável e origem da evidência.')`
- `ValueError('O dataset deve ser um arquivo.')`
- `ConflictError('ID já registrado. Crie uma nova revisão de evidência.')`

**Colaboradores chamados diretamente**

- `identifier`
- `isinstance`
- `owner.strip`
- `source.strip`
- `ValueError`
- `contained`
- `path.is_file`
- `ProjectStore(root).path`
- `ProjectStore`
- `path.relative_to(Path(root).resolve()).as_posix`
- `path.relative_to`
- `Path(root).resolve`
- `Path`
- `sha256`
- `path.stat`
- `datetime.now(timezone.utc).isoformat`
- `datetime.now`
- `workspace_lock`
- `read_catalog`
- `any`
- `ConflictError`
- `catalog['datasets'].append`
- `destination.parent.mkdir`
- `destination.with_suffix`
- `temporary.write_text`
- `yaml.safe_dump`
- `temporary.replace`

### `verify_catalog`

[Implementação: source/antares_fd/application/datasets.py:60](../../source/antares_fd/application/datasets.py#L60)

```python
verify_catalog(root: Path) -> dict
```

Classifique cada evidência como VERIFIED, MISSING ou CHANGED pelo conteúdo local.

**Entradas e tipos declarados**

- `root: Path`

**Retornos/yields explícitos**

- `{'valid': all((row['status'] == 'VERIFIED' for row in rows)), 'datasets': rows}`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `read_catalog`
- `contained`
- `sha256`
- `rows.append`
- `all`

## `source/antares_fd/application/jobs.py`

Supervisor local: cada simulação roda em subprocesso com cancelamento de grupo.

### `JobManager.__init__`

[Implementação: source/antares_fd/application/jobs.py:23](../../source/antares_fd/application/jobs.py#L23)

```python
JobManager.__init__(self, root: Path, max_jobs: int=2)
```

Configure capacidade limitada e recupere estados interrompidos do servidor anterior.

**Entradas e tipos declarados**

- `root: Path`
- `max_jobs: int`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- `raise (propaga a exceção ativa)`

**Colaboradores chamados diretamente**

- `Path(root).resolve`
- `Path`
- `threading.RLock`
- `workspace_lock`
- `self._lease.__enter__`
- `self._recover`
- `self._lease.__exit__`
- `sys.exc_info`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `JobManager._recover`

[Implementação: source/antares_fd/application/jobs.py:37](../../source/antares_fd/application/jobs.py#L37)

```python
JobManager._recover(self)
```

Marque jobs órfãos como INTERRUPTED sem tentar matar um PID reutilizado.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `None`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `contained`
- `results.exists`
- `results.glob`
- `candidate.relative_to`
- `json.loads`
- `path.read_text`
- `state.get`
- `state.update`
- `write_json_atomic`

### `JobManager.start`

[Implementação: source/antares_fd/application/jobs.py:52](../../source/antares_fd/application/jobs.py#L52)

```python
JobManager.start(self, project_id: str, request: dict) -> dict
```

Valide, crie um job e inicie a CLI comum sem shell e sem argumentos arbitrários.

**Entradas e tipos declarados**

- `project_id: str`
- `request: dict`

**Retornos/yields explícitos**

- `state`

**Exceções lançadas explicitamente**

- `ValueError('Parâmetros de execução desconhecidos.')`
- `ValueError('Corrija os erros de validação antes de executar.')`
- `ValueError('Cenário, modo ou perfil desconhecido.')`
- `ValueError('workers deve estar entre 1 e 64.')`
- `ValueError('samples deve estar entre 1 e 20000.')`
- `ValueError('Capacidade local atingida. Aguarde ou cancele uma execução.')`
- `raise (propaga a exceção ativa)`

**Colaboradores chamados diretamente**

- `isinstance`
- `set`
- `ValueError`
- `validate_project`
- `request.get`
- `sum`
- `process.poll`
- `self.processes.values`
- `ProjectStore(self.root).path`
- `ProjectStore`
- `new_run_id`
- `run_path`
- `path.mkdir`
- `datetime.now(timezone.utc).isoformat`
- `datetime.now`
- `write_json_atomic`
- `str`
- `command.append`
- `dict`
- `list`
- `key.startswith`
- `Path(__file__).resolve`
- `Path`
- `os.pathsep.join`
- `environment.get`
- `(path / 'job.log').open`
- `subprocess.Popen`
- `state.update`
- `type`
- `threading.Thread(target=self._watch, args=(project_id, run_id, process), daemon=True).start`
- `threading.Thread`

### `JobManager._watch`

[Implementação: source/antares_fd/application/jobs.py:105](../../source/antares_fd/application/jobs.py#L105)

```python
JobManager._watch(self, project_id: str, run_id: str, process)
```

Feche o estado de subprocessos que terminam antes de publicar o manifesto final.

**Entradas e tipos declarados**

- `project_id: str`
- `run_id: str`
- `process: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `process.wait`
- `run_path`
- `json.loads`
- `path.read_text`
- `state.get`
- `state.update`
- `write_json_atomic`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `JobManager.cancel`

[Implementação: source/antares_fd/application/jobs.py:119](../../source/antares_fd/application/jobs.py#L119)

```python
JobManager.cancel(self, project_id: str, run_id: str) -> dict
```

Encerre o grupo do worker local e publique CANCELLED, sem remover resultados parciais.

**Entradas e tipos declarados**

- `project_id: str`
- `run_id: str`

**Retornos/yields explícitos**

- `read_run(self.root, project_id, run_id)`

**Exceções lançadas explicitamente**

- `ValueError('Esta execução não está ativa neste servidor.')`

**Colaboradores chamados diretamente**

- `self.processes.get`
- `process.poll`
- `ValueError`
- `subprocess.run`
- `str`
- `os.killpg`
- `process.wait`
- `process.kill`
- `run_path`
- `json.loads`
- `path.read_text`
- `state.update`
- `datetime.now(timezone.utc).isoformat`
- `datetime.now`
- `write_json_atomic`
- `read_run`

### `JobManager.close`

[Implementação: source/antares_fd/application/jobs.py:143](../../source/antares_fd/application/jobs.py#L143)

```python
JobManager.close(self)
```

Cancele os workers ativos ao encerrar a aplicação local.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `list`
- `self.processes.items`
- `process.poll`
- `self.cancel`
- `self._lease.__exit__`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

## `source/antares_fd/application/monte_carlo.py`

Controlador Monte Carlo compartilhado; mantém o contrato legado da CLI.

### `run_campaign`

[Implementação: source/antares_fd/application/monte_carlo.py:15](../../source/antares_fd/application/monte_carlo.py#L15)

```python
run_campaign(root, project_dir, args, runner, parser, *, model_project_dir=None)
```

Execute uma campanha canônica e restaure controles em todos os caminhos.

runner seleciona o mesmo motor compartilhado para CLI/GUI; o callback legado
continua instrumentável. model_project_dir permite entradas congeladas sem
alterar a raiz de armazenamento. Falhas preservam manifestos terminais.

**Entradas e tipos declarados**

- `root: tipo não anotado; ver contrato acima`
- `project_dir: tipo não anotado; ver contrato acima`
- `args: tipo não anotado; ver contrato acima`
- `runner: tipo não anotado; ver contrato acima`
- `parser: tipo não anotado; ver contrato acima`
- `model_project_dir: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `0`

**Exceções lançadas explicitamente**

- `SystemExit(f'Campaign manifest not found: {manifest_path}')`
- `SystemExit(f'Campaign manifest has no valid requested sample count: {manifest_path}')`
- `RuntimeError('Monte Carlo scenario runner returned without terminal manifests: ' + ', '.join((f'{scenario}={status}' for scenario, status in zip(scenarios, scenario_statuses))))`
- `raise (propaga a exceção ativa)`

**Colaboradores chamados diretamente**

- `parser.error`
- `sorted`
- `Path`
- `load_project_config`
- `int`
- `mc_cfg.get`
- `tuple`
- `configured_scenario_ids`
- `getattr`
- `campaign_path_for`
- `str`
- `manifest_path.is_symlink`
- `manifest_path.exists`
- `SystemExit`
- `json.loads`
- `manifest_path.read_text`
- `manifest.get`
- `StochasticScenarioCampaign`
- `PROFILES[args.profile].get`
- `max`
- `os.environ.get`
- `campaign.snapshot_config`
- `campaign.ensure_samples`
- `registry_path.exists`
- `campaign.write_manifest`
- `len`
- `os.environ.update`
- `runner`
- `completed_scenario_ids.append`
- `campaign.scenario_manifests`
- `scenario_summaries.get(scenario_id, {}).get`
- `scenario_summaries.get`
- `any`
- `RuntimeError`
- `', '.join`
- `zip`
- `campaign.finalize_paired_comparison`
- `type`
- `campaign.scenario`
- `child_manifest_path.exists`
- `child_manifest_path.read_text`
- `child_manifest.get`
- `child_campaign.write_manifest`
- `os.environ.pop`
- `previous.items`

## `source/antares_fd/application/projects.py`

Criação, leitura e revisão de projetos com controle de alterações concorrentes.

### `read_mapping`

[Implementação: source/antares_fd/application/projects.py:22](../../source/antares_fd/application/projects.py#L22)

```python
read_mapping(path: Path) -> dict
```

Leia um YAML pequeno com raiz mapping e rejeite números não finitos.

O limite de 2 MiB protege o editor de configuração; documentos muito grandes
devem ser divididos em assets. Árvores cíclicas não pertencem ao contrato.

**Entradas e tipos declarados**

- `path: Path`

**Retornos/yields explícitos**

- `value`

**Exceções lançadas explicitamente**

- `ValueError(f'Configuração muito grande: {path.name}.')`
- `ValueError(f'{path.name}: a raiz deve ser um mapeamento.')`

**Colaboradores chamados diretamente**

- `path.stat`
- `ValueError`
- `yaml.safe_load`
- `path.read_text`
- `isinstance`
- `json.dumps`

### `input_files`

[Implementação: source/antares_fd/application/projects.py:37](../../source/antares_fd/application/projects.py#L37)

```python
input_files(project: Path) -> list[Path]
```

Liste entradas de projeto, recusando links e excluindo saídas e revisões.

**Entradas e tipos declarados**

- `project: Path`

**Retornos/yields explícitos**

- `files`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `contained`
- `directory.exists`
- `sorted`
- `directory.rglob`
- `path.relative_to`
- `safe.is_file`
- `files.append`

### `project_revision`

[Implementação: source/antares_fd/application/projects.py:50](../../source/antares_fd/application/projects.py#L50)

```python
project_revision(project: Path) -> str
```

Identifique o conteúdo das entradas, incluindo curvas e fontes importadas.

**Entradas e tipos declarados**

- `project: Path`

**Retornos/yields explícitos**

- `hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `path.relative_to(project).as_posix`
- `path.relative_to`
- `sha256`
- `input_files`
- `hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest`
- `hashlib.sha256`
- `json.dumps(records, sort_keys=True).encode`
- `json.dumps`

### `ProjectStore.__init__`

[Implementação: source/antares_fd/application/projects.py:59](../../source/antares_fd/application/projects.py#L59)

```python
ProjectStore.__init__(self, root: Path)
```

Associe o serviço à raiz existente do repositório, sem criar um projeto.

**Entradas e tipos declarados**

- `root: Path`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `Path(root).resolve`
- `Path`
- `contained`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `ProjectStore.path`

[Implementação: source/antares_fd/application/projects.py:64](../../source/antares_fd/application/projects.py#L64)

```python
ProjectStore.path(self, project_id: str) -> Path
```

Resolva um projeto por ID ignorando capitalização, sem seguir symlinks.

**Entradas e tipos declarados**

- `project_id: str`

**Retornos/yields explícitos**

- `safe`

**Exceções lançadas explicitamente**

- `FileNotFoundError(f'Projeto não encontrado: {project_id}.')`

**Colaboradores chamados diretamente**

- `identifier`
- `self.projects.iterdir`
- `path.name.lower`
- `project_id.lower`
- `contained`
- `safe.is_dir`
- `(safe / 'config').is_dir`
- `FileNotFoundError`

### `ProjectStore.list`

[Implementação: source/antares_fd/application/projects.py:74](../../source/antares_fd/application/projects.py#L74)

```python
ProjectStore.list(self) -> list[dict]
```

Retorne identificadores, nomes e estados; um projeto inválido não oculta os outros.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `rows`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `sorted`
- `self.projects.iterdir`
- `path.name.startswith`
- `path.is_symlink`
- `(path / 'config').is_dir`
- `self.read`
- `rows.append`
- `str`

### `ProjectStore.read`

[Implementação: source/antares_fd/application/projects.py:87](../../source/antares_fd/application/projects.py#L87)

```python
ProjectStore.read(self, project_id: str) -> dict
```

Leia configurações e fingerprint do projeto, preservando campos desconhecidos.

**Entradas e tipos declarados**

- `project_id: str`

**Retornos/yields explícitos**

- `self._read(project)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.path`
- `workspace_lock`
- `self._read`

### `ProjectStore._read`

[Implementação: source/antares_fd/application/projects.py:93](../../source/antares_fd/application/projects.py#L93)

```python
ProjectStore._read(self, project: Path) -> dict
```

Leia uma revisão coerente enquanto o chamador mantém o lock do projeto.

**Entradas e tipos declarados**

- `project: Path`

**Retornos/yields explícitos**

- `result`

**Exceções lançadas explicitamente**

- `ValueError('vehicle e model devem ser mapeamentos.')`

**Colaboradores chamados diretamente**

- `sorted`
- `(project / 'config').glob`
- `read_mapping`
- `contained`
- `path.relative_to`
- `config.get('vehicle', {}).get`
- `config.get`
- `config.get('model', {}).get`
- `isinstance`
- `ValueError`
- `vehicle.get`
- `model.get`
- `project_revision`
- `vehicle['mass_properties'].get`
- `mass_properties`

### `ProjectStore.create`

[Implementação: source/antares_fd/application/projects.py:114](../../source/antares_fd/application/projects.py#L114)

```python
ProjectStore.create(self, project_id: str, source: str='00_Copy_This') -> dict
```

Crie um projeto por cópia isolada das entradas, sem telemetria ou resultados.

Nomes existentes nunca são sobrescritos. A origem e sua revisão ficam no
model.yaml, e a nova montagem começa no estado DESIGN.

**Entradas e tipos declarados**

- `project_id: str`
- `source: str`

**Retornos/yields explícitos**

- `self.read(project_id)`

**Exceções lançadas explicitamente**

- `ConflictError('Já existe um projeto com este nome.')`
- `ConflictError('A origem mudou durante a cópia; crie novamente após a edição.')`

**Colaboradores chamados diretamente**

- `identifier`
- `workspace_lock`
- `any`
- `path.name.lower`
- `project_id.lower`
- `self.projects.iterdir`
- `ConflictError`
- `self.path`
- `project_revision`
- `uuid.uuid4`
- `stage.mkdir`
- `input_files`
- `path.relative_to`
- `target.parent.mkdir`
- `shutil.copy2`
- `read_mapping`
- `vehicle['vehicle'].update`
- `vehicle_path.write_text`
- `yaml.safe_dump`
- `(stage / 'config/model.yaml').write_text`
- `(stage / 'README.md').write_text`
- `stage.rename`
- `stage.exists`
- `shutil.rmtree`
- `self.read`

### `ProjectStore.history`

[Implementação: source/antares_fd/application/projects.py:155](../../source/antares_fd/application/projects.py#L155)

```python
ProjectStore.history(self, project_id: str) -> list[dict]
```

Liste revisões preservadas pelo serviço em ordem de gravação.

**Entradas e tipos declarados**

- `project_id: str`

**Retornos/yields explícitos**

- `sorted(rows, key=lambda row: row['created_utc'], reverse=True)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.path`
- `contained`
- `directory.exists`
- `sorted`
- `directory.glob`
- `path.parent.name.startswith`
- `rows.append`
- `json.loads`
- `contained(project, path.relative_to(project)).read_text`
- `path.relative_to`

### `ProjectStore._snapshot`

[Implementação: source/antares_fd/application/projects.py:167](../../source/antares_fd/application/projects.py#L167)

```python
ProjectStore._snapshot(self, project: Path, revision: str, note: str) -> None
```

Preserve as entradas anteriores à edição com hashes; não sobrescreva uma revisão.

**Entradas e tipos declarados**

- `project: Path`
- `revision: str`
- `note: str`

**Retornos/yields explícitos**

- `None`

**Exceções lançadas explicitamente**

- `ConflictError('As entradas mudaram durante a preservação da revisão.')`

**Colaboradores chamados diretamente**

- `contained`
- `destination.exists`
- `uuid.uuid4`
- `stage.mkdir`
- `input_files`
- `path.relative_to`
- `target.parent.mkdir`
- `shutil.copy2`
- `relative.as_posix`
- `sha256`
- `project_revision`
- `ConflictError`
- `write_json_atomic`
- `getpass.getuser`
- `datetime.now(timezone.utc).isoformat`
- `datetime.now`
- `stage.rename`
- `stage.exists`
- `shutil.rmtree`

### `ProjectStore.save`

[Implementação: source/antares_fd/application/projects.py:191](../../source/antares_fd/application/projects.py#L191)

```python
ProjectStore.save(self, project_id: str, config: dict, expected_revision: str, note: str='Edição local', *, assets: dict | None=None, replace_config: bool=False) -> dict
```

Grave uma edição otimista e preserve a revisão anterior.

Valida os documentos antes da primeira escrita; em falha de gravação
restaura os bytes anteriores. O lock serializa CLI e GUI no workspace.

**Entradas e tipos declarados**

- `project_id: str`
- `config: dict`
- `expected_revision: str`
- `note: str`
- `assets: dict | None`
- `replace_config: bool`

**Retornos/yields explícitos**

- `self.read(project_id)`

**Exceções lançadas explicitamente**

- `ValueError('Documento de configuração ou seção desconhecida.')`
- `ValueError('Descreva a alteração em até 2000 caracteres.')`
- `ValueError(f'{name}: informe um mapeamento.')`
- `ValueError(f'{name}: versão de schema não suportada.')`
- `ValueError('Estado deve ser DESIGN, AS_BUILT ou AS_FLOWN.')`
- `ValueError('Assets devem ser um mapeamento.')`
- `ValueError('Asset inválido ou maior que 16 MiB.')`
- `ConflictError('O projeto mudou desde sua leitura. Recarregue antes de salvar.')`
- `raise (propaga a exceção ativa)`

**Colaboradores chamados diretamente**

- `isinstance`
- `set`
- `ValueError`
- `note.strip`
- `len`
- `config.items`
- `json.dumps`
- `str`
- `document.get`
- `validate_components`
- `config.get('model', {}).get`
- `config.get`
- `model.get`
- `self.path`
- `(assets or {}).items`
- `Path`
- `contained`
- `workspace_lock`
- `identifier`
- `project_revision`
- `ConflictError`
- `self._snapshot`
- `(project / 'config').glob`
- `path.read_bytes`
- `path.unlink`
- `checked_assets.items`
- `path.relative_to`
- `path.exists`
- `path.parent.mkdir`
- `path.write_bytes`
- `path.with_name`
- `temporary.write_text`
- `yaml.safe_dump`
- `temporary.replace`
- `previous.items`
- `self.read`

### `ProjectStore.restore`

[Implementação: source/antares_fd/application/projects.py:255](../../source/antares_fd/application/projects.py#L255)

```python
ProjectStore.restore(self, project_id: str, revision: str, expected_revision: str) -> dict
```

Restaure uma revisão de configuração preservando o estado atual como histórico.

Verifica hashes das entradas arquivadas. Assets não são apagados; uma
revisão antiga de YAML pode voltar a apontar para seus arquivos originais.

**Entradas e tipos declarados**

- `project_id: str`
- `revision: str`
- `expected_revision: str`

**Retornos/yields explícitos**

- `self.save(project_id, config, expected_revision, 'Restauração de ' + revision, assets=assets, replace_config=True)`

**Exceções lançadas explicitamente**

- `ValueError('Revisão deve ser um SHA-256.')`
- `ValueError('Revisão arquivada falhou na verificação de integridade.')`

**Colaboradores chamados diretamente**

- `re_full_hash`
- `ValueError`
- `self.path`
- `contained`
- `json.loads`
- `(snapshot / 'revision.json').read_text`
- `manifest['files'].items`
- `sha256`
- `read_mapping`
- `(snapshot / 'config').glob`
- `contained(snapshot, relative, exists=True).read_bytes`
- `Path`
- `self.save`

### `re_full_hash`

[Implementação: source/antares_fd/application/projects.py:276](../../source/antares_fd/application/projects.py#L276)

```python
re_full_hash(value: str) -> bool
```

Identifique uma impressão digital SHA-256 hexadecimal de 64 caracteres.

**Entradas e tipos declarados**

- `value: str`

**Retornos/yields explícitos**

- `isinstance(value, str) and len(value) == 64 and all((c in '0123456789abcdef' for c in value))`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `isinstance`
- `len`
- `all`

## `source/antares_fd/application/runs.py`

Execução isolada, snapshots verificáveis e consulta de artefatos de campanha.

### `new_run_id`

[Implementação: source/antares_fd/application/runs.py:27](../../source/antares_fd/application/runs.py#L27)

```python
new_run_id() -> str
```

Crie um ID UTC com sufixo aleatório, independente de nomes de arquivos externos.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid.uuid4().hex[:8]`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `datetime.now(timezone.utc).strftime`
- `datetime.now`
- `uuid.uuid4`

### `run_path`

[Implementação: source/antares_fd/application/runs.py:32](../../source/antares_fd/application/runs.py#L32)

```python
run_path(root: Path, project: str, run_id: str) -> Path
```

Resolva um diretório de execução com identificadores contidos em results/.

**Entradas e tipos declarados**

- `root: Path`
- `project: str`
- `run_id: str`

**Retornos/yields explícitos**

- `contained(root, f'results/{identifier(project)}/{identifier(run_id)}')`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `contained`
- `identifier`

### `plain`

[Implementação: source/antares_fd/application/runs.py:37](../../source/antares_fd/application/runs.py#L37)

```python
plain(value)
```

Converta dataclasses/NumPy em JSON, preservando ausências como null.

Valores NaN de métricas não avaliadas viram null apenas na apresentação;
os artefatos tabulares mantêm seus indicadores de indisponibilidade.

**Entradas e tipos declarados**

- `value: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `{field.name: plain(getattr(value, field.name)) for field in dataclasses.fields(value)}`
- `{key: plain(item) for key, item in value.items()}`
- `[plain(item) for item in value]`
- `plain(value.item())`
- `None`
- `value`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `dataclasses.is_dataclass`
- `plain`
- `getattr`
- `dataclasses.fields`
- `isinstance`
- `value.items`
- `value.item`
- `np.isfinite`

### `snapshot_project`

[Implementação: source/antares_fd/application/runs.py:56](../../source/antares_fd/application/runs.py#L56)

```python
snapshot_project(root: Path, project_id: str, destination: Path) -> dict
```

Congele entradas em uma cópia autocontida e verifique hashes após copiar.

O lock é liberado antes da integração. Edições posteriores não alteram o
modelo congelado usado pelo worker; fontes originais não são reescritas.

**Entradas e tipos declarados**

- `root: Path`
- `project_id: str`
- `destination: Path`

**Retornos/yields explícitos**

- `{'revision': before, 'files': hashes}`

**Exceções lançadas explicitamente**

- `ValueError('Entrada alterada durante o snapshot: ' + str(relative))`
- `ValueError('Projeto mudou durante o snapshot.')`

**Colaboradores chamados diretamente**

- `ProjectStore`
- `workspace_lock`
- `store.path`
- `project_revision`
- `destination.mkdir`
- `input_files`
- `source.relative_to`
- `target.parent.mkdir`
- `sha256`
- `shutil.copy2`
- `ValueError`
- `str`
- `relative.as_posix`

### `_deterministic`

[Implementação: source/antares_fd/application/runs.py:82](../../source/antares_fd/application/runs.py#L82)

```python
_deterministic(snapshot: Path, output: Path, scenario: str, report: bool)
```

Integre um cenário com os construtores comuns e grave métricas e séries.

A exportação usa apenas dados desse Flight; não consulta mapas externos.
O PDF é opcional e seu erro não transforma uma integração em sucesso total.

**Entradas e tipos declarados**

- `snapshot: Path`
- `output: Path`
- `scenario: str`
- `report: bool`

**Retornos/yields explícitos**

- `metrics`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `load_project_config`
- `resolve_vehicle_mass`
- `execute_scenario`
- `archive_environment`
- `extract_flight_metrics`
- `apply_scenario`
- `plain`
- `serialized.pop`
- `write_json_atomic`
- `write_parquet_atomic`
- `pd.DataFrame`
- `atmosphere.items`
- `isinstance`
- `len`
- `arrays.values`
- `FlightDataExporter(flight).export_kml`
- `FlightDataExporter`
- `str`
- `FlightDynamicsReport(flight=flight, config=config, project_dir=snapshot, run_id=output.name).generate`
- `FlightDynamicsReport`

### `software_provenance`

[Implementação: source/antares_fd/application/runs.py:118](../../source/antares_fd/application/runs.py#L118)

```python
software_provenance(root: Path) -> dict
```

Registre intérprete, bibliotecas e lock utilizado, sem alegar identidade entre CPUs.

**Entradas e tipos declarados**

- `root: Path`

**Retornos/yields explícitos**

- `{'version': __version__, 'python': platform.python_version(), 'platform': platform.platform(), 'packages': packages, 'git': get_git_provenance(root), 'lockfile': {'path': lock.name, 'sha256': sha256(lock)} if lock.exists() else None}`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `importlib.metadata.version`
- `Path`
- `platform.python_version_tuple`
- `platform.python_version`
- `platform.platform`
- `get_git_provenance`
- `lock.exists`
- `sha256`

### `execute_run`

[Implementação: source/antares_fd/application/runs.py:133](../../source/antares_fd/application/runs.py#L133)

```python
execute_run(root: Path, project_id: str, *, scenario: str='nominal', mode: str='deterministic', profile: str='debug', samples: int | None=None, workers: int=1, report: bool=True, run_id: str | None=None, managed: bool=False) -> dict
```

Execute CLI/GUI por um contrato comum, com estados persistidos e entradas congeladas.

A GUI chama este serviço em subprocesso separado. Validação acontece antes
da aquisição meteorológica; exceções registram FAILED e são propagadas.

**Entradas e tipos declarados**

- `root: Path`
- `project_id: str`
- `scenario: str`
- `mode: str`
- `profile: str`
- `samples: int | None`
- `workers: int`
- `report: bool`
- `run_id: str | None`
- `managed: bool`

**Retornos/yields explícitos**

- `state`

**Exceções lançadas explicitamente**

- `ValueError('Cenário, modo ou perfil desconhecido.')`
- `ValueError('workers deve estar entre 1 e 64.')`
- `ValueError('samples deve estar entre 1 e 20000.')`
- `ValueError('Projeto inválido: ' + '; '.join((row['path'] + ': ' + row['message'] for row in validation['issues'] if row['severity'] == 'error')))`
- `FileExistsError('A execução já existe.')`
- `ValueError('A execução gerenciada não está na fila.')`
- `ValueError('As entradas congeladas não passaram na validação; revise o projeto.')`
- `raise (propaga a exceção ativa)`

**Colaboradores chamados diretamente**

- `ValueError`
- `isinstance`
- `validate_project`
- `'; '.join`
- `ProjectStore`
- `store.path`
- `new_run_id`
- `run_path`
- `output.exists`
- `FileExistsError`
- `json.loads`
- `(output / 'execution.json').read_text`
- `previous.get`
- `output.mkdir`
- `datetime.now(timezone.utc).isoformat`
- `datetime.now`
- `phase`
- `snapshot_project`
- `write_json_atomic`
- `software_provenance`
- `_deterministic`
- `SimpleNamespace`
- `run_campaign`
- `argparse.ArgumentParser`
- `(output / 'manifest.json').read_text`
- `path.relative_to(output).as_posix`
- `path.relative_to`
- `sha256`
- `output.rglob`
- `path.is_file`
- `state.update`
- `type`
- `str`

### `execute_run.phase`

[Implementação: source/antares_fd/application/runs.py:167](../../source/antares_fd/application/runs.py#L167)

```python
execute_run.phase(name, progress)
```

Persista progresso por fase e emita um registro legível pelo supervisor.

**Entradas e tipos declarados**

- `name: tipo não anotado; ver contrato acima`
- `progress: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `state.update`
- `write_json_atomic`
- `print`
- `json.dumps`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `execute_run.runner`

[Implementação: source/antares_fd/application/runs.py:192](../../source/antares_fd/application/runs.py#L192)

```python
execute_run.runner(_project)
```

Execute o único motor estocástico com a entrada congelada e raiz explícita.

**Entradas e tipos declarados**

- `_project: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `execute_monte_carlo(load_project_config(snapshot), snapshot, workspace_root=root, archive_atmospheres=True)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `execute_monte_carlo`
- `load_project_config`

### `list_runs`

[Implementação: source/antares_fd/application/runs.py:212](../../source/antares_fd/application/runs.py#L212)

```python
list_runs(root: Path, project_id: str) -> list[dict]
```

Liste execuções novas e legadas, mantendo status e ausência de métricas explícitos.

**Entradas e tipos declarados**

- `root: Path`
- `project_id: str`

**Retornos/yields explícitos**

- `rows`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `ProjectStore(root).path`
- `ProjectStore`
- `contained`
- `directory.exists`
- `sorted`
- `directory.iterdir`
- `path.is_symlink`
- `path.is_dir`
- `metadata_path.exists`
- `json.loads`
- `metadata_path.read_text`
- `metrics_path.exists`
- `metrics_path.read_text`
- `metadata.get`
- `_mc_summary(path, metadata).get`
- `_mc_summary`
- `rows.append`
- `metadata.get('inputs', {}).get`
- `metrics.get`
- `str`

### `_mc_summary`

[Implementação: source/antares_fd/application/runs.py:240](../../source/antares_fd/application/runs.py#L240)

```python
_mc_summary(path: Path, state: dict) -> dict
```

Leia distribuições canônicas sem confundir mediana, voo único e apogeu ASL.

A visualização reduz nuvens/ECDF a até 1000 pontos; tabelas completas
permanecem nos artefatos. Distribuições representam apenas casos válidos.

**Entradas e tipos declarados**

- `path: Path`
- `state: dict`

**Retornos/yields explícitos**

- `result`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `identifier`
- `state.get`
- `contained`
- `target.exists`
- `pd.read_parquet`
- `len`
- `plain`
- `frame[keys].iloc[::max(1, (len(frame) + 999) // 1000)].to_dict`
- `max`
- `float`
- `frame[key].median`
- `frame[key].notna().any`
- `frame[key].notna`
- `pd.concat`
- `frame.groupby`
- `reduced.to_dict`
- `frame.head(2000).to_dict`
- `frame.head`

### `read_run`

[Implementação: source/antares_fd/application/runs.py:268](../../source/antares_fd/application/runs.py#L268)

```python
read_run(root: Path, project_id: str, run_id: str) -> dict
```

Leia estado, métricas e série reduzida para visualização, sem reexecutar física.

**Entradas e tipos declarados**

- `root: Path`
- `project_id: str`
- `run_id: str`

**Retornos/yields explícitos**

- `{'run_id': run_id, 'state': state, 'metrics': metrics, 'series': series, 'campaign': campaign, 'artifacts': artifacts, 'log': log}`

**Exceções lançadas explicitamente**

- `FileNotFoundError('Execução não encontrada.')`

**Colaboradores chamados diretamente**

- `ProjectStore(root).path`
- `ProjectStore`
- `run_path`
- `path.is_dir`
- `FileNotFoundError`
- `contained`
- `state_path.exists`
- `json.loads`
- `state_path.read_text`
- `metrics_path.exists`
- `metrics_path.read_text`
- `series_path.exists`
- `pd.read_parquet`
- `max`
- `len`
- `plain`
- `frame.to_dict`
- `item.relative_to(path).as_posix`
- `item.relative_to`
- `sorted`
- `path.rglob`
- `item.is_file`
- `item.is_symlink`
- `log_path.exists`
- `log_path.open`
- `stream.seek`
- `log_path.stat`
- `stream.read().decode`
- `stream.read`
- `state.get`
- `_mc_summary`

### `verify_run`

[Implementação: source/antares_fd/application/runs.py:301](../../source/antares_fd/application/runs.py#L301)

```python
verify_run(root: Path, project_id: str, run_id: str) -> dict
```

Verifique cada hash registrado e identifique arquivos ausentes ou alterados.

**Entradas e tipos declarados**

- `root: Path`
- `project_id: str`
- `run_id: str`

**Retornos/yields explícitos**

- `{'valid': not errors, 'checked': len(manifest['files']), 'invalid': errors}`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `run_path`
- `ProjectStore(root).path`
- `ProjectStore`
- `json.loads`
- `contained(path, 'artifact_manifest.json', exists=True).read_text`
- `contained`
- `manifest['files'].items`
- `sha256`
- `errors.append`
- `len`

## `source/antares_fd/application/validation.py`

Validação central sem rede e diagnóstico de instalação para CLI e GUI.

### `validate_project`

[Implementação: source/antares_fd/application/validation.py:20](../../source/antares_fd/application/validation.py#L20)

```python
validate_project(root: Path, project_id: str) -> dict
```

Liste erros e avisos de um projeto sem adquirir atmosfera nem integrar voo.

Campos desconhecidos da versão futura são rejeitados pelo schema_version;
ausências, limites físicos e arquivos referenciados são indicados por caminho.
Assunções são permitidas e continuam visíveis como avisos de proveniência.

**Entradas e tipos declarados**

- `root: Path`
- `project_id: str`

**Retornos/yields explícitos**

- `{'valid': False, 'issues': [{'path': 'project', 'message': str(exc), 'severity': 'error'}]}`
- `{'valid': not any((row['severity'] == 'error' for row in issues)), 'issues': issues, 'project': data['id'], 'revision': data['revision'], 'stage': data['stage']}`

**Exceções lançadas explicitamente**

- `ValueError('A curva deve ser um arquivo.')`
- `ValueError('Fonte de empuxo deve ser um arquivo.')`

**Colaboradores chamados diretamente**

- `ProjectStore`
- `store.read`
- `store.path`
- `str`
- `config.items`
- `document.get`
- `issue`
- `config.get`
- `isinstance`
- `path.split`
- `parent.get`
- `vehicle.get`
- `scalar`
- `props.get`
- `mass_properties`
- `any`
- `abs`
- `validate_components`
- `vehicle.get('drag', {}).get`
- `drag.get`
- `contained(project, drag.get('file') or '__missing__', exists=True).is_file`
- `contained`
- `ValueError`
- `vehicle.get('staging', {}).get`
- `motor.get`
- `int`
- `len`
- `math.isfinite`
- `contained(project, source, exists=True).is_file`
- `vehicle.get('motor_mount', {}).get`
- `launch.get`
- `{'latitude': 90, 'longitude': 180}.get`
- `datetime.fromisoformat`
- `ZoneInfo`
- `date.get`
- `str(sections['environment'].get('type', '')).lower`
- `sections['environment'].get`
- `add_recovery_system`
- `RecoveryCollector`
- `vehicle.get('provenance', {}).get`
- `evidence.get`
- `config.get('model', {}).get`
- `model.get`
- `load_project_config`
- `build_motor`
- `build_vehicle`

### `validate_project.issue`

[Implementação: source/antares_fd/application/validation.py:28](../../source/antares_fd/application/validation.py#L28)

```python
validate_project.issue(path, message, severity='error')
```

Acrescente um diagnóstico estruturado sem ocultar erros de outros campos.

**Entradas e tipos declarados**

- `path: tipo não anotado; ver contrato acima`
- `message: tipo não anotado; ver contrato acima`
- `severity: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `issues.append`
- `str`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `validate_project.scalar`

[Implementação: source/antares_fd/application/validation.py:62](../../source/antares_fd/application/validation.py#L62)

```python
validate_project.scalar(mapping, key, prefix, minimum=None)
```

Valide um campo escalar preservando a localização no diagnóstico.

**Entradas e tipos declarados**

- `mapping: tipo não anotado; ver contrato acima`
- `key: tipo não anotado; ver contrato acima`
- `prefix: tipo não anotado; ver contrato acima`
- `minimum: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `number(mapping.get(key), prefix + '.' + key, minimum=minimum)`
- `None`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `number`
- `mapping.get`
- `issue`

### `validate_project.RecoveryCollector.add_parachute`

[Implementação: source/antares_fd/application/validation.py:170](../../source/antares_fd/application/validation.py#L170)

```python
validate_project.RecoveryCollector.add_parachute(self, **kwargs)
```

Aceite parâmetros já validados sem instalar um paraquedas real.

**Entradas e tipos declarados**

- `**kwargs: argumentos nomeados adicionais`

**Retornos/yields explícitos**

- `None`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- Nenhuma ocorrência explícita no corpo local.

### `doctor`

[Implementação: source/antares_fd/application/validation.py:198](../../source/antares_fd/application/validation.py#L198)

```python
doctor(root: Path) -> dict
```

Inspecione instalação, ferramentas e diretórios sem baixar dados ou executar voos.

**Entradas e tipos declarados**

- `root: Path`

**Retornos/yields explícitos**

- `{'healthy': not issues, 'python': platform.python_version(), 'executable': sys.executable, 'platform': platform.platform(), 'versions': versions, 'issues': issues, 'lockfile': lock.name if lock.exists() else None, 'optional': {'pytest': importlib.util.find_spec('pytest') is not None}}`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `importlib.metadata.version`
- `issues.append`
- `(Path(root) / 'projects').is_dir`
- `Path`
- `versions.get`
- `versions['rocketpy'].startswith`
- `platform.python_version`
- `platform.platform`
- `lock.exists`
- `importlib.util.find_spec`

### `migrate_project`

[Implementação: source/antares_fd/application/validation.py:220](../../source/antares_fd/application/validation.py#L220)

```python
migrate_project(root: Path, project_id: str, *, apply: bool=False) -> dict
```

Adicione metadados v1 a projetos legados por migração explícita e reversível.

A execução padrão é preview. Nenhum dado físico é modificado; apply=True
usa a revisão esperada do serviço e preserva a configuração anterior.

**Entradas e tipos declarados**

- `root: Path`
- `project_id: str`
- `apply: bool`

**Retornos/yields explícitos**

- `{'changed': False, 'message': 'Metadados já presentes.', 'revision': data['revision']}`
- `{'changed': apply, 'preview': document, 'revision': data['revision']}`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `ProjectStore`
- `store.read`
- `store.save`

## `source/antares_fd/application/workspace.py`

Caminhos contidos no workspace, hashes e exclusão mútua entre processos.

### `identifier`

[Implementação: source/antares_fd/application/workspace.py:16](../../source/antares_fd/application/workspace.py#L16)

```python
identifier(value: str) -> str
```

Valide identificadores de projeto, execução e dataset sem separadores.

Aceita até 80 letras ASCII, números, hífen ou underscore; retorna o texto.
A restrição impede que um identificador seja interpretado como caminho.

**Entradas e tipos declarados**

- `value: str`

**Retornos/yields explícitos**

- `value`

**Exceções lançadas explicitamente**

- `ValueError('Identificador: use 1–80 letras, números, hífen ou underscore.')`

**Colaboradores chamados diretamente**

- `isinstance`
- `re.fullmatch`
- `ValueError`

### `contained`

[Implementação: source/antares_fd/application/workspace.py:27](../../source/antares_fd/application/workspace.py#L27)

```python
contained(root: Path, relative: str | Path, *, exists: bool=False) -> Path
```

Resolva um caminho relativo dentro de root e rejeite links simbólicos.

Verifica contenção antes e depois da resolução e cada componente existente.
Não cria arquivos; exists=True exige que o destino já exista.

**Entradas e tipos declarados**

- `root: Path`
- `relative: str | Path`
- `exists: bool`

**Retornos/yields explícitos**

- `resolved`

**Exceções lançadas explicitamente**

- `ValueError('O caminho deve ser relativo e permanecer no workspace.')`
- `ValueError('A raiz não pode ser um link simbólico.')`
- `ValueError('Links simbólicos não são aceitos neste caminho.')`
- `ValueError('Caminho fora do workspace.')`
- `FileNotFoundError(str(relative))`

**Colaboradores chamados diretamente**

- `Path(root).absolute`
- `Path`
- `relative.is_absolute`
- `ValueError`
- `root.is_symlink`
- `candidate.is_symlink`
- `candidate.resolve`
- `resolved.is_relative_to`
- `root.resolve`
- `resolved.exists`
- `FileNotFoundError`
- `str`

### `sha256`

[Implementação: source/antares_fd/application/workspace.py:52](../../source/antares_fd/application/workspace.py#L52)

```python
sha256(path: Path) -> str
```

Calcule SHA-256 em blocos de 1 MiB sem alterar o arquivo de origem.

**Entradas e tipos declarados**

- `path: Path`

**Retornos/yields explícitos**

- `digest.hexdigest()`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `hashlib.sha256`
- `Path(path).open`
- `Path`
- `iter`
- `digest.update`
- `digest.hexdigest`

### `workspace_lock`

[Implementação: source/antares_fd/application/workspace.py:62](../../source/antares_fd/application/workspace.py#L62)

```python
workspace_lock(root: Path, key: str)
```

Serialize mutações locais usando lock do sistema operacional.

O lock tem espera limitada a cinco segundos, é liberado em finally e não
depende de apagar arquivos após crash. Funciona com fcntl e msvcrt.

**Entradas e tipos declarados**

- `root: Path`
- `key: str`

**Retornos/yields explícitos**

- `None`

**Exceções lançadas explicitamente**

- `ConflictError('Outra operação está alterando estes dados. Tente novamente.')`

**Colaboradores chamados diretamente**

- `contained`
- `directory.mkdir`
- `identifier`
- `path.open`
- `path.stat`
- `stream.write`
- `stream.flush`
- `range`
- `stream.seek`
- `msvcrt.locking`
- `stream.fileno`
- `fcntl.flock`
- `time.sleep`
- `ConflictError`

## `source/antares_fd/builders/__init__.py`

Módulo declarativo, ponto de entrada sem funções ou exportação de interfaces; não contém funções próprias.

## `source/antares_fd/builders/environment.py`

Build independent, traceable atmospheric environments for each simulation.

### `ProfileVariable.__call__`

[Implementação: source/antares_fd/builders/environment.py:23](../../source/antares_fd/builders/environment.py#L23)

```python
ProfileVariable.__call__(self, altitude)
```

Interpole uma variável atmosférica na altitude ASL solicitada.

Usa interpolação linear em altitude e mantém o valor do primeiro nível abaixo
do solo para os passos do integrador. Acima da cobertura, lança
AtmosphereUnavailableError; aceita altitude escalar ou vetor em metros.

**Entradas e tipos declarados**

- `altitude: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `np.interp(altitude, self.altitude, self.values)`

**Exceções lançadas explicitamente**

- `AtmosphereUnavailableError(f'Flight exceeded atmospheric coverage ({self.altitude[-1]} m ASL)')`

**Colaboradores chamados diretamente**

- `np.any`
- `np.asarray`
- `AtmosphereUnavailableError`
- `np.interp`

### `_base_environment`

[Implementação: source/antares_fd/builders/environment.py:35](../../source/antares_fd/builders/environment.py#L35)

```python
_base_environment(launch_config)
```

Construa o ambiente geográfico e sua data UTC a partir do lançamento.

Valida latitude, longitude, elevação e data/hora; aplica o fuso declarado
e instancia Environment com o datum configurado. Não consulta meteorologia.

**Entradas e tipos declarados**

- `launch_config: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `env`

**Exceções lançadas explicitamente**

- `ConfigurationError('launch_config is required to build Environment')`
- `ConfigurationError('launch.site requires latitude, longitude, and elevation')`
- `ConfigurationError('Invalid launch site coordinates')`
- `ConfigurationError('launch.datetime.date and time are required')`
- `ConfigurationError('Invalid date/time format. Expected YYYY-MM-DD and HH:MM:SS with a valid timezone')`

**Colaboradores chamados diretamente**

- `ConfigurationError`
- `launch_config.get`
- `site.get`
- `any`
- `np.isfinite([lat, lon, elev]).all`
- `np.isfinite`
- `cfg.get`
- `datetime.datetime.fromisoformat`
- `date.replace`
- `ZoneInfo`
- `Environment`
- `env.set_date`
- `date.astimezone`

### `_weather_time`

[Implementação: source/antares_fd/builders/environment.py:62](../../source/antares_fd/builders/environment.py#L62)

```python
_weather_time(config, launch_config, environment)
```

Resolva o instante meteorológico em formato ISO 8601 UTC.

Usa target_date/target_time quando declarados; caso contrário usa a data
do ambiente. Datas sem offset recebem o fuso do lançamento explicitamente.

**Entradas e tipos declarados**

- `config: tipo não anotado; ver contrato acima`
- `launch_config: tipo não anotado; ver contrato acima`
- `environment: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `environment.datetime_date.isoformat()`
- `value.astimezone(datetime.UTC).isoformat()`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `config.get`
- `environment.datetime_date.isoformat`
- `str`
- `datetime.datetime.fromisoformat`
- `text.replace`
- `value.replace`
- `ZoneInfo`
- `launch_config['datetime'].get`
- `value.astimezone(datetime.UTC).isoformat`
- `value.astimezone`

### `_apply_profile`

[Implementação: source/antares_fd/builders/environment.py:80](../../source/antares_fd/builders/environment.py#L80)

```python
_apply_profile(env, profile)
```

Aplique um AtmosphericProfile validado a um Environment RocketPy.

Exige cobertura do solo, instala interpoladores sem extrapolação superior
e recalcula densidade, som e viscosidade. Com umidade, corrige somente
a densidade pela equação do ar úmido. Modifica e retorna env, registrando
a proveniência e os limites verticais em antares_atmosphere.

**Entradas e tipos declarados**

- `env: tipo não anotado; ver contrato acima`
- `profile: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `env`

**Exceções lançadas explicitamente**

- `AtmosphereUnavailableError('Atmospheric profile does not cover the launch elevation')`

**Colaboradores chamados diretamente**

- `np.asarray`
- `AtmosphereUnavailableError`
- `np.column_stack`
- `env.set_atmospheric_model`
- `setattr`
- `Function`
- `ProfileVariable`
- `z.copy`
- `np.asarray(values).copy`
- `env.calculate_density_profile`
- `profile.specific_humidity_kg_kg.copy`
- `np.asarray(profile.specific_humidity_kg_kg, dtype=float).copy`
- `env.calculate_speed_of_sound_profile`
- `env.calculate_dynamic_viscosity`
- `float`
- `str`

### `_build_environments`

[Implementação: source/antares_fd/builders/environment.py:120](../../source/antares_fd/builders/environment.py#L120)

```python
_build_environments(environment_config, launch_config, ensemble)
```

Construa ambientes independentes para o perfil nominal ou ensemble.

Seleciona atmosfera padrão ou MAGI conforme environment_config. Falhas
meteorológicas abortam com AtmosphereUnavailableError, salvo fallback
explicitamente habilitado e registrado. Retorna lista de Environment.

**Entradas e tipos declarados**

- `environment_config: tipo não anotado; ver contrato acima`
- `launch_config: tipo não anotado; ver contrato acima`
- `ensemble: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `[env]`
- `[_apply_profile(_base_environment(launch_config), profile) for profile in profiles]`

**Exceções lançadas explicitamente**

- `ConfigurationError(f'Unsupported environment type: {kind}')`
- `AtmosphereUnavailableError('MAGI returned an empty atmospheric ensemble')`
- `AtmosphereUnavailableError(f'MAGI atmospheric data unavailable: {exc}')`
- `ConfigurationError('Only explicitly configured standard_atmosphere fallback is supported')`

**Colaboradores chamados diretamente**

- `_base_environment`
- `str(config.get('type', 'standard_atmosphere')).lower`
- `str`
- `config.get`
- `ConfigurationError`
- `env.set_atmospheric_model`
- `_weather_time`
- `get_atmospheric_ensemble`
- `get_atmospheric_profile`
- `AtmosphereUnavailableError`
- `_apply_profile`
- `fallback.get`
- `print`

### `build_environment`

[Implementação: source/antares_fd/builders/environment.py:164](../../source/antares_fd/builders/environment.py#L164)

```python
build_environment(environment_config, launch_config)
```

Retorne o ambiente nominal definido pelos YAMLs de atmosfera e lançamento.

Delega ao construtor comum com ensemble=False e retorna o primeiro perfil.
Erros de configuração ou de cobertura são propagados ao chamador.

**Entradas e tipos declarados**

- `environment_config: tipo não anotado; ver contrato acima`
- `launch_config: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `_build_environments(environment_config, launch_config, ensemble=False)[0]`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `_build_environments`

### `build_environment_ensemble`

[Implementação: source/antares_fd/builders/environment.py:173](../../source/antares_fd/builders/environment.py#L173)

```python
build_environment_ensemble(environment_config, launch_config)
```

Return complete profiles, including separately identified time scenarios.

**Entradas e tipos declarados**

- `environment_config: tipo não anotado; ver contrato acima`
- `launch_config: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `_build_environments(environment_config, launch_config, ensemble=True)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `_build_environments`

## `source/antares_fd/builders/motor.py`

Solid motor construction with explicit validation of the thrust curve.

### `_thrust_source`

[Implementação: source/antares_fd/builders/motor.py:12](../../source/antares_fd/builders/motor.py#L12)

```python
_thrust_source(source, project_dir)
```

Resolva a fonte de empuxo declarada sem inventar uma curva.

Aceita os formatos suportados pelo construtor, verifica arquivos relativos
a project_dir e rejeita fontes ausentes com ConfigurationError. Retorna
a fonte que será entregue ao SolidMotor.

**Entradas e tipos declarados**

- `source: tipo não anotado; ver contrato acima`
- `project_dir: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `source`
- `str(path)`
- `points`

**Exceções lançadas explicitamente**

- `ConfigurationError(f'Motor thrust file not found: {path}')`
- `ConfigurationError(f'Invalid thrust curve in {path}: require finite, increasing times and nonnegative thrust.')`

**Colaboradores chamados diretamente**

- `isinstance`
- `Path`
- `path.is_file`
- `ConfigurationError`
- `path.suffix.lower`
- `str`
- `Motor.import_eng`
- `np.asarray`
- `len`
- `np.array_equal`
- `np.isfinite(points).all`
- `np.isfinite`
- `np.any`
- `np.diff`

### `build_motor`

[Implementação: source/antares_fd/builders/motor.py:40](../../source/antares_fd/builders/motor.py#L40)

```python
build_motor(config, project_dir: Path)
```

Build a SolidMotor; reject missing data and non-finite mass/impulse.

**Entradas e tipos declarados**

- `config: tipo não anotado; ver contrato acima`
- `project_dir: Path`

**Retornos/yields explícitos**

- `motor`

**Exceções lançadas explicitamente**

- `ConfigurationError('motor configuration is missing. A motor.yaml file is required.')`
- `ConfigurationError(f"Unsupported motor type: {config.get('type')}")`
- `ConfigurationError(f"Failed to build SolidMotor: required motor fields: {', '.join(missing)}")`
- `ValueError('thrust, impulse and propellant mass/flow must be finite; impulse must be positive')`
- `ConfigurationError(f'Failed to build SolidMotor: {exc}')`

**Colaboradores chamados diretamente**

- `ConfigurationError`
- `config.get('type', 'solid').lower`
- `config.get`
- `', '.join`
- `_thrust_source`
- `SolidMotor`
- `np.unique`
- `motor.thrust`
- `motor.propellant_mass`
- `motor.total_mass_flow_rate`
- `np.isfinite(values).all`
- `np.isfinite`
- `ValueError`

## `source/antares_fd/builders/recovery.py`

### `_finite_number`

[Implementação: source/antares_fd/builders/recovery.py:5](../../source/antares_fd/builders/recovery.py#L5)

```python
_finite_number(value, field, *, minimum=None, positive=False)
```

Valide um parâmetro escalar da recuperação antes de alterar o foguete.

Converte value em float, rejeita booleanos e valores não finitos e exige
o limite mínimo informado. positive=True exige valor maior que zero.
Retorna float ou lança ConfigurationError com identificação de field.

**Entradas e tipos declarados**

- `value: tipo não anotado; ver contrato acima`
- `field: tipo não anotado; ver contrato acima`
- `minimum: tipo não anotado; ver contrato acima`
- `positive: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `number`

**Exceções lançadas explicitamente**

- `ConfigurationError(f'{field} must be a finite number')`
- `ConfigurationError(f'{field} must be positive')`
- `ConfigurationError(f'{field} must be at least {minimum}')`

**Colaboradores chamados diretamente**

- `float`
- `ConfigurationError`
- `isinstance`
- `math.isfinite`

### `_build_trigger`

[Implementação: source/antares_fd/builders/recovery.py:24](../../source/antares_fd/builders/recovery.py#L24)

```python
_build_trigger(trigger_config)
```

Translates the YAML trigger configuration into a RocketPy trigger.
RocketPy triggers can be 'apogee', a float (altitude), or a callable.

**Entradas e tipos declarados**

- `trigger_config: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `'apogee'`
- `_finite_number(value, 'recovery trigger altitude', minimum=0)`

**Exceções lançadas explicitamente**

- `ConfigurationError('recovery trigger altitude value is required')`
- `ConfigurationError('Altitude recovery triggers currently support descent only')`
- `ConfigurationError('recovery trigger time value is required')`
- `ConfigurationError('Time-based recovery triggers are not natively supported as a simple value in this builder yet. Use a custom trigger.')`
- `ConfigurationError('Custom recovery triggers are not yet implemented in the generic builder.')`
- `ConfigurationError(f'Unsupported recovery trigger type: {ttype}')`

**Colaboradores chamados diretamente**

- `trigger_config.get`
- `alt_config.get`
- `ConfigurationError`
- `_finite_number`
- `time_config.get`

### `add_recovery_system`

[Implementação: source/antares_fd/builders/recovery.py:54](../../source/antares_fd/builders/recovery.py#L54)

```python
add_recovery_system(rocket, config, *, verbose=True)
```

Adds Parachute objects to the RocketPy Rocket based on the recovery configuration.

**Entradas e tipos declarados**

- `rocket: tipo não anotado; ver contrato acima`
- `config: tipo não anotado; ver contrato acima`
- `verbose: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `None`

**Exceções lançadas explicitamente**

- `ConfigurationError('Recovery altitude_reference must be AGL')`
- `ConfigurationError(f"Unsupported recovery device type: {device.get('type')}")`
- `ConfigurationError(f"recovery device '{name}' requires cd_s or drag_coefficient + reference_area")`
- `ConfigurationError(f"recovery device '{name}' requires cd_s")`
- `ConfigurationError(f"recovery device '{name}' requires deployment lag")`
- `ConfigurationError(f'{name}.noise.time_correlation must be in [-1, 1]')`

**Colaboradores chamados diretamente**

- `print`
- `config.get`
- `settings.get`
- `ConfigurationError`
- `device.get`
- `aero.get`
- `_finite_number`
- `_build_trigger`
- `device.get('sampling', {}).get`
- `device.get('deployment', {}).get`
- `sensor_model.get('pressure', {}).get`
- `sensor_model.get`
- `sensor_model['pressure'].get`
- `validated_devices.append`
- `rocket.add_parachute`

## `source/antares_fd/builders/vehicle.py`

### `BoundedDrag.__call__`

[Implementação: source/antares_fd/builders/vehicle.py:15](../../source/antares_fd/builders/vehicle.py#L15)

```python
BoundedDrag.__call__(self, mach)
```

Avalie Cd no Mach solicitado dentro do domínio tabulado.

Rejeita Mach fora da cobertura com ConfigurationError; dentro dela, avalia
a curva configurada. Evita extrapolar um modelo aerodinâmico sem dados.

**Entradas e tipos declarados**

- `mach: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `self.curve(mach)`

**Exceções lançadas explicitamente**

- `ConfigurationError(f'Drag requested outside Mach [{self.minimum}, {self.maximum}]: {mach}')`

**Colaboradores chamados diretamente**

- `np.any`
- `np.asarray`
- `ConfigurationError`
- `self.curve`

### `_resolve_drag_source`

[Implementação: source/antares_fd/builders/vehicle.py:26](../../source/antares_fd/builders/vehicle.py#L26)

```python
_resolve_drag_source(drag_config, project_dir: Path)
```

Traduza a declaração de arrasto para uma fonte RocketPy validada.

Lê Cd constante ou tabela relativa a project_dir, valida valores e domínio
de Mach e preserva os limites de cobertura. Configuração inválida gera
ConfigurationError antes da integração do voo.

**Entradas e tipos declarados**

- `drag_config: tipo não anotado; ver contrato acima`
- `project_dir: Path`

**Retornos/yields explícitos**

- `BoundedDrag(curve, float(points[0, 0]), float(points[-1, 0]))`
- `curve`
- `float(const_val)`

**Exceções lançadas explicitamente**

- `ConfigurationError('Both power_on and power_off drag sources are required')`
- `ConfigurationError("drag source_type is 'file' but no 'file' path provided")`
- `ConfigurationError(f'Drag file not found: {full_path}')`
- `ConfigurationError(f'Unsupported drag interpolation: {interpolation}')`
- `ConfigurationError(f'Unsupported drag extrapolation: {extrapolation}')`
- `ConfigurationError(f'Invalid Mach/Cd data: {full_path}')`
- `ConfigurationError("drag source_type is 'constant' but no 'constant' provided")`
- `ConfigurationError('Constant drag must be finite and nonnegative')`
- `ConfigurationError(f'Unsupported drag source_type: {source_type}')`

**Colaboradores chamados diretamente**

- `ConfigurationError`
- `drag_config.get`
- `full_path.exists`
- `Function`
- `str`
- `np.isfinite(points).all`
- `np.isfinite`
- `len`
- `np.any`
- `np.diff`
- `BoundedDrag`
- `float`

### `build_vehicle`

[Implementação: source/antares_fd/builders/vehicle.py:69](../../source/antares_fd/builders/vehicle.py#L69)

```python
build_vehicle(vehicle_config, motor, project_dir: Path, *, verbose=True) -> Rocket
```

Construa um RocketPy Rocket pelas entradas do veículo, sem integrar voo.

Recebe configuração em SI, motor já construído e diretório das curvas.
Se o inventário de componentes estiver ativo, calcula massa/CG/tensor em
uma cópia antes de montar superfícies, trilhos e motor. Rejeita recursos
não representados pelo builder; erros físicos e de arquivo propagam-se.
verbose=False suprime a mensagem operacional para validadores/CLI JSON.
Retorna o objeto pronto para instalar recuperação e executar o cenário.

**Entradas e tipos declarados**

- `vehicle_config: tipo não anotado; ver contrato acima`
- `motor: tipo não anotado; ver contrato acima`
- `project_dir: Path`
- `verbose: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `rocket`

**Exceções lançadas explicitamente**

- `ConfigurationError('reference_area_override is not supported; provide reference_diameter')`
- `ConfigurationError(f'vehicle.{section} is not implemented')`
- `ConfigurationError('Staging requires an event model and explicit post-separation properties')`
- `ConfigurationError('vehicle.geometry.reference_diameter is required')`
- `ConfigurationError('vehicle.mass_properties.mass_without_motor is required')`
- `ConfigurationError('vehicle.mass_properties.center_of_mass_without_motor is required')`
- `ConfigurationError('vehicle.mass_properties.inertia I11, I22, I33 are required')`
- `ConfigurationError('vehicle.motor_mount.position is required')`
- `ConfigurationError('vehicle.motor_mount is enabled but no motor was supplied')`
- `ConfigurationError('Nonzero motor_mount.alignment is not implemented')`
- `ConfigurationError('vehicle.nose.length is required')`
- `ConfigurationError(f'vehicle.tails requires {field}')`
- `ConfigurationError(f"vehicle.fin_sets position is required for fin set '{f.get('name')}'")`
- `ConfigurationError(f"vehicle.fin_sets number is required for fin set '{f.get('name')}'")`
- `ConfigurationError(f'vehicle.fin_sets (trapezoidal) requires {field}')`
- `ConfigurationError(f'vehicle.fin_sets (elliptical) requires {field}')`
- `ConfigurationError(f'Unsupported fin type: {ftype}')`
- `ConfigurationError('Custom fin airfoil is not implemented by this builder')`
- `ConfigurationError('vehicle.rail_guides upper and lower positions are required')`
- `ConfigurationError(f'vehicle.eccentricities.{name} requires x and y')`

**Colaboradores chamados diretamente**

- `resolve_vehicle_mass`
- `print`
- `vehicle_config.get`
- `geometry.get`
- `ConfigurationError`
- `vehicle_config.get('staging', {}).get`
- `mass_props.get`
- `inertia_config.get`
- `_resolve_drag_source`
- `drag.get`
- `Rocket`
- `vehicle_config.get('coordinate_system', {}).get`
- `motor_mount.get`
- `rocket.add_motor`
- `any`
- `alignment.values`
- `nose.get`
- `nose.get('type', '').replace`
- `rocket.add_nose`
- `t.get`
- `rocket.add_tail`
- `f.get`
- `rocket.add_trapezoidal_fins`
- `rocket.add_elliptical_fins`
- `f.get('airfoil', {}).get`
- `rails.get`
- `rocket.set_rail_buttons`
- `vehicle_config.get('eccentricities', {}).get`
- `values.get`
- `method`

## `source/antares_fd/cli.py`

Command line entry point for Antares Flight Dynamics campaigns.

### `_project`

[Implementação: source/antares_fd/cli.py:17](../../source/antares_fd/cli.py#L17)

```python
_project(root: Path, name: str) -> Path
```

Localize um projeto pelo nome na raiz informada.

Resolve os candidatos aceitos e exige um diretório existente; retorna Path
ou lança erro de seleção antes de iniciar qualquer simulação.

**Entradas e tipos declarados**

- `root: Path`
- `name: str`

**Retornos/yields explícitos**

- `resolved`

**Exceções lançadas explicitamente**

- `SystemExit(f'Project directory cannot be a symlink: {projects_root}')`
- `SystemExit(f'Project directory cannot be a symlink: {path}')`
- `SystemExit(f'Project path resolves outside projects/: {path}')`
- `SystemExit(f'Project not found below {projects_root}: {name}')`

**Colaboradores chamados diretamente**

- `projects_root.is_symlink`
- `SystemExit`
- `projects_root.resolve`
- `projects_root.iterdir`
- `path.name.lower`
- `name.lower`
- `path.is_dir`
- `path.is_symlink`
- `path.resolve`
- `resolved.is_relative_to`

### `_run_script`

[Implementação: source/antares_fd/cli.py:39](../../source/antares_fd/cli.py#L39)

```python
_run_script(project_dir: Path) -> None
```

Execute o motor Monte Carlo comum para a entrada de compatibilidade mc.

O nome privado é mantido para extensões existentes. Carrega apenas YAML,
sem executar scripts do projeto; novos comandos run congelam as entradas.

**Entradas e tipos declarados**

- `project_dir: Path`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `execute_monte_carlo`
- `load_project_config`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `main`

[Implementação: source/antares_fd/cli.py:50](../../source/antares_fd/cli.py#L50)

```python
main(argv: list[str] | None=None) -> int
```

Execute a interface de linha de comando do Antares Flight Dynamics.

Interpreta argv com argparse e despacha campanhas, relatórios, telemetria
e reconstrução. Valida caminhos e opções antes de executar o fluxo escolhido;
restaura variáveis de ambiente temporárias e retorna o código de saída.
Comandos de análise leem artefatos; comandos de simulação geram novos resultados.

**Entradas e tipos declarados**

- `argv: list[str] | None`

**Retornos/yields explícitos**

- `handled`
- `0`
- `2`
- `run_campaign(root, _project(root, args.project), args, _run_script, parser)`

**Exceções lançadas explicitamente**

- `SystemExit(f'Campaign manifest not found: {manifest_path}')`
- `SystemExit(f'Campaign not found: {campaign_path}')`
- `SystemExit('Pass --section when project metadata does not declare exactly one marker')`

**Colaboradores chamados diretamente**

- `argparse.ArgumentParser`
- `parser.add_argument`
- `parser.add_subparsers`
- `subparsers.add_parser`
- `mc.add_argument`
- `report.add_argument`
- `archive.add_argument`
- `telemetry.add_subparsers`
- `telemetry_subparsers.add_parser`
- `telemetry_audit.add_argument`
- `telemetry_process.add_argument`
- `register_commands`
- `parser.parse_args`
- `Path(args.repo_root or os.environ.get('ANTARES_FD_ROOT') or Path(__file__).resolve().parents[2]).resolve`
- `Path`
- `os.environ.get`
- `Path(__file__).resolve`
- `handle_command`
- `(root / 'projects').is_dir`
- `parser.error`
- `_project`
- `campaign_path_for`
- `str`
- `manifest_path.is_symlink`
- `manifest_path.is_file`
- `SystemExit`
- `MonteCarloCampaign`
- `print`
- `campaign.archive`
- `campaign_path.exists`
- `FlightDynamicsReport.from_artifacts(campaign_path, project_dir=project_dir).generate`
- `FlightDynamicsReport.from_artifacts`
- `audit_project`
- `yaml.safe_load`
- `metadata_path.read_text`
- `metadata.get`
- `len`
- `process_audit_section`
- `run_campaign`

## `source/antares_fd/config/__init__.py`

Módulo declarativo, ponto de entrada sem funções ou exportação de interfaces; não contém funções próprias.

## `source/antares_fd/config/exceptions.py`

Módulo declarativo, ponto de entrada sem funções ou exportação de interfaces; não contém funções próprias.

## `source/antares_fd/config/input_files.py`

Resolve project-local files that directly affect flight model execution.

### `_project_file`

[Implementação: source/antares_fd/config/input_files.py:11](../../source/antares_fd/config/input_files.py#L11)

```python
_project_file(project_dir: Path, relative: Any) -> Path
```

Resolva uma referência de entrada dentro do diretório do projeto.

Normaliza relative e verifica contenção e existência do arquivo. Retorna
Path ou lança ValueError ou FileNotFoundError, evitando snapshots de caminhos externos.

**Entradas e tipos declarados**

- `project_dir: Path`
- `relative: Any`

**Retornos/yields explícitos**

- `path`

**Exceções lançadas explicitamente**

- `ValueError('Model input path must be nonempty relative text')`
- `ValueError(f'Model input is outside project: {relative}')`
- `FileNotFoundError(f'Model input is missing: {relative}')`

**Colaboradores chamados diretamente**

- `isinstance`
- `relative.strip`
- `ValueError`
- `project_dir.resolve`
- `(project_root / relative).resolve`
- `path.is_relative_to`
- `path.is_file`
- `FileNotFoundError`

### `_mapping`

[Implementação: source/antares_fd/config/input_files.py:28](../../source/antares_fd/config/input_files.py#L28)

```python
_mapping(path: Path) -> dict[str, Any]
```

Leia um documento YAML que deve conter um mapeamento.

Usa safe_load no arquivo path e rejeita estruturas incompatíveis. O retorno
é usado apenas para descobrir entradas referenciadas pelo modelo.

**Entradas e tipos declarados**

- `path: Path`

**Retornos/yields explícitos**

- `value`

**Exceções lançadas explicitamente**

- `ValueError(f'Model configuration must contain a mapping: {path}')`

**Colaboradores chamados diretamente**

- `yaml.safe_load`
- `path.read_text`
- `isinstance`
- `ValueError`

### `collect_project_model_inputs`

[Implementação: source/antares_fd/config/input_files.py:40](../../source/antares_fd/config/input_files.py#L40)

```python
collect_project_model_inputs(project_dir: Path) -> tuple[Path, ...]
```

List config YAML plus the configured thrust and file-backed drag curves.

Paths are resolved within the project directory. A referenced symlink may
point within the project, but references that resolve outside it are
rejected so snapshots remain portable and bounded.

**Entradas e tipos declarados**

- `project_dir: Path`

**Retornos/yields explícitos**

- `tuple(sorted(inputs))`

**Exceções lançadas explicitamente**

- `FileNotFoundError(f'No YAML configuration files in {config_dir}')`
- `ValueError(f'Motor configuration must contain a mapping: {motor_path}')`
- `ValueError(f'Vehicle configuration must contain a mapping: {vehicle_path}')`
- `ValueError(f'Vehicle drag configuration must contain a mapping: {vehicle_path}')`
- `ValueError(f'Vehicle {mode} drag configuration must contain a mapping: {vehicle_path}')`

**Colaboradores chamados diretamente**

- `Path(project_dir).resolve`
- `Path`
- `sorted`
- `_project_file`
- `path.relative_to(project_root).as_posix`
- `path.relative_to`
- `config_dir.glob`
- `FileNotFoundError`
- `set`
- `motor_path.is_file`
- `_mapping`
- `motor.get`
- `isinstance`
- `ValueError`
- `inputs.add`
- `vehicle_path.is_file`
- `vehicle.get`
- `drag.get`
- `entry.get`
- `tuple`

## `source/antares_fd/config/loader.py`

### `_load_yaml_file`

[Implementação: source/antares_fd/config/loader.py:8](../../source/antares_fd/config/loader.py#L8)

```python
_load_yaml_file(file_path: Path) -> dict
```

Leia um arquivo YAML UTF-8 com raiz do tipo mapeamento.

Arquivo vazio retorna dict vazio. Arquivo ausente, YAML malformado ou raiz
incompatível gera ConfigurationError com identificação do arquivo.

**Entradas e tipos declarados**

- `file_path: Path`

**Retornos/yields explícitos**

- `{}`
- `data`

**Exceções lançadas explicitamente**

- `ConfigurationError(f'Configuration file not found: {file_path}')`
- `ConfigurationError(f'YAML root must be a mapping in {file_path}')`
- `ConfigurationError(f'Malformed YAML in {file_path}: {e}')`

**Colaboradores chamados diretamente**

- `file_path.exists`
- `ConfigurationError`
- `file_path.open`
- `yaml.safe_load`
- `isinstance`

### `_dict_to_config_dict`

[Implementação: source/antares_fd/config/loader.py:28](../../source/antares_fd/config/loader.py#L28)

```python
_dict_to_config_dict(d: Any) -> Any
```

Converta uma árvore YAML para contêineres com acesso por atributos.

Reconstrói dicionários como ConfigDict e listas como listas, preservando
escalares e None. A conversão é recursiva e não altera a árvore de entrada.

**Entradas e tipos declarados**

- `d: Any`

**Retornos/yields explícitos**

- `ConfigDict({k: _dict_to_config_dict(v) for k, v in d.items()})`
- `[_dict_to_config_dict(v) for v in d]`
- `d`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `isinstance`
- `ConfigDict`
- `_dict_to_config_dict`
- `d.items`

### `load_project_config`

[Implementação: source/antares_fd/config/loader.py:40](../../source/antares_fd/config/loader.py#L40)

```python
load_project_config(project_dir: Path) -> ProjectConfig
```

Loads all relevant YAML configuration files from a project directory
and returns a unified ProjectConfig object.

Raises:
    ConfigurationError: If required files are missing or malformed.

**Entradas e tipos declarados**

- `project_dir: Path`

**Retornos/yields explícitos**

- `ProjectConfig(vehicle=vehicle_config, recovery=recovery_config, launch=launch_config, motor=motor_config, environment=environment_config, simulation=simulation_config, monte_carlo=monte_carlo_config)`

**Exceções lançadas explicitamente**

- `ConfigurationError(f'Config directory not found at {config_dir}')`
- `ConfigurationError('vehicle.yaml is missing required field: name')`

**Colaboradores chamados diretamente**

- `config_dir.exists`
- `ConfigurationError`
- `_load_yaml_file`
- `vehicle_raw.get`
- `recovery_raw.get`
- `launch_raw.get`
- `_dict_to_config_dict`
- `components_path.exists`
- `vehicle_config.get('mass_properties', {}).get`
- `vehicle_config.get`
- `components.get`
- `getattr`
- `(config_dir / 'motor.yaml').exists`
- `motor_raw.get`
- `(config_dir / 'environment.yaml').exists`
- `env_raw.get`
- `(config_dir / 'simulation.yaml').exists`
- `sim_raw.get`
- `(config_dir / 'monte_carlo.yaml').exists`
- `mc_raw.get`
- `ProjectConfig`

## `source/antares_fd/config/models.py`

### `ConfigDict.__getattr__`

[Implementação: source/antares_fd/config/models.py:9](../../source/antares_fd/config/models.py#L9)

```python
ConfigDict.__getattr__(self, name: str) -> Any
```

Leia uma chave pelo acesso de atributo.

Retorna self[name]; chave ausente gera AttributeError para manter o contrato
de getattr e hasattr, sem fabricar um valor padrão.

**Entradas e tipos declarados**

- `name: str`

**Retornos/yields explícitos**

- `self[name]`

**Exceções lançadas explicitamente**

- `AttributeError(f"'ConfigDict' object has no attribute '{name}'")`

**Colaboradores chamados diretamente**

- `AttributeError`

### `ConfigDict.__setattr__`

[Implementação: source/antares_fd/config/models.py:20](../../source/antares_fd/config/models.py#L20)

```python
ConfigDict.__setattr__(self, name: str, value: Any) -> None
```

Grave um atributo como chave do dicionário de configuração.

Atribui value em self[name] e retorna None. A operação modifica a instância
e mantém acesso por chave e por atributo sobre o mesmo armazenamento.

**Entradas e tipos declarados**

- `name: str`
- `value: Any`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- Nenhuma ocorrência explícita no corpo local.

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

## `source/antares_fd/design/__init__.py`

Contratos de componentes, propriedades de massa e importação rastreável.

Módulo declarativo, ponto de entrada sem funções ou exportação de interfaces; não contém funções próprias.

## `source/antares_fd/design/components.py`

Propriedades de massa de uma lista explícita de componentes em SI.

A posição axial cresce do bico para a cauda. O tensor usa os eixos do
RocketPy: I11/I22 transversais e I33 longitudinal, com produtos I12/I13/I23.
Motor e propelente ficam fora da massa do veículo para impedir dupla contagem.

### `number`

[Implementação: source/antares_fd/design/components.py:21](../../source/antares_fd/design/components.py#L21)

```python
number(value: Any, field: str, *, minimum: float | None=None) -> float
```

Exija um escalar finito, rejeitando booleanos e limites inferiores inválidos.

**Entradas e tipos declarados**

- `value: Any`
- `field: str`
- `minimum: float | None`

**Retornos/yields explícitos**

- `float(value)`

**Exceções lançadas explicitamente**

- `ConfigurationError(f'{field}: informe um número finito.')`
- `ConfigurationError(f'{field}: mínimo {minimum}.')`

**Colaboradores chamados diretamente**

- `isinstance`
- `math.isfinite`
- `ConfigurationError`
- `float`

### `validate_components`

[Implementação: source/antares_fd/design/components.py:30](../../source/antares_fd/design/components.py#L30)

```python
validate_components(document: dict, *, complete: bool=False) -> list[str]
```

Valide a lista de componentes sem transformar ausências em números.

Em edição, null é aceito e retornado como pendência; complete=True exige
cobertura COMPLETE e todos os dados necessários à soma de massa e tensor.
Valores presentes inválidos sempre geram ConfigurationError.

**Entradas e tipos declarados**

- `document: dict`
- `complete: bool`

**Retornos/yields explícitos**

- `pending`

**Exceções lançadas explicitamente**

- `ConfigurationError('components.schema_version deve ser 1.')`
- `ConfigurationError('components.coverage deve ser COMPLETE ou PARTIAL.')`
- `ConfigurationError('components deve ser uma lista com até 10000 itens.')`
- `ConfigurationError(f'components[{index}] deve ser um mapeamento.')`
- `ConfigurationError('Cada componente precisa de id único não vazio.')`
- `ConfigurationError(f'{key}: categoria desconhecida.')`
- `ConfigurationError(f'{key}: proveniência desconhecida.')`
- `ConfigurationError(f'{key}.included deve ser booleano.')`
- `ConfigurationError(f'{key}: modelo de inércia desconhecido.')`
- `ConfigurationError(f'{key}.geometry deve ser mapeamento.')`
- `raise (propaga a exceção ativa)`
- `ConfigurationError(f'{key}.radial_position_m exige dois valores.')`
- `ConfigurationError('Inventário incompleto: ' + '; '.join(pending or ['lista vazia']))`

**Colaboradores chamados diretamente**

- `isinstance`
- `str`
- `document.get`
- `ConfigurationError`
- `len`
- `set`
- `pending.append`
- `enumerate`
- `row.get`
- `key.strip`
- `seen.add`
- `provenance.get`
- `number`
- `geometry.get`
- `missing_geometry.append`
- `intrinsic_inertia`
- `'; '.join`

### `intrinsic_inertia`

[Implementação: source/antares_fd/design/components.py:105](../../source/antares_fd/design/components.py#L105)

```python
intrinsic_inertia(component: dict) -> np.ndarray
```

Obtenha o tensor local por declaração explícita ou geometria analítica.

Modelos aceitos: provided, point_mass, solid_cylinder, hollow_cylinder e
box. O centro local já deve ser o CG; posições não são somadas aqui.

**Entradas e tipos declarados**

- `component: dict`

**Retornos/yields explícitos**

- `tensor`
- `np.zeros((3, 3))`
- `np.diag([transverse, transverse, axial])`
- `np.diag([mass * (height ** 2 + length ** 2) / 12, mass * (width ** 2 + length ** 2) / 12, mass * (width ** 2 + height ** 2) / 12])`

**Exceções lançadas explicitamente**

- `ConfigurationError(f"{component.get('id')}.inertia_kg_m2 exige seis valores.")`
- `ConfigurationError('Tensor de inércia não representa uma distribuição de massa física.')`
- `ConfigurationError('Raios interno/externo incompatíveis com o modelo.')`
- `ConfigurationError(f'Modelo de inércia não suportado: {model}.')`

**Colaboradores chamados diretamente**

- `component.get`
- `isinstance`
- `len`
- `ConfigurationError`
- `number`
- `np.array`
- `np.linalg.eigvalsh`
- `eigenvalues.min`
- `eigenvalues.max`
- `eigenvalues.sum`
- `np.zeros`
- `geometry.get`
- `np.diag`

### `mass_properties`

[Implementação: source/antares_fd/design/components.py:145](../../source/antares_fd/design/components.py#L145)

```python
mass_properties(document: dict) -> dict
```

Some massas e tensores pelo teorema dos eixos paralelos, sem incluir motor.

Exige inventário completo; calcula CG tridimensional e transporta cada
tensor ao CG agregado. Retorna massa, posição axial, offset radial e seis
entradas do tensor, mantendo a convenção RocketPy explícita.

**Entradas e tipos declarados**

- `document: dict`

**Retornos/yields explícitos**

- `{'mass_without_motor': total, 'center_of_mass_without_motor': float(center[2]), 'radial_center_of_mass_m': center[:2].tolist(), 'inertia': dict(zip(('I11', 'I22', 'I33', 'I12', 'I13', 'I23'), map(float, inertia))), 'component_count': len(rows), 'method': 'components'}`

**Exceções lançadas explicitamente**

- `ConfigurationError('A massa sem motor deve ser positiva.')`

**Colaboradores chamados diretamente**

- `validate_components`
- `row.get`
- `math.fsum`
- `ConfigurationError`
- `np.array`
- `sum`
- `zip`
- `np.zeros`
- `intrinsic_inertia`
- `np.dot`
- `np.eye`
- `np.outer`
- `float`
- `center[:2].tolist`
- `dict`
- `map`
- `len`

### `resolve_vehicle_mass`

[Implementação: source/antares_fd/design/components.py:171](../../source/antares_fd/design/components.py#L171)

```python
resolve_vehicle_mass(vehicle: dict) -> dict
```

Materialize propriedades agregadas de componentes em uma cópia do veículo.

Mantém o caminho legado para method diferente de components. Componentes
não são adicionados novamente como payloads; o agregado é passado ao Rocket.
CG radial não nulo é rejeitado até existir montagem equivalente no builder.

**Entradas e tipos declarados**

- `vehicle: dict`

**Retornos/yields explícitos**

- `result`

**Exceções lançadas explicitamente**

- `ConfigurationError('CG radial não nulo exige um modelo explícito de excentricidade.')`

**Colaboradores chamados diretamente**

- `copy.deepcopy`
- `result.get('mass_properties', {}).get`
- `result.get`
- `mass_properties`
- `any`
- `abs`
- `properties.pop`
- `ConfigurationError`

## `source/antares_fd/design/openrocket.py`

Leitura conservadora de OpenRocket: conserva fonte e identifica lacunas.

Referências: especificação .ork e savers oficiais do OpenRocket. O parser não
executa Java nem presume equivalência de aerodinâmica, recuperação ou motores.

### `design_xml`

[Implementação: source/antares_fd/design/openrocket.py:28](../../source/antares_fd/design/openrocket.py#L28)

```python
design_xml(content: bytes) -> bytes
```

Leia XML, ZIP ou GZip com limites de expansão e sem extrair arquivos.

Rejeita DTD/entities, múltiplos candidatos, arquivos cifrados, profundidade
e nós excessivos. Nenhum nome do ZIP é usado como caminho de escrita.

**Entradas e tipos declarados**

- `content: bytes`

**Retornos/yields explícitos**

- `content`

**Exceções lançadas explicitamente**

- `ValueError('Arquivo OpenRocket vazio ou maior que 16 MiB.')`
- `ValueError('Arquivo compactado excede os limites de expansão.')`
- `ValueError('O ZIP deve conter um único documento de projeto não cifrado.')`
- `ValueError('XML com DTD/entities ou tamanho não permitido.')`

**Colaboradores chamados diretamente**

- `len`
- `ValueError`
- `io.BytesIO`
- `zipfile.is_zipfile`
- `zipfile.ZipFile`
- `archive.infolist`
- `sum`
- `Path`
- `item.filename.endswith`
- `archive.read`
- `content.startswith`
- `gzip.GzipFile`
- `content.upper`

### `numeric`

[Implementação: source/antares_fd/design/openrocket.py:55](../../source/antares_fd/design/openrocket.py#L55)

```python
numeric(element: ET.Element, name: str, default=None)
```

Leia um número explícito; auto e expressões desconhecidas permanecem ausentes.

**Entradas e tipos declarados**

- `element: ET.Element`
- `name: str`
- `default: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `default`
- `None`
- `value if math.isfinite(value) else None`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `element.findtext`
- `float`
- `math.isfinite`

### `absolute_start`

[Implementação: source/antares_fd/design/openrocket.py:67](../../source/antares_fd/design/openrocket.py#L67)

```python
absolute_start(element, parent_start, parent_length, previous_end, length)
```

Resolva posição top/bottom/middle/after/absolute mantendo offsets em metros.

Referências que exigem comprimentos ausentes retornam None. Geometria de
pods, clusters ou estágios paralelos é tratada como não suportada.

**Entradas e tipos declarados**

- `element: tipo não anotado; ver contrato acima`
- `parent_start: tipo não anotado; ver contrato acima`
- `parent_length: tipo não anotado; ver contrato acima`
- `previous_end: tipo não anotado; ver contrato acima`
- `length: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `None`
- `offset`
- `None if previous_end is None else previous_end + offset`
- `parent_start + offset`
- `parent_start + (parent_length - length) * fraction + offset`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `element.find`
- `position.get('method', position.get('type', 'top')).lower`
- `position.get`
- `float`
- `math.isfinite`

### `component_row`

[Implementação: source/antares_fd/design/openrocket.py:101](../../source/antares_fd/design/openrocket.py#L101)

```python
component_row(element, key, parent, start, length)
```

Extraia componente, overrides e material sem fabricar propriedades ausentes.

Cilindros com raio, comprimento e densidade explícitos recebem massa e
tensor analíticos. Outras formas preservam campos, exigindo revisão antes
de usar o inventário como uma montagem completa.

**Entradas e tipos declarados**

- `element: tipo não anotado; ver contrato acima`
- `key: tipo não anotado; ver contrato acima`
- `parent: tipo não anotado; ver contrato acima`
- `start: tipo não anotado; ver contrato acima`
- `length: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `row`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `element.find`
- `numeric`
- `material.get`
- `float`
- `math.isfinite`
- `math.radians`
- `element.findtext`
- `math.cos`
- `math.sin`

### `parse_openrocket`

[Implementação: source/antares_fd/design/openrocket.py:150](../../source/antares_fd/design/openrocket.py#L150)

```python
parse_openrocket(content: bytes) -> dict
```

Extraia uma árvore .ork com relatório de cobertura e identidade SHA-256.

Preserva todos os componentes, inclusive não suportados. Overrides de
assembleia, múltiplas instâncias, formas sem tensor e posições ambíguas
impedem a marcação COMPLETE. A curva de empuxo não é inferida.

**Entradas e tipos declarados**

- `content: bytes`

**Retornos/yields explícitos**

- `{'name': rocket.findtext('name', 'Importação OpenRocket'), 'sha256': digest, 'creator': root.get('creator'), 'format_version': root.get('version'), 'components': document, 'mass_properties': properties, 'unsupported': unsupported, 'warnings': warnings, 'pending': pending[1:], 'motor_configurations_xml': motors, 'review_required': True, 'limitations': ['Curvas Cd(Mach) e empuxo exigem fontes independentes.', 'Importação não prova equivalência numérica com OpenRocket.']}`

**Exceções lançadas explicitamente**

- `ValueError('Arquivo OpenRocket inválido: ' + str(exc))`
- `ValueError('Documento não contém um foguete OpenRocket.')`
- `ValueError('Árvore XML excede limites de nós/profundidade.')`

**Colaboradores chamados diretamente**

- `hashlib.sha256(content).hexdigest`
- `hashlib.sha256`
- `ET.fromstring`
- `design_xml`
- `ValueError`
- `str`
- `root.find`
- `stack.pop`
- `stack.extend`
- `set`
- `visit`
- `validate_components`
- `len`
- `any`
- `mass_properties`
- `warnings.append`
- `ET.tostring`
- `rocket.findall`
- `rocket.findtext`
- `root.get`

### `parse_openrocket.visit`

[Implementação: source/antares_fd/design/openrocket.py:173](../../source/antares_fd/design/openrocket.py#L173)

```python
parse_openrocket.visit(element, parent, parent_start, parent_length, previous_end)
```

Percorra a montagem e mantenha a referência local de cada componente.

**Entradas e tipos declarados**

- `element: tipo não anotado; ver contrato acima`
- `parent: tipo não anotado; ver contrato acima`
- `parent_start: tipo não anotado; ver contrato acima`
- `parent_length: tipo não anotado; ver contrato acima`
- `previous_end: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `end`

**Exceções lançadas explicitamente**

- `ValueError('IDs duplicados no documento OpenRocket.')`

**Colaboradores chamados diretamente**

- `element.findtext`
- `len`
- `ValueError`
- `ids.add`
- `numeric`
- `absolute_start`
- `component_row`
- `unsupported.append`
- `any`
- `element.findtext(flag, 'false').lower`
- `warnings.append`
- `element.find`
- `rows.append`
- `element.findall`
- `visit`
- `max`

### `import_design`

[Implementação: source/antares_fd/design/openrocket.py:228](../../source/antares_fd/design/openrocket.py#L228)

```python
import_design(root: Path, project_id: str, content: bytes, expected_revision: str) -> dict
```

Importe um .ork preservando seus bytes e exigindo revisão explícita do modelo.

Geometria externa suportada é mapeada para o builder. Propriedades antigas
de massa e montagem do motor não são reutilizadas após a importação.

**Entradas e tipos declarados**

- `root: Path`
- `project_id: str`
- `content: bytes`
- `expected_revision: str`

**Retornos/yields explícitos**

- `{'project': updated, 'report': report}`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `parse_openrocket`
- `ProjectStore`
- `store.read`
- `copy.deepcopy`
- `ET.Element`
- `fields.items`
- `ET.SubElement`
- `ends.append`
- `numeric`
- `radii.append`
- `element.findtext`
- `{'haack': 'vonkarman', 'conical': 'conical', 'ogive': 'ogive', 'ellipsoid': 'elliptical'}.get`
- `report['warnings'].append`
- `vehicle['fin_sets'].append`
- `max`
- `config.setdefault`
- `model.update`
- `motor.update`
- `store.save`
- `json.dumps(report, ensure_ascii=False, indent=2).encode`
- `json.dumps`

## `source/antares_fd/design/variants.py`

Transformações de montagem explícitas, sem efeitos no projeto original.

### `transform_components`

[Implementação: source/antares_fd/design/variants.py:10](../../source/antares_fd/design/variants.py#L10)

```python
transform_components(document: dict, *, swap: list[str] | None=None, structural_factor: float=1.0) -> dict
```

Troque posições axiais e escale massas estruturais em uma cópia do inventário.

swap contém dois IDs distintos com posições conhecidas. O fator aplica-se
somente a estruturas incluídas; tensores informados escalam linearmente,
sob hipótese explícita de geometria conservada. Dados ausentes bloqueiam
a transformação necessária; nenhum motor/empuxo é inferido ou modificado.

**Entradas e tipos declarados**

- `document: dict`
- `swap: list[str] | None`
- `structural_factor: float`

**Retornos/yields explícitos**

- `result`

**Exceções lançadas explicitamente**

- `ConfigurationError('structural_factor deve ser no máximo 2.')`
- `ConfigurationError('Selecione dois IDs de componentes distintos.')`
- `ConfigurationError('Componente da troca não encontrado.')`

**Colaboradores chamados diretamente**

- `validate_components`
- `number`
- `ConfigurationError`
- `deepcopy`
- `isinstance`
- `len`
- `next`
- `any`
- `row.get`
- `', '.join`

## `source/antares_fd/environment/__init__.py`

Módulo declarativo, ponto de entrada sem funções ou exportação de interfaces; não contém funções próprias.

## `source/antares_fd/environment/archive.py`

Arquivos autocontidos das condições atmosféricas efetivamente integradas.

### `archive_environment`

[Implementação: source/antares_fd/environment/archive.py:10](../../source/antares_fd/environment/archive.py#L10)

```python
archive_environment(environment, output: Path)
```

Preserve variáveis do ambiente efetivamente integrado e sua cobertura.

Perfis MAGI mantêm os níveis originais. Atmosfera analítica usa uma grade
amostrada identificada como tal; configuração e versão fixam sua equação.
Não reacquire previsão nem extrapola além da cobertura declarada.

**Entradas e tipos declarados**

- `environment: tipo não anotado; ver contrato acima`
- `output: Path`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `output.mkdir`
- `getattr`
- `isinstance`
- `np.linspace`
- `float`
- `np.asarray`
- `np.array`
- `function`
- `len`
- `write_parquet_atomic`
- `pd.DataFrame`
- `write_json_atomic`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

## `source/antares_fd/environment/atmosphere.py`

### `AtmosphericProfile.__post_init__`

[Implementação: source/antares_fd/environment/atmosphere.py:26](../../source/antares_fd/environment/atmosphere.py#L26)

```python
AtmosphericProfile.__post_init__(self)
```

Valide e copie vetores atmosféricos unidimensionais em unidades SI.

Cada campo recebe uma cópia numérica somente para leitura, com pelo
menos dois níveis finitos. Altitude deve crescer e pressão decrescer;
temperatura e pressão devem ser positivas. Umidade específica, quando
presente, deve pertencer a [0, 1). Falhas geram ConfigurationError
antes da construção do ambiente RocketPy.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- `ConfigurationError(f'Array {name} must be numeric')`
- `ConfigurationError(f'Array {name} must be one-dimensional')`
- `ConfigurationError('Atmospheric profile must have at least 2 altitude levels.')`
- `ConfigurationError(f'Array {name} length ({len(arr)}) does not match altitude length ({n}).')`
- `ConfigurationError(f'Array {name} contains NaN or Inf values.')`
- `ConfigurationError('Altitude array is not strictly monotonically increasing.')`
- `ConfigurationError('Pressure array contains non-positive values.')`
- `ConfigurationError('Temperature array contains non-positive values.')`
- `ConfigurationError('Pressure must decrease strictly with altitude.')`
- `ConfigurationError('Specific humidity requires one finite value in [0, 1) per level')`

**Colaboradores chamados diretamente**

- `np.array`
- `getattr`
- `ConfigurationError`
- `vector.setflags`
- `object.__setattr__`
- `len`
- `np.isnan(arr).any`
- `np.isnan`
- `np.isinf(arr).any`
- `np.isinf`
- `np.all`
- `np.diff`
- `np.any`
- `np.asarray`
- `np.isfinite(q).all`
- `np.isfinite`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

## `source/antares_fd/gui/__init__.py`

Estação de trabalho local servida em loopback, sem dependência de nuvem.

Módulo declarativo, ponto de entrada sem funções ou exportação de interfaces; não contém funções próprias.

## `source/antares_fd/gui/server.py`

GUI local com API comum, arquivos contidos e proteção contra requisições externas.

### `LocalApplication.__init__`

[Implementação: source/antares_fd/gui/server.py:31](../../source/antares_fd/gui/server.py#L31)

```python
LocalApplication.__init__(self, root: Path)
```

Associe os serviços à raiz e crie um token efêmero por inicialização.

**Entradas e tipos declarados**

- `root: Path`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `Path(root).resolve`
- `Path`
- `ProjectStore`
- `JobManager`
- `secrets.token_hex`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `LocalApplication.get`

[Implementação: source/antares_fd/gui/server.py:38](../../source/antares_fd/gui/server.py#L38)

```python
LocalApplication.get(self, path: list[str])
```

Retorne documentos de consulta, sempre pelo contrato de aplicação.

**Entradas e tipos declarados**

- `path: list[str]`

**Retornos/yields explícitos**

- `doctor(self.root)`
- `self.projects.list()`
- `verify_catalog(self.root)`
- `self.projects.read(project)`
- `validate_project(self.root, project)`
- `self.projects.history(project)`
- `list_runs(self.root, project)`
- `read_run(self.root, project, path[3])`

**Exceções lançadas explicitamente**

- `FileNotFoundError('Rota não encontrada.')`

**Colaboradores chamados diretamente**

- `doctor`
- `self.projects.list`
- `verify_catalog`
- `len`
- `self.projects.read`
- `validate_project`
- `self.projects.history`
- `list_runs`
- `read_run`
- `FileNotFoundError`

### `LocalApplication.post`

[Implementação: source/antares_fd/gui/server.py:61](../../source/antares_fd/gui/server.py#L61)

```python
LocalApplication.post(self, path: list[str], body: dict)
```

Execute mutações locais por serviços de projeto, jobs ou catálogo.

**Entradas e tipos declarados**

- `path: list[str]`
- `body: dict`

**Retornos/yields explícitos**

- `self.projects.create(body.get('id'), body.get('source', '00_Copy_This'))`
- `register_dataset(self.root, body.get('id'), body.get('path'), kind=body.get('kind'), owner=body.get('owner'), source=body.get('source'), project=body.get('project'))`
- `self.projects.save(project, body.get('config'), body.get('revision'), body.get('note', 'Edição pela GUI'))`
- `self.projects.restore(project, body.get('target'), body.get('revision'))`
- `mass_properties(body)`
- `transform_components(body.get('components'), swap=body.get('swap'), structural_factor=body.get('structural_factor', 1.0))`
- `import_design(self.root, project, content, body.get('revision'))`
- `self.projects.save(project, {}, body.get('revision'), 'Inclusão de arquivo de entrada', assets={body.get('path', ''): content})`
- `self.jobs.start(project, body)`
- `self.jobs.cancel(project, path[3])`
- `verify_run(self.root, project, path[3])`

**Exceções lançadas explicitamente**

- `ValueError('Arquivo codificado inválido.')`
- `FileNotFoundError('Rota não encontrada.')`

**Colaboradores chamados diretamente**

- `self.projects.create`
- `body.get`
- `register_dataset`
- `len`
- `self.projects.save`
- `self.projects.restore`
- `mass_properties`
- `transform_components`
- `base64.b64decode`
- `ValueError`
- `import_design`
- `self.jobs.start`
- `self.jobs.cancel`
- `verify_run`
- `FileNotFoundError`

### `Handler.__init__`

[Implementação: source/antares_fd/gui/server.py:105](../../source/antares_fd/gui/server.py#L105)

```python
Handler.__init__(self, *args, app: LocalApplication, **kwargs)
```

Injete o estado do servidor sem variáveis de aplicação globais.

**Entradas e tipos declarados**

- `app: LocalApplication`
- `*args: argumentos posicionais adicionais`
- `**kwargs: argumentos nomeados adicionais`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `super().__init__`
- `super`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `Handler.log_message`

[Implementação: source/antares_fd/gui/server.py:110](../../source/antares_fd/gui/server.py#L110)

```python
Handler.log_message(self, format, *args)
```

Registre somente a mensagem HTTP padrão, nunca os corpos ou o token.

**Entradas e tipos declarados**

- `format: tipo não anotado; ver contrato acima`
- `*args: argumentos posicionais adicionais`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `LOGGER.info`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `Handler._trusted`

[Implementação: source/antares_fd/gui/server.py:114](../../source/antares_fd/gui/server.py#L114)

```python
Handler._trusted(self, *, mutation=False)
```

Exija Host de loopback e, para mutações, token explícito e origem local.

**Entradas e tipos declarados**

- `mutation: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- `PermissionError('Este serviço atende apenas sua origem local.')`
- `PermissionError('Origem não autorizada.')`
- `PermissionError('Sessão inválida.')`
- `PermissionError('Sessão expirada; recarregue a estação local.')`

**Colaboradores chamados diretamente**

- `self.headers.get`
- `PermissionError`
- `cookies.SimpleCookie`
- `jar.load`
- `secrets.compare_digest`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `Handler._send`

[Implementação: source/antares_fd/gui/server.py:136](../../source/antares_fd/gui/server.py#L136)

```python
Handler._send(self, data: bytes, content_type: str, status=200, *, session=False)
```

Envie resposta sem cache, com CSP restrita e cookie de sessão local.

**Entradas e tipos declarados**

- `data: bytes`
- `content_type: str`
- `status: tipo não anotado; ver contrato acima`
- `session: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.send_response`
- `self.send_header`
- `str`
- `len`
- `self.end_headers`
- `self.wfile.write`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `Handler._json`

[Implementação: source/antares_fd/gui/server.py:149](../../source/antares_fd/gui/server.py#L149)

```python
Handler._json(self, value, status=200)
```

Serialize JSON com NaN proibido e mensagem de erro estruturada.

**Entradas e tipos declarados**

- `value: tipo não anotado; ver contrato acima`
- `status: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self._send`
- `json.dumps(plain(value), ensure_ascii=False, default=str, allow_nan=False).encode`
- `json.dumps`
- `plain`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `Handler.do_GET`

[Implementação: source/antares_fd/gui/server.py:153](../../source/antares_fd/gui/server.py#L153)

```python
Handler.do_GET(self)
```

Sirva assets próprios ou uma consulta autenticada de projeto/resultado.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `None`

**Exceções lançadas explicitamente**

- `PermissionError('Host não autorizado.')`
- `ValueError('Arquivo indisponível para visualização local.')`
- `FileNotFoundError('Rota não encontrada.')`

**Colaboradores chamados diretamente**

- `urlsplit`
- `self.headers.get`
- `PermissionError`
- `(STATIC / name).read_bytes().replace`
- `(STATIC / name).read_bytes`
- `self.app.token.encode`
- `self._send`
- `mimetypes.guess_type`
- `self._trusted`
- `unquote`
- `url.path.split`
- `len`
- `contained`
- `document.read_bytes`
- `self.app.projects.path`
- `run_path`
- `'/'.join`
- `artifact.is_file`
- `artifact.stat`
- `artifact.suffix.lower`
- `ValueError`
- `artifact.read_bytes`
- `FileNotFoundError`
- `self._json`
- `self.app.get`
- `self._error`

### `Handler.do_POST`

[Implementação: source/antares_fd/gui/server.py:187](../../source/antares_fd/gui/server.py#L187)

```python
Handler.do_POST(self)
```

Valide autenticação e corpo limitado antes de despachar uma mutação.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- `ValueError('Use Content-Type application/json.')`
- `ValueError('Corpo vazio ou maior que 24 MiB.')`
- `ValueError('O corpo deve ser um objeto JSON.')`
- `FileNotFoundError('Rota não encontrada.')`

**Colaboradores chamados diretamente**

- `self._trusted`
- `self.headers.get('Content-Type', '').split`
- `self.headers.get`
- `ValueError`
- `int`
- `json.loads`
- `self.rfile.read`
- `isinstance`
- `unquote`
- `urlsplit(self.path).path.split`
- `urlsplit`
- `FileNotFoundError`
- `self._json`
- `self.app.post`
- `self._error`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `Handler._error`

[Implementação: source/antares_fd/gui/server.py:206](../../source/antares_fd/gui/server.py#L206)

```python
Handler._error(self, exc)
```

Converta erros conhecidos em HTTP sem expor traceback ao navegador.

**Entradas e tipos declarados**

- `exc: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `isinstance`
- `LOGGER.exception`
- `self._json`
- `str`
- `type`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `make_server`

[Implementação: source/antares_fd/gui/server.py:222](../../source/antares_fd/gui/server.py#L222)

```python
make_server(root: Path, port: int=0) -> ThreadingHTTPServer
```

Crie o servidor exclusivamente em 127.0.0.1, aceitando porta efêmera para testes.

**Entradas e tipos declarados**

- `root: Path`
- `port: int`

**Retornos/yields explícitos**

- `server`

**Exceções lançadas explicitamente**

- `ValueError('Porta inválida.')`
- `raise (propaga a exceção ativa)`

**Colaboradores chamados diretamente**

- `isinstance`
- `ValueError`
- `LocalApplication`
- `ThreadingHTTPServer`
- `partial`
- `app.jobs.close`

### `serve`

[Implementação: source/antares_fd/gui/server.py:237](../../source/antares_fd/gui/server.py#L237)

```python
serve(root: Path, *, port: int=8765, open_browser: bool=True)
```

Sirva a estação local até Ctrl+C e encerre workers ativos ao sair.

**Entradas e tipos declarados**

- `root: Path`
- `port: int`
- `open_browser: bool`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `make_server`
- `print`
- `webbrowser.open`
- `server.serve_forever`
- `server.app.jobs.close`
- `server.server_close`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

## `source/antares_fd/reconstruction/__init__.py`

Postflight observations derived from audited telemetry, never raw mutation.

Módulo declarativo, ponto de entrada sem funções ou exportação de interfaces; não contém funções próprias.

## `source/antares_fd/reconstruction/aero.py`

Source-tagged Cd curve import and overlap-only comparison contracts.

### `CurveSpec.__post_init__`

[Implementação: source/antares_fd/reconstruction/aero.py:27](../../source/antares_fd/reconstruction/aero.py#L27)

```python
CurveSpec.__post_init__(self) -> None
```

Valide a identidade e a área de referência de uma curva de Cd.

Exige nome, proveniência, IDs de geometria e condição, fonte e estado
de propulsão suportados e área finita positiva em m². Em falha lança
ValueError antes da leitura ou comparação das curvas.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- `ValueError('Cd curve name and provenance are required')`
- `ValueError('Cd curve source or power state is unsupported')`
- `ValueError('Cd curve geometry and condition identifiers are required')`
- `ValueError('Cd curve reference area must be finite and positive')`

**Colaboradores chamados diretamente**

- `self.name.strip`
- `self.provenance.strip`
- `ValueError`
- `self.geometry_id.strip`
- `self.condition_id.strip`
- `np.isfinite`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `load_cd_curve`

[Implementação: source/antares_fd/reconstruction/aero.py:51](../../source/antares_fd/reconstruction/aero.py#L51)

```python
load_cd_curve(path: Path, spec: CurveSpec) -> CdCurve
```

Read a declared Mach/Cd file without interpolation or extrapolation.

**Entradas e tipos declarados**

- `path: Path`
- `spec: CurveSpec`

**Retornos/yields explícitos**

- `CdCurve(spec, pd.DataFrame({'mach': mach, 'Cd': cd}), hashlib.sha256(data).hexdigest())`

**Exceções lançadas explicitamente**

- `ValueError('Cd curve requires at least two rows with columns mach,Cd')`
- `ValueError('Cd curve must contain numeric Mach and Cd')`
- `ValueError('Cd curve contains non-finite values')`
- `ValueError('Mach and Cd must be nonnegative')`
- `ValueError('Mach values must be strictly increasing')`

**Colaboradores chamados diretamente**

- `Path`
- `path.read_bytes`
- `pd.read_csv`
- `BytesIO`
- `list`
- `len`
- `ValueError`
- `points['mach'].to_numpy`
- `points['Cd'].to_numpy`
- `np.isfinite(mach).all`
- `np.isfinite`
- `np.isfinite(cd).all`
- `np.any`
- `np.diff`
- `CdCurve`
- `pd.DataFrame`
- `hashlib.sha256(data).hexdigest`
- `hashlib.sha256`

### `compare_cd_curves`

[Implementação: source/antares_fd/reconstruction/aero.py:75](../../source/antares_fd/reconstruction/aero.py#L75)

```python
compare_cd_curves(reference: CdCurve, candidate: CdCurve) -> pd.DataFrame
```

Compare two source-tagged curves only where their domains overlap.

**Entradas e tipos declarados**

- `reference: CdCurve`
- `candidate: CdCurve`

**Retornos/yields explícitos**

- `pd.DataFrame({'mach': grid, f'{reference.spec.name}_cd': ref, f'{candidate.spec.name}_cd': cand, f'{candidate.spec.name}_minus_{reference.spec.name}_cd': cand - ref})`

**Exceções lançadas explicitamente**

- `ValueError('Cannot compare different power states')`
- `ValueError('Cannot compare Cd curves with different geometry identifiers')`
- `ValueError('Cannot compare Cd curves with different condition identifiers')`
- `ValueError('Cannot compare Cd curves with different reference areas')`
- `ValueError('Cd curves have no common Mach interval')`

**Colaboradores chamados diretamente**

- `ValueError`
- `np.isclose`
- `max`
- `min`
- `np.unique`
- `np.concatenate`
- `reference.points.loc[reference.points['mach'].between(lo, hi), 'mach'].to_numpy`
- `reference.points['mach'].between`
- `candidate.points.loc[candidate.points['mach'].between(lo, hi), 'mach'].to_numpy`
- `candidate.points['mach'].between`
- `np.array`
- `np.interp`
- `pd.DataFrame`

## `source/antares_fd/reconstruction/artifacts.py`

Publish auditable observed-flight products from one verified telemetry audit.

### `_sha256`

[Implementação: source/antares_fd/reconstruction/artifacts.py:26](../../source/antares_fd/reconstruction/artifacts.py#L26)

```python
_sha256(path: Path) -> str
```

Calcule a impressão digital SHA-256 de um arquivo de evidência.

Lê o conteúdo binário em blocos e retorna o digest hexadecimal; não modifica
o arquivo. Falhas de leitura são propagadas.

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

### `_plot_altitude`

[Implementação: source/antares_fd/reconstruction/artifacts.py:39](../../source/antares_fd/reconstruction/artifacts.py#L39)

```python
_plot_altitude(frame: pd.DataFrame, events: dict, output: Path) -> None
```

Desenhe altitudes observadas com os eventos que têm suporte nos dados.

Usa frame e events para produzir o gráfico em output, preservando segmentos
de aquisição. Salva e fecha a figura; não calibra os sensores.

**Entradas e tipos declarados**

- `frame: pd.DataFrame`
- `events: dict`
- `output: Path`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `matplotlib.use`
- `plt.subplots`
- `ax.plot`
- `ax.axvline`
- `ax.set`
- `ax.grid`
- `ax.legend`
- `figure.tight_layout`
- `figure.savefig`
- `plt.close`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `process_audit_section`

[Implementação: source/antares_fd/reconstruction/artifacts.py:68](../../source/antares_fd/reconstruction/artifacts.py#L68)

```python
process_audit_section(audit_dir: Path, *, repo_root: Path, section_marker: str, output_dir: Path | None=None) -> Path
```

Produce a new, separate result directory without altering source evidence.

**Entradas e tipos declarados**

- `audit_dir: Path`
- `repo_root: Path`
- `section_marker: str`
- `output_dir: Path | None`

**Retornos/yields explícitos**

- `output_dir`

**Exceções lançadas explicitamente**

- `ValueError('Raw telemetry source is missing or differs from the verified audit')`
- `ValueError('Reconstruction artifacts must be written below the repository results/ directory')`
- `FileExistsError(f'Refusing to overwrite reconstruction output: {output_dir}')`
- `ValueError('Reconstruction output may not contain the raw source')`
- `ValueError('Raw telemetry changed during reconstruction')`
- `raise (propaga a exceção ativa)`

**Colaboradores chamados diretamente**

- `Path(audit_dir).resolve`
- `Path`
- `Path(repo_root).resolve`
- `verify_artifact_set`
- `source.is_absolute`
- `source.resolve`
- `source.is_file`
- `_sha256`
- `ValueError`
- `pd.read_parquet`
- `json.loads`
- `(audit_dir / 'telemetry_inventory.json').read_text`
- `build_observed_section`
- `inventory.get`
- `datetime.now(timezone.utc).strftime`
- `datetime.now`
- `output_dir.is_absolute`
- `output_dir.resolve`
- `output_dir.is_relative_to`
- `output_dir.exists`
- `FileExistsError`
- `source.is_relative_to`
- `output_dir.parent.mkdir`
- `tempfile.mkdtemp`
- `summary.update`
- `block.get`
- `write_parquet_atomic`
- `write_json_atomic`
- `_plot_altitude`
- `datetime.now(timezone.utc).isoformat`
- `platform.python_version`
- `get_git_provenance`
- `(stage / name).stat`
- `os.replace`
- `shutil.rmtree`

## `source/antares_fd/reconstruction/observations.py`

Conservative, segment-local observations from audited telemetry tables.

### `build_observed_section`

[Implementação: source/antares_fd/reconstruction/observations.py:14](../../source/antares_fd/reconstruction/observations.py#L14)

```python
build_observed_section(samples: pd.DataFrame, segments: pd.DataFrame, *, section_marker: str, altitude_channels: tuple[str, str]=ALTITUDE_CHANNELS, timebase_diagnostics: pd.DataFrame | None=None, duplicate_blocks: list[dict] | None=None) -> tuple[pd.DataFrame, dict, dict]
```

Derive only recorded relative-altitude observations and interval rates.

The source order, clock segment, and source line remain explicit. Interval
rates are secants between samples, not instantaneous inertial velocity.
A recorded altitude extremum is distinct from a physical apogee estimate.

**Entradas e tipos declarados**

- `samples: pd.DataFrame`
- `segments: pd.DataFrame`
- `section_marker: str`
- `altitude_channels: tuple[str, str]`
- `timebase_diagnostics: pd.DataFrame | None`
- `duplicate_blocks: list[dict] | None`

**Retornos/yields explícitos**

- `(frame, events, summary)`

**Exceções lançadas explicitamente**

- `ValueError(f'No audited samples carry section marker {section_marker!r}')`
- `ValueError('The marked section lacks a required time or altitude channel')`
- `ValueError('Audited samples contain duplicate record/channel keys')`
- `ValueError('Altitude channels must be labeled DERIVED in the audit')`
- `ValueError('Timebase diagnostics contain duplicate record IDs')`
- `ValueError('Exact-duplicate block has inconsistent original and copy lengths')`
- `ValueError(f'Conflicting exact-duplicate lineage for record {copy_index}')`
- `ValueError('Marked section spans multiple clock segments; explicit alignment is required')`
- `ValueError('Marked section has missing or unsupported clock values')`
- `ValueError('Marked section clock is not strictly increasing')`
- `ValueError('Audited sample and segment raw timestamps disagree')`

**Colaboradores chamados diretamente**

- `samples.loc[samples['section_marker'].eq(section_marker)].copy`
- `samples['section_marker'].eq`
- `ValueError`
- `selected['raw_channel_name'].isin`
- `set`
- `selected.duplicated(['record_index', 'raw_channel_name']).any`
- `selected.duplicated`
- `selected.loc[selected['raw_channel_name'].isin(altitude_channels), 'data_origin'].dropna().unique`
- `selected.loc[selected['raw_channel_name'].isin(altitude_channels), 'data_origin'].dropna`
- `len`
- `selected.pivot`
- `selected['raw_channel_name'].eq`
- `lineage.merge`
- `wide.reset_index`
- `frame.merge(segments[['record_index', 'segment_id', 'raw_time', 'segment_elapsed_s']], on='record_index', validate='one_to_one').sort_values('record_index', kind='stable').reset_index`
- `frame.merge(segments[['record_index', 'segment_id', 'raw_time', 'segment_elapsed_s']], on='record_index', validate='one_to_one').sort_values`
- `frame.merge`
- `diagnostics['record_index'].duplicated().any`
- `diagnostics['record_index'].duplicated`
- `int`
- `range`
- `str`
- `block.get`
- `frame['record_index'].isin`
- `pd.array`
- `duplicate_of.get`
- `frame['segment_id'].nunique`
- `frame['segment_elapsed_s'].isna().any`
- `frame['segment_elapsed_s'].isna`
- `np.isfinite(frame['segment_elapsed_s']).all`
- `np.isfinite`
- `(frame['segment_elapsed_s'].diff().dropna() <= 0).any`
- `frame['segment_elapsed_s'].diff().dropna`
- `frame['segment_elapsed_s'].diff`
- `np.allclose`
- `frame['section_elapsed_s'].diff`
- `frame['interval_class'].map(interval_quality).fillna`
- `frame['interval_class'].map`
- `channel.removesuffix`
- `frame[channel].diff`
- `frame[channel].dropna`
- `peak_indices.append`
- `finite.idxmax`
- `float`
- `list`
- `all`
- `math.isfinite`
- `unobservable_event`
- `frame['interval_quality'].value_counts().items`
- `frame['interval_quality'].value_counts`
- `frame['interval_duration_s'].max`
- `frame['is_exact_duplicate_copy'].sum`

### `build_observed_section.unobservable_event`

[Implementação: source/antares_fd/reconstruction/observations.py:164](../../source/antares_fd/reconstruction/observations.py#L164)

```python
build_observed_section.unobservable_event(name: str, channels: list[str], reason: str) -> dict
```

Registre um evento que os canais disponíveis não permitem observar.

Retorna metadados com nome, canais e justificativa, sem estimar instante
ou valor físico ausente no registro.

**Entradas e tipos declarados**

- `name: str`
- `channels: list[str]`
- `reason: str`

**Retornos/yields explícitos**

- `{'status': 'INSUFFICIENT_OBSERVABILITY', 'event': name, 'timestamp': None, 'confidence': 'NOT_ASSIGNABLE', 'evidence_channels': channels, 'method': 'NOT_DETECTED', 'reason': reason, 'time_uncertainty': 'NOT_QUANTIFIABLE'}`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- Nenhuma ocorrência explícita no corpo local.

## `source/antares_fd/reporting/__init__.py`

Antares Flight Dynamics - Automated PDF Reporting Subsystem.

Provides publication-grade engineering PDF report generation,
data visualization, and tabular summaries.

Módulo declarativo, ponto de entrada sem funções ou exportação de interfaces; não contém funções próprias.

## `source/antares_fd/reporting/builder.py`

### `ReportContext.__init__`

[Implementação: source/antares_fd/reporting/builder.py:17](../../source/antares_fd/reporting/builder.py#L17)

```python
ReportContext.__init__(self, project_dir: Path, metrics: FlightMetrics, req_db: RequirementDB)
```

Prepare o contexto compartilhado do relatório determinístico.

Armazena diretório, métricas e base de requisitos; calcula avaliações
e proveniência que serão consumidas pelas seções, sem reintegrar o voo.

**Entradas e tipos declarados**

- `project_dir: Path`
- `metrics: FlightMetrics`
- `req_db: RequirementDB`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `req_db.evaluate`
- `collect_reproducibility_data`
- `evaluate_model_validity`
- `self.output_dir.mkdir`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `FlightDynamicsReportBuilder.__init__`

[Implementação: source/antares_fd/reporting/builder.py:37](../../source/antares_fd/reporting/builder.py#L37)

```python
FlightDynamicsReportBuilder.__init__(self, context: ReportContext)
```

Inicialize a montagem de elementos ReportLab a partir de context.

Prepara estilos, diretório de figuras e lista de flowables. Os métodos
de seção acrescentam elementos a essa lista antes da escrita do PDF.

**Entradas e tipos declarados**

- `context: ReportContext`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `setup_report_styles`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `FlightDynamicsReportBuilder.build_deterministic_report`

[Implementação: source/antares_fd/reporting/builder.py:47](../../source/antares_fd/reporting/builder.py#L47)

```python
FlightDynamicsReportBuilder.build_deterministic_report(self, output_pdf: Path)
```

Constructs phases 0-14 for standard flight.

**Entradas e tipos declarados**

- `output_pdf: Path`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self._add_cover`
- `self._add_executive_summary`
- `self._add_provenance_and_validity`
- `self._add_flight_kinematics`
- `self._add_mass_propulsion`
- `self._add_aero_loads`
- `self._add_stability`
- `self._add_atmosphere`
- `self._add_recovery`
- `len`
- `self._add_multi_scenario`
- `self._add_monte_carlo`
- `self._add_reproducibility_appendix`
- `BaseReportDocTemplate`
- `str`
- `doc.build`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `FlightDynamicsReportBuilder._add_cover`

[Implementação: source/antares_fd/reporting/builder.py:77](../../source/antares_fd/reporting/builder.py#L77)

```python
FlightDynamicsReportBuilder._add_cover(self, title: str)
```

Acrescente a capa com título e identificação do projeto.

Cria parágrafos, espaçamento e quebra de página em self.flowables.
Não grava o PDF nesta etapa.

**Entradas e tipos declarados**

- `title: str`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.flowables.append`
- `Spacer`
- `Paragraph`
- `self.ctx.metrics.project_name.replace('_', ' ').upper`
- `self.ctx.metrics.project_name.replace`
- `PageBreak`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `FlightDynamicsReportBuilder._add_executive_summary`

[Implementação: source/antares_fd/reporting/builder.py:89](../../source/antares_fd/reporting/builder.py#L89)

```python
FlightDynamicsReportBuilder._add_executive_summary(self)
```

Acrescente o resumo de desempenho e conformidade do voo.

Lê métricas e requisitos do contexto, compõe tabelas e parágrafos
e sinaliza resultados críticos sem recalcular a dinâmica.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.flowables.append`
- `Paragraph`
- `len`
- `mc_summary_file.exists`
- `open`
- `json.load`
- `mc_data.get('status', 'PARTIAL').upper`
- `mc_data.get`
- `tables.build_completeness_table`
- `Spacer`
- `tables.build_flight_performance_table`
- `tables.build_stability_table`
- `tables.build_recovery_table`
- `isinstance`
- `str`
- `table_data.append`
- `tables._get_badge`
- `tables.create_standard_table`
- `PageBreak`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `FlightDynamicsReportBuilder._add_provenance_and_validity`

[Implementação: source/antares_fd/reporting/builder.py:156](../../source/antares_fd/reporting/builder.py#L156)

```python
FlightDynamicsReportBuilder._add_provenance_and_validity(self)
```

Acrescente origem dos dados e limites de validade do modelo.

Converte as avaliações do contexto em tabelas rastreáveis na sequência
de flowables, preservando classificações desconhecidas.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.flowables.append`
- `Paragraph`
- `val_data.append`
- `tables.build_model_validity_envelope_table`
- `Spacer`
- `qual_data.append`
- `tables.build_model_input_quality_table`
- `PageBreak`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `FlightDynamicsReportBuilder._add_flight_kinematics`

[Implementação: source/antares_fd/reporting/builder.py:179](../../source/antares_fd/reporting/builder.py#L179)

```python
FlightDynamicsReportBuilder._add_flight_kinematics(self)
```

Acrescente a seção de trajetória e cinemática.

Gera a figura a partir de FlightMetrics, referencia o arquivo resultante
e adiciona os elementos ao relatório em montagem.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.flowables.append`
- `Paragraph`
- `plot_registry.generate_kinematics_chart`
- `fig_path.exists`
- `Image`
- `str`
- `plot_registry.generate_trajectory_views_chart`
- `fig2_path.exists`
- `PageBreak`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `FlightDynamicsReportBuilder._add_mass_propulsion`

[Implementação: source/antares_fd/reporting/builder.py:197](../../source/antares_fd/reporting/builder.py#L197)

```python
FlightDynamicsReportBuilder._add_mass_propulsion(self)
```

Acrescente diagnóstico de massa, empuxo e propulsão.

Usa séries e escalares canônicos para tabelas e gráficos, com unidades
explícitas; atualiza flowables e arquivos de figuras.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.flowables.append`
- `Paragraph`
- `p_data.append`
- `tables.create_standard_table`
- `Spacer`
- `plot_registry.generate_mass_and_propulsion_chart`
- `fig_path.exists`
- `Image`
- `str`
- `PageBreak`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `FlightDynamicsReportBuilder._add_aero_loads`

[Implementação: source/antares_fd/reporting/builder.py:227](../../source/antares_fd/reporting/builder.py#L227)

```python
FlightDynamicsReportBuilder._add_aero_loads(self)
```

Acrescente cargas aerodinâmicas e seus limites declarados.

Lê pressão dinâmica e demais métricas do contexto, gera a visualização
e inclui o resultado no relatório, sem alterar o modelo de arrasto.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.flowables.append`
- `Paragraph`
- `q_data.append`
- `tables.create_standard_table`
- `Spacer`
- `plot_registry.generate_propulsion_and_loads_chart`
- `fig_path.exists`
- `Image`
- `str`
- `PageBreak`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `FlightDynamicsReportBuilder._add_stability`

[Implementação: source/antares_fd/reporting/builder.py:255](../../source/antares_fd/reporting/builder.py#L255)

```python
FlightDynamicsReportBuilder._add_stability(self)
```

Acrescente as margens de estabilidade e evolução de CG/CP.

Produz tabela e gráfico a partir das métricas canônicas e adiciona
a interpretação dos limites disponíveis ao relatório.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.flowables.append`
- `Paragraph`
- `sm_data.append`
- `tables.create_standard_table`
- `Spacer`
- `plot_registry.generate_stability_and_attitude_chart`
- `fig_path.exists`
- `Image`
- `str`
- `PageBreak`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `FlightDynamicsReportBuilder._add_atmosphere`

[Implementação: source/antares_fd/reporting/builder.py:280](../../source/antares_fd/reporting/builder.py#L280)

```python
FlightDynamicsReportBuilder._add_atmosphere(self)
```

Acrescente o perfil atmosférico utilizado na simulação.

Gera a figura a partir dos dados armazenados nas métricas e inclui
a imagem no relatório; não adquire uma nova previsão.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.flowables.append`
- `Paragraph`
- `plot_registry.generate_full_atmosphere_chart`
- `fig_path.exists`
- `Image`
- `str`
- `PageBreak`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `FlightDynamicsReportBuilder._add_recovery`

[Implementação: source/antares_fd/reporting/builder.py:293](../../source/antares_fd/reporting/builder.py#L293)

```python
FlightDynamicsReportBuilder._add_recovery(self)
```

Acrescente os resultados de recuperação e descida.

Apresenta os eventos e velocidades registrados em FlightMetrics;
configurações não avaliadas permanecem identificadas como ausentes.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.flowables.append`
- `Paragraph`
- `plot_registry.generate_recovery_descent_chart`
- `fig_path.exists`
- `Image`
- `str`
- `PageBreak`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `FlightDynamicsReportBuilder._add_multi_scenario`

[Implementação: source/antares_fd/reporting/builder.py:306](../../source/antares_fd/reporting/builder.py#L306)

```python
FlightDynamicsReportBuilder._add_multi_scenario(self)
```

Acrescente comparação entre cenários quando houver métricas adicionais.

Percorre scenario_metrics, monta tabela comparativa e figura; sem cenários
adicionais, retorna sem acrescentar uma seção vazia.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.flowables.append`
- `Paragraph`
- `self.ctx.scenario_metrics.items`
- `t_data.append`
- `tables.create_standard_table`
- `Spacer`
- `plot_registry.generate_multi_scenario_chart`
- `fig_path.exists`
- `Image`
- `str`
- `PageBreak`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `FlightDynamicsReportBuilder._add_monte_carlo`

[Implementação: source/antares_fd/reporting/builder.py:336](../../source/antares_fd/reporting/builder.py#L336)

```python
FlightDynamicsReportBuilder._add_monte_carlo(self)
```

Acrescente estatísticas e requisitos probabilísticos da campanha salva.

Lê JSONL, tabelas e figuras em mc_results_dir; compõe distribuições,
dispersão e sensibilidade. Não executa novas amostras ou novos voos.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `None`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.flowables.append`
- `Paragraph`
- `mc_file.exists`
- `mc_summary_file.exists`
- `open`
- `json.load`
- `s_data.append`
- `mc_data.get`
- `mc_data.get('status', 'Unknown').upper`
- `'; '.join`
- `tables.create_standard_table`
- `Spacer`
- `tables.build_mc_input_table`
- `tables.build_mc_output_table`
- `getattr`
- `callable`
- `mc_file.suffix.lower`
- `__import__('pandas').read_parquet(mc_file).to_dict`
- `__import__('pandas').read_parquet`
- `__import__`
- `read_jsonl_objects`
- `stochastic_evaluator`
- `pd.DataFrame`
- `stochastic_table_builder`
- `fig_disp.exists`
- `plot_registry.generate_mc_dispersion_chart`
- `Image`
- `str`
- `fig_dist.exists`
- `plot_registry.generate_mc_distributions_chart`
- `PageBreak`
- `fig_conv.exists`
- `plot_registry.generate_mc_convergence_chart`
- `sens_file.exists`
- `plot_registry.generate_sensitivity_tornado_chart`
- `fig_sens.exists`

### `FlightDynamicsReportBuilder._add_reproducibility_appendix`

[Implementação: source/antares_fd/reporting/builder.py:434](../../source/antares_fd/reporting/builder.py#L434)

```python
FlightDynamicsReportBuilder._add_reproducibility_appendix(self)
```

Acrescente a identificação da revisão usada para construir o relatório.

Consulta Git e horário UTC, registra diretório do projeto e hashes
disponíveis. Falhas de identificação são apresentadas como desconhecidas.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.flowables.append`
- `PageBreak`
- `Paragraph`
- `subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf-8').strip`
- `subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode`
- `subprocess.check_output`
- `subprocess.check_output(['git', 'status', '--porcelain']).decode('utf-8').strip`
- `subprocess.check_output(['git', 'status', '--porcelain']).decode`
- `datetime.utcnow().isoformat`
- `datetime.utcnow`
- `tables.create_standard_table`
- `Spacer`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

## `source/antares_fd/reporting/charts.py`

Chart Generation for Antares Engineering Reports.

Generates standardized, publication-grade figures for nominal flights
and Monte Carlo campaigns. Every metric and boundary line aligns with
the centralized analysis single-source-of-truth.

### `_get_flight_events`

[Implementação: source/antares_fd/reporting/charts.py:23](../../source/antares_fd/reporting/charts.py#L23)

```python
_get_flight_events(flight: Any) -> List[tuple[float, str]]
```

Extracts key event timestamps from flight.

**Entradas e tipos declarados**

- `flight: Any`

**Retornos/yields explícitos**

- `events`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `hasattr`
- `events.append`
- `float`
- `getattr`
- `events.sort`

### `_add_event_lines`

[Implementação: source/antares_fd/reporting/charts.py:44](../../source/antares_fd/reporting/charts.py#L44)

```python
_add_event_lines(ax, events: List[tuple[float, str]], max_t: Optional[float]=None, color: str='#64748B')
```

Annotates vertical event lines on an axes.

**Entradas e tipos declarados**

- `ax: tipo não anotado; ver contrato acima`
- `events: List[tuple[float, str]]`
- `max_t: Optional[float]`
- `color: str`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `ax.get_xlim`
- `ax.get_ylim`
- `ax.axvline`
- `ax.text`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `generate_mass_and_propulsion_chart`

[Implementação: source/antares_fd/reporting/charts.py:59](../../source/antares_fd/reporting/charts.py#L59)

```python
generate_mass_and_propulsion_chart(flight: Any, output_path: Path) -> Path
```

Generates high-density Mass & Propulsion diagnostics:
- Motor Thrust and Instantaneous T/W vs Time
- Vehicle Total Mass and Propellant Mass vs Time
- Cumulative Impulse vs Time

**Entradas e tipos declarados**

- `flight: Any`
- `output_path: Path`

**Retornos/yields explícitos**

- `output_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `setup_matplotlib_theme`
- `float`
- `np.linspace`
- `np.array`
- `motor.thrust`
- `rocket.total_mass`
- `np.maximum`
- `np.cumsum`
- `plt.subplots`
- `ax1.plot`
- `ax1.fill_between`
- `ax1.set_ylabel`
- `ax1.tick_params`
- `ax1.set_ylim`
- `ax1.twinx`
- `ax1_tw.plot`
- `ax1_tw.set_ylabel`
- `ax1_tw.tick_params`
- `ax1_tw.set_ylim`
- `ax1.set_title`
- `ax2.plot`
- `ax2.axhline`
- `ax2.set_ylabel`
- `ax2.legend`
- `ax2.set_ylim`
- `ax3.plot`
- `getattr`
- `ax3.axhline`
- `ax3.set_ylabel`
- `ax3.set_xlabel`
- `ax3.legend`
- `ax3.set_xlim`
- `fig.tight_layout`
- `output_path.parent.mkdir`
- `save_figure`
- `plt.close`

### `generate_kinematics_chart`

[Implementação: source/antares_fd/reporting/charts.py:123](../../source/antares_fd/reporting/charts.py#L123)

```python
generate_kinematics_chart(flight: Any, output_path: Path, metrics: Optional[Dict[str, Any]]=None) -> Path
```

Generates 3-panel Trajectory & Ascent Kinematics chart:
- Altitude AGL with key milestone markers
- Speed (m/s) and Mach number
- Total Acceleration and Vertical Acceleration (Ascent Phase)

**Entradas e tipos declarados**

- `flight: Any`
- `output_path: Path`
- `metrics: Optional[Dict[str, Any]]`

**Retornos/yields explícitos**

- `output_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `setup_matplotlib_theme`
- `_get_flight_events`
- `float`
- `plt.subplots`
- `ax1.plot`
- `ax1.set_ylabel`
- `ax1.set_title`
- `ax1.legend`
- `_add_event_lines`
- `ax2.plot`
- `ax2.set_ylabel`
- `ax2.tick_params`
- `ax2.twinx`
- `ax2_mach.plot`
- `ax2_mach.set_ylabel`
- `ax2_mach.tick_params`
- `np.sqrt`
- `ax3.plot`
- `metrics.get('kinematics', {}).get`
- `metrics.get`
- `np.max`
- `np.argmax`
- `ax3.annotate`
- `dict`
- `ax3.set_ylabel`
- `ax3.set_xlabel`
- `ax3.legend`
- `fig.tight_layout`
- `output_path.parent.mkdir`
- `save_figure`
- `plt.close`

### `generate_propulsion_and_loads_chart`

[Implementação: source/antares_fd/reporting/charts.py:199](../../source/antares_fd/reporting/charts.py#L199)

```python
generate_propulsion_and_loads_chart(flight: Any, output_path: Path, metrics: Optional[Dict[str, Any]]=None) -> Path
```

Generates Dynamic Pressure (Max Q) and Bending load Q * alpha (strictly post rail exit).

**Entradas e tipos declarados**

- `flight: Any`
- `output_path: Path`
- `metrics: Optional[Dict[str, Any]]`

**Retornos/yields explícitos**

- `output_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `setup_matplotlib_theme`
- `_get_flight_events`
- `float`
- `plt.subplots`
- `ax1.plot`
- `ax1.set_ylabel`
- `ax1.set_ylim`
- `int`
- `np.argmax`
- `ax1.annotate`
- `dict`
- `ax1.set_title`
- `_add_event_lines`
- `np.interp`
- `np.abs`
- `ax2.plot`
- `ax2.fill_between`
- `ax2.set_ylabel`
- `ax2.set_xlabel`
- `ax2.set_ylim`
- `len`
- `ax2.annotate`
- `fig.tight_layout`
- `output_path.parent.mkdir`
- `save_figure`
- `plt.close`

### `generate_stability_and_attitude_chart`

[Implementação: source/antares_fd/reporting/charts.py:273](../../source/antares_fd/reporting/charts.py#L273)

```python
generate_stability_and_attitude_chart(flight: Any, output_path: Path, metrics: Optional[Dict[str, Any]]=None) -> Path
```

Generates CG/CP migration, Static Margin corridor, and Angle of Attack.
Explicitly highlights Rail Exit, Max Q, Burnout, and Apogee milestones.

**Entradas e tipos declarados**

- `flight: Any`
- `output_path: Path`
- `metrics: Optional[Dict[str, Any]]`

**Retornos/yields explícitos**

- `output_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `setup_matplotlib_theme`
- `_get_flight_events`
- `float`
- `plt.subplots`
- `np.linspace`
- `rocket.center_of_mass`
- `rocket.cp_position`
- `ax1.plot`
- `ax1.fill_between`
- `ax1.set_ylabel`
- `ax1.set_xlim`
- `ax1.legend`
- `ax1.set_title`
- `_add_event_lines`
- `ax2.plot`
- `ax2.axhspan`
- `ax2.axhline`
- `metrics.get('aerodynamic_loads', {}).get`
- `metrics.get`
- `ax2.annotate`
- `dict`
- `ax2.set_ylabel`
- `ax2.set_xlabel`
- `ax2.set_ylim`
- `max`
- `np.max`
- `ax2.legend`
- `fig.tight_layout`
- `output_path.parent.mkdir`
- `save_figure`
- `plt.close`

### `generate_full_atmosphere_chart`

[Implementação: source/antares_fd/reporting/charts.py:336](../../source/antares_fd/reporting/charts.py#L336)

```python
generate_full_atmosphere_chart(flight: Any, output_path: Path) -> Path
```

Generates a full-page 4-panel Atmospheric Profile based on MAGI data:
- Wind Speed vs Altitude AGL
- Wind Direction vs Altitude AGL
- Density and Speed of Sound vs Altitude AGL
- Wind Hodograph (U-East vs V-North)

**Entradas e tipos declarados**

- `flight: Any`
- `output_path: Path`

**Retornos/yields explícitos**

- `output_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `setup_matplotlib_theme`
- `float`
- `hasattr`
- `np.linspace`
- `env.wind_velocity_x`
- `env.wind_velocity_y`
- `np.hypot`
- `np.degrees`
- `np.arctan2`
- `env.density`
- `env.speed_of_sound`
- `u_east.append`
- `v_north.append`
- `wind_speeds.append`
- `wind_dirs.append`
- `densities.append`
- `sound_speeds.append`
- `plt.subplots`
- `ax1.plot`
- `ax1.set_xlabel`
- `ax1.set_ylabel`
- `ax1.set_title`
- `ax1.set_xlim`
- `ax2.plot`
- `ax2.set_xlabel`
- `ax2.set_ylabel`
- `ax2.set_title`
- `ax2.set_xlim`
- `ax3.plot`
- `ax3.set_xlabel`
- `ax3.set_ylabel`
- `ax3.tick_params`
- `ax3.twiny`
- `ax3_c.plot`
- `ax3_c.set_xlabel`
- `ax3_c.tick_params`
- `ax3.set_title`
- `ax4.plot`
- `ax4.scatter`
- `ax4.axhline`
- `ax4.axvline`
- `ax4.set_xlabel`
- `ax4.set_ylabel`
- `ax4.set_title`
- `ax4.axis`
- `ax4.legend`
- `fig.suptitle`
- `fig.tight_layout`
- `output_path.parent.mkdir`
- `save_figure`
- `plt.close`

### `generate_recovery_descent_chart`

[Implementação: source/antares_fd/reporting/charts.py:425](../../source/antares_fd/reporting/charts.py#L425)

```python
generate_recovery_descent_chart(flight: Any, output_path: Path) -> Path
```

Generates Recovery Profile: Altitude vs Time from Apogee to Touchdown, and sink rate.

**Entradas e tipos declarados**

- `flight: Any`
- `output_path: Path`

**Retornos/yields explícitos**

- `output_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `setup_matplotlib_theme`
- `_get_flight_events`
- `float`
- `plt.subplots`
- `ax1.plot`
- `ax1.set_ylabel`
- `ax1.set_xlim`
- `ax1.set_title`
- `ax1.legend`
- `_add_event_lines`
- `np.abs`
- `ax2.plot`
- `ax2.axhline`
- `ax2.set_ylabel`
- `ax2.set_xlabel`
- `ax2.legend`
- `fig.tight_layout`
- `output_path.parent.mkdir`
- `save_figure`
- `plt.close`

### `generate_trajectory_views_chart`

[Implementação: source/antares_fd/reporting/charts.py:465](../../source/antares_fd/reporting/charts.py#L465)

```python
generate_trajectory_views_chart(flight: Any, output_path: Path) -> Path
```

Generates 2D trajectory overview: Altitude vs Downrange and Top-Down ground track.

**Entradas e tipos declarados**

- `flight: Any`
- `output_path: Path`

**Retornos/yields explícitos**

- `output_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `setup_matplotlib_theme`
- `plt.subplots`
- `float`
- `np.sqrt`
- `ax1.plot`
- `int`
- `np.argmax`
- `ax1.scatter`
- `ax1.set_xlabel`
- `ax1.set_ylabel`
- `ax1.set_title`
- `ax1.legend`
- `ax2.plot`
- `ax2.scatter`
- `ax2.set_xlabel`
- `ax2.set_ylabel`
- `ax2.set_title`
- `ax2.axis`
- `ax2.legend`
- `fig.tight_layout`
- `output_path.parent.mkdir`
- `save_figure`
- `plt.close`

### `generate_multi_scenario_chart`

[Implementação: source/antares_fd/reporting/charts.py:505](../../source/antares_fd/reporting/charts.py#L505)

```python
generate_multi_scenario_chart(scenario_flights: Dict[str, Any], output_path: Path) -> Path
```

Generates high-density comparative multi-scenario flight dynamics charts:
- Top panel: Altitude AGL vs Time for all scenarios (Nominal, Ballistic, Main at Apogee, Separation, Only Reefing)
- Bottom panel: Ground Downrange Distance vs Time for all scenarios

**Entradas e tipos declarados**

- `scenario_flights: Dict[str, Any]`
- `output_path: Path`

**Retornos/yields explícitos**

- `output_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `setup_matplotlib_theme`
- `plt.subplots`
- `scenario_flights.items`
- `float`
- `np.sqrt`
- `max`
- `styles_map.get`
- `ax1.plot`
- `ax1.scatter`
- `ax2.plot`
- `ax2.scatter`
- `ax1.set_ylabel`
- `ax1.set_title`
- `ax1.set_ylim`
- `ax1.set_xlim`
- `ax1.legend`
- `ax2.set_ylabel`
- `ax2.set_xlabel`
- `ax2.set_title`
- `ax2.set_ylim`
- `ax2.set_xlim`
- `ax2.legend`
- `fig.tight_layout`
- `output_path.parent.mkdir`
- `save_figure`
- `plt.close`

### `generate_landing_validation_map_chart`

[Implementação: source/antares_fd/reporting/charts.py:564](../../source/antares_fd/reporting/charts.py#L564)

```python
generate_landing_validation_map_chart(validation_data: Dict[str, Any], output_path: Path) -> Optional[Path]
```

Generates high-resolution Cartographic V&V Map:
Pad ★, Predicted Touchdown ●, Actual Fuselage ×, Actual Nose Cone ×
Concentric range rings (500m, 1000m, 1500m) and error vectors.

**Entradas e tipos declarados**

- `validation_data: Dict[str, Any]`
- `output_path: Path`

**Retornos/yields explícitos**

- `None`
- `output_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `validation_data.get`
- `setup_matplotlib_theme`
- `plt.subplots`
- `plt.Circle`
- `ax.add_patch`
- `ax.text`
- `ax.scatter`
- `ax.plot`
- `abs`
- `ax.set_xlabel`
- `ax.set_ylabel`
- `ax.set_title`
- `ax.axis`
- `ax.legend`
- `fig.tight_layout`
- `output_path.parent.mkdir`
- `save_figure`
- `plt.close`

### `generate_mc_dispersion_chart`

[Implementação: source/antares_fd/reporting/charts.py:614](../../source/antares_fd/reporting/charts.py#L614)

```python
generate_mc_dispersion_chart(outputs_file: Path, output_path: Path, run_id: str, validation_data: Optional[Dict[str, Any]]=None) -> Optional[Path]
```

Generates 2D Ground Dispersion with 50%, 90%, 95%, 99% covariance ellipses and KDE contours.

**Entradas e tipos declarados**

- `outputs_file: Path`
- `output_path: Path`
- `run_id: str`
- `validation_data: Optional[Dict[str, Any]]`

**Retornos/yields explícitos**

- `None`
- `output_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `outputs_file.exists`
- `read_jsonl_objects`
- `x_impact.append`
- `y_impact.append`
- `len`
- `setup_matplotlib_theme`
- `np.array`
- `plt.subplots`
- `ax.scatter`
- `calculate_covariance_ellipse`
- `Ellipse`
- `ax.add_patch`
- `validation_data.get`
- `ax.set_xlabel`
- `ax.set_ylabel`
- `ax.set_title`
- `ax.axis`
- `ax.legend`
- `fig.tight_layout`
- `output_path.parent.mkdir`
- `save_figure`
- `plt.close`

### `generate_mc_distributions_chart`

[Implementação: source/antares_fd/reporting/charts.py:678](../../source/antares_fd/reporting/charts.py#L678)

```python
generate_mc_distributions_chart(outputs_file: Path, output_path: Path) -> Optional[Path]
```

Generates 4-panel Monte Carlo statistical distribution histograms.

**Entradas e tipos declarados**

- `outputs_file: Path`
- `output_path: Path`

**Retornos/yields explícitos**

- `None`
- `output_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `outputs_file.exists`
- `read_jsonl_objects`
- `len`
- `pd.DataFrame`
- `all`
- `setup_matplotlib_theme`
- `plt.subplots`
- `ax1.hist`
- `df['apogee'].mean`
- `df['apogee'].std`
- `ax1.axvline`
- `ax1.set_xlabel`
- `ax1.set_ylabel`
- `ax1.set_title`
- `ax1.legend`
- `ax2.hist`
- `df['out_of_rail_velocity'].mean`
- `ax2.axvline`
- `ax2.set_xlabel`
- `ax2.set_ylabel`
- `ax2.set_title`
- `ax2.legend`
- `ax3.hist`
- `df['max_mach_number'].mean`
- `ax3.axvline`
- `ax3.set_xlabel`
- `ax3.set_ylabel`
- `ax3.set_title`
- `ax3.legend`
- `np.abs`
- `ax4.hist`
- `imp_vel.mean`
- `ax4.axvline`
- `ax4.set_xlabel`
- `ax4.set_ylabel`
- `ax4.set_title`
- `ax4.legend`
- `fig.suptitle`
- `fig.tight_layout`
- `output_path.parent.mkdir`
- `save_figure`
- `plt.close`

### `generate_mc_convergence_chart`

[Implementação: source/antares_fd/reporting/charts.py:747](../../source/antares_fd/reporting/charts.py#L747)

```python
generate_mc_convergence_chart(outputs_file: Path, output_path: Path) -> Optional[Path]
```

Generates Running Mean and Standard Deviation stabilization curves.

**Entradas e tipos declarados**

- `outputs_file: Path`
- `output_path: Path`

**Retornos/yields explícitos**

- `None`
- `output_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `outputs_file.exists`
- `read_jsonl_objects`
- `len`
- `pd.DataFrame`
- `setup_matplotlib_theme`
- `df['apogee'].expanding().mean`
- `df['apogee'].expanding`
- `df['apogee'].expanding().std`
- `np.arange`
- `plt.subplots`
- `ax1.plot`
- `ax1.fill_between`
- `ax1.set_ylabel`
- `ax1.set_title`
- `ax1.legend`
- `ax2.plot`
- `ax2.axhline`
- `ax2.set_ylim`
- `ax2.set_ylabel`
- `ax2.set_xlabel`
- `ax2.legend`
- `fig.tight_layout`
- `output_path.parent.mkdir`
- `save_figure`
- `plt.close`

### `generate_sensitivity_tornado_chart`

[Implementação: source/antares_fd/reporting/charts.py:799](../../source/antares_fd/reporting/charts.py#L799)

```python
generate_sensitivity_tornado_chart(sensitivity_data: Dict[str, Any], output_path: Path) -> Optional[Path]
```

Generates a horizontal Tornado Bar Chart of parameter sensitivities.

**Entradas e tipos declarados**

- `sensitivity_data: Dict[str, Any]`
- `output_path: Path`

**Retornos/yields explícitos**

- `None`
- `output_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `sensitivity_data.get`
- `setup_matplotlib_theme`
- `top_items.reverse`
- `item['parameter'].replace('_', ' ').title`
- `item['parameter'].replace`
- `plt.subplots`
- `np.arange`
- `len`
- `ax.barh`
- `ax.set_yticks`
- `ax.set_yticklabels`
- `ax.axvline`
- `ax.set_xlim`
- `ax.set_xlabel`
- `sensitivity_data.get('sensitivity_target', 'Metric').replace('_', ' ').title`
- `sensitivity_data.get('sensitivity_target', 'Metric').replace`
- `ax.set_title`
- `zip`
- `bar.get_width`
- `ax.text`
- `bar.get_y`
- `bar.get_height`
- `fig.tight_layout`
- `output_path.parent.mkdir`
- `save_figure`
- `plt.close`

## `source/antares_fd/reporting/pdf_report.py`

FlightDynamicsReport entrypoint.
Constructs the deterministc PDF report using the strict, single-source-of-truth FlightMetrics architecture,
also handling multiple campaigns and Monte Carlo statistics.

### `CustomJSONEncoder.default`

[Implementação: source/antares_fd/reporting/pdf_report.py:19](../../source/antares_fd/reporting/pdf_report.py#L19)

```python
CustomJSONEncoder.default(self, obj)
```

Serialize dataclasses e objetos NumPy no arquivo de métricas.

Converte dataclass em dict, ndarray em lista e escalares NumPy em escalares
Python. Tipos não suportados seguem o erro padrão de JSONEncoder.

**Entradas e tipos declarados**

- `obj: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `dataclasses.asdict(obj)`
- `obj.tolist()`
- `obj.item()`
- `super().default(obj)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `dataclasses.is_dataclass`
- `dataclasses.asdict`
- `isinstance`
- `obj.tolist`
- `hasattr`
- `obj.item`
- `super().default`
- `super`

### `FlightDynamicsReport.__init__`

[Implementação: source/antares_fd/reporting/pdf_report.py:38](../../source/antares_fd/reporting/pdf_report.py#L38)

```python
FlightDynamicsReport.__init__(self, flight: Any=None, config: Any=None, project_dir: Optional[Path]=None, mc_results_dir: Optional[Path]=None, run_id: str='nominal', scenario_flights: Optional[Dict[str, Any]]=None, artifact_dir: Optional[Path]=None)
```

Prepare um relatório a partir de voos ou de artefatos canônicos.

Extrai métricas uma vez para os voos recebidos; no modo artifact_dir, exige
master_metrics.json válido e não cria contexto que reavalie física.
Sem qualquer fonte de métricas, lança ValueError.

**Entradas e tipos declarados**

- `flight: Any`
- `config: Any`
- `project_dir: Optional[Path]`
- `mc_results_dir: Optional[Path]`
- `run_id: str`
- `scenario_flights: Optional[Dict[str, Any]]`
- `artifact_dir: Optional[Path]`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- `ValueError('No Flight provided to report.')`

**Colaboradores chamados diretamente**

- `Path.cwd`
- `Path`
- `scenario_flights.items`
- `extract_flight_metrics`
- `list`
- `self.scenario_metrics.values`
- `_load_artifact_metrics`
- `_namespace`
- `ValueError`
- `Path(__file__).with_name`
- `RequirementDB`
- `ReportContext`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `FlightDynamicsReport.from_artifacts`

[Implementação: source/antares_fd/reporting/pdf_report.py:84](../../source/antares_fd/reporting/pdf_report.py#L84)

```python
FlightDynamicsReport.from_artifacts(cls, artifact_dir: Path, project_dir: Optional[Path]=None)
```

Create a report object that can only consume saved artifacts.

**Entradas e tipos declarados**

- `artifact_dir: Path`
- `project_dir: Optional[Path]`

**Retornos/yields explícitos**

- `cls(project_dir=project_dir or artifact_dir.parents[2], mc_results_dir=artifact_dir, run_id=run_id, artifact_dir=artifact_dir)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `Path`
- `_read_json_file`
- `payload.get`
- `payload.get('campaign', {}).get`
- `cls`

### `FlightDynamicsReport.generate`

[Implementação: source/antares_fd/reporting/pdf_report.py:91](../../source/antares_fd/reporting/pdf_report.py#L91)

```python
FlightDynamicsReport.generate(self, output_path: Path)
```

Build a vector PDF from canonical metrics and saved campaign data.

**Entradas e tipos declarados**

- `output_path: Path`

**Retornos/yields explícitos**

- `output_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `output_path.parent.mkdir`
- `dataclasses.is_dataclass`
- `dataclasses.asdict`
- `metrics_dict.pop`
- `_plain`
- `vars`
- `open`
- `json.dump`
- `print`
- `VectorReportRenderer`
- `renderer.render`

### `_read_json_file`

[Implementação: source/antares_fd/reporting/pdf_report.py:117](../../source/antares_fd/reporting/pdf_report.py#L117)

```python
_read_json_file(path: Path)
```

Leia metadados JSON opcionais de um caminho.

Retorna o conteúdo desserializado, ou None se a leitura ou sintaxe falhar.
Não deve ser usado para aceitar métricas obrigatórias incompletas.

**Entradas e tipos declarados**

- `path: Path`

**Retornos/yields explícitos**

- `json.loads(path.read_text(encoding='utf-8'))`
- `None`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `json.loads`
- `path.read_text`

### `_load_artifact_metrics`

[Implementação: source/antares_fd/reporting/pdf_report.py:129](../../source/antares_fd/reporting/pdf_report.py#L129)

```python
_load_artifact_metrics(path: Path) -> dict
```

Load canonical metrics or fail visibly; partial JSON is not evidence.

**Entradas e tipos declarados**

- `path: Path`

**Retornos/yields explícitos**

- `payload`

**Exceções lançadas explicitamente**

- `ValueError(f'Metrics artifact must contain a JSON object: {path}')`

**Colaboradores chamados diretamente**

- `json.loads`
- `Path(path).read_text`
- `Path`
- `isinstance`
- `ValueError`

### `_plain`

[Implementação: source/antares_fd/reporting/pdf_report.py:137](../../source/antares_fd/reporting/pdf_report.py#L137)

```python
_plain(value)
```

Converta namespaces aninhados em estruturas serializáveis.

Percorre dicts, sequências e atributos de objetos, preservando escalares.
A conversão recursiva cria estruturas novas e não modifica a entrada.

**Entradas e tipos declarados**

- `value: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `{key: _plain(item) for key, item in value.items()}`
- `[_plain(item) for item in value]`
- `_plain(vars(value))`
- `value`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `isinstance`
- `_plain`
- `value.items`
- `hasattr`
- `vars`

## `source/antares_fd/reporting/plot_registry.py`

Chart Generation for Antares Engineering Reports.
Consumes ONLY FlightMetrics. No RocketPy dependencies allowed.

### `_get_flight_events`

[Implementação: source/antares_fd/reporting/plot_registry.py:21](../../source/antares_fd/reporting/plot_registry.py#L21)

```python
_get_flight_events(metrics: FlightMetrics) -> List[tuple[float, str]]
```

Extracts key event timestamps from FlightMetrics.

**Entradas e tipos declarados**

- `metrics: FlightMetrics`

**Retornos/yields explícitos**

- `events`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `events.append`
- `events.sort`

### `_add_event_lines`

[Implementação: source/antares_fd/reporting/plot_registry.py:41](../../source/antares_fd/reporting/plot_registry.py#L41)

```python
_add_event_lines(ax, events: List[tuple[float, str]], max_t: Optional[float]=None, color: str='#64748B')
```

Annotates vertical event lines on an axes.

**Entradas e tipos declarados**

- `ax: tipo não anotado; ver contrato acima`
- `events: List[tuple[float, str]]`
- `max_t: Optional[float]`
- `color: str`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `ax.get_xlim`
- `ax.get_ylim`
- `ax.axvline`
- `ax.text`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `generate_mass_and_propulsion_chart`

[Implementação: source/antares_fd/reporting/plot_registry.py:56](../../source/antares_fd/reporting/plot_registry.py#L56)

```python
generate_mass_and_propulsion_chart(metrics: FlightMetrics, output_path: Path) -> Path
```

Gere o gráfico de empuxo, razão empuxo/peso, consumo de massa e impulso acumulado.

Recebe FlightMetrics (ou mapeamento por cenário) e output_path; usa
as séries e eventos já extraídos, sem acessar o integrador RocketPy.
Salva a figura vetorial, fecha recursos gráficos e retorna seu caminho.
Unidades e instantes seguem o contrato canônico das métricas.

**Entradas e tipos declarados**

- `metrics: FlightMetrics`
- `output_path: Path`

**Retornos/yields explícitos**

- `output_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `setup_matplotlib_theme`
- `np.maximum`
- `np.diff`
- `np.cumsum`
- `plt.subplots`
- `ax1.plot`
- `ax1.fill_between`
- `ax1.set_ylabel`
- `ax1.tick_params`
- `ax1.set_ylim`
- `ax1.twinx`
- `ax1_tw.plot`
- `ax1_tw.set_ylabel`
- `ax1_tw.tick_params`
- `ax1_tw.set_ylim`
- `ax1.set_title`
- `ax2.plot`
- `ax2.axhline`
- `ax2.set_ylabel`
- `ax2.legend`
- `ax2.set_ylim`
- `ax3.plot`
- `ax3.axhline`
- `ax3.set_ylabel`
- `ax3.set_xlabel`
- `ax3.legend`
- `ax3.set_xlim`
- `fig.tight_layout`
- `output_path.parent.mkdir`
- `save_figure`
- `plt.close`

### `generate_kinematics_chart`

[Implementação: source/antares_fd/reporting/plot_registry.py:121](../../source/antares_fd/reporting/plot_registry.py#L121)

```python
generate_kinematics_chart(metrics: FlightMetrics, output_path: Path) -> Path
```

Gere o gráfico de altitude, velocidade e aceleração ao longo do voo.

Recebe FlightMetrics (ou mapeamento por cenário) e output_path; usa
as séries e eventos já extraídos, sem acessar o integrador RocketPy.
Salva a figura vetorial, fecha recursos gráficos e retorna seu caminho.
Unidades e instantes seguem o contrato canônico das métricas.

**Entradas e tipos declarados**

- `metrics: FlightMetrics`
- `output_path: Path`

**Retornos/yields explícitos**

- `output_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `setup_matplotlib_theme`
- `_get_flight_events`
- `plt.subplots`
- `ax1.plot`
- `ax1.set_ylabel`
- `ax1.set_title`
- `ax1.legend`
- `_add_event_lines`
- `ax2.plot`
- `ax2.set_ylabel`
- `ax2.tick_params`
- `ax2.twinx`
- `ax2_mach.plot`
- `ax2_mach.set_ylabel`
- `ax2_mach.tick_params`
- `ax3.plot`
- `ax3.annotate`
- `dict`
- `ax3.set_ylabel`
- `ax3.set_xlabel`
- `ax3.legend`
- `fig.tight_layout`
- `output_path.parent.mkdir`
- `save_figure`
- `plt.close`

### `generate_propulsion_and_loads_chart`

[Implementação: source/antares_fd/reporting/plot_registry.py:187](../../source/antares_fd/reporting/plot_registry.py#L187)

```python
generate_propulsion_and_loads_chart(metrics: FlightMetrics, output_path: Path) -> Path
```

Gere o gráfico de pressão dinâmica e cargas aerodinâmicas após a saída da rampa.

Recebe FlightMetrics (ou mapeamento por cenário) e output_path; usa
as séries e eventos já extraídos, sem acessar o integrador RocketPy.
Salva a figura vetorial, fecha recursos gráficos e retorna seu caminho.
Unidades e instantes seguem o contrato canônico das métricas.

**Entradas e tipos declarados**

- `metrics: FlightMetrics`
- `output_path: Path`

**Retornos/yields explícitos**

- `output_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `setup_matplotlib_theme`
- `_get_flight_events`
- `plt.subplots`
- `ax1.plot`
- `ax1.set_ylabel`
- `ax1.set_ylim`
- `ax1.annotate`
- `dict`
- `ax1.set_title`
- `_add_event_lines`
- `ax2.plot`
- `ax2.fill_between`
- `ax2.set_ylabel`
- `ax2.set_xlabel`
- `ax2.set_ylim`
- `ax2.annotate`
- `fig.tight_layout`
- `output_path.parent.mkdir`
- `save_figure`
- `plt.close`

### `generate_stability_and_attitude_chart`

[Implementação: source/antares_fd/reporting/plot_registry.py:255](../../source/antares_fd/reporting/plot_registry.py#L255)

```python
generate_stability_and_attitude_chart(metrics: FlightMetrics, output_path: Path) -> Path
```

Gere o gráfico de CG, CP, margem estática e ângulo de ataque.

Recebe FlightMetrics (ou mapeamento por cenário) e output_path; usa
as séries e eventos já extraídos, sem acessar o integrador RocketPy.
Salva a figura vetorial, fecha recursos gráficos e retorna seu caminho.
Unidades e instantes seguem o contrato canônico das métricas.

**Entradas e tipos declarados**

- `metrics: FlightMetrics`
- `output_path: Path`

**Retornos/yields explícitos**

- `output_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `setup_matplotlib_theme`
- `_get_flight_events`
- `plt.subplots`
- `ax1.plot`
- `ax1.fill_between`
- `ax1.set_ylabel`
- `ax1.set_xlim`
- `ax1.legend`
- `ax1.set_title`
- `_add_event_lines`
- `ax2.plot`
- `ax2.axhspan`
- `ax2.axhline`
- `ax2.annotate`
- `dict`
- `ax2.set_ylabel`
- `ax2.set_xlabel`
- `ax2.set_ylim`
- `max`
- `float`
- `np.max`
- `ax2.legend`
- `fig.tight_layout`
- `output_path.parent.mkdir`
- `save_figure`
- `plt.close`

### `generate_full_atmosphere_chart`

[Implementação: source/antares_fd/reporting/plot_registry.py:315](../../source/antares_fd/reporting/plot_registry.py#L315)

```python
generate_full_atmosphere_chart(metrics: FlightMetrics, output_path: Path) -> Path
```

Gere o gráfico de temperatura, pressão, densidade e vento do perfil atmosférico usado.

Recebe FlightMetrics (ou mapeamento por cenário) e output_path; usa
as séries e eventos já extraídos, sem acessar o integrador RocketPy.
Salva a figura vetorial, fecha recursos gráficos e retorna seu caminho.
Unidades e instantes seguem o contrato canônico das métricas.

**Entradas e tipos declarados**

- `metrics: FlightMetrics`
- `output_path: Path`

**Retornos/yields explícitos**

- `output_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `setup_matplotlib_theme`
- `plt.subplots`
- `ax1.plot`
- `ax1.set_xlabel`
- `ax1.set_ylabel`
- `ax1.set_title`
- `ax1.set_xlim`
- `ax2.plot`
- `ax2.set_xlabel`
- `ax2.set_ylabel`
- `ax2.set_title`
- `ax2.set_xlim`
- `ax3.plot`
- `ax3.set_xlabel`
- `ax3.set_ylabel`
- `ax3.tick_params`
- `ax3.twiny`
- `ax3_c.plot`
- `ax3_c.set_xlabel`
- `ax3_c.tick_params`
- `ax3.set_title`
- `ax4.plot`
- `len`
- `ax4.scatter`
- `ax4.axhline`
- `ax4.axvline`
- `ax4.set_xlabel`
- `ax4.set_ylabel`
- `ax4.set_title`
- `ax4.axis`
- `ax4.legend`
- `fig.suptitle`
- `fig.tight_layout`
- `output_path.parent.mkdir`
- `save_figure`
- `plt.close`

### `generate_recovery_descent_chart`

[Implementação: source/antares_fd/reporting/plot_registry.py:376](../../source/antares_fd/reporting/plot_registry.py#L376)

```python
generate_recovery_descent_chart(metrics: FlightMetrics, output_path: Path) -> Path
```

Gere o gráfico de altitude e velocidade de descida com os eventos de recuperação.

Recebe FlightMetrics (ou mapeamento por cenário) e output_path; usa
as séries e eventos já extraídos, sem acessar o integrador RocketPy.
Salva a figura vetorial, fecha recursos gráficos e retorna seu caminho.
Unidades e instantes seguem o contrato canônico das métricas.

**Entradas e tipos declarados**

- `metrics: FlightMetrics`
- `output_path: Path`

**Retornos/yields explícitos**

- `output_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `setup_matplotlib_theme`
- `_get_flight_events`
- `plt.subplots`
- `ax1.plot`
- `ax1.set_ylabel`
- `ax1.set_xlim`
- `ax1.set_title`
- `ax1.legend`
- `_add_event_lines`
- `np.abs`
- `ax2.plot`
- `ax2.axhline`
- `ax2.set_ylabel`
- `ax2.set_xlabel`
- `ax2.legend`
- `fig.tight_layout`
- `output_path.parent.mkdir`
- `save_figure`
- `plt.close`

### `generate_trajectory_views_chart`

[Implementação: source/antares_fd/reporting/plot_registry.py:419](../../source/antares_fd/reporting/plot_registry.py#L419)

```python
generate_trajectory_views_chart(metrics: FlightMetrics, output_path: Path) -> Path
```

Gere o gráfico de trajetória em vistas lateral e do plano de solo.

Recebe FlightMetrics (ou mapeamento por cenário) e output_path; usa
as séries e eventos já extraídos, sem acessar o integrador RocketPy.
Salva a figura vetorial, fecha recursos gráficos e retorna seu caminho.
Unidades e instantes seguem o contrato canônico das métricas.

**Entradas e tipos declarados**

- `metrics: FlightMetrics`
- `output_path: Path`

**Retornos/yields explícitos**

- `output_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `setup_matplotlib_theme`
- `plt.subplots`
- `np.hypot`
- `ax1.plot`
- `int`
- `np.argmax`
- `ax1.scatter`
- `ax1.set_xlabel`
- `ax1.set_ylabel`
- `ax1.set_title`
- `ax1.legend`
- `ax2.plot`
- `ax2.scatter`
- `ax2.set_xlabel`
- `ax2.set_ylabel`
- `ax2.set_title`
- `ax2.axis`
- `ax2.legend`
- `fig.tight_layout`
- `output_path.parent.mkdir`
- `save_figure`
- `plt.close`

### `generate_multi_scenario_chart`

[Implementação: source/antares_fd/reporting/plot_registry.py:465](../../source/antares_fd/reporting/plot_registry.py#L465)

```python
generate_multi_scenario_chart(scenario_metrics: Dict[str, FlightMetrics], output_path: Path) -> Path
```

Gere o gráfico de comparação das séries canônicas entre cenários.

Recebe FlightMetrics (ou mapeamento por cenário) e output_path; usa
as séries e eventos já extraídos, sem acessar o integrador RocketPy.
Salva a figura vetorial, fecha recursos gráficos e retorna seu caminho.
Unidades e instantes seguem o contrato canônico das métricas.

**Entradas e tipos declarados**

- `scenario_metrics: Dict[str, FlightMetrics]`
- `output_path: Path`

**Retornos/yields explícitos**

- `output_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `setup_matplotlib_theme`
- `plt.subplots`
- `scenario_metrics.items`
- `np.hypot`
- `max`
- `styles_map.get`
- `ax1.plot`
- `ax1.scatter`
- `ax2.plot`
- `ax2.scatter`
- `ax1.set_ylabel`
- `ax1.set_title`
- `ax1.set_ylim`
- `ax1.set_xlim`
- `ax1.legend`
- `ax2.set_ylabel`
- `ax2.set_xlabel`
- `ax2.set_title`
- `ax2.set_ylim`
- `ax2.set_xlim`
- `ax2.legend`
- `fig.tight_layout`
- `output_path.parent.mkdir`
- `save_figure`
- `plt.close`

### `generate_landing_validation_map_chart`

[Implementação: source/antares_fd/reporting/plot_registry.py:524](../../source/antares_fd/reporting/plot_registry.py#L524)

```python
generate_landing_validation_map_chart(validation_data: Dict[str, Any], output_path: Path) -> Optional[Path]
```

Generates high-resolution Cartographic V&V Map:
Pad ★, Predicted Touchdown ●, Actual Fuselage ×, Actual Nose Cone ×
Concentric range rings (500m, 1000m, 1500m) and error vectors.

**Entradas e tipos declarados**

- `validation_data: Dict[str, Any]`
- `output_path: Path`

**Retornos/yields explícitos**

- `None`
- `output_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `validation_data.get`
- `setup_matplotlib_theme`
- `plt.subplots`
- `plt.Circle`
- `ax.add_patch`
- `ax.text`
- `ax.scatter`
- `ax.plot`
- `abs`
- `ax.set_xlabel`
- `ax.set_ylabel`
- `ax.set_title`
- `ax.axis`
- `ax.legend`
- `fig.tight_layout`
- `output_path.parent.mkdir`
- `save_figure`
- `plt.close`

### `generate_mc_dispersion_chart`

[Implementação: source/antares_fd/reporting/plot_registry.py:574](../../source/antares_fd/reporting/plot_registry.py#L574)

```python
generate_mc_dispersion_chart(outputs_file: Path, output_path: Path, run_id: str, validation_data: Optional[Dict[str, Any]]=None) -> Optional[Path]
```

Generates 2D Ground Dispersion with 50%, 90%, 95%, 99% covariance ellipses and KDE contours.

**Entradas e tipos declarados**

- `outputs_file: Path`
- `output_path: Path`
- `run_id: str`
- `validation_data: Optional[Dict[str, Any]]`

**Retornos/yields explícitos**

- `None`
- `output_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `outputs_file.exists`
- `read_jsonl_objects`
- `x_impact.append`
- `y_impact.append`
- `len`
- `setup_matplotlib_theme`
- `np.array`
- `plt.subplots`
- `ax.scatter`
- `calculate_covariance_ellipse`
- `Ellipse`
- `ax.add_patch`
- `validation_data.get`
- `ax.set_xlabel`
- `ax.set_ylabel`
- `ax.set_title`
- `ax.axis`
- `ax.legend`
- `fig.tight_layout`
- `output_path.parent.mkdir`
- `save_figure`
- `plt.close`

### `generate_mc_distributions_chart`

[Implementação: source/antares_fd/reporting/plot_registry.py:640](../../source/antares_fd/reporting/plot_registry.py#L640)

```python
generate_mc_distributions_chart(outputs_file: Path, output_path: Path) -> Optional[Path]
```

Generates 4-panel Monte Carlo statistical distribution histograms.

**Entradas e tipos declarados**

- `outputs_file: Path`
- `output_path: Path`

**Retornos/yields explícitos**

- `None`
- `output_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `outputs_file.exists`
- `read_jsonl_objects`
- `len`
- `pd.DataFrame`
- `all`
- `setup_matplotlib_theme`
- `plt.subplots`
- `ax1.hist`
- `df['apogee'].mean`
- `df['apogee'].std`
- `ax1.axvline`
- `ax1.set_xlabel`
- `ax1.set_ylabel`
- `ax1.set_title`
- `ax1.legend`
- `ax2.hist`
- `df['out_of_rail_velocity'].mean`
- `ax2.axvline`
- `ax2.set_xlabel`
- `ax2.set_ylabel`
- `ax2.set_title`
- `ax2.legend`
- `ax3.hist`
- `df['max_mach_number'].mean`
- `ax3.axvline`
- `ax3.set_xlabel`
- `ax3.set_ylabel`
- `ax3.set_title`
- `ax3.legend`
- `np.abs`
- `ax4.hist`
- `imp_vel.mean`
- `ax4.axvline`
- `ax4.set_xlabel`
- `ax4.set_ylabel`
- `ax4.set_title`
- `ax4.legend`
- `fig.suptitle`
- `fig.tight_layout`
- `output_path.parent.mkdir`
- `save_figure`
- `plt.close`

### `generate_mc_convergence_chart`

[Implementação: source/antares_fd/reporting/plot_registry.py:709](../../source/antares_fd/reporting/plot_registry.py#L709)

```python
generate_mc_convergence_chart(outputs_file: Path, output_path: Path) -> Optional[Path]
```

Generates Running Mean and Standard Deviation stabilization curves.

**Entradas e tipos declarados**

- `outputs_file: Path`
- `output_path: Path`

**Retornos/yields explícitos**

- `None`
- `output_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `outputs_file.exists`
- `read_jsonl_objects`
- `len`
- `pd.DataFrame`
- `setup_matplotlib_theme`
- `df['apogee'].expanding().mean`
- `df['apogee'].expanding`
- `df['apogee'].expanding().std`
- `np.arange`
- `plt.subplots`
- `ax1.plot`
- `ax1.fill_between`
- `ax1.set_ylabel`
- `ax1.set_title`
- `ax1.legend`
- `ax2.plot`
- `ax2.axhline`
- `ax2.set_ylim`
- `ax2.set_ylabel`
- `ax2.set_xlabel`
- `ax2.legend`
- `fig.tight_layout`
- `output_path.parent.mkdir`
- `save_figure`
- `plt.close`

### `generate_sensitivity_tornado_chart`

[Implementação: source/antares_fd/reporting/plot_registry.py:761](../../source/antares_fd/reporting/plot_registry.py#L761)

```python
generate_sensitivity_tornado_chart(sensitivity_data: Dict[str, Any], output_path: Path) -> Optional[Path]
```

Generates a horizontal Tornado Bar Chart of parameter sensitivities.

**Entradas e tipos declarados**

- `sensitivity_data: Dict[str, Any]`
- `output_path: Path`

**Retornos/yields explícitos**

- `None`
- `output_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `sensitivity_data.get`
- `setup_matplotlib_theme`
- `top_items.reverse`
- `item['parameter'].replace('_', ' ').title`
- `item['parameter'].replace`
- `plt.subplots`
- `np.arange`
- `len`
- `ax.barh`
- `ax.set_yticks`
- `ax.set_yticklabels`
- `ax.axvline`
- `ax.set_xlim`
- `ax.set_xlabel`
- `sensitivity_data.get('sensitivity_target', 'Metric').replace('_', ' ').title`
- `sensitivity_data.get('sensitivity_target', 'Metric').replace`
- `ax.set_title`
- `zip`
- `bar.get_width`
- `ax.text`
- `bar.get_y`
- `bar.get_height`
- `fig.tight_layout`
- `output_path.parent.mkdir`
- `save_figure`
- `plt.close`

## `source/antares_fd/reporting/qa.py`

Automated PDF and artifact quality checks for engineering reports.

### `render_report_pages`

[Implementação: source/antares_fd/reporting/qa.py:20](../../source/antares_fd/reporting/qa.py#L20)

```python
render_report_pages(pdf_path: Path, output_dir: Path, dpi: int=180) -> list[Path]
```

Render every PDF page for automated visual inspection.

**Entradas e tipos declarados**

- `pdf_path: Path`
- `output_dir: Path`
- `dpi: int`

**Retornos/yields explícitos**

- `[]`
- `pages`
- `sorted(output_dir.glob('page-*.png'))`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `Path`
- `output_dir.mkdir`
- `output_dir.glob`
- `old.unlink`
- `shutil.which`
- `str`
- `int`
- `fitz.open`
- `float`
- `fitz.Matrix`
- `enumerate`
- `page.get_pixmap(matrix=matrix, alpha=False).save`
- `page.get_pixmap`
- `pages.append`
- `subprocess.run`
- `sorted`

### `inspect_report`

[Implementação: source/antares_fd/reporting/qa.py:52](../../source/antares_fd/reporting/qa.py#L52)

```python
inspect_report(pdf_path: Path, figures_dir: Path | None=None, render_dir: Path | None=None) -> dict[str, Any]
```

Return deterministic QA findings without requiring a PDF GUI tool.

**Entradas e tipos declarados**

- `pdf_path: Path`
- `figures_dir: Path | None`
- `render_dir: Path | None`

**Retornos/yields explícitos**

- `{'exists': path.exists(), 'page_count': pages, 'blank_pages': blank_pages, 'missing_headings': missing_headings, 'vector_figures': vector_figures, 'raster_engineering_figures': normal_plot_pngs, 'page_rasterization': 'not available: install pdftoppm or Ghostscript' if not _has_rasterizer() else 'available', 'rendered_pages': len(rendered_pages), 'visual_qa_complete': visual_qa_available, 'passed': bool(path.exists() and pages > 0 and (not missing_headings) and (not normal_plot_pngs) and (not blank_pages) and visual_qa_available)}`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `Path`
- `path.exists`
- `path.read_bytes`
- `len`
- `re.findall`
- `data.decode`
- `manifest_path.exists`
- `json.loads`
- `manifest_path.read_text`
- `manifest.get`
- `sorted`
- `Path(figures_dir).rglob`
- `item.is_file`
- `item.resolve`
- `path.resolve`
- `_portable`
- `item.suffix.lower`
- `render_report_pages`
- `bool`
- `Image.open(page).convert`
- `Image.open`
- `ImageStat.Stat`
- `blank_pages.append`
- `str`
- `_has_rasterizer`

### `inspect_report._portable`

[Implementação: source/antares_fd/reporting/qa.py:74](../../source/antares_fd/reporting/qa.py#L74)

```python
inspect_report._portable(item: Path) -> str
```

Converta um caminho de artefato em identificação portável para o relatório.

Prioriza referências relativas ao diretório examinado; usa o nome do arquivo
quando a relativização não é possível. Não altera o arquivo.

**Entradas e tipos declarados**

- `item: Path`

**Retornos/yields explícitos**

- `item.resolve().relative_to(Path(figures_dir).resolve()).as_posix()`
- `item.name`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `item.resolve().relative_to(Path(figures_dir).resolve()).as_posix`
- `item.resolve().relative_to`
- `item.resolve`
- `Path(figures_dir).resolve`
- `Path`

### `_has_rasterizer`

[Implementação: source/antares_fd/reporting/qa.py:119](../../source/antares_fd/reporting/qa.py#L119)

```python
_has_rasterizer() -> bool
```

Verifique se há um renderizador PDF disponível para inspeção.

Consulta ferramentas opcionais instaladas e retorna bool, permitindo
registrar a limitação sem simular uma verificação visual.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `bool(shutil.which('pdftoppm') or shutil.which('mutool') or shutil.which('gswin64c') or shutil.which('magick'))`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `bool`
- `shutil.which`

### `assert_report_quality`

[Implementação: source/antares_fd/reporting/qa.py:129](../../source/antares_fd/reporting/qa.py#L129)

```python
assert_report_quality(pdf_path: Path, figures_dir: Path | None=None) -> dict[str, Any]
```

Exija aprovação das verificações automáticas do PDF.

Chama inspect_report e lança AssertionError quando o resultado contém falhas.
Lê pdf_path e figures_dir sem recalcular os dados de engenharia.
Retorna o diagnóstico completo quando aprovado.

**Entradas e tipos declarados**

- `pdf_path: Path`
- `figures_dir: Path | None`

**Retornos/yields explícitos**

- `result`

**Exceções lançadas explicitamente**

- `AssertionError(result)`

**Colaboradores chamados diretamente**

- `inspect_report`
- `AssertionError`

## `source/antares_fd/reporting/tables.py`

ReportLab Table Formatters for Antares Engineering Reports.

### `_get_badge`

[Implementação: source/antares_fd/reporting/tables.py:22](../../source/antares_fd/reporting/tables.py#L22)

```python
_get_badge(status: str, style_base: ParagraphStyle) -> Paragraph
```

Generates a color-coded status badge Paragraph.

**Entradas e tipos declarados**

- `status: str`
- `style_base: ParagraphStyle`

**Retornos/yields explícitos**

- `Paragraph(text, badge_style)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `str(status).upper().strip`
- `str(status).upper`
- `str`
- `ParagraphStyle`
- `Paragraph`

### `_cell`

[Implementação: source/antares_fd/reporting/tables.py:51](../../source/antares_fd/reporting/tables.py#L51)

```python
_cell(value: Any, header: bool=False) -> Any
```

Converta um valor em célula ReportLab com quebra de texto.

Mantém Paragraph existente; nos demais casos, aplica estilo de cabeçalho
ou corpo e escapa ampersands. Retorna Paragraph para uso na tabela.

**Entradas e tipos declarados**

- `value: Any`
- `header: bool`

**Retornos/yields explícitos**

- `value`
- `Paragraph(str(value).replace('&', '&amp;'), style)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `isinstance`
- `ParagraphStyle`
- `Paragraph`
- `str(value).replace`
- `str`

### `create_standard_table`

[Implementação: source/antares_fd/reporting/tables.py:70](../../source/antares_fd/reporting/tables.py#L70)

```python
create_standard_table(data_matrix: List[List[Any]], col_widths: Optional[List[float]]=None, landscape: bool=False) -> Table
```

Construa uma tabela paginável com cabeçalho repetido.

Preenche linhas curtas com células vazias e calcula larguras proporcionais
quando col_widths não é informado. landscape seleciona a largura útil.
Retorna LongTable estilizada; matriz vazia produz indicação NO DATA.

**Entradas e tipos declarados**

- `data_matrix: List[List[Any]]`
- `col_widths: Optional[List[float]]`
- `landscape: bool`

**Retornos/yields explícitos**

- `Table([['NO DATA']])`
- `t`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `Table`
- `max`
- `len`
- `list`
- `range`
- `str`
- `weights.append`
- `min`
- `sum`
- `_cell`
- `enumerate`
- `LongTable`
- `t.setStyle`
- `TableStyle`
- `colors.HexColor`

### `build_model_validity_envelope_table`

[Implementação: source/antares_fd/reporting/tables.py:108](../../source/antares_fd/reporting/tables.py#L108)

```python
build_model_validity_envelope_table(validity_data: List[Dict[str, Any]], styles: Any) -> Table
```

Formate limites e avaliações de validade física em uma tabela.

Percorre validity_data, acrescenta domínio, pico, limite, status e nota
e aplica indicadores de classificação com os estilos recebidos.

**Entradas e tipos declarados**

- `validity_data: List[Dict[str, Any]]`
- `styles: Any`

**Retornos/yields explícitos**

- `create_standard_table(table_data)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `check.get`
- `str`
- `str(check.get('status', 'INFO')).upper`
- `Paragraph`
- `_get_badge`
- `table_data.append`
- `create_standard_table`

### `build_model_input_quality_table`

[Implementação: source/antares_fd/reporting/tables.py:129](../../source/antares_fd/reporting/tables.py#L129)

```python
build_model_input_quality_table(quality_data: List[Dict[str, Any]], styles: Any) -> Table
```

Formate a rastreabilidade dos parâmetros de entrada.

Transforma quality_data em linhas de parâmetro, origem, classe e confiança.
Retorna tabela sem promover estimativas a dados medidos.

**Entradas e tipos declarados**

- `quality_data: List[Dict[str, Any]]`
- `styles: Any`

**Retornos/yields explícitos**

- `create_standard_table(table_data)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `str`
- `q.get`
- `str(q.get('confidence', '')).upper`
- `_get_badge`
- `table_data.append`
- `create_standard_table`

### `build_flight_performance_table`

[Implementação: source/antares_fd/reporting/tables.py:149](../../source/antares_fd/reporting/tables.py#L149)

```python
build_flight_performance_table(metrics: FlightMetrics) -> Table
```

Apresente as métricas escalares de desempenho com unidades.

Lê o objeto FlightMetrics e cria linhas formatadas para o relatório.
Não calcula uma nova trajetória nem altera as métricas.

**Entradas e tipos declarados**

- `metrics: FlightMetrics`

**Retornos/yields explícitos**

- `create_standard_table(data)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `data.append`
- `create_standard_table`

### `build_stability_table`

[Implementação: source/antares_fd/reporting/tables.py:166](../../source/antares_fd/reporting/tables.py#L166)

```python
build_stability_table(metrics: FlightMetrics) -> Table
```

Apresente margens de estabilidade nos instantes canônicos do voo.

Lê FlightMetrics, formata os valores e retorna uma tabela ReportLab
para comparação com os limites de engenharia.

**Entradas e tipos declarados**

- `metrics: FlightMetrics`

**Retornos/yields explícitos**

- `create_standard_table(data)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `data.append`
- `create_standard_table`

### `build_recovery_table`

[Implementação: source/antares_fd/reporting/tables.py:179](../../source/antares_fd/reporting/tables.py#L179)

```python
build_recovery_table(metrics: FlightMetrics) -> Table
```

Apresente eventos e resultados de recuperação disponíveis.

Percorre as métricas de paraquedas e impacto, preserva campos sem avaliação
e retorna uma tabela ReportLab com unidades declaradas.

**Entradas e tipos declarados**

- `metrics: FlightMetrics`

**Retornos/yields explícitos**

- `create_standard_table(data)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `data.append`
- `max`
- `create_standard_table`

### `build_completeness_table`

[Implementação: source/antares_fd/reporting/tables.py:201](../../source/antares_fd/reporting/tables.py#L201)

```python
build_completeness_table(completeness: Dict[str, str], styles: Any) -> Table
```

Formate o inventário de disponibilidade das métricas.

Converte o mapeamento completeness em linhas com indicador de status,
utilizando styles para a apresentação. Não preenche dados ausentes.

**Entradas e tipos declarados**

- `completeness: Dict[str, str]`
- `styles: Any`

**Retornos/yields explícitos**

- `create_standard_table(data)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `completeness.items`
- `data.append`
- `_get_badge`
- `create_standard_table`

### `build_mc_input_table`

[Implementação: source/antares_fd/reporting/tables.py:212](../../source/antares_fd/reporting/tables.py#L212)

```python
build_mc_input_table(project_dir: Path, styles: Any) -> Table
```

Apresente as distribuições declaradas no YAML Monte Carlo do projeto.

Lê project_dir/config/monte_carlo.yaml, percorre os grupos e formata
parâmetros e dispersões; falha de leitura produz indicação na tabela.

**Entradas e tipos declarados**

- `project_dir: Path`
- `styles: Any`

**Retornos/yields explícitos**

- `create_standard_table(data)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `unc_path.exists`
- `data.append`
- `create_standard_table`
- `open`
- `yaml.safe_load`
- `d.get`
- `uncs.items`
- `v.get`
- `prov.get('type', 'UNKNOWN').upper`
- `prov.get`
- `_get_badge`
- `str`

### `build_mc_output_table`

[Implementação: source/antares_fd/reporting/tables.py:258](../../source/antares_fd/reporting/tables.py#L258)

```python
build_mc_output_table(outputs_file: Path) -> Table
```

Apresente estatísticas finitas das saídas Monte Carlo salvas.

Lê objetos JSONL por contrato estrito, seleciona métricas numéricas
e calcula contagem, média, desvio e percentis. Não executa simulações.

**Entradas e tipos declarados**

- `outputs_file: Path`

**Retornos/yields explícitos**

- `create_standard_table(data)`

**Exceções lançadas explicitamente**

- `ValueError(f'Metric {label!r} percentile calculation overflowed finite range')`

**Colaboradores chamados diretamente**

- `outputs_file.exists`
- `data.append`
- `create_standard_table`
- `outputs_file.suffix.lower`
- `pd.read_parquet(outputs_file).to_dict`
- `pd.read_parquet`
- `read_jsonl_objects`
- `next`
- `finite_numeric_values`
- `summarize_finite_values`
- `np.percentile`
- `np.isfinite(percentiles).all`
- `np.isfinite`
- `ValueError`
- `str`

## `source/antares_fd/reporting/theme.py`

Styling, Themes, and Color Schemes for Antares Reports.

Consistent aerospace theme inspired by engineering publications:
Clean typography, high-contrast curves, muted backgrounds, clear grids.

### `save_figure`

[Implementação: source/antares_fd/reporting/theme.py:42](../../source/antares_fd/reporting/theme.py#L42)

```python
save_figure(fig, output_path: Path, preview: bool=True) -> Path
```

Write the authoritative engineering figure as vector PDF.

A PNG is emitted only when the caller requests a non-PDF path, which is
retained for legacy previews. Report generation uses the returned PDF.

**Entradas e tipos declarados**

- `fig: tipo não anotado; ver contrato acima`
- `output_path: Path`
- `preview: bool`

**Retornos/yields explícitos**

- `pdf_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `Path`
- `output_path.suffix.lower`
- `output_path.with_suffix`
- `pdf_path.parent.mkdir`
- `fig.savefig`

### `setup_report_styles`

[Implementação: source/antares_fd/reporting/theme.py:56](../../source/antares_fd/reporting/theme.py#L56)

```python
setup_report_styles()
```

Crie os estilos de texto usados nas seções ReportLab.

Instancia ParagraphStyle para títulos, corpo e células com fontes, cores
e espaçamentos consistentes. Retorna o StyleSheet1.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `styles`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `StyleSheet1`
- `styles.add`
- `ParagraphStyle`

### `BaseReportDocTemplate.handle_pageBegin`

[Implementação: source/antares_fd/reporting/theme.py:74](../../source/antares_fd/reporting/theme.py#L74)

```python
BaseReportDocTemplate.handle_pageBegin(self)
```

Inicie uma página conforme o ciclo de vida de BaseDocTemplate.

Delega ao método da classe base para manter a paginação ReportLab
e seus eventos de página.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self._handle_pageBegin`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `BaseReportDocTemplate.build`

[Implementação: source/antares_fd/reporting/theme.py:81](../../source/antares_fd/reporting/theme.py#L81)

```python
BaseReportDocTemplate.build(self, flowables, **kwargs)
```

Monte o PDF e instale o rodapé de identificação em cada página.

Define o callback footer e delega a construção da sequência flowables
a BaseDocTemplate, passando as opções recebidas.

**Entradas e tipos declarados**

- `flowables: tipo não anotado; ver contrato acima`
- `**kwargs: argumentos nomeados adicionais`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self._calc`
- `Frame`
- `self.addPageTemplates`
- `PageTemplate`
- `super().build`
- `super`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `BaseReportDocTemplate.build.footer`

[Implementação: source/antares_fd/reporting/theme.py:90](../../source/antares_fd/reporting/theme.py#L90)

```python
BaseReportDocTemplate.build.footer(canvas, doc)
```

Desenhe o rodapé da página no canvas ReportLab.

Preserva e restaura o estado gráfico, escreve identificação e número
de página usando o documento recebido; não altera os dados do relatório.

**Entradas e tipos declarados**

- `canvas: tipo não anotado; ver contrato acima`
- `doc: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `canvas.saveState`
- `canvas.setFont`
- `canvas.setFillColor`
- `canvas.drawString`
- `canvas.drawRightString`
- `canvas.restoreState`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `setup_matplotlib_theme`

[Implementação: source/antares_fd/reporting/theme.py:106](../../source/antares_fd/reporting/theme.py#L106)

```python
setup_matplotlib_theme()
```

Configures matplotlib rcParams for publication-quality figures.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `plt.rcParams.update`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

## `source/antares_fd/reporting/vector_report.py`

Vector-first engineering report renderer.

The report is made with Matplotlib's PDF backend.  This is used when a TeX
engine is unavailable, and keeps all normal engineering graphics and report
text as PDF drawing primitives.  It consumes FlightMetrics or archived
analysis tables; it never constructs RocketPy objects or reruns physics.

### `_namespace`

[Implementação: source/antares_fd/reporting/vector_report.py:37](../../source/antares_fd/reporting/vector_report.py#L37)

```python
_namespace(value: Any) -> Any
```

Converta dicionários de artefatos em namespaces de acesso por atributo.

Percorre listas e mapeamentos recursivamente; preserva escalares e ausências.
Retorna estruturas novas sem reavaliar os valores físicos.

**Entradas e tipos declarados**

- `value: Any`

**Retornos/yields explícitos**

- `SimpleNamespace(**{key: _namespace(item) for key, item in value.items()})`
- `[_namespace(item) for item in value]`
- `value`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `isinstance`
- `SimpleNamespace`
- `_namespace`
- `value.items`

### `_read_json`

[Implementação: source/antares_fd/reporting/vector_report.py:50](../../source/antares_fd/reporting/vector_report.py#L50)

```python
_read_json(path: Path, default: Any=None) -> Any
```

Leia um artefato JSON opcional para compor o relatório.

Retorna default quando o arquivo não pode ser lido ou contém JSON inválido.
Esse fallback de apresentação não deve substituir a validação de métricas
obrigatórias realizada na entrada do relatório.

**Entradas e tipos declarados**

- `path: Path`
- `default: Any`

**Retornos/yields explícitos**

- `json.loads(path.read_text(encoding='utf-8'))`
- `default`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `json.loads`
- `path.read_text`

### `_read_table`

[Implementação: source/antares_fd/reporting/vector_report.py:63](../../source/antares_fd/reporting/vector_report.py#L63)

```python
_read_table(path: Path) -> pd.DataFrame
```

Leia uma tabela Parquet opcional da campanha.

Retorna DataFrame vazio se o arquivo não existe ou se leitura, formato
ou dependência opcional impedem a carga. Não modifica os dados salvos.

**Entradas e tipos declarados**

- `path: Path`

**Retornos/yields explícitos**

- `pd.read_parquet(path) if path.exists() else pd.DataFrame()`
- `pd.DataFrame()`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `path.exists`
- `pd.read_parquet`
- `pd.DataFrame`

### `_fmt`

[Implementação: source/antares_fd/reporting/vector_report.py:75](../../source/antares_fd/reporting/vector_report.py#L75)

```python
_fmt(value: Any, digits: int=2, unit: str='') -> str
```

Formate um escalar com precisão e unidade explícitas.

Valores ausentes ou não finitos recebem indicação de indisponibilidade;
os demais usam digits casas decimais e o sufixo unit.

**Entradas e tipos declarados**

- `value: Any`
- `digits: int`
- `unit: str`

**Retornos/yields explícitos**

- `'NOT AVAILABLE'`
- `f"{float(value):.{digits}f}{(' ' + unit if unit else '')}"`
- `str(value)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `isinstance`
- `np.isfinite`
- `float`
- `str`

### `_wrap`

[Implementação: source/antares_fd/reporting/vector_report.py:88](../../source/antares_fd/reporting/vector_report.py#L88)

```python
_wrap(value: Any, width: int=28) -> str
```

Quebre texto em linhas para caber nos elementos vetoriais.

Converte value em texto e aplica textwrap com a largura width;
retorna uma string, sem alterar o conteúdo de engenharia.

**Entradas e tipos declarados**

- `value: Any`
- `width: int`

**Retornos/yields explícitos**

- `'\n'.join(textwrap.wrap(str(value), width=width, break_long_words=True, break_on_hyphens=True))`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `'\n'.join`
- `textwrap.wrap`
- `str`

### `VectorReportRenderer.__init__`

[Implementação: source/antares_fd/reporting/vector_report.py:98](../../source/antares_fd/reporting/vector_report.py#L98)

```python
VectorReportRenderer.__init__(self, metrics: Any, project_dir: Path, output_path: Path, run_id: str='nominal', campaign_dir: Path | None=None, scenarios: dict[str, Any] | None=None)
```

Configure o gerador PDF vetorial e suas fontes de evidência.

Armazena métricas, caminhos, identificação da campanha e cenários;
prepara a leitura de artefatos e o contador de páginas. Não simula voos.

**Entradas e tipos declarados**

- `metrics: Any`
- `project_dir: Path`
- `output_path: Path`
- `run_id: str`
- `campaign_dir: Path | None`
- `scenarios: dict[str, Any] | None`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `Path`
- `self.figures_dir.mkdir`
- `setup_matplotlib_theme`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `VectorReportRenderer._branding_asset`

[Implementação: source/antares_fd/reporting/vector_report.py:115](../../source/antares_fd/reporting/vector_report.py#L115)

```python
VectorReportRenderer._branding_asset(self) -> Path | None
```

Localize a marca visual disponível para a capa.

Procura os caminhos conhecidos do projeto e do pacote, retornando
o arquivo existente ou ausência explícita; não baixa imagens.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `candidate`
- `None`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `candidate.exists`

### `VectorReportRenderer._page`

[Implementação: source/antares_fd/reporting/vector_report.py:128](../../source/antares_fd/reporting/vector_report.py#L128)

```python
VectorReportRenderer._page(self, title: str, section: str='')
```

Crie uma página vetorial com título, seção e identificação.

Instancia a figura Matplotlib e desenha os elementos fixos. Retorna fig
para receber conteúdo antes de ser salva por _finish.

**Entradas e tipos declarados**

- `title: str`
- `section: str`

**Retornos/yields explícitos**

- `fig`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `plt.figure`
- `fig.text`
- `fig.add_artist`
- `plt.Line2D`
- `getattr`

### `VectorReportRenderer._finish`

[Implementação: source/antares_fd/reporting/vector_report.py:145](../../source/antares_fd/reporting/vector_report.py#L145)

```python
VectorReportRenderer._finish(self, pdf: PdfPages, fig)
```

Grave e encerre uma página do PDF.

Envia fig a PdfPages, fecha a figura para liberar recursos
e atualiza o contador de páginas do renderizador.

**Entradas e tipos declarados**

- `pdf: PdfPages`
- `fig: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `pdf.savefig`
- `plt.close`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `VectorReportRenderer._text`

[Implementação: source/antares_fd/reporting/vector_report.py:155](../../source/antares_fd/reporting/vector_report.py#L155)

```python
VectorReportRenderer._text(self, fig, x: float, y: float, text: str, size: float=10, color: str=INK, weight: str='normal', width: int=100)
```

Adicione texto posicionado em coordenadas normalizadas da página.

Aplica tamanho, cor, peso e quebra por width antes de desenhar em fig.
O método modifica somente os elementos gráficos da figura.

**Entradas e tipos declarados**

- `fig: tipo não anotado; ver contrato acima`
- `x: float`
- `y: float`
- `text: str`
- `size: float`
- `color: str`
- `weight: str`
- `width: int`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `fig.text`
- `_wrap`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `VectorReportRenderer._table`

[Implementação: source/antares_fd/reporting/vector_report.py:163](../../source/antares_fd/reporting/vector_report.py#L163)

```python
VectorReportRenderer._table(self, fig, rows: list[list[Any]], rect=(0.07, 0.12, 0.86, 0.7), fontsize=7.4, widths=None)
```

Desenhe uma tabela vetorial dentro do retângulo solicitado.

Formata rows, larguras e tipografia sobre eixos ocultos da figura;
permite ajustar fonte e proporção sem rasterizar células.

**Entradas e tipos declarados**

- `fig: tipo não anotado; ver contrato acima`
- `rows: list[list[Any]]`
- `rect: tipo não anotado; ver contrato acima`
- `fontsize: tipo não anotado; ver contrato acima`
- `widths: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `table`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `fig.add_axes`
- `ax.axis`
- `_wrap`
- `max`
- `int`
- `enumerate`
- `ax.table`
- `table.auto_set_font_size`
- `table.set_fontsize`
- `table.scale`
- `table.get_celld().items`
- `table.get_celld`
- `cell.set_edgecolor`
- `cell.set_linewidth`
- `cell.set_text_props`
- `cell.set_facecolor`

### `VectorReportRenderer._cover`

[Implementação: source/antares_fd/reporting/vector_report.py:184](../../source/antares_fd/reporting/vector_report.py#L184)

```python
VectorReportRenderer._cover(self, pdf)
```

Produza a capa com identificação do voo e da campanha.

Cria página, inclui marca disponível e textos de controle e chama _finish
para gravá-la em pdf.

**Entradas e tipos declarados**

- `pdf: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `plt.figure`
- `self._branding_asset`
- `logo.suffix.lower`
- `fig.add_axes`
- `ax.imshow`
- `mpimg.imread`
- `ax.axis`
- `fig.text`
- `getattr`
- `self._table`
- `self._finish`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `VectorReportRenderer._document_control`

[Implementação: source/antares_fd/reporting/vector_report.py:210](../../source/antares_fd/reporting/vector_report.py#L210)

```python
VectorReportRenderer._document_control(self, pdf)
```

Produza a página de controle e proveniência documental.

Lê identificadores, revisão e metadados já disponíveis e os organiza
em tabelas; não gera evidência física nova.

**Entradas e tipos declarados**

- `pdf: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `collect_reproducibility_data`
- `repro.get`
- `getattr`
- `git.get`
- `env.get`
- `'; '.join`
- `repro.get('config_hashes', {}).items`
- `repro.get('data_hashes', {}).items`
- `self._page`
- `self._table`
- `self._text`
- `self._finish`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `VectorReportRenderer._toc`

[Implementação: source/antares_fd/reporting/vector_report.py:237](../../source/antares_fd/reporting/vector_report.py#L237)

```python
VectorReportRenderer._toc(self, pdf)
```

Produza o índice das seções do relatório.

Lista os blocos previstos para a modalidade de relatório e grava
uma página vetorial com a navegação textual.

**Entradas e tipos declarados**

- `pdf: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self._page`
- `self._text`
- `fig.text`
- `self._finish`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `VectorReportRenderer._executive`

[Implementação: source/antares_fd/reporting/vector_report.py:253](../../source/antares_fd/reporting/vector_report.py#L253)

```python
VectorReportRenderer._executive(self, pdf)
```

Produza o resumo executivo das métricas e da campanha.

Reúne indicadores escalares e disponibilidade das evidências, formata
tabelas de leitura rápida e grava a página em pdf.

**Entradas e tipos declarados**

- `pdf: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `_fmt`
- `getattr`
- `self._mc_value`
- `self._mc_ellipse`
- `self._page`
- `self._table`
- `self._text`
- `self._interpretation`
- `self._finish`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `VectorReportRenderer._mc_summary`

[Implementação: source/antares_fd/reporting/vector_report.py:277](../../source/antares_fd/reporting/vector_report.py#L277)

```python
VectorReportRenderer._mc_summary(self)
```

Obtenha o resumo canônico salvo da campanha Monte Carlo.

Lê os caminhos suportados de summary.json e retorna o documento
ou estrutura vazia quando não houver campanha disponível.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `{}`
- `summary`
- `_read_json(primary / 'summary.json', _read_json(primary / 'monte_carlo_summary.json', {})) or {}`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `_read_json`
- `self._scenario_dir`

### `VectorReportRenderer._scenario_dir`

[Implementação: source/antares_fd/reporting/vector_report.py:291](../../source/antares_fd/reporting/vector_report.py#L291)

```python
VectorReportRenderer._scenario_dir(self, scenario_id: str) -> Path
```

Resolva o diretório de artefatos de um cenário estocástico.

Considera os layouts de campanha aceitos e retorna Path ou None
quando o cenário solicitado não tiver resultados salvos.

**Entradas e tipos declarados**

- `scenario_id: str`

**Retornos/yields explícitos**

- `Path()`
- `candidate if candidate.exists() else self.campaign_dir`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `Path`
- `candidate.exists`

### `VectorReportRenderer._scenario_dirs`

[Implementação: source/antares_fd/reporting/vector_report.py:302](../../source/antares_fd/reporting/vector_report.py#L302)

```python
VectorReportRenderer._scenario_dirs(self) -> dict[str, Path]
```

Liste os cenários estocásticos com artefatos disponíveis.

Percorre o layout de campaign_dir e retorna um mapeamento entre
identificador de cenário e diretório, sem executar novos casos.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `{}`
- `{path.name: path for path in sorted(root.iterdir()) if path.is_dir()} if root.exists() else {}`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `root.exists`
- `sorted`
- `root.iterdir`
- `path.is_dir`

### `VectorReportRenderer._mc_value`

[Implementação: source/antares_fd/reporting/vector_report.py:313](../../source/antares_fd/reporting/vector_report.py#L313)

```python
VectorReportRenderer._mc_value(self, metric: str, stat: str) -> str
```

Consulte uma estatística escalar de uma métrica Monte Carlo.

Seleciona metric e stat na tabela de estatísticas armazenada;
retorna ausência quando não há linha ou coluna correspondente.

**Entradas e tipos declarados**

- `metric: str`
- `stat: str`

**Retornos/yields explícitos**

- `str(s.get('successful', s.get('completed', 'NOT AVAILABLE')))`
- `'NOT AVAILABLE'`
- `_fmt(row.iloc[0].get(stat), 1, 'm') if not row.empty else 'NOT AVAILABLE'`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self._mc_summary`
- `str`
- `s.get`
- `_read_table`
- `self._scenario_dir`
- `pd.DataFrame`
- `_fmt`
- `row.iloc[0].get`

### `VectorReportRenderer._mc_ellipse`

[Implementação: source/antares_fd/reporting/vector_report.py:328](../../source/antares_fd/reporting/vector_report.py#L328)

```python
VectorReportRenderer._mc_ellipse(self, key: str) -> str
```

Consulte um parâmetro da dispersão de pouso salva.

Lê key na estrutura de elipses da campanha. O retorno conserva
a indisponibilidade quando não há amostras suficientes.

**Entradas e tipos declarados**

- `key: str`

**Retornos/yields explícitos**

- `_fmt(ellipse.get('major_axis'), 0, 'm') if ellipse else 'NOT AVAILABLE'`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self._mc_summary().get`
- `self._mc_summary`
- `_read_json(self._scenario_dir('nominal') / 'summary.json', {}).get`
- `_read_json`
- `self._scenario_dir`
- `landing.get('ellipses', {}).get`
- `landing.get`
- `_fmt`
- `ellipse.get`

### `VectorReportRenderer._interpretation`

[Implementação: source/antares_fd/reporting/vector_report.py:340](../../source/antares_fd/reporting/vector_report.py#L340)

```python
VectorReportRenderer._interpretation(self) -> str
```

Construa a interpretação textual a partir das evidências disponíveis.

Relaciona métricas, limites e incertezas registrados, distinguindo
resultados simulados de validação experimental.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `f"Engineering Interpretation: maximum dynamic pressure is {_fmt(getattr(m, 'max_dynamic_pressure', 0) / 1000.0, 1, 'kPa')} at t = {_fmt(getattr(m, 'max_q_time', 0), 2, 's')} and {_fmt(getattr(m, 'max_q_altitude', 0), 1, 'm')} AGL. The reported AoA at Max-Q is {_fmt(getattr(m, 'angle_of_attack_at_max_q', 0), 2, 'deg')}; the valid-window maximum is {_fmt(getattr(m, 'max_angle_of_attack', 0), 1, 'deg')}. Q-alpha is a load indicator and is not a structural bending moment."`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `_fmt`
- `getattr`

### `VectorReportRenderer._warnings`

[Implementação: source/antares_fd/reporting/vector_report.py:350](../../source/antares_fd/reporting/vector_report.py#L350)

```python
VectorReportRenderer._warnings(self, pdf)
```

Produza a página de limitações e condições de interpretação.

Reúne avisos de modelo, dados ausentes e semântica das análises
e grava os textos em pdf.

**Entradas e tipos declarados**

- `pdf: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `list`
- `self._mc_summary().get`
- `self._mc_summary`
- `getattr`
- `warnings.append`
- `self._page`
- `self._table`
- `self._finish`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `VectorReportRenderer._requirements`

[Implementação: source/antares_fd/reporting/vector_report.py:371](../../source/antares_fd/reporting/vector_report.py#L371)

```python
VectorReportRenderer._requirements(self, pdf)
```

Produza a página de conformidade com os requisitos declarados.

Converte _compliance_rows em tabela vetorial e inclui o contexto
dos critérios usados, sem alterar limites para aprovar resultados.

**Entradas e tipos declarados**

- `pdf: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self._compliance_rows`
- `rows.append`
- `row.get`
- `len`
- `self._page`
- `self._table`
- `self._finish`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `VectorReportRenderer._compliance_rows`

[Implementação: source/antares_fd/reporting/vector_report.py:388](../../source/antares_fd/reporting/vector_report.py#L388)

```python
VectorReportRenderer._compliance_rows(self)
```

Monte linhas de conformidade a partir das avaliações disponíveis.

Seleciona requisito, valor, limite e status preservando desconhecidos.
Retorna linhas para apresentação, sem nova integração física.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `[]`
- `frame.to_dict('records') if not frame.empty else []`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `_read_table`
- `self._scenario_dir`
- `frame.to_dict`

### `VectorReportRenderer._provenance`

[Implementação: source/antares_fd/reporting/vector_report.py:399](../../source/antares_fd/reporting/vector_report.py#L399)

```python
VectorReportRenderer._provenance(self, pdf)
```

Produza a página de proveniência dos parâmetros de entrada.

Apresenta fonte, classificação, confiança e semântica disponíveis
no inventário canônico; grava a página em pdf.

**Entradas e tipos declarados**

- `pdf: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `collect_reproducibility_data`
- `repro.get`
- `item.get`
- `rows.append`
- `len`
- `self._page`
- `self._table`
- `self._finish`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `VectorReportRenderer._validity`

[Implementação: source/antares_fd/reporting/vector_report.py:417](../../source/antares_fd/reporting/vector_report.py#L417)

```python
VectorReportRenderer._validity(self, pdf)
```

Produza a página de domínio de validade do modelo.

Relaciona métricas simuladas aos envelopes declarados e mantém
visíveis os limites ausentes ou ultrapassados.

**Entradas e tipos declarados**

- `pdf: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `getattr`
- `window.get`
- `_fmt`
- `self._page`
- `self._table`
- `self._text`
- `self._finish`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `VectorReportRenderer._flight_pages`

[Implementação: source/antares_fd/reporting/vector_report.py:437](../../source/antares_fd/reporting/vector_report.py#L437)

```python
VectorReportRenderer._flight_pages(self, pdf)
```

Produza páginas de cinemática, propulsão, estabilidade e recuperação.

Usa séries temporais e eventos já extraídos para desenhar os gráficos
vetoriais. Não acessa um integrador nem reconstitui parâmetros ausentes.

**Entradas e tipos declarados**

- `pdf: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `None`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `getattr`
- `self._page`
- `fig.add_axes`
- `zip`
- `axis.plot`
- `axis.set`
- `axis.grid`
- `axis.axvline`
- `self._finish`
- `axes[0].plot`
- `axes[0].set`
- `axes[1].plot`
- `axes[1].set`
- `axes[2].plot`
- `axes[2].scatter`
- `axes[2].set`
- `axes[2].axis`
- `axes[3].plot`
- `np.hypot`
- `axes[3].set`
- `float`
- `ax.plot`
- `ax.twinx`
- `ax2.plot`
- `np.maximum`
- `ax.set`
- `ax2.set_ylabel`
- `ax.grid`
- `_fmt`
- `self._table`
- `ax.axvline`
- `ax.legend`
- `ax2.axhline`
- `ax2.set`
- `ax2.legend`
- `ax2.grid`
- `ax3.plot`
- `ax3.set`
- `ax3.grid`

### `VectorReportRenderer._scenarios`

[Implementação: source/antares_fd/reporting/vector_report.py:490](../../source/antares_fd/reporting/vector_report.py#L490)

```python
VectorReportRenderer._scenarios(self, pdf)
```

Produza a comparação dos cenários determinísticos disponíveis.

Percorre as métricas por cenário, apresenta diferenças de desempenho
e grava os gráficos e tabelas no PDF.

**Entradas e tipos declarados**

- `pdf: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `None`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.scenarios.items`
- `rows.append`
- `_fmt`
- `getattr`
- `self._page`
- `self._table`
- `self._text`
- `self._finish`

### `VectorReportRenderer._mc_pages`

[Implementação: source/antares_fd/reporting/vector_report.py:504](../../source/antares_fd/reporting/vector_report.py#L504)

```python
VectorReportRenderer._mc_pages(self, pdf)
```

Produza as páginas de incerteza da campanha Monte Carlo salva.

Lê estatísticas, amostras e saídas para apresentar distribuições,
dispersão, convergência e sensibilidade. Não cria novos casos.

**Entradas e tipos declarados**

- `pdf: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `None`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self._scenario_dirs`
- `self._scenario_stochastic_pages`
- `self._mc_summary`
- `_read_json`
- `summary.get`
- `performance.get`
- `self._page`
- `self._table`
- `self._text`
- `self._finish`
- `_read_table`
- `stats.iterrows`
- `rows.append`
- `row.get`
- `len`
- `conv.tail(18).iterrows`
- `conv.tail`
- `{'input', 'output', 'coefficient'}.issubset`
- `sens.assign(abs_coeff=sens.coefficient.abs()).sort_values('abs_coeff').tail`
- `sens.assign(abs_coeff=sens.coefficient.abs()).sort_values`
- `sens.assign`
- `sens.coefficient.abs`
- `fig.add_axes`
- `ax.barh`
- `top.input.astype`
- `ax.set_xlabel`
- `ax.grid`

### `VectorReportRenderer._scenario_stochastic_pages`

[Implementação: source/antares_fd/reporting/vector_report.py:539](../../source/antares_fd/reporting/vector_report.py#L539)

```python
VectorReportRenderer._scenario_stochastic_pages(self, pdf, scenario_dirs: dict[str, Path])
```

Render multi-scenario stochastic evidence from saved tables only.

**Entradas e tipos declarados**

- `pdf: tipo não anotado; ver contrato acima`
- `scenario_dirs: dict[str, Path]`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `_read_json`
- `scenario_dirs.items`
- `pairing.get`
- `max`
- `int`
- `item.get`
- `rows.append`
- `self._page`
- `self._table`
- `self._text`
- `self._finish`
- `_read_table`
- `uncertainty.iterrows`
- `str(item.get('source_type', 'UNKNOWN')).upper`
- `str`
- `fig.add_axes`
- `zip`
- `pd.to_numeric(output[metric], errors='coerce').dropna`
- `pd.to_numeric`
- `len`
- `axis.hist`
- `axis.set_xlabel`
- `axis.set_ylabel`
- `axis.grid`
- `axis.legend`
- `{'landing_east', 'landing_north'}.issubset`
- `x.notna`
- `y.notna`
- `axis.scatter`
- `valid.any`
- `x[valid].mean`
- `y[valid].mean`
- `axis.axis`
- `scenario_dirs.keys`
- `convergence.get`
- `pd.Series`
- `pd.DataFrame`
- `row.append`
- `selected.iloc[-1].get`
- `sorted`
- `scenario_dirs.values`
- `_read_table(path / 'compliance.parquet').get('requirement', pd.Series(dtype=str)).dropna().astype`
- `_read_table(path / 'compliance.parquet').get('requirement', pd.Series(dtype=str)).dropna`
- `_read_table(path / 'compliance.parquet').get`
- `compliance['requirement'].astype`
- `_fmt`
- `paired_stats.iterrows`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `VectorReportRenderer._validation`

[Implementação: source/antares_fd/reporting/vector_report.py:638](../../source/antares_fd/reporting/vector_report.py#L638)

```python
VectorReportRenderer._validation(self, pdf)
```

Produza a seção de evidência de validação experimental.

Apresenta os dados e limitações declarados; quando não há medição
rastreável, registra indisponibilidade em vez de afirmar validação.

**Entradas e tipos declarados**

- `pdf: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self._page`
- `getattr`
- `validation.get`
- `validation.get('predicted', {}).get`
- `validation.get('fuselage', {}).get`
- `validation.get('nose_cone', {}).get`
- `self._table`
- `self._text`
- `self._finish`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `VectorReportRenderer._appendices`

[Implementação: source/antares_fd/reporting/vector_report.py:653](../../source/antares_fd/reporting/vector_report.py#L653)

```python
VectorReportRenderer._appendices(self, pdf)
```

Produza os apêndices com metadados e referências dos artefatos.

Organiza as informações de reprodução disponíveis na campanha
e grava as páginas finais em pdf.

**Entradas e tipos declarados**

- `pdf: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `getattr`
- `rows.append`
- `_fmt`
- `self._page`
- `self._table`
- `self._finish`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `VectorReportRenderer.render`

[Implementação: source/antares_fd/reporting/vector_report.py:669](../../source/antares_fd/reporting/vector_report.py#L669)

```python
VectorReportRenderer.render(self) -> Path
```

Grave o relatório completo no caminho configurado.

Abre PdfPages em contexto de fechamento garantido, executa as seções
na ordem documental e fecha cada figura após a gravação.
O efeito externo é o PDF em output_path; falhas de escrita são propagadas.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `self.output_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.output_path.parent.mkdir`
- `PdfPages`
- `self._cover`
- `self._document_control`
- `self._toc`
- `self._executive`
- `self._warnings`
- `self._requirements`
- `self._provenance`
- `self._validity`
- `self._flight_pages`
- `self._scenarios`
- `self._mc_pages`
- `self._validation`
- `self._appendices`
- `self._branding_asset`
- `branding.resolve().relative_to(self.project_dir.parents[1].resolve()).as_posix`
- `branding.resolve().relative_to`
- `branding.resolve`
- `self.project_dir.parents[1].resolve`
- `manifest_path.write_text`
- `json.dumps`
- `list`
- `inspect_report`
- `_read_json`
- `qa.get`
- `print`

## `source/antares_fd/simulation/__init__.py`

Public flight and campaign entry points.

Project scripts use this package surface; implementation details stay in
their own modules, and the campaign runner is imported lazily.

### `run_project_campaign`

[Implementação: source/antares_fd/simulation/__init__.py:20](../../source/antares_fd/simulation/__init__.py#L20)

```python
run_project_campaign(*args, **kwargs)
```

Lazy wrapper that avoids importing reporting during package startup.

**Entradas e tipos declarados**

- `*args: argumentos posicionais adicionais`
- `**kwargs: argumentos nomeados adicionais`

**Retornos/yields explícitos**

- `_run_project_campaign(*args, **kwargs)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `_run_project_campaign`

## `source/antares_fd/simulation/campaign.py`

ANTARES FLIGHT DYNAMICS
Unified Campaign Orchestrator.

Executes declared simulation scenarios (deterministic + Monte Carlo)
in a project's simulations directory within a SINGLE execution lifecycle.
Guarantees that:
1. ONLY ONE campaign folder is created in results/<project_name>/<run_id>.
2. ALL intermediate data (trajectories, KMLs, Monte Carlo outputs) are centralized.
3. ONLY ONE comprehensive, master engineering PDF report is compiled.

### `select_campaign_scripts`

[Implementação: source/antares_fd/simulation/campaign.py:56](../../source/antares_fd/simulation/campaign.py#L56)

```python
select_campaign_scripts(simulations_dir: Path) -> tuple[list[Path], list[Path]]
```

Select only declared flight entry points; unrelated helpers never run.

**Entradas e tipos declarados**

- `simulations_dir: Path`

**Retornos/yields explícitos**

- `(deterministic, stochastic[:1])`

**Exceções lançadas explicitamente**

- `FileNotFoundError(f'Campaign requires a nominal.py flight entry point: {nominal}')`

**Colaboradores chamados diretamente**

- `Path`
- `nominal.is_file`
- `FileNotFoundError`
- `(path := (simulations_dir / f'{stem}.py')).is_file`
- `ballistic.is_file`
- `selected_ballistic.is_file`
- `next`
- `enumerate`
- `len`
- `deterministic.insert`

### `run_project_campaign`

[Implementação: source/antares_fd/simulation/campaign.py:83](../../source/antares_fd/simulation/campaign.py#L83)

```python
run_project_campaign(simulations_dir: Path) -> Path
```

Run a campaign and restore every campaign control variable on all exits.

**Entradas e tipos declarados**

- `simulations_dir: Path`

**Retornos/yields explícitos**

- `_run_project_campaign_impl(simulations_dir)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `os.environ.get`
- `_run_project_campaign_impl`
- `previous.items`
- `os.environ.pop`

### `_run_project_campaign_impl`

[Implementação: source/antares_fd/simulation/campaign.py:96](../../source/antares_fd/simulation/campaign.py#L96)

```python
_run_project_campaign_impl(simulations_dir: Path) -> Path
```

Executes declared simulation files in `simulations_dir`, aggregates results,
and produces a single master engineering PDF report in a single output directory.

**Entradas e tipos declarados**

- `simulations_dir: Path`

**Retornos/yields explícitos**

- `generated_pdf`

**Exceções lançadas explicitamente**

- `RuntimeError(f'Could not load deterministic entry point: {script_path}')`
- `RuntimeError(f'Deterministic entry point has no main(): {script_path}')`
- `RuntimeError(f'Deterministic entry point returned no flight: {script_path}')`
- `RuntimeError('Nominal flight failed; campaign report cannot use another scenario as nominal')`
- `RuntimeError(f'Could not load Monte Carlo entry point: {primary_mc}')`
- `RuntimeError(f'Monte Carlo entry point has no main(): {primary_mc}')`
- `RuntimeError(f'Monte Carlo campaign failed; report was written to {generated_pdf}')`

**Colaboradores chamados diretamente**

- `Path(simulations_dir).resolve`
- `Path`
- `select_campaign_scripts`
- `str`
- `sys.path.insert`
- `datetime.datetime.now(datetime.UTC).strftime`
- `datetime.datetime.now`
- `campaign_dir.mkdir`
- `trajectories_dir.mkdir`
- `os.environ.get`
- `print`
- `len`
- `enumerate`
- `SCENARIO_NAME_MAP.get`
- `scenario_id.replace('_', ' ').title`
- `scenario_id.replace`
- `importlib.util.spec_from_file_location`
- `RuntimeError`
- `importlib.util.module_from_spec`
- `spec.loader.exec_module`
- `hasattr`
- `mod.main`
- `deterministic_failures.append`
- `type`
- `os.environ.pop`
- `datetime.datetime.now(datetime.UTC).isoformat`
- `list`
- `scenario_flights.keys`
- `(campaign_dir / 'manifest.yaml').open`
- `yaml.safe_dump`
- `load_project_config`
- `mc_cfg.get`
- `int`
- `StochasticScenarioCampaign`
- `PROFILES[profile].get`
- `tuple`
- `configured_scenario_ids`
- `scenario_campaign.ensure_samples`
- `registry.exists`
- `scenario_campaign.write_manifest`
- `scenario_campaign.finalize_paired_comparison`
- `SCENARIO_NAME_MAP.items`
- `scenario_flights.items`
- `reverse_names.get`
- `label.lower().replace`
- `label.lower`
- `apply_scenario`
- `extract_flight_metrics`
- `(campaign_dir / 'deterministic_scenario_consistency.json').write_text`
- `json.dumps`
- `deterministic_scenario_consistency`
- `FlightDynamicsReport`
- `report.generate`
- `campaign_dir.glob`
- `redundant.unlink`
- `(campaign_dir / 'scenarios.csv').unlink`
- `open`
- `yaml.dump`

## `source/antares_fd/simulation/case_ids.py`

Canonical Monte Carlo case-ID contract.

Antares campaign case IDs are non-negative, zero-based integers. RocketPy's
parallel producer already exports zero-based ``index`` values; the serial
producer exports its incremented monitor count, so the campaign adapter must
normalize that producer at the boundary. Consumers never guess an index base.

### `normalize_case_id`

[Implementação: source/antares_fd/simulation/case_ids.py:19](../../source/antares_fd/simulation/case_ids.py#L19)

```python
normalize_case_id(value: Any, *, context: str='case ID') -> int
```

Validate and return a canonical zero-based case ID.

**Entradas e tipos declarados**

- `value: Any`
- `context: str`

**Retornos/yields explícitos**

- `case_id`
- `int(number)`

**Exceções lançadas explicitamente**

- `ValueError(f'{context} must be a zero-based integer')`
- `ValueError(f'{context} must be a non-negative zero-based integer')`
- `ValueError(f'{context} is outside the finite integer range')`

**Colaboradores chamados diretamente**

- `isinstance`
- `ValueError`
- `int`
- `float`
- `math.isfinite`
- `number.is_integer`

### `canonicalize_case_records`

[Implementação: source/antares_fd/simulation/case_ids.py:37](../../source/antares_fd/simulation/case_ids.py#L37)

```python
canonicalize_case_records(records: Iterable[Mapping[str, Any]], *, allowed_case_ids: set[int] | None=None, context: str='Monte Carlo records') -> list[dict[str, Any]]
```

Copy records with explicit canonical IDs; reject ambiguity and duplicates.

**Entradas e tipos declarados**

- `records: Iterable[Mapping[str, Any]]`
- `allowed_case_ids: set[int] | None`
- `context: str`

**Retornos/yields explícitos**

- `normalized`

**Exceções lançadas explicitamente**

- `ValueError(f'{context} row {row_number} must be an object')`
- `ValueError(f'{context} row {row_number} has no case_id or index')`
- `ValueError(f'{context} row {row_number} has conflicting case_id and index')`
- `ValueError(f'{context} contains duplicate case ID {case_id}')`
- `ValueError(f'{context} contains case ID {case_id} outside the sample table')`

**Colaboradores chamados diretamente**

- `set`
- `enumerate`
- `isinstance`
- `ValueError`
- `record.get`
- `normalize_case_id`
- `seen.add`
- `dict`
- `normalized.append`

### `completed_prefix_length`

[Implementação: source/antares_fd/simulation/case_ids.py:77](../../source/antares_fd/simulation/case_ids.py#L77)

```python
completed_prefix_length(case_ids: Iterable[int], requested: int) -> int
```

Return a safely resumable completed prefix or fail closed on sparse IDs.

**Entradas e tipos declarados**

- `case_ids: Iterable[int]`
- `requested: int`

**Retornos/yields explícitos**

- `len(ids)`

**Exceções lançadas explicitamente**

- `ValueError('requested case count must be non-negative')`
- `ValueError(f'completed case IDs exceed requested range [0, {requested}): {outside[:5]}')`
- `ValueError(f'cannot safely resume Monte Carlo records with non-prefix case IDs; present={present[:10]}, missing within prefix={missing[:10]}')`

**Colaboradores chamados diretamente**

- `int`
- `ValueError`
- `normalize_case_id`
- `sorted`
- `set`
- `range`
- `len`

## `source/antares_fd/simulation/monte_carlo.py`

Motor legado mantido para consumidores e testes de compatibilidade.

Entradas CLI/GUI e scripts de projeto usam monte_carlo_failure, que registra
falhas e estatísticas pelo mesmo contrato. Não adicione regras físicas aqui;
migrações de consumidores externos exigem comparar formatos de artefatos.

### `execute_monte_carlo`

[Implementação: source/antares_fd/simulation/monte_carlo.py:28](../../source/antares_fd/simulation/monte_carlo.py#L28)

```python
execute_monte_carlo(config, project_dir)
```

Build stochastic RocketPy inputs, restore case logs, then run remaining cases.

``ANTARES_MC_SCENARIO`` selects the scenario. Campaign environment
variables route artifacts into a parent campaign; standalone runs create
their own results directory. Case logs are restored before worker startup,
so a complete resume does not launch the process manager.

**Entradas e tipos declarados**

- `config: tipo não anotado; ver contrato acima`
- `project_dir: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `mc`

**Exceções lançadas explicitamente**

- `ConfigurationError('Monte Carlo configuration (monte_carlo.yaml) is missing or empty.')`
- `RuntimeError(f'Monte Carlo campaign incomplete: {len(mc.outputs_log)}/{num_sims} simulations exported. Check worker errors and results in {results_dir}.')`

**Colaboradores chamados diretamente**

- `ConfigurationError`
- `int`
- `mc_cfg.get`
- `os.environ.get`
- `apply_scenario`
- `np.random.seed`
- `random.seed`
- `print`
- `build_environment`
- `build_environment_ensemble`
- `(env_cfg.get('wind_velocity_x') or {}).get`
- `env_cfg.get`
- `(env_cfg.get('wind_velocity_y') or {}).get`
- `ProfileStochasticEnvironment`
- `(env_cfg.get('elevation') or {}).get`
- `build_motor`
- `(mot_cfg.get('total_impulse_scale') or {}).get`
- `mot_cfg.get`
- `StochasticSolidMotor`
- `build_vehicle`
- `add_recovery_system`
- `(veh_cfg.get('mass') or {}).get`
- `veh_cfg.get`
- `(veh_cfg.get('power_off_drag_factor') or {}).get`
- `(veh_cfg.get('power_on_drag_factor') or {}).get`
- `StochasticRocket`
- `stoch_rocket.add_motor`
- `_transfer_rocket_components`
- `(config.launch.get('rail') or {}).get`
- `config.launch.get`
- `run_flight`
- `StochasticFlight`
- `launch_angle_distribution`
- `flt_cfg.get`
- `Path`
- `results_dir.mkdir`
- `datetime.datetime.now(datetime.UTC).strftime`
- `datetime.datetime.now`
- `str`
- `ConfiguredMonteCarlo`
- `restore_jsonl_case_logs`
- `set`
- `range`
- `CampaignManager`
- `manager.start`
- `manager.TrajectoryStore`
- `mc.simulate`
- `all_flights.snapshot`
- `manager.shutdown`
- `subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=str(project_dir)).decode().strip`
- `subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=str(project_dir)).decode`
- `subprocess.check_output`
- `bool`
- `subprocess.check_output(['git', 'status', '--porcelain'], cwd=str(project_dir)).decode().strip`
- `subprocess.check_output(['git', 'status', '--porcelain'], cwd=str(project_dir)).decode`
- `datetime.datetime.now(datetime.UTC).isoformat`
- `len`
- `hasattr`
- `open`
- `yaml.dump`
- `RuntimeError`
- `outputs_file.exists`
- `plot_monte_carlo_dispersion`
- `plot_monte_carlo_distributions`
- `plot_monte_carlo_convergence`
- `FlightDynamicsReport`
- `report.generate`

### `execute_monte_carlo._patched_run_single`

[Implementação: source/antares_fd/simulation/monte_carlo.py:140](../../source/antares_fd/simulation/monte_carlo.py#L140)

```python
execute_monte_carlo._patched_run_single(*args, **kwargs)
```

Capture a trajetória compacta após cada caso RocketPy executado.

Delega ao executor original e armazena os vetores necessários aos gráficos.
Retorna o mesmo Flight ao consumidor; a captura é um efeito auxiliar.

**Entradas e tipos declarados**

- `*args: argumentos posicionais adicionais`
- `**kwargs: argumentos nomeados adicionais`

**Retornos/yields explícitos**

- `flt`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `_orig_run_single`
- `all_flights.append`

## `source/antares_fd/simulation/monte_carlo_failure.py`

Run failure-aware campaigns from a frozen population of stochastic cases.

Samples receive stable case IDs before RocketPy runs. Successful outputs,
failed cases, and scenario metadata remain separate campaign records.

### `_deterministic_sim_producer`

[Implementação: source/antares_fd/simulation/monte_carlo_failure.py:44](../../source/antares_fd/simulation/monte_carlo_failure.py#L44)

```python
_deterministic_sim_producer(self, _worker_seed, sim_monitor, mutex, error_event)
```

RocketPy producer variant that assigns the frozen seed by case ID.

RocketPy's stock producer seeds once per worker. That makes a case's
random stream depend on scheduling. This drop-in producer keeps RocketPy's
simulation and serialization code, while reseeding all stochastic models
immediately after the monitor assigns a deterministic case index.

**Entradas e tipos declarados**

- `_worker_seed: tipo não anotado; ver contrato acima`
- `sim_monitor: tipo não anotado; ver contrato acima`
- `mutex: tipo não anotado; ver contrato acima`
- `error_event: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `sim_monitor.keep_simulating`
- `sim_monitor.increment`
- `int`
- `getattr`
- `self.environment.set_profile`
- `len`
- `self.environment._set_stochastic`
- `self.rocket._set_stochastic`
- `self.flight._set_stochastic`
- `self._MonteCarlo__run_single_simulation`
- `_explicit_case_id_json`
- `self._MonteCarlo__evaluate_flight_inputs`
- `self._MonteCarlo__evaluate_flight_outputs`
- `mutex.acquire`
- `error_event.is_set`
- `open`
- `stream.write`
- `sim_monitor.print_update_status`
- `mutex.release`
- `print`
- `traceback.format_exc`
- `error_event.set`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `_explicit_case_id_json`

[Implementação: source/antares_fd/simulation/monte_carlo_failure.py:95](../../source/antares_fd/simulation/monte_carlo_failure.py#L95)

```python
_explicit_case_id_json(serialized: str, case_id: int) -> str
```

Add the canonical ID to RocketPy's scalar JSON record.

**Entradas e tipos declarados**

- `serialized: str`
- `case_id: int`

**Retornos/yields explícitos**

- `json.dumps(record, ensure_ascii=False, separators=(',', ':')) + '\n'`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `json.loads`
- `int`
- `json.dumps`

### `_failure_records`

[Implementação: source/antares_fd/simulation/monte_carlo_failure.py:103](../../source/antares_fd/simulation/monte_carlo_failure.py#L103)

```python
_failure_records(mc, samples, requested)
```

Represent every missing case explicitly in the canonical failure table.

**Entradas e tipos declarados**

- `mc: tipo não anotado; ver contrato acima`
- `samples: tipo não anotado; ver contrato acima`
- `requested: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `[{'case_id': case_id, 'seed': seed_by_case.get(case_id), 'exception_class': 'RocketPySimulationError', 'short_error': 'no scalar output was exported for this case', 'stage': 'trajectory', 'worker': None, 'status': 'FAILED'} for case_id in range(int(requested)) if case_id not in successful_ids]`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `canonicalize_case_records`
- `getattr`
- `set`
- `range`
- `int`
- `{'case_id', 'seed'}.issubset`
- `samples.set_index('case_id')['seed'].to_dict`
- `samples.set_index`
- `seed_by_case.get`

### `execute_monte_carlo`

[Implementação: source/antares_fd/simulation/monte_carlo_failure.py:128](../../source/antares_fd/simulation/monte_carlo_failure.py#L128)

```python
execute_monte_carlo(config, project_dir, *, workspace_root=None, archive_atmospheres=False)
```

Run a stochastic scenario while retaining failures and resume state.

The uncertainty registry creates the case population before RocketPy runs.
Results are paired to that population by zero-based ``case_id``; finalization
receives successful outputs, failures, and scenario metadata separately.

**Entradas e tipos declarados**

- `config: tipo não anotado; ver contrato acima`
- `project_dir: tipo não anotado; ver contrato acima`
- `workspace_root: tipo não anotado; ver contrato acima`
- `archive_atmospheres: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `mc`

**Exceções lançadas explicitamente**

- `ConfigurationError('Monte Carlo configuration (monte_carlo.yaml) is missing or empty.')`
- `ConfigurationError(f'Unsupported stochastic scenario: {scenario_id}')`
- `ConfigurationError('monte_carlo.workers must be an integer')`
- `ConfigurationError('monte_carlo.workers must be greater than zero')`
- `ValueError('Monte Carlo sample table contains duplicate case IDs')`
- `ValueError(f'canonical Monte Carlo outputs omit RocketPy field {field!r}')`
- `ValueError(f'canonical Monte Carlo output disagrees with its RocketPy log at case {case_id}, field {field!r}')`
- `ValueError('RocketPy and canonical campaign logs have incompatible case IDs')`
- `ConfigurationError('monte_carlo.batch_size must be greater than zero')`
- `ValueError('cannot safely resume this Monte Carlo campaign: canonical results and RocketPy compatibility logs do not contain the same completed case IDs; restore matching JSONL logs or start a new campaign')`
- `RuntimeError(f'Monte Carlo campaign incomplete: {len(mc.outputs_log)}/{simulation_goal} simulations exported. Check worker errors and results in {results_dir}.')`

**Colaboradores chamados diretamente**

- `ConfigurationError`
- `str(os.environ.get('ANTARES_MC_SCENARIO', NOMINAL)).lower`
- `str`
- `os.environ.get`
- `apply_scenario`
- `int`
- `mc_cfg.get`
- `bool`
- `min`
- `os.cpu_count`
- `np.random.seed`
- `random.seed`
- `Path`
- `datetime.datetime.now(datetime.UTC).strftime`
- `datetime.datetime.now`
- `results_dir.mkdir`
- `MonteCarloCampaign`
- `canonical_campaign.snapshot_config`
- `canonical_campaign.write_manifest`
- `registry_path.exists`
- `print`
- `build_environment`
- `build_environment_ensemble`
- `archive_environment`
- `enumerate`
- `canonical_campaign.make_samples`
- `len`
- `UncertaintyRegistry`
- `SamplingPlan`
- `plan.export`
- `wx_list.append`
- `e.wind_velocity_x`
- `wy_list.append`
- `e.wind_velocity_y`
- `float`
- `np.std`
- `(env_cfg.get('wind_velocity_x') or {}).get`
- `env_cfg.get`
- `(env_cfg.get('wind_velocity_y') or {}).get`
- `ProfileStochasticEnvironment`
- `(env_cfg.get('elevation') or {}).get`
- `build_motor`
- `(mot_cfg.get('total_impulse_scale') or {}).get`
- `mot_cfg.get`
- `StochasticSolidMotor`
- `build_vehicle`
- `add_recovery_system`
- `(veh_cfg.get('mass') or {}).get`
- `veh_cfg.get`
- `(veh_cfg.get('power_off_drag_factor') or {}).get`
- `(veh_cfg.get('power_on_drag_factor') or {}).get`
- `StochasticRocket`
- `stoch_rocket.add_motor`
- `_transfer_rocket_components`
- `(config.launch.get('rail') or {}).get`
- `config.launch.get`
- `run_flight`
- `StochasticFlight`
- `launch_angle_distribution`
- `flt_cfg.get`
- `ConfiguredMonteCarlo`
- `samples_df.sort_values`
- `pd.to_numeric(ordered_samples['atmosphere_ensemble'], errors='coerce').fillna(0).astype(int).tolist`
- `pd.to_numeric(ordered_samples['atmosphere_ensemble'], errors='coerce').fillna(0).astype`
- `pd.to_numeric(ordered_samples['atmosphere_ensemble'], errors='coerce').fillna`
- `pd.to_numeric`
- `CampaignManager`
- `manager.start`
- `manager.TrajectoryStore`
- `TrajectoryStore`
- `samples_df.sort_values('case_id')['seed'].astype('uint64').tolist`
- `samples_df.sort_values('case_id')['seed'].astype`
- `types.MethodType`
- `set`
- `range`
- `samples_df[['case_id']].to_dict`
- `canonicalize_case_records`
- `ValueError`
- `restore_jsonl_case_logs`
- `canonical_outputs_path.exists`
- `pd.read_parquet`
- `cached_outputs.to_dict`
- `completed_prefix_length`
- `raw_row.items`
- `pd.isna`
- `canonical_ids.issubset`
- `raw_output_ids.issubset`
- `record.items`
- `existing_summary.exists`
- `json.loads`
- `existing_summary.read_text`
- `previous_summary.get('convergence', {}).get`
- `previous_summary.get`
- `canonical_campaign.next_target`
- `list`
- `results_dir.glob`
- `getattr`
- `mc.simulate`
- `pd.DataFrame`
- `canonical_campaign.write_batch`
- `finalize_campaign_analysis`
- `interim['convergence'].get`
- `all_flights.snapshot`
- `manager.shutdown`
- `subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=str(project_dir)).decode().strip`
- `subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=str(project_dir)).decode`
- `subprocess.check_output`
- `subprocess.check_output(['git', 'status', '--porcelain'], cwd=str(project_dir)).decode().strip`
- `subprocess.check_output(['git', 'status', '--porcelain'], cwd=str(project_dir)).decode`
- `hasattr`
- `campaign_status.upper`
- `open`
- `json.dump`
- `datetime.datetime.now(datetime.UTC).isoformat`
- `yaml.dump`
- `_failure_records`
- `RuntimeError`
- `outputs_file.exists`
- `np.argmax`
- `copy.deepcopy`
- `Flight`
- `plot_monte_carlo_dispersion`
- `plot_monte_carlo_distributions`
- `plot_monte_carlo_convergence`
- `FlightDynamicsReport`
- `report.generate`

### `execute_monte_carlo._patched_run_single`

[Implementação: source/antares_fd/simulation/monte_carlo_failure.py:362](../../source/antares_fd/simulation/monte_carlo_failure.py#L362)

```python
execute_monte_carlo._patched_run_single(*args, **kwargs)
```

Execute um caso e capture métricas e trajetória para a campanha.

Envolve o executor original, associa o resultado à população amostrada
e registra séries compactas para diagnóstico. Retorna Flight; a rotina
de campanha mantém restauração do método original e encerramento do manager.

**Entradas e tipos declarados**

- `*args: argumentos posicionais adicionais`
- `**kwargs: argumentos nomeados adicionais`

**Retornos/yields explícitos**

- `flt_nom`
- `flt_fail`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `hasattr`
- `min`
- `len`
- `int`
- `getattr`
- `mc.environment._set_stochastic`
- `mc.rocket._set_stochastic`
- `mc.flight._set_stochastic`
- `_orig_run_single`
- `all_flights.append`
- `np.argmax`
- `range`
- `copy.deepcopy`
- `Flight`
- `np.concatenate`
- `max`
- `print`

### `execute_monte_carlo._serial_inputs`

[Implementação: source/antares_fd/simulation/monte_carlo_failure.py:473](../../source/antares_fd/simulation/monte_carlo_failure.py#L473)

```python
execute_monte_carlo._serial_inputs(one_based_index)
```

Serialize entradas de um caso usando o identificador canônico.

Adapta o índice de contagem do RocketPy para o case_id iniciado em zero
e acrescenta os valores declarados e realizados ao registro JSON.

**Entradas e tipos declarados**

- `one_based_index: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `_explicit_case_id_json(_orig_evaluate_inputs(one_based_index), case_id)`

**Exceções lançadas explicitamente**

- `ValueError('RocketPy serial monitor IDs must start at one')`

**Colaboradores chamados diretamente**

- `normalize_case_id`
- `ValueError`
- `_explicit_case_id_json`
- `_orig_evaluate_inputs`

### `execute_monte_carlo._serial_outputs`

[Implementação: source/antares_fd/simulation/monte_carlo_failure.py:487](../../source/antares_fd/simulation/monte_carlo_failure.py#L487)

```python
execute_monte_carlo._serial_outputs(flight_result, one_based_index)
```

Serialize as saídas de um caso com seu identificador canônico.

Recebe flight_result e o índice de contagem RocketPy, delega a extração
de escalares e garante o vínculo com o case_id da população congelada.

**Entradas e tipos declarados**

- `flight_result: tipo não anotado; ver contrato acima`
- `one_based_index: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `_explicit_case_id_json(_orig_evaluate_outputs(flight_result, one_based_index), case_id)`

**Exceções lançadas explicitamente**

- `ValueError('RocketPy serial monitor IDs must start at one')`

**Colaboradores chamados diretamente**

- `normalize_case_id`
- `ValueError`
- `_explicit_case_id_json`
- `_orig_evaluate_outputs`

## `source/antares_fd/simulation/monte_carlo_parameters.py`

Translate configured launch-angle distributions to RocketPy arguments.

### `launch_angle_distribution`

[Implementação: source/antares_fd/simulation/monte_carlo_parameters.py:8](../../source/antares_fd/simulation/monte_carlo_parameters.py#L8)

```python
launch_angle_distribution(nominal, settings, name)
```

Translate uniform bounds or a normal spread to RocketPy sampler arguments.

Uniform settings use RocketPy's ``(low, high, "uniform")`` form; normal
settings use ``(mean, standard_deviation)``. A zero spread leaves the angle
deterministic.

**Entradas e tipos declarados**

- `nominal: tipo não anotado; ver contrato acima`
- `settings: tipo não anotado; ver contrato acima`
- `name: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `(lower, upper, 'uniform')`
- `(nominal, std) if std else None`

**Exceções lançadas explicitamente**

- `ConfigurationError(f'flight.{name}: uniform distribution requires 0 <= min < max <= {limit}.')`
- `ConfigurationError(f'flight.{name}: use min/max, not std, for uniform.')`
- `ConfigurationError(f'flight.{name}: specify distribution: uniform for bounds.')`
- `ConfigurationError(f'flight.{name}.std must be finite and non-negative.')`

**Colaboradores chamados diretamente**

- `settings.get`
- `all`
- `isinstance`
- `isfinite`
- `ConfigurationError`

## `source/antares_fd/simulation/monte_carlo_patch.py`

Local RocketPy adapters; never change dependency classes globally.

### `ProfileStochasticEnvironment.__init__`

[Implementação: source/antares_fd/simulation/monte_carlo_patch.py:19](../../source/antares_fd/simulation/monte_carlo_patch.py#L19)

```python
ProfileStochasticEnvironment.__init__(self, environment, profiles=None, **kwargs)
```

Inicialize o adaptador com os perfis atmosféricos completos disponíveis.

Delega parâmetros estocásticos à classe base e mantém environment como
perfil único quando profiles não é informado. Nenhum perfil é sorteado aqui.

**Entradas e tipos declarados**

- `environment: tipo não anotado; ver contrato acima`
- `profiles: tipo não anotado; ver contrato acima`
- `**kwargs: argumentos nomeados adicionais`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `super().__init__`
- `super`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `ProfileStochasticEnvironment._set_stochastic`

[Implementação: source/antares_fd/simulation/monte_carlo_patch.py:29](../../source/antares_fd/simulation/monte_carlo_patch.py#L29)

```python
ProfileStochasticEnvironment._set_stochastic(self, seed=None)
```

Reinicialize os geradores estocásticos com a semente do caso.

Configura a classe base e cria um Generator NumPy exclusivo para selecionar
o perfil inteiro, mantendo reprodução independente do escalonamento.

**Entradas e tipos declarados**

- `seed: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `super()._set_stochastic`
- `super`
- `np.random.default_rng`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `ProfileStochasticEnvironment.set_profile`

[Implementação: source/antares_fd/simulation/monte_carlo_patch.py:38](../../source/antares_fd/simulation/monte_carlo_patch.py#L38)

```python
ProfileStochasticEnvironment.set_profile(self, profile)
```

Fixe o perfil previamente selecionado pela população canônica.

Armazena profile para o próximo create_object; None restaura a seleção
por sorteio. Não modifica o Environment recebido.

**Entradas e tipos declarados**

- `profile: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- Nenhuma ocorrência explícita no corpo local.

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `ProfileStochasticEnvironment.create_object`

[Implementação: source/antares_fd/simulation/monte_carlo_patch.py:46](../../source/antares_fd/simulation/monte_carlo_patch.py#L46)

```python
ProfileStochasticEnvironment.create_object(self)
```

Crie um ambiente amostrado sem modificar o perfil de origem.

Escolhe o perfil prescrito ou sorteado, faz deepcopy e atualiza os campos
de vento usados pela classe base. Retorna o ambiente amostrado e registra
a seleção em last_rnd_dict para rastreabilidade.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `result`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `int`
- `self._profile_rng.integers`
- `len`
- `copy.deepcopy`
- `super().create_object`
- `super`

### `ConfiguredMonteCarlo._MonteCarlo__run_single_simulation`

[Implementação: source/antares_fd/simulation/monte_carlo_patch.py:65](../../source/antares_fd/simulation/monte_carlo_patch.py#L65)

```python
ConfiguredMonteCarlo._MonteCarlo__run_single_simulation(self)
```

Construa um voo amostrado preservando as opções numéricas nominais.

Obtém parâmetros do StochasticFlight, repõe tolerâncias e limites de passo
e cria Flight com foguete e ambiente amostrados. Retorna o voo integrado;
o nome privado acompanha o ponto de extensão da versão RocketPy utilizada.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `Flight(rocket=self.rocket.create_object(), environment=self.environment.create_object(), **parameters)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `next`
- `self.flight.dict_generator`
- `parameters.update`
- `getattr`
- `Flight`
- `self.rocket.create_object`
- `self.environment.create_object`

### `LengthDefinedStochasticFins.create_object`

[Implementação: source/antares_fd/simulation/monte_carlo_patch.py:87](../../source/antares_fd/simulation/monte_carlo_patch.py#L87)

```python
LengthDefinedStochasticFins.create_object(self)
```

Reconstrua aletas trapezoidais usando comprimento de enflechamento.

Copia os parâmetros sorteados e remove sweep_angle para não fornecer
duas definições geométricas incompatíveis ao construtor TrapezoidalFins.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `TrapezoidalFins(**values)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `dict`
- `next`
- `self.dict_generator`
- `values.pop`
- `TrapezoidalFins`

### `_transfer_rocket_components`

[Implementação: source/antares_fd/simulation/monte_carlo_patch.py:98](../../source/antares_fd/simulation/monte_carlo_patch.py#L98)

```python
_transfer_rocket_components(rocket, stoch_rocket)
```

Copy supported surfaces, rail buttons, and parachutes to the stochastic rocket.

RocketPy does not inherit these components from the deterministic vehicle.
Unsupported surface types fail here rather than disappearing from a case.

**Entradas e tipos declarados**

- `rocket: tipo não anotado; ver contrato acima`
- `stoch_rocket: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- `ConfigurationError(f'Unsupported stochastic surface: {type(surface).__name__}')`

**Colaboradores chamados diretamente**

- `isinstance`
- `stoch_rocket.add_nose`
- `StochasticNoseCone`
- `stoch_rocket.add_trapezoidal_fins`
- `LengthDefinedStochasticFins`
- `stoch_rocket.add_elliptical_fins`
- `StochasticEllipticalFins`
- `stoch_rocket.add_tail`
- `StochasticTail`
- `ConfigurationError`
- `type`
- `stoch_rocket.set_rail_buttons`
- `stoch_rocket.add_parachute`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

## `source/antares_fd/simulation/monte_carlo_resume.py`

Strict RocketPy JSONL restore and resume-prefix validation.

### `restore_jsonl_case_logs`

[Implementação: source/antares_fd/simulation/monte_carlo_resume.py:16](../../source/antares_fd/simulation/monte_carlo_resume.py#L16)

```python
restore_jsonl_case_logs(monte_carlo: Any, outputs_path: Path, inputs_path: Path, *, allowed_case_ids: set[int]) -> int
```

Restore RocketPy logs and its resume counter from validated case IDs.

JSONL physical line counts are deliberately ignored: blank lines do not
represent simulations. Input and output records must pair by unique,
zero-based case ID, and successful outputs must form a prefix so RocketPy's
append API resumes at the next correct index.

**Entradas e tipos declarados**

- `monte_carlo: Any`
- `outputs_path: Path`
- `inputs_path: Path`
- `allowed_case_ids: set[int]`

**Retornos/yields explícitos**

- `completed`

**Exceções lançadas explicitamente**

- `ValueError('allowed Monte Carlo case IDs must form a zero-based range')`
- `ValueError('RocketPy input/output logs do not contain the same case IDs; refusing an unsafe resume')`

**Colaboradores chamados diretamente**

- `normalize_case_id`
- `set`
- `range`
- `len`
- `ValueError`
- `canonicalize_case_records`
- `read_jsonl_objects`
- `Path`
- `completed_prefix_length`

## `source/antares_fd/simulation/monte_carlo_storage.py`

Bounded storage for the trajectories actually used by campaign plots.

### `TrajectoryStore.__init__`

[Implementação: source/antares_fd/simulation/monte_carlo_storage.py:18](../../source/antares_fd/simulation/monte_carlo_storage.py#L18)

```python
TrajectoryStore.__init__(self, seed=42)
```

Inicialize o armazenamento limitado de trajetórias de diagnóstico.

Define capacidades de extremos e amostras, listas internas e contadores.
A retenção é independente do número total de casos executados.

**Entradas e tipos declarados**

- `seed: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `random.Random`
- `Lock`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `TrajectoryStore.append`

[Implementação: source/antares_fd/simulation/monte_carlo_storage.py:30](../../source/antares_fd/simulation/monte_carlo_storage.py#L30)

```python
TrajectoryStore.append(self, trajectory)
```

Incorpore uma trajetória mantendo apenas extremos e amostras limitadas.

Atualiza o contador de casos vistos e seleciona registros para visualização
conforme a capacidade. Modifica o armazenamento; não altera o voo original.

**Entradas e tipos declarados**

- `trajectory: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self._extremes.get`
- `len`
- `self._sample.append`
- `self._rng.randrange`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `TrajectoryStore.snapshot`

[Implementação: source/antares_fd/simulation/monte_carlo_storage.py:55](../../source/antares_fd/simulation/monte_carlo_storage.py#L55)

```python
TrajectoryStore.snapshot(self)
```

Retorne uma cópia compacta das trajetórias retidas e dos contadores.

Agrupa extremos e amostras em um dicionário serializável para consumo
fora do processo gerenciador. Não entrega o objeto completo de cada Flight.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `{'trajectories': list(unique.values()), 'samples': [path for _, path in self._sample], 'seen': self._count}`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `dict`
- `self._extremes.values`
- `unique.update`
- `list`
- `unique.values`

## `source/antares_fd/simulation/orchestrator.py`

Construct and execute one deterministic RocketPy scenario.

### `execute_scenario`

[Implementação: source/antares_fd/simulation/orchestrator.py:8](../../source/antares_fd/simulation/orchestrator.py#L8)

```python
execute_scenario(config, project_dir, print_summary=True, export_kml=True, scenario_id=NOMINAL, environment=None)
```

Apply a scenario to a configuration copy, build RocketPy objects, and run it.

The optional ``environment`` lets paired cases reuse one atmosphere.
``print_summary`` controls the standard result export; the return value is
the RocketPy ``Flight`` object.

**Entradas e tipos declarados**

- `config: tipo não anotado; ver contrato acima`
- `project_dir: tipo não anotado; ver contrato acima`
- `print_summary: tipo não anotado; ver contrato acima`
- `export_kml: tipo não anotado; ver contrato acima`
- `scenario_id: tipo não anotado; ver contrato acima`
- `environment: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `flight`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `apply_scenario`
- `build_environment`
- `build_motor`
- `build_vehicle`
- `add_recovery_system`
- `run_flight`
- `print_flight_summary`

## `source/antares_fd/simulation/plotters.py`

Render trajectory and Monte Carlo plots from saved simulation results.

### `plot_monte_carlo_dispersion`

[Implementação: source/antares_fd/simulation/plotters.py:12](../../source/antares_fd/simulation/plotters.py#L12)

```python
plot_monte_carlo_dispersion(outputs_file: Path, results_dir: Path, run_id: str, nominal_flight=None, nominal_flight_fail=None, all_flights=None, sample_flights=None)
```

Parses outputs JSONL file to plot the 2D landing dispersion with probability ellipses.

**Entradas e tipos declarados**

- `outputs_file: Path`
- `results_dir: Path`
- `run_id: str`
- `nominal_flight: tipo não anotado; ver contrato acima`
- `nominal_flight_fail: tipo não anotado; ver contrato acima`
- `all_flights: tipo não anotado; ver contrato acima`
- `sample_flights: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `None`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `read_jsonl_objects`
- `x_impact.append`
- `y_impact.append`
- `len`
- `print`
- `np.array`
- `np.all`
- `hasattr`
- `plt.figure`
- `np.max`
- `np.argmax`
- `np.min`
- `np.argmin`
- `float`
- `any`
- `id`
- `plotted_extremes.append`
- `enumerate`
- `plt.plot`
- `np.abs(nominal_flight.x[:, 0] - t_fail_start).argmin`
- `np.abs`
- `plt.scatter`
- `np.vstack`
- `gaussian_kde`
- `x.min`
- `x.max`
- `y.min`
- `y.max`
- `complex`
- `X_grid.ravel`
- `Y_grid.ravel`
- `np.reshape`
- `kde`
- `plt.contourf`
- `plt.contour`
- `plt.gca`
- `zip`
- `probabilities.items`
- `calculate_covariance_ellipse`
- `Ellipse`
- `ax.add_patch`
- `plt.xlabel`
- `plt.ylabel`
- `getattr`
- `isinstance`
- `env.wind_direction`
- `env.wind_velocity_x`
- `env.wind_velocity_y`
- `plt.title`
- `plt.axis`
- `plt.grid`
- `str`
- `np.radians`
- `np.cos`
- `np.cov`
- `np.linalg.inv`
- `np.mean`
- `calculate_probability`
- `plt.gca().text`
- `dict`
- `plt.legend`
- `folium.Map`
- `folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri', name='Esri World Imagery', overlay=False, control=True).add_to`
- `folium.TileLayer`
- `folium.Marker(location=[lat_pad, lon_pad], popup='Launch Pad', icon=folium.Icon(color='black', icon='rocket', prefix='fa')).add_to`
- `folium.Marker`
- `folium.Icon`
- `np.linspace`
- `np.sin`
- `xy_to_latlon`
- `points.append`
- `folium.Polygon(locations=points, color=color, fill=True, fill_opacity=0.1, weight=2, tooltip=f'{label}% Containment').add_to`
- `folium.Polygon`
- `folium.CircleMarker(location=(ilat, ilon), radius=1, color='blue', fill=True, fill_opacity=0.5).add_to`
- `folium.CircleMarker`
- `folium.Marker(location=[lat_nose, lon_nose], popup='Real Nose Cone Landing', icon=folium.Icon(color='darkred', icon='info-sign')).add_to`
- `folium.Marker(location=[lat_fuse, lon_fuse], popup='Real Fuselage Landing', icon=folium.Icon(color='orange', icon='info-sign')).add_to`
- `path_pts.append`
- `folium.PolyLine(locations=path_pts, color='black', weight=2, dash_array='5', tooltip='Nominal Trajectory').add_to`
- `folium.PolyLine`
- `fail_pts.append`
- `folium.PolyLine(locations=fail_pts, color='magenta', weight=2, dash_array='5', tooltip='Failure Free-fall').add_to`
- `m.save`
- `open`
- `kml.write`
- `max`
- `random.sample`
- `list`
- `min`
- `plt.savefig`
- `plt.close`
- `fig_3d.add_subplot`
- `ax_3d.scatter`
- `np.zeros_like`
- `np.meshgrid`
- `ax_3d.plot_surface`
- `ax_3d.plot`
- `ax_3d.set_zlim`
- `ax_3d.set_xlabel`
- `ax_3d.set_ylabel`
- `ax_3d.set_zlabel`
- `ax_3d.set_title`
- `ax_3d.legend`

### `plot_monte_carlo_dispersion.calculate_probability`

[Implementação: source/antares_fd/simulation/plotters.py:196](../../source/antares_fd/simulation/plotters.py#L196)

```python
plot_monte_carlo_dispersion.calculate_probability(px, py)
```

Calcule o percentual de contenção gaussiana de um ponto no plano ENU.

Calcula a distância de Mahalanobis ao centro da nuvem de impactos
e aplica a CDF qui-quadrado com dois graus de liberdade, em %.
Não representa probabilidade de autorização de lançamento.

**Entradas e tipos declarados**

- `px: tipo não anotado; ver contrato acima`
- `py: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `chi2.cdf(mahalanobis_sq, 2) * 100`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `np.array`
- `np.dot`
- `chi2.cdf`

### `plot_monte_carlo_dispersion.xy_to_latlon`

[Implementação: source/antares_fd/simulation/plotters.py:241](../../source/antares_fd/simulation/plotters.py#L241)

```python
plot_monte_carlo_dispersion.xy_to_latlon(px, py, ref_lat, ref_lon)
```

Converta deslocamentos locais leste/norte para latitude e longitude.

Aplica a aproximação esférica local com raio terrestre explícito e latitude
do lançamento. Retorna coordenadas angulares para desenho cartográfico.

**Entradas e tipos declarados**

- `px: tipo não anotado; ver contrato acima`
- `py: tipo não anotado; ver contrato acima`
- `ref_lat: tipo não anotado; ver contrato acima`
- `ref_lon: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `(lat, lon)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `np.degrees`
- `np.cos`
- `np.radians`

### `euler_from_quaternion`

[Implementação: source/antares_fd/simulation/plotters.py:539](../../source/antares_fd/simulation/plotters.py#L539)

```python
euler_from_quaternion(e0, e1, e2, e3)
```

Convert a quaternion into euler angles (roll, pitch, yaw)
roll is rotation around x in radians (counterclockwise)
pitch is rotation around y in radians (counterclockwise)
yaw is rotation around z in radians (counterclockwise)

**Entradas e tipos declarados**

- `e0: tipo não anotado; ver contrato acima`
- `e1: tipo não anotado; ver contrato acima`
- `e2: tipo não anotado; ver contrato acima`
- `e3: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `(roll_x, pitch_y, yaw_z)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `np.degrees`
- `np.arctan2`
- `np.clip`
- `np.arcsin`

### `export_nominal_flight_plots`

[Implementação: source/antares_fd/simulation/plotters.py:561](../../source/antares_fd/simulation/plotters.py#L561)

```python
export_nominal_flight_plots(flight, results_dir: Path, project_name: str, scenario_name: str='nominal')
```

Exports nominal flight data to multiple PDF charts:
- 3D Isometric Trajectory
- Top-Down 2D Trajectory
- Side Views (X-Z and Y-Z)
- Stability margin vs Time
- Acceleration vs Time
- Pitch, Roll, Yaw vs Time
- Angle of Attack vs Time
- Mach vs Time

**Entradas e tipos declarados**

- `flight: tipo não anotado; ver contrato acima`
- `results_dir: Path`
- `project_name: str`
- `scenario_name: str`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `print`
- `matplotlib.backends.backend_pdf.PdfPages`
- `events.append`
- `plt.figure`
- `fig.add_subplot`
- `ax.plot`
- `ax.set_xlabel`
- `ax.set_ylabel`
- `ax.set_zlabel`
- `ax.set_title`
- `np.argmax`
- `ax.scatter`
- `ax.legend`
- `pdf.savefig`
- `plt.close`
- `plt.subplots`
- `ax.axis`
- `ax.grid`
- `ax1.plot`
- `ax1.scatter`
- `ax1.set_xlabel`
- `ax1.set_ylabel`
- `ax1.set_title`
- `ax1.grid`
- `ax1.legend`
- `ax2.plot`
- `ax2.scatter`
- `ax2.set_xlabel`
- `ax2.set_ylabel`
- `ax2.set_title`
- `ax2.grid`
- `ax2.legend`
- `ax.set_xlim`
- `add_event_markers`
- `np.sqrt`
- `ax1.tick_params`
- `ax1.set_xlim`
- `ax1.twinx`
- `ax2.tick_params`
- `ax3.spines['right'].set_position`
- `ax3.set_ylabel`
- `ax3.plot`
- `ax3.tick_params`
- `fig.tight_layout`
- `plt.title`
- `euler_from_quaternion`
- `pdf.close`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `export_nominal_flight_plots.add_event_markers`

[Implementação: source/antares_fd/simulation/plotters.py:588](../../source/antares_fd/simulation/plotters.py#L588)

```python
export_nominal_flight_plots.add_event_markers(ax)
```

Anote eventos do voo no painel de telemetria.

Percorre os instantes disponíveis no escopo externo e desenha linhas
e rótulos em ax, respeitando as opções de apresentação recebidas.

**Entradas e tipos declarados**

- `ax: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `ax.get_xlim`
- `ax.get_ylim`
- `ax.axvline`
- `ax.text`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `plot_monte_carlo_distributions`

[Implementação: source/antares_fd/simulation/plotters.py:784](../../source/antares_fd/simulation/plotters.py#L784)

```python
plot_monte_carlo_distributions(outputs_file, results_dir, run_id)
```

Plot selected output distributions from the scalar Monte Carlo log.

**Entradas e tipos declarados**

- `outputs_file: tipo não anotado; ver contrato acima`
- `results_dir: tipo não anotado; ver contrato acima`
- `run_id: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `None`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `read_jsonl_objects`
- `len`
- `pd.DataFrame`
- `all`
- `np.sqrt`
- `plt.figure`
- `fig.suptitle`
- `plt.subplot`
- `ax1.hist`
- `df['apogee'].mean`
- `df['apogee'].std`
- `ax1.axvline`
- `ax1.set_title`
- `ax1.set_xlabel`
- `ax1.set_ylabel`
- `ax1.legend`
- `ax1.grid`
- `ax2.hist`
- `df['out_of_rail_velocity'].mean`
- `ax2.axvline`
- `ax2.set_title`
- `ax2.set_xlabel`
- `ax2.set_ylabel`
- `ax2.legend`
- `ax2.grid`
- `ax3.hist`
- `df['max_mach_number'].mean`
- `ax3.axvline`
- `ax3.set_title`
- `ax3.set_xlabel`
- `ax3.set_ylabel`
- `ax3.legend`
- `ax3.grid`
- `np.abs`
- `ax4.hist`
- `imp_vel.mean`
- `ax4.axvline`
- `ax4.set_title`
- `ax4.set_xlabel`
- `ax4.set_ylabel`
- `ax4.legend`
- `ax4.grid`
- `ax5.scatter`
- `plt.colorbar`
- `ax5.set_title`
- `ax5.set_xlabel`
- `ax5.set_ylabel`
- `ax5.grid`
- `plt.tight_layout`
- `plt.savefig`
- `plt.close`
- `print`

### `plot_monte_carlo_convergence`

[Implementação: source/antares_fd/simulation/plotters.py:873](../../source/antares_fd/simulation/plotters.py#L873)

```python
plot_monte_carlo_convergence(outputs_file, results_dir, run_id)
```

Plot running apogee and drift summaries as cases accumulate.

**Entradas e tipos declarados**

- `outputs_file: tipo não anotado; ver contrato acima`
- `results_dir: tipo não anotado; ver contrato acima`
- `run_id: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `None`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `read_jsonl_objects`
- `len`
- `pd.DataFrame`
- `df['apogee'].expanding().mean`
- `df['apogee'].expanding`
- `df['apogee'].expanding().std`
- `np.sqrt`
- `df['impact_distance'].expanding().mean`
- `df['impact_distance'].expanding`
- `df['impact_distance'].expanding().std`
- `np.arange`
- `plt.figure`
- `fig.suptitle`
- `plt.subplot`
- `ax1.plot`
- `ax1.fill_between`
- `ax1.set_title`
- `ax1.set_xlabel`
- `ax1.set_ylabel`
- `ax1.grid`
- `ax1.legend`
- `ax2.plot`
- `ax2.fill_between`
- `ax2.set_title`
- `ax2.set_xlabel`
- `ax2.set_ylabel`
- `ax2.grid`
- `ax2.legend`
- `ax3.plot`
- `ax3.axhline`
- `ax3.set_ylim`
- `ax3.set_title`
- `ax3.set_xlabel`
- `ax3.set_ylabel`
- `ax3.grid`
- `ax3.legend`
- `plt.tight_layout`
- `plt.savefig`
- `plt.close`

## `source/antares_fd/simulation/report.py`

Build a standalone LaTeX or plain-text summary from Monte Carlo artifacts.

### `_summarize_metric`

[Implementação: source/antares_fd/simulation/report.py:11](../../source/antares_fd/simulation/report.py#L11)

```python
_summarize_metric(values: pd.Series, metric: str) -> tuple[int, float | None, float | None]
```

Return the valid count, sample mean, and sample standard deviation.

**Entradas e tipos declarados**

- `values: pd.Series`
- `metric: str`

**Retornos/yields explícitos**

- `summarize_finite_values(values, metric, ddof=1)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `summarize_finite_values`

### `generate_latex_report`

[Implementação: source/antares_fd/simulation/report.py:16](../../source/antares_fd/simulation/report.py#L16)

```python
generate_latex_report(config, results_dir: Path, run_id: str)
```

Write the report from saved configuration and results, with a text fallback.

**Entradas e tipos declarados**

- `config: tipo não anotado; ver contrato acima`
- `results_dir: Path`
- `run_id: str`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `print`
- `mc_cfg.items`
- `isinstance`
- `category.capitalize`
- `params.items`
- `param.replace`
- `outputs_file.exists`
- `read_jsonl_objects`
- `pd.DataFrame`
- `_summarize_metric`
- `col.replace('_', ' ').title`
- `col.replace`
- `run_id.replace`
- `mc_cfg.get`
- `plot_2d.exists`
- `plot_3d.exists`
- `plot_dist.exists`
- `plot_conv.exists`
- `open`
- `f.write`
- `subprocess.run`
- `str`
- `f_txt.write`
- `category.upper`
- `locals`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

## `source/antares_fd/simulation/results.py`

Export a human-readable summary and optional artifacts for one flight.

### `print_flight_summary`

[Implementação: source/antares_fd/simulation/results.py:11](../../source/antares_fd/simulation/results.py#L11)

```python
print_flight_summary(flight, project_dir=None)
```

Prints a standard summary of the flight simulation, exports KML, PDF, and Manifest.
Supports unified campaign mode when ANTARES_CAMPAIGN_DIR is set.

**Entradas e tipos declarados**

- `flight: tipo não anotado; ver contrato acima`
- `project_dir: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `None`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `print`
- `len`
- `os.environ.get`
- `Path`
- `traj_dir.mkdir`
- `datetime.datetime.now(datetime.UTC).strftime`
- `datetime.datetime.now`
- `results_dir.mkdir`
- `FlightDataExporter(flight).export_kml`
- `FlightDataExporter`
- `str`
- `zip`
- `StaticMap`
- `Line`
- `m.add_line`
- `CircleMarker`
- `m.add_marker`
- `m.render`
- `img.save`
- `subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=str(project_dir)).decode().strip`
- `subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=str(project_dir)).decode`
- `subprocess.check_output`
- `bool`
- `subprocess.check_output(['git', 'status', '--porcelain'], cwd=str(project_dir)).decode().strip`
- `subprocess.check_output(['git', 'status', '--porcelain'], cwd=str(project_dir)).decode`
- `datetime.datetime.now(datetime.UTC).isoformat`
- `float`
- `open`
- `yaml.dump`
- `export_nominal_flight_plots`
- `FlightDynamicsReport`
- `report.generate`

## `source/antares_fd/simulation/runner.py`

Translate explicit numerical settings and execute a RocketPy flight.

### `flight_options`

[Implementação: source/antares_fd/simulation/runner.py:16](../../source/antares_fd/simulation/runner.py#L16)

```python
flight_options(simulation_config)
```

Return supported Flight keyword arguments; never ignore a misspelling.

**Entradas e tipos declarados**

- `simulation_config: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `config`

**Exceções lançadas explicitamente**

- `ConfigurationError(f'Unsupported simulation options: {sorted(unknown)}')`
- `ConfigurationError(f"simulation.{key} must be finite and {('nonnegative' if key == 'min_time_step' else 'positive')}")`

**Colaboradores chamados diretamente**

- `dict`
- `set`
- `ConfigurationError`
- `sorted`
- `np.asarray`
- `np.isfinite(values).all`
- `np.isfinite`
- `lower_ok.all`

### `run_flight`

[Implementação: source/antares_fd/simulation/runner.py:31](../../source/antares_fd/simulation/runner.py#L31)

```python
run_flight(rocket, environment, launch_config, simulation_config)
```

Execute with configured tolerances, preserving RocketPy's defaults otherwise.

**Entradas e tipos declarados**

- `rocket: tipo não anotado; ver contrato acima`
- `environment: tipo não anotado; ver contrato acima`
- `launch_config: tipo não anotado; ver contrato acima`
- `simulation_config: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `flight`

**Exceções lançadas explicitamente**

- `ConfigurationError('launch_config is required for Flight')`
- `ConfigurationError('launch.rail.length is required and must be positive')`
- `ConfigurationError('launch.rail.inclination_deg must be in [0, 90]')`
- `ConfigurationError('launch.rail.heading_deg is required in [0, 360]')`
- `ConfigurationError(f'Nonzero launch.rail.{key} is not implemented')`
- `ConfigurationError(f'Nonzero launch.initial_conditions.{section}: use simulation.initial_solution')`
- `ConfigurationError('Delayed ignition is not implemented in the launch builder')`
- `RuntimeError('Flight integration produced non-finite state values')`

**Colaboradores chamados diretamente**

- `ConfigurationError`
- `launch_config.get`
- `rail.get`
- `np.isfinite`
- `launch_config.get('initial_conditions', {}).items`
- `any`
- `entries.values`
- `ignition.get`
- `Flight`
- `flight_options`
- `np.isfinite(np.asarray(flight.solution, dtype=float)).all`
- `np.asarray`
- `RuntimeError`

## `source/antares_fd/simulation/scenarios.py`

Canonical mission scenarios and explicit recovery overrides.

Scenario definitions live here so deterministic simulations, stochastic
campaigns, metrics and reports use the same identifiers and the same physical
configuration changes.  The functions mutate only a deep copy of the loaded
project configuration.

### `_devices`

[Implementação: source/antares_fd/simulation/scenarios.py:37](../../source/antares_fd/simulation/scenarios.py#L37)

```python
_devices(recovery: dict[str, Any]) -> list[dict[str, Any]]
```

Return the configured device list, creating it when absent.

**Entradas e tipos declarados**

- `recovery: dict[str, Any]`

**Retornos/yields explícitos**

- `recovery.setdefault('devices', [])`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `recovery.setdefault`

### `_nominal`

[Implementação: source/antares_fd/simulation/scenarios.py:42](../../source/antares_fd/simulation/scenarios.py#L42)

```python
_nominal(recovery: dict[str, Any]) -> None
```

Leave the project's recovery devices unchanged for the nominal case.

**Entradas e tipos declarados**

- `recovery: dict[str, Any]`

**Retornos/yields explícitos**

- `None`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- Nenhuma ocorrência explícita no corpo local.

### `_main_at_apogee`

[Implementação: source/antares_fd/simulation/scenarios.py:47](../../source/antares_fd/simulation/scenarios.py#L47)

```python
_main_at_apogee(recovery: dict[str, Any]) -> None
```

Disable the drogue and set the main parachute trigger to apogee.

**Entradas e tipos declarados**

- `recovery: dict[str, Any]`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `_devices`
- `str(device.get('id', '')).lower`
- `str`
- `device.get`
- `device.setdefault`
- `trigger.setdefault`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `_only_reefing`

[Implementação: source/antares_fd/simulation/scenarios.py:61](../../source/antares_fd/simulation/scenarios.py#L61)

```python
_only_reefing(recovery: dict[str, Any]) -> None
```

Keep the existing two-stage implementation explicit.

The project represents the reefed state with the drogue device at apogee
and the fully open main device at the configured main altitude.  The CdS
reduction is read from the configured main parachute and is therefore part
of the scenario definition rather than report logic.

**Entradas e tipos declarados**

- `recovery: dict[str, Any]`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- `ConfigurationError('only_reefing requires recovery.reefing.cd_s_fraction in (0, 1]')`

**Colaboradores chamados diretamente**

- `recovery.get('reefing', {}).get`
- `recovery.get`
- `ConfigurationError`
- `_devices`
- `str(device.get('id', '')).lower`
- `str`
- `device.get`
- `device.get('aerodynamics', {}).get`
- `device.setdefault`
- `trigger.setdefault`
- `float`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `_ballistic`

[Implementação: source/antares_fd/simulation/scenarios.py:90](../../source/antares_fd/simulation/scenarios.py#L90)

```python
_ballistic(recovery: dict[str, Any]) -> None
```

Disable the recovery system and all individual deployment devices.

**Entradas e tipos declarados**

- `recovery: dict[str, Any]`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `_devices`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `_drogue_only`

[Implementação: source/antares_fd/simulation/scenarios.py:97](../../source/antares_fd/simulation/scenarios.py#L97)

```python
_drogue_only(recovery: dict[str, Any]) -> None
```

Enable only the device whose ID is ``drogue``.

**Entradas e tipos declarados**

- `recovery: dict[str, Any]`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `_devices`
- `str(device.get('id', '')).lower`
- `str`
- `device.get`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `get_scenario`

[Implementação: source/antares_fd/simulation/scenarios.py:112](../../source/antares_fd/simulation/scenarios.py#L112)

```python
get_scenario(scenario_id: str) -> ScenarioDefinition
```

Return a registered scenario or raise for an unsupported ID.

**Entradas e tipos declarados**

- `scenario_id: str`

**Retornos/yields explícitos**

- `SCENARIOS[key]`

**Exceções lançadas explicitamente**

- `ValueError(f'Unsupported scenario_id: {scenario_id}')`

**Colaboradores chamados diretamente**

- `str(scenario_id).strip().lower`
- `str(scenario_id).strip`
- `str`
- `ValueError`

### `scenario_ids`

[Implementação: source/antares_fd/simulation/scenarios.py:120](../../source/antares_fd/simulation/scenarios.py#L120)

```python
scenario_ids(config: Any, include_optional: bool=True) -> tuple[str, ...]
```

Return configured canonical IDs, preserving required scenario order.

**Entradas e tipos declarados**

- `config: Any`
- `include_optional: bool`

**Retornos/yields explícitos**

- `REQUIRED_SCENARIOS`
- `tuple(result or REQUIRED_SCENARIOS)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `config.monte_carlo.get`
- `str(value).strip().lower`
- `str(value).strip`
- `str`
- `result.extend`
- `tuple`

### `apply_scenario`

[Implementação: source/antares_fd/simulation/scenarios.py:136](../../source/antares_fd/simulation/scenarios.py#L136)

```python
apply_scenario(config: Any, scenario_id: str) -> Any
```

Deep-copy a ``ProjectConfig`` and apply one canonical override.

**Entradas e tipos declarados**

- `config: Any`
- `scenario_id: str`

**Retornos/yields explícitos**

- `result`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `copy.deepcopy`
- `get_scenario`
- `definition.override`

## `source/antares_fd/simulation/statistics.py`

Statistical geometry helpers used by flight-dispersion plots.

### `calculate_covariance_ellipse`

[Implementação: source/antares_fd/simulation/statistics.py:6](../../source/antares_fd/simulation/statistics.py#L6)

```python
calculate_covariance_ellipse(x: np.ndarray, y: np.ndarray, probability: float)
```

Calculates a 2D probability containment ellipse for a given probability.
Assumes a bivariate normal distribution.

Args:
    x: Array of x coordinates (e.g. East).
    y: Array of y coordinates (e.g. North).
    probability: Desired containment probability (e.g. 0.95 for 95%).

Returns:
    dict: Containing 'center' (x, y), 'width', 'height', 'angle' (in degrees),
          and the calculated 'chi2_val'.

**Entradas e tipos declarados**

- `x: np.ndarray`
- `y: np.ndarray`
- `probability: float`

**Retornos/yields explícitos**

- `{'center': (mean_x, mean_y), 'width': width, 'height': height, 'angle': angle, 'chi2_val': chi2_val}`

**Exceções lançadas explicitamente**

- `ValueError('x and y must be arrays of equal length with at least 2 points.')`
- `ValueError('Coordinates must contain only finite values.')`
- `ValueError('Probability must be between 0 and 1.')`
- `ValueError('Coordinate covariance is not positive semidefinite.')`

**Colaboradores chamados diretamente**

- `np.asarray`
- `ValueError`
- `np.isfinite(x).all`
- `np.isfinite`
- `np.isfinite(y).all`
- `np.vstack`
- `np.cov`
- `np.mean`
- `np.linalg.eigh`
- `np.finfo`
- `max`
- `float`
- `np.max`
- `np.abs`
- `eigvals.min`
- `np.maximum`
- `eigvals.argsort`
- `chi2.ppf`
- `np.sqrt`
- `np.degrees`
- `np.arctan2`

## `source/antares_fd/simulation/uncertainty.py`

### `UncertaintyDef.provenance_type`

[Implementação: source/antares_fd/simulation/uncertainty.py:20](../../source/antares_fd/simulation/uncertainty.py#L20)

```python
UncertaintyDef.provenance_type(self) -> str
```

Retorne a classificação de origem da incerteza.

Consulta provenance.type e retorna UNKNOWN quando ausente, sem promover
a distribuição a uma medição experimental.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `str(self.provenance.get('type', 'UNKNOWN'))`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `str`
- `self.provenance.get`

### `UncertaintyDef.correlation_group`

[Implementação: source/antares_fd/simulation/uncertainty.py:29](../../source/antares_fd/simulation/uncertainty.py#L29)

```python
UncertaintyDef.correlation_group(self) -> str | None
```

Retorne o grupo de correlação declarado nos parâmetros.

Consulta params sem inferir dependências; ausência retorna None.
O metadado não implementa por si só uma distribuição multivariada.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `self.params.get('correlation_group')`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.params.get`

### `UncertaintyDef.epistemic_or_aleatory`

[Implementação: source/antares_fd/simulation/uncertainty.py:38](../../source/antares_fd/simulation/uncertainty.py#L38)

```python
UncertaintyDef.epistemic_or_aleatory(self) -> str
```

Retorne a natureza epistemológica declarada da incerteza.

Lê params.epistemic_or_aleatory e conserva UNKNOWN se não houver
classificação explícita; não classifica automaticamente a variável.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `str(self.params.get('epistemic_or_aleatory', 'UNKNOWN'))`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `str`
- `self.params.get`

### `UncertaintyRegistry.__init__`

[Implementação: source/antares_fd/simulation/uncertainty.py:49](../../source/antares_fd/simulation/uncertainty.py#L49)

```python
UncertaintyRegistry.__init__(self, yaml_path: Path)
```

Inicialize e carregue o registro de incertezas de yaml_path.

Prepara versão de esquema e mapeamento de definições, depois chama load.
Erros de leitura ou formato interrompem a criação do registro.

**Entradas e tipos declarados**

- `yaml_path: Path`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.load`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `UncertaintyRegistry.load`

[Implementação: source/antares_fd/simulation/uncertainty.py:60](../../source/antares_fd/simulation/uncertainty.py#L60)

```python
UncertaintyRegistry.load(self)
```

Read the uncertainty YAML and populate enabled parameter definitions.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `open`
- `yaml.safe_load`
- `data.get`
- `uncs.items`
- `v.get`
- `UncertaintyDef`
- `v.items`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `UncertaintyRegistry.validate`

[Implementação: source/antares_fd/simulation/uncertainty.py:81](../../source/antares_fd/simulation/uncertainty.py#L81)

```python
UncertaintyRegistry.validate(self, strict: bool=True) -> list[str]
```

Validate supported distribution parameters before trajectory work.

**Entradas e tipos declarados**

- `strict: bool`

**Retornos/yields explícitos**

- `errors`

**Exceções lançadas explicitamente**

- `ValueError('Invalid uncertainty registry: ' + '; '.join(errors))`

**Colaboradores chamados diretamente**

- `self.registry.items`
- `uncertainty.distribution.lower`
- `errors.append`
- `float`
- `params.get`
- `{'left', 'mode', 'right'}.issubset`
- `ValueError`
- `'; '.join`

### `SamplingPlan.__init__`

[Implementação: source/antares_fd/simulation/uncertainty.py:102](../../source/antares_fd/simulation/uncertainty.py#L102)

```python
SamplingPlan.__init__(self, registry: UncertaintyRegistry, num_samples: int, seed: int=42, env_ensemble_size: int=0)
```

Prepare uma população reprodutível antes de integrar trajetórias.

Armazena registro, número de casos, semente e tamanho do ensemble;
valida distribuições e gera a tabela samples com case_id e seed estáveis.

**Entradas e tipos declarados**

- `registry: UncertaintyRegistry`
- `num_samples: int`
- `seed: int`
- `env_ensemble_size: int`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `pd.DataFrame`
- `registry.validate`
- `self._generate`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `SamplingPlan._generate`

[Implementação: source/antares_fd/simulation/uncertainty.py:116](../../source/antares_fd/simulation/uncertainty.py#L116)

```python
SamplingPlan._generate(self)
```

Gere uma linha por caso com um fluxo aleatório independente.

SeedSequence deriva sementes filhas da semente raiz; cada Generator
amostra todas as definições habilitadas daquele caso. Substitui samples
pelo DataFrame completo, preservando a ordem dos IDs.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `np.random.SeedSequence`
- `root.spawn`
- `enumerate`
- `np.random.default_rng`
- `int`
- `child.generate_state`
- `self.registry.registry.items`
- `self._sample_value`
- `rows.append`
- `pd.DataFrame`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `SamplingPlan._sample_value`

[Implementação: source/antares_fd/simulation/uncertainty.py:134](../../source/antares_fd/simulation/uncertainty.py#L134)

```python
SamplingPlan._sample_value(self, uncertainty: UncertaintyDef, rng: np.random.Generator) -> Any
```

Sample one case using only that case's generator.

**Entradas e tipos declarados**

- `uncertainty: UncertaintyDef`
- `rng: np.random.Generator`

**Retornos/yields explícitos**

- `float(rng.uniform(float(params.get('min', 0.0)), float(params.get('max', 1.0))))`
- `np.nan`
- `float(rng.normal(float(mean), float(params.get('sigma', 1.0))))`
- `float(rng.triangular(float(params['left']), float(params['mode']), float(params['right'])))`
- `values[int(rng.integers(0, len(values)))]`

**Exceções lançadas explicitamente**

- `ValueError(f"Uncertainty '{uncertainty.name}' has no categorical values")`
- `ValueError(f"Uncertainty '{uncertainty.name}' has no empirical samples")`
- `ValueError(f'Unsupported distribution: {uncertainty.distribution}')`

**Colaboradores chamados diretamente**

- `uncertainty.distribution.lower`
- `float`
- `rng.uniform`
- `params.get`
- `rng.normal`
- `rng.triangular`
- `list`
- `range`
- `ValueError`
- `int`
- `rng.integers`
- `len`

### `SamplingPlan.export`

[Implementação: source/antares_fd/simulation/uncertainty.py:164](../../source/antares_fd/simulation/uncertainty.py#L164)

```python
SamplingPlan.export(self, path: Path)
```

Exporte a população amostrada para Parquet ou CSV conforme a extensão.

Parquet usa pyarrow e compressão zstd; os demais caminhos recebem CSV.
Não inclui índice pandas; erros de escrita são propagados ao chamador.

**Entradas e tipos declarados**

- `path: Path`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `Path`
- `path.suffix.lower`
- `self.samples.to_parquet`
- `self.samples.to_csv`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

## `source/antares_fd/simulation/uq_campaign.py`

Canonical campaign metadata, deterministic sampling and resumable paths.

### `_hash_file`

[Implementação: source/antares_fd/simulation/uq_campaign.py:40](../../source/antares_fd/simulation/uq_campaign.py#L40)

```python
_hash_file(path: Path) -> str
```

Calcule SHA-256 de uma entrada para identificar a população da campanha.

Lê blocos binários e retorna digest hexadecimal, sem incluir caminhos
absolutos no conteúdo identificado.

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

### `_path_component`

[Implementação: source/antares_fd/simulation/uq_campaign.py:53](../../source/antares_fd/simulation/uq_campaign.py#L53)

```python
_path_component(value: str, label: str) -> str
```

Valide um identificador usado como componente de caminho.

Rejeita vazio, separadores e referências que escapem do diretório.
Retorna texto seguro para organização dos artefatos da campanha.

**Entradas e tipos declarados**

- `value: str`
- `label: str`

**Retornos/yields explícitos**

- `value`

**Exceções lançadas explicitamente**

- `ValueError(f'{label} must be a single safe path component')`

**Colaboradores chamados diretamente**

- `isinstance`
- `value.strip`
- `Path(value).is_absolute`
- `Path`
- `ValueError`

### `_results_root`

[Implementação: source/antares_fd/simulation/uq_campaign.py:72](../../source/antares_fd/simulation/uq_campaign.py#L72)

```python
_results_root(root: Path) -> Path
```

Resolva a raiz autorizada de resultados de um projeto.

Resolve root/results e rejeita links simbólicos na raiz de resultados.
Retorna Path para criação dos diretórios da campanha.

**Entradas e tipos declarados**

- `root: Path`

**Retornos/yields explícitos**

- `results`

**Exceções lançadas explicitamente**

- `ValueError(f'Campaign artifacts cannot use a symlinked results directory: {results}')`

**Colaboradores chamados diretamente**

- `Path(root).resolve`
- `Path`
- `results.is_symlink`
- `ValueError`

### `_results_artifact_path`

[Implementação: source/antares_fd/simulation/uq_campaign.py:85](../../source/antares_fd/simulation/uq_campaign.py#L85)

```python
_results_artifact_path(root: Path, path: Path) -> Path
```

Resolve one campaign artifact path and reject escapes or symlink hops.

**Entradas e tipos declarados**

- `root: Path`
- `path: Path`

**Retornos/yields explícitos**

- `lexical`

**Exceções lançadas explicitamente**

- `ValueError(f'Campaign artifact path must remain below results/: {path}')`
- `ValueError(f'Campaign artifact path cannot traverse symlinks: {current}')`
- `ValueError(f'Campaign artifact path resolves outside results/: {path}')`

**Colaboradores chamados diretamente**

- `Path(root).resolve`
- `Path`
- `_results_root`
- `candidate.is_absolute`
- `os.path.abspath`
- `lexical.is_relative_to`
- `ValueError`
- `lexical.relative_to`
- `current.is_symlink`
- `results.resolve`
- `lexical.resolve`
- `resolved.is_relative_to`

### `campaign_path_for`

[Implementação: source/antares_fd/simulation/uq_campaign.py:107](../../source/antares_fd/simulation/uq_campaign.py#L107)

```python
campaign_path_for(root: Path, project: str, campaign_id: str) -> Path
```

Return a validated campaign path beneath the repository results area.

**Entradas e tipos declarados**

- `root: Path`
- `project: str`
- `campaign_id: str`

**Retornos/yields explícitos**

- `_results_artifact_path(repository, repository / 'results' / project_name / run_id)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `_path_component`
- `Path(root).resolve`
- `Path`
- `_results_artifact_path`

### `_git_metadata`

[Implementação: source/antares_fd/simulation/uq_campaign.py:115](../../source/antares_fd/simulation/uq_campaign.py#L115)

```python
_git_metadata(root: Path) -> dict[str, Any]
```

Obtenha revisão Git e estado de trabalho para a proveniência.

Delega ao coletor compartilhado que registra commit, alterações e snapshot.
Retorna metadados sem modificar o repositório.

**Entradas e tipos declarados**

- `root: Path`

**Retornos/yields explícitos**

- `{'commit': provenance.get('commit', 'unknown'), 'branch': provenance.get('branch', 'unknown'), 'dirty': dirty, 'working_tree_snapshot_sha256': provenance.get('working_tree_snapshot_sha256', 'unknown')}`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `get_git_provenance`
- `Path`
- `provenance.get`

### `MonteCarloCampaign.__post_init__`

[Implementação: source/antares_fd/simulation/uq_campaign.py:146](../../source/antares_fd/simulation/uq_campaign.py#L146)

```python
MonteCarloCampaign.__post_init__(self) -> None
```

Prepare a configuração resolvida e os diretórios da campanha Monte Carlo.

Resolve perfil, limites de amostragem, hashes e estado de retomada;
valida consistência antes de criar ou reutilizar os artefatos canônicos.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- `ValueError(f'Unknown Monte Carlo profile: {self.profile}')`
- `raise (propaga a exceção ativa)`

**Colaboradores chamados diretamente**

- `ValueError`
- `dict`
- `time.perf_counter`
- `_path_component`
- `datetime.now(timezone.utc).strftime`
- `datetime.now`
- `campaign_path_for`
- `candidate_root.mkdir`
- `candidate_root.exists`
- `self.root_path.mkdir`
- `_results_artifact_path`
- `self.path.mkdir`
- `self.samples_path.parent.mkdir`
- `self.batches_path.mkdir`
- `directory.mkdir`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `MonteCarloCampaign.is_scenario_campaign`

[Implementação: source/antares_fd/simulation/uq_campaign.py:197](../../source/antares_fd/simulation/uq_campaign.py#L197)

```python
MonteCarloCampaign.is_scenario_campaign(self) -> bool
```

Informe se a campanha usa o layout compartilhado por cenários.

Retorna bool a partir do estado configurado; a propriedade determina
como os diretórios e manifestos devem ser organizados.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `self.scenario_id is not None`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- Nenhuma ocorrência explícita no corpo local.

### `MonteCarloCampaign.snapshot_config`

[Implementação: source/antares_fd/simulation/uq_campaign.py:205](../../source/antares_fd/simulation/uq_campaign.py#L205)

```python
MonteCarloCampaign.snapshot_config(self, project_dir: Path) -> dict[str, str]
```

Snapshot all project-local model inputs without replacing prior bytes.

**Entradas e tipos declarados**

- `project_dir: Path`

**Retornos/yields explícitos**

- `hashes`

**Exceções lançadas explicitamente**

- `ValueError(f'Campaign model input changed after snapshot: {relative.as_posix()}')`
- `RuntimeError(f'Campaign model input changed while snapshotting: {relative.as_posix()}')`

**Colaboradores chamados diretamente**

- `Path(project_dir).resolve`
- `Path`
- `_results_artifact_path`
- `destination.mkdir`
- `collect_project_model_inputs`
- `source.relative_to`
- `target.parent.mkdir`
- `_hash_file`
- `target.exists`
- `ValueError`
- `relative.as_posix`
- `shutil.copy2`
- `RuntimeError`

### `MonteCarloCampaign.next_target`

[Implementação: source/antares_fd/simulation/uq_campaign.py:226](../../source/antares_fd/simulation/uq_campaign.py#L226)

```python
MonteCarloCampaign.next_target(self, completed: int, converged: bool=False) -> int
```

Return the next bounded target for an adaptive official campaign.

**Entradas e tipos declarados**

- `completed: int`
- `converged: bool`

**Retornos/yields explícitos**

- `min(self.max_samples, self.target_samples)`
- `self.min_samples`
- `completed`
- `min(self.max_samples, completed + max(1, batch))`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `int`
- `self.settings.get`
- `min`
- `max`

### `MonteCarloCampaign.target_samples`

[Implementação: source/antares_fd/simulation/uq_campaign.py:239](../../source/antares_fd/simulation/uq_campaign.py#L239)

```python
MonteCarloCampaign.target_samples(self) -> int
```

Retorne a meta de casos definida pelo perfil e pelas opções de execução.

Converte o valor configurado em inteiro; a meta é usada pelo controlador
de lotes, sem gerar amostras nesta consulta.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `int(self.settings.get('target_samples', self.settings.get('min_samples', 0)))`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `int`
- `self.settings.get`

### `MonteCarloCampaign.min_samples`

[Implementação: source/antares_fd/simulation/uq_campaign.py:248](../../source/antares_fd/simulation/uq_campaign.py#L248)

```python
MonteCarloCampaign.min_samples(self) -> int
```

Retorne o mínimo de casos exigido antes da parada por convergência.

Obtém o valor do perfil configurado e o converte em inteiro.
A consulta não avalia a convergência dos resultados.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `int(self.settings.get('min_samples', self.target_samples))`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `int`
- `self.settings.get`

### `MonteCarloCampaign.max_samples`

[Implementação: source/antares_fd/simulation/uq_campaign.py:257](../../source/antares_fd/simulation/uq_campaign.py#L257)

```python
MonteCarloCampaign.max_samples(self) -> int
```

Retorne o limite superior de casos autorizado para a campanha.

Obtém o limite do perfil e opções resolvidas; o controlador de lotes
usa esse valor para impedir crescimento ilimitado da população.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `int(self.settings.get('max_samples', self.target_samples))`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `int`
- `self.settings.get`

### `MonteCarloCampaign.make_samples`

[Implementação: source/antares_fd/simulation/uq_campaign.py:265](../../source/antares_fd/simulation/uq_campaign.py#L265)

```python
MonteCarloCampaign.make_samples(self, registry_path: Path | None, count: int | None=None, ensemble_size: int=0) -> pd.DataFrame
```

Create the immutable input table, including a case-local seed.

**Entradas e tipos declarados**

- `registry_path: Path | None`
- `count: int | None`
- `ensemble_size: int`

**Retornos/yields explícitos**

- `pd.read_parquet(self.samples_path)`
- `samples`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `_results_artifact_path`
- `self.samples_path.exists`
- `pd.read_parquet`
- `int`
- `Path(registry_path).exists`
- `Path`
- `UncertaintyRegistry`
- `SamplingPlan(registry, count, self.master_seed, ensemble_size).samples.copy`
- `SamplingPlan`
- `np.random.SeedSequence(self.master_seed).spawn`
- `np.random.SeedSequence`
- `pd.DataFrame`
- `range`
- `child.generate_state`
- `write_parquet_atomic`

### `MonteCarloCampaign.completed_case_ids`

[Implementação: source/antares_fd/simulation/uq_campaign.py:280](../../source/antares_fd/simulation/uq_campaign.py#L280)

```python
MonteCarloCampaign.completed_case_ids(self) -> set[int]
```

Recupere IDs concluídos nas saídas canônicas já salvas.

Lê os lotes disponíveis e retorna os identificadores para planejamento
de retomada, sem contar arquivos como substitutos de casos.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `completed`

**Exceções lançadas explicitamente**

- `ValueError(f'Campaign batch cannot be a symlink: {file}')`
- `ValueError(f'Cannot read campaign batch file: {file}')`

**Colaboradores chamados diretamente**

- `set`
- `_results_artifact_path`
- `sorted`
- `batches_path.glob`
- `file.is_symlink`
- `ValueError`
- `pd.read_parquet`
- `completed.update`
- `batch['case_id'].astype(int).tolist`
- `batch['case_id'].astype`

### `MonteCarloCampaign.write_batch`

[Implementação: source/antares_fd/simulation/uq_campaign.py:299](../../source/antares_fd/simulation/uq_campaign.py#L299)

```python
MonteCarloCampaign.write_batch(self, batch_number: int, results: pd.DataFrame) -> Path
```

Grave um lote canônico de resultados em Parquet.

Organiza o nome do lote no diretório da campanha e utiliza escrita atômica.
O arquivo só substitui o destino depois da gravação completa.

**Entradas e tipos declarados**

- `batch_number: int`
- `results: pd.DataFrame`

**Retornos/yields explícitos**

- `write_parquet_atomic(results, path)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `_results_artifact_path`
- `int`
- `write_parquet_atomic`

### `MonteCarloCampaign.write_manifest`

[Implementação: source/antares_fd/simulation/uq_campaign.py:310](../../source/antares_fd/simulation/uq_campaign.py#L310)

```python
MonteCarloCampaign.write_manifest(self, status: str, samples: pd.DataFrame | None=None, extra: Mapping[str, Any] | None=None) -> Path
```

Publique o manifesto da campanha com o estado de execução atual.

Reúne configuração resolvida, população, proveniência e detalhes recebidos
e escreve JSON de forma atômica para permitir auditoria e retomada.

**Entradas e tipos declarados**

- `status: str`
- `samples: pd.DataFrame | None`
- `extra: Mapping[str, Any] | None`

**Retornos/yields explícitos**

- `write_json_atomic(manifest, self.path / 'manifest.json')`

**Exceções lançadas explicitamente**

- `ValueError(f'Campaign manifest cannot be a symlink: {manifest_path}')`

**Colaboradores chamados diretamente**

- `int`
- `len`
- `_results_artifact_path`
- `manifest_path.is_symlink`
- `ValueError`
- `manifest_path.exists`
- `json.loads`
- `manifest_path.read_text`
- `str`
- `self.samples_path.relative_to`
- `self.completed_case_ids`
- `platform.platform`
- `_git_metadata`
- `Path`
- `datetime.now(timezone.utc).isoformat`
- `datetime.now`
- `previous.get`
- `manifest.update`
- `dict`
- `write_json_atomic`

### `MonteCarloCampaign.artifact_hashes`

[Implementação: source/antares_fd/simulation/uq_campaign.py:341](../../source/antares_fd/simulation/uq_campaign.py#L341)

```python
MonteCarloCampaign.artifact_hashes(self) -> dict[str, str]
```

Hash canonical files so an archived campaign can be verified.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `hashes`

**Exceções lançadas explicitamente**

- `ValueError(f'Campaign artifact cannot be a symlink: {file}')`

**Colaboradores chamados diretamente**

- `_results_artifact_path`
- `sorted`
- `self.path.rglob`
- `file.is_symlink`
- `ValueError`
- `file.is_file`
- `str`
- `file.relative_to`
- `_hash_file`

### `MonteCarloCampaign.archive`

[Implementação: source/antares_fd/simulation/uq_campaign.py:352](../../source/antares_fd/simulation/uq_campaign.py#L352)

```python
MonteCarloCampaign.archive(self, destination: Path | None=None) -> Path
```

Create a portable ZIP containing canonical campaign evidence.

**Entradas e tipos declarados**

- `destination: Path | None`

**Retornos/yields explícitos**

- `destination`

**Exceções lançadas explicitamente**

- `ValueError(f'Campaign manifest cannot be a symlink: {manifest_path}')`
- `FileNotFoundError(f'Cannot archive campaign without a manifest: {manifest_path}')`
- `ValueError(f'Cannot archive campaign with an unreadable manifest: {manifest_path}')`
- `ValueError(f'Cannot archive campaign without a recognized terminal status: {manifest_path}')`
- `ValueError('Campaign archive must be outside its source campaign directory')`
- `FileExistsError(f'Campaign archive already exists: {destination}')`
- `ValueError(f'Campaign archive cannot contain symlinked artifacts: {path}')`

**Colaboradores chamados diretamente**

- `_results_artifact_path`
- `manifest_path.is_symlink`
- `ValueError`
- `json.loads`
- `manifest_path.read_text`
- `FileNotFoundError`
- `isinstance`
- `manifest.get`
- `Path`
- `destination.is_absolute`
- `Path(self.root).resolve`
- `destination.is_relative_to`
- `destination.exists`
- `FileExistsError`
- `self.path.rglob`
- `path.is_symlink`
- `self.artifact_hashes`
- `write_json_atomic`
- `destination.parent.mkdir`
- `zipfile.ZipFile`
- `sorted`
- `file.is_file`
- `archive.write`
- `file.relative_to`

### `StochasticScenarioCampaign.__post_init__`

[Implementação: source/antares_fd/simulation/uq_campaign.py:402](../../source/antares_fd/simulation/uq_campaign.py#L402)

```python
StochasticScenarioCampaign.__post_init__(self) -> None
```

Prepare uma campanha estocástica com uma população comum entre cenários.

Normaliza os IDs solicitados, rejeita cenários desconhecidos e instancia
a campanha base. Não executa trajetórias durante a inicialização.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- `ValueError(f'Unsupported scenario_id(s): {unknown}')`

**Colaboradores chamados diretamente**

- `tuple`
- `dict.fromkeys`
- `str(item).lower`
- `str`
- `ValueError`
- `MonteCarloCampaign`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `StochasticScenarioCampaign.path`

[Implementação: source/antares_fd/simulation/uq_campaign.py:420](../../source/antares_fd/simulation/uq_campaign.py#L420)

```python
StochasticScenarioCampaign.path(self) -> Path
```

Retorne o diretório raiz da campanha base.

A propriedade encaminha base.root_path, permitindo que manifestos
e comparações pareadas compartilhem a mesma raiz.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `self.base.root_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- Nenhuma ocorrência explícita no corpo local.

### `StochasticScenarioCampaign.samples_path`

[Implementação: source/antares_fd/simulation/uq_campaign.py:429](../../source/antares_fd/simulation/uq_campaign.py#L429)

```python
StochasticScenarioCampaign.samples_path(self) -> Path
```

Retorne o caminho da população compartilhada de amostras.

Encaminha a referência da campanha pai para que os cenários usem
os mesmos case_id e sementes.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `self.base.samples_path`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- Nenhuma ocorrência explícita no corpo local.

### `StochasticScenarioCampaign.target_samples`

[Implementação: source/antares_fd/simulation/uq_campaign.py:438](../../source/antares_fd/simulation/uq_campaign.py#L438)

```python
StochasticScenarioCampaign.target_samples(self) -> int
```

Consulte a meta de casos da campanha pai.

Retorna a propriedade correspondente sem manter uma segunda configuração
que possa divergir entre cenários.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `self.base.target_samples`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- Nenhuma ocorrência explícita no corpo local.

### `StochasticScenarioCampaign.min_samples`

[Implementação: source/antares_fd/simulation/uq_campaign.py:447](../../source/antares_fd/simulation/uq_campaign.py#L447)

```python
StochasticScenarioCampaign.min_samples(self) -> int
```

Consulte o mínimo de amostras da campanha pai.

Retorna o mesmo limite usado por todos os cenários da população pareada;
a consulta não altera o estado da campanha.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `self.base.min_samples`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- Nenhuma ocorrência explícita no corpo local.

### `StochasticScenarioCampaign.max_samples`

[Implementação: source/antares_fd/simulation/uq_campaign.py:456](../../source/antares_fd/simulation/uq_campaign.py#L456)

```python
StochasticScenarioCampaign.max_samples(self) -> int
```

Consulte o teto de amostras da campanha pai.

Retorna o limite compartilhado que restringe a execução do cenário,
sem ampliar automaticamente a população.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `self.base.max_samples`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- Nenhuma ocorrência explícita no corpo local.

### `StochasticScenarioCampaign.snapshot_config`

[Implementação: source/antares_fd/simulation/uq_campaign.py:464](../../source/antares_fd/simulation/uq_campaign.py#L464)

```python
StochasticScenarioCampaign.snapshot_config(self, project_dir: Path) -> dict[str, str]
```

Encaminhe a criação do snapshot de entradas à campanha pai.

Evita cópias conflitantes da configuração entre cenários; retorna
a referência produzida pelo método compartilhado.

**Entradas e tipos declarados**

- `project_dir: Path`

**Retornos/yields explícitos**

- `self.base.snapshot_config(project_dir)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.base.snapshot_config`

### `StochasticScenarioCampaign.scenario`

[Implementação: source/antares_fd/simulation/uq_campaign.py:472](../../source/antares_fd/simulation/uq_campaign.py#L472)

```python
StochasticScenarioCampaign.scenario(self, scenario_id: str) -> MonteCarloCampaign
```

Crie a visão MonteCarloCampaign de um cenário autorizado.

Normaliza o nome, exige associação a scenario_ids e instancia a visão
com projeto, semente, perfil, configuração e ID de campanha compartilhados.

**Entradas e tipos declarados**

- `scenario_id: str`

**Retornos/yields explícitos**

- `MonteCarloCampaign(self.project, self.root, self.master_seed, self.profile, self.campaign_id, self.config, scenario_id)`

**Exceções lançadas explicitamente**

- `ValueError(f'Scenario is not part of this campaign: {scenario_id}')`

**Colaboradores chamados diretamente**

- `str(scenario_id).lower`
- `str`
- `ValueError`
- `MonteCarloCampaign`

### `StochasticScenarioCampaign.ensure_samples`

[Implementação: source/antares_fd/simulation/uq_campaign.py:486](../../source/antares_fd/simulation/uq_campaign.py#L486)

```python
StochasticScenarioCampaign.ensure_samples(self, registry_path: Path | None, ensemble_size: int=0) -> pd.DataFrame
```

Generate the complete shared sample table exactly once.

**Entradas e tipos declarados**

- `registry_path: Path | None`
- `ensemble_size: int`

**Retornos/yields explícitos**

- `self.base.make_samples(registry_path, self.base.max_samples, ensemble_size)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.base.make_samples`

### `StochasticScenarioCampaign.write_manifest`

[Implementação: source/antares_fd/simulation/uq_campaign.py:490](../../source/antares_fd/simulation/uq_campaign.py#L490)

```python
StochasticScenarioCampaign.write_manifest(self, status: str='CREATED', **extra: Any) -> Path
```

Grave o estado terminal ou intermediário de um cenário.

Reúne ID, parâmetros compartilhados e detalhes de execução e publica
o manifesto no diretório do cenário com escrita atômica.

**Entradas e tipos declarados**

- `status: str`
- `**extra: argumentos nomeados adicionais`

**Retornos/yields explícitos**

- `write_json_atomic(payload, manifest_path)`

**Exceções lançadas explicitamente**

- `ValueError(f'Campaign manifest cannot be a symlink: {manifest_path}')`

**Colaboradores chamados diretamente**

- `_results_artifact_path`
- `manifest_path.is_symlink`
- `ValueError`
- `manifest_path.exists`
- `json.loads`
- `manifest_path.read_text`
- `list`
- `str`
- `self.samples_path.relative_to`
- `self.samples_path.exists`
- `int`
- `len`
- `pd.read_parquet`
- `platform.platform`
- `_git_metadata`
- `Path`
- `datetime.now(timezone.utc).isoformat`
- `datetime.now`
- `previous.get`
- `payload.update`
- `write_json_atomic`

### `StochasticScenarioCampaign.scenario_manifests`

[Implementação: source/antares_fd/simulation/uq_campaign.py:528](../../source/antares_fd/simulation/uq_campaign.py#L528)

```python
StochasticScenarioCampaign.scenario_manifests(self) -> dict[str, dict[str, Any]]
```

Liste os manifestos de cenário disponíveis na campanha pai.

Delega a consulta compartilhada e retorna os documentos salvos,
sem reexecutar os cenários.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `result`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.scenario`
- `manifest.exists`
- `json.loads`
- `manifest.read_text`

### `StochasticScenarioCampaign.finalize_paired_comparison`

[Implementação: source/antares_fd/simulation/uq_campaign.py:547](../../source/antares_fd/simulation/uq_campaign.py#L547)

```python
StochasticScenarioCampaign.finalize_paired_comparison(self) -> dict[str, Any]
```

Persist paired deltas and a compact comparison summary.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `summary`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.scenario`
- `output.exists`
- `pd.read_parquet`
- `comparison_dir.mkdir`
- `paired_scenario_comparison`
- `write_parquet_atomic`
- `paired_comparison_statistics`
- `paired.get`
- `pd.Series`
- `comparison_status.eq('PAIRED_COMMON_RANDOM_NUMBERS').any`
- `comparison_status.eq`
- `comparison_status.eq('PAIRED_COMMON_RANDOM_NUMBERS_PARTIAL').any`
- `list`
- `status.startswith`
- `int`
- `len`
- `write_json_atomic`

## `source/antares_fd/simulation/uq_pipeline.py`

Finalize compact campaign artifacts from RocketPy's scalar logs.

### `_read_json_lines`

[Implementação: source/antares_fd/simulation/uq_pipeline.py:35](../../source/antares_fd/simulation/uq_pipeline.py#L35)

```python
_read_json_lines(path: Path) -> list[dict[str, Any]]
```

Leia registros JSONL usando o contrato estrito do armazenamento comum.

Retorna lista de objetos; linhas inválidas e números não finitos geram
erro com posição, evitando descartar casos silenciosamente.

**Entradas e tipos declarados**

- `path: Path`

**Retornos/yields explícitos**

- `read_jsonl_objects(path, missing_ok=True)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `read_jsonl_objects`

### `_sample_case_ids`

[Implementação: source/antares_fd/simulation/uq_pipeline.py:44](../../source/antares_fd/simulation/uq_pipeline.py#L44)

```python
_sample_case_ids(samples: pd.DataFrame | None) -> set[int] | None
```

Extraia e valide os identificadores da população amostrada.

Exige case_id canônico, inteiro não negativo e sem duplicatas.
Retorna o conjunto autorizado para vincular entradas e saídas.

**Entradas e tipos declarados**

- `samples: pd.DataFrame | None`

**Retornos/yields explícitos**

- `None`
- `case_ids`

**Exceções lançadas explicitamente**

- `ValueError('sample table must contain unique case IDs')`

**Colaboradores chamados diretamente**

- `canonicalize_case_records`
- `samples[['case_id']].to_dict`
- `len`
- `ValueError`

### `_uncertainty_frame`

[Implementação: source/antares_fd/simulation/uq_pipeline.py:61](../../source/antares_fd/simulation/uq_pipeline.py#L61)

```python
_uncertainty_frame(registry_path: Path) -> pd.DataFrame
```

Serialize the configured uncertainty registry for report traceability.

**Entradas e tipos declarados**

- `registry_path: Path`

**Retornos/yields explícitos**

- `pd.DataFrame()`
- `pd.DataFrame(rows)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `registry_path.exists`
- `pd.DataFrame`
- `UncertaintyRegistry`
- `registry.registry.values`
- `rows.append`
- `json.dumps`
- `definition.params.get`
- `provenance.get`

### `_output_frame`

[Implementação: source/antares_fd/simulation/uq_pipeline.py:85](../../source/antares_fd/simulation/uq_pipeline.py#L85)

```python
_output_frame(records: list[dict[str, Any]], samples: pd.DataFrame | None, scenario_id: str | None=None) -> pd.DataFrame
```

Converta registros RocketPy em uma tabela canônica por caso.

Normaliza IDs e métricas, valida a população permitida e usa elevação
realizada por caso para converter apogeu ASL em AGL. Preserva velocidade
vertical com sinal e calcula magnitude de impacto separadamente.
Retorna DataFrame; duplicatas ou valores físicos inválidos geram erro.

**Entradas e tipos declarados**

- `records: list[dict[str, Any]]`
- `samples: pd.DataFrame | None`
- `scenario_id: str | None`

**Retornos/yields explícitos**

- `pd.DataFrame()`
- `frame`

**Exceções lançadas explicitamente**

- `ValueError(f'Monte Carlo output row {row_number} metric {column!r} is not numeric')`
- `ValueError(f'Monte Carlo output row {row_number} metric {column!r} is non-finite')`
- `ValueError('Monte Carlo AGL apogee requires finite per-case elevation')`

**Colaboradores chamados diretamente**

- `pd.DataFrame`
- `_sample_case_ids`
- `canonicalize_case_records`
- `enumerate`
- `record.items`
- `isinstance`
- `ValueError`
- `np.isfinite`
- `pd.to_numeric(frame['case_id'], errors='raise').astype`
- `pd.to_numeric`
- `aliases.items`
- `frame['apogee_asl'].notna`
- `valid_apogee.any`
- `pd.to_numeric(samples.set_index('case_id')['rocketpy_elevation'], errors='coerce').reindex(frame['case_id'].tolist()).reset_index`
- `pd.to_numeric(samples.set_index('case_id')['rocketpy_elevation'], errors='coerce').reindex`
- `samples.set_index`
- `frame['case_id'].tolist`
- `pd.to_numeric(samples.set_index('case_id')['site_elevation'], errors='coerce').reindex(frame['case_id'].tolist()).reset_index`
- `pd.to_numeric(samples.set_index('case_id')['site_elevation'], errors='coerce').reindex`
- `np.isfinite(elevation.loc[valid_apogee].to_numpy(dtype=float)).all`
- `elevation.loc[valid_apogee].to_numpy`
- `np.hypot`
- `frame['touchdown_velocity_signed'].abs`
- `frame['case_id'].map`
- `str`

### `_input_frame`

[Implementação: source/antares_fd/simulation/uq_pipeline.py:179](../../source/antares_fd/simulation/uq_pipeline.py#L179)

```python
_input_frame(samples: pd.DataFrame, records: list[dict[str, Any]] | None) -> pd.DataFrame
```

Combine declared samples with the exact scalar values RocketPy used.

**Entradas e tipos declarados**

- `samples: pd.DataFrame`
- `records: list[dict[str, Any]] | None`

**Retornos/yields explícitos**

- `samples`
- `actual`
- `result.reset_index()`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `_sample_case_ids`
- `normalized_records.append`
- `isinstance`
- `json.dumps`
- `record.items`
- `canonicalize_case_records`
- `pd.DataFrame`
- `pd.to_numeric(actual['case_id'], errors='raise').astype`
- `pd.to_numeric`
- `actual.rename`
- `samples.set_index`
- `actual.set_index`
- `pd.Series(actual[column], index=actual.index, dtype=actual[column].dtype).reindex`
- `pd.Series`
- `result.index.intersection`
- `actual.loc[common, column].to_numpy`
- `result.reset_index`

### `_requirements`

[Implementação: source/antares_fd/simulation/uq_pipeline.py:214](../../source/antares_fd/simulation/uq_pipeline.py#L214)

```python
_requirements(project_dir: Path) -> dict[str, dict[str, Any]]
```

Carregue os requisitos probabilísticos declarados para a campanha.

Lê a configuração aplicável e retorna o mapeamento de critérios
que será passado à análise de conformidade, sem criar limites novos.

**Entradas e tipos declarados**

- `project_dir: Path`

**Retornos/yields explícitos**

- `{}`
- `data.get('requirements', {})`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `Path`
- `path.exists`
- `yaml.safe_load`
- `path.read_text`
- `data.get`

### `_representative_cases`

[Implementação: source/antares_fd/simulation/uq_pipeline.py:227](../../source/antares_fd/simulation/uq_pipeline.py#L227)

```python
_representative_cases(frame: pd.DataFrame) -> pd.DataFrame
```

Selecione casos representativos a partir das saídas existentes.

Usa métricas e percentis para registrar IDs de referência e extremos.
Retorna metadados de seleção; não cria trajetórias sintéticas.

**Entradas e tipos declarados**

- `frame: pd.DataFrame`

**Retornos/yields explícitos**

- `pd.DataFrame()`
- `pd.DataFrame(selections).drop_duplicates(subset=['selection', 'case_id'])`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `pd.DataFrame`
- `metrics.items`
- `pd.to_numeric`
- `values.notna().any`
- `values.notna`
- `values.idxmin`
- `values.idxmax`
- `selections.append`
- `int`
- `float`
- `np.percentile`
- `values.dropna`
- `(values - target).abs().idxmin`
- `(values - target).abs`
- `pd.DataFrame(selections).drop_duplicates`

### `finalize_campaign_analysis`

[Implementação: source/antares_fd/simulation/uq_pipeline.py:259](../../source/antares_fd/simulation/uq_pipeline.py#L259)

```python
finalize_campaign_analysis(campaign: MonteCarloCampaign, project_dir: Path, output_records: list[dict[str, Any]] | None=None, input_records: list[dict[str, Any]] | None=None, failure_records: list[dict[str, Any]] | None=None) -> dict[str, Any]
```

Build all cheap statistical artifacts from saved scalar data.

**Entradas e tipos declarados**

- `campaign: MonteCarloCampaign`
- `project_dir: Path`
- `output_records: list[dict[str, Any]] | None`
- `input_records: list[dict[str, Any]] | None`
- `failure_records: list[dict[str, Any]] | None`

**Retornos/yields explícitos**

- `summary`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `campaign.samples_path.exists`
- `pd.read_parquet`
- `pd.DataFrame`
- `_read_json_lines`
- `_input_frame`
- `write_parquet_atomic`
- `_uncertainty_frame`
- `_output_frame`
- `getattr`
- `list`
- `campaign.batches_path.glob`
- `campaign.write_batch`
- `outputs.select_dtypes`
- `distribution_statistics`
- `landing_dispersion`
- `(landing.get('ellipses') or {}).items`
- `landing.get`
- `ellipse_rows.append`
- `float`
- `ellipse.get`
- `{'landing_east', 'landing_north'}.issubset`
- `empirical_landing_surface`
- `min`
- `max`
- `int`
- `np.sqrt`
- `len`
- `write_json_atomic`
- `empirical_containment_levels`
- `ecdf`
- `curve.insert`
- `ecdf_rows.append`
- `pd.concat`
- `pd.to_numeric(outputs[metric], errors='coerce').notna().any`
- `pd.to_numeric(outputs[metric], errors='coerce').notna`
- `pd.to_numeric`
- `applicability_rows.append`
- `settings.get`
- `isinstance`
- `configured.get`
- `convergence_table`
- `sensitivity_stability_table`
- `pd.to_numeric(outputs[metric], errors='coerce').dropna`
- `quantile_confidence_interval`
- `np.percentile`
- `confidence_rows.append`
- `spearman_sensitivity`
- `conditional_tail_analysis`
- `any`
- `compliance_analysis`
- `_requirements`
- `_representative_cases`
- `bool`
- `(convergence['status'] == 'CONVERGED').all`
- `str`
- `campaign.settings.get`
- `magi_sampling_method.startswith`
- `warnings.append`
- `samples[column].isna().all`
- `samples[column].isna`
- `policy.get`
- `(stability['status'] == 'CONVERGED').all`
- `pd.notna`
- `_write_plot_artifacts`
- `campaign.samples_path.stat`
- `(campaign.path / 'outputs.parquet').stat`
- `directory_size`
- `time.perf_counter`
- `np.finfo`
- `campaign.write_manifest`

### `_write_plot_artifacts`

[Implementação: source/antares_fd/simulation/uq_pipeline.py:451](../../source/antares_fd/simulation/uq_pipeline.py#L451)

```python
_write_plot_artifacts(directory: Path, outputs: pd.DataFrame, convergence: pd.DataFrame, sensitivity: pd.DataFrame, compliance: pd.DataFrame) -> None
```

Create a small, fixed set of review plots from canonical tables.

**Entradas e tipos declarados**

- `directory: Path`
- `outputs: pd.DataFrame`
- `convergence: pd.DataFrame`
- `sensitivity: pd.DataFrame`
- `compliance: pd.DataFrame`

**Retornos/yields explícitos**

- `None`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `directory.mkdir`
- `plt.subplots`
- `pd.to_numeric(outputs['apogee_agl'], errors='coerce').dropna`
- `pd.to_numeric`
- `axis.hist`
- `axis.axvline`
- `values.quantile`
- `axis.set`
- `axis.legend`
- `fig.tight_layout`
- `save_figure`
- `plt.close`
- `{'landing_east', 'landing_north'}.issubset`
- `axis.scatter`
- `axis.axis`
- `empirical_landing_surface`
- `min`
- `max`
- `int`
- `np.sqrt`
- `len`
- `surface.get`
- `np.asarray`
- `axis.pcolormesh`
- `fig.colorbar`
- `plt.figure`
- `figure.add_subplot`
- `np.meshgrid`
- `axis.plot_surface`
- `figure.tight_layout`
- `zip`
- `axes.ravel`
- `pd.to_numeric(outputs[metric], errors='coerce').dropna`
- `axis.set_title`
- `metric.replace('_', ' ').title`
- `metric.replace`
- `axis.grid`
- `ecdf`
- `axis.step`
- `pd.to_numeric(outputs['touchdown_velocity'], errors='coerce').dropna`
- `axis.plot`
- `sensitivity[sensitivity['output'] == 'apogee_agl'].sort_values`
- `axis.barh`
- `axis.bar`
- `axis.set_ylim`
- `axis.set_ylabel`
- `axis.tick_params`
- `axis.axhline`
- `compliance.iterrows`

## `source/antares_fd/simulation/uq_storage.py`

Small, atomic storage primitives used by Monte Carlo campaigns.

The campaign keeps metadata in JSON and tabular data in compressed Parquet.
Writes are completed in the destination directory and committed with an atomic
rename, so an interrupted process cannot leave a file that looks complete.

### `read_parquet_files`

[Implementação: source/antares_fd/simulation/uq_storage.py:19](../../source/antares_fd/simulation/uq_storage.py#L19)

```python
read_parquet_files(directory: Path, pattern: str='batch_*.parquet') -> pd.DataFrame
```

Read campaign batches without requiring one file per simulation case.

**Entradas e tipos declarados**

- `directory: Path`
- `pattern: str`

**Retornos/yields explícitos**

- `pd.DataFrame()`
- `pd.concat((pd.read_parquet(file) for file in files), ignore_index=True)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `sorted`
- `Path(directory).glob`
- `Path`
- `pd.DataFrame`
- `pd.concat`
- `pd.read_parquet`

### `directory_size`

[Implementação: source/antares_fd/simulation/uq_storage.py:27](../../source/antares_fd/simulation/uq_storage.py#L27)

```python
directory_size(path: Path) -> int
```

Return the number of bytes below *path* without loading file contents.

**Entradas e tipos declarados**

- `path: Path`

**Retornos/yields explícitos**

- `0`
- `sum((item.stat().st_size for item in root.rglob('*') if item.is_file()))`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `Path`
- `root.exists`
- `sum`
- `item.stat`
- `root.rglob`
- `item.is_file`

## `source/antares_fd/storage.py`

Atomic JSON and Parquet writers shared by simulation and telemetry.

### `_validate_finite_json_values`

[Implementação: source/antares_fd/storage.py:15](../../source/antares_fd/storage.py#L15)

```python
_validate_finite_json_values(value: Any) -> None
```

Rejeite números não finitos em estruturas JSON aninhadas.

Percorre objetos e listas recursivamente; float NaN ou infinito gera
ValueError. Não transforma valores inválidos em zero ou texto.

**Entradas e tipos declarados**

- `value: Any`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- `ValueError('non-finite numeric value')`

**Colaboradores chamados diretamente**

- `isinstance`
- `math.isfinite`
- `ValueError`
- `float`
- `value.values`
- `_validate_finite_json_values`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `iter_jsonl_objects`

[Implementação: source/antares_fd/storage.py:38](../../source/antares_fd/storage.py#L38)

```python
iter_jsonl_objects(path: Path, *, missing_ok: bool=False) -> Iterator[dict[str, Any]]
```

Yield ordered JSONL objects and fail on malformed or non-finite records.

Blank lines are ignored. Every nonblank line must contain one JSON object;
numeric values must be representable as finite Python floats. Errors
include the source path and physical line number so partial analyses cannot
silently omit a damaged record.

**Entradas e tipos declarados**

- `path: Path`
- `missing_ok: bool`

**Retornos/yields explícitos**

- `None`
- `record`

**Exceções lançadas explicitamente**

- `FileNotFoundError(path)`
- `ValueError(f'{path}:{line_number}: invalid JSON')`
- `ValueError(f'{path}:{line_number}: expected a JSON object')`
- `ValueError(f'{path}:{line_number}: {exc}')`

**Colaboradores chamados diretamente**

- `Path`
- `path.exists`
- `FileNotFoundError`
- `path.open`
- `enumerate`
- `line.strip`
- `json.loads`
- `ValueError`
- `isinstance`
- `_validate_finite_json_values`

### `read_jsonl_objects`

[Implementação: source/antares_fd/storage.py:69](../../source/antares_fd/storage.py#L69)

```python
read_jsonl_objects(path: Path, *, missing_ok: bool=False) -> list[dict[str, Any]]
```

Read every JSONL record using the strict shared validation contract.

**Entradas e tipos declarados**

- `path: Path`
- `missing_ok: bool`

**Retornos/yields explícitos**

- `list(iter_jsonl_objects(path, missing_ok=missing_ok))`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `list`
- `iter_jsonl_objects`

### `_temporary_path`

[Implementação: source/antares_fd/storage.py:74](../../source/antares_fd/storage.py#L74)

```python
_temporary_path(path: Path) -> Path
```

Crie um arquivo temporário exclusivo ao lado do destino.

Garante o diretório pai, usa mkstemp e fecha o descritor imediatamente.
Retorna Path no mesmo sistema de arquivos para permitir os.replace atômico.

**Entradas e tipos declarados**

- `path: Path`

**Retornos/yields explícitos**

- `Path(name)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `path.parent.mkdir`
- `tempfile.mkstemp`
- `os.close`
- `Path`

### `write_parquet_atomic`

[Implementação: source/antares_fd/storage.py:86](../../source/antares_fd/storage.py#L86)

```python
write_parquet_atomic(frame: pd.DataFrame, path: Path, compression: str='zstd') -> Path
```

Write *frame* to Parquet and atomically replace *path*.

**Entradas e tipos declarados**

- `frame: pd.DataFrame`
- `path: Path`
- `compression: str`

**Retornos/yields explícitos**

- `path`

**Exceções lançadas explicitamente**

- `raise (propaga a exceção ativa)`

**Colaboradores chamados diretamente**

- `Path`
- `_temporary_path`
- `frame.to_parquet`
- `os.replace`
- `temporary.unlink`

### `write_json_atomic`

[Implementação: source/antares_fd/storage.py:99](../../source/antares_fd/storage.py#L99)

```python
write_json_atomic(value: Any, path: Path) -> Path
```

Write a small JSON document with an atomic commit.

**Entradas e tipos declarados**

- `value: Any`
- `path: Path`

**Retornos/yields explícitos**

- `path`

**Exceções lançadas explicitamente**

- `raise (propaga a exceção ativa)`

**Colaboradores chamados diretamente**

- `Path`
- `_temporary_path`
- `temporary.open`
- `json.dump`
- `stream.write`
- `stream.flush`
- `os.fsync`
- `stream.fileno`
- `os.replace`
- `temporary.unlink`

## `source/antares_fd/telemetry/__init__.py`

Non-destructive telemetry ingestion and data-quality auditing.

Módulo declarativo, ponto de entrada sem funções ou exportação de interfaces; não contém funções próprias.

## `source/antares_fd/telemetry/artifacts.py`

Dataset configuration, artifact writing, verification, and human report.

### `_sha256`

[Implementação: source/antares_fd/telemetry/artifacts.py:42](../../source/antares_fd/telemetry/artifacts.py#L42)

```python
_sha256(path: Path) -> str
```

Calcule SHA-256 de um artefato de telemetria sem modificá-lo.

Lê blocos binários e retorna o digest hexadecimal para verificação
de integridade e vinculação ao registro bruto.

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

### `_load_metadata`

[Implementação: source/antares_fd/telemetry/artifacts.py:55](../../source/antares_fd/telemetry/artifacts.py#L55)

```python
_load_metadata(metadata_path: Path) -> dict[str, Any]
```

Carregue e valide os metadados YAML da auditoria de telemetria.

Lê metadata_path, exige o contrato esperado e retorna o mapeamento.
Campos de calibração ausentes não são preenchidos com estimativas.

**Entradas e tipos declarados**

- `metadata_path: Path`

**Retornos/yields explícitos**

- `metadata`

**Exceções lançadas explicitamente**

- `ValueError(f'Cannot read telemetry metadata {metadata_path}: {exc}')`
- `ValueError(f'Telemetry metadata must be a YAML mapping: {metadata_path}')`
- `ValueError('Telemetry metadata must declare raw_data.path')`
- `ValueError(f'Telemetry metadata is missing required fields: {missing_top}')`
- `ValueError('Telemetry metadata channels must be a non-empty list')`
- `ValueError(f'Telemetry channel metadata at index {index} must be a mapping')`
- `ValueError(f'Telemetry channel metadata at index {index} is missing fields: {missing}')`
- `ValueError(f"Unsupported data_origin for {entry.get('raw_channel_name')}: {entry['data_origin']}")`
- `ValueError(f"Unsupported unit_status for {entry.get('raw_channel_name')}: {entry['unit_status']}")`
- `ValueError(f"Channel {entry['raw_channel_name']} has no unit but is not marked UNKNOWN")`
- `ValueError(f"Channel {entry['raw_channel_name']} declares a unit while unit_status is UNKNOWN")`
- `ValueError('Telemetry channel raw and canonical names must be unique')`

**Colaboradores chamados diretamente**

- `metadata_path.open`
- `yaml.safe_load`
- `ValueError`
- `isinstance`
- `metadata.get`
- `raw.get`
- `enumerate`
- `entry.get`
- `len`
- `set`

### `_write_text_atomic`

[Implementação: source/antares_fd/telemetry/artifacts.py:115](../../source/antares_fd/telemetry/artifacts.py#L115)

```python
_write_text_atomic(text: str, path: Path) -> None
```

Publique um documento de texto sem expor gravação parcial.

Escreve UTF-8 em arquivo temporário no diretório de destino e usa
substituição atômica. Em falha, remove o temporário e propaga o erro.

**Entradas e tipos declarados**

- `text: str`
- `path: Path`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- `raise (propaga a exceção ativa)`

**Colaboradores chamados diretamente**

- `path.parent.mkdir`
- `tempfile.mkstemp`
- `Path`
- `os.fdopen`
- `stream.write`
- `stream.flush`
- `os.fsync`
- `stream.fileno`
- `os.replace`
- `temporary.unlink`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `_calibration_manifest`

[Implementação: source/antares_fd/telemetry/artifacts.py:135](../../source/antares_fd/telemetry/artifacts.py#L135)

```python
_calibration_manifest(metadata: dict[str, Any], *, source_sha256: str, metadata_sha256: str) -> dict[str, Any]
```

Record the calibration knowledge boundary without assuming constants.

**Entradas e tipos declarados**

- `metadata: dict[str, Any]`
- `source_sha256: str`
- `metadata_sha256: str`

**Retornos/yields explícitos**

- `{'schema_version': '1.0', 'dataset_id': metadata['dataset_id'], 'source_sha256': source_sha256, 'metadata_sha256': metadata_sha256, 'status': 'BLOCKED_BY_MISSING_METADATA', 'unknown_fields_policy': 'UNKNOWN means no sensor-specific evidence is declared; no calibration is applied', 'sensors': list(sensors.values())}`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `sensors.setdefault`
- `sensor['channels'].append`
- `list`
- `sensors.values`

### `_markdown_table`

[Implementação: source/antares_fd/telemetry/artifacts.py:180](../../source/antares_fd/telemetry/artifacts.py#L180)

```python
_markdown_table(headers: list[str], rows: list[list[Any]]) -> str
```

Formate cabeçalhos e linhas em uma tabela Markdown.

Converte as células com o formatador local e inclui a linha separadora.
Retorna texto para o relatório sem alterar os dados canônicos.

**Entradas e tipos declarados**

- `headers: list[str]`
- `rows: list[list[Any]]`

**Retornos/yields explícitos**

- `'\n'.join(output)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `' | '.join`
- `output.extend`
- `cell`
- `'\n'.join`

### `_markdown_table.cell`

[Implementação: source/antares_fd/telemetry/artifacts.py:186](../../source/antares_fd/telemetry/artifacts.py#L186)

```python
_markdown_table.cell(value: Any) -> str
```

Escape uma célula para não quebrar a estrutura Markdown.

Converte value em texto e neutraliza separadores e quebras de linha.
O retorno é usado somente na apresentação do relatório.

**Entradas e tipos declarados**

- `value: Any`

**Retornos/yields explícitos**

- `'—'`
- `str(value).replace('|', '\\|').replace('\n', ' ')`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `isinstance`
- `pd.isna`
- `str(value).replace('|', '\\|').replace`
- `str(value).replace`
- `str`

### `_render_report`

[Implementação: source/antares_fd/telemetry/artifacts.py:201](../../source/antares_fd/telemetry/artifacts.py#L201)

```python
_render_report(output_dir: Path) -> str
```

Render Markdown only from the canonical JSON and Parquet artifacts.

**Entradas e tipos declarados**

- `output_dir: Path`

**Retornos/yields explícitos**

- `'\n'.join(lines)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `json.loads`
- `(output_dir / 'telemetry_inventory.json').read_text`
- `pd.read_parquet`
- `gps.get`
- `stats.to_dict`
- `flags.groupby('quality_flag', dropna=False).size().sort_values(ascending=False).to_dict`
- `flags.groupby('quality_flag', dropna=False).size().sort_values`
- `flags.groupby('quality_flag', dropna=False).size`
- `flags.groupby`
- `timebase['interval_class'].value_counts().to_dict`
- `timebase['interval_class'].value_counts`
- `inventory.get`
- `sorted`
- `flag_counts.items`
- `issue_counts.items`
- `', '.join`
- `len`
- `_markdown_table`
- `json.dumps`
- `'\n'.join`

### `verify_artifact_set`

[Implementação: source/antares_fd/telemetry/artifacts.py:358](../../source/antares_fd/telemetry/artifacts.py#L358)

```python
verify_artifact_set(output_dir: Path) -> dict[str, Any]
```

Verify manifest checksums, Parquet readability, columns, and row counts.

**Entradas e tipos declarados**

- `output_dir: Path`

**Retornos/yields explícitos**

- `manifest`

**Exceções lançadas explicitamente**

- `TelemetryArtifactError(f'Telemetry artifact manifest is missing: {manifest_path}')`
- `TelemetryArtifactError(f'Telemetry artifact manifest is unreadable: {exc}')`
- `TelemetryArtifactError(f'Declared telemetry artifact is missing: {path}')`
- `TelemetryArtifactError(f'Checksum mismatch for telemetry artifact {path.name}')`
- `TelemetryArtifactError(f'Size mismatch for telemetry artifact {path.name}')`
- `TelemetryArtifactError(f'Corrupt or unreadable Parquet artifact {path.name}: {exc}')`
- `TelemetryArtifactError(f'Schema or row-count mismatch for telemetry artifact {path.name}')`
- `TelemetryArtifactError(f'Corrupt JSON artifact {path.name}: {exc}')`
- `TelemetryArtifactError('Telemetry manifest artifact list is incomplete or unexpected')`

**Colaboradores chamados diretamente**

- `Path`
- `manifest_path.is_file`
- `TelemetryArtifactError`
- `json.loads`
- `manifest_path.read_text`
- `manifest.get('artifacts', {}).items`
- `manifest.get`
- `path.is_file`
- `_sha256`
- `path.stat`
- `pd.read_parquet`
- `list`
- `len`
- `path.read_text`
- `set`

### `audit_project`

[Implementação: source/antares_fd/telemetry/artifacts.py:396](../../source/antares_fd/telemetry/artifacts.py#L396)

```python
audit_project(project_dir: Path, *, repo_root: Path, metadata_path: Path | None=None, source_path: Path | None=None, output_dir: Path | None=None) -> Path
```

Run a configured audit and atomically publish its complete artifact set.

**Entradas e tipos declarados**

- `project_dir: Path`
- `repo_root: Path`
- `metadata_path: Path | None`
- `source_path: Path | None`
- `output_dir: Path | None`

**Retornos/yields explícitos**

- `output_dir`

**Exceções lançadas explicitamente**

- `TelemetryArtifactError('Telemetry metadata changed while being read')`
- `FileNotFoundError(f'Declared telemetry source is unavailable: {source}')`
- `FileNotFoundError(f'Required related telemetry file is unavailable: {related_path}')`
- `ValueError("Telemetry audit output must be a new directory beneath the repository's ignored results area")`
- `FileExistsError(f'Refusing to overwrite existing telemetry audit output: {output_dir}')`
- `ValueError('Telemetry audit output directory must not contain the raw source file')`
- `ValueError('Telemetry audit artifact path would overwrite the raw source file')`
- `TelemetryArtifactError(f'Generated Parquet artifact failed read-back: {filename}: {exc}')`
- `TelemetryArtifactError('Raw telemetry checksum changed before artifact publication')`
- `TelemetryArtifactError('Telemetry metadata changed during audit')`
- `TelemetryArtifactError(f"Related source artifact changed during audit: {file_record['path']}")`
- `raise (propaga a exceção ativa)`
- `TelemetryArtifactError('Raw telemetry checksum changed during audit publication')`

**Colaboradores chamados diretamente**

- `Path(project_dir).resolve`
- `Path`
- `Path(repo_root).resolve`
- `Path(metadata_path or project_dir / 'telemetry' / 'metadata' / 'dataset.yaml').resolve`
- `_sha256`
- `_load_metadata`
- `TelemetryArtifactError`
- `Path(source_path or repo_root / metadata['raw_data']['path']).resolve`
- `source.is_file`
- `FileNotFoundError`
- `source.is_relative_to`
- `source.relative_to(repo_root).as_posix`
- `source.relative_to`
- `str`
- `parse_telemetry_log`
- `metadata.get('raw_data', {}).get`
- `metadata.get`
- `tuple`
- `audit_dataset`
- `float`
- `sections.get`
- `sections.items`
- `raw_data.get`
- `source.suffix.lstrip('.').lower`
- `source.suffix.lstrip`
- `len`
- `list`
- `related_path.is_absolute`
- `(repo_root / related_path).resolve`
- `related_path.is_file`
- `declared.get`
- `related_path.is_relative_to`
- `related_path.relative_to(repo_root).as_posix`
- `related_path.relative_to`
- `related_path.suffix.lstrip('.').lower`
- `related_path.suffix.lstrip`
- `related_path.stat`
- `related_files.append`
- `inventory['files'].append`
- `datetime.now(timezone.utc).strftime`
- `datetime.now`
- `output_dir.is_absolute`
- `(repo_root / output_dir).resolve`
- `Path(output_dir).resolve`
- `results_root.is_symlink`
- `results_root.resolve`
- `output_dir.is_relative_to`
- `ValueError`
- `output_dir.exists`
- `FileExistsError`
- `(output_dir / name).resolve`
- `output_dir.parent.mkdir`
- `tempfile.mkdtemp`
- `write_json_atomic`
- `_calibration_manifest`
- `write_parquet_atomic`
- `pd.read_parquet`
- `Path(file_record['path']).is_absolute`
- `_write_text_atomic`
- `_render_report`
- `artifact_path.stat`
- `importlib.metadata.version`
- `datetime.now(timezone.utc).isoformat`
- `metadata_path.is_relative_to`
- `metadata_path.relative_to(repo_root).as_posix`
- `metadata_path.relative_to`
- `platform.python_version`
- `get_git_provenance`
- `verify_artifact_set`
- `os.replace`
- `shutil.rmtree`

## `source/antares_fd/telemetry/audit.py`

Provenance-preserving timebase and channel-quality diagnostics.

### `_flag`

[Implementação: source/antares_fd/telemetry/audit.py:81](../../source/antares_fd/telemetry/audit.py#L81)

```python
_flag(rows: list[dict[str, Any]], dataset_id: str, quality_flag: str, trigger: str, *, channel_name: str | None=None, severity: str='WARNING', source_line_number: int | None=None, end_source_line_number: int | None=None, timestamp_value: float | None=None, details: dict[str, Any] | None=None) -> None
```

Acrescente um diagnóstico rastreável à lista de qualidade da telemetria.

Registra dataset_id, regra acionada, severidade, canal e posição da fonte.
Modifica rows; não remove nem corrige amostras do registro bruto.

**Entradas e tipos declarados**

- `rows: list[dict[str, Any]]`
- `dataset_id: str`
- `quality_flag: str`
- `trigger: str`
- `channel_name: str | None`
- `severity: str`
- `source_line_number: int | None`
- `end_source_line_number: int | None`
- `timestamp_value: float | None`
- `details: dict[str, Any] | None`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `rows.append`
- `json.dumps`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `_finite_values`

[Implementação: source/antares_fd/telemetry/audit.py:114](../../source/antares_fd/telemetry/audit.py#L114)

```python
_finite_values(parsed: ParsedTelemetry, channel: str) -> list[tuple[dict[str, Any], dict[str, Any]]]
```

Extraia os valores numéricos finitos de um canal analisado.

Percorre ParsedTelemetry e retorna os escalares válidos para estatística;
os registros originais e as ausências continuam preservados no inventário.

**Entradas e tipos declarados**

- `parsed: ParsedTelemetry`
- `channel: str`

**Retornos/yields explícitos**

- `[(record, record['values'][channel]) for record in parsed.records if record['values'][channel]['value_status'] == 'VALID']`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- Nenhuma ocorrência explícita no corpo local.

### `_robust_spread`

[Implementação: source/antares_fd/telemetry/audit.py:127](../../source/antares_fd/telemetry/audit.py#L127)

```python
_robust_spread(values: list[float]) -> float | None
```

Calcule uma medida robusta da dispersão de um conjunto numérico.

Usa mediana e desvios absolutos conforme a regra interna de diagnóstico,
reduzindo a influência de extremos sem editar as amostras.

**Entradas e tipos declarados**

- `values: list[float]`

**Retornos/yields explícitos**

- `None`
- `float(1.4826 * statistics.median((abs(value - median) for value in values)))`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `statistics.median`
- `float`
- `abs`

### `_metadata_for_channel`

[Implementação: source/antares_fd/telemetry/audit.py:139](../../source/antares_fd/telemetry/audit.py#L139)

```python
_metadata_for_channel(channel: str, channels: dict[str, dict[str, Any]]) -> dict[str, Any]
```

Resolva os metadados declarados de um canal.

Consulta channels pelo nome e preserva classificações desconhecidas
quando não há descrição explícita, sem inferir calibração.

**Entradas e tipos declarados**

- `channel: str`
- `channels: dict[str, dict[str, Any]]`

**Retornos/yields explícitos**

- `channels[channel]`

**Exceções lançadas explicitamente**

- `ValueError(f'No provenance metadata declared for raw channel {channel!r}')`

**Colaboradores chamados diretamente**

- `ValueError`

### `classify_gps`

[Implementação: source/antares_fd/telemetry/audit.py:151](../../source/antares_fd/telemetry/audit.py#L151)

```python
classify_gps(channel_names: Iterable[str], records: Iterable[dict[str, Any]], *, latitude_channel: str='gps_lat_deg', longitude_channel: str='gps_lon_deg', timestamp_channel: str='time_ms', timestamp_unit: str | None='ms') -> dict[str, Any]
```

Classify in-range coordinate pairs; no GPS fix quality is inferred.

**Entradas e tipos declarados**

- `channel_names: Iterable[str]`
- `records: Iterable[dict[str, Any]]`
- `latitude_channel: str`
- `longitude_channel: str`
- `timestamp_channel: str`
- `timestamp_unit: str | None`

**Retornos/yields explícitos**

- `{'status': 'GPS_CHANNEL_ABSENT', 'coordinate_channels_present': sorted(names.intersection({latitude_channel, longitude_channel})), 'in_range_coordinate_pair_count': 0, 'record_count': len(record_list), 'first_in_range_coordinate_pair_timestamp': None, 'last_in_range_coordinate_pair_timestamp': None, 'first_in_range_coordinate_pair_source_line_number': None, 'last_in_range_coordinate_pair_source_line_number': None, 'timestamp_unit': timestamp_unit, 'coordinate_pair_transition_count': 0, 'coordinate_pair_intervals': [], 'fix_quality_status': 'UNKNOWN_NOT_RECORDED'}`
- `{'status': status, 'coordinate_channels_present': [latitude_channel, longitude_channel], 'in_range_coordinate_pair_count': count, 'record_count': record_count, 'first_in_range_coordinate_pair_timestamp': boundary(valid_records[0])['timestamp_value'] if valid_records else None, 'last_in_range_coordinate_pair_timestamp': boundary(valid_records[-1])['timestamp_value'] if valid_records else None, 'first_in_range_coordinate_pair_source_line_number': boundary(valid_records[0])['source_line_number'] if valid_records else None, 'last_in_range_coordinate_pair_source_line_number': boundary(valid_records[-1])['source_line_number'] if valid_records else None, 'timestamp_unit': timestamp_unit, 'coordinate_pair_transition_count': validity_transitions, 'coordinate_pair_intervals': validity_intervals, 'fix_quality_status': 'UNKNOWN_NOT_RECORDED'}`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `set`
- `list`
- `{latitude_channel, longitude_channel}.issubset`
- `sorted`
- `names.intersection`
- `len`
- `enumerate`
- `is_valid`
- `valid_records.append`
- `validity_intervals.append`
- `boundary`

### `classify_gps.is_valid`

[Implementação: source/antares_fd/telemetry/audit.py:184](../../source/antares_fd/telemetry/audit.py#L184)

```python
classify_gps.is_valid(record: dict[str, Any]) -> bool
```

Verifique somente os limites geográficos de um par latitude/longitude.

Aceita coordenadas numéricas presentes nos intervalos [-90, 90] e
[-180, 180]. Retorna bool; coordenadas no intervalo não comprovam fix GPS.

**Entradas e tipos declarados**

- `record: dict[str, Any]`

**Retornos/yields explícitos**

- `lat is not None and lon is not None and (-90 <= lat <= 90) and (-180 <= lon <= 180)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- Nenhuma ocorrência explícita no corpo local.

### `classify_gps.boundary`

[Implementação: source/antares_fd/telemetry/audit.py:194](../../source/antares_fd/telemetry/audit.py#L194)

```python
classify_gps.boundary(record: dict[str, Any]) -> dict[str, Any]
```

Extraia o limite rastreável de um intervalo de coordenadas.

Retorna índice, linha da fonte e timestamp numérico do registro recebido.
Não interpola horários nem preenche ausência do canal temporal.

**Entradas e tipos declarados**

- `record: dict[str, Any]`

**Retornos/yields explícitos**

- `{'record_index': record.get('record_index'), 'source_line_number': record.get('source_line_number'), 'timestamp_value': source_value}`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `record.get('values', {}).get`
- `record.get`
- `time_cell.get`

### `find_exact_duplicate_blocks`

[Implementação: source/antares_fd/telemetry/audit.py:250](../../source/antares_fd/telemetry/audit.py#L250)

```python
find_exact_duplicate_blocks(parsed: ParsedTelemetry) -> list[dict[str, Any]]
```

Find marked sections repeated verbatim earlier in the same raw stream.

Comparison uses every raw channel token, including missing-value spelling.
This is evidence of repetition only; the acquisition mechanism is unknown.

**Entradas e tipos declarados**

- `parsed: ParsedTelemetry`

**Retornos/yields explícitos**

- `result`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `tuple`
- `len`
- `range`
- `result.append`

### `audit_dataset`

[Implementação: source/antares_fd/telemetry/audit.py:295](../../source/antares_fd/telemetry/audit.py#L295)

```python
audit_dataset(parsed: ParsedTelemetry, *, dataset_id: str, channel_metadata: list[dict[str, Any]], raw_source_file: str, gap_factor: float=1.5) -> dict[str, Any]
```

Return canonical inventory, long-form samples, and diagnostic tables.

**Entradas e tipos declarados**

- `parsed: ParsedTelemetry`
- `dataset_id: str`
- `channel_metadata: list[dict[str, Any]]`
- `raw_source_file: str`
- `gap_factor: float`

**Retornos/yields explícitos**

- `{'inventory': inventory, 'samples': pd.DataFrame.from_records(sample_rows, columns=SAMPLE_COLUMNS), 'channel_statistics': pd.DataFrame(channel_summaries), 'timebase_diagnostics': pd.DataFrame(timebase_rows), 'segments': segments, 'sensor_quality_flags': pd.DataFrame(flags, columns=FLAG_COLUMNS)}`

**Exceções lançadas explicitamente**

- `ValueError('gap_factor must be finite and greater than 1')`
- `ValueError('Channel provenance contains duplicate raw_channel_name entries')`
- `ValueError(f'Channel provenance does not match the source header; missing={missing}, extra={extra}')`
- `ValueError('Exactly one channel must be declared as the timestamp channel')`
- `ValueError('The timebase has no positive timestamp intervals')`

**Colaboradores chamados diretamente**

- `math.isfinite`
- `ValueError`
- `len`
- `set`
- `sorted`
- `next`
- `entry.get`
- `sum`
- `bool`
- `timestamp_channel.get`
- `str(source_time_unit or '').strip().casefold().replace`
- `str(source_time_unit or '').strip().casefold`
- `str(source_time_unit or '').strip`
- `str`
- `_TIME_UNIT_TO_SECONDS.get`
- `segment_timebase`
- `segments['segment_id'].to_numpy`
- `int`
- `zip`
- `Counter`
- `min`
- `float`
- `statistics.median`
- `enumerate`
- `timebase_rows.append`
- `gap_durations.append`
- `max`
- `round`
- `counts.items`
- `_flag`
- `_metadata_for_channel`
- `_finite_values`
- `metadata.get`
- `statistics.fmean`
- `statistics.stdev`
- `_robust_spread`
- `channel_summaries.append`
- `range`
- `consecutive_differences.append`
- `abs`
- `np.quantile`
- `sample_rows.append`
- `classify_gps`
- `dict`
- `issue_counts.items`
- `list`
- `find_exact_duplicate_blocks`
- `pd.DataFrame.from_records`
- `pd.DataFrame`

## `source/antares_fd/telemetry/loader.py`

Strict, non-mutating parsing for CSV telemetry logs with text preambles.

### `ParsedTelemetry.to_wide_frame`

[Implementação: source/antares_fd/telemetry/loader.py:33](../../source/antares_fd/telemetry/loader.py#L33)

```python
ParsedTelemetry.to_wide_frame(self) -> pd.DataFrame
```

Return numeric columns for display or analysis, retaining missing values.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `pd.DataFrame([{name: record['values'][name]['numeric_value'] for name in self.channels} for record in self.records], columns=self.channels)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `pd.DataFrame`

### `_sha256`

[Implementação: source/antares_fd/telemetry/loader.py:42](../../source/antares_fd/telemetry/loader.py#L42)

```python
_sha256(path: Path) -> str
```

Calcule a identidade binária SHA-256 do registro bruto de telemetria.

Lê o arquivo em blocos sem normalizar linhas ou valores; retorna digest
hexadecimal e propaga falhas de leitura para preservar rastreabilidade.

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

### `find_csv_header_line`

[Implementação: source/antares_fd/telemetry/loader.py:55](../../source/antares_fd/telemetry/loader.py#L55)

```python
find_csv_header_line(source_path: Path, *, header_channel: str, encoding: str='utf-8', delimiter: str=',') -> int
```

Find a header whose first field exactly matches the configured channel.

**Entradas e tipos declarados**

- `source_path: Path`
- `header_channel: str`
- `encoding: str`
- `delimiter: str`

**Retornos/yields explícitos**

- `line_number`

**Exceções lançadas explicitamente**

- `TelemetryParseError(f'Cannot read telemetry source {source_path}: {exc}')`
- `TelemetryParseError(f'CSV header beginning with {header_channel!r} not found in {source_path}')`

**Colaboradores chamados diretamente**

- `Path`
- `source_path.open`
- `enumerate`
- `next`
- `csv.reader`
- `fields[0].strip`
- `TelemetryParseError`

### `parse_telemetry_log`

[Implementação: source/antares_fd/telemetry/loader.py:79](../../source/antares_fd/telemetry/loader.py#L79)

```python
parse_telemetry_log(source_path: Path, *, header_channel: str, timestamp_channel: str, expected_channels: tuple[str, ...] | list[str] | None=None, encoding: str='utf-8', delimiter: str=',', missing_tokens: tuple[str, ...]=('', 'nan', 'NaN', 'NAN'), section_markers: tuple[str, ...] | list[str]=()) -> ParsedTelemetry
```

Parse numeric CSV rows without editing the source or hiding bad rows.

Lines with the wrong width, empty lines, and non-data text remain visible in
``parse_issues`` with their one-based source line number and original text.
Numeric tokens are retained alongside their parsed floating-point form.

**Entradas e tipos declarados**

- `source_path: Path`
- `header_channel: str`
- `timestamp_channel: str`
- `expected_channels: tuple[str, ...] | list[str] | None`
- `encoding: str`
- `delimiter: str`
- `missing_tokens: tuple[str, ...]`
- `section_markers: tuple[str, ...] | list[str]`

**Retornos/yields explícitos**

- `ParsedTelemetry(source_path=source_path.resolve(), source_sha256=digest_before, source_size_bytes=size_bytes, header_line_number=header_line, channels=tuple(channels), records=tuple(records), parse_issues=tuple(issues), encoding=encoding, delimiter=delimiter)`

**Exceções lançadas explicitamente**

- `TelemetryParseError(f'Telemetry source does not exist or is not a file: {source_path}')`
- `TelemetryParseError(f'Duplicate channel names in header at line {line_number}')`
- `TelemetryParseError(f'Required timestamp channel {timestamp_channel!r} is absent from the header')`
- `TelemetryParseError(f'Telemetry header does not match the declared schema: expected {list(expected_channels)!r}, found {channels!r}')`
- `TelemetryParseError(f'Failed while parsing telemetry source {source_path}: {exc}')`
- `TelemetryParseError(f'CSV header was not read from {source_path}')`
- `TelemetryParseError(f'No correctly shaped telemetry records found in {source_path}')`
- `TelemetryParseError(f'Telemetry source changed while being read: {source_path}')`

**Colaboradores chamados diretamente**

- `Path`
- `source_path.is_file`
- `TelemetryParseError`
- `_sha256`
- `source_path.stat`
- `find_csv_header_line`
- `marker.casefold`
- `source_path.open`
- `enumerate`
- `next`
- `csv.reader`
- `issues.append`
- `raw_line.rstrip`
- `str`
- `field.strip`
- `len`
- `set`
- `tuple`
- `list`
- `raw_line.strip`
- `marker_values.get`
- `stripped.casefold`
- `zip`
- `raw_value.strip`
- `float`
- `math.isfinite`
- `records.append`
- `ParsedTelemetry`
- `source_path.resolve`

## `source/antares_fd/telemetry/timebase.py`

File-order clock segmentation without an inferred inter-segment timeline.

### `segment_timebase`

[Implementação: source/antares_fd/telemetry/timebase.py:21](../../source/antares_fd/telemetry/timebase.py#L21)

```python
segment_timebase(parsed: ParsedTelemetry, *, timestamp_channel: str, seconds_per_unit: float | None) -> pd.DataFrame
```

Retain acquisition order and restart local elapsed time at a clock decrease.

The first finite clock reading in a segment is its local origin. A missing
clock value remains in that segment with an unavailable elapsed time. The
next finite value is compared with the preceding finite reading, so an
intervening missing value cannot conceal an observed backward jump.
Neither reset downtime nor a globally continuous clock is inferred.

**Entradas e tipos declarados**

- `parsed: ParsedTelemetry`
- `timestamp_channel: str`
- `seconds_per_unit: float | None`

**Retornos/yields explícitos**

- `pd.DataFrame.from_records(rows, columns=SEGMENT_COLUMNS)`

**Exceções lançadas explicitamente**

- `ValueError(f'Timestamp channel {timestamp_channel!r} is absent from the parsed header')`
- `ValueError('seconds_per_unit must be finite and positive')`

**Colaboradores chamados diretamente**

- `ValueError`
- `math.isfinite`
- `rows.append`
- `pd.DataFrame.from_records`

## `source/antares_fd/validation/__init__.py`

Explicit model provenance and time-aligned flight comparison contracts.

Módulo declarativo, ponto de entrada sem funções ou exportação de interfaces; não contém funções próprias.

## `source/antares_fd/validation/models.py`

Validated model-variant declarations; this module never changes physics inputs.

### `_nonempty_text`

[Implementação: source/antares_fd/validation/models.py:48](../../source/antares_fd/validation/models.py#L48)

```python
_nonempty_text(value: Any, field: str) -> str
```

Exija texto não vazio para identificar um campo de proveniência.

Valida o tipo e remove espaços externos; retorna o texto normalizado.
Ausência ou texto vazio gera ValueError com o nome field.

**Entradas e tipos declarados**

- `value: Any`
- `field: str`

**Retornos/yields explícitos**

- `value.strip()`

**Exceções lançadas explicitamente**

- `ValueError(f'{field} must be nonempty text')`

**Colaboradores chamados diretamente**

- `isinstance`
- `value.strip`
- `ValueError`

### `parse_model_variants`

[Implementação: source/antares_fd/validation/models.py:59](../../source/antares_fd/validation/models.py#L59)

```python
parse_model_variants(document: Mapping[str, Any]) -> dict[str, ModelVariant]
```

Validate provenance, status and separation before consumers use a model.

**Entradas e tipos declarados**

- `document: Mapping[str, Any]`

**Retornos/yields explícitos**

- `variants`

**Exceções lançadas explicitamente**

- `ValueError('model_variants schema_version must be 1')`
- `ValueError('variants must be a nonempty list')`
- `ValueError('Each variant must be a mapping')`
- `ValueError(f'Duplicate variant id: {model_id}')`
- `ValueError(f'{model_id}: unsupported role {role}')`
- `ValueError(f'Duplicate variant role: {role}')`
- `ValueError(f'{model_id}: status {status} is invalid for {role}')`
- `ValueError(f'{model_id}.runnable must be boolean')`
- `ValueError(f'{model_id}: {status} requires runnable=true')`
- `ValueError(f'{model_id}: runnable requires a complete or reference configuration')`
- `ValueError(f'{model_id}: non-runnable variant cannot claim a configuration')`
- `ValueError(f'{model_id}.evidence must be a list')`
- `ValueError(f'{model_id}.evidence entries must be mappings')`
- `ValueError(f'{model_id}: unsupported evidence origin {origin}')`
- `ValueError(f'{model_id}: PREFLIGHT cannot use {origin} evidence')`
- `ValueError(f'{model_id}.missing_evidence must be a list of nonempty strings')`
- `ValueError(f'{model_id}: incomplete status requires missing_evidence')`
- `ValueError(f'{model_id}.identified_changes must be a list')`
- `ValueError(f'{model_id}: only POSTFLIGHT may identify parameters')`
- `ValueError(f'{model_id}.identified_changes needs {sorted(CHANGE_FIELDS)}')`

**Colaboradores chamados diretamente**

- `isinstance`
- `document.get`
- `ValueError`
- `_nonempty_text`
- `set`
- `entry.get`
- `roles_seen.add`
- `item.get`
- `evidence.append`
- `Evidence`
- `any`
- `x.strip`
- `change.keys`
- `sorted`
- `ModelVariant`
- `tuple`
- `dict`

### `load_model_variants`

[Implementação: source/antares_fd/validation/models.py:140](../../source/antares_fd/validation/models.py#L140)

```python
load_model_variants(path: Path) -> dict[str, ModelVariant]
```

Read a declared model history without inferring any missing inputs.

**Entradas e tipos declarados**

- `path: Path`

**Retornos/yields explícitos**

- `parse_model_variants(document)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `Path(path).open`
- `Path`
- `yaml.safe_load`
- `parse_model_variants`

## `source/antares_fd/validation/reference.py`

Archive a current RocketPy model run without claiming preflight validation.

### `_sha256`

[Implementação: source/antares_fd/validation/reference.py:37](../../source/antares_fd/validation/reference.py#L37)

```python
_sha256(path: Path) -> str
```

Calcule SHA-256 de uma entrada ou produto de referência.

Lê blocos binários e retorna digest hexadecimal, sem modificar
o arquivo que será comparado ao manifesto.

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

### `_snapshot_inputs`

[Implementação: source/antares_fd/validation/reference.py:50](../../source/antares_fd/validation/reference.py#L50)

```python
_snapshot_inputs(project_dir: Path, snapshot_dir: Path) -> dict[str, str]
```

Copy inputs once; reject concurrent edits while preparing the snapshot.

**Entradas e tipos declarados**

- `project_dir: Path`
- `snapshot_dir: Path`

**Retornos/yields explícitos**

- `hashes`

**Exceções lançadas explicitamente**

- `RuntimeError(f'Model input changed during snapshot: {relative}')`

**Colaboradores chamados diretamente**

- `collect_project_model_inputs`
- `source.relative_to`
- `_sha256`
- `target.parent.mkdir`
- `shutil.copyfile`
- `RuntimeError`
- `relative.as_posix`

### `_timeseries_frame`

[Implementação: source/antares_fd/validation/reference.py:67](../../source/antares_fd/validation/reference.py#L67)

```python
_timeseries_frame(metrics: Any) -> pd.DataFrame
```

Converta séries canônicas de FlightMetrics em uma tabela temporal.

Organiza tempo e grandezas físicas com nomes de coluna estáveis.
Retorna DataFrame para armazenamento da execução de referência.

**Entradas e tipos declarados**

- `metrics: Any`

**Retornos/yields explícitos**

- `frame`

**Exceções lançadas explicitamente**

- `ValueError('RocketPy reference timeseries contains non-finite or non-increasing values')`

**Colaboradores chamados diretamente**

- `pd.DataFrame`
- `np.asarray`
- `getattr`
- `names.items`
- `np.isfinite(frame.to_numpy()).all`
- `np.isfinite`
- `frame.to_numpy`
- `np.any`
- `np.diff`
- `ValueError`

### `_atmosphere_frame`

[Implementação: source/antares_fd/validation/reference.py:87](../../source/antares_fd/validation/reference.py#L87)

```python
_atmosphere_frame(flight: Any) -> pd.DataFrame
```

Read the full interpolated MAGI grid directly, with no synthetic fallback.

**Entradas e tipos declarados**

- `flight: Any`

**Retornos/yields explícitos**

- `frame`

**Exceções lançadas explicitamente**

- `ValueError('Current reference requires a non-fallback MAGI atmospheric profile')`
- `ValueError('MAGI pressure grid is unavailable for archival')`
- `ValueError('MAGI altitude grid is invalid')`
- `ValueError('MAGI atmosphere contains non-finite values')`

**Colaboradores chamados diretamente**

- `getattr`
- `isinstance`
- `provenance.get`
- `ValueError`
- `np.asarray`
- `len`
- `np.any`
- `np.diff`
- `env.pressure`
- `env.temperature`
- `env.density`
- `env.wind_velocity_x`
- `env.wind_velocity_y`
- `env.speed_of_sound`
- `env.dynamic_viscosity`
- `pd.DataFrame`
- `np.isfinite(frame.to_numpy()).all`
- `np.isfinite`
- `frame.to_numpy`

### `_plain`

[Implementação: source/antares_fd/validation/reference.py:118](../../source/antares_fd/validation/reference.py#L118)

```python
_plain(value: Any) -> Any
```

Converta métricas estruturadas em dados serializáveis de manifesto.

Trata dataclasses, arrays e escalares NumPy conforme o contrato interno;
retorna a estrutura convertida sem modificar os objetos de origem.

**Entradas e tipos declarados**

- `value: Any`

**Retornos/yields explícitos**

- `{field.name: _plain(getattr(value, field.name)) for field in dataclasses.fields(value)}`
- `{str(key): _plain(item) for key, item in value.items()}`
- `[_plain(item) for item in value]`
- `_plain(value.tolist())`
- `_plain(value.item())`
- `value`
- `value.isoformat()`

**Exceções lançadas explicitamente**

- `ValueError('Model artifact contains a non-finite scalar')`
- `TypeError(f'Cannot serialize model provenance value of type {type(value).__name__}')`

**Colaboradores chamados diretamente**

- `dataclasses.is_dataclass`
- `_plain`
- `getattr`
- `dataclasses.fields`
- `isinstance`
- `str`
- `value.items`
- `value.tolist`
- `value.item`
- `math.isfinite`
- `ValueError`
- `hasattr`
- `value.isoformat`
- `TypeError`
- `type`

### `_git_metadata`

[Implementação: source/antares_fd/validation/reference.py:143](../../source/antares_fd/validation/reference.py#L143)

```python
_git_metadata(root: Path) -> dict[str, Any]
```

Colete a proveniência Git usando o coletor compartilhado.

Retorna revisão, estado de alterações e identidade do conteúdo de root.
A consulta não modifica arquivos nem o índice Git.

**Entradas e tipos declarados**

- `root: Path`

**Retornos/yields explícitos**

- `get_git_provenance(root)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `get_git_provenance`

### `_results_output_path`

[Implementação: source/antares_fd/validation/reference.py:152](../../source/antares_fd/validation/reference.py#L152)

```python
_results_output_path(project_dir: Path, output_dir: Path) -> Path
```

Valide o diretório de saída de uma referência de modelo.

Resolve output_dir e exige a organização autorizada em results.
Rejeita destinos que possam sobrescrever entradas do projeto.

**Entradas e tipos declarados**

- `project_dir: Path`
- `output_dir: Path`

**Retornos/yields explícitos**

- `output_dir`

**Exceções lançadas explicitamente**

- `ValueError('Reference artifacts require a non-symlink repository results/ directory')`
- `ValueError('Reference artifacts must be written below the repository results/ directory')`
- `FileExistsError(f'Reference output already exists: {output_dir}')`

**Colaboradores chamados diretamente**

- `results_root.is_symlink`
- `ValueError`
- `Path`
- `output_dir.is_absolute`
- `output_dir.resolve`
- `results_root.resolve`
- `output_dir.is_relative_to`
- `output_dir.exists`
- `FileExistsError`

### `_archived_environment`

[Implementação: source/antares_fd/validation/reference.py:173](../../source/antares_fd/validation/reference.py#L173)

```python
_archived_environment(config: Any, atmosphere: pd.DataFrame, provenance: dict[str, Any]) -> Any
```

Rebuild archived MAGI inputs through the same RocketPy profile builder.

**Entradas e tipos declarados**

- `config: Any`
- `atmosphere: pd.DataFrame`
- `provenance: dict[str, Any]`

**Retornos/yields explícitos**

- `env`

**Exceções lançadas explicitamente**

- `ValueError('Archived atmosphere lacks one or more required physical fields')`
- `ValueError('Archived atmosphere contains too few or non-finite values')`
- `ValueError('Archived atmosphere altitude must increase strictly')`
- `ValueError('Archived atmosphere does not cover launch elevation')`

**Colaboradores chamados diretamente**

- `any`
- `ValueError`
- `atmosphere['altitude_asl_m'].to_numpy`
- `len`
- `np.isfinite(atmosphere[list(required)].to_numpy(dtype=float)).all`
- `np.isfinite`
- `atmosphere[list(required)].to_numpy`
- `list`
- `np.any`
- `np.diff`
- `float`
- `atmosphere['specific_humidity_kg_kg'].to_numpy`
- `provenance.get`
- `_base_environment`
- `np.column_stack`
- `atmosphere['pressure_pa'].to_numpy`
- `atmosphere['temperature_k'].to_numpy`
- `atmosphere['wind_east_mps'].to_numpy`
- `atmosphere['wind_north_mps'].to_numpy`
- `env.set_atmospheric_model`
- `Function`
- `ProfileVariable`
- `z.copy`
- `atmosphere[column].to_numpy(dtype=float).copy`
- `atmosphere[column].to_numpy`
- `setattr`
- `dict`
- `isinstance`
- `datetime.fromisoformat`
- `valid_time.replace`
- `run_time.replace`
- `AtmosphericProfile`
- `str`
- `datetime.fromtimestamp`
- `provenance.items`
- `_apply_profile`

### `_execute_reference_products`

[Implementação: source/antares_fd/validation/reference.py:263](../../source/antares_fd/validation/reference.py#L263)

```python
_execute_reference_products(project_dir: Path, variant: ModelVariant, stage: Path, snapshot: Path, input_hashes: dict[str, str], *, environment: Any | None=None) -> tuple[dict[str, Any], Any]
```

Execute o modelo de referência com entradas previamente congeladas.

Constrói os objetos RocketPy a partir do snapshot, integra um voo e grava
métricas, séries, perfil atmosférico e manifesto em stage.
input_hashes vincula os produtos às entradas; environment permite replay
da atmosfera arquivada sem consultar uma nova previsão.

**Entradas e tipos declarados**

- `project_dir: Path`
- `variant: ModelVariant`
- `stage: Path`
- `snapshot: Path`
- `input_hashes: dict[str, str]`
- `environment: Any | None`

**Retornos/yields explícitos**

- `(manifest, flight)`

**Exceções lançadas explicitamente**

- `ValueError('Current reference requires configured MAGI with fallback disabled')`

**Colaboradores chamados diretamente**

- `load_project_config`
- `str(config.environment.get('type', '')).lower`
- `str`
- `config.environment.get`
- `config.environment.get('fallback', {}).get`
- `ValueError`
- `time.perf_counter`
- `execute_scenario`
- `extract_flight_metrics`
- `_timeseries_frame`
- `_atmosphere_frame`
- `write_parquet_atomic`
- `_plain`
- `getattr`
- `dataclasses.fields`
- `write_json_atomic`
- `importlib.metadata.version`
- `datetime.now(timezone.utc).isoformat`
- `datetime.now`
- `_git_metadata`
- `platform.python_version`
- `_sha256`

### `run_current_reference`

[Implementação: source/antares_fd/validation/reference.py:328](../../source/antares_fd/validation/reference.py#L328)

```python
run_current_reference(project_dir: Path, variant: ModelVariant, output_dir: Path) -> Path
```

Run a labeled current-model reference from copied inputs.

This is a model execution, not comparison to flight evidence. The call
refuses to publish a partial output and never falls back to standard air.

**Entradas e tipos declarados**

- `project_dir: Path`
- `variant: ModelVariant`
- `output_dir: Path`

**Retornos/yields explícitos**

- `output_dir`

**Exceções lançadas explicitamente**

- `ValueError('Only a runnable CURRENT_REFERENCE variant may use this exporter')`
- `ValueError('Unsupported current-reference configuration source')`
- `raise (propaga a exceção ativa)`

**Colaboradores chamados diretamente**

- `ValueError`
- `Path(project_dir).resolve`
- `Path`
- `_results_output_path`
- `output_dir.parent.mkdir`
- `tempfile.mkdtemp`
- `_snapshot_inputs`
- `_execute_reference_products`
- `os.replace`
- `shutil.rmtree`

### `_compare_reference_timeseries`

[Implementação: source/antares_fd/validation/reference.py:353](../../source/antares_fd/validation/reference.py#L353)

```python
_compare_reference_timeseries(original: pd.DataFrame, replay: pd.DataFrame, *, rtol: float, atol: float) -> dict[str, Any]
```

Compare states at common physical times, without extrapolation.

**Entradas e tipos declarados**

- `original: pd.DataFrame`
- `replay: pd.DataFrame`
- `rtol: float`
- `atol: float`

**Retornos/yields explícitos**

- `{'matches': False, 'reason': 'trajectory schemas differ', 'common_time_samples': 0, 'channels': {}}`
- `{'matches': False, 'reason': 'trajectories have no common sampled time', 'common_time_samples': 0, 'channels': {}}`
- `{'matches': bool(matches), 'reason': None, 'alignment': 'linear interpolation of replay states onto source times within shared time domain; no extrapolation', 'common_time_samples': int(len(common_time)), 'common_time_bounds_s': [float(common_time[0]), float(common_time[-1])], 'source_time_samples_outside_common_domain': int((~in_common_domain).sum()), 'index_paired_time_maximum_difference_s': float(np.max(np.abs(source_time[:min(len(source_time), len(replay_time))] - replay_time[:min(len(source_time), len(replay_time))]))), 'maximum_absolute_difference': maximum_difference, 'maximum_difference_channel': channel_name, 'maximum_difference_time_s': max_difference_time, 'channels': channels}`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `list`
- `original['time_s'].to_numpy`
- `replay['time_s'].to_numpy`
- `len`
- `original[column].to_numpy`
- `np.interp`
- `replay[column].to_numpy`
- `np.abs`
- `np.isfinite(difference).all`
- `np.isfinite`
- `int`
- `np.argmax`
- `float`
- `np.sqrt`
- `np.mean`
- `all_differences.append`
- `bool`
- `np.all`
- `np.concatenate`
- `np.array`
- `np.cumsum`
- `np.searchsorted`
- `(~in_common_domain).sum`
- `np.max`
- `min`

### `replay_archived_reference`

[Implementação: source/antares_fd/validation/reference.py:436](../../source/antares_fd/validation/reference.py#L436)

```python
replay_archived_reference(archive_dir: Path, output_dir: Path) -> Path
```

Repeat a current-model run with the exact archived input and MAGI tables.

**Entradas e tipos declarados**

- `archive_dir: Path`
- `output_dir: Path`

**Retornos/yields explícitos**

- `output_dir`

**Exceções lançadas explicitamente**

- `ValueError('Archived source is not a CURRENT_REFERENCE artifact')`
- `ValueError('Cannot locate the project checkout associated with this archive')`
- `ValueError('Archive contains no frozen model input hashes')`
- `ValueError(f'Archived model input is missing or changed: {relative}')`
- `ValueError(f'Archived reference artifact is missing or fails its checksum: {name}')`
- `ValueError('Copied model inputs do not match the original reference manifest')`
- `raise (propaga a exceção ativa)`

**Colaboradores chamados diretamente**

- `Path(archive_dir).resolve`
- `Path`
- `json.loads`
- `archive_manifest_path.read_text`
- `manifest.get`
- `ValueError`
- `project_dir.is_dir`
- `_results_output_path`
- `expected_hashes.items`
- `(input_dir / relative).resolve`
- `source.is_relative_to`
- `input_dir.resolve`
- `source.is_file`
- `_sha256`
- `artifact_path.is_file`
- `expected_outputs.get`
- `output_dir.parent.mkdir`
- `tempfile.mkdtemp`
- `shutil.copytree`
- `pd.read_parquet`
- `load_project_config`
- `_archived_environment`
- `ModelVariant`
- `str`
- `_execute_reference_products`
- `_compare_reference_timeseries`
- `bool`
- `list`
- `np.allclose`
- `original_atmosphere.to_numpy`
- `replay_atmosphere.to_numpy`
- `(archive_dir / 'flight_metrics.json').read_text`
- `(stage / 'flight_metrics.json').read_text`
- `original_metrics.keys`
- `replay_metrics.keys`
- `isinstance`
- `float`
- `np.isclose`
- `manifest.get('git', {}).get`
- `replay_manifest.get('git', {}).get`
- `replay_manifest.get`
- `np.max`
- `np.abs`
- `getattr`
- `write_json_atomic`
- `os.replace`
- `shutil.rmtree`

## `source/antares_fd/validation/residuals.py`

Descriptive residuals with explicit, evidence-backed clock alignment.

### `Alignment.__post_init__`

[Implementação: source/antares_fd/validation/residuals.py:24](../../source/antares_fd/validation/residuals.py#L24)

```python
Alignment.__post_init__(self) -> None
```

Valide a transformação temporal declarada para comparar séries.

Exige deslocamento finito e justificativa de alinhamento compatível
com o tipo informado. Falhas geram ValueError antes da interpolação.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- `ValueError('segment_id must be a nonnegative integer')`
- `ValueError('Alignment times must be finite and uncertainty nonnegative')`
- `ValueError('Alignment requires an observed event and evidence')`

**Colaboradores chamados diretamente**

- `isinstance`
- `ValueError`
- `any`
- `math.isfinite`
- `self.event.strip`
- `self.evidence.strip`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `ComparisonBasis.__post_init__`

[Implementação: source/antares_fd/validation/residuals.py:51](../../source/antares_fd/validation/residuals.py#L51)

```python
ComparisonBasis.__post_init__(self) -> None
```

Valide unidades e referenciais usados na comparação experimental.

Exige a base declarada das grandezas e sua proveniência, evitando
comparar séries com origens físicas diferentes sem indicação explícita.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- `ValueError('Comparison units, frames and evidence must be nonempty')`
- `ValueError('observed_unit_status must describe the unit evidence')`
- `ValueError('Comparison unit mismatch; convert explicitly upstream')`
- `ValueError('Comparison frame mismatch or unknown frame')`

**Colaboradores chamados diretamente**

- `any`
- `isinstance`
- `value.strip`
- `ValueError`
- `self.observed_frame.upper`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `_array`

[Implementação: source/antares_fd/validation/residuals.py:72](../../source/antares_fd/validation/residuals.py#L72)

```python
_array(values: Sequence[float], name: str) -> np.ndarray
```

Converta uma sequência em vetor numérico unidimensional não vazio.

Usa dtype float e rejeita arrays vazios ou com mais de uma dimensão.
Erro identifica name. Finitude e suporte de interpolação são tratados
posteriormente pelo comparador.

**Entradas e tipos declarados**

- `values: Sequence[float]`
- `name: str`

**Retornos/yields explícitos**

- `array`

**Exceções lançadas explicitamente**

- `ValueError(f'{name} must be a nonempty one-dimensional series')`

**Colaboradores chamados diretamente**

- `np.asarray`
- `ValueError`

### `compare_time_series`

[Implementação: source/antares_fd/validation/residuals.py:85](../../source/antares_fd/validation/residuals.py#L85)

```python
compare_time_series(observed_time_s: Sequence[float], observed_segment_id: Sequence[int], observed_values: Sequence[float], simulated_time_s: Sequence[float], simulated_values: Sequence[float], *, observed_record_index: Sequence[int], alignment: Alignment, basis: ComparisonBasis, quantity: str, observed_origin: str) -> pd.DataFrame
```

Return simulated-minus-observed residuals without crossing clock segments.

The caller must establish the event anchor independently from telemetry.
This operation interpolates the simulated series only within its domain.
It does not infer a launch time, correct timestamps or fill missing samples.

**Entradas e tipos declarados**

- `observed_time_s: Sequence[float]`
- `observed_segment_id: Sequence[int]`
- `observed_values: Sequence[float]`
- `simulated_time_s: Sequence[float]`
- `simulated_values: Sequence[float]`
- `observed_record_index: Sequence[int]`
- `alignment: Alignment`
- `basis: ComparisonBasis`
- `quantity: str`
- `observed_origin: str`

**Retornos/yields explícitos**

- `result`

**Exceções lançadas explicitamente**

- `ValueError('observed_origin must be MEASURED or DERIVED')`
- `ValueError('basis must explicitly declare matching units and frames')`
- `ValueError('quantity must be explicitly named with units')`
- `ValueError('Observed time, segment and value series must have equal length')`
- `ValueError('Simulated time and value series need at least two paired samples')`
- `ValueError('observed_record_index must preserve unique acquisition order')`
- `ValueError('observed_segment_id must contain integer segment_id values')`
- `ValueError('Comparison requires a single observed segment matching the alignment')`
- `ValueError('Time coordinates and simulated values must be finite')`
- `ValueError('Observed values may be missing (NaN), but not infinite')`
- `ValueError('Time coordinates must increase strictly in file order')`
- `ValueError('Comparison would require simulation extrapolation')`

**Colaboradores chamados diretamente**

- `ValueError`
- `isinstance`
- `quantity.strip`
- `_array`
- `np.asarray`
- `len`
- `np.issubdtype`
- `np.any`
- `np.diff`
- `np.all`
- `np.isfinite(obs_t).all`
- `np.isfinite`
- `np.isfinite(sim_t).all`
- `np.isfinite(sim_y).all`
- `np.isinf(obs_y).any`
- `np.isinf`
- `np.interp`
- `pd.DataFrame`
- `result.attrs.update`

### `summarize_residuals`

[Implementação: source/antares_fd/validation/residuals.py:159](../../source/antares_fd/validation/residuals.py#L159)

```python
summarize_residuals(residuals: pd.DataFrame) -> dict[str, float | int | str]
```

Describe valid residuals; this does not establish model validity.

**Entradas e tipos declarados**

- `residuals: pd.DataFrame`

**Retornos/yields explícitos**

- `{'status': 'INSUFFICIENT_OBSERVABILITY', 'valid_count': 0}`
- `{'status': 'DESCRIPTIVE_ONLY', 'valid_count': int(len(finite)), 'mean': float(np.mean(finite)), 'mae': float(np.mean(np.abs(finite))), 'rmse': float(np.sqrt(np.mean(finite * finite))), 'maximum_absolute': float(np.max(np.abs(finite)))}`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `residuals['residual_simulated_minus_observed'].to_numpy`
- `np.isfinite`
- `len`
- `int`
- `float`
- `np.mean`
- `np.abs`
- `np.sqrt`
- `np.max`
