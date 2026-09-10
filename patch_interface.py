import re
with open("MAGI/interface.py", "r") as f:
    content = f.read()

new_code = """
def _process_df_to_profile(df_nominal, elevation, latitude, longitude):
    alt_asl = df_nominal['altitude_agl_m'].values.astype(float) + elevation
    pressure_vals = df_nominal['pressure_pa'].values.astype(float)
    temp_vals = df_nominal['temperature_k'].values.astype(float)
    u_vals = df_nominal['u_east_mps'].values.astype(float)
    v_vals = df_nominal['v_north_mps'].values.astype(float)
    
    model_name = df_nominal['model_name'].iloc[0] if 'model_name' in df_nominal.columns else "Unknown"
    valid_time = df_nominal['valid_time_utc'].iloc[0] if 'valid_time_utc' in df_nominal.columns else pd.Timestamp.utcnow()
    run_time = df_nominal['generation_time_utc'].iloc[0] if 'generation_time_utc' in df_nominal.columns else None
    
    return AtmosphericProfile(
        altitude_asl_m=alt_asl,
        pressure_pa=pressure_vals,
        temperature_k=temp_vals,
        wind_u_mps=u_vals,
        wind_v_mps=v_vals,
        source="MAGI",
        source_type=df_nominal['data_source'].iloc[0] if 'data_source' in df_nominal.columns else 'ensemble',
        model=model_name,
        run_time_utc=run_time,
        valid_time_utc=valid_time,
        latitude_deg=latitude,
        longitude_deg=longitude,
        member_id=df_nominal.get('ensemble_member', pd.Series(["control"])).iloc[0]
    )

def get_atmospheric_ensemble(latitude, longitude, elevation, target_date_str=None) -> list[AtmosphericProfile]:
    from MAGI.state_manager import StateManager
    from MAGI.balthasar import Balthasar
    from MAGI.casper import CasperProcessor
    
    magi_path = Path(__file__).resolve().parent
    cache_dir = str(magi_path / "dados_cache")
    
    state_mgr = StateManager(cache_dir=cache_dir)
    balthasar = Balthasar(cache_dir=cache_dir, elevation_msl=elevation)
    forecast_result, is_real_ensemble = balthasar.fetch_operational_forecast(latitude, longitude, target_date_str)
    
    if forecast_result is None:
        raise ConfigurationError("MAGI failed to generate an atmospheric profile.")

    if target_date_str:
        target_date = pd.to_datetime(target_date_str, utc=True)
        if isinstance(forecast_result, list):
            for df in forecast_result:
                df['valid_time_utc'] = target_date
        else:
            forecast_result['valid_time_utc'] = target_date

    VERTICAL_GRID = np.arange(10, 6000 + 100, 100)
    casper = CasperProcessor(elevation_msl=elevation, surface_scenario="OPEN_TERRAIN")
    
    profiles = []
    if not is_real_ensemble:
        df_nominal = casper.interpolate_profile(forecast_result, VERTICAL_GRID)
        df_nominal = df_nominal.dropna(subset=['pressure_pa', 'temperature_k', 'u_east_mps', 'v_north_mps'])
        profiles.append(_process_df_to_profile(df_nominal, elevation, latitude, longitude))
    else:
        for df in forecast_result:
            df_interp = casper.interpolate_profile(df, VERTICAL_GRID)
            df_interp = df_interp.dropna(subset=['pressure_pa', 'temperature_k', 'u_east_mps', 'v_north_mps'])
            profiles.append(_process_df_to_profile(df_interp, elevation, latitude, longitude))
            
    return profiles

"""

# Prepend the new functions before get_atmospheric_profile
content = content.replace("def get_atmospheric_profile", new_code + "def get_atmospheric_profile")

with open("MAGI/interface.py", "w") as f:
    f.write(content)

