import sys
import yaml
import subprocess
import datetime
from pathlib import Path
import os

def print_flight_summary(flight, project_dir=None):
    """
    Prints a standard summary of the flight simulation, exports KML, PDF, and Manifest.
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
        # Determine script name and run ID
        script_name = Path(sys.argv[0]).stem
        run_timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H%M%SZ')
        run_id = f"{run_timestamp}_{project_dir.name}_{script_name}"
        
        # We output to results/<project>/<run_id>/
        results_dir = project_dir.parents[1] / "results" / project_dir.name / run_id
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Export KML
        try:
            from rocketpy.simulation.flight_data_exporter import FlightDataExporter
            output_kml = results_dir / "trajectory.kml"
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
                
                output_pdf = results_dir / f"{project_dir.name}_{script_name}.pdf"
                img = m.render()
                img.save(str(output_pdf), "PDF", resolution=100.0)
                print(f"[PDF Export] Map trajectory saved to: {output_pdf}")
                
        except ImportError:
            print("\n[PDF Export] 'staticmap' library not installed. Skipping PDF map generation.")
        except Exception as e:
            print(f"\n[PDF Export Failed] {e}")
            
        # Write Manifest
        try:
            commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(project_dir)).decode().strip()
            dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=str(project_dir)).decode().strip())
        except Exception:
            commit = "unknown"
            dirty = False

        manifest = {
            "run": {
                "id": run_id,
                "timestamp_utc": datetime.datetime.utcnow().isoformat(),
                "script": script_name,
                "project": project_dir.name,
                "apogee_m": float(flight.apogee),
                "max_mach": float(flight.max_mach_number)
            },
            "git": {
                "commit": commit,
                "dirty_worktree": dirty,
            }
        }
        
        with open(results_dir / "manifest.yaml", "w") as f:
            yaml.dump(manifest, f, default_flow_style=False)
            
        print(f"[Manifest] Traceability data saved to: {results_dir / 'manifest.yaml'}")
        
        # Export comprehensive telemetry plots
        try:
            from antares_fd.simulation.plotters import export_nominal_flight_plots
            export_nominal_flight_plots(flight, results_dir, project_dir.name)
        except Exception as e:
            print(f"[Telemetry Plots Failed] {e}")

    print("\n")
