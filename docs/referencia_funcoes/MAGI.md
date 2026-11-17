# Funções de MAGI

[Índice e convenções](README.md)

## `MAGI/MAGI_App.py`

Módulo declarativo, ponto de entrada sem funções ou exportação de interfaces; não contém funções próprias.

## `MAGI/__init__.py`

Módulo declarativo, ponto de entrada sem funções ou exportação de interfaces; não contém funções próprias.

## `MAGI/balthasar.py`

Deterministic Open-Meteo profiles and explicitly identified time scenarios.

The forecast endpoint does not provide a native probabilistic vertical ensemble.
Samples at different valid times are sensitivity scenarios, never real members.
For dates beyond the operational numerical forecast horizon, real historical
profiles from past years are retrieved to construct an authentic multi-year ensemble.

### `Balthasar.__init__`

[Implementação: MAGI/balthasar.py:35](../../MAGI/balthasar.py#L35)

```python
Balthasar.__init__(self, cache_dir='dados_cache', elevation_msl=450, model=None)
```

Configure a aquisição meteorológica e seu diretório de cache.

Resolve cache relativo ao módulo, armazena elevação MSL e modelo opcional
e cria o diretório. Inicializa metadados sem afirmar aquisição bem-sucedida.

**Entradas e tipos declarados**

- `cache_dir: tipo não anotado; ver contrato acima`
- `elevation_msl: tipo não anotado; ver contrato acima`
- `model: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `os.path.isabs`
- `os.path.dirname`
- `os.path.abspath`
- `os.path.join`
- `str`
- `Path(self.cache_dir).mkdir`
- `Path`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `Balthasar._utc`

[Implementação: MAGI/balthasar.py:53](../../MAGI/balthasar.py#L53)

```python
Balthasar._utc(value)
```

Normalize um instante para Timestamp UTC com fuso explícito.

None seleciona o horário atual UTC; timestamp sem timezone gera ValueError.
O retorno é usado para comparar cobertura temporal e idade do cache.

**Entradas e tipos declarados**

- `value: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `timestamp.tz_convert('UTC')`

**Exceções lançadas explicitamente**

- `ValueError('Forecast time must include an explicit UTC offset')`

**Colaboradores chamados diretamente**

- `pd.Timestamp.now`
- `pd.Timestamp`
- `ValueError`
- `timestamp.tz_convert`

### `Balthasar._safe_replace_year`

[Implementação: MAGI/balthasar.py:65](../../MAGI/balthasar.py#L65)

```python
Balthasar._safe_replace_year(dt: pd.Timestamp, year: int) -> pd.Timestamp
```

Replace year in timestamp, gracefully handling leap-year edge cases.

**Entradas e tipos declarados**

- `dt: pd.Timestamp`
- `year: int`

**Retornos/yields explícitos**

- `dt.replace(year=year)`
- `dt.replace(year=year, day=28)`

**Exceções lançadas explicitamente**

- `raise (propaga a exceção ativa)`

**Colaboradores chamados diretamente**

- `dt.replace`

### `Balthasar._resolve_historical_years`

[Implementação: MAGI/balthasar.py:74](../../MAGI/balthasar.py#L74)

```python
Balthasar._resolve_historical_years(self, target: pd.Timestamp, explicit_years=None)
```

Determine verified historical years with pressure-level coverage.

**Entradas e tipos declarados**

- `target: pd.Timestamp`
- `explicit_years: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `years`
- `available if available else [self.HISTORICAL_START_YEAR]`

**Exceções lançadas explicitamente**

- `ValueError('explicit_years list cannot be empty')`

**Colaboradores chamados diretamente**

- `sorted`
- `int`
- `ValueError`
- `pd.Timestamp.now`
- `self._safe_replace_year`
- `now.date`
- `target_in_now_year.date`
- `range`

### `Balthasar._is_beyond_forecast_horizon`

[Implementação: MAGI/balthasar.py:90](../../MAGI/balthasar.py#L90)

```python
Balthasar._is_beyond_forecast_horizon(self, target: pd.Timestamp) -> bool
```

Check if target date is further ahead than the numerical forecast limit (~14 days).

**Entradas e tipos declarados**

- `target: pd.Timestamp`

**Retornos/yields explícitos**

- `target.date() > (now + pd.Timedelta(days=self.FORECAST_MAX_DAYS_AHEAD)).date()`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `pd.Timestamp.now`
- `target.date`
- `(now + pd.Timedelta(days=self.FORECAST_MAX_DAYS_AHEAD)).date`
- `pd.Timedelta`

### `Balthasar._load_payload`

[Implementação: MAGI/balthasar.py:95](../../MAGI/balthasar.py#L95)

```python
Balthasar._load_payload(self, lat, lon, target, window_minutes=0)
```

Obtenha a resposta meteorológica correspondente ao local e intervalo.

Valida coordenadas, monta a consulta Open-Meteo e calcula chave SHA-256.
Prefere cache recente; caso necessário consulta HTTP com timeout, valida
unidades/cobertura e salva o cache. Em falha de rede pode reutilizar cache
antigo identificado como tal; atualiza last_fetch_metadata sem renovar
artificialmente o instante da aquisição.

**Entradas e tipos declarados**

- `lat: tipo não anotado; ver contrato acima`
- `lon: tipo não anotado; ver contrato acima`
- `target: tipo não anotado; ver contrato acima`
- `window_minutes: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `payload`

**Exceções lançadas explicitamente**

- `ValueError('Valid latitude, longitude and elevation are required')`
- `exc`

**Colaboradores chamados diretamente**

- `np.isfinite([lat, lon, self.elevation_msl]).all`
- `np.isfinite`
- `ValueError`
- `pd.Timedelta`
- `','.join`
- `(target - span).strftime`
- `(target + span).strftime`
- `target.date`
- `pd.Timestamp.now(tz='UTC').date`
- `pd.Timestamp.now`
- `hashlib.sha256(json.dumps([url, params], sort_keys=True).encode()).hexdigest`
- `hashlib.sha256`
- `json.dumps([url, params], sort_keys=True).encode`
- `json.dumps`
- `Path`
- `cache_file.exists`
- `json.loads`
- `cache_file.read_text`
- `(now - self._utc(cached['retrieved_at_utc'])).total_seconds`
- `self._utc`
- `requests.get`
- `response.raise_for_status`
- `response.json`
- `self._profile_from_payload`
- `now.isoformat`
- `cache_file.with_suffix`
- `temporary.write_text`
- `temporary.replace`

### `Balthasar._profile_from_payload`

[Implementação: MAGI/balthasar.py:162](../../MAGI/balthasar.py#L162)

```python
Balthasar._profile_from_payload(self, payload, target, lat, lon)
```

Interpolate within two available times in ENU, with unit checks.

**Entradas e tipos declarados**

- `payload: tipo não anotado; ver contrato acima`
- `target: tipo não anotado; ver contrato acima`
- `lat: tipo não anotado; ver contrato acima`
- `lon: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `df`

**Exceções lançadas explicitamente**

- `ValueError('Forecast has no strictly increasing valid-time axis')`
- `ValueError(f'Requested time {target} is outside forecast coverage {times[0]} .. {times[-1]}')`
- `ValueError(f'Unexpected units for {key}: {units.get(key)!r}; expected {unit}')`
- `ValueError(f'Forecast time/variable length mismatch: {key}')`
- `ValueError('Forecast lacks two complete pressure levels (including humidity)')`

**Colaboradores chamados diretamente**

- `payload.get`
- `pd.DatetimeIndex`
- `pd.to_datetime`
- `hourly.get`
- `len`
- `ValueError`
- `min`
- `int`
- `times.searchsorted`
- `expected_units.items`
- `units.get`
- `np.asarray`
- `np.isfinite(pair).all`
- `np.isfinite`
- `CasperPhysics.speed_dir_to_uv`
- `blend`
- `records.append`
- `pd.DataFrame(records).sort_values('altitude_agl_m').reset_index`
- `pd.DataFrame(records).sort_values`
- `pd.DataFrame`
- `CasperPhysics.uv_to_speed_dir`
- `CasperPhysics.calc_specific_humidity`
- `CasperPhysics.calc_density`
- `CasperPhysics.calc_shear`
- `metadata.items`
- `times[left].isoformat`
- `times[right].isoformat`
- `MagiSchema.validate`

### `Balthasar._fetch_open_meteo`

[Implementação: MAGI/balthasar.py:229](../../MAGI/balthasar.py#L229)

```python
Balthasar._fetch_open_meteo(self, lat, lon, target_date_str)
```

Converta uma consulta determinística em perfil atmosférico MAGI.

Normaliza o instante, obtém payload por rede/cache e usa o conversor comum
com verificação de unidades. Retorna DataFrame com metadados de aquisição.

**Entradas e tipos declarados**

- `lat: tipo não anotado; ver contrato acima`
- `lon: tipo não anotado; ver contrato acima`
- `target_date_str: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `df`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self._utc`
- `self._load_payload`
- `self._profile_from_payload`
- `df.attrs.update`

### `Balthasar.fetch_operational_forecast`

[Implementação: MAGI/balthasar.py:242](../../MAGI/balthasar.py#L242)

```python
Balthasar.fetch_operational_forecast(self, lat=None, lon=None, target_date_str=None, time_window_minutes=0, time_step_minutes=10, historical_years=None, historical_reference_year=None, is_ensemble=False)
```

Return (deterministic profile or time scenarios/multi-year ensemble, is_native_ensemble=False).

**Entradas e tipos declarados**

- `lat: tipo não anotado; ver contrato acima`
- `lon: tipo não anotado; ver contrato acima`
- `target_date_str: tipo não anotado; ver contrato acima`
- `time_window_minutes: tipo não anotado; ver contrato acima`
- `time_step_minutes: tipo não anotado; ver contrato acima`
- `historical_years: tipo não anotado; ver contrato acima`
- `historical_reference_year: tipo não anotado; ver contrato acima`
- `is_ensemble: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `(df, False)`
- `(members, False)`
- `(self._fetch_open_meteo(lat, lon, target), False)`
- `(df_fallback, False)`

**Exceções lançadas explicitamente**

- `ValueError('Time window must be nonnegative and time step positive')`
- `ValueError(f'Failed to retrieve any real historical profiles for target {target} across years {years}')`
- `exc`

**Colaboradores chamados diretamente**

- `ValueError`
- `self._utc`
- `self._is_beyond_forecast_horizon`
- `self._resolve_historical_years`
- `self._safe_replace_year`
- `self._load_payload`
- `self._profile_from_payload`
- `target.isoformat`
- `target_hist.isoformat`
- `target.strftime`
- `target_hist.strftime`
- `df.attrs.update`
- `np.arange`
- `pd.Timedelta`
- `float`
- `len`
- `timestamp.isoformat`
- `timestamp.strftime`
- `member.attrs.update`
- `members.append`
- `print`
- `self._fetch_open_meteo`
- `self._fetch_deterministic_fallback`

### `Balthasar._fetch_deterministic_fallback`

[Implementação: MAGI/balthasar.py:341](../../MAGI/balthasar.py#L341)

```python
Balthasar._fetch_deterministic_fallback(self)
```

Read a legacy CSV for offline analysis, never relabel it as a forecast.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `MagiSchema.create_empty()`
- `df`

**Exceções lançadas explicitamente**

- `ValueError('Legacy data needs timestamps and measured/model humidity')`

**Colaboradores chamados diretamente**

- `Path`
- `path.exists`
- `MagiSchema.create_empty`
- `pd.read_csv`
- `ValueError`
- `len`
- `pd.to_datetime`
- `CasperPhysics.speed_dir_to_uv`
- `CasperPhysics.uv_to_speed_dir`
- `CasperPhysics.calc_specific_humidity`
- `CasperPhysics.calc_density`
- `CasperPhysics.calc_shear`

### `Balthasar.fetch_metar_taf`

[Implementação: MAGI/balthasar.py:369](../../MAGI/balthasar.py#L369)

```python
Balthasar.fetch_metar_taf(self, aeroportos='SBBU,SBAE,SBRP,SBSR,SBGR')
```

Connects to AviationWeather.gov API to fetch METARs and TAFs.

**Entradas e tipos declarados**

- `aeroportos: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `(metars, tafs)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `print`
- `os.path.join`
- `socket.create_connection`
- `requests.get`
- `open`
- `f.write`
- `os.path.exists`
- `line.strip`
- `f.readlines`

### `BalthasarVisuals.print_aerodrome_report`

[Implementação: MAGI/balthasar.py:416](../../MAGI/balthasar.py#L416)

```python
BalthasarVisuals.print_aerodrome_report(metars, tafs)
```

Formate observações METAR e previsões TAF em Markdown.

Percorre as listas de boletins e indica indisponibilidade quando vazias.
Retorna uma string; não consulta rede e não imprime diretamente.

**Entradas e tipos declarados**

- `metars: tipo não anotado; ver contrato acima`
- `tafs: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `md_output`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- Nenhuma ocorrência explícita no corpo local.

## `MAGI/build_notebook.py`

### `add_cell`

[Implementação: MAGI/build_notebook.py:15](../../MAGI/build_notebook.py#L15)

```python
add_cell()
```

Acrescente ao notebook a célula acumulada do aplicativo MAGI.

Lê current_lines e current_type do escopo do script; remove marcadores
de comentário para Markdown e conserva código em células próprias.
Ignora conteúdo vazio e modifica nb.cells, sem executar a célula.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `None`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `''.join(current_lines).strip`
- `''.join`
- `line.startswith`
- `md_lines.append`
- `nb.cells.append`
- `nbf.v4.new_markdown_cell`
- `''.join(md_lines).strip`
- `nbf.v4.new_code_cell`

## `MAGI/casper.py`

Atmospheric interpolation and moist-air physics in SI units.

Wind vectors use ENU; reported directions identify where wind comes from.
Humidity q is water mass / total moist-air mass, not the mixing ratio r.

### `MagiSchema.create_empty`

[Implementação: MAGI/casper.py:30](../../MAGI/casper.py#L30)

```python
MagiSchema.create_empty(num_rows=0)
```

Crie um DataFrame com o esquema atmosférico canônico.

Aloca num_rows linhas e as colunas declaradas em COLUMNS, inicialmente
sem valores. Retorna a tabela para preenchimento pelos produtores.

**Entradas e tipos declarados**

- `num_rows: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `pd.DataFrame(index=range(num_rows), columns=MagiSchema.COLUMNS)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `pd.DataFrame`
- `range`

### `MagiSchema.validate`

[Implementação: MAGI/casper.py:39](../../MAGI/casper.py#L39)

```python
MagiSchema.validate(df, *, allow_empty=False)
```

Verifique presença das colunas e consistência física básica de um perfil.

Exige grandezas finitas, pressão e temperatura positivas e umidade relativa
em [0, 100]. Perfil vazio só é aceito com allow_empty=True.
Retorna True em sucesso ou lança ValueError sem modificar df.

**Entradas e tipos declarados**

- `df: tipo não anotado; ver contrato acima`
- `allow_empty: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `True`

**Exceções lançadas explicitamente**

- `ValueError(f'Missing schema columns: {sorted(missing)}')`
- `ValueError('Atmospheric profile is empty')`
- `ValueError('Atmospheric profile contains missing or non-finite physical values')`
- `ValueError('Pressure and absolute temperature must be positive')`
- `ValueError('Relative humidity must be in [0, 100]')`

**Colaboradores chamados diretamente**

- `set`
- `ValueError`
- `sorted`
- `df[MagiSchema.REQUIRED_PHYSICS].to_numpy`
- `np.isfinite(values).all`
- `np.isfinite`
- `np.any`

### `CasperPhysics.calc_vapor_pressure`

[Implementação: MAGI/casper.py:69](../../MAGI/casper.py#L69)

```python
CasperPhysics.calc_vapor_pressure(temp_k)
```

Saturation vapour pressure over liquid water, in hPa (Bolton form).

**Entradas e tipos declarados**

- `temp_k: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `6.112 * np.exp(17.67 * temp_c / (temp_c + 243.5))`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `np.asarray`
- `np.exp`

### `CasperPhysics.calc_specific_humidity`

[Implementação: MAGI/casper.py:75](../../MAGI/casper.py#L75)

```python
CasperPhysics.calc_specific_humidity(pressure_pa, temp_k, rh_pct)
```

Calcule umidade específica q em kg de vapor por kg de ar úmido.

Recebe pressão em Pa, temperatura em K e umidade relativa em %.
Converte pressão de saturação de hPa para Pa e aplica
q = epsilon*e / (p - (1-epsilon)*e). Rejeita p <= 0, RH fora de [0,100]
ou pressão de vapor que alcance a pressão total.

**Entradas e tipos declarados**

- `pressure_pa: tipo não anotado; ver contrato acima`
- `temp_k: tipo não anotado; ver contrato acima`
- `rh_pct: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `epsilon * e / (p - (1 - epsilon) * e)`

**Exceções lançadas explicitamente**

- `ValueError('Invalid pressure / relative humidity / vapour pressure')`

**Colaboradores chamados diretamente**

- `np.asarray`
- `CasperPhysics.calc_vapor_pressure`
- `np.any`
- `ValueError`

### `CasperPhysics.calc_rh_from_specific_humidity`

[Implementação: MAGI/casper.py:92](../../MAGI/casper.py#L92)

```python
CasperPhysics.calc_rh_from_specific_humidity(pressure_pa, temp_k, q)
```

Recupere umidade relativa em % a partir de q, pressão Pa e temperatura K.

Inverte a relação de umidade específica e divide a pressão parcial
pela saturação. Rejeita q fora de [0,1); não corta supersaturação,
que deve ser avaliada explicitamente pelo chamador.

**Entradas e tipos declarados**

- `pressure_pa: tipo não anotado; ver contrato acima`
- `temp_k: tipo não anotado; ver contrato acima`
- `q: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `100 * e / (100 * CasperPhysics.calc_vapor_pressure(temp_k))`

**Exceções lançadas explicitamente**

- `ValueError('Specific humidity must be in [0, 1)')`

**Colaboradores chamados diretamente**

- `np.asarray`
- `np.any`
- `ValueError`
- `CasperPhysics.calc_vapor_pressure`

### `CasperPhysics.virtual_temperature`

[Implementação: MAGI/casper.py:108](../../MAGI/casper.py#L108)

```python
CasperPhysics.virtual_temperature(temp_k, q)
```

Calcule temperatura virtual em K para a equação do ar úmido.

Usa Tv = T * (1 + (1/epsilon - 1)*q), com q em kg/kg.
Aceita escalares ou arrays compatíveis por broadcasting NumPy.

**Entradas e tipos declarados**

- `temp_k: tipo não anotado; ver contrato acima`
- `q: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `np.asarray(temp_k) * (1 + (1 / CasperPhysics.EPSILON - 1) * np.asarray(q))`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `np.asarray`

### `CasperPhysics.calc_density`

[Implementação: MAGI/casper.py:117](../../MAGI/casper.py#L117)

```python
CasperPhysics.calc_density(pressure_pa, temp_k, rh_pct)
```

Calcule densidade do ar úmido em kg/m³ pela equação de estado.

Deriva q de pressão Pa, temperatura K e RH %, obtém Tv
e retorna p/(R_ar*Tv). Propaga erros do cálculo de umidade.

**Entradas e tipos declarados**

- `pressure_pa: tipo não anotado; ver contrato acima`
- `temp_k: tipo não anotado; ver contrato acima`
- `rh_pct: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `np.asarray(pressure_pa) / (CasperPhysics.R_AIR * CasperPhysics.virtual_temperature(temp_k, q))`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `CasperPhysics.calc_specific_humidity`
- `np.asarray`
- `CasperPhysics.virtual_temperature`

### `CasperPhysics.speed_dir_to_uv`

[Implementação: MAGI/casper.py:127](../../MAGI/casper.py#L127)

```python
CasperPhysics.speed_dir_to_uv(speed, direction_from)
```

Converta vento meteorológico para componentes leste/norte em m/s.

Recebe velocidade e direção de origem em graus; usa u=-V*sin(theta)
e v=-V*cos(theta). Retorna o par (u,v), escalar ou vetorizado.

**Entradas e tipos declarados**

- `speed: tipo não anotado; ver contrato acima`
- `direction_from: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `(-speed * np.sin(angle), -speed * np.cos(angle))`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `np.radians`
- `np.sin`
- `np.cos`

### `CasperPhysics.uv_to_speed_dir`

[Implementação: MAGI/casper.py:137](../../MAGI/casper.py#L137)

```python
CasperPhysics.uv_to_speed_dir(u, v)
```

Converta componentes ENU em velocidade e direção meteorológica de origem.

Usa hypot(u,v) e atan2(-u,-v); normaliza o ângulo para [0,360).
Retorna (velocidade m/s, direção graus), preservando a forma dos arrays.

**Entradas e tipos declarados**

- `u: tipo não anotado; ver contrato acima`
- `v: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `(np.hypot(u, v), (np.degrees(np.arctan2(-u, -v)) + 360) % 360)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `np.hypot`
- `np.degrees`
- `np.arctan2`

### `CasperPhysics.calc_shear`

[Implementação: MAGI/casper.py:146](../../MAGI/casper.py#L146)

```python
CasperPhysics.calc_shear(u, v, z)
```

Calcule a magnitude do gradiente vertical do vento horizontal em s⁻¹.

Recebe u e v em m/s e z em metros; combina gradientes NumPy por hypot.
Com menos de dois níveis, retorna NaN porque a derivada é indeterminada.

**Entradas e tipos declarados**

- `u: tipo não anotado; ver contrato acima`
- `v: tipo não anotado; ver contrato acima`
- `z: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `np.full_like(z, np.nan, dtype=float)`
- `np.hypot(np.gradient(u, z), np.gradient(v, z))`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `len`
- `np.full_like`
- `np.hypot`
- `np.gradient`

### `CasperPhysics.hydrostatic_diagnostic`

[Implementação: MAGI/casper.py:157](../../MAGI/casper.py#L157)

```python
CasperPhysics.hydrostatic_diagnostic(pressure_pa, density_kgm3, z_m)
```

Dimensionless residual at each level; unavailable derivatives are NaN.

**Entradas e tipos declarados**

- `pressure_pa: tipo não anotado; ver contrato acima`
- `density_kgm3: tipo não anotado; ver contrato acima`
- `z_m: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `np.full_like(z_m, np.nan, dtype=float)`
- `np.abs(np.gradient(pressure_pa, z_m) + rho_g) / rho_g`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `len`
- `np.full_like`
- `np.asarray`
- `np.abs`
- `np.gradient`

### `CasperProcessor.__init__`

[Implementação: MAGI/casper.py:171](../../MAGI/casper.py#L171)

```python
CasperProcessor.__init__(self, elevation_msl=450, surface_scenario='OPEN_TERRAIN')
```

Configure elevação MSL e hipótese explícita de rugosidade superficial.

Valida surface_scenario contra as opções conhecidas e armazena z0 em metros.
None proíbe extensão abaixo da primeira observação; cenário inválido gera erro.

**Entradas e tipos declarados**

- `elevation_msl: tipo não anotado; ver contrato acima`
- `surface_scenario: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- `ValueError(f'Unknown surface scenario: {surface_scenario}')`

**Colaboradores chamados diretamente**

- `ValueError`
- `self.SURFACE_ROUGHNESS.get`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `CasperProcessor.interpolate_profile`

[Implementação: MAGI/casper.py:183](../../MAGI/casper.py#L183)

```python
CasperProcessor.interpolate_profile(self, df_raw, altitude_grid)
```

PCHIP on a strictly increasing AGL grid, with no upper extrapolation.

Below the first observation, an explicitly selected surface scenario
uses neutral log wind, isothermal constant-q air and hydrostatic pressure.
These levels retain SYNTHETIC_SURFACE_LAYER flags. Set surface_scenario
to None to prohibit this approximation.

**Entradas e tipos declarados**

- `df_raw: tipo não anotado; ver contrato acima`
- `altitude_grid: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `MagiSchema.create_empty()`
- `grid`

**Exceções lançadas explicitamente**

- `ValueError('Altitude grid must contain at least two finite increasing levels')`
- `ValueError('Raw profile requires at least two complete finite levels')`
- `ValueError('Duplicate profile altitudes are ambiguous')`
- `ValueError('Pressure must be positive and decrease with altitude')`
- `ValueError('Absolute temperature must be positive')`
- `ValueError('Surface log-law requires nonnegative AGL and reference altitude above roughness')`
- `ValueError(f'A single vertical profile must have one {col}')`

**Colaboradores chamados diretamente**

- `np.asarray`
- `len`
- `np.isfinite(z).all`
- `np.isfinite`
- `np.any`
- `np.diff`
- `ValueError`
- `MagiSchema.create_empty`
- `df_raw.sort_values('altitude_agl_m').copy`
- `df_raw.sort_values`
- `raw[MagiSchema.REQUIRED_PHYSICS].to_numpy`
- `np.isfinite(values).all`
- `raw.altitude_agl_m.to_numpy`
- `raw.pressure_pa.to_numpy`
- `CasperPhysics.calc_specific_humidity`
- `PchipInterpolator(z_orig, raw[col], extrapolate=False)`
- `PchipInterpolator`
- `np.exp`
- `PchipInterpolator(z_orig, np.log(p_orig), extrapolate=False)`
- `np.log`
- `below.any`
- `np.maximum`
- `CasperPhysics.virtual_temperature`
- `CasperPhysics.calc_rh_from_specific_humidity`
- `self._derive`
- `raw[col].nunique`
- `np.isfinite(grid[MagiSchema.REQUIRED_PHYSICS].to_numpy(dtype=float)).all`
- `grid[MagiSchema.REQUIRED_PHYSICS].to_numpy`
- `np.full`
- `valid.sum`
- `CasperPhysics.hydrostatic_diagnostic`
- `np.convolve`
- `failures.astype`
- `np.ones`
- `dict`

### `CasperProcessor._derive`

[Implementação: MAGI/casper.py:254](../../MAGI/casper.py#L254)

```python
CasperProcessor._derive(grid)
```

Preencha grandezas derivadas de um perfil atmosférico interpolado.

Modifica grid com velocidade/direção do vento, q, densidade e cisalhamento.
Calcula gradiente somente onde há vento finito em pelo menos dois níveis.

**Entradas e tipos declarados**

- `grid: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `CasperPhysics.uv_to_speed_dir`
- `CasperPhysics.calc_specific_humidity`
- `CasperPhysics.calc_density`
- `np.isfinite`
- `valid.sum`
- `CasperPhysics.calc_shear`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `CasperProcessor.generate_synthetic_ensemble`

[Implementação: MAGI/casper.py:268](../../MAGI/casper.py#L268)

```python
CasperProcessor.generate_synthetic_ensemble(self, df_nominal, cov_matrix, altitude_grid, num_members=100, *, seed=None, rng=None)
```

Gaussian historical-variability scenarios, conditioned on valid moist air.

Invalid samples are rejected, never clipped. This conditional ensemble
does not retain exactly the input covariance and is not forecast-error
calibration. Pressure is integrated hydrostatically from the base level.

**Entradas e tipos declarados**

- `df_nominal: tipo não anotado; ver contrato acima`
- `cov_matrix: tipo não anotado; ver contrato acima`
- `altitude_grid: tipo não anotado; ver contrato acima`
- `num_members: tipo não anotado; ver contrato acima`
- `seed: tipo não anotado; ver contrato acima`
- `rng: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `members`

**Exceções lançadas explicitamente**

- `ValueError('Nominal profile and covariance grid must match exactly')`
- `ValueError('num_members must be a positive integer')`
- `ValueError('Pass seed or rng, not both')`
- `ValueError('Synthetic ensemble rejected too many unphysical samples; review covariance/model')`

**Colaboradores chamados diretamente**

- `MagiSchema.validate`
- `np.asarray`
- `len`
- `np.array_equal`
- `df_nominal.altitude_agl_m.to_numpy`
- `np.any`
- `np.diff`
- `ValueError`
- `isinstance`
- `np.random.default_rng`
- `covariance_factor`
- `np.concatenate`
- `df_nominal[col].to_numpy`
- `max`
- `float`
- `min`
- `rng.standard_normal`
- `np.all`
- `np.where`
- `CasperPhysics.virtual_temperature`
- `np.empty`
- `np.exp`
- `np.cumsum`
- `CasperPhysics.calc_rh_from_specific_humidity`
- `np.isfinite`
- `df_nominal.copy`
- `self._derive`
- `member.attrs.update`
- `members.append`

### `CasperVisuals.plot_painel`

[Implementação: MAGI/casper.py:359](../../MAGI/casper.py#L359)

```python
CasperVisuals.plot_painel(df_atual, df_stats)
```

Desenhe o painel simplificado dos perfis atmosféricos e históricos.

Usa df_atual e df_stats nas rotinas gráficas disponíveis; a visualização
não recalcula uma previsão nem modifica os dados de entrada.

**Entradas e tipos declarados**

- `df_atual: tipo não anotado; ver contrato acima`
- `df_stats: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `fig`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `plt.subplots`
- `zip`
- `ax.plot`
- `ax.set`
- `axes[1].plot`
- `axes[1].legend`
- `fig.tight_layout`

## `MAGI/covariance.py`

Covariance validation shared by both synthetic-ensemble interfaces.

### `covariance_factor`

[Implementação: MAGI/covariance.py:6](../../MAGI/covariance.py#L6)

```python
covariance_factor(covariance, size)
```

Return L with L L.T = covariance, rejecting indefinite input.

The eigensystem is evaluated in correlation coordinates, so roundoff
tolerances do not compare humidity variance with wind variance in SI.
Only eigenvalues within 1e-10 of zero (relative to the spectrum) may be
rounded to zero. This is a numerical tolerance, not physical regularization.

**Entradas e tipos declarados**

- `covariance: tipo não anotado; ver contrato acima`
- `size: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `factor`

**Exceções lançadas explicitamente**

- `ValueError(f'Covariance must be a finite ({size}, {size}) matrix')`
- `ValueError('Covariance has negative variances')`
- `ValueError('Zero-variance variables must have zero covariance')`
- `ValueError('Covariance must be symmetric')`
- `ValueError('Covariance is not positive semidefinite')`

**Colaboradores chamados diretamente**

- `np.asarray`
- `np.isfinite(cov).all`
- `np.isfinite`
- `ValueError`
- `np.diag`
- `np.any`
- `np.sqrt`
- `np.zeros_like`
- `active.any`
- `np.ix_`
- `np.outer`
- `np.allclose`
- `np.linalg.eigh`
- `max`
- `np.max`
- `np.abs`
- `eigenvalues.min`
- `np.maximum`

## `MAGI/exporter.py`

### `NetCDFExporter.export_magi_netcdf`

[Implementação: MAGI/exporter.py:7](../../MAGI/exporter.py#L7)

```python
NetCDFExporter.export_magi_netcdf(df_nominal, df_ensembles, df_stats, output_path, global_attrs)
```

Exports the MAGI data structures to a canonical NetCDF format via xarray.

**Entradas e tipos declarados**

- `df_nominal: tipo não anotado; ver contrato acima`
- `df_ensembles: tipo não anotado; ver contrato acima`
- `df_stats: tipo não anotado; ver contrato acima`
- `output_path: tipo não anotado; ver contrato acima`
- `global_attrs: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `None`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `pd.to_datetime([df_nominal['valid_time_utc'].iloc[0]]).tz_localize`
- `pd.to_datetime`
- `len`
- `np.full`
- `member_roles.append`
- `member_sources.append`
- `model_names.append`
- `enumerate`
- `np.arange`
- `np.interp`
- `xr.Dataset`
- `ds.to_netcdf`

## `MAGI/interface.py`

Validated interface between MAGI profiles and the flight-dynamics package.

### `_process_df_to_profile`

[Implementação: MAGI/interface.py:14](../../MAGI/interface.py#L14)

```python
_process_df_to_profile(frame, elevation, latitude, longitude)
```

Converta uma tabela MAGI em contrato atmosférico para a dinâmica de voo.

Valida o esquema e as flags de qualidade, extrai arrays em SI e preserva
origem, instante, membro e metadados. Retorna AtmosphericProfile, cuja
validação rejeita dados inválidos. latitude/longitude identificam o local;
elevação já foi aplicada ao eixo MSL durante a interpolação.

**Entradas e tipos declarados**

- `frame: tipo não anotado; ver contrato acima`
- `elevation: tipo não anotado; ver contrato acima`
- `latitude: tipo não anotado; ver contrato acima`
- `longitude: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `AtmosphericProfile(altitude_asl_m=frame.altitude_msl_m.to_numpy(dtype=float), pressure_pa=frame.pressure_pa.to_numpy(dtype=float), temperature_k=frame.temperature_k.to_numpy(dtype=float), wind_u_mps=frame.u_east_mps.to_numpy(dtype=float), wind_v_mps=frame.v_north_mps.to_numpy(dtype=float), source=value('data_source', 'unknown'), source_type=value('data_type', 'unknown'), model=value('model_name'), run_time_utc=value('generation_time_utc'), valid_time_utc=value('valid_time_utc'), latitude_deg=latitude, longitude_deg=longitude, member_id=value('ensemble_member'), specific_humidity_kg_kg=frame.specific_humidity_kg_kg.to_numpy(dtype=float), metadata=meta)`

**Exceções lançadas explicitamente**

- `ConfigurationError(f'MAGI profile rejected by quality control: {sorted(set(frame.quality_flag))}')`

**Colaboradores chamados diretamente**

- `MagiSchema.validate`
- `frame.quality_flag.isin(accepted).all`
- `frame.quality_flag.isin`
- `ConfigurationError`
- `sorted`
- `set`
- `str`
- `value`
- `AtmosphericProfile`
- `frame.altitude_msl_m.to_numpy`
- `frame.pressure_pa.to_numpy`
- `frame.temperature_k.to_numpy`
- `frame.u_east_mps.to_numpy`
- `frame.v_north_mps.to_numpy`
- `frame.specific_humidity_kg_kg.to_numpy`

### `_process_df_to_profile.value`

[Implementação: MAGI/interface.py:26](../../MAGI/interface.py#L26)

```python
_process_df_to_profile.value(column, default=None)
```

Leia o primeiro valor de um metadado do perfil.

Coluna ausente ou célula nula retorna default; caso contrário preserva
o valor registrado. A operação não preenche as séries físicas.

**Entradas e tipos declarados**

- `column: tipo não anotado; ver contrato acima`
- `default: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `default if pd.isna(item) else item`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `pd.isna`

### `get_atmospheric_ensemble`

[Implementação: MAGI/interface.py:63](../../MAGI/interface.py#L63)

```python
get_atmospheric_ensemble(latitude, longitude, elevation, target_date_str=None, time_window_minutes=120, time_step_minutes=10, *, cache_dir=None, surface_scenario='OPEN_TERRAIN', max_altitude_agl_m=6000, vertical_step_m=10, historical_years=None, historical_reference_year=None, model=None)
```

Return an atmospheric ensemble (multi-year historical archive or temporal scenarios).

**Entradas e tipos declarados**

- `latitude: tipo não anotado; ver contrato acima`
- `longitude: tipo não anotado; ver contrato acima`
- `elevation: tipo não anotado; ver contrato acima`
- `target_date_str: tipo não anotado; ver contrato acima`
- `time_window_minutes: tipo não anotado; ver contrato acima`
- `time_step_minutes: tipo não anotado; ver contrato acima`
- `cache_dir: tipo não anotado; ver contrato acima`
- `surface_scenario: tipo não anotado; ver contrato acima`
- `max_altitude_agl_m: tipo não anotado; ver contrato acima`
- `vertical_step_m: tipo não anotado; ver contrato acima`
- `historical_years: tipo não anotado; ver contrato acima`
- `historical_reference_year: tipo não anotado; ver contrato acima`
- `model: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `[_process_df_to_profile(processor.interpolate_profile(frame, grid), elevation, latitude, longitude) for frame in frames]`

**Exceções lançadas explicitamente**

- `ConfigurationError('MAGI vertical extent and step must be positive')`
- `ConfigurationError('MAGI returned no complete atmospheric profiles')`

**Colaboradores chamados diretamente**

- `ConfigurationError`
- `Path`
- `Balthasar`
- `balthasar.fetch_operational_forecast`
- `isinstance`
- `any`
- `np.unique`
- `np.arange`
- `CasperProcessor`
- `_process_df_to_profile`
- `processor.interpolate_profile`

### `get_atmospheric_profile`

[Implementação: MAGI/interface.py:90](../../MAGI/interface.py#L90)

```python
get_atmospheric_profile(latitude, longitude, elevation, target_date_str=None, *, cache_dir=None, surface_scenario='OPEN_TERRAIN', max_altitude_agl_m=6000, vertical_step_m=10, historical_years=None, historical_reference_year=None, model=None, **kwargs)
```

Return the nominal profile at the requested time (or representative historical reference year).

**Entradas e tipos declarados**

- `latitude: tipo não anotado; ver contrato acima`
- `longitude: tipo não anotado; ver contrato acima`
- `elevation: tipo não anotado; ver contrato acima`
- `target_date_str: tipo não anotado; ver contrato acima`
- `cache_dir: tipo não anotado; ver contrato acima`
- `surface_scenario: tipo não anotado; ver contrato acima`
- `max_altitude_agl_m: tipo não anotado; ver contrato acima`
- `vertical_step_m: tipo não anotado; ver contrato acima`
- `historical_years: tipo não anotado; ver contrato acima`
- `historical_reference_year: tipo não anotado; ver contrato acima`
- `model: tipo não anotado; ver contrato acima`
- `**kwargs: argumentos nomeados adicionais`

**Retornos/yields explícitos**

- `_process_df_to_profile(processor.interpolate_profile(frame, grid), elevation, latitude, longitude)`

**Exceções lançadas explicitamente**

- `ConfigurationError('MAGI vertical extent and step must be positive')`
- `ConfigurationError('MAGI returned an empty atmospheric profile')`

**Colaboradores chamados diretamente**

- `ConfigurationError`
- `Path`
- `Balthasar`
- `balthasar.fetch_operational_forecast`
- `isinstance`
- `np.unique`
- `np.arange`
- `CasperProcessor`
- `_process_df_to_profile`
- `processor.interpolate_profile`

## `MAGI/magi/__init__.py`

Módulo declarativo, ponto de entrada sem funções ou exportação de interfaces; não contém funções próprias.

## `MAGI/magi/casper/__init__.py`

Casper package exports used by MAGI applications and integrations.

Módulo declarativo, ponto de entrada sem funções ou exportação de interfaces; não contém funções próprias.

## `MAGI/magi/casper/ensemble/__init__.py`

Módulo declarativo, ponto de entrada sem funções ou exportação de interfaces; não contém funções próprias.

## `MAGI/magi/casper/ensemble/eof.py`

EOF (Empirical Orthogonal Functions) and Principal Component Analysis for MAGI.

Provides spectral decomposition and perturbation routines for vertical atmospheric
state vectors: [u(z), v(z), T(z), q(z)]^T.

### `compute_covariance`

[Implementação: MAGI/magi/casper/ensemble/eof.py:12](../../MAGI/magi/casper/ensemble/eof.py#L12)

```python
compute_covariance(df_nominal, altitude_grid)
```

Interface hook for covariance computation.

In the MAGI architecture, full climatological covariance estimation is performed
by MELCHIOR using Ledoit-Wolf shrinkage.

**Entradas e tipos declarados**

- `df_nominal: tipo não anotado; ver contrato acima`
- `altitude_grid: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `melchior.calculate_multivariate_covariance(df_nominal, altitude_grid)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `Melchior`
- `melchior.calculate_multivariate_covariance`

### `apply_eof_perturbation`

[Implementação: MAGI/magi/casper/ensemble/eof.py:27](../../MAGI/magi/casper/ensemble/eof.py#L27)

```python
apply_eof_perturbation(nominal_profile: Dict[str, np.ndarray], cov_matrix: Optional[np.ndarray], rng: np.random.Generator, nz: int, num_members: int) -> Optional[List[Tuple[np.ndarray, np.ndarray, np.ndarray, Optional[np.ndarray]]]]
```

Apply EOF/PCA-based stochastic perturbations to a nominal vertical atmospheric profile.

Perturbs state vector X = [u, v, T, q]^T (or [u, v, T]^T if 3-variable covariance is provided)
using the spectral decomposition of the covariance matrix:
    Sigma = V * Lambda * V^T
    perturbation = V * sqrt(Lambda) * xi,  where xi ~ N(0, I)

Parameters
----------
nominal_profile : dict
    Dictionary containing baseline 1D profiles for keys:
    - "u_wind": Eastward wind component (m/s), shape (nz,)
    - "v_wind": Northward wind component (m/s), shape (nz,)
    - "temperature": Absolute air temperature (K), shape (nz,)
    - "specific_humidity": (Optional) Specific humidity (kg/kg), shape (nz,)
cov_matrix : np.ndarray, optional
    Multivariate covariance matrix of shape (dim, dim), where dim >= 3 * nz.
    If dim >= 4 * nz, specific humidity perturbations are explicitly computed.
rng : np.random.Generator
    NumPy random number generator for reproducible sampling.
nz : int
    Number of vertical grid levels.
num_members : int
    Number of perturbed ensemble members to generate.

Returns
-------
list of tuple or None
    List of length `num_members`, where each entry is a tuple:
    (u_pert, v_pert, t_pert, q_pert) with shapes (nz,).
    If covariance is invalid or missing, returns None.

**Entradas e tipos declarados**

- `nominal_profile: Dict[str, np.ndarray]`
- `cov_matrix: Optional[np.ndarray]`
- `rng: np.random.Generator`
- `nz: int`
- `num_members: int`

**Retornos/yields explícitos**

- `None`
- `member_profiles`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `np.linalg.eigh`
- `np.maximum`
- `np.sqrt`
- `np.asarray`
- `nominal_profile.get`
- `np.zeros`
- `np.full`
- `rng.standard_normal`
- `range`
- `np.clip`
- `member_profiles.append`

## `MAGI/magi/casper/ensemble/generator.py`

Ensemble Cube Generator for MAGI and RocketPy.

Orchestrates synthetic 5D atmospheric ensemble cubes (member, time, pressure_level, latitude, longitude)
combining horizontal spatial tiling, isobaric vertical profiles, and EOF stochastic perturbations.

### `EnsembleGenerator.__init__`

[Implementação: MAGI/magi/casper/ensemble/generator.py:20](../../MAGI/magi/casper/ensemble/generator.py#L20)

```python
EnsembleGenerator.__init__(self, config: Optional[dict]=None)
```

Configure dimensões, grade e gerador aleatório do ensemble atmosférico.

Lê config opcional e os valores padrão do gerador. A semente controla
a reprodução das perturbações; os membros só são criados na geração.

**Entradas e tipos declarados**

- `config: Optional[dict]`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.config.get`
- `np.random.default_rng`
- `spatial.get`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `EnsembleGenerator._create_spatial_grid`

[Implementação: MAGI/magi/casper/ensemble/generator.py:42](../../MAGI/magi/casper/ensemble/generator.py#L42)

```python
EnsembleGenerator._create_spatial_grid(self, center_lat: float, center_lon: float)
```

Create local latitude and longitude coordinate arrays.

**Entradas e tipos declarados**

- `center_lat: float`
- `center_lon: float`

**Retornos/yields explícitos**

- `(lats, lons)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `np.arange`

### `EnsembleGenerator.create_empty_cube`

[Implementação: MAGI/magi/casper/ensemble/generator.py:48](../../MAGI/magi/casper/ensemble/generator.py#L48)

```python
EnsembleGenerator.create_empty_cube(self, times, lats, lons, members) -> xr.Dataset
```

Create an empty Atmospheric Ensemble Cube (xarray.Dataset) with CF metadata.

**Entradas e tipos declarados**

- `times: tipo não anotado; ver contrato acima`
- `lats: tipo não anotado; ver contrato acima`
- `lons: tipo não anotado; ver contrato acima`
- `members: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `ds`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `xr.Dataset`

### `EnsembleGenerator.generate_synthetic_ensemble`

[Implementação: MAGI/magi/casper/ensemble/generator.py:66](../../MAGI/magi/casper/ensemble/generator.py#L66)

```python
EnsembleGenerator.generate_synthetic_ensemble(self, nominal_profile: dict, cov_matrix: Optional[np.ndarray], center_lat: float, center_lon: float, valid_time: Union[pd.Timestamp, np.datetime64, datetime.datetime]) -> xr.Dataset
```

Generate a synthetic ensemble dataset from a nominal profile and a covariance matrix.

Parameters
----------
nominal_profile : dict
    Dictionary or DataFrame containing vertical profiles at `self.pressure_levels`.
cov_matrix : np.ndarray, optional
    Multivariate covariance matrix from reanalysis or historical data.
center_lat : float
    Launch site latitude in degrees.
center_lon : float
    Launch site longitude in degrees.
valid_time : Timestamp-like
    Valid time for the atmospheric forecast.

Returns
-------
xr.Dataset
    5D xarray Dataset containing variables: temperature, geopotential_height,
    u_wind, v_wind, and specific_humidity.

**Entradas e tipos declarados**

- `nominal_profile: dict`
- `cov_matrix: Optional[np.ndarray]`
- `center_lat: float`
- `center_lon: float`
- `valid_time: Union[pd.Timestamp, np.datetime64, datetime.datetime]`

**Retornos/yields explícitos**

- `ds`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self._create_spatial_grid`
- `np.arange`
- `self.create_empty_cube`
- `len`
- `np.zeros`
- `ds['temperature'].attrs.update`
- `ds['geopotential_height'].attrs.update`
- `ds['u_wind'].attrs.update`
- `ds['v_wind'].attrs.update`
- `ds['specific_humidity'].attrs.update`
- `SyntheticEnsembleGenerator`
- `generator.generate`
- `enumerate`

## `MAGI/magi/casper/ensemble/synthetic.py`

Synthetic atmospheric ensemble generation for MAGI in pressure coordinates.

Applies historical multivariate error statistics to nominal atmospheric profiles
while strictly preserving hydrostatic balance and moist-air buoyancy (virtual temperature).

### `SyntheticEnsembleGenerator.__init__`

[Implementação: MAGI/magi/casper/ensemble/synthetic.py:31](../../MAGI/magi/casper/ensemble/synthetic.py#L31)

```python
SyntheticEnsembleGenerator.__init__(self, rng: np.random.Generator, pressure_levels: Union[List[float], np.ndarray])
```

Inicialize o gerador com seu fluxo aleatório e níveis de pressão.

Armazena rng, converte pressure_levels para array numérico e registra
o número de níveis. A consistência física é avaliada na geração.

**Entradas e tipos declarados**

- `rng: np.random.Generator`
- `pressure_levels: Union[List[float], np.ndarray]`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `np.asarray`
- `len`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `SyntheticEnsembleGenerator.generate`

[Implementação: MAGI/magi/casper/ensemble/synthetic.py:41](../../MAGI/magi/casper/ensemble/synthetic.py#L41)

```python
SyntheticEnsembleGenerator.generate(self, nominal_profile: Dict[str, np.ndarray], cov_matrix: Optional[np.ndarray], num_members: int) -> List[Dict[str, np.ndarray]]
```

Generate `num_members` physically consistent vertical profile realizations.

Parameters
----------
nominal_profile : dict
    Baseline profile containing "u_wind", "v_wind", "temperature",
    "geopotential_height", and optionally "specific_humidity".
cov_matrix : np.ndarray, optional
    Multivariate covariance matrix from historical reanalysis (MELCHIOR).
num_members : int
    Number of ensemble members to generate.

Returns
-------
list of dict
    List of member dictionaries containing "u_wind", "v_wind", "temperature",
    "specific_humidity", and "geopotential_height" arrays of shape (nz,).

**Entradas e tipos declarados**

- `nominal_profile: Dict[str, np.ndarray]`
- `cov_matrix: Optional[np.ndarray]`
- `num_members: int`

**Retornos/yields explícitos**

- `members`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `apply_eof_perturbation`
- `np.asarray`
- `nominal_profile.get`
- `np.zeros`
- `np.full`
- `np.linspace`
- `len`
- `self._calculate_hydrostatic_height`
- `members.append`
- `np.arange`
- `np.exp`
- `np.abs`
- `np.linalg.cholesky`
- `np.eye`
- `range`
- `self.rng.standard_normal`
- `np.maximum`
- `np.clip`

### `SyntheticEnsembleGenerator._calculate_hydrostatic_height`

[Implementação: MAGI/magi/casper/ensemble/synthetic.py:116](../../MAGI/magi/casper/ensemble/synthetic.py#L116)

```python
SyntheticEnsembleGenerator._calculate_hydrostatic_height(self, h0: float, t_profile: np.ndarray, q_profile: Optional[np.ndarray]=None) -> np.ndarray
```

Calculate geopotential height using the hypsometric equation with virtual temperature.

Equation:
    dz = (Rd * Tv_layer / g0) * ln(p_lower / p_upper)
    Tv = T * (1 + 0.608 * q)

Supports both bottom-to-top (decreasing pressure) and top-to-bottom (increasing pressure)
vertical coordinates, preserving strict physical altitude monotonicity.

Parameters
----------
h0 : float
    Base geopotential height at level index 0 [m].
t_profile : np.ndarray
    Temperature profile [K], shape (nz,).
q_profile : np.ndarray, optional
    Specific humidity profile [kg/kg], shape (nz,).

Returns
-------
np.ndarray
    Hydrostatically integrated geopotential height profile [m], shape (nz,).

**Entradas e tipos declarados**

- `h0: float`
- `t_profile: np.ndarray`
- `q_profile: Optional[np.ndarray]`

**Retornos/yields explícitos**

- `np.full(self.nz, h0)`
- `hgt`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `np.asarray`
- `np.full`
- `np.empty`
- `np.maximum`
- `np.log`
- `np.cumsum`

## `MAGI/magi/casper/export/__init__.py`

Módulo declarativo, ponto de entrada sem funções ou exportação de interfaces; não contém funções próprias.

## `MAGI/magi/casper/export/rocketpy.py`

### `RocketPyEnsembleExporter.__init__`

[Implementação: MAGI/magi/casper/export/rocketpy.py:26](../../MAGI/magi/casper/export/rocketpy.py#L26)

```python
RocketPyEnsembleExporter.__init__(self, config=None)
```

Configure as opções do exportador de ensembles RocketPy.

Armazena config opcional para uso durante validação e exportação;
não cria arquivo NetCDF durante a inicialização.

**Entradas e tipos declarados**

- `config: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- Nenhuma ocorrência explícita no corpo local.

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `RocketPyEnsembleExporter.validate_dataset`

[Implementação: MAGI/magi/casper/export/rocketpy.py:34](../../MAGI/magi/casper/export/rocketpy.py#L34)

```python
RocketPyEnsembleExporter.validate_dataset(self, ds: xr.Dataset)
```

Validates the dataset for RocketPy compatibility and physical sanity.

**Entradas e tipos declarados**

- `ds: xr.Dataset`

**Retornos/yields explícitos**

- `True`

**Exceções lançadas explicitamente**

- `ValueError(f'Missing required dimensions: {missing_dims}')`
- `ValueError('pressure_level coordinate must be strictly monotonic')`
- `ValueError('latitude coordinate out of bounds [-90, 90]')`
- `ValueError(f'Missing required variable: {var}')`

**Colaboradores chamados diretamente**

- `set`
- `ValueError`
- `ds.pressure_level.to_index`
- `ds.latitude.min`
- `ds.latitude.max`
- `ds[var].isnull().any`
- `ds[var].isnull`
- `warnings.warn`

### `RocketPyEnsembleExporter.export`

[Implementação: MAGI/magi/casper/export/rocketpy.py:59](../../MAGI/magi/casper/export/rocketpy.py#L59)

```python
RocketPyEnsembleExporter.export(self, ensemble_ds: xr.Dataset, filename: str, naming: str='native')
```

Valide e grave um cubo atmosférico em NetCDF para RocketPy.

Recebe ensemble_ds e filename, verifica o contrato físico e escolhe
nomes de variáveis segundo naming. Preserva coordenadas e metadados;
falhas de validação ou escrita são propagadas.

**Entradas e tipos declarados**

- `ensemble_ds: xr.Dataset`
- `filename: str`
- `naming: str`

**Retornos/yields explícitos**

- `filename`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.validate_dataset`
- `ensemble_ds.copy`
- `rename_dict.items`
- `ds_out.rename`
- `ds_out.attrs.update`
- `datetime.datetime.now(datetime.UTC).isoformat`
- `datetime.datetime.now`
- `self.config.get`
- `ds_out.to_netcdf`

### `export_rocketpy_ensemble`

[Implementação: MAGI/magi/casper/export/rocketpy.py:109](../../MAGI/magi/casper/export/rocketpy.py#L109)

```python
export_rocketpy_ensemble(ensemble, output='MAGI_ensemble.nc', horizon_hours=168, timestep_hours=1)
```

Exports a list of MAGI DataFrames to a RocketPy-compatible NetCDF ensemble file.
It generates a temporal evolution over 'horizon_hours'.

**Entradas e tipos declarados**

- `ensemble: tipo não anotado; ver contrato acima`
- `output: tipo não anotado; ver contrato acima`
- `horizon_hours: tipo não anotado; ver contrato acima`
- `timestep_hours: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `exported_file`

**Exceções lançadas explicitamente**

- `ValueError('No ensemble members provided.')`
- `ValueError('Missing valid_time_utc in ensemble members.')`
- `ValueError(f'Expected multiple timestamps, got {len(t_vals)}')`
- `ValueError(f'Round-trip time validation failed. Expected {horizon_hours}h duration, got {total_duration_ns} ns')`
- `ValueError(f'Round-trip time step validation failed. Expected {timestep_hours}h, got {step_ns} ns')`

**Colaboradores chamados diretamente**

- `ValueError`
- `df0.dropna`
- `pd.to_datetime(df0['valid_time_utc'].iloc[0]).tz_localize`
- `pd.to_datetime`
- `int`
- `round`
- `pd.Timedelta`
- `pd.date_range`
- `len`
- `np.array`
- `np.zeros`
- `enumerate`
- `df.dropna`
- `xr.Dataset`
- `np.arange`
- `ds['temperature'].attrs.update`
- `ds['geopotential_height'].attrs.update`
- `ds['u_wind'].attrs.update`
- `ds['v_wind'].attrs.update`
- `base_time.isoformat`
- `RocketPyEnsembleExporter`
- `exporter.export`
- `xr.open_dataset`
- `np.timedelta64(t_vals[-1] - t_vals[0], 'ns').astype('timedelta64[ns]').astype`
- `np.timedelta64(t_vals[-1] - t_vals[0], 'ns').astype`
- `np.timedelta64`
- `abs`
- `np.timedelta64(t_vals[1] - t_vals[0], 'ns').astype('timedelta64[ns]').astype`
- `np.timedelta64(t_vals[1] - t_vals[0], 'ns').astype`

### `dataframes_to_rocketpy_dataset`

[Implementação: MAGI/magi/casper/export/rocketpy.py:221](../../MAGI/magi/casper/export/rocketpy.py#L221)

```python
dataframes_to_rocketpy_dataset(*args, **kwargs)
```

Rejeite a antiga interface de conversão de DataFrames.

Sempre lança DeprecationWarning como exceção, indicando ao chamador
que deve usar export_rocketpy_ensemble. Não converte dados nem grava arquivo.

**Entradas e tipos declarados**

- `*args: argumentos posicionais adicionais`
- `**kwargs: argumentos nomeados adicionais`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- `DeprecationWarning('Use export_rocketpy_ensemble instead.')`

**Colaboradores chamados diretamente**

- `DeprecationWarning`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

## `MAGI/magi/visualization.py`

### `_extract_launch_site_data`

[Implementação: MAGI/magi/visualization.py:8](../../MAGI/magi/visualization.py#L8)

```python
_extract_launch_site_data(dataset, latitude, longitude)
```

Selecione a coluna atmosférica mais próxima do local de lançamento.

Recebe dataset e coordenadas opcionais; resolve latitude/longitude
e retorna a seleção usada nos painéis, sem alterar o cubo original.

**Entradas e tipos declarados**

- `dataset: tipo não anotado; ver contrato acima`
- `latitude: tipo não anotado; ver contrato acima`
- `longitude: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `ds_loc`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `dataset.interp`
- `dataset.isel`

### `plot_ensemble_overview`

[Implementação: MAGI/magi/visualization.py:26](../../MAGI/magi/visualization.py#L26)

```python
plot_ensemble_overview(ensemble, latitude=None, longitude=None, selected_time=None, variable='wind_speed', altitude_max=30000, style='report', show_hodograph=False, show_cube=True)
```

Generate a publication-quality overview of the MAGI atmospheric ensemble.

**Entradas e tipos declarados**

- `ensemble: tipo não anotado; ver contrato acima`
- `latitude: tipo não anotado; ver contrato acima`
- `longitude: tipo não anotado; ver contrato acima`
- `selected_time: tipo não anotado; ver contrato acima`
- `variable: tipo não anotado; ver contrato acima`
- `altitude_max: tipo não anotado; ver contrato acima`
- `style: tipo não anotado; ver contrato acima`
- `show_hodograph: tipo não anotado; ver contrato acima`
- `show_cube: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `fig`

**Exceções lançadas explicitamente**

- `ValueError('u_wind and v_wind are required in dataset to compute wind_speed')`
- `ValueError(f"Variable '{variable}' not found in the dataset.")`
- `ValueError('No time dimension found in the dataset.')`

**Colaboradores chamados diretamente**

- `_extract_launch_site_data`
- `np.sqrt`
- `ValueError`
- `ds_loc['geopotential_height'].mean`
- `var_data.isel`
- `ds_loc['geopotential_height'].isel`
- `var_data.copy`
- `np.broadcast_to`
- `pd.to_datetime`
- `len`
- `(times - t0).total_seconds`
- `np.argmin`
- `np.abs`
- `plt.subplots`
- `_plot_panel_b`
- `fig.tight_layout`
- `plt.figure`
- `fig.add_subplot`
- `_plot_panel_a`
- `gridspec.GridSpec`
- `gs.update`
- `_add_inset_hodograph`
- `_plot_panel_c`
- `_add_metadata_header`

### `_plot_panel_a`

[Implementação: MAGI/magi/visualization.py:136](../../MAGI/magi/visualization.py#L136)

```python
_plot_panel_a(ax, var_data, z_data, time_hours, standalone=False)
```

Desenhe a evolução vertical e temporal da variável no painel A.

Usa var_data, z_data e time_hours para os elementos gráficos em ax.
standalone ajusta a apresentação; não gera novos dados meteorológicos.

**Entradas e tipos declarados**

- `ax: tipo não anotado; ver contrato acima`
- `var_data: tipo não anotado; ver contrato acima`
- `z_data: tipo não anotado; ver contrato acima`
- `time_hours: tipo não anotado; ver contrato acima`
- `standalone: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `len`
- `min`
- `np.linspace`
- `Normalize`
- `float`
- `var_data.min`
- `var_data.max`
- `plt.get_cmap`
- `z_data.isel`
- `var_data.isel`
- `np.nanmean`
- `np.meshgrid`
- `np.full_like`
- `ax.plot_surface`
- `cmap`
- `norm`
- `ax.set_xlim`
- `ax.set_ylim`
- `ax.set_zlim`
- `z_data.min`
- `z_data.max`
- `ax.set_xlabel`
- `ax.set_ylabel`
- `ax.set_zlabel`
- `ax.set_title`
- `ax.tick_params`
- `ax.zaxis.set_tick_params`
- `ax.view_init`
- `ax.grid`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `_plot_panel_b`

[Implementação: MAGI/magi/visualization.py:194](../../MAGI/magi/visualization.py#L194)

```python
_plot_panel_b(ax, var_data, z_data, sel_idx, variable)
```

Desenhe o perfil vertical dos membros no instante selecionado.

Seleciona sel_idx em var_data, usa z_data como altura e variable
para rótulos. Modifica ax e preserva os dados atmosféricos.

**Entradas e tipos declarados**

- `ax: tipo não anotado; ver contrato acima`
- `var_data: tipo não anotado; ver contrato acima`
- `z_data: tipo não anotado; ver contrato acima`
- `sel_idx: tipo não anotado; ver contrato acima`
- `variable: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `var_data.isel`
- `z_data.isel`
- `range`
- `ax.plot`
- `v_slice.isel`
- `z_slice.isel`
- `v_slice.quantile`
- `v_slice.median`
- `z_slice.mean`
- `ax.fill_betweenx`
- `Line2D`
- `ax.get_legend_handles_labels`
- `handles.insert`
- `labels.insert`
- `ax.legend`
- `variable.replace('_', ' ').capitalize`
- `variable.replace`
- `var_name.lower`
- `ax.set_xlabel`
- `ax.set_ylabel`
- `ax.set_title`
- `ax.spines['top'].set_visible`
- `ax.spines['right'].set_visible`
- `ax.grid`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `_plot_panel_c`

[Implementação: MAGI/magi/visualization.py:240](../../MAGI/magi/visualization.py#L240)

```python
_plot_panel_c(ax, var_data, z_data, time_hours, selected_time_hr, variable)
```

Desenhe a série temporal resumida da variável no painel C.

Usa os dados e a grade de tempo recebidos e marca selected_time_hr.
O gráfico representa a população existente, sem extrapolar previsões.

**Entradas e tipos declarados**

- `ax: tipo não anotado; ver contrato acima`
- `var_data: tipo não anotado; ver contrato acima`
- `z_data: tipo não anotado; ver contrato acima`
- `time_hours: tipo não anotado; ver contrato acima`
- `selected_time_hr: tipo não anotado; ver contrato acima`
- `variable: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `var_data.std`
- `z_data.mean`
- `np.meshgrid`
- `ax.pcolormesh`
- `plt.colorbar`
- `variable.replace('_', ' ').capitalize`
- `variable.replace`
- `cbar.set_label`
- `ax.axvline`
- `ax.text`
- `z_mean.max`
- `ax.set_xlabel`
- `ax.set_ylabel`
- `ax.set_title`
- `ax.spines['top'].set_visible`
- `ax.spines['right'].set_visible`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `_add_inset_hodograph`

[Implementação: MAGI/magi/visualization.py:269](../../MAGI/magi/visualization.py#L269)

```python
_add_inset_hodograph(ax, ds_loc, sel_idx, alt_mask)
```

Inclua um hodógrafo ENU no painel atmosférico.

Seleciona o instante sel_idx e os níveis alt_mask em ds_loc,
desenhando componentes de vento em eixos auxiliares de ax.

**Entradas e tipos declarados**

- `ax: tipo não anotado; ver contrato acima`
- `ds_loc: tipo não anotado; ver contrato acima`
- `sel_idx: tipo não anotado; ver contrato acima`
- `alt_mask: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `inset_axes`
- `ds_loc['u_wind'].isel`
- `ds_loc['v_wind'].isel`
- `ds_loc['geopotential_height'].isel`
- `u_slice.median`
- `v_slice.median`
- `z_slice.mean`
- `Normalize`
- `z_med.min`
- `z_med.max`
- `plt.get_cmap`
- `np.array([u_med, v_med]).T.reshape`
- `np.array`
- `np.concatenate`
- `LineCollection`
- `lc.set_array`
- `ax_ins.add_collection`
- `ax_ins.plot`
- `max`
- `np.nanmax`
- `np.abs`
- `np.isnan`
- `ax_ins.set_xlim`
- `ax_ins.set_ylim`
- `ax_ins.axhline`
- `ax_ins.axvline`
- `ax_ins.set_xticks`
- `ax_ins.set_yticks`
- `ax_ins.set_title`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `_add_metadata_header`

[Implementação: MAGI/magi/visualization.py:314](../../MAGI/magi/visualization.py#L314)

```python
_add_metadata_header(fig, ds_loc, lat, lon)
```

Inclua localização e proveniência no cabeçalho da figura.

Lê atributos de ds_loc e as coordenadas lat/lon e acrescenta textos
em fig. Metadados não disponíveis permanecem distintos de medições.

**Entradas e tipos declarados**

- `fig: tipo não anotado; ver contrato acima`
- `ds_loc: tipo não anotado; ver contrato acima`
- `lat: tipo não anotado; ver contrato acima`
- `lon: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `ds_loc.sizes.get`
- `ds_loc.attrs.get`
- `fig.text`
- `dict`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

## `MAGI/melchior.py`

### `Melchior.__init__`

[Implementação: MAGI/melchior.py:12](../../MAGI/melchior.py#L12)

```python
Melchior.__init__(self, cache_dir='dados_cache', elevation_msl=450)
```

Configure o diretório de climatologia e a elevação local em metros MSL.

Resolve cache relativo ao módulo e prepara caminhos de leitura;
a criação de climatologia sintética não ocorre implicitamente aqui.

**Entradas e tipos declarados**

- `cache_dir: tipo não anotado; ver contrato acima`
- `elevation_msl: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `os.path.isabs`
- `os.path.dirname`
- `os.path.abspath`
- `os.path.join`
- `os.makedirs`
- `print`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `Melchior.fetch_historical_data`

[Implementação: MAGI/melchior.py:28](../../MAGI/melchior.py#L28)

```python
Melchior.fetch_historical_data(self)
```

Leia a climatologia disponível com origem e qualidade identificadas.

Carrega o cache existente, converte unidades explicitamente e deriva
vento, umidade, densidade e cisalhamento por perfil. Ausência de cache
retorna esquema vazio; não transforma dados sintéticos em observações reais.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `MagiSchema.create_empty()`
- `df`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `print`
- `os.path.join`
- `os.path.exists`
- `MagiSchema.create_empty`
- `pd.read_csv`
- `len`
- `pd.to_datetime`
- `CasperPhysics.speed_dir_to_uv`
- `old_df.get`
- `CasperPhysics.calc_specific_humidity`
- `CasperPhysics.calc_density`
- `df.dropna`
- `df.groupby`
- `res.append`
- `calc_shear`
- `group.copy`
- `pd.concat`

### `Melchior.fetch_historical_data.calc_shear`

[Implementação: MAGI/melchior.py:77](../../MAGI/melchior.py#L77)

```python
Melchior.fetch_historical_data.calc_shear(group)
```

Calcule o cisalhamento dentro de um único perfil histórico.

Ordena o grupo por altitude e aplica gradientes às componentes ENU.
Retorna o grupo com a coluna derivada, sem unir datas diferentes.

**Entradas e tipos declarados**

- `group: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `group`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `group.sort_values('altitude_agl_m').drop_duplicates`
- `group.sort_values`
- `len`
- `CasperPhysics.calc_shear`

### `Melchior.select_worst_day`

[Implementação: MAGI/melchior.py:97](../../MAGI/melchior.py#L97)

```python
Melchior.select_worst_day(self, df_hist=None)
```

Analisa os perfis históricos e seleciona o pior dia — aquele com a combinação
mais severa de ventos fortes, alta umidade (indicativo de chuva/nuvens) e cisalhamento.

Retorna:
    df_worst: DataFrame no esquema MAGI com o perfil do pior dia
    worst_info: dict com metadados do dia selecionado (timestamp, scores)

**Entradas e tipos declarados**

- `df_hist: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `(MagiSchema.create_empty(), {})`
- `(df_worst, worst_info)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `print`
- `self.fetch_historical_data`
- `MagiSchema.create_empty`
- `df_hist.groupby`
- `group['wind_speed_mps'].max`
- `group['relative_humidity_pct'].max`
- `group['wind_shear_s_1'].max`
- `len`
- `group['altitude_agl_m'].idxmin`
- `min`
- `max`
- `df_hist[df_hist['valid_time_utc'] == worst_time].copy`

### `Melchior._aligned_profiles`

[Implementação: MAGI/melchior.py:161](../../MAGI/melchior.py#L161)

```python
Melchior._aligned_profiles(df_hist, altitude_grid)
```

Use one common grid for statistics and covariance; never extrapolate.

**Entradas e tipos declarados**

- `df_hist: tipo não anotado; ver contrato acima`
- `altitude_grid: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `profiles`

**Exceções lançadas explicitamente**

- `ValueError('Historical grid must contain finite increasing levels')`

**Colaboradores chamados diretamente**

- `np.asarray`
- `len`
- `np.isfinite(grid).all`
- `np.isfinite`
- `np.any`
- `np.diff`
- `ValueError`
- `df_hist.groupby`
- `raw.sort_values`
- `raw.altitude_agl_m.to_numpy`
- `np.isfinite(z).all`
- `pd.DataFrame`
- `np.interp`
- `raw[col].to_numpy`
- `set`
- `CasperPhysics.uv_to_speed_dir`
- `CasperPhysics.calc_shear`
- `CasperPhysics.calc_density`
- `CasperPhysics.calc_specific_humidity`
- `profiles.append`

### `Melchior.calc_stats_hist`

[Implementação: MAGI/melchior.py:187](../../MAGI/melchior.py#L187)

```python
Melchior.calc_stats_hist(self, df_hist, altitude_grid=None)
```

Calcule estatísticas históricas sobre uma única grade vertical comum.

Alinha perfis sem extrapolação e agrega média, desvio e percentis
por altitude. Retorna DataFrame de estatísticas; não completa cobertura ausente.

**Entradas e tipos declarados**

- `df_hist: tipo não anotado; ver contrato acima`
- `altitude_grid: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `pd.DataFrame()`
- `pd.DataFrame(rows)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `pd.DataFrame`
- `self._aligned_profiles`
- `pd.concat(profiles).groupby`
- `pd.concat`
- `group[variable].to_numpy`
- `np.isfinite`
- `len`
- `np.mean`
- `np.median`
- `np.percentile`
- `np.full`
- `zip`
- `CasperPhysics.uv_to_speed_dir`
- `rows.append`

### `Melchior.calculate_multivariate_covariance`

[Implementação: MAGI/melchior.py:221](../../MAGI/melchior.py#L221)

```python
Melchior.calculate_multivariate_covariance(self, df_hist, altitude_grid)
```

Historical variability of [u(z), v(z), T(z), q(z)] in SI.

Shrink the dimensionless correlation matrix, then restore each column's
empirical standard deviation. This preserves units and zero-variance
quantities. It does not turn climatological variability into forecast
error statistics. Only complete profiles spanning the grid contribute.

**Entradas e tipos declarados**

- `df_hist: tipo não anotado; ver contrato acima`
- `altitude_grid: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `(None, None)`
- `(mean, covariance)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self._aligned_profiles`
- `set`
- `np.concatenate`
- `profile[col].to_numpy`
- `np.isfinite(vector).all`
- `np.isfinite`
- `vectors.append`
- `len`
- `np.asarray`
- `samples.mean`
- `samples.std`
- `np.zeros`
- `active.any`
- `LedoitWolf(store_precision=False).fit`
- `LedoitWolf`
- `np.ix_`
- `np.outer`

### `MelchiorVisuals.plot_magnitude_vento`

[Implementação: MAGI/melchior.py:252](../../MAGI/melchior.py#L252)

```python
MelchiorVisuals.plot_magnitude_vento(df_stats)
```

Desenhe a magnitude histórica do vento por altitude.

Usa df_stats para representar perfil central e faixa de variabilidade
com unidades explícitas; não modifica a climatologia.

**Entradas e tipos declarados**

- `df_stats: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `fig`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `plt.subplots`
- `ax.plot`
- `ax.fill_betweenx`
- `ax.set_title`
- `ax.legend`

## `MAGI/scoring.py`

Exploratory atmospheric favorability score for aerospace and flight dynamics operations.

WARNING: This module provides atmospheric comparison and diagnostic ranking only.
It does NOT constitute launch authorization.

### `AtmosphericScoring.calculate_score`

[Implementação: MAGI/scoring.py:38](../../MAGI/scoring.py#L38)

```python
AtmosphericScoring.calculate_score(df_ensemble: List[pd.DataFrame], df_stats: pd.DataFrame, z_grid: Union[List[float], np.ndarray], *, operational_state: Optional[str]=None, calibration: Optional[dict]=None, weather_score: Optional[float]=None, data_quality_score: Optional[float]=None) -> Tuple[Optional[float], str]
```

Calculate the atmospheric favorability index.

Parameters
----------
df_ensemble : list of pd.DataFrame
    List of forecast profile DataFrames (must include nominal and/or ensemble members).
    Each DataFrame must contain 'altitude_agl_m', 'wind_speed_mps', 'wind_shear_s_1'.
df_stats : pd.DataFrame
    Historical climatology statistics indexed by or containing 'altitude_agl_m'
    with median, p90, and p99 columns for wind speed and wind shear.
z_grid : array-like
    Target vertical altitude grid AGL [m].
operational_state : str, optional
    Operational pipeline state from StateManager.
calibration : dict, optional
    Calibration dict containing 'spread_limits_mps' (3 strictly increasing floats).
weather_score : float, optional
    Precipitation / convective weather quality input (0..10, default 5.0).
data_quality_score : float, optional
    Data provenance / sensor quality input (0..10, default 5.0).

Returns
-------
score : float or None
    Composite favorability score from 0.0 to 100.0 (None if unavailable).
score_class : str
    Diagnostic classification string ("EXPLORATORY_ATMOSPHERIC_INDEX" or
    "ATMOSPHERIC_SCORE_UNAVAILABLE").

**Entradas e tipos declarados**

- `df_ensemble: List[pd.DataFrame]`
- `df_stats: pd.DataFrame`
- `z_grid: Union[List[float], np.ndarray]`
- `operational_state: Optional[str]`
- `calibration: Optional[dict]`
- `weather_score: Optional[float]`
- `data_quality_score: Optional[float]`

**Retornos/yields explícitos**

- `unavailable`
- `(score, 'EXPLORATORY_ATMOSPHERIC_INDEX')`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `len`
- `all`
- `np.isfinite`
- `np.asarray`
- `mask.any`
- `np.array_equal`
- `frame.altitude_agl_m.to_numpy`
- `frame.loc[mask, 'quality_flag'].isin(accepted_flags).all`
- `frame.loc[mask, 'quality_flag'].isin`
- `frame.wind_speed_mps.to_numpy`
- `frame.wind_shear_s_1.to_numpy`
- `np.isfinite(wind).all`
- `np.isfinite(shear).all`
- `winds.append`
- `shears.append`
- `df_stats.set_index('altitude_agl_m').reindex`
- `df_stats.set_index`
- `df_stats.reindex`
- `float`
- `np.exp`
- `np.sum`
- `set`
- `stats[columns].to_numpy`
- `np.isfinite(values).all`
- `np.any`
- `np.diff`
- `np.percentile`
- `np.empty`
- `range`
- `np.interp`
- `np.min`
- `calibration.get`
- `np.isfinite(limits).all`
- `np.clip`

## `MAGI/state_manager.py`

Track acquisition freshness without renewing cache age on reads.

### `StateManager.__init__`

[Implementação: MAGI/state_manager.py:20](../../MAGI/state_manager.py#L20)

```python
StateManager.__init__(self, cache_dir='dados_cache')
```

Prepare o caminho dos metadados de estado da aquisição meteorológica.

Armazena cache_dir e cria somente o diretório pai de cache_meta.json.
A inicialização não marca os dados como recentes.

**Entradas e tipos declarados**

- `cache_dir: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `str`
- `Path`
- `self.metadata_path.parent.mkdir`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `StateManager._read_metadata`

[Implementação: MAGI/state_manager.py:30](../../MAGI/state_manager.py#L30)

```python
StateManager._read_metadata(self)
```

Leia os metadados persistidos sem renovar o instante de aquisição.

Retorna dict vazio se o arquivo não existe, não pode ser lido ou tem JSON
inválido. A avaliação posterior trata ausência como informação indisponível.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `{}`
- `json.loads(self.metadata_path.read_text())`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.metadata_path.exists`
- `json.loads`
- `self.metadata_path.read_text`

### `StateManager.write_metadata`

[Implementação: MAGI/state_manager.py:43](../../MAGI/state_manager.py#L43)

```python
StateManager.write_metadata(self, meta)
```

Publique os metadados de estado por substituição de arquivo.

Serializa meta em um temporário vizinho e substitui cache_meta.json
após a escrita. Erros de escrita são propagados.

**Entradas e tipos declarados**

- `meta: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.metadata_path.with_suffix`
- `temporary.write_text`
- `json.dumps`
- `temporary.replace`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `StateManager._utc`

[Implementação: MAGI/state_manager.py:54](../../MAGI/state_manager.py#L54)

```python
StateManager._utc(value)
```

Converta uma data ISO 8601 com offset para datetime UTC.

Aceita o sufixo Z; rejeita datas sem timezone com ValueError.
O resultado permite comparar cobertura e idade sem misturar fusos.

**Entradas e tipos declarados**

- `value: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `date.astimezone(datetime.UTC)`

**Exceções lançadas explicitamente**

- `ValueError('State timestamps require explicit timezone')`

**Colaboradores chamados diretamente**

- `datetime.datetime.fromisoformat`
- `str(value).replace`
- `str`
- `ValueError`
- `date.astimezone`

### `StateManager.evaluate_state`

[Implementação: MAGI/state_manager.py:65](../../MAGI/state_manager.py#L65)

```python
StateManager.evaluate_state(self, is_online=False, fetch_success=False, is_real_ensemble=False, variables_complete=False, valid_time_utc=None, *, available_valid_times=None, has_climatology=False, retrieved_at_utc=None)
```

Only a complete successful acquisition can advance the update time.

Valid-time coverage must be supplied independently of the requested date.
Reads and degraded/incomplete acquisitions never make old data fresh.

**Entradas e tipos declarados**

- `is_online: tipo não anotado; ver contrato acima`
- `fetch_success: tipo não anotado; ver contrato acima`
- `is_real_ensemble: tipo não anotado; ver contrato acima`
- `variables_complete: tipo não anotado; ver contrato acima`
- `valid_time_utc: tipo não anotado; ver contrato acima`
- `available_valid_times: tipo não anotado; ver contrato acima`
- `has_climatology: tipo não anotado; ver contrato acima`
- `retrieved_at_utc: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `{'operational_state': state, 'state_reason': reason, 'cache_age_hours': age, 'last_successful_update_utc': meta.get('last_successful_update_utc', ''), 'requested_valid_time_utc': requested.isoformat()}`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `datetime.datetime.now`
- `self._read_metadata`
- `self._utc`
- `meta.get`
- `len`
- `requested.isoformat`
- `any`
- `abs`
- `(requested - self._utc(value)).total_seconds`
- `meta.update`
- `retrieved.isoformat`
- `self._utc(value).isoformat`
- `bool`
- `self.write_metadata`
- `(now - self._utc(meta['last_successful_update_utc'])).total_seconds`
- `float`

## `MAGI/visuals.py`

### `LayoutReport.__init__`

[Implementação: MAGI/visuals.py:23](../../MAGI/visuals.py#L23)

```python
LayoutReport.__init__(self, fig)
```

Inicialize o diagnóstico de sobreposição para uma figura Matplotlib.

Armazena fig e listas vazias de textos registrados e problemas
de layout. Não desenha nem salva a figura nesta etapa.

**Entradas e tipos declarados**

- `fig: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- Nenhuma ocorrência explícita no corpo local.

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `LayoutReport.register_text`

[Implementação: MAGI/visuals.py:33](../../MAGI/visuals.py#L33)

```python
LayoutReport.register_text(self, text_obj, name)
```

Registre um objeto de texto para verificar colisões no layout.

Acrescenta text_obj e seu identificador name à lista de caixas.
A extensão gráfica será calculada após desenhar o canvas.

**Entradas e tipos declarados**

- `text_obj: tipo não anotado; ver contrato acima`
- `name: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.bboxes.append`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `LayoutReport.check_collisions`

[Implementação: MAGI/visuals.py:41](../../MAGI/visuals.py#L41)

```python
LayoutReport.check_collisions(self)
```

Detecte sobreposição de textos de grupos conceituais distintos.

Desenha o canvas, obtém caixas em pixels e compara todos os pares
de caixas registradas. Acrescenta descrições em issues; objetos
sem extensão gráfica utilizável são ignorados neste diagnóstico visual.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- `(len(self.issues) == 0, report, self.issues)`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `self.fig.canvas.draw`
- `self.fig.canvas.get_renderer`
- `item['obj'].get_window_extent`
- `boxes.append`
- `range`
- `len`
- `n1.split`
- `n2.split`
- `self.issues.append`
- `any`

### `VisualManager._ensure_dir`

[Implementação: MAGI/visuals.py:85](../../MAGI/visuals.py#L85)

```python
VisualManager._ensure_dir()
```

Garanta o diretório de saída das figuras MAGI.

Cria os pais necessários sem remover arquivos existentes.
Retorna conforme o contrato interno; erros do sistema são propagados.

**Entradas e tipos declarados**

- Nenhuma ocorrência explícita no corpo local.

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `os.makedirs`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `VisualManager.save_figure`

[Implementação: MAGI/visuals.py:94](../../MAGI/visuals.py#L94)

```python
VisualManager.save_figure(fig, base_name, report_obj)
```

Salve a figura e o diagnóstico de layout com identificação temporal.

Usa base_name para organizar saídas e report_obj para registrar problemas.
A rotina escreve arquivos de visualização; não modifica perfis físicos.

**Entradas e tipos declarados**

- `fig: tipo não anotado; ver contrato acima`
- `base_name: tipo não anotado; ver contrato acima`
- `report_obj: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- Nenhuma ocorrência explícita no corpo local.

**Exceções lançadas explicitamente**

- `ValueError('Layout collision detected. See report.')`

**Colaboradores chamados diretamente**

- `VisualManager._ensure_dir`
- `report_obj.check_collisions`
- `print`
- `ValueError`
- `datetime.datetime.now(datetime.UTC).strftime`
- `datetime.datetime.now`
- `os.path.join`
- `fig.savefig`
- `fig.get_facecolor`
- `shutil.copyfile`

Sem `return`/`yield` local: o retorno implícito é `None` (se a função terminar normalmente).

### `_friendly_model_name`

[Implementação: MAGI/visuals.py:158](../../MAGI/visuals.py#L158)

```python
_friendly_model_name(raw_name)
```

Convert internal model identifiers to human-readable display names.

**Entradas e tipos declarados**

- `raw_name: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `_MODEL_DISPLAY_NAMES[raw_name]`
- `raw_name.replace('_', ' ').title() if raw_name else 'Unknown'`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `raw_name.replace('_', ' ').title`
- `raw_name.replace`

### `_friendly_timestamp`

[Implementação: MAGI/visuals.py:165](../../MAGI/visuals.py#L165)

```python
_friendly_timestamp(ts)
```

Convert a timestamp to human-readable format: '21 Jul 2026, 18:20 BRT | 21:20 UTC'.

**Entradas e tipos declarados**

- `ts: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `str(ts)`
- `f"{ts_brt.strftime('%d %b %Y')}, {brt_str} | {ts_utc.strftime('%H:%M UTC')}"`
- `utc_str`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `isinstance`
- `pd.Timestamp`
- `str`
- `hasattr`
- `ts.tz_convert`
- `ts_utc.strftime`
- `pd.Timedelta`
- `datetime.timedelta`
- `ts_brt.strftime`

### `CasperVisualsV3._create_title_axes`

[Implementação: MAGI/visuals.py:191](../../MAGI/visuals.py#L191)

```python
CasperVisualsV3._create_title_axes(fig, gridspec_slot, title, subtitle, report, wrap_width=50)
```

Create a subplot with a dedicated title row and caption row above the plot area.

Captions are word-wrapped to `wrap_width` characters to prevent overflow into
neighbouring axes.

**Entradas e tipos declarados**

- `fig: tipo não anotado; ver contrato acima`
- `gridspec_slot: tipo não anotado; ver contrato acima`
- `title: tipo não anotado; ver contrato acima`
- `subtitle: tipo não anotado; ver contrato acima`
- `report: tipo não anotado; ver contrato acima`
- `wrap_width: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `ax_plot`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `gridspec.GridSpecFromSubplotSpec`
- `fig.add_subplot`
- `ax_text.axis`
- `'\n'.join`
- `textwrap.wrap`
- `ax_text.text`
- `report.register_text`
- `ax_plot.set_facecolor`
- `ax_plot.grid`
- `ax_plot.spines.values`
- `spine.set_color`
- `ax_plot.tick_params`

### `CasperVisualsV3.plot_magi_operational_panorama`

[Implementação: MAGI/visuals.py:219](../../MAGI/visuals.py#L219)

```python
CasperVisualsV3.plot_magi_operational_panorama(df_nominal, df_ensembles, df_stats, score_info, state_info, is_example=False)
```

Gere o painel integrado de atmosfera, climatologia e estado dos dados.

Recebe perfil nominal, membros, estatísticas, score_info e state_info;
desenha vento, cisalhamento, termodinâmica, mapa e proveniência.
is_example identifica a visualização ilustrativa. Imagens cartográficas
são opcionais; a rotina salva figuras e diagnóstico de layout.

**Entradas e tipos declarados**

- `df_nominal: tipo não anotado; ver contrato acima`
- `df_ensembles: tipo não anotado; ver contrato acima`
- `df_stats: tipo não anotado; ver contrato acima`
- `score_info: tipo não anotado; ver contrato acima`
- `state_info: tipo não anotado; ver contrato acima`
- `is_example: tipo não anotado; ver contrato acima`

**Retornos/yields explícitos**

- `fig`

**Exceções lançadas explicitamente**

- Nenhuma ocorrência explícita no corpo local.

**Colaboradores chamados diretamente**

- `MAGI_PALETTE.copy`
- `plt.style.use`
- `plt.figure`
- `LayoutReport`
- `fig.subplots_adjust`
- `gridspec.GridSpec`
- `gridspec.GridSpecFromSubplotSpec`
- `fig.add_subplot`
- `ax_logo.axis`
- `MAGI_LOGO_PATH.exists`
- `Image.open(MAGI_LOGO_PATH).convert`
- `Image.open`
- `np.array`
- `logo_arr[:, :, 3].min`
- `int`
- `logo_img.resize`
- `OffsetImage`
- `AnnotationBbox`
- `ax_logo.add_artist`
- `print`
- `ax_ht.axis`
- `ax_ht.text`
- `report.register_text`
- `ax_hm.axis`
- `_friendly_timestamp`
- `state_info.get`
- `score_info.get`
- `df_nominal.get`
- `_friendly_model_name`
- `op_state_raw.replace('_', ' ').title`
- `op_state_raw.replace`
- `ax_hm.text`
- `len`
- `CasperVisualsV3._create_title_axes`
- `ax_wind.fill_betweenx`
- `ax_wind.plot`
- `np.nanpercentile`
- `ax_wind.set_ylabel`
- `ax_wind.set_xlabel`
- `ax_wind.set_ylim`
- `ax_wind.legend`
- `plt.setp`
- `ax_uv.get_yticklabels`
- `ax_uv.axvline`
- `ax_uv.set_ylim`
- `ax_uv.plot`
- `ax_uv.fill_betweenx`
- `ax_uv.text`
- `dict`
- `ax_uv.set_xlabel`
- `ax_uv.legend`
- `ax_shear.get_yticklabels`
- `ax_shear.set_ylim`
- `ax_shear.plot`
- `ax_shear.fill_betweenx`
- `np.nanmax`
- `np.nanargmax`
- `ax_shear.text`
- `ax_shear.set_xlabel`
- `ax_shear.legend`
- `pd.Timestamp`
- `datetime.datetime.now`
- `pd.Timedelta`
- `range`
- `np.sin`
- `np.linspace`
- `h.strftime`
- `enumerate`
- `ax_bar.bar`
- `ax_bar.plot`
- `ax_bar.set_xticks`
- `ax_bar.set_xticklabels`
- `ax_bar.set_ylabel`
- `ax_bar.set_xlabel`
- `patches.Patch`
- `zip`
- `ax_bar.legend`
- `ax_temp.get_yticklabels`
- `ax_temp.set_ylim`
- `ax_temp.plot`
- `ax_temp.fill_betweenx`
- `ax_temp.set_xlabel`
- `ax_temp.text`
- `ax_temp.legend`
- `ax_r_leg.axis`
- `ax_r_leg.text`
- `np.arange`
- `np.radians`
- `np.abs(z_grid - alt).argmin`
- `np.abs`
- `np.isnan`
- `np.random.seed`
- `np.histogram`
- `np.random.normal`
- `max`
- `hist_freq.max`
- `hist_ens.max`
- `ax_t.axis`
- `ax_t.text`
- `ax_r.set_facecolor`
- `ax_r.set_xticks`
- `ax_r.set_xticklabels`
- `ax_r.tick_params`
- `ax_r.grid`
- `ax_r.spines.values`
- `spine.set_color`
- `ax_r.bar`
- `ax_r.plot`
- `ax_r.set_theta_zero_location`
- `ax_r.set_theta_direction`
- `ax_r.set_rmax`
- `ax_r.set_yticks`
- `ax_d.axis`
- `ax_d.text`
- `ax_cards.axis`
- `df_nominal['cloud_cover_pct'].isna().all`
- `df_nominal['cloud_cover_pct'].isna`
- `float`
- `df_nominal['relative_humidity_pct'].isna().all`
- `df_nominal['relative_humidity_pct'].isna`
- `np.clip`
- `patches.Rectangle`
- `ax_cards.add_patch`
- `ax_cards.text`
- `ax_prov.axis`
- `ax_prov.text`
- `ax_cape.text`
- `ax_cape.set_xticks`
- `ax_cape.set_yticks`
- `ax_cloud.text`
- `ax_cloud.set_xticks`
- `ax_cloud.set_yticks`
- `ax_map.axis`
- `math.radians`
- `math.asinh`
- `math.tan`
- `Image.new`
- `requests.get`
- `open`
- `f.write`
- `img_map.paste`
- `Image.open(temp_osm).convert`
- `os.remove`
- `np.zeros`
- `np.indices`
- `np.sqrt`
- `np.random.rand`
- `(radar_sim[..., 3] * (0.8 + 0.2 * noise)).astype`
- `Image.fromarray`
- `ax_map.text`
- `(noise_oct * 255).astype`
- `n_img.resize`
- `n_img.filter`
- `ImageFilter.GaussianBlur`
- `np.array(n_img).astype`
- `cloud_noise.min`
- `cloud_noise.max`
- `np.percentile`
- `(alpha_raw * max_alpha).astype`
- `r_radar.json`
- `radar_json.get`
- `datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc).strftime`
- `datetime.datetime.fromtimestamp`
- `radar_map.paste`
- `Image.open(temp_radar).convert`
- `(radar_data[..., 3] * 0.7).astype`
- `ax_map.imshow`
- `ax_map.set_xlim`
- `ax_map.set_ylim`
- `ax_map.scatter`
- `ax_map.annotate`
- `ax_map.inset_axes`
- `compass_ax.axis`
- `compass_ax.add_patch`
- `patches.Circle`
- `compass_ax.arrow`
- `math.cos`
- `math.sin`
- `cbar_ax.set_xlim`
- `cbar_ax.set_yticks`
- `np.linspace(0, 70, 256).reshape`
- `cbar_ax.imshow`
- `cbar_ax.set_xticks`
- `cbar_ax.set_xticklabels`
- `cbar_ax.tick_params`
- `cbar_ax.set_xlabel`
- `cbar_ax.spines.values`
- `ax_fl.axis`
- `datetime.datetime.now(datetime.UTC).strftime`
- `ax_fl.text`
- `ax_fc.axis`
- `ax_fc.text`
- `ax_fr.axis`
- `ax_fr.text`
- `item['obj'].get_text`
- `item['obj'].set_text`
- `VisualManager.save_figure`
- `MAGI_PALETTE.update`
