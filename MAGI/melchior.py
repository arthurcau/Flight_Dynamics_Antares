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
        
        # specific humidity
        df['specific_humidity_kg_kg'] = CasperPhysics.calc_specific_humidity(
            df['pressure_pa'], df['temperature_k'], df['relative_humidity_pct']
        )
        
        # density
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
            # Normalização aproximada:
            #   vento: 0-30 m/s → 0-100
            #   umidade: 0-100% → 0-100
            #   cisalhamento: 0-0.05 s⁻¹ → 0-100
            #   vento superfície: 0-15 m/s → 0-100
            score_wind = min(max_wind / 30.0, 1.0) * 100
            score_humidity = min(max_humidity / 100.0, 1.0) * 100
            score_shear = min(max_shear / 0.05, 1.0) * 100
            score_sfc = min(sfc_wind / 15.0, 1.0) * 100

            # Pesos: vento 40%, umidade 25%, cisalhamento 20%, vento_superficie 15%
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

        # Selecionar o pior
        worst_time = max(severity_scores, key=lambda k: severity_scores[k]['composite'])
        worst_info = severity_scores[worst_time]
        worst_info['timestamp'] = worst_time

        print(f"MELCHIOR: Pior dia selecionado — {worst_time}")
        print(f"  Score composto: {worst_info['composite']:.1f}/100")
        print(f"  Vento máx: {worst_info['max_wind_mps']:.1f} m/s | Umidade máx: {worst_info['max_humidity_pct']:.0f}%")
        print(f"  Cisalhamento máx: {worst_info['max_shear_s1']:.4f} s⁻¹ | Vento superfície: {worst_info['sfc_wind_mps']:.1f} m/s")

        df_worst = df_hist[df_hist['valid_time_utc'] == worst_time].copy()

        # Adicionar metadados
        df_worst['data_type'] = 'historical_worst_case'
        df_worst['model_name'] = 'ERA5 Historical Worst Case'

        # Simular condições de precipitação e cobertura de nuvens para o painel exemplo
        # (O dataset histórico não tem essas variáveis, mas inferimos pela umidade alta)
        if 'cloud_cover_pct' not in df_worst.columns:
            # Alta umidade → alta cobertura de nuvens
            df_worst['cloud_cover_pct'] = np.clip(df_worst['relative_humidity_pct'] * 1.2, 0, 100)
        if 'cape_jkg' not in df_worst.columns:
            # Alta umidade + vento forte → CAPE elevado
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
        
        # 1. Convert all profiles to the common vertical grid first
        interpolated_profiles = []
        for time, group in df_hist.groupby('valid_time_utc'):
            group = group.sort_values('altitude_agl_m').drop_duplicates('altitude_agl_m')
            z_orig = group['altitude_agl_m'].values
            
            df_interp = pd.DataFrame({'altitude_agl_m': altitude_grid})
            for col in ['u_east_mps', 'v_north_mps', 'temperature_k', 'pressure_pa', 'relative_humidity_pct']:
                if col in group.columns:
                    f = interp1d(z_orig, group[col].values, bounds_error=False, fill_value=np.nan)
                    df_interp[col] = f(altitude_grid)
            
            # Recalculate physics per profile
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
        
        # Now calculate statistics
        stats = []
        for z, group in df_grid_all.groupby('altitude_agl_m'):
            s = {'altitude_agl_m': z}
            for var in ['u_east_mps', 'v_north_mps', 'temperature_k', 'pressure_pa', 'relative_humidity_pct', 'density_kgm3']:
                if var in group.columns:
                    s[f'{var}_mean'] = group[var].mean()
                    s[f'{var}_median'] = group[var].median()
                    for p in [5, 10, 25, 75, 90, 95]:
                        s[f'{var}_p{p}'] = np.nanpercentile(group[var], p)
            
            # Re-derive speed from mean/percentile of U and V to satisfy V = sqrt(u^2 + v^2)
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
        
        # Validate P05 <= P95
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
        """
        Builds the state vector X = [u, v, T, q]^T per profile and computes the regularized covariance matrix.
        Returns the mean vector and covariance matrix, along with block indices.
        """
        print("MELCHIOR: Construindo vetor de estado multivariado e calculando matriz de covariância (Ledoit-Wolf)...")
        # Ensure we only use profiles that have valid data at all requested grid altitudes.
        # This requires interpolation or binning to the standard grid first.
        # Since df_hist might not be aligned, we align it first.
        # For simplicity, we assume df_hist is already somewhat binned, or we just interpolate historical.
        # In a full implementation, we'd loop over profiles and use CasperProcessor to get them on `altitude_grid`.
        # Here we do a simplified pivot if they are already on the grid, or we just skip and return Identity.
        
        # Pivot the data
        # We need wide format: Rows = timestamps, Cols = (variable, altitude)
        df_grid = df_hist[df_hist['altitude_agl_m'].isin(altitude_grid)]
        
        # Check if we have enough samples
        if df_grid.empty:
            return None, None
            
        pivoted = df_grid.pivot(index='valid_time_utc', columns='altitude_agl_m', 
                                values=['u_east_mps', 'v_north_mps', 'temperature_k', 'specific_humidity_kg_kg'])
                                
        pivoted = pivoted.dropna()
        if len(pivoted) < 2:
            return None, None
            
        # Reorder columns to [u(z1..zn), v(z1..zn), T(z1..zn), q(z1..zn)]
        # pivoted columns are MultiIndex: (variable, altitude)
        ordered_cols = []
        for var in ['u_east_mps', 'v_north_mps', 'temperature_k', 'specific_humidity_kg_kg']:
            for z in altitude_grid:
                if (var, z) in pivoted.columns:
                    ordered_cols.append((var, z))
                    
        X = pivoted[ordered_cols].values
        
        # Compute mean
        mu = np.mean(X, axis=0)
        
        # Compute regularized covariance using Ledoit-Wolf shrinkage
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
