import requests
import pandas as pd
import datetime

def fetch_open_meteo(lat, lon, target_date=None):
    levels = [1000, 975, 950, 925, 900, 850, 800, 700, 600, 500, 400, 300, 250, 200, 150, 100, 70, 50]
    hourly_vars = []
    for l in levels:
        hourly_vars.extend([f"temperature_{l}hPa", f"windspeed_{l}hPa", f"winddirection_{l}hPa", f"geopotential_height_{l}hPa"])
    
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly={','.join(hourly_vars)}&models=gfs_seamless"
    if target_date:
        d = target_date.strftime("%Y-%m-%d")
        url += f"&start_date={d}&end_date={d}"
        
    r = requests.get(url)
    if r.status_code != 200:
        raise Exception("Failed to fetch")
        
    data = r.json()
    
    # We need to pick the closest hour to target_date
    times = pd.to_datetime(data['hourly']['time'])
    if target_date:
        # ensure target_date is timezone naive or both are aware
        target_date = pd.to_datetime(target_date).tz_localize(None)
        import numpy as np
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
                'altitude_msl_m': h,
                'temperature_k': t + 273.15, # open-meteo provides Celsius by default? No, wait, temperature_1000hPa is Celsius. Let's check!
                'wind_speed_mps': ws / 3.6, # km/h to m/s
                'wind_direction_from_deg': wd
            })
            
    df = pd.DataFrame(records)
    print(df.head())
    
fetch_open_meteo(-22.3, -49.0, datetime.datetime.now())
