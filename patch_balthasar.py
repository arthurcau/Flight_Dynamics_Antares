import sys
import os

with open("MAGI/balthasar.py", "r") as f:
    code = f.read()

# Replace the single index fetching with time-window ensemble generation
# In _fetch_open_meteo, we can return the full hourly dataframe and let fetch_operational_forecast do the interpolation.
# Actually, let's just modify fetch_operational_forecast to generate time-shifted dataframes directly.

# It is easier to patch fetch_operational_forecast to just interpolate the hourly data.

code_to_replace = """    def fetch_operational_forecast(self, lat, lon, target_date_str=None):

        \"\"\"
        Fetches current operational forecast and triggers all external pipeline fetchers.
        \"\"\"
        print("BALTHASAR-2: Iniciando busca de previsão operacional e validações de rotina...")
        df_nominal = self._fetch_open_meteo(lat, lon, target_date_str)
        if len(df_nominal) == 0:
            return df_nominal, False
            
        print("Generating dynamic real-time ensemble members...")
        ensemble_members = [df_nominal]
        
        # Initiate parallel stub fetches to simulate the ingestion of all requested sources
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
            
            # Decorate with mandatory metadata fields requested by user
            df_member['source'] = 'gfs_ensemble'
            df_member['type'] = 'forecast'
            df_member['timestamp'] = df_nominal['valid_time_utc'].iloc[0]
            df_member['age_hours'] = 0.0
            df_member['distance_km'] = 0.0
            df_member['qf'] = 1
            
            ensemble_members.append(df_member)
            
        return ensemble_members, True"""

new_code = """    def fetch_operational_forecast(self, lat, lon, target_date_str=None, time_window_minutes=120, time_step_minutes=10):
        print("BALTHASAR-2: Iniciando busca de previsão operacional...")
        import json
        import pandas as pd
        import numpy as np
        import os
        
        # First, ensure we download the data
        df_nominal = self._fetch_open_meteo(lat, lon, target_date_str)
        if len(df_nominal) == 0:
            return df_nominal, False
            
        # Re-read the cached JSON which has the full 24h data
        cache_file = os.path.join(self.cache_dir, f"openmeteo_{lat}_{lon}.json")
        try:
            with open(cache_file, "r") as f:
                data = json.load(f)
        except:
            return [df_nominal], True
            
        times = pd.to_datetime(data['hourly']['time']).tz_localize(None)
        
        if target_date_str:
            target_date = pd.to_datetime(target_date_str).tz_localize(None)
        else:
            target_date = times[0]
            
        print(f"Generating time-shifted real-time ensemble members (Window: {time_window_minutes}m, Step: {time_step_minutes}m)...")
        ensemble_members = []
        
        levels = [1000, 975, 950, 925, 900, 850, 800, 700, 600, 500, 400, 300, 250, 200, 150, 100, 70, 50]
        
        # Create timestamps for the ensemble
        offsets = np.arange(-time_window_minutes/2, time_window_minutes/2 + time_step_minutes, time_step_minutes)
        target_timestamps = [target_date + pd.Timedelta(minutes=m) for m in offsets]
        
        for i, t_target in enumerate(target_timestamps):
            # Find the two bounding hourly indices
            idx_left = np.where(times <= t_target)[0]
            idx_right = np.where(times >= t_target)[0]
            
            idx0 = idx_left[-1] if len(idx_left) > 0 else 0
            idx1 = idx_right[0] if len(idx_right) > 0 else len(times) - 1
            
            # Interpolation weight
            t0 = times[idx0]
            t1 = times[idx1]
            if t0 == t1:
                w = 0.0
            else:
                w = (t_target - t0).total_seconds() / (t1 - t0).total_seconds()
                
            records = []
            for l in levels:
                temp0 = data['hourly'][f"temperature_{l}hPa"][idx0]
                temp1 = data['hourly'][f"temperature_{l}hPa"][idx1]
                
                ws0 = data['hourly'][f"windspeed_{l}hPa"][idx0]
                ws1 = data['hourly'][f"windspeed_{l}hPa"][idx1]
                
                wd0 = data['hourly'][f"winddirection_{l}hPa"][idx0]
                wd1 = data['hourly'][f"winddirection_{l}hPa"][idx1]
                
                h0 = data['hourly'][f"geopotential_height_{l}hPa"][idx0]
                h1 = data['hourly'][f"geopotential_height_{l}hPa"][idx1]
                
                if temp0 is not None and temp1 is not None:
                    # Circular interpolation for wind direction
                    wd0_rad = np.radians(wd0)
                    wd1_rad = np.radians(wd1)
                    sin_wd = (1-w)*np.sin(wd0_rad) + w*np.sin(wd1_rad)
                    cos_wd = (1-w)*np.cos(wd0_rad) + w*np.cos(wd1_rad)
                    wd = (np.degrees(np.arctan2(sin_wd, cos_wd)) + 360) % 360
                    
                    records.append({
                        'pressure_pa': l * 100.0,
                        'altitude_msl_m': float((1-w)*h0 + w*h1),
                        'temperature_k': float((1-w)*temp0 + w*temp1) + 273.15,
                        'wind_speed_mps': float((1-w)*ws0 + w*ws1) / 3.6, # km/h to m/s
                        'wind_direction_from_deg': float(wd)
                    })
            
            if not records:
                continue
                
            df_member = pd.DataFrame(records)
            df_member['altitude_agl_m'] = df_member['altitude_msl_m'] - self.elevation_msl
            
            from MAGI.casper import CasperPhysics
            u, v = CasperPhysics.speed_dir_to_uv(df_member['wind_speed_mps'], df_member['wind_direction_from_deg'])
            df_member['u_east_mps'] = u
            df_member['v_north_mps'] = v
            df_member['w_up_mps'] = 0.0
            
            # Metadata
            df_member['data_source'] = "open_meteo"
            df_member['model_name'] = "gfs_seamless"
            df_member['ensemble_member'] = f"time_shift_{int(offsets[i])}m"
            df_member['valid_time_utc'] = pd.to_datetime(t_target).tz_localize('UTC')
            df_member['generation_time_utc'] = pd.Timestamp.utcnow()
            
            ensemble_members.append(df_member)
            
        return ensemble_members, True"""

code = code.replace(code_to_replace, new_code)

with open("MAGI/balthasar.py", "w") as f:
    f.write(code)

