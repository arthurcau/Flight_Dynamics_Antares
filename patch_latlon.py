import sys

with open("source/antares_fd/simulation/plotters.py", "r") as f:
    content = f.read()

# I need to extract xy_to_latlon out of KML and place it right after lat_pad/lon_pad definitions.
kml_def = """    try:
        R_earth = 6378137.0
        
        def xy_to_latlon(px, py, ref_lat, ref_lon):
            lat = ref_lat + np.degrees(py / R_earth)
            lon = ref_lon + np.degrees(px / (R_earth * np.cos(np.radians(ref_lat))))
            return lat, lon"""
            
new_kml_def = """    try:
        kml_path = results_dir / f"dispersion_{run_id}.kml\""""

content = content.replace(kml_def, new_kml_def)

# Now inject it before folium:
global_def = """
    R_earth = 6378137.0
    def xy_to_latlon(px, py, ref_lat, ref_lon):
        lat = ref_lat + np.degrees(py / R_earth)
        lon = ref_lon + np.degrees(px / (R_earth * np.cos(np.radians(ref_lat))))
        return lat, lon
"""

marker = "    # --- GENERATE INTERACTIVE FOLIUM HTML MAP WITH SATELLITE IMAGERY ---"
content = content.replace(marker, global_def + "\n" + marker)

with open("source/antares_fd/simulation/plotters.py", "w") as f:
    f.write(content)
