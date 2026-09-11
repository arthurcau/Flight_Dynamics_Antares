import sys

with open("source/antares_fd/simulation/plotters.py", "r") as f:
    content = f.read()

line_code = """
        # Add Nominal Trajectory path
        if nominal_flight is not None:
            path_pts = []
            for px, py in zip(nominal_flight.x[:, 1], nominal_flight.y[:, 1]):
                plat, plon = xy_to_latlon(px, py, lat_pad, lon_pad)
                path_pts.append((plat, plon))
            folium.PolyLine(locations=path_pts, color='black', weight=2, dash_array='5', tooltip='Nominal Trajectory').add_to(m)
            
        if nominal_flight_fail is not None:
            fail_pts = []
            for px, py in zip(nominal_flight_fail.x[:, 1], nominal_flight_fail.y[:, 1]):
                plat, plon = xy_to_latlon(px, py, lat_pad, lon_pad)
                fail_pts.append((plat, plon))
            folium.PolyLine(locations=fail_pts, color='magenta', weight=2, dash_array='5', tooltip='Failure Free-fall').add_to(m)
"""

marker = "        html_path = results_dir / f\"interactive_map_{run_id}.html\""
content = content.replace(marker, line_code + "\n" + marker)

with open("source/antares_fd/simulation/plotters.py", "w") as f:
    f.write(content)

