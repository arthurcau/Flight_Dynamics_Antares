def print_flight_summary(flight, project_dir=None):
    """
    Prints a standard summary of the flight simulation and exports KML.
    """
    if flight is None:
        print("Flight Summary: No flight generated.")
        return
        
    print("\n" + "="*50)
    print("FLIGHT SUMMARY")
    print("="*50)
    print(f"Apogee: {flight.apogee:.2f} m")
    print(f"Time to Apogee: {flight.apogee_time:.2f} s")
    print(f"Max Velocity: {flight.max_speed:.2f} m/s")
    print(f"Max Mach Number: {flight.max_mach_number:.3f}")
    
    if len(flight.parachute_events) > 0:
        print("\nRecovery Events:")
        for event in flight.parachute_events:
            print(f"  - {event[1].name} deployed at {event[0]:.2f} s")
            
    print("="*50)
    
    if project_dir:
        # Export KML
        try:
            from rocketpy.simulation.flight_data_exporter import FlightDataExporter
            output_kml = project_dir / "trajectory.kml"
            FlightDataExporter(flight).export_kml(
                file_name=str(output_kml),
                extrude=True,
                altitude_mode="absolute"
            )
            print(f"\n[KML Export] Trajectory saved to: {output_kml}")
        except Exception as e:
            print(f"\n[KML Export Failed] {e}")
            
        # Export PDF Map
        try:
            from staticmap import StaticMap, Line
            
            # Extract coordinates from RocketPy Flight Function arrays
            lats = flight.latitude[:, 1]
            lons = flight.longitude[:, 1]
            coords = [[lon, lat] for lat, lon in zip(lats, lons)]
            
            if len(coords) > 0:
                m = StaticMap(1000, 1000)
                line = Line(coords, 'red', 3)
                m.add_line(line)
                
                output_pdf = project_dir / "trajectory_map.pdf"
                img = m.render()
                img.save(str(output_pdf), "PDF", resolution=100.0)
                print(f"[PDF Export] Map trajectory saved to: {output_pdf}")
                
        except ImportError:
            print("\n[PDF Export] 'staticmap' library not installed. Skipping PDF map generation.")
        except Exception as e:
            print(f"\n[PDF Export Failed] {e}")
            
    print("\n")
