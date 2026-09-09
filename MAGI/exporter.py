import xarray as xr
import pandas as pd
import numpy as np

class NetCDFExporter:
    @staticmethod
    def export_magi_netcdf(df_nominal, df_ensembles, df_stats, output_path, global_attrs):
        """
        Exports the MAGI data structures to a canonical NetCDF format via xarray.
        """
        if df_nominal is None or df_nominal.empty:
            return
            
        z_grid = df_nominal['altitude_agl_m'].values
        valid_time = pd.to_datetime([df_nominal['valid_time_utc'].iloc[0]]).tz_localize(None)
        
        # Dimensions
        n_alt = len(z_grid)
        n_members = 1 + len(df_ensembles)
        
        # Prepare arrays for main variables
        vars_to_export = [
            'u_east_mps', 'v_north_mps', 'w_up_mps', 'wind_speed_mps', 'wind_direction_from_deg',
            'temperature_k', 'pressure_pa', 'relative_humidity_pct', 'specific_humidity_kg_kg',
            'density_kgm3', 'wind_shear_s_1'
        ]
        
        # We will build numpy arrays of shape (1, n_members, 1, n_alt)
        # dims: (valid_time, ensemble_member, surface_scenario, altitude_agl_m)
        
        data_arrays = {var: np.full((1, n_members, 1, n_alt), np.nan) for var in vars_to_export}
        member_roles = []
        member_sources = []
        model_names = []
        
        # Fill Nominal (Member 0)
        for var in vars_to_export:
            if var in df_nominal.columns:
                data_arrays[var][0, 0, 0, :] = df_nominal[var].values
        member_roles.append('nominal')
        member_sources.append(df_nominal['ensemble_source'].iloc[0] if 'ensemble_source' in df_nominal.columns else 'unknown')
        model_names.append(df_nominal['model_name'].iloc[0] if 'model_name' in df_nominal.columns else 'unknown')
                
        # Fill Ensembles (Member 1..N)
        for i, df_ens in enumerate(df_ensembles):
            idx = i + 1
            for var in vars_to_export:
                if var in df_ens.columns:
                    data_arrays[var][0, idx, 0, :] = df_ens[var].values
            role = 'synthetic_ensemble' if df_ens['data_type'].iloc[0] == 'synthetic_ensemble' else 'real_ensemble'
            member_roles.append(role)
            member_sources.append(df_ens['ensemble_source'].iloc[0] if 'ensemble_source' in df_ens.columns else 'unknown')
            model_names.append(df_ens['model_name'].iloc[0] if 'model_name' in df_ens.columns else 'unknown')
            
        # Create coordinates
        coords = {
            'valid_time': valid_time,
            'ensemble_member': np.arange(n_members),
            'surface_scenario': ['default'],
            'altitude_agl_m': z_grid,
            'member_role': ('ensemble_member', member_roles),
            'member_source': ('ensemble_member', member_sources),
            'model_name': ('ensemble_member', model_names)
        }
        
        # Create main Dataset
        ds_vars = {}
        for var in vars_to_export:
            ds_vars[var] = (('valid_time', 'ensemble_member', 'surface_scenario', 'altitude_agl_m'), data_arrays[var])
            
        # Add Climatology variables if available
        if df_stats is not None and not df_stats.empty:
            coords['climatology_statistic'] = ['mean', 'median', 'p10', 'p25', 'p75', 'p90']
            clim_z = df_stats['altitude_agl_m'].values
            for var in ['wind_speed_mps', 'temperature_k', 'u_east_mps', 'v_north_mps']:
                clim_data = np.full((len(coords['climatology_statistic']), n_alt), np.nan)
                for j, stat in enumerate(coords['climatology_statistic']):
                    col = f"{var}_{stat}"
                    if col in df_stats.columns:
                        # Interpolate to z_grid to match altitude_agl_m dimension
                        clim_data[j, :] = np.interp(z_grid, clim_z, df_stats[col].values, left=np.nan, right=np.nan)
                ds_vars[f"climatology_{var}"] = (('climatology_statistic', 'altitude_agl_m'), clim_data)
                
        ds = xr.Dataset(ds_vars, coords=coords)
        ds.attrs = global_attrs
        
        ds.to_netcdf(output_path)
