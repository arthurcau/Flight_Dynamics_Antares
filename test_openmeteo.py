import requests
import pandas as pd
import datetime

def fetch_open_meteo(lat, lon, target_date=None):
    # Standard pressure levels in Open-Meteo
    levels = [1000, 975, 950, 925, 900, 850, 800, 700, 600, 500, 400, 300, 250, 200, 150, 100, 70, 50]
    hourly_vars = []
    for l in levels:
        hourly_vars.extend([f"temperature_{l}hPa", f"windspeed_{l}hPa", f"winddirection_{l}hPa", f"geopotential_height_{l}hPa"])
    
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly={','.join(hourly_vars)}&models=gfs_seamless"
    if target_date:
        d = target_date.strftime("%Y-%m-%d")
        url += f"&start_date={d}&end_date={d}"
        
    print(url[:200] + "...")
    r = requests.get(url)
    if r.status_code == 200:
        print("Success!")
        data = r.json()
        print(list(data['hourly'].keys())[:5])
    else:
        print("Failed:", r.status_code, r.text)

fetch_open_meteo(-22.3, -49.0, datetime.datetime.now())
