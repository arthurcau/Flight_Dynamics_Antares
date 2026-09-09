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
        # q ≈ 0.622 * e / (p - 0.378 * e) but using simplified form commonly used:
        q = np.where(pressure_hpa > e, (0.622 * e) / (pressure_hpa - e), 0)
        return q

    @staticmethod
    def calc_rh_from_specific_humidity(pressure_pa, temp_k, q):
        es = CasperPhysics.calc_vapor_pressure(temp_k)
        pressure_hpa = pressure_pa / 100.0
        # q = 0.622 * e / (p - e) => e = (q * p) / (0.622 + q)
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
        # Neutral log profile below lowest observation
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
        """
        Interpolates raw profile. Fills out-of-range with NaNs. Uses surface layer below lowest forecast.
        """
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
        
        # Interpolate variables without extrapolation
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
                
        # Interpolate pressure via ln(p)
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


        # Apply surface layer for U and V below lowest forecast
        mask_below = altitude_grid < lowest_z
        if np.any(mask_below):
            u_ref = df_raw['u_east_mps'].iloc[0]
            v_ref = df_raw['v_north_mps'].iloc[0]
            u_s, v_s = self._generate_surface_layer(altitude_grid, lowest_z, u_ref, v_ref)
            df_grid.loc[mask_below, 'u_east_mps'] = u_s[mask_below]
            df_grid.loc[mask_below, 'v_north_mps'] = v_s[mask_below]
            # Keeping T, P, RH constant below lowest layer as approximation or leave NaN
            # For Stage 2, leave them as NaN or fill forward? The roadmap says "Abaixo do menor nível... CASPER poderá utilizar modelo de camada superficial... Acima do último... não deverá haver extrapolação".
            # For T, P, RH we will just backfill to surface for consistency, marked as synthetic.
            df_grid.loc[mask_below, 'temperature_k'] = df_raw['temperature_k'].iloc[0]
            df_grid.loc[mask_below, 'pressure_pa'] = df_raw['pressure_pa'].iloc[0] # A bit inaccurate physically, but keeps profile valid. A proper barometric formula could be used.
            df_grid.loc[mask_below, 'relative_humidity_pct'] = df_raw['relative_humidity_pct'].iloc[0]

        # Re-derive dependents
        df_grid['wind_speed_mps'], df_grid['wind_direction_from_deg'] = CasperPhysics.uv_to_speed_dir(df_grid['u_east_mps'], df_grid['v_north_mps'])
        df_grid['specific_humidity_kg_kg'] = CasperPhysics.calc_specific_humidity(df_grid['pressure_pa'], df_grid['temperature_k'], df_grid['relative_humidity_pct'])
        df_grid['density_kgm3'] = CasperPhysics.calc_density(df_grid['pressure_pa'], df_grid['temperature_k'], df_grid['relative_humidity_pct'])
        df_grid['wind_shear_s_1'] = CasperPhysics.calc_shear(df_grid['u_east_mps'].values, df_grid['v_north_mps'].values, df_grid['altitude_agl_m'].values)
        
        # Diagnostics
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
                
        # Carry over metadata & cloud cover
        meta_cols = ['valid_time_utc', 'generation_time_utc', 'data_source', 'data_type', 'model_name', 'ensemble_member', 'ensemble_source', 'cloud_cover_pct']
        for col in meta_cols:
            if col in df_raw.columns:
                df_grid[col] = df_raw[col].iloc[0]
        if 'cloud_cover_pct' not in df_grid.columns or df_grid['cloud_cover_pct'].isna().all():
            df_grid['cloud_cover_pct'] = np.clip(df_grid['relative_humidity_pct'] * 1.2, 15.0, 95.0)
            
        # Quality flagging
        df_grid['quality_flag'] = 'VALID'
        df_grid.loc[altitude_grid > highest_z, 'quality_flag'] = 'OUT_OF_VERTICAL_RANGE'
        df_grid.loc[mask_below, 'quality_flag'] = 'SYNTHETIC_SURFACE_LAYER'
        
        return df_grid

    def generate_synthetic_ensemble(self, df_nominal, cov_matrix, altitude_grid, num_members=100):
        """
        Generates synthetic ensemble members using Eigendecomposition on the historical covariance.
        cov_matrix should be aligned with the grid variables [u, v, T, q].
        """
        print(f"CASPER: Gerando {num_members} membros de ensemble sintético via autodecomposição da covariância histórica...")
        if cov_matrix is None or len(df_nominal) != len(altitude_grid):
            print("Invalid nominal profile or covariance matrix.")
            return []
            
        n_vars = 4
        nz = len(altitude_grid)
        if cov_matrix.shape[0] != n_vars * nz:
            print("Covariance matrix dimension mismatch.")
            return []
            
        # Eigendecomposition
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
