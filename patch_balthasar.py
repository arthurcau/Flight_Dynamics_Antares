import re
with open("MAGI/balthasar.py", "r") as f:
    content = f.read()

new_open_meteo = """
    def _fetch_open_meteo(self, lat, lon, target_date_str):
        import requests
        import json
        import datetime
        import pandas as pd
        import numpy as np
        
        print(f"BALTHASAR-2: Downloading GFS data from Open-Meteo for lat={lat}, lon={lon}...")
        
        levels = [1000, 975, 950, 925, 900, 850, 800, 700, 600, 500, 400, 300, 250, 200, 150, 100, 70, 50]
        hourly_vars = []
        for l in levels:
            hourly_vars.extend([f"temperature_{l}hPa", f"windspeed_{l}hPa", f"winddirection_{l}hPa", f"geopotential_height_{l}hPa"])
        
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly={','.join(hourly_vars)}&models=gfs_seamless"
        
        target_date = None
        if target_date_str:
            target_date = pd.to_datetime(target_date_str)
            d = target_date.strftime("%Y-%m-%d")
            url += f"&start_date={d}&end_date={d}"
            
        r = requests.get(url)
        if r.status_code != 200:
            print("Failed to fetch from Open-Meteo:", r.status_code, r.text)
            return MagiSchema.create_empty()
            
        data = r.json()
        
        # Save to cache
        cache_file = os.path.join(self.cache_dir, f"openmeteo_{lat}_{lon}.json")
        with open(cache_file, "w") as f:
            json.dump(data, f)
            
        times = pd.to_datetime(data['hourly']['time'])
        if target_date:
            target_date = target_date.tz_localize(None)
            idx = np.abs(times - target_date).argmin()
        else:
            idx = 0
            
        records = []
        for l in levels:
            t = data['hourly'][f"temperature_{l}hPa"][idx]
            ws = data['hourly'][f"windspeed_{l}hPa"][idx]
            wd = data['hourly'][f"winddirection_{l}hPa"][idx]
            h = data['hourly'][f"geopotential_height_{l}hPa"][idx]
            if t is not None:
                records.append({
                    'pressure_pa': l * 100.0,
                    'altitude_msl_m': float(h),
                    'temperature_k': float(t) + 273.15,
                    'wind_speed_mps': float(ws) / 3.6,
                    'wind_direction_from_deg': float(wd)
                })
                
        df = pd.DataFrame(records)
        df['valid_time_utc'] = pd.to_datetime(data['hourly']['time'][idx]).tz_localize('UTC')
        df['generation_time_utc'] = pd.to_datetime(datetime.datetime.now(datetime.UTC))
        df['altitude_agl_m'] = df['altitude_msl_m'] - self.elevation_msl
        
        u, v = CasperPhysics.speed_dir_to_uv(df['wind_speed_mps'], df['wind_direction_from_deg'])
        df['u_east_mps'] = u
        df['v_north_mps'] = v
        df['w_up_mps'] = 0.0
        
        df['relative_humidity_pct'] = 50.0
        df['cloud_cover_pct'] = 50.0
        
        df['data_source'] = "open_meteo_gfs"
        df['data_type'] = "forecast"
        df['quality_flag'] = "API_FRESH"
        df['model_name'] = "gfs_seamless"
        df['ensemble_member'] = "control"
        
        df['source'] = 'Open-Meteo'
        df['type'] = 'deterministic'
        df['timestamp'] = df['valid_time_utc']
        df['age_hours'] = 0.0
        df['distance_km'] = 0.0
        df['qf'] = 1
        
        df = df.dropna(subset=['wind_speed_mps', 'temperature_k'])
        return df

    def fetch_operational_forecast(self, lat, lon, target_date_str=None):
"""

old_fetch_sig = "def fetch_operational_forecast(self):"
new_fetch_sig = "def fetch_operational_forecast(self, lat, lon, target_date_str=None):"

content = content.replace(old_fetch_sig, new_open_meteo)

content = content.replace("df_nominal = self._fetch_deterministic_fallback()", "df_nominal = self._fetch_open_meteo(lat, lon, target_date_str)")

with open("MAGI/balthasar.py", "w") as f:
    f.write(content)

