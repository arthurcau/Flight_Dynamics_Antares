def print_flight_summary(flight):
    """
    Prints a standard summary of the flight simulation.
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
            print(f"  - {event[0].name} deployed at {event[1]:.2f} s")
            
    print("="*50 + "\n")
