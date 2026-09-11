import sys

with open("source/antares_fd/simulation/plotters.py", "r") as f:
    content = f.read()

kde_code = """
    # Draw KDE Density Contours (Non-Linear Density Map)
    try:
        from scipy.stats import gaussian_kde
        xy = np.vstack([x, y])
        kde = gaussian_kde(xy)
        
        # Grid bounds
        xmin, xmax = x.min() - 100, x.max() + 100
        ymin, ymax = y.min() - 100, y.max() + 100
        
        # Determine appropriate grid spacing based on dispersion size
        grid_pts = 100
        X_grid, Y_grid = np.mgrid[xmin:xmax:complex(0, grid_pts), ymin:ymax:complex(0, grid_pts)]
        positions = np.vstack([X_grid.ravel(), Y_grid.ravel()])
        
        Z_grid = np.reshape(kde(positions).T, X_grid.shape)
        
        # Plot filled contours underneath
        cs = plt.contourf(X_grid, Y_grid, Z_grid, levels=7, cmap='Blues', alpha=0.3, zorder=1)
        plt.contour(X_grid, Y_grid, Z_grid, levels=7, colors='blue', alpha=0.3, linewidths=0.5, zorder=2)
    except Exception as e:
        print(f"[Monte Carlo] KDE Contour Plot failed: {e}")
"""

# Insert KDE code before probabilities/ellipses
marker_ellipses = "    probabilities = {"
content = content.replace(marker_ellipses, kde_code + "\n" + marker_ellipses)


kml_code = """
    # --- EXPORT KML FOR GOOGLE EARTH ---
    try:
        R_earth = 6378137.0
        
        def xy_to_latlon(px, py, ref_lat, ref_lon):
            lat = ref_lat + np.degrees(py / R_earth)
            lon = ref_lon + np.degrees(px / (R_earth * np.cos(np.radians(ref_lat))))
            return lat, lon
            
        kml_path = results_dir / f"dispersion_{run_id}.kml"
        with open(kml_path, 'w') as kml:
            kml.write("<?xml version=\\"1.0\\" encoding=\\"UTF-8\\"?>\\n")
            kml.write("<kml xmlns=\\"http://www.opengis.net/kml/2.2\\">\\n")
            kml.write("  <Document>\\n")
            kml.write(f"    <name>Monte Carlo Run: {run_id}</name>\\n")
            
            # Write Ellipses as Polygons
            for (label, p), color in zip(probabilities.items(), colors):
                try:
                    ellipse_data = calculate_covariance_ellipse(x, y, p)
                    cx, cy = ellipse_data['center']
                    w, h = ellipse_data['width'], ellipse_data['height']
                    ang = np.radians(ellipse_data['angle'])
                    
                    t = np.linspace(0, 2*np.pi, 50)
                    x_ell = cx + (w/2)*np.cos(t)*np.cos(ang) - (h/2)*np.sin(t)*np.sin(ang)
                    y_ell = cy + (w/2)*np.cos(t)*np.sin(ang) + (h/2)*np.sin(t)*np.cos(ang)
                    
                    kml.write(f"    <Placemark>\\n")
                    kml.write(f"      <name>{label}% Containment</name>\\n")
                    kml.write(f"      <Style><LineStyle><color>ff0000ff</color><width>2</width></LineStyle><PolyStyle><fill>0</fill></PolyStyle></Style>\\n")
                    kml.write(f"      <Polygon><outerBoundaryIs><LinearRing><coordinates>\\n")
                    for ex, ey in zip(x_ell, y_ell):
                        elat, elon = xy_to_latlon(ex, ey, lat_pad, lon_pad)
                        kml.write(f"        {elon},{elat},0\\n")
                    # close ring
                    elat, elon = xy_to_latlon(x_ell[0], y_ell[0], lat_pad, lon_pad)
                    kml.write(f"        {elon},{elat},0\\n")
                    kml.write(f"      </coordinates></LinearRing></outerBoundaryIs></Polygon>\\n")
                    kml.write(f"    </Placemark>\\n")
                except Exception: pass
                
            kml.write("  </Document>\\n")
            kml.write("</kml>\\n")
            
        print(f"[Monte Carlo] KML Exported to {kml_path} for Google Earth.")
    except Exception as e:
        print(f"[Monte Carlo] KML Export failed: {e}")
    # -----------------------------------
"""

# We need to make sure lat_pad and lon_pad are defined BEFORE the end of plot_monte_carlo_dispersion where we insert KML code.
# Currently they are defined inside `if 'neblina_1' in str(results_dir):`.
# Let's extract lat_pad and lon_pad earlier.
extract_pad_code = """
    # Get Launch Pad coordinates for KML and map
    lat_pad = -21.938982
    lon_pad = -48.950316
    if nominal_flight is not None and hasattr(nominal_flight, 'env'):
        lat_pad = nominal_flight.env.latitude
        lon_pad = nominal_flight.env.longitude
"""

content = content.replace("    plt.figure(figsize=(10, 10))", extract_pad_code + "\n    plt.figure(figsize=(10, 10))")

marker_end = "    plot_path = results_dir / f\"dispersion_plot_{run_id}.pdf\""
content = content.replace(marker_end, kml_code + "\n" + marker_end)

with open("source/antares_fd/simulation/plotters.py", "w") as f:
    f.write(content)

