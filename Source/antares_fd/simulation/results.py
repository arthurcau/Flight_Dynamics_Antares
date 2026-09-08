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
        try:
            from rocketpy.simulation.flight_data_exporter import FlightDataExporter
            output_path = project_dir / "trajectory.kml"
            FlightDataExporter(flight).export_kml(
                file_name=str(output_path),
                extrude=True,
                altitude_mode="absolute"
            )
            print(f"\n[KML Export] Trajectory saved to: {output_path}")
        except Exception as e:
            print(f"\n[KML Export Failed] {e}")
    print("\n")
