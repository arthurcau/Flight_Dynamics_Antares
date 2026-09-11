import sys

with open("source/antares_fd/simulation/plotters.py", "r") as f:
    content = f.read()

kml_3d_paths = """
            # Write Nominal 3D Flight Path
            if nominal_flight is not None:
                kml.write(f"    <Placemark>\\n")
                kml.write(f"      <name>Nominal Trajectory</name>\\n")
                kml.write(f"      <Style><LineStyle><color>ff000000</color><width>4</width></LineStyle></Style>\\n")
                kml.write(f"      <LineString>\\n")
                kml.write(f"        <extrude>0</extrude><tessellate>1</tessellate><altitudeMode>relativeToGround</altitudeMode>\\n")
                kml.write(f"        <coordinates>\\n")
                # Downsample to avoid massive KMLs
                step = max(1, len(nominal_flight.x[:, 1]) // 500)
                for px, py, pz in zip(nominal_flight.x[::step, 1], nominal_flight.y[::step, 1], nominal_flight.z[::step, 1]):
                    plat, plon = xy_to_latlon(px, py, lat_pad, lon_pad)
                    kml.write(f"          {plon},{plat},{pz}\\n")
                kml.write(f"        </coordinates>\\n")
                kml.write(f"      </LineString>\\n")
                kml.write(f"    </Placemark>\\n")
                
            # Write Failure 3D Flight Path
            if nominal_flight_fail is not None:
                kml.write(f"    <Placemark>\\n")
                kml.write(f"      <name>Failure Free-Fall Trajectory</name>\\n")
                kml.write(f"      <Style><LineStyle><color>ffff00ff</color><width>4</width></LineStyle></Style>\\n") # Magenta
                kml.write(f"      <LineString>\\n")
                kml.write(f"        <extrude>0</extrude><tessellate>1</tessellate><altitudeMode>relativeToGround</altitudeMode>\\n")
                kml.write(f"        <coordinates>\\n")
                step = max(1, len(nominal_flight_fail.x[:, 1]) // 500)
                for px, py, pz in zip(nominal_flight_fail.x[::step, 1], nominal_flight_fail.y[::step, 1], nominal_flight_fail.z[::step, 1]):
                    plat, plon = xy_to_latlon(px, py, lat_pad, lon_pad)
                    kml.write(f"          {plon},{plat},{pz}\\n")
                kml.write(f"        </coordinates>\\n")
                kml.write(f"      </LineString>\\n")
                kml.write(f"    </Placemark>\\n")
                
            # Optionally write 5 random Monte Carlo 3D outliers to see the dispersion cone in the sky!
            if all_flights is not None and len(all_flights) > 0:
                import random
                sample_flights = random.sample(list(all_flights), min(5, len(all_flights)))
                for idx, flt in enumerate(sample_flights):
                    if 'z' in flt:
                        kml.write(f"    <Placemark>\\n")
                        kml.write(f"      <name>Monte Carlo Iteration {idx}</name>\\n")
                        kml.write(f"      <Style><LineStyle><color>7f0000ff</color><width>1</width></LineStyle></Style>\\n") # Semi-transparent Red
                        kml.write(f"      <LineString>\\n")
                        kml.write(f"        <extrude>0</extrude><tessellate>1</tessellate><altitudeMode>relativeToGround</altitudeMode>\\n")
                        kml.write(f"        <coordinates>\\n")
                        step = max(1, len(flt['x']) // 200)
                        for px, py, pz in zip(flt['x'][::step], flt['y'][::step], flt['z'][::step]):
                            plat, plon = xy_to_latlon(px, py, lat_pad, lon_pad)
                            kml.write(f"          {plon},{plat},{pz}\\n")
                        kml.write(f"        </coordinates>\\n")
                        kml.write(f"      </LineString>\\n")
                        kml.write(f"    </Placemark>\\n")
"""

marker = "            kml.write(\"  </Document>\\n\")"
content = content.replace(marker, kml_3d_paths + "\n" + marker)

with open("source/antares_fd/simulation/plotters.py", "w") as f:
    f.write(content)

