import sys

with open("source/antares_fd/simulation/plotters.py", "r") as f:
    content = f.read()

folium_code = """
    # --- GENERATE INTERACTIVE FOLIUM HTML MAP WITH SATELLITE IMAGERY ---
    try:
        import folium
        
        # Initialize map at the launch pad
        m = folium.Map(location=[lat_pad, lon_pad], zoom_start=14, tiles=None)
        
        # Add high-res satellite imagery from Esri
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Esri World Imagery',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Add Launch Pad Marker
        folium.Marker(
            location=[lat_pad, lon_pad],
            popup='Launch Pad',
            icon=folium.Icon(color='black', icon='rocket', prefix='fa')
        ).add_to(m)
        
        # Add Ellipses
        hex_colors = ['green', 'orange', 'red', 'purple']
        for (label, p), color in zip(probabilities.items(), hex_colors):
            try:
                ellipse_data = calculate_covariance_ellipse(x, y, p)
                cx, cy = ellipse_data['center']
                w, h = ellipse_data['width'], ellipse_data['height']
                ang = np.radians(ellipse_data['angle'])
                
                t = np.linspace(0, 2*np.pi, 50)
                x_ell = cx + (w/2)*np.cos(t)*np.cos(ang) - (h/2)*np.sin(t)*np.sin(ang)
                y_ell = cy + (w/2)*np.cos(t)*np.sin(ang) + (h/2)*np.sin(t)*np.cos(ang)
                
                points = []
                for ex, ey in zip(x_ell, y_ell):
                    elat, elon = xy_to_latlon(ex, ey, lat_pad, lon_pad)
                    points.append((elat, elon))
                
                folium.Polygon(
                    locations=points,
                    color=color,
                    fill=True,
                    fill_opacity=0.1,
                    weight=2,
                    tooltip=f'{label}% Containment'
                ).add_to(m)
            except Exception: pass
            
        # Add Simulated Impact Scatter
        for ix, iy in zip(x, y):
            ilat, ilon = xy_to_latlon(ix, iy, lat_pad, lon_pad)
            folium.CircleMarker(
                location=(ilat, ilon),
                radius=1,
                color='blue',
                fill=True,
                fill_opacity=0.5
            ).add_to(m)
            
        # Add Real Landing Sites if Neblina
        if 'neblina_1' in str(results_dir):
            folium.Marker(
                location=[lat_nose, lon_nose],
                popup='Real Nose Cone Landing',
                icon=folium.Icon(color='darkred', icon='info-sign')
            ).add_to(m)
            folium.Marker(
                location=[lat_fuse, lon_fuse],
                popup='Real Fuselage Landing',
                icon=folium.Icon(color='orange', icon='info-sign')
            ).add_to(m)
            
        html_path = results_dir / f"interactive_map_{run_id}.html"
        m.save(str(html_path))
        print(f"[Monte Carlo] Interactive Satellite Map (Folium) saved to {html_path}")
    except ImportError:
        print("[Monte Carlo] Folium not installed. Skipping interactive map.")
    except Exception as e:
        print(f"[Monte Carlo] Folium map generation failed: {e}")
    # -------------------------------------------------------------------
"""

marker_kml = "    # --- EXPORT KML FOR GOOGLE EARTH ---"
if marker_kml in content:
    content = content.replace(marker_kml, folium_code + "\n" + marker_kml)
    with open("source/antares_fd/simulation/plotters.py", "w") as f:
        f.write(content)
    print("Patched folium code!")
else:
    print("Could not find KML marker")

