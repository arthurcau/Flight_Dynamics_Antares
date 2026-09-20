"""Atmospheric interpolation and moist-air physics in SI units.

Wind vectors use ENU; reported directions identify where wind comes from.
Humidity q is water mass / total moist-air mass, not the mixing ratio r.
"""

import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator

try:
    from MAGI.covariance import covariance_factor
except ImportError:
    from covariance import covariance_factor


class MagiSchema:
    COLUMNS = [
        "valid_time_utc", "generation_time_utc", "altitude_agl_m", "altitude_msl_m",
        "u_east_mps", "v_north_mps", "w_up_mps", "wind_speed_mps",
        "wind_direction_from_deg", "pressure_pa", "temperature_k",
        "relative_humidity_pct", "specific_humidity_kg_kg", "density_kgm3",
        "wind_shear_s_1", "data_source", "data_type", "quality_flag", "model_name",
        "ensemble_member", "generation_method", "ensemble_source",
    ]
    REQUIRED_PHYSICS = ["altitude_agl_m", "u_east_mps", "v_north_mps",
                        "pressure_pa", "temperature_k", "relative_humidity_pct"]

    @staticmethod
    def create_empty(num_rows=0):
        return pd.DataFrame(index=range(num_rows), columns=MagiSchema.COLUMNS)

    @staticmethod
    def validate(df, *, allow_empty=False):
        missing = set(MagiSchema.COLUMNS) - set(df.columns)
        if missing:
            raise ValueError(f"Missing schema columns: {sorted(missing)}")
        if df.empty:
            if allow_empty:
                return True
            raise ValueError("Atmospheric profile is empty")
        values = df[MagiSchema.REQUIRED_PHYSICS].to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise ValueError("Atmospheric profile contains missing or non-finite physical values")
        if np.any(df.pressure_pa <= 0) or np.any(df.temperature_k <= 0):
            raise ValueError("Pressure and absolute temperature must be positive")
        if np.any((df.relative_humidity_pct < 0) | (df.relative_humidity_pct > 100)):
            raise ValueError("Relative humidity must be in [0, 100]")
        return True


class CasperPhysics:
    R_AIR = 287.05  # J/(kg K), dry air
    G = 9.80665     # m/s², standard gravity
    EPSILON = 0.622 # molecular-mass ratio water vapour / dry air

    @staticmethod
    def calc_vapor_pressure(temp_k):
        """Saturation vapour pressure over liquid water, in hPa (Bolton form)."""
        temp_c = np.asarray(temp_k) - 273.15
        return 6.112 * np.exp(17.67 * temp_c / (temp_c + 243.5))

    @staticmethod
    def calc_specific_humidity(pressure_pa, temp_k, rh_pct):
        p = np.asarray(pressure_pa)
        rh = np.asarray(rh_pct)
        e = rh / 100 * CasperPhysics.calc_vapor_pressure(temp_k) * 100  # hPa -> Pa
        if np.any(p <= 0) or np.any((rh < 0) | (rh > 100)) or np.any(e >= p):
            raise ValueError("Invalid pressure / relative humidity / vapour pressure")
        epsilon = CasperPhysics.EPSILON
        return epsilon * e / (p - (1 - epsilon) * e)

    @staticmethod
    def calc_rh_from_specific_humidity(pressure_pa, temp_k, q):
        q = np.asarray(q)
        if np.any((q < 0) | (q >= 1)):
            raise ValueError("Specific humidity must be in [0, 1)")
        epsilon = CasperPhysics.EPSILON
        e = q * np.asarray(pressure_pa) / (epsilon + (1 - epsilon) * q)
        # Do not clip supersaturation: callers must reject or explicitly model it.
        return 100 * e / (100 * CasperPhysics.calc_vapor_pressure(temp_k))

    @staticmethod
    def virtual_temperature(temp_k, q):
        return np.asarray(temp_k) * (1 + (1 / CasperPhysics.EPSILON - 1) * np.asarray(q))

    @staticmethod
    def calc_density(pressure_pa, temp_k, rh_pct):
        q = CasperPhysics.calc_specific_humidity(pressure_pa, temp_k, rh_pct)
        return np.asarray(pressure_pa) / (CasperPhysics.R_AIR * CasperPhysics.virtual_temperature(temp_k, q))

    @staticmethod
    def speed_dir_to_uv(speed, direction_from):
        angle = np.radians(direction_from)
        return -speed * np.sin(angle), -speed * np.cos(angle)

    @staticmethod
    def uv_to_speed_dir(u, v):
        return np.hypot(u, v), (np.degrees(np.arctan2(-u, -v)) + 360) % 360

    @staticmethod
    def calc_shear(u, v, z):
        if len(z) < 2:
            return np.full_like(z, np.nan, dtype=float)
        return np.hypot(np.gradient(u, z), np.gradient(v, z))

    @staticmethod
    def hydrostatic_diagnostic(pressure_pa, density_kgm3, z_m):
        """Dimensionless residual at each level; unavailable derivatives are NaN."""
        if len(z_m) < 2:
            return np.full_like(z_m, np.nan, dtype=float)
        rho_g = np.asarray(density_kgm3) * CasperPhysics.G
        return np.abs(np.gradient(pressure_pa, z_m) + rho_g) / rho_g


class CasperProcessor:
    SURFACE_ROUGHNESS = {"OPEN_TERRAIN": 0.03, "VEGETATED_TERRAIN": 0.10, "ROUGH_RURAL": 0.30}
    HYDROSTATIC_WARNING_THRESHOLD = 0.08
    HYDROSTATIC_FAILURE_THRESHOLD = 0.20
    HYDROSTATIC_CONSECUTIVE_LEVELS = 3

    def __init__(self, elevation_msl=450, surface_scenario="OPEN_TERRAIN"):
        if surface_scenario not in self.SURFACE_ROUGHNESS and surface_scenario is not None:
            raise ValueError(f"Unknown surface scenario: {surface_scenario}")
        self.elevation_msl = elevation_msl
        self.surface_scenario = surface_scenario
        self.z0 = self.SURFACE_ROUGHNESS.get(surface_scenario)

    def interpolate_profile(self, df_raw, altitude_grid):
        """PCHIP on a strictly increasing AGL grid, with no upper extrapolation.

        Below the first observation, an explicitly selected surface scenario
        uses neutral log wind, isothermal constant-q air and hydrostatic pressure.
        These levels retain SYNTHETIC_SURFACE_LAYER flags. Set surface_scenario
        to None to prohibit this approximation.
        """
        z = np.asarray(altitude_grid, dtype=float)
        if z.ndim != 1 or len(z) < 2 or not np.isfinite(z).all() or np.any(np.diff(z) <= 0):
            raise ValueError("Altitude grid must contain at least two finite increasing levels")
        if df_raw.empty:
            return MagiSchema.create_empty()
        raw = df_raw.sort_values("altitude_agl_m").copy()
        values = raw[MagiSchema.REQUIRED_PHYSICS].to_numpy(dtype=float)
        if not np.isfinite(values).all() or len(raw) < 2:
            raise ValueError("Raw profile requires at least two complete finite levels")
        z_orig = raw.altitude_agl_m.to_numpy(dtype=float)
        if np.any(np.diff(z_orig) <= 0):
            raise ValueError("Duplicate profile altitudes are ambiguous")
        p_orig = raw.pressure_pa.to_numpy(dtype=float)
        if np.any(p_orig <= 0) or np.any(np.diff(p_orig) >= 0):
            raise ValueError("Pressure must be positive and decrease with altitude")
        q_orig = CasperPhysics.calc_specific_humidity(p_orig, raw.temperature_k, raw.relative_humidity_pct)
        if np.any(raw.temperature_k <= 0):
            raise ValueError("Absolute temperature must be positive")
        grid = MagiSchema.create_empty(len(z))
        grid["altitude_agl_m"], grid["altitude_msl_m"] = z, z + self.elevation_msl
        for col in ("u_east_mps", "v_north_mps", "temperature_k", "relative_humidity_pct"):
            grid[col] = PchipInterpolator(z_orig, raw[col], extrapolate=False)(z)
        grid["pressure_pa"] = np.exp(PchipInterpolator(z_orig, np.log(p_orig), extrapolate=False)(z))
        below = z < z_orig[0]
        if self.z0 is not None and below.any():
            if z_orig[0] <= self.z0 or np.any(z[below] < 0):
                raise ValueError("Surface log-law requires nonnegative AGL and reference altitude above roughness")
            scale = np.log(np.maximum(z[below], self.z0) / self.z0) / np.log(z_orig[0] / self.z0)
            for col in ("u_east_mps", "v_north_mps"):
                grid.loc[below, col] = raw[col].iloc[0] * scale
            t_ref, q_ref = raw.temperature_k.iloc[0], q_orig[0]
            tv_ref = CasperPhysics.virtual_temperature(t_ref, q_ref)
            p_surface = p_orig[0] * np.exp(-CasperPhysics.G * (z[below] - z_orig[0]) / (CasperPhysics.R_AIR * tv_ref))
            grid.loc[below, "temperature_k"] = t_ref
            grid.loc[below, "pressure_pa"] = p_surface
            grid.loc[below, "relative_humidity_pct"] = CasperPhysics.calc_rh_from_specific_humidity(p_surface, t_ref, q_ref)
        self._derive(grid)
        for col in ("valid_time_utc", "generation_time_utc", "data_source", "data_type", "model_name",
                    "ensemble_member", "ensemble_source", "latitude", "longitude", "retrieved_at_utc"):
            if col in raw:
                if raw[col].nunique(dropna=False) != 1:
                    raise ValueError(f"A single vertical profile must have one {col}")
                grid[col] = raw[col].iloc[0]
        grid["generation_method"] = "pchip_no_upper_extrapolation"
        grid["quality_flag"] = "VALID"
        grid.loc[below, "quality_flag"] = "SYNTHETIC_SURFACE_LAYER" if self.z0 is not None else "OUT_OF_VERTICAL_RANGE"
        grid.loc[z > z_orig[-1], "quality_flag"] = "OUT_OF_VERTICAL_RANGE"
        valid = np.isfinite(grid[MagiSchema.REQUIRED_PHYSICS].to_numpy(dtype=float)).all(axis=1)
        eps = np.full(len(z), np.nan)
        if valid.sum() >= 2:
            eps[valid] = CasperPhysics.hydrostatic_diagnostic(grid.pressure_pa[valid], grid.density_kgm3[valid], z[valid])
        grid["hydrostatic_residual"] = eps
        failures = eps > self.HYDROSTATIC_FAILURE_THRESHOLD
        consecutive = np.convolve(failures.astype(int), np.ones(self.HYDROSTATIC_CONSECUTIVE_LEVELS, dtype=int), mode="valid")
        if len(z) >= self.HYDROSTATIC_CONSECUTIVE_LEVELS and np.any(consecutive == self.HYDROSTATIC_CONSECUTIVE_LEVELS):
            grid.loc[valid, "quality_flag"] = "HYDROSTATIC_FAILURE"
        else:
            grid.loc[(eps > self.HYDROSTATIC_WARNING_THRESHOLD) & (grid.quality_flag == "VALID"), "quality_flag"] = "HYDROSTATIC_WARNING"
        grid.attrs = dict(raw.attrs)
        grid.attrs["surface_scenario"] = self.surface_scenario or "none"
        return grid

    @staticmethod
    def _derive(grid):
        grid["wind_speed_mps"], grid["wind_direction_from_deg"] = CasperPhysics.uv_to_speed_dir(grid.u_east_mps, grid.v_north_mps)
        grid["specific_humidity_kg_kg"] = CasperPhysics.calc_specific_humidity(grid.pressure_pa, grid.temperature_k, grid.relative_humidity_pct)
        grid["density_kgm3"] = CasperPhysics.calc_density(grid.pressure_pa, grid.temperature_k, grid.relative_humidity_pct)
        valid = np.isfinite(grid.u_east_mps) & np.isfinite(grid.v_north_mps)
        grid["wind_shear_s_1"] = np.nan
        if valid.sum() >= 2:
            grid.loc[valid, "wind_shear_s_1"] = CasperPhysics.calc_shear(grid.u_east_mps[valid], grid.v_north_mps[valid], grid.altitude_agl_m[valid])

    def generate_synthetic_ensemble(self, df_nominal, cov_matrix, altitude_grid, num_members=100, *, seed=None, rng=None):
        """Gaussian historical-variability scenarios, conditioned on valid moist air.

        Invalid samples are rejected, never clipped. This conditional ensemble
        does not retain exactly the input covariance and is not forecast-error
        calibration. Pressure is integrated hydrostatically from the base level.
        """
        MagiSchema.validate(df_nominal)
        z = np.asarray(altitude_grid, dtype=float)
        nz = len(z)
        if not np.array_equal(df_nominal.altitude_agl_m.to_numpy(), z) or np.any(np.diff(z) <= 0):
            raise ValueError("Nominal profile and covariance grid must match exactly")
        if not isinstance(num_members, int) or num_members < 1:
            raise ValueError("num_members must be a positive integer")
        if rng is not None and seed is not None:
            raise ValueError("Pass seed or rng, not both")
        rng = rng if rng is not None else np.random.default_rng(seed)
        factor = covariance_factor(cov_matrix, 4 * nz)
        x_nom = np.concatenate([df_nominal[col].to_numpy(dtype=float) for col in
                                ("u_east_mps", "v_north_mps", "temperature_k", "specific_humidity_kg_kg")])
        members = []
        batch_size = max(num_members * 2, 50)
        attempts = 0
        max_attempts = 100 * num_members

        p0 = float(df_nominal.pressure_pa.iloc[0])
        dz = np.diff(z)

        while len(members) < num_members and attempts < max_attempts:
            cur_batch = min(batch_size, max_attempts - attempts)
            noise_batch = rng.standard_normal((4 * nz, cur_batch))
            pert_batch = factor @ noise_batch
            attempts += cur_batch

            x_batch = x_nom[:, None] + pert_batch
            u_batch = x_batch[0:nz, :]
            v_batch = x_batch[nz:2 * nz, :]
            temp_batch = x_batch[2 * nz:3 * nz, :]
            q_batch = x_batch[3 * nz:4 * nz, :]

            # Filter valid moist-air state (T > 0 and 0 <= q < 1)
            valid_mask = np.all(temp_batch > 0, axis=0) & np.all((q_batch >= 0) & (q_batch < 1), axis=0)
            valid_indices = np.where(valid_mask)[0]
            if len(valid_indices) == 0:
                continue

            t_sub = temp_batch[:, valid_indices]
            q_sub = q_batch[:, valid_indices]
            tv_sub = CasperPhysics.virtual_temperature(t_sub, q_sub)

            # Vectorized trapezoidal hydrostatic integration: d ln(p)/dz = -g/(Rd Tv)
            inv_tv = 1.0 / tv_sub
            increments = (-CasperPhysics.G / CasperPhysics.R_AIR) * dz[:, None] * (inv_tv[1:, :] + inv_tv[:-1, :]) / 2.0
            pressures = np.empty((nz, len(valid_indices)), dtype=float)
            pressures[0, :] = p0
            pressures[1:, :] = p0 * np.exp(np.cumsum(increments, axis=0))

            rh_sub = CasperPhysics.calc_rh_from_specific_humidity(pressures, t_sub, q_sub)
            valid_rh = np.all(np.isfinite(rh_sub) & (rh_sub >= 0) & (rh_sub <= 100), axis=0)
            accepted = np.where(valid_rh)[0]

            for idx in accepted:
                b = valid_indices[idx]
                u = u_batch[:, b]
                v = v_batch[:, b]
                temp = t_sub[:, idx]
                pressure = pressures[:, idx]
                rh = rh_sub[:, idx]

                member = df_nominal.copy()
                for col, values in (("u_east_mps", u), ("v_north_mps", v), ("temperature_k", temp),
                                    ("pressure_pa", pressure), ("relative_humidity_pct", rh)):
                    member[col] = values
                self._derive(member)
                member["data_type"] = "synthetic_ensemble"
                member["generation_method"] = "historical_covariance_gaussian_rejection_hydrostatic"
                member["ensemble_source"] = "synthetic_from_deterministic"
                member["ensemble_member"] = f"synthetic_{len(members) + 1}"
                member["quality_flag"] = "SYNTHETIC_MODEL"
                member.attrs.update({"seed": seed if seed is not None else "external_rng", "draws_so_far": attempts})
                members.append(member)
                if len(members) == num_members:
                    return members

        if len(members) < num_members:
            raise ValueError("Synthetic ensemble rejected too many unphysical samples; review covariance/model")
        return members


class CasperVisuals:
    @staticmethod
    def plot_painel(df_atual, df_stats):
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 4, figsize=(16, 6))
        d = df_atual[df_atual.quality_flag != "OUT_OF_VERTICAL_RANGE"]
        for ax, col, title in zip(axes, ("wind_speed_mps", "u_east_mps", "wind_shear_s_1", "density_kgm3"),
                                  ("Wind speed (m/s)", "Wind ENU (m/s)", "Shear (1/s)", "Density (kg/m³)")):
            ax.plot(d[col], d.altitude_agl_m, label=col)
            ax.set(title=title, ylabel="Altitude AGL (m)")
        axes[1].plot(d.v_north_mps, d.altitude_agl_m, label="v_north_mps")
        axes[1].legend()
        fig.tight_layout()
        return fig
