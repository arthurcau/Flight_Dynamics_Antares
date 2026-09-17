import sys
import yaml
import subprocess
import datetime
from pathlib import Path
import os


def print_flight_summary(flight, project_dir=None):
    """
    Prints a standard summary of the flight simulation, exports KML, PDF, and Manifest.
    Supports unified campaign mode when ANTARES_CAMPAIGN_DIR is set.
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
        script_name = os.environ.get("ANTARES_CURRENT_SCENARIO") or Path(sys.argv[0]).stem
        campaign_dir_env = os.environ.get("ANTARES_CAMPAIGN_DIR")
        is_campaign_active = os.environ.get("ANTARES_CAMPAIGN_ACTIVE") == "1"
        compact_outputs = (
            is_campaign_active
            and os.environ.get("ANTARES_COMPACT_OUTPUTS", "1") != "0"
        )

        if campaign_dir_env:
            results_dir = Path(campaign_dir_env)
            run_id = os.environ.get("ANTARES_CAMPAIGN_RUN_ID", results_dir.name)
            traj_dir = results_dir / "trajectories"
            traj_dir.mkdir(parents=True, exist_ok=True)
            output_kml = traj_dir / f"{script_name}.kml"
        else:
            run_timestamp = datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%dT%H%M%SZ')
            run_id = f"{run_timestamp}_{project_dir.name}_{script_name}"
            results_dir = project_dir.parents[1] / "results" / project_dir.name / run_id
            results_dir.mkdir(parents=True, exist_ok=True)
            output_kml = results_dir / "trajectory.kml"
        
        # Keep the nominal trajectory as the campaign's representative path.
        # Exporting every deterministic scenario here duplicates information
        # already summarized in the master report and consumes disk/time.
        if not compact_outputs or script_name == "nominal":
            try:
                from rocketpy.simulation.flight_data_exporter import FlightDataExporter
                FlightDataExporter(flight).export_kml(
                    file_name=str(output_kml),
                    extrude=True,
                    altitude_mode="absolute"
                )
                print(f"\n[KML Export] Trajectory saved to: {output_kml}")
            except Exception as e:
                print(f"\n[KML Export Failed] {e}")
        else:
            print(f"\n[KML Export] Skipped for compact campaign output: {script_name}")
            
        # Export PDF Map (standalone only)
        if not is_campaign_active:
            try:
                from staticmap import StaticMap, Line, CircleMarker
                
                # Extract coordinates from RocketPy Flight Function arrays
                lats = flight.latitude[:, 1]
                lons = flight.longitude[:, 1]
                coords = [[lon, lat] for lat, lon in zip(lats, lons)]
                
                if len(coords) > 0:
                    m = StaticMap(1000, 1000)
                    line = Line(coords, 'red', 3)
                    m.add_line(line)
                    
                    # Add launchpad marker
                    launchpad = CircleMarker((lons[0], lats[0]), 'black', 8)
                    m.add_marker(launchpad)
                    
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
                    "timestamp_utc": datetime.datetime.now(datetime.UTC).isoformat(),
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
                export_nominal_flight_plots(flight, results_dir, project_dir.name, script_name)
            except Exception as e:
                print(f"[Telemetry Plots Failed] {e}")

            # Generate Canonical Engineering Report (PDF + metrics.json)
            try:
                from antares_fd.reporting import FlightDynamicsReport
                report = FlightDynamicsReport(flight=flight, project_dir=project_dir, run_id=run_id)
                report.generate(results_dir / "reports" / "flight_dynamics_report.pdf")
            except Exception as e:
                print(f"[Engineering Report Failed] {e}")
        else:
            print(f"[Campaign Mode] Scenario '{script_name}' trajectory registered.")

    print("\n")
