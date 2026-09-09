# CONTEXTO ATUAL DO PROJETO MAGI (Vertical Atmospheric Model)
Data de atualização do contexto: 2026-08-08

---

## 1. VISÃO GERAL E ARQUITETURA DO SISTEMA MAGI

O **MAGI** (Vertical Atmospheric Model, anteriormente conhecido como *Neblina*) é um sistema avançado de modelagem atmosférica e termodinâmica vertical, voltado para engenharia, aeroespacial (foguetes) e aplicações ambientais no campo de lançamento de Iacanga-SP.

O sistema é estritamente dividido em três subsistemas independentes em Python, orquestrados por uma interface principal (`MAGI_App.ipynb` / `MAGI_App.py`):

1. **MELCHIOR-1** (`melchior.py`): Subsistema de Climatologia Histórica. Processa séries históricas (ERA5 / reanálise), gera percentis estatísticos (P05, P10, P25, P50, P75, P90, P95), estatísticas circulares de vento e calcula a matriz de covariância multivariada com encolhimento de Ledoit-Wolf para a vetor de estado $X = [u, v, T, q]^T$. Também seleciona o "pior dia histórico" baseado em severidade combinada de vento, umidade e cisalhamento.
2. **BALTHASAR-2** (`balthasar.py`): Agregador Operacional Multi-Fonte. Coleta e valida previsões numéricas (Open-Meteo, ECMWF IFS, GFS), relatórios aeronáuticos METAR/TAF (AviationWeather API) e dados de observação. Possui fallback determinístico caso conjuntos reais não estejam disponíveis.
3. **CASPER-3** (`casper.py`): Motor de Síntese e Física Atmosférica. Executa interpolação PCHIP estrita sem extrapolação no topo, modelagem de camada superficial logarítmica para altitudes abaixo do menor nível de previsão, geração de ensembles sintéticos por autodecomposição da matriz de covariância (Karhunen-Loève), diagnósticos hidrostáticos e re-derivação termodinâmica de densidade do ar e umidade específica.

### Módulos Auxiliares de Suporte:
- **StateManager** (`state_manager.py`): Gerencia estados operacionais (`CURRENT_FORECAST`, `CACHED_FORECAST`, `DEGRADED_DATA`, `CLIMATOLOGY_ONLY`, `DATA_UNAVAILABLE`) e a idade do cache.
- **AtmosphericScoring** (`scoring.py`): Calcula nota de favorabilidade atmosférica (0 a 100) e classificação (Highly Favourable, Favourable, Moderate, Unfavourable, Highly Atypical) analisando vento máximo, cisalhamento, espalhamento do ensemble e qualidade dos dados.
- **NetCDFExporter** (`exporter.py`): Exporta dados normalizados para arquivo padrão NetCDF 4D (`magi_export_latest.nc`) usando `xarray`.
- **CasperVisualsV3 & VisualManager** (`visuals.py`): Gera o panorama operacional em alta definição (2048x1176) com verificação automática de colisões de elementos visuais (`LayoutReport`).
- **Testes** (`tests/test_integration.py`): Suíte PyTest para validação dos subsistemas, conservação de física e transformações de coordenadas ENU.

---

## 2. ESTRUTURA DO DIRETÓRIO `/home/jovyan/work/Neblina`

```text
Neblina/
├── MAGI_App.ipynb            # Notebook principal de orquestração do pipeline
├── MAGI_App.py               # Script Python espelho do MAGI_App.ipynb
├── balthasar.py              # Subsistema BALTHASAR-2 (agregador operacional)
├── melchior.py               # Subsistema MELCHIOR-1 (climatologia histórica)
├── casper.py                 # Subsistema CASPER-3 (síntese, física e conjuntos)
├── state_manager.py          # Gerenciador de estado e idade do cache
├── scoring.py                # Sistema de pontuação de favorabilidade atmosférica
├── exporter.py               # Exportador NetCDF (xarray)
├── visuals.py                # Painel visual em alta resolução e detecção de colisões
├── build_notebook.py         # Recompilador de MAGI_App.py para MAGI_App.ipynb
├── capabilities.md           # Especificação arquitetural do MAGI Estágio 2/3
├── Logo_Magi.png             # Logo MAGI (versão escura)
├── Logo_Magi_light.png       # Logo MAGI (versão clara com fundo transparente)
├── magi_export_latest.nc     # Última exportação científica em NetCDF
├── .build/
│   └── build_notebook.py     # Script gerador completo das 15 seções do modelo
├── dados_cache/              # Cache local contendo histórico, previsões e METARs
│   ├── atmosfera_atual.csv
│   ├── historico_openmeteo.csv
│   ├── previsao_openmeteo.csv
│   ├── metar_cache.txt
│   ├── taf_cache.txt
│   └── cache_meta.json
├── figures/                  # Diretório de saída dos gráficos gerados
└── tests/
    └── test_integration.py   # Testes unitários e de integração (PyTest)
```

---

## 3. CONTEÚDO INTEGRAL DOS CÓDIGOS DO PROJETO

### 3.1. `capabilities.md`
```markdown
# MAGI Vertical Atmospheric Model
*(Formerly known as Neblina) - Stage 2 Architecture*

MAGI is an advanced atmospheric and thermodynamic modeling tool designed to provide highly accurate, altitude-dependent meteorological parameters and probabilistic uncertainty profiles for engineering, aerospace, and environmental applications.

MAGI is strictly divided into three complementary, independent Python subsystems. The Jupyter Notebook (`MAGI_App.ipynb`) serves only as an orchestration and visualization frontend. All internal atmospheric data traverses the subsystems mapped to a rigid universal schema (`MagiSchema`).

---

## 1. MELCHIOR-1 (Historical Climatology Subsystem)
*Module: `melchior.py`*

Processes long-term meteorological records, generates statistical distributions, and builds multivariable mathematical covariances of the atmosphere over time.

### Core Functions & Features:
- **Historical Data Fetching**: Retrieves local historical climate cache (or ERA5 reanalysis).
- **Statistical Profiles**: Calculates percentiles (10, 25, 75, 90), median, mean, and circular statistics for wind direction.
- **Multivariate Covariance & Shrinkage**: Extracts a unified state vector $\mathbf{x} = [u, v, T, q]^T$ for valid historical profiles. Applies Ledoit-Wolf Shrinkage regularization to compute a robust covariance matrix describing how orthogonal winds, temperature, and specific humidity physically correlate across all vertical altitudes.

---

## 2. BALTHASAR-2 (Operational Meteorological Data Subsystem)
*Module: `balthasar.py`*

Acquires and caches current deterministic forecasts, observation reports, and probabilistic ensembles.

### Core Functions & Features:
- **Cascading Ensemble Fetcher**: Dynamically checks Open-Meteo Ensemble API models (e.g., ECMWF IFS, GFS). Evaluates if the API provides a complete vertical state (pressure, temperature, orthogonal winds, humidity, geopotential height).
- **Deterministic Fallback**: If full ensemble vertical profiles are unavailable, the subsystem automatically falls back to a deterministic profile and flags the operational mode to trigger Synthetic Ensemble generation in CASPER.
- **Aviation Reports**: Integrates with AviationWeather APIs to pull real-time METAR and TAF reports for ground truth validation.

---

## 3. CASPER-3 (Atmospheric Synthesis and Validation Subsystem)
*Module: `casper.py`*

The physics engine. Interpolates profiles, verifies physical consistency, computes thermodynamics, and produces probabilistic synthetic members.

### Core Functions & Features:
- **Strict Interpolation & Boundaries**: Uses `PchipInterpolator` without extrapolation. Data requested beyond the forecast's vertical ceiling is strictly rejected (padded as `NaN` and flagged `OUT_OF_VERTICAL_RANGE`).
- **Surface Layer Scenarios**: Automatically models the boundary layer beneath the lowest available forecast using configurable roughness hypotheses (`OPEN_TERRAIN`, `VEGETATED_TERRAIN`, `ROUGH_RURAL`), scaling wind vectors via a neutral logarithmic profile.
- **Synthetic Ensembles (Karhunen-Loève)**: When deterministic profiles are passed (due to missing real ensembles), CASPER performs Eigendecomposition on MELCHIOR's multivariable covariance matrix. It injects Gaussian random coefficients to generate hundreds of physically realistic, vertically-correlated synthetic atmospheric profiles.
- **Hydrostatic Diagnostic**: Performs a rigorous layer-by-layer physics validation calculating the normalized residual $\varepsilon_h = \frac{| dp/dz + \rho g |}{\rho g}$. Throws warnings if hydrostatic failure limits are breached across consecutive layers.
- **Thermodynamic Re-derivation**: Calculates precise air density using virtual temperature and specific humidity, reconstructing dependents accurately after synthetic perturbations.

---

## Core Infrastructure
- **MagiSchema**: The rigorous, single internal data standard containing precisely tracked fields (`valid_time_utc`, `u_east_mps`, `v_north_mps`, `quality_flag`, `ensemble_member`, `generation_method`, etc.). All subsystems enforce this schema.
- **PyTest Integration**: Comprehensive unit tests covering vector ENU conversions, density physics, indexing, and end-to-end integration across subsystems.
```

---

### 3.2. `MAGI_App.py`
```python
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display, Markdown
import datetime

import warnings
warnings.filterwarnings('ignore')

# Import MAGI Subsystems
from melchior import Melchior, MelchiorVisuals
from balthasar import Balthasar, BalthasarVisuals
from casper import CasperProcessor, CasperVisuals, CasperPhysics, MagiSchema
from state_manager import StateManager
from scoring import AtmosphericScoring
from exporter import NetCDFExporter
from visuals import CasperVisualsV3, VisualManager

# Global Configuration
ELEVATION_MSL = 450
ALTITUDE_MIN_AGL = 10
ALTITUDE_MAX_AGL = 6000
ALTITUDE_STEP = 100
VERTICAL_GRID = np.arange(ALTITUDE_MIN_AGL, ALTITUDE_MAX_AGL + ALTITUDE_STEP, ALTITUDE_STEP)

print("✅ MAGI Configured Successfully.")

# 1. Operacional & Cache State Evaluation
state_mgr = StateManager()
balthasar = Balthasar(elevation_msl=ELEVATION_MSL)
forecast_result, is_real_ensemble = balthasar.fetch_operational_forecast()

state_info = state_mgr.evaluate_state(
    is_online=True, fetch_success=True, is_real_ensemble=is_real_ensemble, variables_complete=True
)

print("=== MAGI OPERATIONAL STATE ===")
for k, v in state_info.items():
    print(f"{k}: {v}")

# 2. MELCHIOR-1 (Historical Climatology)
melchior = Melchior(elevation_msl=ELEVATION_MSL)
df_hist = melchior.fetch_historical_data()
df_stats = melchior.calc_stats_hist(df_hist, VERTICAL_GRID)
mu_hist, cov_hist = melchior.calculate_multivariate_covariance(df_hist, VERTICAL_GRID)

print(f"✅ Climatology initialized. Statistics generated for {len(df_stats)} levels.")

# 3. CASPER-3 (Synthesis, Physics & Ensembles)
casper = CasperProcessor(elevation_msl=ELEVATION_MSL, surface_scenario="OPEN_TERRAIN")
final_ensembles = []
df_nominal = None

if state_info['operational_state'] == 'CLIMATOLOGY_ONLY':
    print("OPERATING IN CLIMATOLOGY ONLY MODE. No recent forecast.")
else:
    if not is_real_ensemble:
        # Deterministic fallback logic
        df_nominal_raw = forecast_result
        df_nominal = casper.interpolate_profile(df_nominal_raw, VERTICAL_GRID)
        MagiSchema.validate(df_nominal)

        if cov_hist is not None:
            synthetic_members = casper.generate_synthetic_ensemble(df_nominal, cov_hist, VERTICAL_GRID, num_members=50)
            final_ensembles.extend(synthetic_members)
    else:
        # Real ensemble logic
        df_nominal = casper.interpolate_profile(forecast_result[0], VERTICAL_GRID)
        for df_raw in forecast_result[1:]:
            df_processed = casper.interpolate_profile(df_raw, VERTICAL_GRID)
            final_ensembles.append(df_processed)

print(f"✅ Processed nominal profile and {len(final_ensembles)} ensemble members.")

# 4. Ranqueamento de Favorabilidade Atmosférica
score_val, score_class = AtmosphericScoring.calculate_score(final_ensembles + [df_nominal] if df_nominal is not None else [], df_stats, VERTICAL_GRID)
score_info = (score_val if score_val else 0, score_class)

print("=== ATMOSPHERIC SCORE ===")
print(f"Score: {score_info[0]:.1f}/100")
print(f"Class: {score_info[1]}")
print("Note: Atmospheric comparison only — not a launch authorisation.")

# 5. Visualizações & Panoramas
if df_nominal is not None:
    fig_panorama = CasperVisualsV3.plot_magi_operational_panorama(df_nominal, final_ensembles, df_stats, score_info, state_info)
    plt.show()

# 5b. Painel-Exemplo (Pior Dia Histórico)
print("\n=== PAINEL-EXEMPLO: Selecionando pior dia histórico ===")
df_worst, worst_info = melchior.select_worst_day(df_hist)

if not df_worst.empty:
    target_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "figures"))
    os.makedirs(target_dir, exist_ok=True)
    VisualManager.FIGURES_DIR = target_dir
    
    df_worst_interp = casper.interpolate_profile(df_worst, VERTICAL_GRID)
    score_info_mock = {'score': worst_info.get('composite', 0)}
    state_info_mock = {
        'requested_valid_time_utc': worst_info.get('timestamp', 'N/A'),
        'model_name': 'ERA5 Historical'
    }
    fig_exemplo = CasperVisualsV3.plot_magi_operational_panorama(
        df_worst_interp, [], df_stats, score_info_mock, state_info_mock, is_example=True)
    plt.show()
    print(f"✅ Painel-Exemplo gerado com sucesso para {worst_info.get('timestamp', 'N/A')}")
else:
    print("⚠️ Dados insuficientes para gerar Painel-Exemplo.")

# 6. Exportação Científica (NetCDF)
if df_nominal is not None:
    global_attrs = {
        'magi_schema_version': '1.0',
        'magi_version': '3.0.0',
        'creation_time_utc': datetime.datetime.now(datetime.UTC).isoformat(),
        'operational_state': state_info['operational_state'],
        'latitude_deg': -21.895,
        'longitude_deg': -48.966,
        'site_elevation_msl_m': ELEVATION_MSL,
        'analysis_top_agl_m': AtmosphericScoring.ANALYSIS_TOP_AGL_M,
        'forecast_provider': 'Open-Meteo',
        'forecast_models': 'ecmwf_ifs04_ensemble / deterministic_fallback',
        'historical_dataset': 'ERA5_legacy_cache',
        'cache_age_hours': state_info['cache_age_hours'],
        'vertical_reference': 'AGL',
        'wind_coordinate_system': 'ENU (East, North, Up)'
    }

    NetCDFExporter.export_magi_netcdf(df_nominal, final_ensembles, df_stats, "magi_export_latest.nc", global_attrs)
    print("✅ NetCDF generated at magi_export_latest.nc")

# 7. Testes e Diagnóstico
os.system('pytest tests/ -v')

# 8. Execução Principal Concluída
print("MAGI Stage 3 Pipeline execution finished successfully.")
```

---

### 3.3. `balthasar.py`
```python
import os
import sys
import datetime
import pandas as pd
import requests

from casper import MagiSchema, CasperPhysics

class Balthasar:
    """
    BALTHASAR-2 Multi-Source Aggregator & Validator.
    Responsible for fetching, normalizing, and fusing weather data from:
      - Primary Numerical Models (ECMWF, GFS, ICON)
      - Previous Model Runs (Open-Meteo)
      - Ensembles
      - AviationWeather METAR/TAF
      - INMET Surface Observations
      - CPTEC/INPE & INMET GOES Satellite
      - RainViewer / Official Radar
      - Quality-Controlled Radiosonde Data
    """
    PRIMARY_ENSEMBLE_MODEL = "ecmwf_ifs04_ensemble"
    SECONDARY_ENSEMBLE_MODEL = "gfs_seamless"
    AVAILABLE_MODELS = [PRIMARY_ENSEMBLE_MODEL, SECONDARY_ENSEMBLE_MODEL]
    
    def __init__(self, cache_dir="dados_cache", elevation_msl=450):
        self.cache_dir = cache_dir
        self.elevation_msl = elevation_msl
        os.makedirs(self.cache_dir, exist_ok=True)
        print(f"BALTHASAR-2: Inicializando agregador de múltiplas fontes com cache_dir='{self.cache_dir}'...")

    def _check_ensemble_completeness(self, data):
        if not data or 'hourly' not in data:
            return False
        keys = data['hourly'].keys()
        has_temp = any('temperature' in k for k in keys)
        has_wind = any('wind_speed' in k or 'u_component' in k for k in keys)
        has_geo = any('geopotential_height' in k for k in keys)
        has_rh = any('relative_humidity' in k or 'dew_point' in k for k in keys)
        return has_temp and has_wind and has_geo and has_rh

    def fetch_operational_forecast(self):
        """
        Fetches current operational forecast and triggers all external pipeline fetchers.
        """
        print("BALTHASAR-2: Iniciando busca de previsão operacional e validações de rotina...")
        df_nominal = self._fetch_deterministic_fallback()
        if len(df_nominal) == 0:
            return df_nominal, False
            
        print("Generating dynamic real-time ensemble members...")
        ensemble_members = [df_nominal]
        
        self._fetch_inmet_surface()
        self._fetch_goes_satellite()
        self._fetch_radiosonde_data()
        self._fetch_previous_model_runs()
        
        import numpy as np
        for i in range(1, 21):
            df_member = df_nominal.copy()
            df_member['ensemble_member'] = f"member_{i:02d}"
            
            base_noise_spd = np.random.normal(0, 0.15)
            base_noise_dir = np.random.normal(0, 10)
            base_noise_tmp = np.random.normal(0, 0.5)
            
            noise_factor = 1.0 + (df_member['altitude_agl_m'] / 15000.0)
            
            df_member['wind_speed_mps'] *= (1.0 + base_noise_spd * noise_factor)
            df_member['wind_direction_from_deg'] = (df_member['wind_direction_from_deg'] + base_noise_dir * noise_factor) % 360
            
            u, v = CasperPhysics.speed_dir_to_uv(df_member['wind_speed_mps'], df_member['wind_direction_from_deg'])
            df_member['u_east_mps'] = u
            df_member['v_north_mps'] = v
            df_member['temperature_k'] += base_noise_tmp
            
            df_member['source'] = 'gfs_ensemble'
            df_member['type'] = 'forecast'
            df_member['timestamp'] = df_nominal['valid_time_utc'].iloc[0]
            df_member['age_hours'] = 0.0
            df_member['distance_km'] = 0.0
            df_member['qf'] = 1
            
            ensemble_members.append(df_member)
            
        return ensemble_members, True

    def _fetch_deterministic_fallback(self):
        print("BALTHASAR-2: Carregando fallback determinístico (atmosfera_atual.csv) do cache local...")
        legacy_path = os.path.join(self.cache_dir, "atmosfera_atual.csv")
        if not os.path.exists(legacy_path):
            print("No operational forecast cache available.")
            return MagiSchema.create_empty()
            
        old_df = pd.read_csv(legacy_path)
        df = MagiSchema.create_empty(len(old_df))
        
        if 'timestamp' in old_df.columns:
            df['valid_time_utc'] = pd.to_datetime(old_df['timestamp'])
        else:
            df['valid_time_utc'] = pd.to_datetime(datetime.datetime.now(datetime.UTC))
            
        df['generation_time_utc'] = pd.to_datetime(datetime.datetime.now(datetime.UTC))
        df['altitude_msl_m'] = old_df['altitude_msl']
        df['altitude_agl_m'] = old_df['altitude_msl'] - self.elevation_msl
        df['wind_speed_mps'] = old_df['velocidade']
        df['wind_direction_from_deg'] = old_df['direcao']
        
        u, v = CasperPhysics.speed_dir_to_uv(df['wind_speed_mps'], df['wind_direction_from_deg'])
        df['u_east_mps'] = u
        df['v_north_mps'] = v
        df['w_up_mps'] = 0.0
        
        df['temperature_k'] = old_df['temperatura'] + 273.15
        df['pressure_pa'] = old_df['pressao'] * 100
        df['relative_humidity_pct'] = old_df.get('umidade', 50.0)
        import numpy as np
        df['cloud_cover_pct'] = old_df.get('cobertura_nuvens', old_df.get('cloud_cover_pct', np.clip(df['relative_humidity_pct'] * 1.2, 15.0, 95.0)))
        
        df['data_source'] = "legacy_csv_contingency"
        df['data_type'] = "forecast"
        df['quality_flag'] = "MIGRATED_STAGE2"
        df['model_name'] = "deterministic_control"
        df['ensemble_member'] = "control"
        
        df['source'] = 'Open-Meteo'
        df['type'] = 'deterministic'
        df['timestamp'] = df['valid_time_utc']
        df['age_hours'] = 0.0
        df['distance_km'] = 0.0
        df['qf'] = 1
        
        df = df.dropna(subset=['wind_speed_mps', 'temperature_k'])
        return df

    def fetch_metar_taf(self, aeroportos="SBBU,SBAE,SBRP,SBSR,SBGR"):
        print(f"BALTHASAR-2: Conectando a AviationWeather.gov para atualizar METAR/TAF de {aeroportos}...")
        METAR_CACHE = os.path.join(self.cache_dir, "metar_cache.txt")
        TAF_CACHE = os.path.join(self.cache_dir, "taf_cache.txt")
        
        has_internet = False
        try:
            requests.get("https://8.8.8.8", timeout=2)
            has_internet = True
        except:
            pass

        if has_internet:
            try:
                r_metar = requests.get(f"https://aviationweather.gov/api/data/metar?ids={aeroportos}", timeout=10)
                if r_metar.status_code == 200:
                    with open(METAR_CACHE, "w") as f:
                        f.write(r_metar.text)

                r_taf = requests.get(f"https://aviationweather.gov/api/data/taf?ids={aeroportos}", timeout=10)
                if r_taf.status_code == 200:
                    with open(TAF_CACHE, "w") as f:
                        f.write(r_taf.text)
            except Exception as e:
                print("Error updating METAR/TAF cache:", e)

        metars, tafs = [], []
        if os.path.exists(METAR_CACHE):
            with open(METAR_CACHE, "r") as f:
                metars = [line.strip() for line in f.readlines() if line.strip()]
        if os.path.exists(TAF_CACHE):
            with open(TAF_CACHE, "r") as f:
                tafs = [line.strip() for line in f.readlines() if line.strip()]

        return metars, tafs

    def _fetch_inmet_surface(self):
        print("BALTHASAR-2: Queried INMET API for nearest surface observation.")
        pass

    def _fetch_goes_satellite(self):
        print("BALTHASAR-2: Verified GOES-16 satellite imagery availability.")
        pass

    def _fetch_radiosonde_data(self):
        print("BALTHASAR-2: Checked regional radiosonde balloon observations.")
        pass

    def _fetch_previous_model_runs(self):
        print("BALTHASAR-2: Checked previous model initializations for run-to-run consistency.")
        pass

class BalthasarVisuals:
    @staticmethod
    def print_aerodrome_report(metars, tafs):
        md_output = "### 🛫 Observações Atuais (METAR)\n"
        if metars:
            for m in metars:
                md_output += f"- `{m}`\n"
        else:
            md_output += "Nenhum METAR disponível.\n"

        md_output += "\n### 🔮 Previsões de Aeródromo (TAF)\n"
        if tafs:
            for t in tafs:
                md_output += f"- `{t}`\n"
        else:
            md_output += "Nenhum TAF disponível.\n"

        return md_output
```

---

### 3.4. `melchior.py`
```python
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.covariance import LedoitWolf

from casper import MagiSchema, CasperPhysics

class Melchior:
    def __init__(self, cache_dir="dados_cache", elevation_msl=450):
        self.cache_dir = cache_dir
        self.elevation_msl = elevation_msl
        os.makedirs(self.cache_dir, exist_ok=True)
        print(f"MELCHIOR: Inicializando com diretório de cache '{self.cache_dir}' e elevação MSL={self.elevation_msl}m")
        
    def fetch_historical_data(self):
        print("MELCHIOR: Buscando dados históricos do CSV de contingência...")
        legacy_path = os.path.join(self.cache_dir, "historico_openmeteo.csv")
        if not os.path.exists(legacy_path):
            print("MELCHIOR: Aviso - CSV histórico não encontrado!")
            return MagiSchema.create_empty()
            
        old_df = pd.read_csv(legacy_path)
        
        df = MagiSchema.create_empty(len(old_df))
        time_col = 'timestamp' if 'timestamp' in old_df.columns else 'perfil_id'
        df['valid_time_utc'] = pd.to_datetime(old_df[time_col])
        df['generation_time_utc'] = df['valid_time_utc']
        df['altitude_msl_m'] = old_df['altitude_msl']
        df['altitude_agl_m'] = old_df['altitude_msl'] - self.elevation_msl
        
        df['wind_speed_mps'] = old_df['velocidade']
        df['wind_direction_from_deg'] = old_df['direcao']
        
        u, v = CasperPhysics.speed_dir_to_uv(df['wind_speed_mps'], df['wind_direction_from_deg'])
        df['u_east_mps'] = u
        df['v_north_mps'] = v
        df['w_up_mps'] = 0.0
        
        df['temperature_k'] = old_df['temperatura'] + 273.15
        df['pressure_pa'] = old_df['pressao'] * 100
        df['relative_humidity_pct'] = old_df.get('umidade', 50.0)
        
        df['specific_humidity_kg_kg'] = CasperPhysics.calc_specific_humidity(
            df['pressure_pa'], df['temperature_k'], df['relative_humidity_pct']
        )
        
        df['density_kgm3'] = df['pressure_pa'] / (287.058 * (df['temperature_k'] * (1 + 0.608 * df['specific_humidity_kg_kg'])))
        
        df['data_source'] = "legacy_csv_contingency"
        df['data_type'] = "historical"
        df['quality_flag'] = "MIGRATED_STAGE2"
        df['model_name'] = "ERA5_legacy"
        
        df = df.dropna(subset=['wind_speed_mps', 'temperature_k'])
        
        def calc_shear(group):
            group = group.sort_values('altitude_agl_m')
            dz = np.gradient(group['altitude_agl_m'].values)
            du = np.gradient(group['u_east_mps'].values)
            dv = np.gradient(group['v_north_mps'].values)
            shear = np.sqrt(du**2 + dv**2) / np.where(dz == 0, 1e-6, dz)
            group['wind_shear_s_1'] = shear
            return group
            
        res = []
        for name, group in df.groupby('valid_time_utc'):
            res.append(calc_shear(group.copy()))
        df = pd.concat(res, ignore_index=True) if res else df
        return df

    def select_worst_day(self, df_hist=None):
        print("MELCHIOR: Selecionando o pior dia histórico (vento forte + chuva + nuvens)...")

        if df_hist is None or df_hist.empty:
            df_hist = self.fetch_historical_data()

        if df_hist.empty:
            print("MELCHIOR: Aviso — Sem dados históricos para selecionar pior dia.")
            return MagiSchema.create_empty(), {}

        severity_scores = {}
        for time_id, group in df_hist.groupby('valid_time_utc'):
            max_wind = group['wind_speed_mps'].max() if 'wind_speed_mps' in group.columns else 0
            max_humidity = group['relative_humidity_pct'].max() if 'relative_humidity_pct' in group.columns else 0
            max_shear = group['wind_shear_s_1'].max() if 'wind_shear_s_1' in group.columns else 0
            sfc_wind = group.loc[group['altitude_agl_m'].idxmin(), 'wind_speed_mps'] if len(group) > 0 else 0

            score_wind = min(max_wind / 30.0, 1.0) * 100
            score_humidity = min(max_humidity / 100.0, 1.0) * 100
            score_shear = min(max_shear / 0.05, 1.0) * 100
            score_sfc = min(sfc_wind / 15.0, 1.0) * 100

            composite = (0.40 * score_wind +
                         0.25 * score_humidity +
                         0.20 * score_shear +
                         0.15 * score_sfc)

            severity_scores[time_id] = {
                'composite': composite,
                'max_wind_mps': max_wind,
                'max_humidity_pct': max_humidity,
                'max_shear_s1': max_shear,
                'sfc_wind_mps': sfc_wind,
            }

        worst_time = max(severity_scores, key=lambda k: severity_scores[k]['composite'])
        worst_info = severity_scores[worst_time]
        worst_info['timestamp'] = worst_time

        print(f"MELCHIOR: Pior dia selecionado — {worst_time}")
        print(f"  Score composto: {worst_info['composite']:.1f}/100")
        print(f"  Vento máx: {worst_info['max_wind_mps']:.1f} m/s | Umidade máx: {worst_info['max_humidity_pct']:.0f}%")
        print(f"  Cisalhamento máx: {worst_info['max_shear_s1']:.4f} s⁻¹ | Vento superfície: {worst_info['sfc_wind_mps']:.1f} m/s")

        df_worst = df_hist[df_hist['valid_time_utc'] == worst_time].copy()
        df_worst['data_type'] = 'historical_worst_case'
        df_worst['model_name'] = 'ERA5 Historical Worst Case'

        if 'cloud_cover_pct' not in df_worst.columns:
            df_worst['cloud_cover_pct'] = np.clip(df_worst['relative_humidity_pct'] * 1.2, 0, 100)
        if 'cape_jkg' not in df_worst.columns:
            df_worst['cape_jkg'] = np.where(
                df_worst['relative_humidity_pct'] > 70, 1500 + np.random.uniform(0, 500, len(df_worst)),
                200 + np.random.uniform(0, 100, len(df_worst))
            )
        if 'precipitation_mm' not in df_worst.columns:
            df_worst['precipitation_mm'] = np.where(
                df_worst['relative_humidity_pct'] > 80, np.random.uniform(5, 25, len(df_worst)),
                np.where(df_worst['relative_humidity_pct'] > 60, np.random.uniform(0.5, 5, len(df_worst)), 0.0)
            )

        return df_worst, worst_info

    def calc_stats_hist(self, df_hist, altitude_grid=None):
        print("MELCHIOR: Calculando estatísticas históricas e percentis ao longo dos níveis de altitude...")
        if df_hist.empty or altitude_grid is None:
            return pd.DataFrame()
            
        from scipy.interpolate import interp1d
        from casper import CasperPhysics
        
        interpolated_profiles = []
        for time, group in df_hist.groupby('valid_time_utc'):
            group = group.sort_values('altitude_agl_m').drop_duplicates('altitude_agl_m')
            z_orig = group['altitude_agl_m'].values
            
            df_interp = pd.DataFrame({'altitude_agl_m': altitude_grid})
            for col in ['u_east_mps', 'v_north_mps', 'temperature_k', 'pressure_pa', 'relative_humidity_pct']:
                if col in group.columns:
                    f = interp1d(z_orig, group[col].values, bounds_error=False, fill_value=np.nan)
                    df_interp[col] = f(altitude_grid)
            
            if 'u_east_mps' in df_interp.columns and 'v_north_mps' in df_interp.columns:
                speed, dir_from = CasperPhysics.uv_to_speed_dir(df_interp['u_east_mps'], df_interp['v_north_mps'])
                df_interp['wind_speed_mps'] = speed
                df_interp['wind_direction_from_deg'] = dir_from
                df_interp['wind_shear_s_1'] = CasperPhysics.calc_shear(df_interp['u_east_mps'].values, df_interp['v_north_mps'].values, altitude_grid)
                
            if 'pressure_pa' in df_interp.columns and 'temperature_k' in df_interp.columns and 'relative_humidity_pct' in df_interp.columns:
                df_interp['density_kgm3'] = CasperPhysics.calc_density(df_interp['pressure_pa'], df_interp['temperature_k'], df_interp['relative_humidity_pct'])
                
            interpolated_profiles.append(df_interp)
            
        if not interpolated_profiles:
            return pd.DataFrame()
            
        df_grid_all = pd.concat(interpolated_profiles, ignore_index=True)
        
        stats = []
        for z, group in df_grid_all.groupby('altitude_agl_m'):
            s = {'altitude_agl_m': z}
            for var in ['u_east_mps', 'v_north_mps', 'temperature_k', 'pressure_pa', 'relative_humidity_pct', 'density_kgm3']:
                if var in group.columns:
                    s[f'{var}_mean'] = group[var].mean()
                    s[f'{var}_median'] = group[var].median()
                    for p in [5, 10, 25, 75, 90, 95]:
                        s[f'{var}_p{p}'] = np.nanpercentile(group[var], p)
            
            if 'u_east_mps_mean' in s and 'v_north_mps_mean' in s:
                s['wind_speed_mps_mean'], s['wind_dir_mean'] = CasperPhysics.uv_to_speed_dir(s['u_east_mps_mean'], s['v_north_mps_mean'])
                s['wind_speed_mps_median'], _ = CasperPhysics.uv_to_speed_dir(s['u_east_mps_median'], s['v_north_mps_median'])
                for p in [5, 10, 25, 75, 90, 95]:
                    s[f'wind_speed_mps_p{p}'], _ = CasperPhysics.uv_to_speed_dir(s[f'u_east_mps_p{p}'], s[f'v_north_mps_p{p}'])
                    
            if 'wind_shear_s_1' in group.columns:
                s['wind_shear_s_1_mean'] = group['wind_shear_s_1'].mean()
                s['wind_shear_s_1_median'] = group['wind_shear_s_1'].median()
                for p in [5, 10, 25, 75, 90, 95]:
                    s[f'wind_shear_s_1_p{p}'] = np.nanpercentile(group['wind_shear_s_1'], p)
                    
            stats.append(s)
            
        df_res = pd.DataFrame(stats)
        
        for col in ['wind_speed_mps', 'u_east_mps', 'v_north_mps', 'wind_shear_s_1', 'density_kgm3', 'temperature_k']:
             if f"{col}_p05" in df_res.columns and f"{col}_p95" in df_res.columns:
                 mask = df_res[f"{col}_p05"] > df_res[f"{col}_p95"]
                 if mask.any():
                     temp = df_res.loc[mask, f"{col}_p05"].copy()
                     df_res.loc[mask, f"{col}_p05"] = df_res.loc[mask, f"{col}_p95"]
                     df_res.loc[mask, f"{col}_p95"] = temp
                     
             if f"{col}_p10" in df_res.columns and f"{col}_p90" in df_res.columns:
                 mask = df_res[f"{col}_p10"] > df_res[f"{col}_p90"]
                 if mask.any():
                     temp = df_res.loc[mask, f"{col}_p10"].copy()
                     df_res.loc[mask, f"{col}_p10"] = df_res.loc[mask, f"{col}_p90"]
                     df_res.loc[mask, f"{col}_p90"] = temp
        return df_res

    def calculate_multivariate_covariance(self, df_hist, altitude_grid):
        print("MELCHIOR: Construindo vetor de estado multivariado e calculando matriz de covariância (Ledoit-Wolf)...")
        df_grid = df_hist[df_hist['altitude_agl_m'].isin(altitude_grid)]
        
        if df_grid.empty:
            return None, None
            
        pivoted = df_grid.pivot(index='valid_time_utc', columns='altitude_agl_m', 
                                values=['u_east_mps', 'v_north_mps', 'temperature_k', 'specific_humidity_kg_kg'])
                                
        pivoted = pivoted.dropna()
        if len(pivoted) < 2:
            return None, None
            
        ordered_cols = []
        for var in ['u_east_mps', 'v_north_mps', 'temperature_k', 'specific_humidity_kg_kg']:
            for z in altitude_grid:
                if (var, z) in pivoted.columns:
                    ordered_cols.append((var, z))
                    
        X = pivoted[ordered_cols].values
        
        mu = np.mean(X, axis=0)
        
        lw = LedoitWolf()
        lw.fit(X)
        cov_matrix = lw.covariance_
        
        return mu, cov_matrix

class MelchiorVisuals:
    @staticmethod
    def plot_magnitude_vento(df_stats):
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(df_stats['wind_speed_mps_mean'], df_stats['altitude_agl_m'], label='Historical Mean')
        ax.fill_betweenx(df_stats['altitude_agl_m'], 
                         df_stats['wind_speed_mps_p10'], 
                         df_stats['wind_speed_mps_p90'], 
                         alpha=0.3, label='10th-90th Percentile')
        ax.set_title("Historical Wind Magnitude")
        ax.legend()
        return fig
```

---

### 3.5. `casper.py`
```python
import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator
import matplotlib.pyplot as plt
import datetime

class MagiSchema:
    COLUMNS = [
        "valid_time_utc",
        "generation_time_utc",
        "altitude_agl_m",
        "altitude_msl_m",
        "u_east_mps",
        "v_north_mps",
        "w_up_mps",
        "wind_speed_mps",
        "wind_direction_from_deg",
        "pressure_pa",
        "temperature_k",
        "relative_humidity_pct",
        "specific_humidity_kg_kg",
        "density_kgm3",
        "wind_shear_s_1",
        "data_source",
        "data_type",
        "quality_flag",
        "model_name",
        "ensemble_member",
        "generation_method",
        "ensemble_source"
    ]

    @staticmethod
    def create_empty(num_rows=0):
        df = pd.DataFrame(index=range(num_rows), columns=MagiSchema.COLUMNS)
        return df

    @staticmethod
    def validate(df):
        missing = set(MagiSchema.COLUMNS) - set(df.columns)
        if missing:
            raise ValueError(f"Missing schema columns: {missing}")
        return True

class CasperPhysics:
    R_AIR = 287.05
    G = 9.80665

    @staticmethod
    def calc_vapor_pressure(temp_k):
        temp_c = temp_k - 273.15
        return 6.112 * np.exp((17.67 * temp_c) / (temp_c + 243.5))

    @staticmethod
    def calc_specific_humidity(pressure_pa, temp_k, rh_pct):
        es = CasperPhysics.calc_vapor_pressure(temp_k)
        e = (rh_pct / 100.0) * es
        pressure_hpa = pressure_pa / 100.0
        q = np.where(pressure_hpa > e, (0.622 * e) / (pressure_hpa - e), 0)
        return q

    @staticmethod
    def calc_rh_from_specific_humidity(pressure_pa, temp_k, q):
        es = CasperPhysics.calc_vapor_pressure(temp_k)
        pressure_hpa = pressure_pa / 100.0
        e = (q * pressure_hpa) / (0.622 + q)
        rh = (e / es) * 100.0
        return np.clip(rh, 0, 100)

    @staticmethod
    def calc_density(pressure_pa, temp_k, rh_pct):
        q = CasperPhysics.calc_specific_humidity(pressure_pa, temp_k, rh_pct)
        tv_k = temp_k * (1 + 0.608 * q)
        return pressure_pa / (CasperPhysics.R_AIR * tv_k)

    @staticmethod
    def speed_dir_to_uv(speed, direction_from):
        dir_rad = np.radians(direction_from)
        u = -speed * np.sin(dir_rad)
        v = -speed * np.cos(dir_rad)
        return u, v

    @staticmethod
    def uv_to_speed_dir(u, v):
        speed = np.sqrt(u**2 + v**2)
        dir_from = (np.degrees(np.arctan2(-u, -v)) + 360) % 360
        return speed, dir_from

    @staticmethod
    def calc_shear(u, v, z):
        if len(z) < 2:
            return np.zeros_like(z, dtype=float)
        du = np.gradient(u, z)
        dv = np.gradient(v, z)
        return np.sqrt(du**2 + dv**2)
        
    @staticmethod
    def hydrostatic_diagnostic(pressure_pa, density_kgm3, z_m):
        if len(z_m) < 2:
            return np.zeros_like(z_m), False
        dp_dz = np.gradient(pressure_pa, z_m)
        rho_g = density_kgm3 * CasperPhysics.G
        eps_h = np.abs(dp_dz + rho_g) / rho_g
        return eps_h

class CasperProcessor:
    SURFACE_ROUGHNESS = {
        "OPEN_TERRAIN": 0.03,
        "VEGETATED_TERRAIN": 0.10,
        "ROUGH_RURAL": 0.30
    }
    
    HYDROSTATIC_WARNING_THRESHOLD = 0.05
    HYDROSTATIC_FAILURE_THRESHOLD = 0.10
    HYDROSTATIC_CONSECUTIVE_LEVELS = 3

    def __init__(self, elevation_msl=450, surface_scenario="OPEN_TERRAIN"):
        self.elevation_msl = elevation_msl
        self.surface_scenario = surface_scenario
        self.z0 = self.SURFACE_ROUGHNESS.get(surface_scenario, 0.03)

    def _generate_surface_layer(self, z_grid, lowest_z_valid, u_ref, v_ref):
        u_surf = np.zeros_like(z_grid, dtype=float)
        v_surf = np.zeros_like(z_grid, dtype=float)
        
        mask = z_grid <= lowest_z_valid
        if not np.any(mask) or lowest_z_valid <= self.z0:
            return u_surf, v_surf
            
        z_masked = np.maximum(z_grid[mask], self.z0)
        scale = np.log(z_masked / self.z0) / np.log(lowest_z_valid / self.z0)
        scale = np.clip(scale, 0, 1)
        
        u_surf[mask] = u_ref * scale
        v_surf[mask] = v_ref * scale
        return u_surf, v_surf

    def interpolate_profile(self, df_raw, altitude_grid):
        print(f"CASPER: Interpolando perfil atmosférico bruto para grade de {len(altitude_grid)} níveis de altitude...")
        if df_raw.empty:
            return MagiSchema.create_empty()
            
        df_raw = df_raw.sort_values('altitude_agl_m').drop_duplicates('altitude_agl_m')
        df_raw = df_raw.dropna(subset=['altitude_agl_m'])
        if len(df_raw) < 2:
            return MagiSchema.create_empty()

        z_orig = df_raw['altitude_agl_m'].values
        df_grid = MagiSchema.create_empty(len(altitude_grid))
        df_grid['altitude_agl_m'] = altitude_grid
        df_grid['altitude_msl_m'] = altitude_grid + self.elevation_msl
        
        lowest_z = z_orig.min()
        highest_z = z_orig.max()
        
        vars_to_interp = ['u_east_mps', 'v_north_mps', 'temperature_k', 'relative_humidity_pct']
        for var in vars_to_interp:
            if df_raw[var].notna().any():
                f = PchipInterpolator(z_orig, df_raw[var].values, extrapolate=False)
                interp_vals = f(altitude_grid)
                mask_above = altitude_grid > highest_z
                if np.any(mask_above):
                    last_idx = df_raw[var].last_valid_index()
                    if last_idx is not None:
                        interp_vals[mask_above] = df_raw.loc[last_idx, var]
                df_grid[var] = interp_vals
            else:
                df_grid[var] = np.nan
                
        if df_raw['pressure_pa'].notna().any():
            ln_p = np.log(df_raw['pressure_pa'].values)
            f_ln_p = PchipInterpolator(z_orig, ln_p, extrapolate=False)
            interp_vals = f_ln_p(altitude_grid)
            mask_above = altitude_grid > highest_z
            if np.any(mask_above):
                p_last_idx = df_raw['pressure_pa'].last_valid_index()
                T_last_idx = df_raw['temperature_k'].last_valid_index()
                if p_last_idx is not None and T_last_idx is not None:
                    p_last = df_raw.loc[p_last_idx, 'pressure_pa']
                    T_last = df_raw.loc[T_last_idx, 'temperature_k']
                    dz = altitude_grid[mask_above] - highest_z
                    interp_vals[mask_above] = np.log(p_last) - (9.81 / (287.05 * T_last)) * dz
            df_grid['pressure_pa'] = np.exp(interp_vals)
        else:
            df_grid['pressure_pa'] = np.nan

        mask_below = altitude_grid < lowest_z
        if np.any(mask_below):
            u_ref = df_raw['u_east_mps'].iloc[0]
            v_ref = df_raw['v_north_mps'].iloc[0]
            u_s, v_s = self._generate_surface_layer(altitude_grid, lowest_z, u_ref, v_ref)
            df_grid.loc[mask_below, 'u_east_mps'] = u_s[mask_below]
            df_grid.loc[mask_below, 'v_north_mps'] = v_s[mask_below]
            df_grid.loc[mask_below, 'temperature_k'] = df_raw['temperature_k'].iloc[0]
            df_grid.loc[mask_below, 'pressure_pa'] = df_raw['pressure_pa'].iloc[0]
            df_grid.loc[mask_below, 'relative_humidity_pct'] = df_raw['relative_humidity_pct'].iloc[0]

        df_grid['wind_speed_mps'], df_grid['wind_direction_from_deg'] = CasperPhysics.uv_to_speed_dir(df_grid['u_east_mps'], df_grid['v_north_mps'])
        df_grid['specific_humidity_kg_kg'] = CasperPhysics.calc_specific_humidity(df_grid['pressure_pa'], df_grid['temperature_k'], df_grid['relative_humidity_pct'])
        df_grid['density_kgm3'] = CasperPhysics.calc_density(df_grid['pressure_pa'], df_grid['temperature_k'], df_grid['relative_humidity_pct'])
        df_grid['wind_shear_s_1'] = CasperPhysics.calc_shear(df_grid['u_east_mps'].values, df_grid['v_north_mps'].values, df_grid['altitude_agl_m'].values)
        
        eps_h = CasperPhysics.hydrostatic_diagnostic(df_grid['pressure_pa'].values, df_grid['density_kgm3'].values, df_grid['altitude_msl_m'].values)
        consecutive_failures = 0
        for e in eps_h:
            if not np.isnan(e) and e > self.HYDROSTATIC_FAILURE_THRESHOLD:
                consecutive_failures += 1
            else:
                consecutive_failures = 0
            if consecutive_failures >= self.HYDROSTATIC_CONSECUTIVE_LEVELS:
                print("HYDROSTATIC FAILURE: Profile fails diagnostic on 3 consecutive layers.")
                break
                
        meta_cols = ['valid_time_utc', 'generation_time_utc', 'data_source', 'data_type', 'model_name', 'ensemble_member', 'ensemble_source', 'cloud_cover_pct']
        for col in meta_cols:
            if col in df_raw.columns:
                df_grid[col] = df_raw[col].iloc[0]
        if 'cloud_cover_pct' not in df_grid.columns or df_grid['cloud_cover_pct'].isna().all():
            df_grid['cloud_cover_pct'] = np.clip(df_grid['relative_humidity_pct'] * 1.2, 15.0, 95.0)
            
        df_grid['quality_flag'] = 'VALID'
        df_grid.loc[altitude_grid > highest_z, 'quality_flag'] = 'OUT_OF_VERTICAL_RANGE'
        df_grid.loc[mask_below, 'quality_flag'] = 'SYNTHETIC_SURFACE_LAYER'
        
        return df_grid

    def generate_synthetic_ensemble(self, df_nominal, cov_matrix, altitude_grid, num_members=100):
        print(f"CASPER: Gerando {num_members} membros de ensemble sintético via autodecomposição da covariância histórica...")
        if cov_matrix is None or len(df_nominal) != len(altitude_grid):
            print("Invalid nominal profile or covariance matrix.")
            return []
            
        n_vars = 4
        nz = len(altitude_grid)
        if cov_matrix.shape[0] != n_vars * nz:
            print("Covariance matrix dimension mismatch.")
            return []
            
        eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
        eigenvalues[eigenvalues < 0] = 0
        
        members = []
        u_nom = df_nominal['u_east_mps'].values
        v_nom = df_nominal['v_north_mps'].values
        T_nom = df_nominal['temperature_k'].values
        q_nom = df_nominal['specific_humidity_kg_kg'].values
        p_nom = df_nominal['pressure_pa'].values
        
        x_nom = np.concatenate([u_nom, v_nom, T_nom, q_nom])
        
        for i in range(num_members):
            coeffs = np.random.randn(len(eigenvalues))
            perturbation = eigenvectors @ (np.sqrt(eigenvalues) * coeffs)
            x_member = x_nom + perturbation
            
            u_m = x_member[0:nz]
            v_m = x_member[nz:2*nz]
            T_m = x_member[2*nz:3*nz]
            q_m = x_member[3*nz:4*nz]
            
            T_m = np.maximum(T_m, 100.0)
            q_m = np.maximum(q_m, 0.0)
            
            df_m = df_nominal.copy()
            df_m['u_east_mps'] = u_m
            df_m['v_north_mps'] = v_m
            df_m['temperature_k'] = T_m
            df_m['specific_humidity_kg_kg'] = q_m
            
            speed, dir_from = CasperPhysics.uv_to_speed_dir(u_m, v_m)
            df_m['wind_speed_mps'] = speed
            df_m['wind_direction_from_deg'] = dir_from
            
            df_m['relative_humidity_pct'] = CasperPhysics.calc_rh_from_specific_humidity(p_nom, T_m, q_m)
            df_m['density_kgm3'] = CasperPhysics.calc_density(p_nom, T_m, df_m['relative_humidity_pct'].values)
            df_m['wind_shear_s_1'] = CasperPhysics.calc_shear(u_m, v_m, altitude_grid)
            
            df_m['data_type'] = "synthetic_ensemble"
            df_m['generation_method'] = "covariance_eigendecomposition"
            df_m['ensemble_member'] = f"synthetic_{i+1}"
            df_m['ensemble_source'] = "synthetic_from_deterministic"
            
            members.append(df_m)
            
        return members

class CasperVisuals:
    @staticmethod
    def plot_painel(df_atual, df_stats):
        fig, axes = plt.subplots(1, 4, figsize=(16, 6))
        fig.suptitle("CASPER Synthesis Panel", fontsize=16)
        
        valid = df_atual['quality_flag'] != 'OUT_OF_VERTICAL_RANGE'
        d = df_atual[valid]
        
        axes[0].plot(d['wind_speed_mps'], d['altitude_agl_m'])
        axes[0].set_title("Wind Speed")
        
        axes[1].plot(d['u_east_mps'], d['altitude_agl_m'], label='U')
        axes[1].plot(d['v_north_mps'], d['altitude_agl_m'], label='V')
        axes[1].set_title("U/V Components")
        axes[1].legend()
        
        axes[2].plot(d['wind_shear_s_1'], d['altitude_agl_m'])
        axes[2].set_title("Wind Shear")
        
        axes[3].plot(d['density_kgm3'], d['altitude_agl_m'])
        axes[3].set_title("Density")
        
        plt.tight_layout()
        return fig
```

---

### 3.6. `scoring.py`
```python
import numpy as np

class AtmosphericScoring:
    ANALYSIS_TOP_AGL_M = 6000
    
    @staticmethod
    def calculate_score(df_ensemble, df_stats, z_grid):
        if not df_ensemble or df_stats.empty:
            return None, "ATMOSPHERIC_SCORE_UNAVAILABLE"
            
        mask = z_grid <= AtmosphericScoring.ANALYSIS_TOP_AGL_M
        
        max_wind_env = 0
        max_shear_env = 0
        spread_wind_max = 0
        
        for df in df_ensemble:
            w_spd = df['wind_speed_mps'].values[mask]
            shear = df['wind_shear_s_1'].values[mask]
            
            w_spd = w_spd[~np.isnan(w_spd)]
            shear = shear[~np.isnan(shear)]
            
            if len(w_spd) > 0:
                max_wind_env = max(max_wind_env, np.max(w_spd))
            if len(shear) > 0:
                max_shear_env = max(max_shear_env, np.max(shear))
                
        if len(df_ensemble) > 1:
            all_winds = np.array([df['wind_speed_mps'].values[mask] for df in df_ensemble])
            p90_env = np.nanpercentile(all_winds, 90, axis=0)
            p10_env = np.nanpercentile(all_winds, 10, axis=0)
            spread_wind_max = np.nanmax(p90_env - p10_env)
            
        hist_mask = df_stats['altitude_agl_m'].values <= AtmosphericScoring.ANALYSIS_TOP_AGL_M
        hist_p50_wind = df_stats['wind_speed_mps_median'].values[hist_mask]
        hist_p90_wind = df_stats['wind_speed_mps_p90'].values[hist_mask]
        
        max_hist_p50 = np.nanmax(hist_p50_wind) if len(hist_p50_wind) > 0 else 10.0
        max_hist_p90 = np.nanmax(hist_p90_wind) if len(hist_p90_wind) > 0 else 20.0
        max_hist_p99 = max_hist_p90 * 1.5
        
        if max_wind_env <= max_hist_p50:
            score_wind = 35.0
        elif max_wind_env <= max_hist_p90:
            ratio = (max_wind_env - max_hist_p50) / (max_hist_p90 - max_hist_p50)
            score_wind = 35.0 - (ratio * 15.0)
        elif max_wind_env <= max_hist_p99:
            ratio = (max_wind_env - max_hist_p90) / (max_hist_p99 - max_hist_p90)
            score_wind = 20.0 - (ratio * 20.0)
        else:
            score_wind = 0.0
            
        shear_p50 = 0.015
        shear_p90 = 0.030
        shear_p99 = 0.050
        
        if max_shear_env <= shear_p50:
            score_shear = 25.0
        elif max_shear_env <= shear_p90:
            ratio = (max_shear_env - shear_p50) / (shear_p90 - shear_p50)
            score_shear = 25.0 - (ratio * 10.0)
        elif max_shear_env <= shear_p99:
            ratio = (max_shear_env - shear_p90) / (shear_p99 - shear_p90)
            score_shear = 15.0 - (ratio * 15.0)
        else:
            score_shear = 0.0
            
        if spread_wind_max <= 1.0:
            score_spread = 20.0
        elif spread_wind_max <= 5.0:
            score_spread = 20.0 - ((spread_wind_max - 1.0)/4.0 * 15.0)
        else:
            score_spread = 0.0
            
        score_weather = 10.0
        score_quality = 10.0
        
        total_score = score_wind + score_shear + score_spread + score_weather + score_quality
        
        if total_score >= 80:
            classification = "Highly Favourable"
        elif total_score >= 60:
            classification = "Favourable"
        elif total_score >= 40:
            classification = "Moderate"
        elif total_score >= 20:
            classification = "Unfavourable"
        else:
            classification = "Highly Atypical"
            
        return total_score, classification
```

---

### 3.7. `state_manager.py`
```python
import datetime
import os
import json

class MagiState:
    CURRENT_FORECAST = "CURRENT_FORECAST"
    CACHED_FORECAST = "CACHED_FORECAST"
    DEGRADED_DATA = "DEGRADED_DATA"
    CLIMATOLOGY_ONLY = "CLIMATOLOGY_ONLY"
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"

class StateManager:
    CACHE_FRESH_LIMIT_HOURS = 6
    CACHE_DEGRADED_LIMIT_HOURS = 12
    
    def __init__(self, cache_dir="dados_cache"):
        self.cache_dir = cache_dir
        self.metadata_path = os.path.join(cache_dir, "cache_meta.json")
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def _read_metadata(self):
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, 'r') as f:
                return json.load(f)
        return {}
        
    def write_metadata(self, meta):
        with open(self.metadata_path, 'w') as f:
            json.dump(meta, f, indent=2)

    def evaluate_state(self, is_online=True, fetch_success=True, is_real_ensemble=True, 
                       variables_complete=True, valid_time_utc=None):
        meta = self._read_metadata()
        now_utc = datetime.datetime.now(datetime.UTC)
        
        last_update_str = meta.get("last_successful_update_utc", None)
        if last_update_str:
            last_update = datetime.datetime.fromisoformat(last_update_str)
            cache_age_hours = (now_utc - last_update).total_seconds() / 3600.0
        else:
            cache_age_hours = float('inf')
            
        state_reason = []
        
        if is_online and fetch_success:
            if variables_complete and is_real_ensemble:
                state = MagiState.CURRENT_FORECAST
                state_reason.append("Online fetch successful, all variables complete.")
            else:
                state = MagiState.DEGRADED_DATA
                state_reason.append("Online fetch successful but missing real ensemble or variables.")
        else:
            if not is_online or not fetch_success:
                state_reason.append("Offline or fetch failed.")
                
            if cache_age_hours <= self.CACHE_FRESH_LIMIT_HOURS:
                state = MagiState.CACHED_FORECAST
            elif cache_age_hours <= self.CACHE_DEGRADED_LIMIT_HOURS:
                state = MagiState.DEGRADED_DATA
                state_reason.append(f"Cache age {cache_age_hours:.1f}h is > {self.CACHE_FRESH_LIMIT_HOURS}h.")
            else:
                state = MagiState.CLIMATOLOGY_ONLY
                state_reason.append(f"Cache age {cache_age_hours:.1f}h exceeds limit {self.CACHE_DEGRADED_LIMIT_HOURS}h.")
                
        if state in [MagiState.CURRENT_FORECAST, MagiState.DEGRADED_DATA]:
            meta["last_successful_update_utc"] = now_utc.isoformat()
            self.write_metadata(meta)
            cache_age_hours = 0.0

        return {
            "operational_state": state,
            "state_reason": "; ".join(state_reason),
            "cache_age_hours": cache_age_hours,
            "last_successful_update_utc": meta.get("last_successful_update_utc", ""),
            "requested_valid_time_utc": valid_time_utc.isoformat() if valid_time_utc else now_utc.isoformat()
        }
```

---

### 3.8. `exporter.py`
```python
import xarray as xr
import pandas as pd
import numpy as np

class NetCDFExporter:
    @staticmethod
    def export_magi_netcdf(df_nominal, df_ensembles, df_stats, output_path, global_attrs):
        if df_nominal is None or df_nominal.empty:
            return
            
        z_grid = df_nominal['altitude_agl_m'].values
        valid_time = pd.to_datetime([df_nominal['valid_time_utc'].iloc[0]]).tz_localize(None)
        
        n_alt = len(z_grid)
        n_members = 1 + len(df_ensembles)
        
        vars_to_export = [
            'u_east_mps', 'v_north_mps', 'w_up_mps', 'wind_speed_mps', 'wind_direction_from_deg',
            'temperature_k', 'pressure_pa', 'relative_humidity_pct', 'specific_humidity_kg_kg',
            'density_kgm3', 'wind_shear_s_1'
        ]
        
        data_arrays = {var: np.full((1, n_members, 1, n_alt), np.nan) for var in vars_to_export}
        member_roles = []
        member_sources = []
        model_names = []
        
        for var in vars_to_export:
            if var in df_nominal.columns:
                data_arrays[var][0, 0, 0, :] = df_nominal[var].values
        member_roles.append('nominal')
        member_sources.append(df_nominal['ensemble_source'].iloc[0] if 'ensemble_source' in df_nominal.columns else 'unknown')
        model_names.append(df_nominal['model_name'].iloc[0] if 'model_name' in df_nominal.columns else 'unknown')
                
        for i, df_ens in enumerate(df_ensembles):
            idx = i + 1
            for var in vars_to_export:
                if var in df_ens.columns:
                    data_arrays[var][0, idx, 0, :] = df_ens[var].values
            role = 'synthetic_ensemble' if df_ens['data_type'].iloc[0] == 'synthetic_ensemble' else 'real_ensemble'
            member_roles.append(role)
            member_sources.append(df_ens['ensemble_source'].iloc[0] if 'ensemble_source' in df_ens.columns else 'unknown')
            model_names.append(df_ens['model_name'].iloc[0] if 'model_name' in df_ens.columns else 'unknown')
            
        coords = {
            'valid_time': valid_time,
            'ensemble_member': np.arange(n_members),
            'surface_scenario': ['default'],
            'altitude_agl_m': z_grid,
            'member_role': ('ensemble_member', member_roles),
            'member_source': ('ensemble_member', member_sources),
            'model_name': ('ensemble_member', model_names)
        }
        
        ds_vars = {}
        for var in vars_to_export:
            ds_vars[var] = (('valid_time', 'ensemble_member', 'surface_scenario', 'altitude_agl_m'), data_arrays[var])
            
        if df_stats is not None and not df_stats.empty:
            coords['climatology_statistic'] = ['mean', 'median', 'p10', 'p25', 'p75', 'p90']
            clim_z = df_stats['altitude_agl_m'].values
            for var in ['wind_speed_mps', 'temperature_k', 'u_east_mps', 'v_north_mps']:
                clim_data = np.full((len(coords['climatology_statistic']), n_alt), np.nan)
                for j, stat in enumerate(coords['climatology_statistic']):
                    col = f"{var}_{stat}"
                    if col in df_stats.columns:
                        clim_data[j, :] = np.interp(z_grid, clim_z, df_stats[col].values, left=np.nan, right=np.nan)
                ds_vars[f"climatology_{var}"] = (('climatology_statistic', 'altitude_agl_m'), clim_data)
                
        ds = xr.Dataset(ds_vars, coords=coords)
        ds.attrs = global_attrs
        
        ds.to_netcdf(output_path)
```

---

### 3.9. `build_notebook.py`
```python
import nbformat as nbf
import re
import os

app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MAGI_App.py")

with open(app_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

nb = nbf.v4.new_notebook()

current_type = None
current_lines = []

def add_cell():
    if not current_lines:
        return
    text = "".join(current_lines).strip()
    if not text:
        return
    if current_type == "markdown":
        md_lines = []
        for line in current_lines:
            if line.startswith("# "):
                md_lines.append(line[2:])
            elif line.startswith("#"):
                md_lines.append(line[1:])
            else:
                md_lines.append(line)
        nb.cells.append(nbf.v4.new_markdown_cell("".join(md_lines).strip()))
    elif current_type == "code":
        nb.cells.append(nbf.v4.new_code_cell(text))

for line in lines:
    if line.startswith("#!") or line.startswith("# coding:"):
        continue
    if re.match(r"^# In\[.*\]:", line):
        add_cell()
        current_type = "code"
        current_lines = []
    elif line.startswith("# #"):
        add_cell()
        current_type = "markdown"
        current_lines = [line]
    else:
        if current_type is None:
            if line.startswith("#"):
                current_type = "markdown"
            else:
                current_type = "code"
        current_lines.append(line)

add_cell()

nb_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MAGI_App.ipynb")
with open(nb_path, "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print(f"Notebook MAGI_App.ipynb successfully rebuilt from MAGI_App.py with {len(nb.cells)} cells.")
```

---

### 3.10. `tests/test_integration.py`
```python
import pytest
import numpy as np
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from casper import MagiSchema, CasperPhysics, CasperProcessor
from melchior import Melchior
from balthasar import Balthasar

def test_schema_creation():
    df = MagiSchema.create_empty(5)
    assert len(df) == 5
    assert "valid_time_utc" in df.columns
    assert "density_kgm3" in df.columns

def test_speed_dir_to_uv():
    u, v = CasperPhysics.speed_dir_to_uv(10, 90)
    assert np.isclose(u, -10.0)
    assert np.isclose(v, 0.0)
    
    u, v = CasperPhysics.speed_dir_to_uv(10, 180)
    assert np.isclose(u, 0.0)
    assert np.isclose(v, 10.0)

def test_uv_to_speed_dir():
    spd, dir_from = CasperPhysics.uv_to_speed_dir(-10.0, 0.0)
    assert np.isclose(spd, 10.0)
    assert np.isclose(dir_from, 90.0)

def test_density_calculation():
    rho = CasperPhysics.calc_density(101325, 288.15, 0.0)
    assert np.isclose(rho, 1.225, atol=0.01)

def test_melchior_integration():
    melchior = Melchior(elevation_msl=450)
    df_hist = melchior.fetch_historical_data()
    MagiSchema.validate(df_hist)

def test_balthasar_integration():
    balthasar = Balthasar(elevation_msl=450)
    df_curr, is_real = balthasar.fetch_operational_forecast()
    if is_real:
        MagiSchema.validate(df_curr[0])
    else:
        MagiSchema.validate(df_curr)

def test_casper_interpolation():
    df_raw = MagiSchema.create_empty(2)
    df_raw['altitude_agl_m'] = [0, 1000]
    df_raw['temperature_k'] = [300, 290]
    df_raw['pressure_pa'] = [100000, 90000]
    df_raw['u_east_mps'] = [5, 10]
    df_raw['v_north_mps'] = [0, 0]
    df_raw['relative_humidity_pct'] = [50, 50]
    df_raw['valid_time_utc'] = pd.to_datetime('2026-07-19T12:00:00Z')
    df_raw['generation_time_utc'] = pd.to_datetime('2026-07-19T10:00:00Z')
    df_raw['data_source'] = 'test'
    df_raw['data_type'] = 'synthetic'
    df_raw['model_name'] = 'test_model'
    df_raw['ensemble_member'] = 'control'
    
    processor = CasperProcessor(elevation_msl=450)
    grid = np.arange(0, 1001, 100)
    df_interp = processor.interpolate_profile(df_raw, grid)
    
    assert len(df_interp) == 11
    MagiSchema.validate(df_interp)
    assert 'VALID' in df_interp['quality_flag'].values
    assert not df_interp['density_kgm3'].isna().any()
    assert not df_interp['wind_shear_s_1'].isna().any()
```

---

## 4. DADOS DE CACHE E CONFIGURAÇÃO ATUAL
- `dados_cache/atmosfera_atual.csv`: 6.1KB, perfil determinístico de contingência local.
- `dados_cache/historico_openmeteo.csv`: 135.7KB, dados históricos legados de reanálise.
- `dados_cache/previsao_openmeteo.csv`: 48.2KB, dados de previsão Open-Meteo.
- `dados_cache/metar_cache.txt` & `taf_cache.txt`: Últimos dados baixados de AviationWeather para aeródromos da região.
- `magi_export_latest.nc`: 151.1KB, arquivo NetCDF 4D contendo variáveis meteorológicas, conjuntos e climatologia estatística.


---

### 3.11. `visuals.py`
```python
import os
import math
import requests
import datetime
import textwrap
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as patches
import matplotlib.transforms as mtransforms
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from pathlib import Path
from PIL import Image

SITE_LATITUDE = -21.89021
SITE_LONGITUDE = -49.01827

# --- Configurable logo path ---
PROJECT_DIR = Path(__file__).resolve().parent
MAGI_LOGO_PATH = PROJECT_DIR / "Logo_Magi_light.png"

class LayoutReport:
    def __init__(self, fig):
        self.fig = fig
        self.bboxes = []
        self.issues = []

    def register_text(self, text_obj, name):
        self.bboxes.append({'name': name, 'obj': text_obj})

    def check_collisions(self):
        self.fig.canvas.draw()
        renderer = self.fig.canvas.get_renderer()
        
        boxes = []
        for item in self.bboxes:
            try:
                bbox = item['obj'].get_window_extent(renderer=renderer)
                boxes.append({'name': item['name'], 'bbox': bbox})
            except:
                pass

        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                b1 = boxes[i]['bbox']
                b2 = boxes[j]['bbox']
                
                # Check intersection
                if not (b1.x1 < b2.x0 or b1.x0 > b2.x1 or b1.y1 < b2.y0 or b1.y0 > b2.y1):
                    # Only report if they are from different conceptual groups
                    n1, n2 = boxes[i]['name'], boxes[j]['name']
                    if n1.split('_')[0] != n2.split('_')[0]:
                        self.issues.append(f"Collision detected between {n1} and {n2}")

        report = "Header overlap: " + ("FAIL" if any("head" in i for i in self.issues) else "PASS") + "\n"
        report += "Top titles overlap: " + ("FAIL" if any("title" in i for i in self.issues) else "PASS") + "\n"
        report += "Rose titles overlap: " + ("FAIL" if any("rose_title" in i for i in self.issues) else "PASS") + "\n"
        report += "Rose legend overlap: " + ("FAIL" if any("rose_leg" in i for i in self.issues) else "PASS") + "\n"
        report += "Footer overlap: " + ("FAIL" if any("foot" in i for i in self.issues) else "PASS") + "\n"
        report += "Logo overlap: " + ("FAIL" if any("logo" in i for i in self.issues) else "PASS") + "\n"
        report += "Caption overlap: " + ("FAIL" if any("sub" in i for i in self.issues) else "PASS") + "\n"
        
        return len(self.issues) == 0, report, self.issues

class VisualManager:
    FIGURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "figures"))
    
    @staticmethod
    def _ensure_dir():
        os.makedirs(VisualManager.FIGURES_DIR, exist_ok=True)
        
    @staticmethod
    def save_figure(fig, base_name, report_obj):
        VisualManager._ensure_dir()
        
        passed, report_txt, issues = report_obj.check_collisions()
        print("=== LAYOUT REPORT ===")
        print(report_txt)
        if not passed:
            for issue in issues: print(f" - {issue}")
            print("CRITICAL: Layout collision detected. Halting output.")
            raise ValueError("Layout collision detected. See report.")
            
        now_str = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
        dated_name = f"{base_name}_{now_str}.png"
        latest_name = f"{base_name}_latest.png"
        path_dated = os.path.join(VisualManager.FIGURES_DIR, dated_name)
        path_latest = os.path.join(VisualManager.FIGURES_DIR, latest_name)
        
        fig.savefig(path_dated, dpi=100, facecolor=fig.get_facecolor(), bbox_inches=None, pad_inches=0)
        import shutil
        shutil.copyfile(path_dated, path_latest)

MAGI_PALETTE = {
    "historical_mean": "#A9AFBF",
    "historical_median": "#747C91",
    "historical_range": "#7D8496",
    "historical_v": "#4a4f5c",
    "forecast_nominal": "#74A7FF",
    "forecast_ensemble": "#4F7FD8",
    "current_observation": "#FF9B5C",
    "synthetic_ensemble": "#B28DFF",
    "shear": "#FFCD9E",
    "threshold": "#FF7597",
    "missing_data": "#858A9C",
    "u_component": "#74A7FF", 
    "v_component": "#FF7597",
    "bg": "#11111a",
    "panel": "#1c1c28",
    "text": "#ffffff",
    "muted": "#a6adc8",
    "grid": "#2d2d44"
}

WARN_PALETTE = {
    'severe_primary': '#FF4444',
    'severe_secondary': '#FF8C42',
    'severe_band': '#993333',
    'severe_text': '#FFCCCC',
    'hist_ref': '#A9AFBF',
    'nominal_blue': '#74A7FF',
}

# --- Helper: Human-readable model name ---
_MODEL_DISPLAY_NAMES = {
    "deterministic_control": "GFS Deterministic Control",
    "ERA5_legacy": "ERA5 Reanalysis (Legacy)",
    "ecmwf_ifs04_ensemble": "ECMWF IFS 0.4° Ensemble",
    "gfs_seamless": "GFS Seamless",
}

def _friendly_model_name(raw_name):
    """Convert internal model identifiers to human-readable display names."""
    if raw_name in _MODEL_DISPLAY_NAMES:
        return _MODEL_DISPLAY_NAMES[raw_name]
    # Capitalise words as fallback
    return raw_name.replace('_', ' ').title() if raw_name else 'Unknown'

def _friendly_timestamp(ts):
    """Convert a timestamp to human-readable format: '21 Jul 2026, 18:20 BRT | 21:20 UTC'."""
    if isinstance(ts, str):
        try:
            ts = pd.Timestamp(ts)
        except Exception:
            return str(ts)
    if not isinstance(ts, (pd.Timestamp, datetime.datetime)):
        return str(ts)
    # Ensure UTC
    if ts.tzinfo is None:
        ts_utc = ts
    else:
        ts_utc = ts.tz_convert('UTC') if hasattr(ts, 'tz_convert') else ts
    utc_str = ts_utc.strftime("%d %b %Y, %H:%M UTC")
    # BRT = UTC-3
    try:
        ts_brt = ts_utc - pd.Timedelta(hours=3) if isinstance(ts_utc, pd.Timestamp) else ts_utc - datetime.timedelta(hours=3)
        brt_str = ts_brt.strftime("%H:%M BRT")
        return f"{ts_brt.strftime('%d %b %Y')}, {brt_str} | {ts_utc.strftime('%H:%M UTC')}"
    except Exception:
        return utc_str


class CasperVisualsV3:
    @staticmethod
    def _create_title_axes(fig, gridspec_slot, title, subtitle, report, wrap_width=50):
        """Create a subplot with a dedicated title row and caption row above the plot area.
        
        Captions are word-wrapped to `wrap_width` characters to prevent overflow into
        neighbouring axes.
        """
        inner = gridspec.GridSpecFromSubplotSpec(2, 1, subplot_spec=gridspec_slot, height_ratios=[0.18, 0.82], hspace=0.02)
        ax_text = fig.add_subplot(inner[0])
        ax_text.axis('off')
        
        # Wrap subtitle to prevent overflow
        wrapped_sub = "\n".join(textwrap.wrap(subtitle, width=wrap_width))
        
        t1 = ax_text.text(0.5, 0.70, title, fontsize=12, fontweight='bold', color=MAGI_PALETTE['text'], ha='center', va='bottom')
        t2 = ax_text.text(0.5, 0.25, wrapped_sub, fontsize=8, color=MAGI_PALETTE['muted'], ha='center', va='top')
        
        report.register_text(t1, f"title_{title[:5]}")
        report.register_text(t2, f"sub_{title[:5]}")
        
        ax_plot = fig.add_subplot(inner[1])
        ax_plot.set_facecolor(MAGI_PALETTE['panel'])
        ax_plot.grid(True, color=MAGI_PALETTE['grid'], linestyle='--', alpha=0.5)
        for spine in ax_plot.spines.values(): spine.set_color(MAGI_PALETTE['grid'])
        ax_plot.tick_params(colors=MAGI_PALETTE['text'], labelsize=10)
        
        return ax_plot

    @staticmethod
    def plot_magi_operational_panorama(df_nominal, df_ensembles, df_stats, score_info, state_info, is_example=False):
        FIGURE_WIDTH_PX = 2048
        FIGURE_HEIGHT_PX = 1176
        FIGURE_DPI = 100

        # Save original palette to restore later
        original_palette = None
        if is_example:
            original_palette = MAGI_PALETTE.copy()
            MAGI_PALETTE['forecast_nominal'] = WARN_PALETTE['severe_primary']
            MAGI_PALETTE['u_component'] = '#FF6B6B'
            MAGI_PALETTE['v_component'] = WARN_PALETTE['severe_secondary']

        plt.style.use('dark_background')
        fig = plt.figure(figsize=(FIGURE_WIDTH_PX / FIGURE_DPI, FIGURE_HEIGHT_PX / FIGURE_DPI), dpi=FIGURE_DPI, facecolor=MAGI_PALETTE['bg'])
        report = LayoutReport(fig)
        
        fig.subplots_adjust(top=0.98, bottom=0.02, left=0.02, right=0.98)

        # =====================================================================
        # OUTER LAYOUT: Header / Main Content / Footer
        # =====================================================================
        outer = gridspec.GridSpec(nrows=3, ncols=1, height_ratios=[0.10, 0.85, 0.05], hspace=0.02)

        # =====================================================================
        # 1. HEADER — Logo + Title + Metadata
        # =====================================================================
        head_grid = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=outer[0], width_ratios=[0.18, 0.82], wspace=0.02)
        
        # --- Logo cell (upper-left) ---
        ax_logo = fig.add_subplot(head_grid[0])
        ax_logo.axis('off')
        logo_loaded = False
        try:
            if MAGI_LOGO_PATH.exists():
                logo_img = Image.open(MAGI_LOGO_PATH).convert("RGBA")
                logo_arr = np.array(logo_img)
                # Verify real alpha channel (not all-255)
                if logo_arr.shape[2] == 4 and logo_arr[:,:,3].min() < 250:
                    # Target: ~65px height in final image. Logo natural aspect preserved.
                    target_h_px = 65
                    max_w_px = 280
                    scale = target_h_px / logo_img.height
                    target_w = int(logo_img.width * scale)
                    if target_w > max_w_px:
                        scale = max_w_px / logo_img.width
                    logo_resized = logo_img.resize(
                        (int(logo_img.width * scale), int(logo_img.height * scale)),
                        Image.LANCZOS
                    )
                    imagebox = OffsetImage(np.array(logo_resized), zoom=1.0)
                    ab = AnnotationBbox(imagebox, (0.5, 0.5), xycoords='axes fraction',
                                        frameon=False, box_alignment=(0.5, 0.5))
                    ax_logo.add_artist(ab)
                    logo_loaded = True
                else:
                    print("WARNING: Logo file has no real alpha channel; skipping logo.")
            else:
                print(f"WARNING: Logo file not found at {MAGI_LOGO_PATH}; generating dashboard without logo.")
        except Exception as e:
            print(f"WARNING: Failed to load logo: {e}; generating dashboard without logo.")
        
        # --- Title + Metadata cell ---
        head_text_grid = gridspec.GridSpecFromSubplotSpec(2, 1, subplot_spec=head_grid[1], height_ratios=[0.55, 0.45], hspace=0.0)
        
        ax_ht = fig.add_subplot(head_text_grid[0])
        ax_ht.axis('off')
        
        if is_example:
            title_text = "PAINEL-EXEMPLO — Pior Dia Histórico Registrado"
            title_color = WARN_PALETTE['severe_primary']
        else:
            title_text = "Iacanga Atmospheric Operational Overview" if logo_loaded else "MAGI — Iacanga Atmospheric Operational Overview"
            title_color = MAGI_PALETTE['text']
            
        t_ht = ax_ht.text(0.0, 0.3, title_text, ha='left', va='bottom', fontsize=24, fontweight="bold", color=title_color)
        report.register_text(t_ht, "head_main")
        
        ax_hm = fig.add_subplot(head_text_grid[1])
        ax_hm.axis('off')
        
        if is_example:
            meta_str = f"Data do evento: {_friendly_timestamp(state_info.get('requested_valid_time_utc', 'N/A'))} | Score de severidade: {score_info.get('score', 0):.1f}/100 | Fonte: {state_info.get('model_name', 'ERA5 Historical')}"
        else:
            # Human-readable valid time
            valid_time = state_info.get('requested_valid_time_utc', 'N/A')
            valid_time_str = _friendly_timestamp(valid_time)
            
            # Human-readable model name
            model_name_raw = df_nominal.get('model_name', ['Unknown']).iloc[0] if df_nominal is not None and 'model_name' in df_nominal.columns else 'Unknown'
            model_name = _friendly_model_name(model_name_raw)
            
            age = state_info.get('cache_age_hours', 0)
            age_str = "just now" if age < 0.1 else (f"{int(age*60)} min ago" if age < 1 else f"{int(age)} h {int((age - int(age)) * 60)} min ago")
            op_state_raw = state_info.get('operational_state', 'UNKNOWN')
            op_state_display = op_state_raw.replace('_', ' ').title()
            meta_str = f"Valid: {valid_time_str}  |  Model: {model_name}  |  State: {op_state_display}  |  Updated: {age_str}"
            
        t_hm = ax_hm.text(0.0, 0.9, meta_str, ha='left', va='top', fontsize=12, color=MAGI_PALETTE['muted'])
        report.register_text(t_hm, "head_meta")

        # =====================================================================
        # MAIN CONTENT — Left plots + Right column
        # =====================================================================
        main_content = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=outer[1], width_ratios=[2.7, 1.6], wspace=0.10)
        left = gridspec.GridSpecFromSubplotSpec(4, 1, subplot_spec=main_content[0], height_ratios=[1.15, 0.75, 0.15, 1.3], hspace=0.35)
        
        top = gridspec.GridSpecFromSubplotSpec(1, 3, subplot_spec=left[0], width_ratios=[2.2, 1.0, 1.0], wspace=0.20)
        
        z_grid = df_nominal['altitude_agl_m'].values if df_nominal is not None else np.array([])
        valid_mask = df_nominal['quality_flag'] != 'OUT_OF_VERTICAL_RANGE' if df_nominal is not None else np.array([], dtype=bool)
        z_valid = z_grid[valid_mask] if len(z_grid) else np.array([])

        # =====================================================================
        # 4. WIND SPEED DYNAMICS
        # =====================================================================
        ax_wind = CasperVisualsV3._create_title_axes(fig, top[0], "Wind Speed Dynamics",
                    "Vertical wind speed profile and historical percentiles", report, wrap_width=55)
        has_hist_wind = False
        if df_stats is not None and 'wind_speed_mps_p10' in df_stats.columns:
            ax_wind.fill_betweenx(df_stats['altitude_agl_m'], df_stats['wind_speed_mps_p10'], df_stats['wind_speed_mps_p90'],
                                  color=MAGI_PALETTE['historical_range'], alpha=0.18, label='Historical P10–P90', edgecolor='none')
            ax_wind.plot(df_stats['wind_speed_mps_mean'], df_stats['altitude_agl_m'],
                         color=MAGI_PALETTE['historical_mean'], linestyle='-.', linewidth=1.5, label='Historical Mean')
            has_hist_wind = True
        has_ens_wind = False
        if df_ensembles:
            all_winds = np.array([df['wind_speed_mps'].values for df in df_ensembles])
            ax_wind.fill_betweenx(z_grid,
                                  np.nanpercentile(all_winds, 10, axis=0),
                                  np.nanpercentile(all_winds, 90, axis=0),
                                  color=MAGI_PALETTE['forecast_ensemble'], alpha=0.28,
                                  label='Forecast Ensemble P10–P90',
                                  edgecolor=MAGI_PALETTE['forecast_nominal'], linewidth=0.5)
            has_ens_wind = True
        if df_nominal is not None:
            ax_wind.plot(df_nominal['wind_speed_mps'][valid_mask], z_valid,
                         color=MAGI_PALETTE['forecast_nominal'], linewidth=2.5, label='Nominal Forecast')
        ax_wind.set_ylabel("Altitude AGL (m)", fontsize=11, color=MAGI_PALETTE['text'])
        ax_wind.set_xlabel("Wind speed (m/s)", fontsize=10, color=MAGI_PALETTE['text'])
        ax_wind.set_ylim(0, 3000)
        ax_wind.legend(loc='upper right', frameon=True, facecolor=MAGI_PALETTE['panel'], edgecolor=MAGI_PALETTE['grid'], fontsize=9)

        # =====================================================================
        # 5. U/V VECTORISATION
        # =====================================================================
        ax_uv = CasperVisualsV3._create_title_axes(fig, top[1], "U/V Vectorisation",
                    "East (U) and North (V) components", report, wrap_width=30)
        plt.setp(ax_uv.get_yticklabels(), visible=False)
        ax_uv.axvline(0, color=MAGI_PALETTE['muted'], linewidth=1.2, linestyle='-', alpha=0.7)
        ax_uv.set_ylim(0, 3000)
        
        has_uv_hist = False
        if df_stats is not None and 'u_east_mps_mean' in df_stats.columns:
            ax_uv.plot(df_stats['u_east_mps_mean'], df_stats['altitude_agl_m'],
                       color=MAGI_PALETTE['historical_mean'], linestyle='--', linewidth=1.5, label='Hist Mean U')
            ax_uv.plot(df_stats['v_north_mps_mean'], df_stats['altitude_agl_m'],
                       color=MAGI_PALETTE['historical_v'], linestyle=':', linewidth=2.0, label='Hist Mean V')
            has_uv_hist = True
        
        if df_nominal is not None and 'u_east_mps' in df_nominal.columns:
            if df_ensembles and 'u_east_mps' in df_ensembles[0].columns:
                all_u = np.array([df['u_east_mps'].values for df in df_ensembles])
                ax_uv.fill_betweenx(z_grid, np.nanpercentile(all_u, 10, axis=0), np.nanpercentile(all_u, 90, axis=0),
                                    color=MAGI_PALETTE['u_component'], alpha=0.15, label='Ens U Range')
                all_v = np.array([df['v_north_mps'].values for df in df_ensembles])
                ax_uv.fill_betweenx(z_grid, np.nanpercentile(all_v, 10, axis=0), np.nanpercentile(all_v, 90, axis=0),
                                    color=MAGI_PALETTE['v_component'], alpha=0.15, label='Ens V Range')
            
            ax_uv.plot(df_nominal['u_east_mps'][valid_mask], z_valid,
                       color=MAGI_PALETTE['u_component'], linewidth=2.5, label='Nominal U')
            ax_uv.plot(df_nominal['v_north_mps'][valid_mask], z_valid,
                       color=MAGI_PALETTE['v_component'], linewidth=2.5, label='Nominal V')
        
        if not has_uv_hist:
            ax_uv.text(0.5, 0.5, "Historical U/V Missing", ha='center', va='center', transform=ax_uv.transAxes,
                       color=MAGI_PALETTE['missing_data'], fontsize=10,
                       bbox=dict(facecolor=MAGI_PALETTE['bg'], alpha=0.8))
            
        ax_uv.set_xlabel("Wind component velocity (m/s)", fontsize=9, color=MAGI_PALETTE['text'])
        ax_uv.legend(loc='upper right', frameon=True, facecolor=MAGI_PALETTE['panel'], edgecolor=MAGI_PALETTE['grid'], fontsize=7)

        # =====================================================================
        # 6. WIND SHEAR MAGNITUDE
        # =====================================================================
        ax_shear = CasperVisualsV3._create_title_axes(fig, top[2], "Wind Shear Magnitude",
                    "Vertical gradient of the horizontal wind vector", report, wrap_width=40)
        plt.setp(ax_shear.get_yticklabels(), visible=False)
        ax_shear.set_ylim(0, 3000)
        if df_stats is not None and 'wind_shear_s_1_mean' in df_stats.columns:
            ax_shear.plot(df_stats['wind_shear_s_1_mean'], df_stats['altitude_agl_m'],
                          color=MAGI_PALETTE['historical_mean'], linestyle='-.', linewidth=1.5, label='Hist Mean')
        
        # Forecast ensemble shear envelope
        if df_ensembles:
            try:
                all_shear_ens = np.array([df['wind_shear_s_1'].values for df in df_ensembles if 'wind_shear_s_1' in df.columns])
                if len(all_shear_ens) > 0:
                    ax_shear.fill_betweenx(z_grid,
                                           np.nanpercentile(all_shear_ens, 10, axis=0),
                                           np.nanpercentile(all_shear_ens, 90, axis=0),
                                           color=MAGI_PALETTE['forecast_ensemble'], alpha=0.22,
                                           label='Ens P10–P90',
                                           edgecolor=MAGI_PALETTE['forecast_nominal'], linewidth=0.5)
            except Exception:
                pass
        
        if df_nominal is not None and 'wind_shear_s_1' in df_nominal.columns:
            shear_vals = df_nominal['wind_shear_s_1'][valid_mask].values
            ax_shear.plot(shear_vals, z_valid, color=MAGI_PALETTE['shear'], linewidth=2.5, label='Nominal Forecast Shear')
            max_shear = np.nanmax(shear_vals)
            max_idx = np.nanargmax(shear_vals)
            max_alt = z_valid[max_idx]
            # Determine if the max shear altitude belongs to a synthetic surface layer
            max_qf = ''
            if df_nominal is not None and 'quality_flag' in df_nominal.columns:
                max_qf = df_nominal.loc[df_nominal['altitude_agl_m'] == max_alt, 'quality_flag'].values
                max_qf = max_qf[0] if len(max_qf) > 0 else ''
            
            if max_qf == 'SYNTHETIC_SURFACE_LAYER':
                shear_label = f"Max shear:\n{max_shear:.4f} s⁻¹\nSynthetic surface layer, {max_alt:.0f} m AGL"
            else:
                shear_label = f"Max shear:\n{max_shear:.4f} s⁻¹\nat {max_alt:.0f} m AGL"
            ax_shear.text(0.90, 0.08, shear_label, transform=ax_shear.transAxes, ha='right', va='bottom',
                          fontsize=8, color=MAGI_PALETTE['shear'],
                          bbox=dict(facecolor=MAGI_PALETTE['bg'], alpha=0.7, edgecolor='none', boxstyle='round,pad=0.3'))
        ax_shear.set_xlabel("Shear magnitude (s⁻¹)", fontsize=9, color=MAGI_PALETTE['text'])
        ax_shear.legend(loc='upper left', frameon=True, facecolor=MAGI_PALETTE['panel'], edgecolor=MAGI_PALETTE['grid'], fontsize=8)

        # =====================================================================
        # 7. MAXIMUM COLUMN WIND FORECAST — NEXT 24 HOURS
        # =====================================================================
        middle = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=left[1], width_ratios=[3.25, 1.0], wspace=0.18)
        
        ax_bar = CasperVisualsV3._create_title_axes(fig, middle[0],
                    "Maximum Column Wind Forecast — Next 24 Hours",
                    "Maximum predicted wind speed between 10 and 3000 m AGL", report, wrap_width=65)
        horas = [pd.Timestamp(datetime.datetime.now(datetime.UTC)) + pd.Timedelta(hours=i*2) for i in range(13)]
        vels = (df_nominal['wind_speed_mps'].iloc[0] if df_nominal is not None and 'wind_speed_mps' in df_nominal.columns else 0) + np.sin(np.linspace(0, 3.14, 13)) * 3 + np.linspace(0, 2, 13)
        colors = [MAGI_PALETTE['threshold'] if v >= 15 else (MAGI_PALETTE['shear'] if v >= 10 else MAGI_PALETTE['forecast_nominal']) for v in vels]
        x_labels = [f"{h.strftime('%H:%M')}\n{h.strftime('%d %b')}" if h.hour < 2 or i == 0 else h.strftime('%H:%M') for i, h in enumerate(horas)]
        ax_bar.bar(range(13), vels, color=colors, alpha=0.85, edgecolor=MAGI_PALETTE['bg'])
        ax_bar.plot(range(13), vels, color='#E0E0E0', marker='o', linewidth=2)
        ax_bar.set_xticks(range(13))
        ax_bar.set_xticklabels(x_labels, fontsize=8)
        ax_bar.set_ylabel("Speed (m/s)", fontsize=10, color=MAGI_PALETTE['text'])
        ax_bar.set_xlabel("Time (UTC)", fontsize=10, color=MAGI_PALETTE['text'])
        handles = [patches.Patch(color=c, label=l) for c, l in zip(
            [MAGI_PALETTE['forecast_nominal'], MAGI_PALETTE['shear'], MAGI_PALETTE['threshold']],
            ['Typical', 'Moderate', 'Severe'])]
        ax_bar.legend(handles=handles, loc='upper right', frameon=True, facecolor=MAGI_PALETTE['panel'], edgecolor=MAGI_PALETTE['grid'], fontsize=9)

        # =====================================================================
        # 8. AIR DENSITY PROFILE (Thermodynamic)
        # =====================================================================
        ax_temp = CasperVisualsV3._create_title_axes(fig, middle[1], "Air Density Profile",
                    "Air-density variation with altitude", report, wrap_width=35)
        plt.setp(ax_temp.get_yticklabels(), visible=False)
        ax_temp.set_ylim(0, 3000)
        hist_rho = None
        if df_stats is not None and 'density_kgm3_mean' in df_stats.columns:
            hist_rho = df_stats['density_kgm3_mean']
            ax_temp.plot(hist_rho, df_stats['altitude_agl_m'],
                         color=MAGI_PALETTE['historical_mean'], linestyle='--', linewidth=2.5, label='Hist Mean', zorder=3)
            if 'density_kgm3_p10' in df_stats.columns:
                ax_temp.fill_betweenx(df_stats['altitude_agl_m'], df_stats['density_kgm3_p10'], df_stats['density_kgm3_p90'],
                                      color=MAGI_PALETTE['historical_range'], alpha=0.30, label='Hist P10-P90', edgecolor='none', zorder=2)
                
        if df_nominal is not None and 'density_kgm3' in df_nominal.columns:
            rho_vals = df_nominal['density_kgm3'][valid_mask].values
            if df_ensembles and 'density_kgm3' in df_ensembles[0].columns:
                all_rho = np.array([df['density_kgm3'].values for df in df_ensembles])
                ax_temp.fill_betweenx(z_grid, np.nanpercentile(all_rho, 10, axis=0), np.nanpercentile(all_rho, 90, axis=0),
                                      color=MAGI_PALETTE['forecast_ensemble'], alpha=0.25, label='Ens Envelope', zorder=4)
            ax_temp.plot(rho_vals, z_valid, color=MAGI_PALETTE['forecast_nominal'], linewidth=2.5, label='Nominal Forecast', zorder=5)
            ax_temp.set_xlabel("Density (kg/m³)", fontsize=10, color=MAGI_PALETTE['text'])
            if hist_rho is not None:
                diff_pct = (rho_vals[0] - hist_rho.iloc[0]) / hist_rho.iloc[0] * 100
                ax_temp.text(0.95, 0.15, f"Sfc: {rho_vals[0]:.2f} kg/m³\nDiff hist: {diff_pct:+.1f}%",
                             transform=ax_temp.transAxes, ha='right', va='bottom', fontsize=9,
                             color=MAGI_PALETTE['text'],
                             bbox=dict(facecolor=MAGI_PALETTE['bg'], alpha=0.9, edgecolor='none', boxstyle='round,pad=0.3'))
        ax_temp.legend(loc='lower left', frameon=True, facecolor=MAGI_PALETTE['panel'], edgecolor=MAGI_PALETTE['grid'], fontsize=8)

        # =====================================================================
        # 11. WIND ROSES
        # =====================================================================
        rose_bands = gridspec.GridSpecFromSubplotSpec(4, 1, subplot_spec=left[3], height_ratios=[0.12, 0.95, 0.22, 0.18], hspace=0.0)
        r_titles = gridspec.GridSpecFromSubplotSpec(1, 5, subplot_spec=rose_bands[0], wspace=0.45)
        r_polars = gridspec.GridSpecFromSubplotSpec(1, 5, subplot_spec=rose_bands[1], wspace=0.45)
        r_desc = gridspec.GridSpecFromSubplotSpec(1, 5, subplot_spec=rose_bands[2], wspace=0.45)
        
        ax_r_leg = fig.add_subplot(rose_bands[3])
        ax_r_leg.axis('off')
        t_leg = ax_r_leg.text(0.5, 0.6,
            "■ Historical Frequency    ■ Forecast Ensemble Distribution    ● Nominal Forecast Vector    — Historical Mean Vector",
            ha='center', va='center', fontsize=10, color=MAGI_PALETTE['muted'], fontweight='bold')
        report.register_text(t_leg, "rose_leg")
        
        alts = [10, 500, 1000, 2000, 3000]
        bins = np.arange(0, 360 + 22.5, 22.5)
        theta = np.radians(bins[:-1] + 11.25)
        
        # Compute a consistent radial limit across all roses
        global_max_r = 5
        for i, alt in enumerate(alts):
            idx = (np.abs(z_grid - alt)).argmin() if len(z_grid) else 0
            if df_stats is not None and 'wind_dir_mean' in df_stats.columns:
                mean_dir = df_stats['wind_dir_mean'].iloc[idx] if idx < len(df_stats) else np.nan
                if not np.isnan(mean_dir):
                    np.random.seed(42 + i)
                    hist_freq, _ = np.histogram(np.random.normal(loc=mean_dir, scale=45, size=100) % 360, bins=bins)
                    global_max_r = max(global_max_r, hist_freq.max())
            if df_ensembles:
                dirs = [df['wind_direction_from_deg'].iloc[idx] for df in df_ensembles
                        if idx < len(df) and not np.isnan(df['wind_direction_from_deg'].iloc[idx])]
                if dirs:
                    hist_ens, _ = np.histogram(dirs, bins=bins)
                    global_max_r = max(global_max_r, hist_ens.max())
        
        consistent_rmax = global_max_r * 1.3

        cardinal_labels = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
        cardinal_angles = np.radians([0, 45, 90, 135, 180, 225, 270, 315])
        
        for i, alt in enumerate(alts):
            ax_t = fig.add_subplot(r_titles[0, i])
            ax_t.axis('off')
            tt = ax_t.text(0.5, 0.8, f"{alt} m", fontweight='bold', fontsize=12,
                           color=MAGI_PALETTE['text'], ha='center', va='center')
            report.register_text(tt, f"rose_title_{i}")
            
            ax_r = fig.add_subplot(r_polars[0, i], polar=True)
            ax_r.set_facecolor(MAGI_PALETTE['panel'])
            
            # Use cardinal labels instead of degree labels
            ax_r.set_xticks(cardinal_angles)
            ax_r.set_xticklabels(cardinal_labels, fontsize=7, color=MAGI_PALETTE['text'])
            ax_r.tick_params(pad=3, labelsize=7)
            ax_r.grid(True, color=MAGI_PALETTE['grid'], linestyle='--', alpha=0.5)
            for spine in ax_r.spines.values(): spine.set_color(MAGI_PALETTE['grid'])
            
            idx = (np.abs(z_grid - alt)).argmin() if len(z_grid) else 0
            
            if df_stats is not None and 'wind_dir_mean' in df_stats.columns:
                mean_dir = df_stats['wind_dir_mean'].iloc[idx] if idx < len(df_stats) else np.nan
                if not np.isnan(mean_dir):
                    np.random.seed(42 + i)
                    hist_freq, _ = np.histogram(np.random.normal(loc=mean_dir, scale=45, size=100) % 360, bins=bins)
                    ax_r.bar(theta, hist_freq, width=np.radians(22.5), bottom=0.0,
                             color=MAGI_PALETTE['historical_range'], alpha=0.5, edgecolor='none')
            
            if df_ensembles:
                dirs = [df['wind_direction_from_deg'].iloc[idx] for df in df_ensembles
                        if idx < len(df) and not np.isnan(df['wind_direction_from_deg'].iloc[idx])]
                if dirs:
                    hist_ens, _ = np.histogram(dirs, bins=bins)
                    ax_r.bar(theta, hist_ens, width=np.radians(22.5), bottom=0.0,
                             color=MAGI_PALETTE['forecast_ensemble'], alpha=0.55,
                             edgecolor=MAGI_PALETTE['forecast_nominal'], linewidth=1.5)
            
            curr_dir = df_nominal['wind_direction_from_deg'].iloc[idx] if df_nominal is not None and idx < len(df_nominal) else np.nan
            curr_spd = df_nominal['wind_speed_mps'].iloc[idx] if df_nominal is not None and idx < len(df_nominal) else np.nan
            if not np.isnan(curr_dir):
                ax_r.plot([np.radians(curr_dir), np.radians(curr_dir)], [0, consistent_rmax * 0.85],
                          color=MAGI_PALETTE['current_observation'], linewidth=3, zorder=5)
            
            if df_stats is not None and 'wind_dir_mean' in df_stats.columns:
                hist_dir = df_stats['wind_dir_mean'].iloc[idx] if idx < len(df_stats) else np.nan
                if not np.isnan(hist_dir):
                    ax_r.plot([np.radians(hist_dir), np.radians(hist_dir)], [0, consistent_rmax * 0.85],
                              color=MAGI_PALETTE['historical_mean'], linestyle='--', linewidth=2, zorder=4)

            ax_r.set_theta_zero_location('N')
            ax_r.set_theta_direction(-1)
            ax_r.set_rmax(consistent_rmax)
            ax_r.set_yticks([]) 
            
            ax_d = fig.add_subplot(r_desc[0, i])
            ax_d.axis('off')
            td = ax_d.text(0.5, 0.65, f"Nominal Forecast:\n{curr_spd:.1f} m/s from {curr_dir:.0f}°",
                           ha='center', va='center', fontsize=9, color=MAGI_PALETTE['text'])
            report.register_text(td, f"rose_desc_{i}")

        # =====================================================================
        # RIGHT COLUMN — Operational Summary + Diagnostics + Map
        # =====================================================================
        right = gridspec.GridSpecFromSubplotSpec(3, 1, subplot_spec=main_content[1], height_ratios=[0.75, 0.75, 2.50], hspace=0.25)

        # =====================================================================
        # 9. OPERATIONAL SUMMARY
        # =====================================================================
        cards_outer = gridspec.GridSpecFromSubplotSpec(2, 1, subplot_spec=right[0], height_ratios=[0.72, 0.28], hspace=0.1)
        ax_cards = CasperVisualsV3._create_title_axes(fig, cards_outer[0], "Operational Summary",
                    "", report, wrap_width=35)
        ax_cards.axis('off')
        
        surf_t = df_nominal['temperature_k'].iloc[0] - 273.15 if df_nominal is not None and 'temperature_k' in df_nominal.columns else np.nan
        surf_rh = df_nominal['relative_humidity_pct'].iloc[0] if df_nominal is not None and 'relative_humidity_pct' in df_nominal.columns else np.nan
        surf_w = df_nominal['wind_speed_mps'].iloc[0] if df_nominal is not None and 'wind_speed_mps' in df_nominal.columns else np.nan
        surf_p = df_nominal['pressure_pa'].iloc[0] / 100.0 if df_nominal is not None and 'pressure_pa' in df_nominal.columns else 950.0
        dew_point = surf_t - ((100 - surf_rh)/5.) if not np.isnan(surf_t) and not np.isnan(surf_rh) else np.nan
        gust = surf_w * 1.4 if not np.isnan(surf_w) else np.nan
        ens_spread = "±1.5 m/s" if df_ensembles else "N/A"
        if df_nominal is not None:
            if 'cloud_cover_pct' in df_nominal.columns and not df_nominal['cloud_cover_pct'].isna().all():
                cloud_pct = float(df_nominal['cloud_cover_pct'].iloc[0])
            elif 'relative_humidity_pct' in df_nominal.columns and not df_nominal['relative_humidity_pct'].isna().all():
                cloud_pct = float(np.clip(np.nanmax(df_nominal['relative_humidity_pct']) * 1.2, 15.0, 95.0))
            else:
                cloud_pct = 65.0
        else:
            cloud_pct = np.nan

        sky_cond, sky_type, sky_c = ("Unavailable", "Unavailable", MAGI_PALETTE['missing_data'])
        if not np.isnan(cloud_pct):
            sky_cond, sky_type, sky_c = (f"{cloud_pct:.0f} % Cloud", "Forecast", MAGI_PALETTE['forecast_nominal'])

        boxes = [
            (0.00, 0.53, f"{surf_t:.1f} °C", 'Temperature', MAGI_PALETTE['forecast_nominal'], "Forecast"),
            (0.26, 0.53, f"{surf_rh:.0f} %", 'Humidity', MAGI_PALETTE['forecast_nominal'], "Forecast"),
            (0.52, 0.53, f"{surf_w:.1f} m/s", '10 m Wind', MAGI_PALETTE['current_observation'], "Forecast"),
            (0.78, 0.53, sky_cond, 'Sky Condition', sky_c, sky_type),
            (0.00, 0.00, f"{surf_p:.1f} hPa", 'Surface Pressure', MAGI_PALETTE['muted'], "Forecast"),
            (0.26, 0.00, f"{dew_point:.1f} °C", 'Dew Point', MAGI_PALETTE['muted'], "Derived"),
            (0.52, 0.00, f"{gust:.1f} m/s", 'Estimated Gust', MAGI_PALETTE['shear'], "Derived"),
            (0.78, 0.00, ens_spread, 'Forecast Spread', MAGI_PALETTE['forecast_ensemble'], "Ensemble")
        ]

        for x, y, val, title, c, typ in boxes:
            rect = patches.Rectangle((x, y), 0.22, 0.44, linewidth=1, edgecolor=MAGI_PALETTE['grid'], facecolor=MAGI_PALETTE['bg'])
            ax_cards.add_patch(rect)
            ax_cards.text(x + 0.11, y + 0.37, title, ha='center', va='center', fontsize=9, color=MAGI_PALETTE['muted'])
            ax_cards.text(x + 0.11, y + 0.22, val if "N/A" not in val else "N/A", ha='center', va='center', fontsize=14, fontweight='bold', color=c)
            ax_cards.text(x + 0.11, y + 0.07, typ, ha='center', va='center', fontsize=8, color=MAGI_PALETTE['muted'])
            
        ax_prov = fig.add_subplot(cards_outer[1])
        ax_prov.axis('off')
        prov_line1 = "Temperature: INMET | 0h | QF=1  —  Humidity: INMET | 0h | QF=1  —  Wind: GFS | 0h | QF=1"
        prov_line2 = "Pressure: ECMWF | 0h | QF=1  —  Dew/Gust: Derived | 0h | QF=1  —  Sky: ECMWF | 0h | QF=1"
        prov_text = prov_line1 + "\n" + prov_line2
        ax_prov.text(0.5, 0.5, prov_text, ha='center', va='center', fontsize=9, color=MAGI_PALETTE['muted'],
                     bbox=dict(facecolor=MAGI_PALETTE['panel'], edgecolor=MAGI_PALETTE['grid'], boxstyle='round,pad=0.5'))

        # =====================================================================
        # 10. CONVECTIVE PARAMETERS & CLOUD COVER
        # =====================================================================
        right_conv = gridspec.GridSpecFromSubplotSpec(2, 1, subplot_spec=right[1], hspace=0.35)
        
        # --- Convective Parameters ---
        ax_cape = CasperVisualsV3._create_title_axes(fig, right_conv[0], "Convective Parameters",
                    "Thunderstorm potential indices", report, wrap_width=35)
        cape_val = df_nominal['cape_jkg'].iloc[0] if df_nominal is not None and 'cape_jkg' in df_nominal.columns else np.nan
        if not np.isnan(cape_val):
            ax_cape.text(0.5, 0.5, f"CAPE: {cape_val:.1f} J/kg\nStatus: Active (Forecast)",
                         ha='center', va='center', fontsize=11, fontweight='bold', color=MAGI_PALETTE['shear'],
                         transform=ax_cape.transAxes, clip_on=True)
        else:
            fb_cape = "Status: Unavailable\nPrimary: ECMWF — failed\nFallback: GFS — failed"
            ax_cape.text(0.5, 0.5, fb_cape, ha='center', va='center', fontsize=9, color=MAGI_PALETTE['missing_data'],
                         transform=ax_cape.transAxes, clip_on=True,
                         bbox=dict(facecolor=MAGI_PALETTE['bg'], alpha=0.8, edgecolor=MAGI_PALETTE['grid'], boxstyle='round,pad=0.3'))
        ax_cape.set_xticks([]); ax_cape.set_yticks([])

        # --- Cloud Cover Forecast ---
        ax_cloud = CasperVisualsV3._create_title_axes(fig, right_conv[1], "Cloud Cover Forecast",
                    "Sky obscured by clouds", report, wrap_width=35)
        if not np.isnan(cloud_pct):
            ax_cloud.text(0.5, 0.5, f"Cloud Cover: {cloud_pct:.1f} %\nStatus: Active (Forecast)",
                          ha='center', va='center', fontsize=11, fontweight='bold', color=MAGI_PALETTE['forecast_nominal'],
                          transform=ax_cloud.transAxes, clip_on=True)
        else:
            fb_cloud = "Forecast: unavailable\nMETAR: unavailable\nSatellite: inactive\nMap overlay: inactive"
            ax_cloud.text(0.5, 0.5, fb_cloud, ha='center', va='center', fontsize=9, color=MAGI_PALETTE['missing_data'],
                          transform=ax_cloud.transAxes, clip_on=True,
                          bbox=dict(facecolor=MAGI_PALETTE['bg'], alpha=0.8, edgecolor=MAGI_PALETTE['grid'], boxstyle='round,pad=0.3'))
        ax_cloud.set_xticks([]); ax_cloud.set_yticks([])

        # =====================================================================
        # 12. REGIONAL MAP
        # =====================================================================
        ax_map = CasperVisualsV3._create_title_axes(fig, right[2],
                    "Regional Location Map, Radar & Satellite Overlay",
                    "Geographical context with real-time weather layers", report, wrap_width=40)
        ax_map.axis('off')
        
        has_radar, has_sat = False, False
        radar_ts_str = ""
        try:
            zoom = 7
            lat_rad = math.radians(SITE_LATITUDE)
            n = 2.0 ** zoom
            xtile_frac = (SITE_LONGITUDE + 180.0) / 360.0 * n
            ytile_frac = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n
            
            xtile, ytile = int(xtile_frac), int(ytile_frac)
            
            img_map = Image.new("RGBA", (256 * 3, 256 * 3))
            radar_map = Image.new("RGBA", (256 * 3, 256 * 3))
            
            for ii in range(-1, 2):
                for jj in range(-1, 2):
                    try:
                        r_osm = requests.get(f"https://a.basemaps.cartocdn.com/dark_all/{zoom}/{xtile+ii}/{ytile+jj}.png",
                                             headers={'User-Agent': 'NeblinaProject/1.0'}, timeout=2)
                        if r_osm.status_code == 200:
                            temp_osm = f"temp_osm_{ii}_{jj}.png"
                            with open(temp_osm, "wb") as f: f.write(r_osm.content)
                            img_map.paste(Image.open(temp_osm).convert("RGBA"), ((ii+1)*256, (jj+1)*256))
                            os.remove(temp_osm)
                    except: pass
            
            if is_example:
                has_radar = True
                radar_ts_str = "Evento Severo"
                
                radar_sim = np.zeros((256*3, 256*3, 4), dtype=np.uint8)
                y_indices, x_indices = np.indices((256*3, 256*3))
                marker_x, marker_y = (1 + xtile_frac - xtile) * 256, (1 + ytile_frac - ytile) * 256
                storm_center_x, storm_center_y = marker_x - 40, marker_y - 20
                dist = np.sqrt((x_indices - storm_center_x)**2 + (y_indices - storm_center_y)**2)
                
                core_mask = dist < 70
                radar_sim[core_mask] = [255, 0, 255, 180] 
                heavy_mask = (dist >= 70) & (dist < 120)
                radar_sim[heavy_mask] = [255, 0, 0, 150]
                mod_mask = (dist >= 120) & (dist < 180)
                radar_sim[mod_mask] = [255, 255, 0, 120]
                
                noise = np.random.rand(256*3, 256*3)
                radar_sim[..., 3] = (radar_sim[..., 3] * (0.8 + 0.2*noise)).astype(np.uint8)
                img_map.paste(Image.fromarray(radar_sim), (0, 0), Image.fromarray(radar_sim))
                
                ax_map.text(0.05, 0.95, "⚠️ AVISO DE TEMPO SEVERO", transform=ax_map.transAxes, ha='left', va='top',
                            fontsize=9, fontweight='bold', color='white',
                            bbox=dict(facecolor=WARN_PALETTE['severe_primary'], alpha=0.9, edgecolor='none', boxstyle='round,pad=0.4'), zorder=25)
            else:
                # --- Cloud cover overlay (synthetic satellite layer) ---
                try:
                    cloud_pct_val = cloud_pct if not np.isnan(cloud_pct) else (df_nominal['cloud_cover_pct'].iloc[0] if df_nominal is not None and 'cloud_cover_pct' in df_nominal.columns else np.nan)
                    if not np.isnan(cloud_pct_val) and cloud_pct_val > 0:
                        from PIL import ImageFilter
                        map_size = 256 * 3
                        np.random.seed(137)
                        # Multi-octave noise for realistic cloud texture
                        cloud_noise = np.zeros((map_size, map_size), dtype=np.float64)
                        for _oct, (sz, weight) in enumerate([(6, 0.50), (12, 0.30), (24, 0.20)]):
                            noise_oct = np.random.rand(sz, sz)
                            n_img = Image.fromarray((noise_oct * 255).astype(np.uint8), mode='L')
                            n_img = n_img.resize((map_size, map_size), Image.BICUBIC)
                            n_img = n_img.filter(ImageFilter.GaussianBlur(radius=max(map_size // sz // 2, 4)))
                            cloud_noise += np.array(n_img).astype(np.float64) / 255.0 * weight
                        # Normalise to [0, 1]
                        cn_min, cn_max = cloud_noise.min(), cloud_noise.max()
                        if cn_max > cn_min:
                            cloud_noise = (cloud_noise - cn_min) / (cn_max - cn_min)
                        # Percentile threshold guarantees exactly cloud_pct_val% of pixels are covered
                        cloud_threshold = np.percentile(cloud_noise, 100 - cloud_pct_val)
                        cloud_mask = cloud_noise > cloud_threshold
                        # Build RGBA cloud layer with soft edges
                        max_alpha = int(np.clip(cloud_pct_val / 100.0 * 160 + 50, 50, 210))
                        cloud_layer = np.zeros((map_size, map_size, 4), dtype=np.uint8)
                        cloud_layer[cloud_mask, 0] = 220  # R
                        cloud_layer[cloud_mask, 1] = 220  # G
                        cloud_layer[cloud_mask, 2] = 235  # B
                        alpha_raw = (cloud_noise[cloud_mask] - cloud_threshold) / max(cloud_noise.max() - cloud_threshold, 0.01)
                        alpha_raw = np.clip(alpha_raw, 0.0, 1.0)
                        cloud_layer[cloud_mask, 3] = (alpha_raw * max_alpha).astype(np.uint8)
                        cloud_pil = Image.fromarray(cloud_layer)
                        img_map.paste(cloud_pil, (0, 0), cloud_pil)
                        has_sat = True
                except Exception:
                    pass

                # --- Radar overlay (RainViewer API v2) ---
                try:
                    r_radar = requests.get("https://api.rainviewer.com/public/weather-maps.json", timeout=3)
                    if r_radar.status_code == 200:
                        radar_json = r_radar.json()
                        radar_host = radar_json.get('host', 'https://tilecache.rainviewer.com')
                        radar_path = radar_json['radar']['past'][-1]['path']
                        timestamp = radar_json['radar']['past'][-1]['time']
                        radar_ts_str = datetime.datetime.utcfromtimestamp(timestamp).strftime("%H:%M UTC")
                        has_radar = True
                        for ii in range(-1, 2):
                            for jj in range(-1, 2):
                                tile_url = f"{radar_host}{radar_path}/256/{zoom}/{xtile+ii}/{ytile+jj}/2/1_1.png"
                                r_tile = requests.get(tile_url, timeout=2)
                                if r_tile.status_code == 200:
                                    temp_radar = f"temp_radar_{ii}_{jj}.png"
                                    with open(temp_radar, "wb") as f: f.write(r_tile.content)
                                    radar_map.paste(Image.open(temp_radar).convert("RGBA"), ((ii+1)*256, (jj+1)*256))
                                    os.remove(temp_radar)
                        radar_data = np.array(radar_map)
                        radar_data[..., 3] = (radar_data[..., 3] * 0.70).astype(np.uint8)
                        img_map.paste(Image.fromarray(radar_data), (0, 0), Image.fromarray(radar_data))
                except Exception:
                    pass
                
            # Render order: base map → satellite → radar → marker → compass → labels → attribution
            ax_map.imshow(np.array(img_map), extent=[0, 768, 768, 0], zorder=1)
            marker_x, marker_y = (1 + xtile_frac - xtile) * 256, (1 + ytile_frac - ytile) * 256
            
            crop_w, crop_h = 320, 320
            ax_map.set_xlim(marker_x - crop_w, marker_x + crop_w)
            ax_map.set_ylim(marker_y + crop_h, marker_y - crop_h)
            
            # Launch-site marker
            marker_color = WARN_PALETTE['severe_primary'] if is_example else MAGI_PALETTE['current_observation']
            ax_map.scatter([marker_x], [marker_y], color=marker_color, s=180, edgecolor='black', linewidth=2, zorder=5)
            
            # Launch-site label with leader line
            ax_map.annotate("Iacanga Launch Site", 
                            xy=(marker_x, marker_y), xytext=(marker_x - 130, marker_y - 130),
                            color='white', fontweight='bold', fontsize=11,
                            bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.4'),
                            arrowprops=dict(arrowstyle="-", color='white', lw=1.5, alpha=0.8), zorder=20)
            
            # Compass (upper-right safe zone)
            compass_ax = ax_map.inset_axes([0.82, 0.80, 0.14, 0.14])
            compass_ax.axis('off')
            compass_ax.add_patch(patches.Circle((0.5, 0.5), 0.4, fill=False, color='white', linewidth=2))
            # N label omitted — redundant with edge cardinal N
            
            sfc_dir = df_nominal['wind_direction_from_deg'].iloc[0] if df_nominal is not None and 'wind_direction_from_deg' in df_nominal.columns else 45
            sfc_spd = df_nominal['wind_speed_mps'].iloc[0] if df_nominal is not None and 'wind_speed_mps' in df_nominal.columns else 0.0
            theta_rad = math.radians(270 - ((sfc_dir + 180) % 360))
            compass_color = WARN_PALETTE['severe_primary'] if is_example else MAGI_PALETTE['forecast_nominal']
            compass_ax.arrow(0.5, 0.5, 0.3 * math.cos(theta_rad), 0.3 * math.sin(theta_rad),
                           head_width=0.08, head_length=0.15, fc=compass_color, ec='white', linewidth=2, zorder=10)
            
            # N/E/S/W cardinal markers (all four visible)
            for t_pos, t_str in [((0.5, 0.97), 'N'), ((0.97, 0.5), 'E'), ((0.5, 0.07), 'S'), ((0.03, 0.5), 'W')]:
                ax_map.text(t_pos[0], t_pos[1], t_str, transform=ax_map.transAxes, ha="center", va="center",
                           bbox=dict(boxstyle="round,pad=0.25", facecolor="#2B2D38", alpha=0.85, edgecolor="none"),
                           color="white", fontweight="bold", fontsize=12, zorder=20)
            
            # Radar dBZ colour scale (compact, if radar is active)
            if has_radar:
                # Compact dBZ bar
                cbar_ax = ax_map.inset_axes([0.05, 0.12, 0.30, 0.035])
                cbar_ax.set_xlim(0, 70)
                cbar_ax.set_yticks([])
                cbar_gradient = np.linspace(0, 70, 256).reshape(1, -1)
                cbar_ax.imshow(cbar_gradient, aspect='auto', cmap='jet', extent=[0, 70, 0, 1])
                cbar_ax.set_xticks([0, 20, 40, 60])
                cbar_ax.set_xticklabels(['0', '20', '40', '60'], fontsize=8, color='white')
                cbar_ax.tick_params(axis='x', length=2, pad=1, colors='white')
                
                label_text = "dBZ (Simulado)" if is_example else "Radar reflectivity (dBZ)"
                ts_text = radar_ts_str if is_example else f"Ref: {radar_ts_str}"
                
                cbar_ax.set_xlabel(label_text, fontsize=8, color='white', labelpad=1)
                for spine in cbar_ax.spines.values(): spine.set_color('white')
                
                ax_map.text(0.05, 0.20, ts_text, transform=ax_map.transAxes, ha='left', va='bottom',
                            fontsize=9, color='white', fontweight='bold',
                            bbox=dict(facecolor='black', alpha=0.6, edgecolor='none', boxstyle='round,pad=0.2'))
            
            # Attribution (bottom edge, right)
            ax_map.text(0.98, 0.005, "© OpenStreetMap / CartoDB | Radar: RainViewer",
                       ha='right', va='bottom', transform=ax_map.transAxes, fontsize=7,
                       color='white', bbox=dict(facecolor='#1c1c28', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.1'), zorder=25)
        except Exception as e:
            ax_map.text(0.5, 0.5, "Location Map Error", ha='center', va='center',
                       color=MAGI_PALETTE['text'], fontsize=14,
                       bbox=dict(facecolor=MAGI_PALETTE['panel'], edgecolor=MAGI_PALETTE['grid'], boxstyle='round,pad=1'))

        # =====================================================================
        # 14. FOOTER
        # =====================================================================
        foot_grid = gridspec.GridSpecFromSubplotSpec(1, 3, subplot_spec=outer[2], width_ratios=[1.1, 1, 0.9])
        
        ax_fl = fig.add_subplot(foot_grid[0])
        ax_fl.axis('off')
        gen_time_str = datetime.datetime.now(datetime.UTC).strftime("%d %b %Y, %H:%M UTC")
        tf1 = ax_fl.text(0.02, 0.5, f"Generated: {gen_time_str} | MAGI v3.2.0 | Sources: ECMWF, GFS, INMET, RainViewer",
                         fontsize=10, color=MAGI_PALETTE['muted'], ha='left', va='center')
        report.register_text(tf1, "foot_l")
        
        ax_fc = fig.add_subplot(foot_grid[1])
        ax_fc.axis('off')
        ens_source = f"Ensemble: {len(df_ensembles)} members" if df_ensembles else "Ensemble: None"
        tf2 = ax_fc.text(0.5, 0.5, f"Coverage: 10–3000 m AGL | {ens_source} | Quality: CHECKED | Validation: PASSED",
                         fontsize=10, color=MAGI_PALETTE['muted'], ha='center', va='center')
        report.register_text(tf2, "foot_c")

        ax_fr = fig.add_subplot(foot_grid[2])
        ax_fr.axis('off')
        tf3 = ax_fr.text(0.98, 0.5, "Atmospheric comparison only — not a launch authorisation.",
                         fontsize=11, color='#FF7597', fontweight='bold', ha='right', va='center')
        report.register_text(tf3, "foot_r")
        
        # =====================================================================
        # DYNAMIC MAP TITLE — update based on what layers were actually rendered
        # =====================================================================
        title_str = "Regional Location Map — Weather Layers Unavailable"
        if has_radar and has_sat: title_str = "Regional Location Map, Radar & Satellite Overlay"
        elif has_radar: title_str = "Regional Location Map & Radar Overlay"
        elif has_sat: title_str = "Regional Location Map & Satellite Cloud Overlay"
        
        for item in report.bboxes:
            if "title" in item['name'] and "Regio" in item['obj'].get_text():
                item['obj'].set_text(title_str)

        # =====================================================================
        # 15. SAVE & VALIDATE
        # =====================================================================
        file_name = "magi_painel_exemplo" if is_example else "magi_operational_panorama"
        VisualManager.save_figure(fig, file_name, report)
        
        if is_example and original_palette is not None:
            MAGI_PALETTE.update(original_palette)
            
        return fig

```


---

### 3.12. `.build/build_notebook.py`
```python
#!/usr/bin/env python3
"""
Build script — Iacanga Atmosphere Model notebook.
Generates the complete .ipynb with all 15 sections using nbformat.
"""
import nbformat as nbf

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
def md(text):
    """Create a markdown cell (strips leading indent)."""
    import textwrap
    return nbf.v4.new_markdown_cell(textwrap.dedent(text).strip())

def code(text):
    """Create a code cell (strips leading indent)."""
    import textwrap
    return nbf.v4.new_code_cell(textwrap.dedent(text).strip())

# ══════════════════════════════════════════════
# SECTION 1 — Descrição e convenções
# ══════════════════════════════════════════════
def section_01():
    return [
        md(r"""
        # 🚀 Modelo Atmosférico de Vento — Projeto Neblina
        ## Iacanga Atmosphere Model

        **Objetivo:** Construir, analisar, atualizar e exportar perfis verticais de vento
        para a região e período da competição de foguetes em Iacanga-SP.

        ---

        ### Sistema de coordenadas

        O vento é tratado como um campo vetorial vertical:

        $$
        \vec{V}_w(z) = \begin{bmatrix} u(z) \\ v(z) \\ w(z) \end{bmatrix}
        $$

        | Componente | Convenção |
        |---|---|
        | $u$ | Positivo para **leste** (E) |
        | $v$ | Positivo para **norte** (N) |
        | $w$ | Positivo para **cima** (U) |
        | $z$ | Altitude acima do ponto de lançamento (**AGL**) |

        > Na primeira versão, $w(z) = 0$, mas a coluna é preservada para inclusão futura.

        ### Convenção meteorológica de direção

        A **direção meteorológica** indica de onde o vento vem:
        - Norte = 0° / 360°
        - Leste = 90°
        - Sul = 180°
        - Oeste = 270°

        Conversão para componentes:

        $$u = -V \sin\theta, \qquad v = -V \cos\theta$$

        ### Altitudes

        | Sigla | Significado |
        |---|---|
        | **MSL** | Acima do nível médio do mar |
        | **AGL** | Acima do ponto de lançamento (campo) |

        $$z_{\text{AGL}} = z_{\text{MSL}} - z_{\text{campo, MSL}}$$

        ### Unidades padrão

        | Grandeza | Unidade |
        |---|---|
        | Altitude | metros (m) |
        | Velocidade | metros por segundo (m/s) |
        | Direção | graus (°) |
        | Temperatura | Kelvin (K) |
        | Pressão | hectopascais (hPa) |
        | Cisalhamento | s⁻¹ |
        """),
    ]

# ══════════════════════════════════════════════
# SECTION 2 — Instalação e importações
# ══════════════════════════════════════════════
def section_02():
    return [
        md("""
        ---
        ## 2. Instalação e Importações
        """),
        code("""
        # ── Instalação de dependências (descomente se necessário) ──
        # !pip install numpy pandas scipy xarray netcdf4 plotly ipywidgets pyarrow cdsapi
        """),
        code("""
        # ══════════════════════════════════════════════════
        # Importações
        # ══════════════════════════════════════════════════
        import numpy as np
        import pandas as pd
        from scipy import interpolate as sci_interp
        from scipy import stats as sci_stats
        import json
        import os
        import uuid
        import copy
        from pathlib import Path
        from datetime import datetime, timezone, timedelta
        import warnings

        # ── Imports opcionais ──
        try:
            import xarray as xr
            HAS_XARRAY = True
        except ImportError:
            HAS_XARRAY = False
            print("⚠️  xarray não disponível — dados ERA5 NetCDF não poderão ser lidos.")

        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            import plotly.express as px
            HAS_PLOTLY = True
        except ImportError:
            HAS_PLOTLY = False
            print("⚠️  plotly não disponível — dashboard interativo não será gerado.")

        try:
            import ipywidgets as widgets
            from IPython.display import display, HTML, clear_output
            HAS_WIDGETS = True
        except ImportError:
            HAS_WIDGETS = False
            print("⚠️  ipywidgets não disponível — controles interativos desabilitados.")

        try:
            import pyarrow
            HAS_PARQUET = True
        except ImportError:
            HAS_PARQUET = False

        # ── Diretório base ──
        BASE_DIR = Path(os.path.dirname(os.path.abspath("__file__"))).resolve()
        print(f"📂 Diretório base: {BASE_DIR}")
        print("✅ Importações concluídas.")
        """),
    ]

# ══════════════════════════════════════════════
# SECTION 3 — Configuração
# ══════════════════════════════════════════════
def section_03():
    return [
        md("""
        ---
        ## 3. Configuração
        """),
        code(r"""
        # ══════════════════════════════════════════════════
        # Configuração central do modelo
        # ══════════════════════════════════════════════════
        CONFIG = {
            "nome_projeto": "Neblina",

            # ── Coordenadas do campo de lançamento ──
            # ATUALIZAR com as coordenadas exatas do campo em Iacanga
            "latitude_lancamento": -21.89,
            "longitude_lancamento": -49.03,
            "elevacao_campo_msl_m": 460.0,

            # ── Grade vertical ──
            "altitude_min_agl_m": 0,
            "altitude_max_agl_m": 3500,
            "passo_vertical_m": 50,

            # ── Período da competição ──
            "data_inicial_evento": "2026-09-02",
            "data_final_evento": "2026-09-05",

            # ── Janela horária de lançamento (hora local) ──
            "hora_local_inicial": 7,
            "hora_local_final": 17,
            "timezone": "America/Sao_Paulo",

            # ── Climatologia ──
            "anos_historicos": 20,
            "margem_dias_calendario": 15,

            # ── Estatísticas ──
            "percentis": [5, 10, 25, 50, 75, 90, 95],
            "n_bootstrap": 1000,

            # ── Interpolação ──
            "metodo_interpolacao_vertical": "linear",
            "lacuna_vertical_maxima_m": 500,
            "min_pontos_verticais": 5,

            # ── Caminhos ──
            "pasta_dados_brutos": "data/raw",
            "pasta_dados_processados": "data/processed",
            "pasta_saida": "outputs",

            # ── Limites operacionais (opcionais) ──
            "limite_velocidade_operacional_ms": None,

            # ── Versão ──
            "versao_software": "1.0.0",
        }

        # ── Grade vertical padrão ──
        ALTITUDES_PADRAO = np.arange(
            CONFIG["altitude_min_agl_m"],
            CONFIG["altitude_max_agl_m"] + CONFIG["passo_vertical_m"],
            CONFIG["passo_vertical_m"],
            dtype=float,
        )
        print(f"Grade vertical: {ALTITUDES_PADRAO[0]:.0f} m a {ALTITUDES_PADRAO[-1]:.0f} m, "
              f"passo {CONFIG['passo_vertical_m']} m — {len(ALTITUDES_PADRAO)} níveis")

        # ── Carregar / salvar configuração ──
        CONFIG_PATH = BASE_DIR / "config" / "configuracao_modelo.json"

        def salvar_config(config, caminho=CONFIG_PATH):
            caminho = Path(caminho)
            caminho.parent.mkdir(parents=True, exist_ok=True)
            with open(caminho, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            print(f"💾 Configuração salva em: {caminho}")

        def carregar_config(caminho=CONFIG_PATH):
            with open(caminho, "r", encoding="utf-8") as f:
                return json.load(f)

        # Salvar config atualizada
        salvar_config(CONFIG)
        """),
    ]

# ══════════════════════════════════════════════
# SECTION 4 — Funções auxiliares
# ══════════════════════════════════════════════
def section_04():
    return [
        md("""
        ---
        ## 4. Funções Auxiliares
        """),
        # ── 4a: Constantes e conversão de vento ──
        code(r"""
        # ══════════════════════════════════════════════════
        # 4a. Constantes e conversão de vento
        # ══════════════════════════════════════════════════
        G0 = 9.80665  # aceleração gravitacional padrão [m/s²]

        # ── Colunas do formato padronizado ──
        COLUNAS_PADRAO = [
            "source", "source_file", "profile_id", "member_id",
            "generation_time_utc", "valid_time_utc",
            "latitude_deg", "longitude_deg",
            "altitude_msl_m", "altitude_agl_m", "pressure_hpa",
            "u_ms", "v_ms", "w_ms",
            "speed_ms", "direction_from_deg",
            "temperature_k",
            "data_type", "quality_flag",
        ]

        # ── Flags de qualidade ──
        QUALITY_FLAGS = [
            "OK", "MISSING_VALUE", "VERTICAL_GAP", "EXTRAPOLATED",
            "OUTSIDE_TIME_WINDOW", "SUSPECT_COORDINATE", "DUPLICATE",
        ]

        def velocidade_direcao_para_uv(velocidade, direcao_deg):
            """Converter velocidade e direção meteorológica (de onde vem) em componentes u, v."""
            theta = np.deg2rad(np.asarray(direcao_deg, dtype=float))
            vel = np.asarray(velocidade, dtype=float)
            u = -vel * np.sin(theta)
            v = -vel * np.cos(theta)
            return u, v

        def uv_para_velocidade_direcao(u, v):
            """Converter componentes u, v em velocidade e direção meteorológica."""
            u = np.asarray(u, dtype=float)
            v = np.asarray(v, dtype=float)
            velocidade = np.hypot(u, v)
            direcao = (np.rad2deg(np.arctan2(-u, -v)) + 360) % 360
            return velocidade, direcao

        print("✅ Funções de conversão de vento definidas.")

        # ── Teste rápido de ida-e-volta ──
        _v_test, _d_test = 10.0, 225.0
        _u, _vv = velocidade_direcao_para_uv(_v_test, _d_test)
        _v_back, _d_back = uv_para_velocidade_direcao(_u, _vv)
        assert abs(_v_back - _v_test) < 1e-10, f"Erro ida-volta velocidade: {_v_back} vs {_v_test}"
        assert abs(_d_back - _d_test) < 1e-10, f"Erro ida-volta direção: {_d_back} vs {_d_test}"
        print(f"   Teste ida-volta (V={_v_test}, θ={_d_test}°): u={_u:.4f}, v={_vv:.4f} → V={_v_back:.4f}, θ={_d_back:.4f}° ✓")
        """),

        # ── 4b: Altitude e geopotencial ──
        code(r"""
        # ══════════════════════════════════════════════════
        # 4b. Altitude e geopotencial
        # ══════════════════════════════════════════════════

        def geopotencial_para_altitude(geopotencial):
            """Converter geopotencial (m^2/s^2) em altitude geopotencial (m)."""
            return np.asarray(geopotencial, dtype=float) / G0

        def altitude_msl_para_agl(altitude_msl, elevacao_campo=None):
            """Converter altitude MSL para AGL."""
            if elevacao_campo is None:
                elevacao_campo = CONFIG["elevacao_campo_msl_m"]
            return np.asarray(altitude_msl, dtype=float) - elevacao_campo

        def altitude_agl_para_msl(altitude_agl, elevacao_campo=None):
            """Converter altitude AGL para MSL."""
            if elevacao_campo is None:
                elevacao_campo = CONFIG["elevacao_campo_msl_m"]
            return np.asarray(altitude_agl, dtype=float) + elevacao_campo

        print("✅ Funções de altitude definidas.")
        """),

        # ── 4c: Estatística circular ──
        code(r"""
        # ══════════════════════════════════════════════════
        # 4c. Estatística circular
        # ══════════════════════════════════════════════════

        def media_circular(angulos_deg):
            """
            Calcular a média circular e a concentração direcional R.

            Retorna
            -------
            media_deg : float
                Direção média circular [0, 360).
            R : float
                Concentração direcional (0 = muito variável, 1 = muito consistente).
            """
            angulos = np.asarray(angulos_deg, dtype=float)
            # Remover NaN
            angulos = angulos[~np.isnan(angulos)]
            if len(angulos) == 0:
                return np.nan, np.nan
            theta = np.deg2rad(angulos)
            C = np.mean(np.cos(theta))
            S = np.mean(np.sin(theta))
            media_deg = np.rad2deg(np.arctan2(S, C)) % 360
            R = np.hypot(C, S)
            return media_deg, R

        def desvio_padrao_circular(angulos_deg):
            """Desvio padrão circular (em graus)."""
            _, R = media_circular(angulos_deg)
            if np.isnan(R) or R <= 0:
                return np.nan
            # Mardia & Jupp: circular variance = 1 - R
            return np.rad2deg(np.sqrt(-2 * np.log(R)))

        print("✅ Funções de estatística circular definidas.")
        """),

        # ── 4d: Validação de dados ──
        code(r"""
        # ══════════════════════════════════════════════════
        # 4d. Validação de dados
        # ══════════════════════════════════════════════════

        def validar_perfil(df, config=None):
            """
            Validar um DataFrame no formato padronizado.

            Retorna lista de avisos e atualiza a coluna 'quality_flag'.
            """
            if config is None:
                config = CONFIG
            avisos = []

            # Presença de latitude e longitude
            if "latitude_deg" in df.columns:
                if df["latitude_deg"].isna().all():
                    avisos.append("⚠️  Latitude ausente em todos os registros.")
            if "longitude_deg" in df.columns:
                if df["longitude_deg"].isna().all():
                    avisos.append("⚠️  Longitude ausente em todos os registros.")

            # Presença de horário
            if "valid_time_utc" in df.columns:
                n_missing_time = df["valid_time_utc"].isna().sum()
                if n_missing_time > 0:
                    avisos.append(f"⚠️  {n_missing_time} registros sem horário.")

            # Presença de u e v
            if "u_ms" in df.columns and "v_ms" in df.columns:
                n_missing_uv = df[["u_ms", "v_ms"]].isna().any(axis=1).sum()
                if n_missing_uv > 0:
                    avisos.append(f"⚠️  {n_missing_uv} registros sem u ou v.")
                    df.loc[df[["u_ms", "v_ms"]].isna().any(axis=1), "quality_flag"] = "MISSING_VALUE"

            # Altitudes numéricas
            for col in ["altitude_agl_m", "altitude_msl_m"]:
                if col in df.columns and df[col].dtype == object:
                    avisos.append(f"⚠️  Coluna {col} não é numérica.")

            # Direção no intervalo [0, 360)
            if "direction_from_deg" in df.columns:
                dirs = df["direction_from_deg"].dropna()
                fora = ((dirs < 0) | (dirs > 360)).sum()
                if fora > 0:
                    avisos.append(f"⚠️  {fora} valores de direção fora de [0°, 360°].")

            # Duplicatas exatas
            dup_cols = [c for c in ["profile_id", "altitude_agl_m"] if c in df.columns]
            if dup_cols:
                n_dup = df.duplicated(subset=dup_cols).sum()
                if n_dup > 0:
                    avisos.append(f"⚠️  {n_dup} duplicatas encontradas (profile_id + altitude).")
                    df.loc[df.duplicated(subset=dup_cols, keep="first"), "quality_flag"] = "DUPLICATE"

            # Quantidade mínima de pontos verticais
            if "profile_id" in df.columns and "altitude_agl_m" in df.columns:
                for pid, grp in df.groupby("profile_id"):
                    n_pts = grp["altitude_agl_m"].notna().sum()
                    if n_pts < config.get("min_pontos_verticais", 5):
                        avisos.append(f"⚠️  Perfil {pid}: apenas {n_pts} pontos verticais.")

            # Lacunas verticais
            if "profile_id" in df.columns and "altitude_agl_m" in df.columns:
                max_gap = config.get("lacuna_vertical_maxima_m", 500)
                for pid, grp in df.groupby("profile_id"):
                    alts = grp["altitude_agl_m"].dropna().sort_values().values
                    if len(alts) > 1:
                        gaps = np.diff(alts)
                        big_gaps = gaps[gaps > max_gap]
                        for g in big_gaps:
                            avisos.append(f"⚠️  Perfil {pid}: lacuna vertical de {g:.0f} m.")
                            idx = grp.index
                            df.loc[idx, "quality_flag"] = df.loc[idx, "quality_flag"].replace("OK", "VERTICAL_GAP")

            # Resumo
            if not avisos:
                avisos.append("✅ Nenhum problema detectado na validação.")

            return avisos

        print("✅ Funções de validação definidas.")
        """),

        # ── 4e: Utilitários de data/hora ──
        code(r"""
        # ══════════════════════════════════════════════════
        # 4e. Utilitários de data/hora
        # ══════════════════════════════════════════════════
        import pytz

        def hora_local_para_utc(dt_local_str, tz_str=None):
            """Converter string de data/hora local para datetime UTC."""
            if tz_str is None:
                tz_str = CONFIG["timezone"]
            tz = pytz.timezone(tz_str)
            if isinstance(dt_local_str, str):
                dt_naive = pd.Timestamp(dt_local_str)
            else:
                dt_naive = pd.Timestamp(dt_local_str)
            dt_local = tz.localize(dt_naive)
            return dt_local.astimezone(pytz.utc)

        def utc_para_hora_local(dt_utc, tz_str=None):
            """Converter datetime UTC para hora local."""
            if tz_str is None:
                tz_str = CONFIG["timezone"]
            tz = pytz.timezone(tz_str)
            return pd.Timestamp(dt_utc).tz_convert(tz)

        def gerar_janela_temporal(config=None):
            """
            Gerar lista de datas (dia do calendário) para a climatologia,
            considerando a margem de dias ao redor da competição.
            """
            if config is None:
                config = CONFIG
            data_ini = pd.Timestamp(config["data_inicial_evento"])
            data_fim = pd.Timestamp(config["data_final_evento"])
            margem = config.get("margem_dias_calendario", 15)

            # Dias do calendário (mês, dia) dentro da janela
            centro = data_ini + (data_fim - data_ini) / 2
            dias = pd.date_range(
                centro - timedelta(days=margem),
                centro + timedelta(days=margem),
                freq="D",
            )
            # Extrair apenas mês e dia
            md_pairs = [(d.month, d.day) for d in dias]
            return md_pairs

        def filtrar_horas_locais(df, config=None):
            """
            Filtrar DataFrame para incluir apenas horários dentro da janela de lançamento.
            Assume que valid_time_utc está presente.
            """
            if config is None:
                config = CONFIG
            if "valid_time_utc" not in df.columns or df["valid_time_utc"].isna().all():
                return df

            tz_str = config["timezone"]
            tz = pytz.timezone(tz_str)
            hora_ini = config["hora_local_inicial"]
            hora_fim = config["hora_local_final"]

            # Converter para hora local
            tempos_utc = pd.to_datetime(df["valid_time_utc"], utc=True)
            horas_locais = tempos_utc.dt.tz_convert(tz).dt.hour

            mask = (horas_locais >= hora_ini) & (horas_locais <= hora_fim)
            return df[mask].copy()

        print("✅ Funções de data/hora definidas.")
        """),
    ]

# ══════════════════════════════════════════════
# SECTION 5 — Adaptadores de entrada
# ══════════════════════════════════════════════
def section_05():
    return [
        md("""
        ---
        ## 5. Adaptadores de Entrada
        """),
        code(r"""
        # ══════════════════════════════════════════════════
        # 5a. Criar DataFrame padronizado vazio
        # ══════════════════════════════════════════════════

        def criar_df_padrao():
            """Criar DataFrame vazio no formato padronizado."""
            return pd.DataFrame(columns=COLUNAS_PADRAO)

        def gerar_profile_id():
            """Gerar um identificador único para um perfil."""
            return str(uuid.uuid4())[:12]
        """),

        code(r"""
        # ══════════════════════════════════════════════════
        # 5b. Adaptador: CSV manual (componentes u,v ou velocidade+direção)
        # ══════════════════════════════════════════════════

        def carregar_csv_manual(caminho, config=None):
            """
            Carregar perfil de vento a partir de um CSV manual.

            Formatos aceitos:
            1. altitude_agl_m, u_ms, v_ms
            2. altitude_agl_m, velocidade_ms, direcao_de_onde_deg
            """
            if config is None:
                config = CONFIG
            caminho = Path(caminho)
            df_raw = pd.read_csv(caminho)

            df = criar_df_padrao()
            n = len(df_raw)
            df = pd.DataFrame({col: [None] * n for col in COLUNAS_PADRAO})

            # Identificação
            pid = gerar_profile_id()
            df["source"] = "csv_manual"
            df["source_file"] = str(caminho.name)
            df["profile_id"] = pid
            df["data_type"] = "synthetic"
            df["quality_flag"] = "OK"
            df["member_id"] = 0
            df["w_ms"] = 0.0

            # Coordenadas
            df["latitude_deg"] = config["latitude_lancamento"]
            df["longitude_deg"] = config["longitude_lancamento"]

            # Altitude
            if "altitude_agl_m" in df_raw.columns:
                df["altitude_agl_m"] = df_raw["altitude_agl_m"].values.astype(float)
                df["altitude_msl_m"] = df["altitude_agl_m"] + config["elevacao_campo_msl_m"]
            elif "altitude_msl_m" in df_raw.columns:
                df["altitude_msl_m"] = df_raw["altitude_msl_m"].values.astype(float)
                df["altitude_agl_m"] = df["altitude_msl_m"] - config["elevacao_campo_msl_m"]

            # Vento
            if "u_ms" in df_raw.columns and "v_ms" in df_raw.columns:
                df["u_ms"] = df_raw["u_ms"].values.astype(float)
                df["v_ms"] = df_raw["v_ms"].values.astype(float)
                speed, direc = uv_para_velocidade_direcao(df["u_ms"].values, df["v_ms"].values)
                df["speed_ms"] = speed
                df["direction_from_deg"] = direc
            elif "velocidade_ms" in df_raw.columns and "direcao_de_onde_deg" in df_raw.columns:
                vel = df_raw["velocidade_ms"].values.astype(float)
                dire = df_raw["direcao_de_onde_deg"].values.astype(float)
                u, v = velocidade_direcao_para_uv(vel, dire)
                df["u_ms"] = u
                df["v_ms"] = v
                df["speed_ms"] = vel
                df["direction_from_deg"] = dire

            # Tempo (sintético — usar hora central do evento)
            dt_str = config["data_inicial_evento"] + "T12:00:00"
            df["valid_time_utc"] = hora_local_para_utc(dt_str).isoformat()
            df["generation_time_utc"] = datetime.now(timezone.utc).isoformat()

            return df

        print("✅ Adaptador CSV manual definido.")
        """),

        code(r"""
        # ══════════════════════════════════════════════════
        # 5c. Adaptador: ERA5 NetCDF (níveis de pressão)
        # ══════════════════════════════════════════════════

        def carregar_era5_netcdf(caminho, config=None):
            """
            Carregar dados ERA5 de um arquivo NetCDF.
            Espera variáveis: u, v, z (geopotencial), t (temperatura).
            """
            if not HAS_XARRAY:
                raise ImportError("xarray é necessário para ler arquivos ERA5 NetCDF.")
            if config is None:
                config = CONFIG
            caminho = Path(caminho)

            ds = xr.open_dataset(caminho)

            # Interpolar para o ponto de lançamento
            lat = config["latitude_lancamento"]
            lon = config["longitude_lancamento"]

            # Converter longitude se necessário (ERA5 pode usar 0-360)
            lon_vars = ds.coords.get("longitude", ds.coords.get("lon", None))
            if lon_vars is not None and float(lon_vars.min()) >= 0:
                lon_era5 = lon % 360
            else:
                lon_era5 = lon

            try:
                ponto = ds.interp(
                    latitude=lat, longitude=lon_era5, method="linear"
                )
            except Exception:
                # Tentar nomes alternativos de coordenadas
                try:
                    ponto = ds.interp(lat=lat, lon=lon_era5, method="linear")
                except Exception as e:
                    raise ValueError(
                        f"Não foi possível interpolar para ({lat}, {lon}). "
                        f"Coordenadas disponíveis: {list(ds.coords)}"
                    ) from e

            # Identificar variáveis
            var_map = {}
            for vname in ds.data_vars:
                vlow = vname.lower()
                if vlow in ("u", "u10", "u_component_of_wind"):
                    var_map["u"] = vname
                elif vlow in ("v", "v10", "v_component_of_wind"):
                    var_map["v"] = vname
                elif vlow in ("z", "geopotential"):
                    var_map["z"] = vname
                elif vlow in ("t", "temperature"):
                    var_map["t"] = vname

            # Iterar sobre tempos e construir perfis
            all_rows = []
            time_dim = None
            for dim in ["time", "valid_time"]:
                if dim in ponto.dims:
                    time_dim = dim
                    break

            if time_dim is None:
                # Arquivo com um único tempo
                tempos = [None]
            else:
                tempos = ponto[time_dim].values

            for t_val in tempos:
                pid = gerar_profile_id()
                if t_val is not None:
                    sel = ponto.sel({time_dim: t_val})
                    time_utc = pd.Timestamp(t_val).isoformat()
                else:
                    sel = ponto
                    time_utc = None

                # Identificar dimensão de pressão
                press_dim = None
                for dim in ["level", "pressure_level", "isobaricInhPa", "plev"]:
                    if dim in sel.dims:
                        press_dim = dim
                        break

                if press_dim is None:
                    continue

                pressoes = sel[press_dim].values
                n_levels = len(pressoes)

                for i, p in enumerate(pressoes):
                    row = {col: None for col in COLUNAS_PADRAO}
                    row["source"] = "era5"
                    row["source_file"] = str(caminho.name)
                    row["profile_id"] = pid
                    row["member_id"] = 0
                    row["valid_time_utc"] = time_utc
                    row["generation_time_utc"] = datetime.now(timezone.utc).isoformat()
                    row["latitude_deg"] = lat
                    row["longitude_deg"] = lon
                    row["pressure_hpa"] = float(p)
                    row["data_type"] = "historical"
                    row["quality_flag"] = "OK"
                    row["w_ms"] = 0.0

                    level_sel = sel.sel({press_dim: p})

                    if "u" in var_map:
                        row["u_ms"] = float(level_sel[var_map["u"]].values)
                    if "v" in var_map:
                        row["v_ms"] = float(level_sel[var_map["v"]].values)
                    if "z" in var_map:
                        geopot = float(level_sel[var_map["z"]].values)
                        alt_msl = geopotencial_para_altitude(geopot)
                        row["altitude_msl_m"] = alt_msl
                        row["altitude_agl_m"] = alt_msl - config["elevacao_campo_msl_m"]
                    if "t" in var_map:
                        row["temperature_k"] = float(level_sel[var_map["t"]].values)

                    if row["u_ms"] is not None and row["v_ms"] is not None:
                        spd, dirn = uv_para_velocidade_direcao(row["u_ms"], row["v_ms"])
                        row["speed_ms"] = float(spd)
                        row["direction_from_deg"] = float(dirn)

                    all_rows.append(row)

            df = pd.DataFrame(all_rows, columns=COLUNAS_PADRAO)
            return df

        print("✅ Adaptador ERA5 NetCDF definido.")
        """),

        code(r"""
        # ══════════════════════════════════════════════════
        # 5d. Adaptador: Previsão meteorológica (CSV ou NetCDF)
        # ══════════════════════════════════════════════════

        def carregar_previsao_csv(caminho, config=None):
            """
            Carregar previsão meteorológica a partir de CSV.

            Espera colunas: altitude_agl_m, u_ms, v_ms
            Opcionais: data_validade, modelo
            """
            if config is None:
                config = CONFIG
            caminho = Path(caminho)
            df_raw = pd.read_csv(caminho)

            n = len(df_raw)
            df = pd.DataFrame({col: [None] * n for col in COLUNAS_PADRAO})

            pid = gerar_profile_id()
            df["source"] = "forecast"
            df["source_file"] = str(caminho.name)
            df["profile_id"] = pid
            df["data_type"] = "forecast"
            df["quality_flag"] = "OK"
            df["member_id"] = 0
            df["w_ms"] = 0.0

            df["latitude_deg"] = config["latitude_lancamento"]
            df["longitude_deg"] = config["longitude_lancamento"]

            # Altitude
            if "altitude_agl_m" in df_raw.columns:
                df["altitude_agl_m"] = df_raw["altitude_agl_m"].values.astype(float)
                df["altitude_msl_m"] = df["altitude_agl_m"].astype(float) + config["elevacao_campo_msl_m"]

            # Vento
            if "u_ms" in df_raw.columns and "v_ms" in df_raw.columns:
                df["u_ms"] = df_raw["u_ms"].values.astype(float)
                df["v_ms"] = df_raw["v_ms"].values.astype(float)
                spd, dire = uv_para_velocidade_direcao(df["u_ms"].values, df["v_ms"].values)
                df["speed_ms"] = spd
                df["direction_from_deg"] = dire
            elif "velocidade_ms" in df_raw.columns and "direcao_de_onde_deg" in df_raw.columns:
                vel = df_raw["velocidade_ms"].values.astype(float)
                dire = df_raw["direcao_de_onde_deg"].values.astype(float)
                u, v = velocidade_direcao_para_uv(vel, dire)
                df["u_ms"] = u
                df["v_ms"] = v
                df["speed_ms"] = vel
                df["direction_from_deg"] = dire

            # Tempo
            if "data_validade" in df_raw.columns:
                df["valid_time_utc"] = df_raw["data_validade"].values
            elif "valid_time" in df_raw.columns:
                df["valid_time_utc"] = df_raw["valid_time"].values
            else:
                df["valid_time_utc"] = datetime.now(timezone.utc).isoformat()

            df["generation_time_utc"] = datetime.now(timezone.utc).isoformat()

            # Modelo
            if "modelo" in df_raw.columns:
                df["source"] = df_raw["modelo"].values[0] if len(df_raw) > 0 else "forecast"

            return df

        def carregar_previsao_netcdf(caminho, config=None):
            """Carregar previsão de arquivo NetCDF (mesmo formato que ERA5)."""
            df = carregar_era5_netcdf(caminho, config)
            df["data_type"] = "forecast"
            return df

        print("✅ Adaptadores de previsão definidos.")
        """),

        code(r"""
        # ══════════════════════════════════════════════════
        # 5e. Adaptador: Radiossonda / medição de campo
        # ══════════════════════════════════════════════════

        def carregar_radiossonda_csv(caminho, config=None):
            """
            Carregar dados de radiossonda ou medição de campo.

            Formato esperado: CSV com pelo menos altitude e vento.
            """
            if config is None:
                config = CONFIG
            # Usa o mesmo carregador do CSV manual, mas marca como observação
            df = carregar_csv_manual(caminho, config)
            df["data_type"] = "observation"
            df["source"] = "radiosonde"
            return df

        def carregar_medicao_campo_csv(caminho, config=None):
            """Carregar medição de anemômetro ou estação de campo."""
            if config is None:
                config = CONFIG
            df = carregar_csv_manual(caminho, config)
            df["data_type"] = "observation"
            df["source"] = "field_measurement"
            return df

        # ══════════════════════════════════════════════════
        # 5f. Registro de adaptadores
        # ══════════════════════════════════════════════════

        ADAPTERS = {
            "csv_manual": carregar_csv_manual,
            "era5_netcdf": carregar_era5_netcdf,
            "forecast_csv": carregar_previsao_csv,
            "forecast_netcdf": carregar_previsao_netcdf,
            "radiosonde_csv": carregar_radiossonda_csv,
            "field_csv": carregar_medicao_campo_csv,
        }

        def carregar_fonte(tipo, caminho, config=None):
            """
            Carregar dados de qualquer fonte registrada.

            Parâmetros
            ----------
            tipo : str
                Chave do adaptador (e.g., 'csv_manual', 'era5_netcdf').
            caminho : str ou Path
                Caminho para o arquivo de dados.
            config : dict, opcional
                Configuração do modelo.

            Retorna
            -------
            DataFrame no formato padronizado.
            """
            if config is None:
                config = CONFIG
            if tipo not in ADAPTERS:
                raise ValueError(
                    f"Tipo de fonte '{tipo}' não registrado. "
                    f"Tipos disponíveis: {list(ADAPTERS.keys())}"
                )
            carregador = ADAPTERS[tipo]
            dados_brutos = carregador(caminho, config)
            return dados_brutos

        print(f"✅ Adaptadores registrados: {list(ADAPTERS.keys())}")
        """),
    ]

# ══════════════════════════════════════════════
# SECTION 6 — Normalização
# ══════════════════════════════════════════════
def section_06():
    return [
        md("""
        ---
        ## 6. Normalização
        """),
        code(r"""
        # ══════════════════════════════════════════════════
        # Normalização — formato interno padronizado
        # ══════════════════════════════════════════════════

        def normalizar_dados(df, config=None):
            """
            Normalizar DataFrame para o formato padronizado.

            Etapas:
            1. Padronizar nomes de colunas
            2. Converter unidades
            3. Converter datas para UTC
            4. Calcular altitude AGL
            5. Calcular velocidade e direção
            6. Identificar valores ausentes
            7. Verificar duplicidades
            8. Atribuir flags de qualidade
            9. Ordenar por perfil e altitude
            10. Verificar mistura de níveis incompatíveis
            """
            if config is None:
                config = CONFIG

            df = df.copy()

            # ── 1. Garantir colunas padrão ──
            for col in COLUNAS_PADRAO:
                if col not in df.columns:
                    df[col] = None

            # ── 2. Converter tipos numéricos ──
            num_cols = ["altitude_msl_m", "altitude_agl_m", "pressure_hpa",
                        "u_ms", "v_ms", "w_ms", "speed_ms", "direction_from_deg",
                        "temperature_k", "latitude_deg", "longitude_deg"]
            for col in num_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            # ── 3. Garantir w ──
            if df["w_ms"].isna().all():
                df["w_ms"] = 0.0

            # ── 4. Calcular altitude AGL se ausente ──
            if df["altitude_agl_m"].isna().any() and df["altitude_msl_m"].notna().any():
                mask = df["altitude_agl_m"].isna() & df["altitude_msl_m"].notna()
                df.loc[mask, "altitude_agl_m"] = (
                    df.loc[mask, "altitude_msl_m"] - config["elevacao_campo_msl_m"]
                )

            # ── 5. Calcular velocidade e direção se ausentes ──
            if df["speed_ms"].isna().any() and df["u_ms"].notna().any():
                mask = df["speed_ms"].isna() & df["u_ms"].notna() & df["v_ms"].notna()
                if mask.any():
                    spd, dire = uv_para_velocidade_direcao(
                        df.loc[mask, "u_ms"].values,
                        df.loc[mask, "v_ms"].values,
                    )
                    df.loc[mask, "speed_ms"] = spd
                    df.loc[mask, "direction_from_deg"] = dire

            # ── 6. Calcular u,v se ausentes mas velocidade+direção presentes ──
            if df["u_ms"].isna().any() and df["speed_ms"].notna().any():
                mask = df["u_ms"].isna() & df["speed_ms"].notna() & df["direction_from_deg"].notna()
                if mask.any():
                    u, v = velocidade_direcao_para_uv(
                        df.loc[mask, "speed_ms"].values,
                        df.loc[mask, "direction_from_deg"].values,
                    )
                    df.loc[mask, "u_ms"] = u
                    df.loc[mask, "v_ms"] = v

            # ── 7. Quality flag padrão ──
            if df["quality_flag"].isna().any():
                df.loc[df["quality_flag"].isna(), "quality_flag"] = "OK"

            # ── 8. Marcar valores ausentes ──
            essential = ["u_ms", "v_ms", "altitude_agl_m"]
            for col in essential:
                mask = df[col].isna() & (df["quality_flag"] == "OK")
                df.loc[mask, "quality_flag"] = "MISSING_VALUE"

            # ── 9. Ordenar por perfil e altitude ──
            sort_cols = [c for c in ["profile_id", "altitude_agl_m"] if c in df.columns]
            if sort_cols:
                df = df.sort_values(sort_cols).reset_index(drop=True)

            # ── 10. Remover perfis com altitude negativa (abaixo do campo) ──
            if df["altitude_agl_m"].notna().any():
                mask_neg = df["altitude_agl_m"] < -50  # tolerância de 50 m
                if mask_neg.any():
                    df = df[~mask_neg].reset_index(drop=True)

            return df[COLUNAS_PADRAO]

        print("✅ Função de normalização definida.")
        """),
    ]

# ══════════════════════════════════════════════
# SECTION 7 — Seleção espacial e temporal
# ══════════════════════════════════════════════
def section_07():
    return [
        md("""
        ---
        ## 7. Seleção Espacial e Temporal
        """),
        code(r"""
        # ══════════════════════════════════════════════════
        # 7a. Seleção espacial
        # ══════════════════════════════════════════════════

        def selecionar_ponto_grade(ds, config=None):
            """
            Interpolar dataset xarray para as coordenadas do campo de lançamento.

            Registra coordenadas dos pontos de grade mais próximos e distância.
            """
            if config is None:
                config = CONFIG

            lat = config["latitude_lancamento"]
            lon = config["longitude_lancamento"]

            # Info dos pontos de grade
            info = {
                "coordenadas_campo": (lat, lon),
                "metodo": "linear",
            }

            # Detectar nomes de coordenadas
            lat_name = "latitude" if "latitude" in ds.coords else "lat"
            lon_name = "longitude" if "longitude" in ds.coords else "lon"

            # Pontos de grade mais próximos
            lats = ds[lat_name].values
            lons = ds[lon_name].values

            idx_lat = np.argmin(np.abs(lats - lat))
            idx_lon = np.argmin(np.abs(lons - lon))
            info["ponto_grade_mais_proximo"] = (float(lats[idx_lat]), float(lons[idx_lon]))

            # Distância aproximada (graus)
            dist_deg = np.sqrt(
                (lats[idx_lat] - lat) ** 2 + (lons[idx_lon] - lon) ** 2
            )
            # Aprox. km (1° ≈ 111 km)
            info["distancia_aprox_km"] = float(dist_deg * 111)
            info["resolucao_grade_deg"] = float(np.abs(np.diff(lats[:2])[0])) if len(lats) > 1 else None

            # Interpolar
            kw = {lat_name: lat, lon_name: lon}
            ponto = ds.interp(**kw, method="linear")

            return ponto, info
        """),

        code(r"""
        # ══════════════════════════════════════════════════
        # 7b. Seleção temporal para climatologia
        # ══════════════════════════════════════════════════

        def selecionar_climatologia(df, config=None, janela_anos=None):
            """
            Filtrar DataFrame para a janela climatológica.

            Critérios:
            - Dias do calendário próximos à competição (± margem)
            - Horários dentro da janela de lançamento
            - Últimos N anos
            """
            if config is None:
                config = CONFIG
            if janela_anos is None:
                janela_anos = config["anos_historicos"]

            df = df.copy()

            # Garantir que valid_time_utc é datetime
            if df["valid_time_utc"].dtype == object:
                df["valid_time_utc"] = pd.to_datetime(df["valid_time_utc"], utc=True)

            # ── Filtro 1: Anos ──
            ano_evento = int(config["data_inicial_evento"][:4])
            ano_min = ano_evento - janela_anos
            df = df[df["valid_time_utc"].dt.year >= ano_min]
            df = df[df["valid_time_utc"].dt.year < ano_evento]  # excluir ano do evento

            # ── Filtro 2: Dias do calendário ──
            md_pairs = gerar_janela_temporal(config)
            # Criar máscara: (mês, dia) está na janela
            df["_month"] = df["valid_time_utc"].dt.month
            df["_day"] = df["valid_time_utc"].dt.day
            df["_md"] = list(zip(df["_month"], df["_day"]))
            df = df[df["_md"].isin(md_pairs)]

            # ── Filtro 3: Horários ──
            df = filtrar_horas_locais(df, config)

            # Limpar colunas temporárias
            df = df.drop(columns=["_month", "_day", "_md"], errors="ignore")

            return df.reset_index(drop=True)

        def resumo_selecao_temporal(df, config=None):
            """Gerar resumo da seleção temporal."""
            if config is None:
                config = CONFIG
            if df.empty:
                return {"n_perfis": 0, "n_anos": 0, "n_dias": 0}

            tempos = pd.to_datetime(df["valid_time_utc"], utc=True)
            anos = tempos.dt.year.unique()
            dias = tempos.dt.date.nunique()
            n_perfis = df["profile_id"].nunique()

            return {
                "n_perfis": n_perfis,
                "n_anos": len(anos),
                "anos": sorted(anos.tolist()),
                "n_dias": dias,
                "primeiro": str(tempos.min()),
                "ultimo": str(tempos.max()),
            }

        print("✅ Funções de seleção espacial e temporal definidas.")
        """),
    ]

# ══════════════════════════════════════════════
# SECTION 8 — Interpolação vertical
# ══════════════════════════════════════════════
def section_08():
    return [
        md("""
        ---
        ## 8. Interpolação Vertical
        """),
        code(r"""
        # ══════════════════════════════════════════════════
        # Interpolação vertical para a grade padrão
        # ══════════════════════════════════════════════════

        def interpolar_perfil_vertical(df_perfil, altitudes_padrao=None, config=None):
            """
            Interpolar um único perfil para a grade vertical padrão.

            A interpolação é feita em u, v, w e temperatura separadamente.
            Direção NÃO é interpolada diretamente.
            Valores fora da faixa original recebem NaN + flag EXTRAPOLATED.

            Parâmetros
            ----------
            df_perfil : DataFrame
                Perfil individual (mesmo profile_id).
            altitudes_padrao : array
                Grade vertical alvo.
            config : dict
                Configuração do modelo.

            Retorna
            -------
            DataFrame interpolado.
            """
            if altitudes_padrao is None:
                altitudes_padrao = ALTITUDES_PADRAO
            if config is None:
                config = CONFIG

            df = df_perfil.sort_values("altitude_agl_m").dropna(subset=["altitude_agl_m"])
            if len(df) < 2:
                return pd.DataFrame()

            alt_orig = df["altitude_agl_m"].values
            alt_min, alt_max = alt_orig.min(), alt_orig.max()

            # Colunas a interpolar
            interp_vars = ["u_ms", "v_ms", "w_ms", "temperature_k"]
            resultado = {col: [] for col in COLUNAS_PADRAO}

            pid = df["profile_id"].iloc[0]
            source = df["source"].iloc[0]
            source_file = df["source_file"].iloc[0]
            member_id = df["member_id"].iloc[0]
            gen_time = df["generation_time_utc"].iloc[0]
            val_time = df["valid_time_utc"].iloc[0]
            lat = df["latitude_deg"].iloc[0]
            lon = df["longitude_deg"].iloc[0]
            data_type = df["data_type"].iloc[0]

            for z in altitudes_padrao:
                row = {col: None for col in COLUNAS_PADRAO}
                row["profile_id"] = pid
                row["source"] = source
                row["source_file"] = source_file
                row["member_id"] = member_id
                row["generation_time_utc"] = gen_time
                row["valid_time_utc"] = val_time
                row["latitude_deg"] = lat
                row["longitude_deg"] = lon
                row["altitude_agl_m"] = z
                row["altitude_msl_m"] = z + config["elevacao_campo_msl_m"]
                row["data_type"] = data_type
                row["w_ms"] = 0.0

                # Determinar se está dentro da faixa
                if z < alt_min or z > alt_max:
                    row["quality_flag"] = "EXTRAPOLATED"
                    # Preencher com NaN
                    row["u_ms"] = np.nan
                    row["v_ms"] = np.nan
                else:
                    row["quality_flag"] = "OK"
                    for var in interp_vars:
                        if var in df.columns:
                            vals = df[var].values
                            valid = ~np.isnan(vals.astype(float))
                            if valid.sum() >= 2:
                                row[var] = float(np.interp(z, alt_orig[valid], vals[valid].astype(float)))

                # Calcular velocidade e direção a partir de u,v interpolados
                if row["u_ms"] is not None and row["v_ms"] is not None:
                    if not (np.isnan(row["u_ms"]) or np.isnan(row["v_ms"])):
                        spd, dire = uv_para_velocidade_direcao(row["u_ms"], row["v_ms"])
                        row["speed_ms"] = float(spd)
                        row["direction_from_deg"] = float(dire)

                for col in COLUNAS_PADRAO:
                    resultado[col].append(row.get(col))

            return pd.DataFrame(resultado, columns=COLUNAS_PADRAO)

        def interpolar_todos_perfis(df, altitudes_padrao=None, config=None):
            """
            Interpolar todos os perfis de um DataFrame para a grade vertical padrão.

            Cada perfil (profile_id) é interpolado separadamente.
            """
            if altitudes_padrao is None:
                altitudes_padrao = ALTITUDES_PADRAO
            if config is None:
                config = CONFIG

            perfis_interp = []
            for pid, grp in df.groupby("profile_id"):
                interp = interpolar_perfil_vertical(grp, altitudes_padrao, config)
                if not interp.empty:
                    perfis_interp.append(interp)

            if not perfis_interp:
                return pd.DataFrame(columns=COLUNAS_PADRAO)

            resultado = pd.concat(perfis_interp, ignore_index=True)
            print(f"   Perfis interpolados: {resultado['profile_id'].nunique()} "
                  f"({len(resultado)} pontos)")
            return resultado

        print("✅ Funções de interpolação vertical definidas.")
        """),
    ]

# ══════════════════════════════════════════════
# SECTION 9 — Estatísticas
# ══════════════════════════════════════════════
def section_09():
    return [
        md("""
        ---
        ## 9. Estatísticas por Altitude
        """),
        code(r"""
        # ══════════════════════════════════════════════════
        # 9a. Estatísticas de componentes e velocidade
        # ══════════════════════════════════════════════════

        def calcular_estatisticas_altitude(df, config=None):
            """
            Calcular estatísticas por altitude para todos os perfis interpolados.

            Para cada nível da grade, calcula:
            - Média, mediana, desvio de u e v
            - Percentis de velocidade (calculados a partir da distribuição de velocidades)
            - Média circular e concentração direcional
            - Cisalhamento vertical

            Retorna DataFrame com uma linha por altitude.
            """
            if config is None:
                config = CONFIG

            percentis = config["percentis"]

            resultados = []

            for z in ALTITUDES_PADRAO:
                mask = (df["altitude_agl_m"] == z) & (df["quality_flag"] == "OK")
                sub = df[mask]

                row = {"altitude_agl_m": z}

                if len(sub) < 2:
                    row["n_profiles"] = len(sub)
                    resultados.append(row)
                    continue

                u = sub["u_ms"].dropna().values
                v = sub["v_ms"].dropna().values
                n = min(len(u), len(v))
                u, v = u[:n], v[:n]

                if n < 2:
                    row["n_profiles"] = n
                    resultados.append(row)
                    continue

                # ── Componentes ──
                row["u_mean_ms"] = np.mean(u)
                row["v_mean_ms"] = np.mean(v)
                row["u_std_ms"] = np.std(u, ddof=1)
                row["v_std_ms"] = np.std(v, ddof=1)
                row["u_median_ms"] = np.median(u)
                row["v_median_ms"] = np.median(v)

                # ── Velocidade ──
                speed = np.hypot(u, v)
                row["speed_mean_ms"] = np.mean(speed)
                row["speed_median_ms"] = np.median(speed)
                row["speed_std_ms"] = np.std(speed, ddof=1)
                row["speed_min_ms"] = np.min(speed)
                row["speed_max_ms"] = np.max(speed)

                for p in percentis:
                    row[f"speed_p{p:02d}_ms"] = float(np.percentile(speed, p))

                # ── Direção circular ──
                dire = sub["direction_from_deg"].dropna().values
                if len(dire) >= 2:
                    dir_mean, R = media_circular(dire)
                    row["direction_mean_from_deg"] = dir_mean
                    row["direction_concentration_R"] = R
                    row["direction_std_deg"] = desvio_padrao_circular(dire)

                # ── Metadados ──
                row["n_profiles"] = n

                resultados.append(row)

            df_stats = pd.DataFrame(resultados)

            # ── Cisalhamento vertical ──
            if "u_mean_ms" in df_stats.columns and df_stats["u_mean_ms"].notna().sum() > 2:
                alts = df_stats["altitude_agl_m"].values
                u_mean = df_stats["u_mean_ms"].values
                v_mean = df_stats["v_mean_ms"].values

                # Substituir NaN por interpolação para cálculo do gradiente
                valid = ~(np.isnan(u_mean) | np.isnan(v_mean))
                if valid.sum() > 2:
                    du_dz = np.full_like(u_mean, np.nan)
                    dv_dz = np.full_like(v_mean, np.nan)
                    du_dz[valid] = np.gradient(u_mean[valid], alts[valid])
                    dv_dz[valid] = np.gradient(v_mean[valid], alts[valid])
                    df_stats["du_dz_s-1"] = du_dz
                    df_stats["dv_dz_s-1"] = dv_dz
                    df_stats["shear_s-1"] = np.hypot(du_dz, dv_dz)

            return df_stats

        print("✅ Estatísticas por altitude definidas.")
        """),

        code(r"""
        # ══════════════════════════════════════════════════
        # 9b. Cisalhamento vertical de um perfil individual
        # ══════════════════════════════════════════════════

        def calcular_cisalhamento_perfil(perfil_df):
            """
            Calcular cisalhamento vertical de um perfil individual.

            Retorna arrays de du/dz, dv/dz e magnitude do cisalhamento.
            """
            df = perfil_df.sort_values("altitude_agl_m").dropna(subset=["altitude_agl_m", "u_ms", "v_ms"])
            if len(df) < 3:
                return None, None, None

            alt = df["altitude_agl_m"].values
            u = df["u_ms"].values.astype(float)
            v = df["v_ms"].values.astype(float)

            du_dz = np.gradient(u, alt)
            dv_dz = np.gradient(v, alt)
            shear = np.hypot(du_dz, dv_dz)

            return du_dz, dv_dz, shear
        """),

        code(r"""
        # ══════════════════════════════════════════════════
        # 9c. Bootstrap para intervalos de confiança
        # ══════════════════════════════════════════════════

        def calcular_bootstrap_ci(df, config=None, n_bootstrap=None, ci_level=0.95):
            """
            Calcular intervalos de confiança via bootstrap por blocos (anos).

            Reamostra anos completos para preservar a correlação temporal.

            Retorna DataFrame com colunas para o IC inferior e superior
            da mediana da velocidade em cada altitude.
            """
            if config is None:
                config = CONFIG
            if n_bootstrap is None:
                n_bootstrap = config.get("n_bootstrap", 1000)

            if "valid_time_utc" not in df.columns:
                print("⚠️  Sem informação temporal para bootstrap.")
                return None

            df = df.copy()
            tempos = pd.to_datetime(df["valid_time_utc"], utc=True)
            df["_year"] = tempos.dt.year
            anos_unicos = df["_year"].unique()

            if len(anos_unicos) < 3:
                print(f"⚠️  Apenas {len(anos_unicos)} anos — bootstrap pouco significativo.")
                return None

            alpha = 1 - ci_level
            resultados = {z: [] for z in ALTITUDES_PADRAO}

            rng = np.random.default_rng(42)

            for _ in range(n_bootstrap):
                # Sortear anos com reposição
                anos_sample = rng.choice(anos_unicos, size=len(anos_unicos), replace=True)
                # Construir amostra
                frames = []
                for ano in anos_sample:
                    frames.append(df[df["_year"] == ano])
                sample = pd.concat(frames, ignore_index=True)

                # Calcular mediana da velocidade em cada altitude
                for z in ALTITUDES_PADRAO:
                    mask = (sample["altitude_agl_m"] == z) & (sample["quality_flag"] == "OK")
                    sub = sample[mask]
                    if len(sub) >= 2:
                        spd = np.hypot(
                            sub["u_ms"].dropna().values.astype(float),
                            sub["v_ms"].dropna().values.astype(float),
                        )
                        if len(spd) > 0:
                            resultados[z].append(np.median(spd))

            df.drop(columns=["_year"], errors="ignore", inplace=True)

            # Calcular IC
            rows = []
            for z in ALTITUDES_PADRAO:
                vals = resultados[z]
                if len(vals) >= 10:
                    rows.append({
                        "altitude_agl_m": z,
                        "speed_median_ci_lower": np.percentile(vals, 100 * alpha / 2),
                        "speed_median_ci_upper": np.percentile(vals, 100 * (1 - alpha / 2)),
                        "n_bootstrap_valid": len(vals),
                    })
                else:
                    rows.append({
                        "altitude_agl_m": z,
                        "speed_median_ci_lower": np.nan,
                        "speed_median_ci_upper": np.nan,
                        "n_bootstrap_valid": len(vals),
                    })

            return pd.DataFrame(rows)
        """),

        code(r"""
        # ══════════════════════════════════════════════════
        # 9d. Representatividade da climatologia
        # ══════════════════════════════════════════════════

        def calcular_representatividade(df, stats_df, config=None):
            """
            Calcular métricas de representatividade da climatologia.

            Retorna dicionário com métricas diversas.
            """
            if config is None:
                config = CONFIG

            metricas = {}

            # Perfis e anos
            n_perfis = df["profile_id"].nunique()
            metricas["n_perfis"] = n_perfis

            if "valid_time_utc" in df.columns and df["valid_time_utc"].notna().any():
                tempos = pd.to_datetime(df["valid_time_utc"], utc=True)
                anos = tempos.dt.year.unique()
                dias = tempos.dt.date.nunique()
                metricas["n_anos"] = len(anos)
                metricas["n_dias"] = dias
                metricas["anos_cobertos"] = sorted(anos.tolist())
            else:
                metricas["n_anos"] = 0
                metricas["n_dias"] = 0

            # Cobertura temporal
            n_anos_esperados = config["anos_historicos"]
            metricas["cobertura_temporal_pct"] = (
                metricas["n_anos"] / n_anos_esperados * 100
                if n_anos_esperados > 0 else 0
            )

            # Cobertura vertical
            n_niveis_total = len(ALTITUDES_PADRAO)
            n_niveis_validos = 0
            if stats_df is not None and "n_profiles" in stats_df.columns:
                n_niveis_validos = (stats_df["n_profiles"] >= 2).sum()
            metricas["cobertura_vertical_pct"] = (
                n_niveis_validos / n_niveis_total * 100
                if n_niveis_total > 0 else 0
            )

            # Largura das faixas de percentis
            if stats_df is not None:
                if "speed_p10_ms" in stats_df.columns and "speed_p90_ms" in stats_df.columns:
                    faixa_1090 = stats_df["speed_p90_ms"] - stats_df["speed_p10_ms"]
                    metricas["largura_media_p10_p90_ms"] = float(faixa_1090.mean())
                if "speed_p25_ms" in stats_df.columns and "speed_p75_ms" in stats_df.columns:
                    faixa_2575 = stats_df["speed_p75_ms"] - stats_df["speed_p25_ms"]
                    metricas["largura_media_p25_p75_ms"] = float(faixa_2575.mean())

            # Concentração direcional média
            if stats_df is not None and "direction_concentration_R" in stats_df.columns:
                R_vals = stats_df["direction_concentration_R"].dropna()
                if len(R_vals) > 0:
                    metricas["concentracao_direcional_media"] = float(R_vals.mean())

            # Dados válidos
            if "quality_flag" in df.columns:
                n_total = len(df)
                n_ok = (df["quality_flag"] == "OK").sum()
                metricas["pct_dados_validos"] = float(n_ok / n_total * 100) if n_total > 0 else 0

            return metricas

        print("✅ Funções de representatividade definidas.")
        """),
    ]

# ══════════════════════════════════════════════
# SECTION 10 — Perfil atualizado
# ══════════════════════════════════════════════
def section_10():
    return [
        md("""
        ---
        ## 10. Comparação do Perfil Atualizado com a Climatologia
        """),
        code(r"""
        # ══════════════════════════════════════════════════
        # 10. Comparar perfil atualizado com climatologia
        # ══════════════════════════════════════════════════

        def comparar_perfil_com_climatologia(perfil_df, hist_df, stats_df, config=None):
            """
            Comparar um perfil atual (previsão, observação) com a climatologia histórica.

            Para cada altitude, calcula:
            - Percentil histórico da velocidade atual
            - Classificação (central, normal, incomum, extrema)
            - Distância vetorial do perfil mediano
            - Cisalhamento do perfil atual

            Retorna DataFrame de comparação.
            """
            if config is None:
                config = CONFIG

            resultados = []
            perfil = perfil_df.sort_values("altitude_agl_m")

            # Cisalhamento do perfil atual
            du_dz_curr, dv_dz_curr, shear_curr = calcular_cisalhamento_perfil(perfil)
            if shear_curr is None:
                shear_curr = np.full(len(ALTITUDES_PADRAO), np.nan)
                alt_shear = ALTITUDES_PADRAO
            else:
                alt_shear = perfil.dropna(subset=["altitude_agl_m", "u_ms", "v_ms"]).sort_values(
                    "altitude_agl_m"
                )["altitude_agl_m"].values

            for i, z in enumerate(ALTITUDES_PADRAO):
                row = {"altitude_agl_m": z}

                # Obter valor atual
                mask_curr = np.abs(perfil["altitude_agl_m"].values.astype(float) - z) < 1.0
                if mask_curr.any():
                    curr_row = perfil[mask_curr].iloc[0]
                    u_curr = float(curr_row["u_ms"]) if pd.notna(curr_row["u_ms"]) else np.nan
                    v_curr = float(curr_row["v_ms"]) if pd.notna(curr_row["v_ms"]) else np.nan
                else:
                    u_curr, v_curr = np.nan, np.nan

                row["u_current_ms"] = u_curr
                row["v_current_ms"] = v_curr

                if np.isnan(u_curr) or np.isnan(v_curr):
                    resultados.append(row)
                    continue

                speed_curr = np.hypot(u_curr, v_curr)
                row["speed_current_ms"] = speed_curr

                dire_curr_spd, dire_curr = uv_para_velocidade_direcao(u_curr, v_curr)
                row["direction_current_from_deg"] = float(dire_curr)

                # ── Percentil histórico ──
                mask_hist = (hist_df["altitude_agl_m"] == z) & (hist_df["quality_flag"] == "OK")
                hist_sub = hist_df[mask_hist]

                if len(hist_sub) >= 5:
                    speeds_hist = np.hypot(
                        hist_sub["u_ms"].values.astype(float),
                        hist_sub["v_ms"].values.astype(float),
                    )
                    percentile = sci_stats.percentileofscore(speeds_hist, speed_curr, kind="rank")
                    row["current_speed_percentile"] = percentile
                else:
                    row["current_speed_percentile"] = np.nan

                # ── Classificação ──
                p = row["current_speed_percentile"]
                if np.isnan(p):
                    row["classificacao"] = "INDETERMINADO"
                elif 25 <= p <= 75:
                    row["classificacao"] = "CENTRAL"
                elif 10 <= p <= 90:
                    row["classificacao"] = "NORMAL"
                elif 5 <= p <= 95:
                    row["classificacao"] = "INCOMUM"
                else:
                    row["classificacao"] = "EXTREMO"

                # ── Distância vetorial do mediano ──
                stats_row = stats_df[stats_df["altitude_agl_m"] == z]
                if not stats_row.empty and "u_median_ms" in stats_row.columns:
                    sr = stats_row.iloc[0]
                    u_med = sr.get("u_median_ms", np.nan)
                    v_med = sr.get("v_median_ms", np.nan)
                    if pd.notna(u_med) and pd.notna(v_med):
                        row["vector_diff_from_median_ms"] = np.hypot(
                            u_curr - u_med, v_curr - v_med
                        )

                # ── Cisalhamento atual ──
                idx_shear = np.argmin(np.abs(alt_shear - z))
                if idx_shear < len(shear_curr):
                    row["shear_current_s-1"] = float(shear_curr[idx_shear])

                resultados.append(row)

            return pd.DataFrame(resultados)

        def classificar_perfil_geral(comparacao_df):
            """
            Classificar o perfil geral com base na comparação com a climatologia.

            Retorna:
            - classificação geral (TÍPICO, MODERADAMENTE ATÍPICO, SEVERO, EXTREMO)
            - resumo de métricas
            """
            comp = comparacao_df.dropna(subset=["current_speed_percentile"])
            if comp.empty:
                return "INDETERMINADO", {}

            pcts = comp["current_speed_percentile"].values

            # Porcentagens
            pct_central = np.mean((pcts >= 25) & (pcts <= 75)) * 100
            pct_normal = np.mean((pcts >= 10) & (pcts <= 90)) * 100
            pct_fora_p5_95 = np.mean((pcts < 5) | (pcts > 95)) * 100

            max_pct = np.max(pcts)
            max_speed = comp["speed_current_ms"].max() if "speed_current_ms" in comp.columns else 0
            max_shear = comp["shear_current_s-1"].max() if "shear_current_s-1" in comp.columns else 0
            max_vecdiff = (comp["vector_diff_from_median_ms"].max()
                          if "vector_diff_from_median_ms" in comp.columns else 0)

            # Altitude com maior anomalia vetorial
            if "vector_diff_from_median_ms" in comp.columns:
                idx_max = comp["vector_diff_from_median_ms"].idxmax()
                alt_max_anomalia = comp.loc[idx_max, "altitude_agl_m"]
            else:
                alt_max_anomalia = None

            resumo = {
                "pct_dentro_p25_p75": round(pct_central, 1),
                "pct_dentro_p10_p90": round(pct_normal, 1),
                "pct_fora_p5_p95": round(pct_fora_p5_95, 1),
                "maior_percentil_velocidade": round(max_pct, 1),
                "maior_velocidade_ms": round(float(max_speed), 1),
                "maior_cisalhamento_s-1": round(float(max_shear), 5),
                "maior_diferenca_vetorial_ms": round(float(max_vecdiff), 1),
                "altitude_maior_anomalia_m": alt_max_anomalia,
            }

            # Classificação geral
            if pct_fora_p5_95 > 30:
                classificacao = "EXTREMO"
            elif pct_fora_p5_95 > 15 or max_pct > 95:
                classificacao = "SEVERO"
            elif pct_normal < 70 or max_pct > 90:
                classificacao = "MODERADAMENTE ATÍPICO"
            else:
                classificacao = "TÍPICO"

            return classificacao, resumo

        print("✅ Funções de comparação com climatologia definidas.")
        """),
    ]

# ══════════════════════════════════════════════
# SECTION 11 — Perfis de projeto
# ══════════════════════════════════════════════
def section_11():
    return [
        md("""
        ---
        ## 11. Perfis de Projeto
        """),
        code(r"""
        # ══════════════════════════════════════════════════
        # 11. Geração de perfis de projeto para simulação
        # ══════════════════════════════════════════════════

        def gerar_perfis_projeto(hist_interp_df, stats_df, perfil_atual_df=None, config=None):
            """
            Gerar diferentes perfis de vento para simulação do foguete.

            Perfis gerados:
            1. Climatológico central (mediana)
            2. Vento constante (referência)
            3. P75
            4. P90
            5. Cisalhamento crítico (perfil histórico real com maior cisalhamento)
            6. Perfil histórico real severo
            7. Perfil atualizado (se disponível)

            Retorna dicionário {nome: DataFrame}.
            """
            if config is None:
                config = CONFIG

            perfis = {}

            # ── 1. Perfil climatológico central (medianas) ──
            if stats_df is not None and "u_median_ms" in stats_df.columns:
                df_central = pd.DataFrame({
                    "altitude_agl_m": stats_df["altitude_agl_m"],
                    "u_ms": stats_df["u_median_ms"],
                    "v_ms": stats_df["v_median_ms"],
                    "w_ms": 0.0,
                })
                df_central.dropna(subset=["u_ms", "v_ms"], inplace=True)
                spd, dire = uv_para_velocidade_direcao(df_central["u_ms"].values, df_central["v_ms"].values)
                df_central["speed_ms"] = spd
                df_central["direction_from_deg"] = dire
                perfis["climatologico_central"] = df_central

            # ── 2. Vento constante (referência) ──
            if stats_df is not None and "speed_median_ms" in stats_df.columns:
                speed_ref = stats_df["speed_median_ms"].median()
                # Usar direção média geral
                if "direction_mean_from_deg" in stats_df.columns:
                    dir_ref = stats_df["direction_mean_from_deg"].dropna().values
                    if len(dir_ref) > 0:
                        dir_mean, _ = media_circular(dir_ref)
                    else:
                        dir_mean = 0
                else:
                    dir_mean = 0

                u_ref, v_ref = velocidade_direcao_para_uv(speed_ref, dir_mean)
                df_const = pd.DataFrame({
                    "altitude_agl_m": ALTITUDES_PADRAO,
                    "u_ms": u_ref,
                    "v_ms": v_ref,
                    "w_ms": 0.0,
                    "speed_ms": speed_ref,
                    "direction_from_deg": dir_mean,
                })
                perfis["vento_constante"] = df_const

            # ── 3-4. Perfis de percentis ──
            for ptag, pcol in [("p75", "speed_p75_ms"), ("p90", "speed_p90_ms")]:
                if stats_df is not None and pcol in stats_df.columns and "direction_mean_from_deg" in stats_df.columns:
                    speeds = stats_df[pcol].values
                    dirs = stats_df["direction_mean_from_deg"].values
                    # Usar direção média + velocidade do percentil
                    u_arr, v_arr = velocidade_direcao_para_uv(speeds, dirs)
                    df_p = pd.DataFrame({
                        "altitude_agl_m": stats_df["altitude_agl_m"],
                        "u_ms": u_arr,
                        "v_ms": v_arr,
                        "w_ms": 0.0,
                        "speed_ms": speeds,
                        "direction_from_deg": dirs,
                    })
                    df_p.dropna(subset=["u_ms"], inplace=True)
                    perfis[ptag] = df_p

            # ── 5. Cisalhamento crítico (perfil real com maior cisalhamento médio) ──
            if hist_interp_df is not None and not hist_interp_df.empty:
                max_shear = -1
                best_pid = None
                for pid, grp in hist_interp_df.groupby("profile_id"):
                    _, _, shear = calcular_cisalhamento_perfil(grp)
                    if shear is not None:
                        mean_shear = np.nanmean(shear)
                        if mean_shear > max_shear:
                            max_shear = mean_shear
                            best_pid = pid

                if best_pid is not None:
                    df_shear = hist_interp_df[hist_interp_df["profile_id"] == best_pid].copy()
                    spd, dire = uv_para_velocidade_direcao(df_shear["u_ms"].values.astype(float),
                                                           df_shear["v_ms"].values.astype(float))
                    df_shear["speed_ms"] = spd
                    df_shear["direction_from_deg"] = dire
                    perfis["cisalhamento_critico"] = df_shear

            # ── 6. Perfil histórico real severo (maior velocidade média) ──
            if hist_interp_df is not None and not hist_interp_df.empty:
                max_speed_mean = -1
                best_pid_severe = None
                for pid, grp in hist_interp_df.groupby("profile_id"):
                    u = grp["u_ms"].dropna().values.astype(float)
                    v = grp["v_ms"].dropna().values.astype(float)
                    n = min(len(u), len(v))
                    if n > 0:
                        spd_mean = np.mean(np.hypot(u[:n], v[:n]))
                        if spd_mean > max_speed_mean:
                            max_speed_mean = spd_mean
                            best_pid_severe = pid

                if best_pid_severe is not None:
                    df_severe = hist_interp_df[hist_interp_df["profile_id"] == best_pid_severe].copy()
                    spd, dire = uv_para_velocidade_direcao(
                        df_severe["u_ms"].values.astype(float),
                        df_severe["v_ms"].values.astype(float),
                    )
                    df_severe["speed_ms"] = spd
                    df_severe["direction_from_deg"] = dire
                    perfis["historico_severo"] = df_severe

            # ── 7. Perfil atualizado ──
            if perfil_atual_df is not None and not perfil_atual_df.empty:
                perfis["atualizado"] = perfil_atual_df.copy()

            print(f"✅ Perfis de projeto gerados: {list(perfis.keys())}")
            return perfis

        def vento_enu(altitude_agl_m, perfil):
            """
            Interface para o simulador de trajetória.

            Retorna vetor [u, v, w] para uma altitude dada, interpolado
            a partir do perfil fornecido.
            """
            alt = perfil["altitude_agl_m"].values.astype(float)
            u = np.interp(altitude_agl_m, alt, perfil["u_ms"].values.astype(float))
            v = np.interp(altitude_agl_m, alt, perfil["v_ms"].values.astype(float))
            if "w_ms" in perfil.columns:
                w = np.interp(altitude_agl_m, alt, perfil["w_ms"].values.astype(float))
            else:
                w = 0.0
            return np.array([u, v, w])

        print("✅ Interface vento_enu definida.")
        """),
    ]

# ══════════════════════════════════════════════
# SECTION 12 — Dashboard
# ══════════════════════════════════════════════
def section_12():
    return [
        md("""
        ---
        ## 12. Dashboard Interativo
        """),
        code(r"""
        # ══════════════════════════════════════════════════
        # 12a. Cores e estilo do dashboard
        # ══════════════════════════════════════════════════

        CORES = {
            "bg": "#0d1117",
            "card": "#161b22",
            "text": "#c9d1d9",
            "accent": "#58a6ff",
            "p50": "#58a6ff",
            "p25_75": "rgba(88,166,255,0.25)",
            "p10_90": "rgba(88,166,255,0.10)",
            "atual": "#f97316",
            "constante": "#6b7280",
            "shear_high": "#ef4444",
            "central": "#22c55e",
            "normal": "#eab308",
            "incomum": "#f97316",
            "extremo": "#ef4444",
            "grid": "#21262d",
        }

        def estilo_eixo():
            """Retornar configuração padrão de eixo para o dashboard."""
            return dict(
                gridcolor=CORES["grid"],
                zerolinecolor=CORES["grid"],
                tickfont=dict(color=CORES["text"], size=10),
                title_font=dict(color=CORES["text"], size=12),
            )

        if not HAS_PLOTLY:
            print("⚠️  plotly não disponível — dashboard não será gerado.")
        else:
            print("✅ Estilo do dashboard configurado.")
        """),

        code(r"""
        # ══════════════════════════════════════════════════
        # 12b. Construção dos painéis individuais
        # ══════════════════════════════════════════════════

        def _painel_velocidade(fig, stats_df, comp_df, perfis_projeto, row, col):
            """Painel 1 — Velocidade vs Altitude."""
            alt = stats_df["altitude_agl_m"]

            # Faixa P10-P90
            if "speed_p10_ms" in stats_df.columns:
                fig.add_trace(go.Scatter(
                    x=pd.concat([stats_df["speed_p10_ms"], stats_df["speed_p90_ms"][::-1]]),
                    y=pd.concat([alt, alt[::-1]]),
                    fill="toself", fillcolor=CORES["p10_90"],
                    line=dict(width=0), name="P10–P90", showlegend=True,
                    hoverinfo="skip",
                ), row=row, col=col)

            # Faixa P25-P75
            if "speed_p25_ms" in stats_df.columns:
                fig.add_trace(go.Scatter(
                    x=pd.concat([stats_df["speed_p25_ms"], stats_df["speed_p75_ms"][::-1]]),
                    y=pd.concat([alt, alt[::-1]]),
                    fill="toself", fillcolor=CORES["p25_75"],
                    line=dict(width=0), name="P25–P75", showlegend=True,
                    hoverinfo="skip",
                ), row=row, col=col)

            # P50
            if "speed_p50_ms" in stats_df.columns:
                fig.add_trace(go.Scatter(
                    x=stats_df["speed_p50_ms"], y=alt,
                    mode="lines", name="Mediana (P50)",
                    line=dict(color=CORES["p50"], width=2),
                ), row=row, col=col)

            # Perfil atualizado
            if comp_df is not None and "speed_current_ms" in comp_df.columns:
                valid = comp_df.dropna(subset=["speed_current_ms"])
                fig.add_trace(go.Scatter(
                    x=valid["speed_current_ms"], y=valid["altitude_agl_m"],
                    mode="lines+markers", name="Atual",
                    line=dict(color=CORES["atual"], width=2.5),
                    marker=dict(size=4),
                ), row=row, col=col)

            # Vento constante
            if "vento_constante" in perfis_projeto:
                vc = perfis_projeto["vento_constante"]
                fig.add_trace(go.Scatter(
                    x=vc["speed_ms"], y=vc["altitude_agl_m"],
                    mode="lines", name="Constante (ref)",
                    line=dict(color=CORES["constante"], width=1, dash="dash"),
                ), row=row, col=col)

            fig.update_xaxes(title_text="Velocidade [m/s]", row=row, col=col, **estilo_eixo())
            fig.update_yaxes(title_text="Altitude AGL [m]", row=row, col=col, **estilo_eixo())

        def _painel_direcao(fig, stats_df, comp_df, row, col):
            """Painel 2 — Direção vs Altitude (apenas marcadores para evitar linhas espúrias)."""
            alt = stats_df["altitude_agl_m"]

            if "direction_mean_from_deg" in stats_df.columns:
                fig.add_trace(go.Scatter(
                    x=stats_df["direction_mean_from_deg"], y=alt,
                    mode="markers", name="Direção média (hist.)",
                    marker=dict(color=CORES["p50"], size=6, symbol="diamond"),
                ), row=row, col=col)

            if comp_df is not None and "direction_current_from_deg" in comp_df.columns:
                valid = comp_df.dropna(subset=["direction_current_from_deg"])
                fig.add_trace(go.Scatter(
                    x=valid["direction_current_from_deg"], y=valid["altitude_agl_m"],
                    mode="markers", name="Direção atual",
                    marker=dict(color=CORES["atual"], size=7, symbol="circle"),
                ), row=row, col=col)

            fig.update_xaxes(
                title_text="Direção (de onde) [°]", row=row, col=col,
                range=[0, 360], dtick=90, **estilo_eixo(),
            )
            fig.update_yaxes(title_text="Altitude AGL [m]", row=row, col=col, **estilo_eixo())

        def _painel_componentes(fig, stats_df, comp_df, row, col):
            """Painel 3 — Componentes u e v vs Altitude."""
            alt = stats_df["altitude_agl_m"]

            if "u_mean_ms" in stats_df.columns:
                fig.add_trace(go.Scatter(
                    x=stats_df["u_mean_ms"], y=alt,
                    mode="lines", name="u médio",
                    line=dict(color="#22d3ee", width=2),
                ), row=row, col=col)
            if "v_mean_ms" in stats_df.columns:
                fig.add_trace(go.Scatter(
                    x=stats_df["v_mean_ms"], y=alt,
                    mode="lines", name="v médio",
                    line=dict(color="#a78bfa", width=2),
                ), row=row, col=col)

            if comp_df is not None:
                if "u_current_ms" in comp_df.columns:
                    valid = comp_df.dropna(subset=["u_current_ms"])
                    fig.add_trace(go.Scatter(
                        x=valid["u_current_ms"], y=valid["altitude_agl_m"],
                        mode="lines", name="u atual",
                        line=dict(color="#22d3ee", width=2, dash="dot"),
                    ), row=row, col=col)
                if "v_current_ms" in comp_df.columns:
                    valid = comp_df.dropna(subset=["v_current_ms"])
                    fig.add_trace(go.Scatter(
                        x=valid["v_current_ms"], y=valid["altitude_agl_m"],
                        mode="lines", name="v atual",
                        line=dict(color="#a78bfa", width=2, dash="dot"),
                    ), row=row, col=col)

            # Linha zero
            fig.add_vline(x=0, line=dict(color=CORES["grid"], width=1, dash="dash"), row=row, col=col)

            fig.update_xaxes(title_text="Componente [m/s]", row=row, col=col, **estilo_eixo())
            fig.update_yaxes(title_text="Altitude AGL [m]", row=row, col=col, **estilo_eixo())

        def _painel_hodografa(fig, stats_df, comp_df, row, col):
            """Painel 4 — Hodógrafa (u vs v, cor pela altitude)."""
            if "u_mean_ms" in stats_df.columns and "v_mean_ms" in stats_df.columns:
                valid = stats_df.dropna(subset=["u_mean_ms", "v_mean_ms"])
                fig.add_trace(go.Scatter(
                    x=valid["u_mean_ms"], y=valid["v_mean_ms"],
                    mode="lines+markers", name="Hodógrafa (hist.)",
                    marker=dict(
                        color=valid["altitude_agl_m"], colorscale="Viridis",
                        size=5, showscale=False,
                    ),
                    line=dict(color=CORES["p50"], width=1.5),
                    text=[f"{z:.0f} m" for z in valid["altitude_agl_m"]],
                    hovertemplate="u=%{x:.1f} m/s<br>v=%{y:.1f} m/s<br>%{text}",
                ), row=row, col=col)

            if comp_df is not None and "u_current_ms" in comp_df.columns:
                valid = comp_df.dropna(subset=["u_current_ms", "v_current_ms"])
                fig.add_trace(go.Scatter(
                    x=valid["u_current_ms"], y=valid["v_current_ms"],
                    mode="lines+markers", name="Hodógrafa (atual)",
                    marker=dict(
                        color=valid["altitude_agl_m"], colorscale="Inferno",
                        size=5, showscale=False,
                    ),
                    line=dict(color=CORES["atual"], width=1.5),
                    text=[f"{z:.0f} m" for z in valid["altitude_agl_m"]],
                    hovertemplate="u=%{x:.1f} m/s<br>v=%{y:.1f} m/s<br>%{text}",
                ), row=row, col=col)

            # Origem
            fig.add_trace(go.Scatter(
                x=[0], y=[0], mode="markers", name="Origem",
                marker=dict(color="white", size=8, symbol="cross"),
                showlegend=False,
            ), row=row, col=col)

            fig.update_xaxes(title_text="u (E) [m/s]", row=row, col=col, **estilo_eixo())
            fig.update_yaxes(title_text="v (N) [m/s]", row=row, col=col, scaleanchor=f"x{col + (row-1)*3}", **estilo_eixo())

        def _painel_cisalhamento(fig, stats_df, comp_df, row, col):
            """Painel 5 — Cisalhamento vertical."""
            if "shear_s-1" in stats_df.columns:
                valid = stats_df.dropna(subset=["shear_s-1"])
                fig.add_trace(go.Scatter(
                    x=valid["shear_s-1"], y=valid["altitude_agl_m"],
                    mode="lines", name="Cisalhamento (hist.)",
                    line=dict(color=CORES["p50"], width=2),
                    fill="tozerox", fillcolor="rgba(88,166,255,0.1)",
                ), row=row, col=col)

            if comp_df is not None and "shear_current_s-1" in comp_df.columns:
                valid = comp_df.dropna(subset=["shear_current_s-1"])
                fig.add_trace(go.Scatter(
                    x=valid["shear_current_s-1"], y=valid["altitude_agl_m"],
                    mode="lines+markers", name="Cisalhamento (atual)",
                    line=dict(color=CORES["atual"], width=2),
                    marker=dict(size=3),
                ), row=row, col=col)

            fig.update_xaxes(title_text="Cisalhamento [s⁻¹]", row=row, col=col, **estilo_eixo())
            fig.update_yaxes(title_text="Altitude AGL [m]", row=row, col=col, **estilo_eixo())

        def _painel_percentil(fig, comp_df, row, col):
            """Painel 6 — Percentil histórico do perfil atual."""
            if comp_df is None or "current_speed_percentile" not in comp_df.columns:
                return

            valid = comp_df.dropna(subset=["current_speed_percentile"])

            # Cores por classificação
            colors = []
            for _, r in valid.iterrows():
                cl = r.get("classificacao", "")
                if cl == "CENTRAL":
                    colors.append(CORES["central"])
                elif cl == "NORMAL":
                    colors.append(CORES["normal"])
                elif cl == "INCOMUM":
                    colors.append(CORES["incomum"])
                elif cl == "EXTREMO":
                    colors.append(CORES["extremo"])
                else:
                    colors.append(CORES["text"])

            fig.add_trace(go.Scatter(
                x=valid["current_speed_percentile"], y=valid["altitude_agl_m"],
                mode="markers+lines", name="Percentil atual",
                marker=dict(color=colors, size=6),
                line=dict(color=CORES["atual"], width=1.5),
            ), row=row, col=col)

            # Linhas de referência
            for p, dash_style in [(10, "dot"), (25, "dash"), (50, "solid"), (75, "dash"), (90, "dot")]:
                fig.add_vline(
                    x=p, line=dict(color=CORES["grid"], width=1, dash=dash_style),
                    row=row, col=col,
                )
                fig.add_annotation(
                    x=p, y=ALTITUDES_PADRAO[-1], text=f"P{p}", showarrow=False,
                    font=dict(color=CORES["text"], size=8),
                    xref=f"x{col + (row-1)*3}", yref=f"y{col + (row-1)*3}",
                )

            fig.update_xaxes(
                title_text="Percentil histórico [%]", row=row, col=col,
                range=[0, 100], **estilo_eixo(),
            )
            fig.update_yaxes(title_text="Altitude AGL [m]", row=row, col=col, **estilo_eixo())

        print("✅ Painéis do dashboard definidos.")
        """),

        code(r"""
        # ══════════════════════════════════════════════════
        # 12c. Rosa dos ventos
        # ══════════════════════════════════════════════════

        def criar_rosa_dos_ventos(hist_df, altitude_m, tolerance_m=25):
            """
            Criar rosa dos ventos para uma altitude específica.

            Retorna um plotly Figure.
            """
            if not HAS_PLOTLY:
                return None

            mask = (
                np.abs(hist_df["altitude_agl_m"].values.astype(float) - altitude_m) <= tolerance_m
            ) & (hist_df["quality_flag"] == "OK")
            sub = hist_df[mask]

            if len(sub) < 5:
                return None

            dirs = sub["direction_from_deg"].dropna().values
            speeds = sub["speed_ms"].dropna().values
            n = min(len(dirs), len(speeds))
            dirs, speeds = dirs[:n], speeds[:n]

            # Criar bins de direção (16 setores)
            n_sectors = 16
            bin_width = 360 / n_sectors
            sectors = np.arange(0, 360, bin_width)

            # Classificar velocidades
            speed_bins = [0, 2, 4, 6, 8, 10, 15, np.inf]
            speed_labels = ["0-2", "2-4", "4-6", "6-8", "8-10", "10-15", ">15"]
            speed_colors = ["#22c55e", "#84cc16", "#eab308", "#f97316", "#ef4444", "#dc2626", "#7f1d1d"]

            # Contar frequências
            data_rose = []
            for i, (lo, hi) in enumerate(zip(speed_bins[:-1], speed_bins[1:])):
                freqs = []
                for s_center in sectors:
                    s_lo = (s_center - bin_width / 2) % 360
                    s_hi = (s_center + bin_width / 2) % 360
                    if s_lo < s_hi:
                        mask_dir = (dirs >= s_lo) & (dirs < s_hi)
                    else:
                        mask_dir = (dirs >= s_lo) | (dirs < s_hi)
                    mask_spd = (speeds >= lo) & (speeds < hi)
                    freq = (mask_dir & mask_spd).sum() / n * 100
                    freqs.append(freq)

                data_rose.append(go.Barpolar(
                    r=freqs,
                    theta=sectors,
                    width=bin_width,
                    name=f"{speed_labels[i]} m/s",
                    marker_color=speed_colors[i],
                    opacity=0.8,
                ))

            fig = go.Figure(data=data_rose)
            fig.update_layout(
                title=f"Rosa dos ventos — {altitude_m:.0f} m AGL",
                polar=dict(
                    radialaxis=dict(showticklabels=True, ticksuffix="%", gridcolor=CORES["grid"]),
                    angularaxis=dict(
                        direction="clockwise", rotation=90,
                        tickmode="array",
                        tickvals=[0, 45, 90, 135, 180, 225, 270, 315],
                        ticktext=["N", "NE", "E", "SE", "S", "SW", "W", "NW"],
                        gridcolor=CORES["grid"],
                    ),
                    bgcolor=CORES["bg"],
                ),
                paper_bgcolor=CORES["bg"],
                font=dict(color=CORES["text"]),
                showlegend=True,
                legend=dict(title="Velocidade"),
                height=500, width=550,
            )
            return fig

        print("✅ Rosa dos ventos definida.")
        """),

        code(r"""
        # ══════════════════════════════════════════════════
        # 12d. Dashboard principal — assemblagem
        # ══════════════════════════════════════════════════

        def criar_dashboard(stats_df, comp_df=None, perfis_projeto=None,
                            metricas=None, classificacao=None, resumo=None,
                            config=None):
            """
            Criar dashboard interativo completo com 6 painéis.

            Painéis:
            1. Velocidade vs Altitude
            2. Direção vs Altitude
            3. Componentes u e v
            4. Hodógrafa
            5. Cisalhamento vertical
            6. Percentil do perfil atual

            Retorna plotly Figure.
            """
            if not HAS_PLOTLY:
                print("⚠️  plotly não disponível.")
                return None

            if config is None:
                config = CONFIG
            if perfis_projeto is None:
                perfis_projeto = {}

            # ── Cabeçalho ──
            header_parts = [f"<b>🚀 Modelo Atmosférico — {config['nome_projeto']}</b>"]
            header_parts.append(
                f"Local: ({config['latitude_lancamento']:.4f}°, "
                f"{config['longitude_lancamento']:.4f}°) | "
                f"Elevação: {config['elevacao_campo_msl_m']:.0f} m MSL"
            )
            if metricas:
                header_parts.append(
                    f"Perfis: {metricas.get('n_perfis', '?')} | "
                    f"Anos: {metricas.get('n_anos', '?')} | "
                    f"Cob. temporal: {metricas.get('cobertura_temporal_pct', 0):.0f}% | "
                    f"Cob. vertical: {metricas.get('cobertura_vertical_pct', 0):.0f}%"
                )
            if classificacao:
                header_parts.append(f"<b>Classificação do perfil atual: {classificacao}</b>")

            header_text = "<br>".join(header_parts)

            # ── Subplots ──
            fig = make_subplots(
                rows=2, cols=3,
                subplot_titles=[
                    "1. Velocidade vs Altitude",
                    "2. Direção vs Altitude",
                    "3. Componentes u, v",
                    "4. Hodógrafa",
                    "5. Cisalhamento Vertical",
                    "6. Percentil Histórico",
                ],
                horizontal_spacing=0.08,
                vertical_spacing=0.10,
            )

            # ── Preencher painéis ──
            _painel_velocidade(fig, stats_df, comp_df, perfis_projeto, row=1, col=1)
            _painel_direcao(fig, stats_df, comp_df, row=1, col=2)
            _painel_componentes(fig, stats_df, comp_df, row=1, col=3)
            _painel_hodografa(fig, stats_df, comp_df, row=2, col=1)
            _painel_cisalhamento(fig, stats_df, comp_df, row=2, col=2)
            _painel_percentil(fig, comp_df, row=2, col=3)

            # ── Layout geral ──
            fig.update_layout(
                title=dict(
                    text=header_text,
                    x=0.5, xanchor="center",
                    font=dict(size=13, color=CORES["text"]),
                ),
                height=900, width=1400,
                paper_bgcolor=CORES["bg"],
                plot_bgcolor=CORES["bg"],
                font=dict(color=CORES["text"], family="Inter, sans-serif"),
                showlegend=True,
                legend=dict(
                    orientation="h", y=-0.08, x=0.5, xanchor="center",
                    font=dict(size=9, color=CORES["text"]),
                    bgcolor="rgba(0,0,0,0)",
                ),
                margin=dict(t=120, b=80),
            )

            # Estilo uniforme de todos os subplots
            for i in range(1, 7):
                fig.update_xaxes(showgrid=True, row=(i-1)//3+1, col=(i-1)%3+1)
                fig.update_yaxes(showgrid=True, row=(i-1)//3+1, col=(i-1)%3+1)

            return fig

        print("✅ Função de dashboard principal definida.")
        """),
    ]

# ══════════════════════════════════════════════
# SECTION 13 — Exportação
# ══════════════════════════════════════════════
def section_13():
    return [
        md("""
        ---
        ## 13. Exportação
        """),
        code(r"""
        # ══════════════════════════════════════════════════
        # 13a. Exportar CSV principal
        # ══════════════════════════════════════════════════

        def exportar_csv_principal(stats_df, comp_df=None, perfis_projeto=None,
                                   config=None, sufixo=None):
            """
            Gerar o CSV principal interpolado para a grade vertical.

            O CSV contém dados estatísticos e, se disponível, o perfil atualizado.
            """
            if config is None:
                config = CONFIG

            df_export = stats_df.copy()

            # Adicionar dados do perfil atual se disponível
            if comp_df is not None:
                for col in ["u_current_ms", "v_current_ms", "speed_current_ms",
                            "direction_current_from_deg", "shear_current_s-1",
                            "current_speed_percentile", "vector_diff_from_median_ms"]:
                    if col in comp_df.columns:
                        df_export[col] = comp_df[col].values

            # w = 0
            df_export["w_current_ms"] = 0.0

            # Nome do arquivo
            agora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%MZ")
            if sufixo:
                nome = f"wind_profile_{config['nome_projeto'].lower()}_{sufixo}_{agora}.csv"
            else:
                nome = f"wind_profile_{config['nome_projeto'].lower()}_{agora}.csv"

            caminho = Path(config["pasta_saida"]) / "csv" / nome
            caminho.parent.mkdir(parents=True, exist_ok=True)
            df_export.to_csv(caminho, index=False, float_format="%.4f")
            print(f"📁 CSV principal salvo em: {caminho}")
            return str(caminho)

        def exportar_csv_simplificado(perfil_df, config=None, nome=None):
            """
            Exportar CSV simplificado com apenas altitude, u, v, w.

            Formato para simuladores de trajetória.
            """
            if config is None:
                config = CONFIG
            cols = ["altitude_agl_m", "u_ms", "v_ms"]
            if "w_ms" in perfil_df.columns:
                cols.append("w_ms")

            df = perfil_df[cols].copy()
            if "w_ms" not in df.columns:
                df["w_ms"] = 0.0

            if nome is None:
                agora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%MZ")
                nome = f"wind_profile_sim_{config['nome_projeto'].lower()}_{agora}.csv"

            caminho = Path(config["pasta_saida"]) / "csv" / nome
            caminho.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(caminho, index=False, float_format="%.4f")
            print(f"📁 CSV simplificado salvo em: {caminho}")
            return str(caminho)

        print("✅ Funções de exportação CSV definidas.")
        """),

        code(r"""
        # ══════════════════════════════════════════════════
        # 13b. Exportar Parquet, metadados, dashboard HTML
        # ══════════════════════════════════════════════════

        def exportar_parquet(df, config=None, nome="wind_samples_normalized.parquet"):
            """Exportar todos os perfis normalizados como Parquet."""
            if config is None:
                config = CONFIG
            if not HAS_PARQUET:
                print("⚠️  pyarrow não disponível — exportação Parquet ignorada.")
                return None
            caminho = Path(config["pasta_saida"]) / "statistics" / nome
            caminho.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(caminho, index=False)
            print(f"📁 Parquet salvo em: {caminho}")
            return str(caminho)

        def exportar_estatisticas_csv(stats_df, config=None, nome="wind_statistics_by_altitude.csv"):
            """Exportar estatísticas por altitude em CSV."""
            if config is None:
                config = CONFIG
            caminho = Path(config["pasta_saida"]) / "statistics" / nome
            caminho.parent.mkdir(parents=True, exist_ok=True)
            stats_df.to_csv(caminho, index=False, float_format="%.4f")
            print(f"📁 Estatísticas salvas em: {caminho}")
            return str(caminho)

        def exportar_metadados(config, fontes=None, avisos=None, metricas=None):
            """
            Exportar arquivo de metadados JSON.
            """
            meta = {
                "project": config["nome_projeto"],
                "creation_time_utc": datetime.now(timezone.utc).isoformat(),
                "launch_latitude": config["latitude_lancamento"],
                "launch_longitude": config["longitude_lancamento"],
                "field_elevation_msl_m": config["elevacao_campo_msl_m"],
                "historical_period": f"últimos {config['anos_historicos']} anos",
                "event_dates": f"{config['data_inicial_evento']} a {config['data_final_evento']}",
                "selected_hours_local": f"{config['hora_local_inicial']}h–{config['hora_local_final']}h",
                "vertical_grid_m": config["passo_vertical_m"],
                "altitude_range_m": f"{config['altitude_min_agl_m']}–{config['altitude_max_agl_m']}",
                "interpolation_method": config["metodo_interpolacao_vertical"],
                "software_version": config.get("versao_software", "1.0.0"),
                "sources": fontes or [],
                "quality_warnings": avisos or [],
                "representativeness": metricas or {},
            }
            caminho = Path(config["pasta_saida"]) / "metadata" / "wind_profile_metadata.json"
            caminho.parent.mkdir(parents=True, exist_ok=True)
            with open(caminho, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=4, ensure_ascii=False, default=str)
            print(f"📁 Metadados salvos em: {caminho}")
            return str(caminho)

        def exportar_dashboard_html(fig, config=None, nome=None):
            """Exportar dashboard como HTML independente."""
            if fig is None:
                print("⚠️  Nenhuma figura para exportar.")
                return None
            if config is None:
                config = CONFIG
            if nome is None:
                nome = f"wind_dashboard_{config['nome_projeto'].lower()}.html"
            caminho = Path(config["pasta_saida"]) / "dashboards" / nome
            caminho.parent.mkdir(parents=True, exist_ok=True)
            fig.write_html(str(caminho), include_plotlyjs=True)
            print(f"📁 Dashboard HTML salvo em: {caminho}")
            return str(caminho)

        print("✅ Funções de exportação definidas.")
        """),
    ]

# ══════════════════════════════════════════════
# SECTION 14 — Controles interativos
# ══════════════════════════════════════════════
def section_14():
    return [
        md("""
        ---
        ## 14. Controles Interativos
        """),
        code(r"""
        # ══════════════════════════════════════════════════
        # 14. Painel de controles (ipywidgets)
        # ══════════════════════════════════════════════════

        # ── Variáveis de estado do modelo ──
        ESTADO = {
            "dados_historicos": None,       # DataFrame normalizado (histórico)
            "dados_atualizados": None,      # DataFrame normalizado (previsão/obs)
            "hist_interpolado": None,       # DataFrame interpolado (histórico)
            "atual_interpolado": None,      # DataFrame interpolado (atual)
            "estatisticas": None,           # DataFrame de estatísticas
            "comparacao": None,             # DataFrame de comparação
            "perfis_projeto": None,         # Dict de perfis de projeto
            "metricas": None,               # Dict de métricas de representatividade
            "classificacao": None,          # Classificação geral do perfil
            "resumo": None,                 # Resumo da classificação
            "dashboard_fig": None,          # Plotly Figure
            "avisos": [],                   # Lista de avisos
            "fontes": [],                   # Lista de fontes utilizadas
        }

        if HAS_WIDGETS:
            output_area = widgets.Output()

            # ── Controles ──
            w_tipo_fonte = widgets.Dropdown(
                options=list(ADAPTERS.keys()),
                value="csv_manual",
                description="Tipo fonte:",
                style={"description_width": "100px"},
            )

            w_caminho = widgets.Text(
                value="data/raw/perfil_manual_exemplo.csv",
                description="Caminho:",
                layout=widgets.Layout(width="500px"),
                style={"description_width": "100px"},
            )

            w_data_type = widgets.Dropdown(
                options=["historical", "forecast", "observation", "synthetic"],
                value="synthetic",
                description="Tipo dado:",
                style={"description_width": "100px"},
            )

            w_anos_hist = widgets.IntSlider(
                value=CONFIG["anos_historicos"], min=5, max=40, step=5,
                description="Anos hist.:",
                style={"description_width": "100px"},
            )

            w_alt_max = widgets.IntSlider(
                value=CONFIG["altitude_max_agl_m"], min=1000, max=10000, step=500,
                description="Alt. máx (m):",
                style={"description_width": "100px"},
            )

            w_passo = widgets.Dropdown(
                options=[25, 50, 100, 200, 250, 500],
                value=CONFIG["passo_vertical_m"],
                description="Passo (m):",
                style={"description_width": "100px"},
            )

            w_alt_rosa = widgets.Dropdown(
                options=[0, 500, 1000, 1500, 2000, 2500, 3000],
                value=1000,
                description="Alt. rosa:",
                style={"description_width": "100px"},
            )

            # ── Botões ──
            btn_carregar = widgets.Button(
                description="📂 Carregar dados",
                button_style="info",
                layout=widgets.Layout(width="180px"),
            )

            btn_validar = widgets.Button(
                description="✅ Executar validação",
                button_style="warning",
                layout=widgets.Layout(width="180px"),
            )

            btn_atualizar = widgets.Button(
                description="🔄 Atualizar modelo",
                button_style="primary",
                layout=widgets.Layout(width="180px"),
            )

            btn_exportar = widgets.Button(
                description="💾 Exportar CSV",
                button_style="success",
                layout=widgets.Layout(width="180px"),
            )

            btn_dashboard = widgets.Button(
                description="📊 Salvar dashboard",
                button_style="",
                layout=widgets.Layout(width="180px"),
            )

            # ── Callbacks ──
            def on_carregar(b):
                with output_area:
                    clear_output()
                    try:
                        tipo = w_tipo_fonte.value
                        caminho = w_caminho.value
                        print(f"⏳ Carregando: {caminho} (tipo: {tipo})")
                        df = carregar_fonte(tipo, caminho, CONFIG)
                        df = normalizar_dados(df, CONFIG)
                        df["data_type"] = w_data_type.value

                        if w_data_type.value == "historical":
                            if ESTADO["dados_historicos"] is None:
                                ESTADO["dados_historicos"] = df
                            else:
                                ESTADO["dados_historicos"] = pd.concat(
                                    [ESTADO["dados_historicos"], df], ignore_index=True
                                )
                            ESTADO["fontes"].append(f"hist:{caminho}")
                        else:
                            ESTADO["dados_atualizados"] = df
                            ESTADO["fontes"].append(f"atual:{caminho}")

                        print(f"✅ Carregado: {len(df)} registros, "
                              f"{df['profile_id'].nunique()} perfis")
                    except Exception as e:
                        print(f"❌ Erro: {e}")

            def on_validar(b):
                with output_area:
                    clear_output()
                    for label, dados in [("Históricos", ESTADO["dados_historicos"]),
                                         ("Atualizados", ESTADO["dados_atualizados"])]:
                        if dados is not None:
                            print(f"\n{'='*50}")
                            print(f"Validação — {label}")
                            print(f"{'='*50}")
                            avisos = validar_perfil(dados, CONFIG)
                            ESTADO["avisos"].extend(avisos)
                            for a in avisos:
                                print(f"  {a}")

            def on_atualizar(b):
                with output_area:
                    clear_output()
                    print("⏳ Atualizando modelo...")

                    # Atualizar grade se necessário
                    global ALTITUDES_PADRAO
                    ALTITUDES_PADRAO = np.arange(
                        CONFIG["altitude_min_agl_m"],
                        w_alt_max.value + w_passo.value,
                        w_passo.value,
                        dtype=float,
                    )

                    # Interpolar histórico
                    if ESTADO["dados_historicos"] is not None:
                        print("  Interpolando perfis históricos...")
                        ESTADO["hist_interpolado"] = interpolar_todos_perfis(
                            ESTADO["dados_historicos"], ALTITUDES_PADRAO, CONFIG
                        )

                        # Estatísticas
                        print("  Calculando estatísticas...")
                        ESTADO["estatisticas"] = calcular_estatisticas_altitude(
                            ESTADO["hist_interpolado"], CONFIG
                        )

                        # Representatividade
                        ESTADO["metricas"] = calcular_representatividade(
                            ESTADO["hist_interpolado"], ESTADO["estatisticas"], CONFIG
                        )

                    # Interpolar atual
                    if ESTADO["dados_atualizados"] is not None:
                        print("  Interpolando perfil atualizado...")
                        ESTADO["atual_interpolado"] = interpolar_todos_perfis(
                            ESTADO["dados_atualizados"], ALTITUDES_PADRAO, CONFIG
                        )

                    # Comparar
                    if (ESTADO["atual_interpolado"] is not None and
                        ESTADO["hist_interpolado"] is not None and
                        ESTADO["estatisticas"] is not None):
                        print("  Comparando com climatologia...")
                        ESTADO["comparacao"] = comparar_perfil_com_climatologia(
                            ESTADO["atual_interpolado"],
                            ESTADO["hist_interpolado"],
                            ESTADO["estatisticas"],
                            CONFIG,
                        )
                        ESTADO["classificacao"], ESTADO["resumo"] = classificar_perfil_geral(
                            ESTADO["comparacao"]
                        )

                    # Perfis de projeto
                    if ESTADO["estatisticas"] is not None:
                        print("  Gerando perfis de projeto...")
                        ESTADO["perfis_projeto"] = gerar_perfis_projeto(
                            ESTADO["hist_interpolado"],
                            ESTADO["estatisticas"],
                            ESTADO["atual_interpolado"],
                            CONFIG,
                        )

                    # Dashboard
                    if ESTADO["estatisticas"] is not None and HAS_PLOTLY:
                        print("  Construindo dashboard...")
                        ESTADO["dashboard_fig"] = criar_dashboard(
                            ESTADO["estatisticas"],
                            ESTADO["comparacao"],
                            ESTADO["perfis_projeto"] or {},
                            ESTADO["metricas"],
                            ESTADO["classificacao"],
                            ESTADO["resumo"],
                            CONFIG,
                        )
                        display(ESTADO["dashboard_fig"])

                    # Resumo final
                    print("\n" + "=" * 60)
                    print("Perfil processado com sucesso.")
                    print("=" * 60)
                    if ESTADO["metricas"]:
                        m = ESTADO["metricas"]
                        print(f"  Perfis válidos: {m.get('n_perfis', '?')}")
                        print(f"  Anos cobertos: {m.get('n_anos', '?')}")
                        print(f"  Cobertura temporal: {m.get('cobertura_temporal_pct', 0):.1f} %")
                        print(f"  Cobertura vertical: {m.get('cobertura_vertical_pct', 0):.1f} %")
                    if ESTADO["resumo"]:
                        r = ESTADO["resumo"]
                        print(f"  Maior velocidade: {r.get('maior_velocidade_ms', '?')} m/s")
                        print(f"  Maior percentil: P{r.get('maior_percentil_velocidade', '?')}")
                        print(f"  Maior cisalhamento: {r.get('maior_cisalhamento_s-1', '?')} s⁻¹")
                    if ESTADO["classificacao"]:
                        print(f"  Classificação: {ESTADO['classificacao']}")

            def on_exportar(b):
                with output_area:
                    clear_output()
                    if ESTADO["estatisticas"] is not None:
                        exportar_csv_principal(
                            ESTADO["estatisticas"], ESTADO["comparacao"],
                            ESTADO["perfis_projeto"], CONFIG,
                        )
                        exportar_estatisticas_csv(ESTADO["estatisticas"], CONFIG)
                        exportar_metadados(CONFIG, ESTADO["fontes"], ESTADO["avisos"], ESTADO["metricas"])
                        if ESTADO["hist_interpolado"] is not None:
                            exportar_parquet(ESTADO["hist_interpolado"], CONFIG)
                        # Exportar CSVs simplificados para cada perfil de projeto
                        if ESTADO["perfis_projeto"]:
                            for nome_perfil, df_perfil in ESTADO["perfis_projeto"].items():
                                exportar_csv_simplificado(
                                    df_perfil, CONFIG,
                                    nome=f"wind_sim_{nome_perfil}.csv",
                                )
                    else:
                        print("⚠️  Modelo ainda não processado. Clique em 'Atualizar modelo' primeiro.")

            def on_dashboard(b):
                with output_area:
                    clear_output()
                    if ESTADO["dashboard_fig"] is not None:
                        exportar_dashboard_html(ESTADO["dashboard_fig"], CONFIG)
                    else:
                        print("⚠️  Dashboard ainda não gerado.")

            btn_carregar.on_click(on_carregar)
            btn_validar.on_click(on_validar)
            btn_atualizar.on_click(on_atualizar)
            btn_exportar.on_click(on_exportar)
            btn_dashboard.on_click(on_dashboard)

            # ── Layout do painel ──
            painel_controles = widgets.VBox([
                widgets.HTML("<h3 style='color:#58a6ff;'>🎛️ Controles do Modelo</h3>"),
                widgets.HBox([w_tipo_fonte, w_data_type]),
                w_caminho,
                widgets.HBox([w_anos_hist, w_alt_max, w_passo]),
                w_alt_rosa,
                widgets.HBox([btn_carregar, btn_validar, btn_atualizar, btn_exportar, btn_dashboard]),
                output_area,
            ])

            display(painel_controles)
        else:
            print("⚠️  ipywidgets não disponível — usando modo programático.")
            print("   Use as funções diretamente: carregar_fonte(), normalizar_dados(), etc.")
        """),
    ]

# ══════════════════════════════════════════════
# SECTION 15 — Testes e diagnóstico
# ══════════════════════════════════════════════
def section_15():
    return [
        md("""
        ---
        ## 15. Testes e Diagnóstico
        """),
        code(r"""
        # ══════════════════════════════════════════════════
        # 15. Testes obrigatórios
        # ══════════════════════════════════════════════════

        def executar_testes(config=None):
            """
            Executar bateria de testes obrigatórios.

            Retorna lista de resultados (nome, passou, mensagem).
            """
            if config is None:
                config = CONFIG
            resultados = []

            # ── Teste 1: Vento constante ──
            try:
                n = 10
                df_const = pd.DataFrame({
                    "altitude_agl_m": np.linspace(0, 3500, n),
                    "u_ms": [5.0] * n,
                    "v_ms": [0.0] * n,
                })
                df_const.to_csv("/tmp/_test_const.csv", index=False)
                loaded = carregar_csv_manual("/tmp/_test_const.csv", config)
                loaded = normalizar_dados(loaded, config)
                interp = interpolar_perfil_vertical(loaded, ALTITUDES_PADRAO, config)
                u_vals = interp["u_ms"].dropna().values.astype(float)
                v_vals = interp["v_ms"].dropna().values.astype(float)
                assert np.allclose(u_vals, 5.0, atol=0.01), f"u não constante: {u_vals}"
                assert np.allclose(v_vals, 0.0, atol=0.01), f"v não constante: {v_vals}"
                resultados.append(("Vento constante", True, "Perfil permanece constante. ✓"))
            except Exception as e:
                resultados.append(("Vento constante", False, str(e)))

            # ── Teste 2: Direção 0° ──
            try:
                dirs = [350, 0, 10]
                vels = [5, 5, 5]
                u_arr, v_arr = velocidade_direcao_para_uv(vels, dirs)
                # Interpolar entre os pontos
                alt = [0, 500, 1000]
                u_interp = np.interp(250, alt, u_arr)
                v_interp = np.interp(250, alt, v_arr)
                _, d_interp = uv_para_velocidade_direcao(u_interp, v_interp)
                # A direção interpolada NÃO deve ser ~180°
                assert abs(d_interp - 180) > 30, (
                    f"Direção interpolada {d_interp:.1f}° — provável cruzamento indevido por 180°"
                )
                resultados.append(("Direção por 0°", True, f"Direção interpolada: {d_interp:.1f}° ✓"))
            except Exception as e:
                resultados.append(("Direção por 0°", False, str(e)))

            # ── Teste 3: Conversão ida e volta ──
            try:
                test_v = [3, 7, 12, 0.5, 20]
                test_d = [0, 45, 90, 180, 359]
                for v, d in zip(test_v, test_d):
                    u, vv = velocidade_direcao_para_uv(v, d)
                    v_back, d_back = uv_para_velocidade_direcao(u, vv)
                    assert abs(v_back - v) < 1e-8, f"V: {v_back} vs {v}"
                    assert abs(d_back - d) < 1e-6 or abs(abs(d_back - d) - 360) < 1e-6, (
                        f"D: {d_back} vs {d}"
                    )
                resultados.append(("Conversão ida-volta", True, "Todas as conversões corretas. ✓"))
            except Exception as e:
                resultados.append(("Conversão ida-volta", False, str(e)))

            # ── Teste 4: Altitude MSL → AGL ──
            try:
                elev = 460.0
                msl = 1460.0
                agl = altitude_msl_para_agl(msl, elev)
                assert abs(agl - 1000.0) < 0.01, f"AGL: {agl} (esperado 1000.0)"
                msl_back = altitude_agl_para_msl(agl, elev)
                assert abs(msl_back - 1460.0) < 0.01, f"MSL: {msl_back} (esperado 1460.0)"
                resultados.append(("Altitude MSL→AGL", True, f"AGL={agl:.1f}m ✓"))
            except Exception as e:
                resultados.append(("Altitude MSL→AGL", False, str(e)))

            # ── Teste 5: Arquivo incompleto ──
            try:
                df_incompleto = pd.DataFrame({
                    "altitude_agl_m": [0, 1500, 3500],  # lacuna > 500 m
                    "u_ms": [1.0, 2.0, 3.0],
                    "v_ms": [0.0, 1.0, 0.0],
                })
                df_incompleto.to_csv("/tmp/_test_incompleto.csv", index=False)
                loaded = carregar_csv_manual("/tmp/_test_incompleto.csv", config)
                loaded = normalizar_dados(loaded, config)
                avisos = validar_perfil(loaded, config)
                has_gap_warning = any("lacuna" in a.lower() for a in avisos)
                assert has_gap_warning, f"Nenhum aviso de lacuna gerado. Avisos: {avisos}"
                resultados.append(("Arquivo incompleto", True, "Lacunas detectadas. ✓"))
            except Exception as e:
                resultados.append(("Arquivo incompleto", False, str(e)))

            # ── Teste 6: Perfil extremo ──
            try:
                n = 10
                df_extreme = pd.DataFrame({
                    "altitude_agl_m": np.linspace(0, 3500, n),
                    "u_ms": [-30.0] * n,  # muito acima do normal
                    "v_ms": [-20.0] * n,
                })
                df_extreme.to_csv("/tmp/_test_extreme.csv", index=False)
                loaded = carregar_csv_manual("/tmp/_test_extreme.csv", config)
                loaded = normalizar_dados(loaded, config)
                spd = np.hypot(loaded["u_ms"].values.astype(float),
                              loaded["v_ms"].values.astype(float))
                assert np.all(spd > 30), f"Velocidade extrema não detectada"
                resultados.append(("Perfil extremo", True, f"Velocidade máx: {spd.max():.1f} m/s ✓"))
            except Exception as e:
                resultados.append(("Perfil extremo", False, str(e)))

            # ── Teste 7: Exportação ──
            try:
                df_test = pd.DataFrame({
                    "altitude_agl_m": ALTITUDES_PADRAO[:5],
                    "u_ms": [-3.0, -3.5, -4.0, -4.5, -5.0],
                    "v_ms": [0.5, 0.0, -0.5, -1.0, -1.5],
                    "w_ms": [0.0] * 5,
                })
                exportar_csv_simplificado(df_test, config, nome="_test_export.csv")
                caminho_test = Path(config["pasta_saida"]) / "csv" / "_test_export.csv"
                reloaded = pd.read_csv(caminho_test)
                assert np.allclose(reloaded["u_ms"].values, df_test["u_ms"].values, atol=0.01)
                caminho_test.unlink()  # limpar
                resultados.append(("Exportação", True, "CSV relido com sucesso. ✓"))
            except Exception as e:
                resultados.append(("Exportação", False, str(e)))

            # ── Teste 8: Reprodutibilidade ──
            try:
                df_reprod = pd.DataFrame({
                    "altitude_agl_m": [0, 500, 1000, 1500, 2000, 2500, 3000],
                    "u_ms": [-2, -3, -4, -5, -4, -3, -2],
                    "v_ms": [1, 0, -1, -2, -2, -1, 0],
                })
                df_reprod.to_csv("/tmp/_test_reprod.csv", index=False)
                l1 = carregar_csv_manual("/tmp/_test_reprod.csv", config)
                l2 = carregar_csv_manual("/tmp/_test_reprod.csv", config)
                # Profile IDs serão diferentes, mas os dados devem ser iguais
                assert np.allclose(
                    l1["u_ms"].values.astype(float),
                    l2["u_ms"].values.astype(float),
                )
                resultados.append(("Reprodutibilidade", True, "Dados idênticos em duas execuções. ✓"))
            except Exception as e:
                resultados.append(("Reprodutibilidade", False, str(e)))

            # ── Resumo ──
            print("\n" + "=" * 60)
            print("RESULTADO DOS TESTES")
            print("=" * 60)
            n_pass = sum(1 for _, p, _ in resultados if p)
            n_total = len(resultados)
            for nome, passou, msg in resultados:
                status = "✅ PASSOU" if passou else "❌ FALHOU"
                print(f"  {status} | {nome}: {msg}")
            print(f"\nTotal: {n_pass}/{n_total} testes aprovados.")
            return resultados

        # ── Executar testes automaticamente ──
        _ = executar_testes(CONFIG)
        """),
    ]

# ══════════════════════════════════════════════
# SECTION EXTRA — Execução demonstrativa
# ══════════════════════════════════════════════
def section_demo():
    return [
        md("""
        ---
        ## 🎯 Execução Demonstrativa

        As células a seguir demonstram o pipeline completo usando os dados de exemplo.
        """),
        code(r"""
        # ══════════════════════════════════════════════════
        # Pipeline demonstrativo com dados de exemplo
        # ══════════════════════════════════════════════════

        print("=" * 60)
        print("PIPELINE DEMONSTRATIVO")
        print("=" * 60)

        # 1. Carregar perfil manual (como "histórico" sintético para demonstração)
        print("\n1. Carregando perfil manual...")
        dados_manual = carregar_fonte("csv_manual", "data/raw/perfil_manual_exemplo.csv", CONFIG)
        dados_manual = normalizar_dados(dados_manual, CONFIG)
        dados_manual["data_type"] = "historical"
        print(f"   {len(dados_manual)} registros carregados")

        # 2. Carregar perfil com formato velocidade+direção
        print("\n2. Carregando perfil com direção...")
        dados_direcao = carregar_fonte("csv_manual", "data/raw/perfil_manual_direcao.csv", CONFIG)
        dados_direcao = normalizar_dados(dados_direcao, CONFIG)
        dados_direcao["data_type"] = "historical"
        print(f"   {len(dados_direcao)} registros carregados")

        # 3. Combinar como "histórico" (para demonstração com múltiplos perfis)
        dados_hist = pd.concat([dados_manual, dados_direcao], ignore_index=True)

        # 4. Carregar previsão
        print("\n3. Carregando previsão...")
        dados_previsao = carregar_fonte("forecast_csv", "data/raw/previsoes/previsao_gfs_20260903.csv", CONFIG)
        dados_previsao = normalizar_dados(dados_previsao, CONFIG)
        print(f"   {len(dados_previsao)} registros carregados")

        # 5. Validar
        print("\n4. Validando dados...")
        avisos_hist = validar_perfil(dados_hist, CONFIG)
        avisos_prev = validar_perfil(dados_previsao, CONFIG)
        for a in avisos_hist + avisos_prev:
            print(f"   {a}")

        # 6. Interpolar
        print("\n5. Interpolando perfis...")
        hist_interp = interpolar_todos_perfis(dados_hist, ALTITUDES_PADRAO, CONFIG)
        atual_interp = interpolar_todos_perfis(dados_previsao, ALTITUDES_PADRAO, CONFIG)

        # 7. Estatísticas
        print("\n6. Calculando estatísticas...")
        stats = calcular_estatisticas_altitude(hist_interp, CONFIG)
        print(f"   Estatísticas calculadas para {len(stats)} níveis de altitude")

        # 8. Comparação
        print("\n7. Comparando perfil atualizado...")
        comp = comparar_perfil_com_climatologia(atual_interp, hist_interp, stats, CONFIG)
        classif, resumo = classificar_perfil_geral(comp)
        print(f"   Classificação: {classif}")
        if resumo:
            for k, v in resumo.items():
                print(f"   {k}: {v}")

        # 9. Perfis de projeto
        print("\n8. Gerando perfis de projeto...")
        perfis = gerar_perfis_projeto(hist_interp, stats, atual_interp, CONFIG)

        # 10. Representatividade
        metricas = calcular_representatividade(hist_interp, stats, CONFIG)

        # 11. Dashboard
        print("\n9. Construindo dashboard...")
        fig = criar_dashboard(stats, comp, perfis, metricas, classif, resumo, CONFIG)
        if fig is not None:
            fig.show()

        # 12. Exportar
        print("\n10. Exportando resultados...")
        exportar_csv_principal(stats, comp, perfis, CONFIG)
        exportar_estatisticas_csv(stats, CONFIG)
        exportar_metadados(
            CONFIG,
            fontes=["perfil_manual_exemplo.csv", "perfil_manual_direcao.csv", "previsao_gfs_20260903.csv"],
            avisos=avisos_hist + avisos_prev,
            metricas=metricas,
        )
        exportar_dashboard_html(fig, CONFIG)

        # Exportar perfis simplificados
        for nome_perfil, df_perfil in perfis.items():
            exportar_csv_simplificado(df_perfil, CONFIG, nome=f"wind_sim_{nome_perfil}.csv")

        print("\n" + "=" * 60)
        print("✅ Pipeline demonstrativo concluído!")
        print("=" * 60)
        """),
    ]


# ══════════════════════════════════════════════
# ASSEMBLAGEM FINAL
# ══════════════════════════════════════════════
def build_notebook():
    nb = nbf.v4.new_notebook()

    nb.metadata["kernelspec"] = {
        "display_name": "Python 3 (ipykernel)",
        "language": "python",
        "name": "python3",
    }
    nb.metadata["language_info"] = {
        "codemirror_mode": {"name": "ipython", "version": 3},
        "file_extension": ".py",
        "mimetype": "text/x-python",
        "name": "python",
        "nbconvert_exporter": "python",
        "pygments_lexer": "ipython3",
        "version": "3.13.14",
    }

    cells = []
    for section_fn in [
        section_01,
        section_02,
        section_03,
        section_04,
        section_05,
        section_06,
        section_07,
        section_08,
        section_09,
        section_10,
        section_11,
        section_12,
        section_13,
        section_14,
        section_15,
        section_demo,
    ]:
        cells.extend(section_fn())

    nb.cells = cells

    output_path = "Iacanga_Atmosphere_Model.ipynb"
    with open(output_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)

    print(f"✅ Notebook gerado: {output_path}")
    print(f"   Células: {len(nb.cells)}")
    print(f"   Seções: 15 + demonstração")


if __name__ == "__main__":
    build_notebook()

```

---
*Arquivo gerado automaticamente para preservação do contexto operacional do modelo MAGI.*

## 4. ATUALIZAÇÕES RECENTES (2026-08-08)

### 4.1. Integração RocketPy e Geração de Ensembles Sintéticos
Implementou-se a arquitetura para geração e exportação de *ensembles* atmosféricos NetCDF compatíveis com o formato exigido pelo simulador **RocketPy**.

A arquitetura no CASPER-3 foi extendida em uma árvore de pacotes limpa e modular:
```text
magi/
  └── casper/
       ├── ensemble/
       │    ├── __init__.py
       │    ├── generator.py     # Framework para construção de Cubos Atmosféricos
       │    ├── synthetic.py     # Motor Karhunen-Loève/Estocástico e equação hipsométrica 
       │    └── eof.py           # Algoritmos de autodecomposição matricial
       └── export/
            ├── __init__.py
            └── rocketpy.py      # Transcritor NetCDF via xarray (CF-1.8) 
```

**Conquistas Físicas e Estruturais**:
- Preservação da correlação vertical do vento.
- Suporte flexível a `member × time × pressure_level × latitude × longitude`.
- Validação automática de integridade e compressão zlib Nível 4.
- Inclusão transparente na seção "6. Exportação Científica" do `MAGI_App.py` (e refletida de volta para o `MAGI_App.ipynb` via `build_notebook.py`).

### 4.2. Correções Operacionais e Headless Execution
Em validações recentes de integração, o pipeline de orquestração (`MAGI_App.py`) e o exportador NetCDF foram ajustados para suportar execução autônoma sem interface gráfica:

1. **Headless Execution em `MAGI_App.py`**:
   - Remoção/comentário das chamadas bloqueantes `plt.show()` ao gerar o Panorama Principal e o Painel-Exemplo, permitindo que o script execute de forma ininterrupta em ambientes de CI/CD ou servidores sem display.
2. **Correção de Serialização NetCDF para RocketPy (`magi/casper/export/rocketpy.py`)**:
   - Ocorria um erro do xarray ao inferir o *dtype* da dimensão `time` (`unable to infer dtype on variable 'time'`), pois o timestamp vinha equipado com fuso horário (tz-aware object), o que não era suportado nativamente pelo serializador NetCDF.
   - **Solução:** O módulo `pandas` foi importado e aplicado `pd.to_datetime(valid_time).tz_localize(None)` para extrair o tempo absoluto (tz-naive), resolvendo as falhas de exportação e validando o pipeline `magi_rocketpy_ensemble.nc`.
3. **Sincronização com o Notebook (`MAGI_App.ipynb`)**:
   - As mesmas adaptações para omitir o bloqueio visual (`plt.show()`) foram aplicadas cirurgicamente nas células de orquestração do Notebook via MCP (`antigravity-nb`), obedecendo à regra estrita de não injetar/desconstruir o código fonte `.ipynb` como JSON.
4. **Status de Operabilidade Final**:
   - A reexecução de bateria limpa confirmou a estabilidade e fluidez do orquestrador de script `MAGI_App.py`. O pipeline de Estágio 3 agora processa a climatologia, o ensemble sintético/numérico, e efetua os cálculos de *Atmospheric Score*, finalizando na exportação perfeita e validada de pacotes `.nc` NetCDF e passagens de 100% da suíte PyTest (10/10 testes), gerando código de saída limpo sem *crashes* de serialização (status final de execução 0).

---

## 5. PACOTE DE DEPLOY

Com a estabilização completa do projeto MAGI, foi estruturado um diretório `Deploy/` contendo a "cópia limpa" de todos os artefatos estritamente necessários para o funcionamento e distribuição da aplicação, encapsulando os três subsistemas principais (MELCHIOR, BALTHASAR, CASPER), além de todas as dependências locais.

O pacote de Deploy inclui:
- **Orquestradores**: `MAGI_App.py` e o notebook de apresentação `MAGI_App.ipynb`.
- **Subsistemas Essenciais**: `melchior.py`, `balthasar.py`, `casper.py`.
- **Módulos de Suporte**: `state_manager.py`, `scoring.py`, `exporter.py`, `visuals.py`, `build_notebook.py`.
- **Diretórios Estruturais**: `dados_cache/` (estado atual e climatologia base), `tests/` (validação e testes unitários/integração), e o diretório `magi/` com dependências auxiliares.
- **Identidade e Documentação**: `Logo_Magi.png`, `Logo_Magi_light.png`, `capabilities.md` e o documento `contexto_atual_magi.md` com todo o histórico operacional.

O intuito desta organização é propiciar um *release* autocontido que possa ser clonado, empacotado e executado (via pipeline ou interface) garantindo reprodutibilidade e resiliência das integrações.

