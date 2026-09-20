import os
import pandas as pd
import numpy as np
from sklearn.covariance import LedoitWolf

try:
    from MAGI.casper import MagiSchema, CasperPhysics
except ImportError:
    from casper import MagiSchema, CasperPhysics

class Melchior:
    def __init__(self, cache_dir="dados_cache", elevation_msl=450):
        if not os.path.isabs(cache_dir):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.cache_dir = os.path.join(base_dir, cache_dir)
        else:
            self.cache_dir = cache_dir
        self.elevation_msl = elevation_msl
        os.makedirs(self.cache_dir, exist_ok=True)
        print(f"MELCHIOR: Inicializando com diretório de cache '{self.cache_dir}' e elevação MSL={self.elevation_msl}m")

    def _generate_synthetic_historical_cache(self, output_path):
        """Generates a representative multi-profile historical climatological dataset for Iacanga (MSL 450m)."""
        print(f"MELCHIOR: Gerando climatologia sintética representativa em '{output_path}'...")
        dates = pd.date_range("2024-01-01 12:00:00", periods=30, freq="7D", tz="UTC")
        alts_msl = np.arange(450, 7001, 250)  # 450 to 7000 m MSL
        records = []

        # Physical constants
        L = 0.0065  # K/m (ISA lapse rate)
        g = 9.80665
        R = 287.05

        np.random.seed(42)
        for i, dt in enumerate(dates):
            # Day-to-day weather variability
            is_severe = (i == 14)  # 15th profile represents a severe front/storm event
            t0 = 23.0 + np.random.normal(0, 4.0) + (5.0 if is_severe else 0.0)
            p0 = (960.0 + np.random.normal(0, 3.0) - (8.0 if is_severe else 0.0)) * 100.0  # Pa
            rh0 = 85.0 if is_severe else float(np.clip(60.0 + np.random.normal(0, 12.0), 35.0, 95.0))

            base_dir = float((120.0 + np.random.normal(0, 25.0)) % 360)  # prevailing ESE
            v_sfc = 12.0 if is_severe else float(np.clip(4.0 + np.random.normal(0, 1.5), 1.5, 9.0))
            v_jet = 35.0 if is_severe else float(np.clip(18.0 + np.random.normal(0, 4.0), 10.0, 30.0))

            for z_msl in alts_msl:
                z_agl = z_msl - self.elevation_msl
                # Temperature (ISA lapse rate with synoptic shift)
                t_k = (t0 + 273.15) - L * z_agl
                t_c = t_k - 273.15

                # Pressure (Hypsometric formula)
                p_pa = p0 * (1.0 - (L * z_agl) / (t0 + 273.15)) ** (g / (R * L))
                p_hpa = p_pa / 100.0

                # Humidity
                rh = float(np.clip(rh0 * np.exp(-z_agl / 4000.0) + np.random.normal(0, 2.0), 15.0, 98.0))

                # Wind speed and direction
                # Surface boundary layer logarithmic + tropospheric increase
                z_rough = max(z_agl, 10.0)
                v_bl = v_sfc * (np.log(z_rough / 0.03) / np.log(10.0 / 0.03))
                v_trop = v_jet * (z_agl / 6550.0) ** 1.2
                v_spd = float(np.clip(v_bl * 0.4 + v_trop * 0.6 + np.random.normal(0, 0.5), 0.5, 45.0))

                # Wind direction veering/backing with height towards WNW jet
                dir_deg = float((base_dir + (z_agl / 6550.0) * 140.0 + np.random.normal(0, 5.0)) % 360)

                records.append({
                    "timestamp": dt.isoformat(),
                    "altitude_msl": z_msl,
                    "velocidade": round(v_spd, 2),
                    "direcao": round(dir_deg, 1),
                    "temperatura": round(t_c, 2),
                    "pressao": round(p_hpa, 2),
                    "umidade": round(rh, 1)
                })

        df_gen = pd.DataFrame(records)
        df_gen.to_csv(output_path, index=False)
        print(f"MELCHIOR: Climatologia sintética salva com {len(df_gen)} registros ({len(dates)} perfis).")
        return df_gen

    def fetch_historical_data(self):
        print("MELCHIOR: Buscando dados históricos do CSV de contingência...")
        legacy_path = os.path.join(self.cache_dir, "historico_openmeteo.csv")
        if not os.path.exists(legacy_path):
            print("MELCHIOR: Aviso - CSV histórico não encontrado! Gerando contingência climatológica sintética...")
            self._generate_synthetic_historical_cache(legacy_path)

        old_df = pd.read_csv(legacy_path)

        df = MagiSchema.create_empty(len(old_df))
        time_col = 'timestamp' if 'timestamp' in old_df.columns else 'perfil_id'
        df['valid_time_utc'] = pd.to_datetime(old_df[time_col], utc=True)
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
        df['relative_humidity_pct'] = old_df.get('umidade', np.nan)

        # specific humidity
        df['specific_humidity_kg_kg'] = CasperPhysics.calc_specific_humidity(
            df['pressure_pa'], df['temperature_k'], df['relative_humidity_pct']
        )

        # density
        df['density_kgm3'] = CasperPhysics.calc_density(df['pressure_pa'], df['temperature_k'], df['relative_humidity_pct'])

        df['data_source'] = "legacy_csv_contingency"
        df['data_type'] = "historical"
        df['quality_flag'] = "MIGRATED_STAGE2"
        df['model_name'] = "legacy_csv_model_unverified"

        df = df.dropna(subset=['wind_speed_mps', 'temperature_k'])

        def calc_shear(group):
            group = group.sort_values('altitude_agl_m').drop_duplicates(subset=['altitude_agl_m'])
            z = group['altitude_agl_m'].values
            if len(z) < 2:
                group['wind_shear_s_1'] = 0.0
                return group
            group['wind_shear_s_1'] = CasperPhysics.calc_shear(group['u_east_mps'].values, group['v_north_mps'].values, z)
            return group

        res = []
        for name, group in df.groupby('valid_time_utc'):
            res.append(calc_shear(group.copy()))
        df = pd.concat(res, ignore_index=True) if res else df
        return df

    def select_worst_day(self, df_hist=None):
        """
        Analisa os perfis históricos e seleciona o pior dia — aquele com a combinação
        mais severa de ventos fortes, alta umidade (indicativo de chuva/nuvens) e cisalhamento.

        Retorna:
            df_worst: DataFrame no esquema MAGI com o perfil do pior dia
            worst_info: dict com metadados do dia selecionado (timestamp, scores)
        """
        print("MELCHIOR: Selecionando o pior dia histórico (vento forte + chuva + nuvens)...")

        if df_hist is None or df_hist.empty:
            df_hist = self.fetch_historical_data()

        if df_hist.empty:
            print("MELCHIOR: Aviso — Sem dados históricos para selecionar pior dia.")
            return MagiSchema.create_empty(), {}

        # Calcular score de severidade por perfil (válido_time_utc)
        severity_scores = {}
        for time_id, group in df_hist.groupby('valid_time_utc'):
            # Vento máximo na coluna
            max_wind = group['wind_speed_mps'].max() if 'wind_speed_mps' in group.columns else 0
            # Umidade máxima (indicativo de precipitação/nuvens)
            max_humidity = group['relative_humidity_pct'].max() if 'relative_humidity_pct' in group.columns else 0
            # Cisalhamento máximo
            max_shear = group['wind_shear_s_1'].max() if 'wind_shear_s_1' in group.columns else 0
            # Vento na superfície (10m)
            sfc_wind = group.loc[group['altitude_agl_m'].idxmin(), 'wind_speed_mps'] if len(group) > 0 else 0

            # Score composto: pesos que favorecem ventos fortes + umidade alta + cisalhamento
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

        return df_worst, worst_info

    @staticmethod
    def _aligned_profiles(df_hist, altitude_grid):
        """Use one common grid for statistics and covariance; never extrapolate."""
        grid = np.asarray(altitude_grid, dtype=float)
        if grid.ndim != 1 or len(grid) == 0 or not np.isfinite(grid).all() or np.any(np.diff(grid) <= 0):
            raise ValueError("Historical grid must contain finite increasing levels")
        profiles = []
        for timestamp, raw in df_hist.groupby('valid_time_utc'):
            raw = raw.sort_values('altitude_agl_m')
            z = raw.altitude_agl_m.to_numpy(dtype=float)
            if len(z) < 2 or not np.isfinite(z).all() or np.any(np.diff(z) <= 0):
                continue
            profile = pd.DataFrame({'altitude_agl_m': grid})
            for col in ('u_east_mps', 'v_north_mps', 'temperature_k', 'pressure_pa',
                        'relative_humidity_pct', 'specific_humidity_kg_kg'):
                if col in raw:
                    profile[col] = np.interp(grid, z, raw[col].to_numpy(dtype=float), left=np.nan, right=np.nan)
            if {'u_east_mps', 'v_north_mps'} <= set(profile):
                profile['wind_speed_mps'], profile['wind_direction_from_deg'] = CasperPhysics.uv_to_speed_dir(profile.u_east_mps, profile.v_north_mps)
                profile['wind_shear_s_1'] = CasperPhysics.calc_shear(profile.u_east_mps, profile.v_north_mps, grid)
            if {'pressure_pa', 'temperature_k', 'relative_humidity_pct'} <= set(profile):
                profile['density_kgm3'] = CasperPhysics.calc_density(profile.pressure_pa, profile.temperature_k, profile.relative_humidity_pct)
                if 'specific_humidity_kg_kg' not in profile:
                    profile['specific_humidity_kg_kg'] = CasperPhysics.calc_specific_humidity(profile.pressure_pa, profile.temperature_k, profile.relative_humidity_pct)
            profiles.append(profile)
        return profiles

    def calc_stats_hist(self, df_hist, altitude_grid=None):
        if df_hist.empty or altitude_grid is None:
            return pd.DataFrame()
        profiles = self._aligned_profiles(df_hist, altitude_grid)
        if not profiles:
            return pd.DataFrame()
        rows = []
        quantiles = [5, 10, 25, 75, 90, 95, 99]
        for altitude, group in pd.concat(profiles).groupby('altitude_agl_m'):
            row = {'altitude_agl_m': altitude}
            for variable in ('u_east_mps', 'v_north_mps', 'temperature_k', 'pressure_pa',
                             'relative_humidity_pct', 'density_kgm3', 'wind_speed_mps', 'wind_shear_s_1'):
                if variable not in group:
                    continue
                values = group[variable].to_numpy(dtype=float)
                values = values[np.isfinite(values)]
                row[f'{variable}_count'] = len(values)
                row[f'{variable}_mean'] = np.mean(values) if len(values) else np.nan
                row[f'{variable}_median'] = np.median(values) if len(values) else np.nan
                percentiles = np.percentile(values, quantiles) if len(values) else np.full(len(quantiles), np.nan)
                for percentile, value in zip(quantiles, percentiles):
                    row[f'{variable}_p{percentile}'] = value
            if 'u_east_mps_mean' in row and 'v_north_mps_mean' in row:
                resultant, direction = CasperPhysics.uv_to_speed_dir(row['u_east_mps_mean'], row['v_north_mps_mean'])
                row['wind_resultant_mps'] = resultant
                row['wind_dir_mean'] = direction if resultant > 0 else np.nan
            rows.append(row)
        return pd.DataFrame(rows)

    def calculate_multivariate_covariance(self, df_hist, altitude_grid):
        """Historical variability of [u(z), v(z), T(z), q(z)] in SI.

        Shrink the dimensionless correlation matrix, then restore each column's
        empirical standard deviation. This preserves units and zero-variance
        quantities. It does not turn climatological variability into forecast
        error statistics. Only complete profiles spanning the grid contribute.
        """
        variables = ('u_east_mps', 'v_north_mps', 'temperature_k', 'specific_humidity_kg_kg')
        vectors = []
        for profile in self._aligned_profiles(df_hist, altitude_grid):
            if not set(variables) <= set(profile):
                continue
            vector = np.concatenate([profile[col].to_numpy(dtype=float) for col in variables])
            if np.isfinite(vector).all():
                vectors.append(vector)
        if len(vectors) < 2:
            return None, None
        samples = np.asarray(vectors)
        mean = samples.mean(axis=0)
        scale = samples.std(axis=0, ddof=0)
        active = scale > 0
        covariance = np.zeros((len(mean), len(mean)))
        if active.any():
            standardized = (samples[:, active] - mean[active]) / scale[active]
            estimate = LedoitWolf(store_precision=False).fit(standardized).covariance_
            covariance[np.ix_(active, active)] = estimate * np.outer(scale[active], scale[active])
        return mean, covariance

class MelchiorVisuals:
    @staticmethod
    def plot_magnitude_vento(df_stats):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(df_stats['wind_speed_mps_mean'], df_stats['altitude_agl_m'], label='Historical Mean')
        ax.fill_betweenx(df_stats['altitude_agl_m'], 
                         df_stats['wind_speed_mps_p10'], 
                         df_stats['wind_speed_mps_p90'], 
                         alpha=0.3, label='10th-90th Percentile')
        ax.set_title("Historical Wind Magnitude")
        ax.legend()
        return fig
