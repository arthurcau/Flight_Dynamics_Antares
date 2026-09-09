"""
ANTARES FLIGHT DYNAMICS
Monte Carlo Simulation
"""
import sys
from pathlib import Path

# Ensures the core 'Source' package can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SOURCE_DIR = PROJECT_ROOT / "source"
if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))

from antares_fd.config import load_project_config
from antares_fd.simulation import execute_scenario

from rocketpy import StochasticEnvironment, StochasticRocket, StochasticFlight, MonteCarlo

def main():
    PROJECT_DIR = Path(__file__).resolve().parents[1]
    
    # 1. Load configuration
    config = load_project_config(PROJECT_DIR)
    
    # 2. Get the deterministic flight object by running the base scenario 
    # (this builds the environment, rocket, and flight under the hood).
    # We suppress prints for the deterministic setup.
    flight = execute_scenario(config, PROJECT_DIR, print_summary=False, export_kml=False)
    
    # 3. Read Monte Carlo config
    if config.monte_carlo is None:
        raise ValueError("monte_carlo.yaml configuration not found in project config.")
    
    mc_cfg = config.monte_carlo
    num_simulations = mc_cfg.get("num_simulations", 100)
    
    # Setup Stochastic Environment
    stoch_env = StochasticEnvironment(
        environment=flight.env,
        wind_velocity_x_factor=(1.0, mc_cfg["environment"]["wind_velocity_x"]["factor_std"]),
        wind_velocity_y_factor=(1.0, mc_cfg["environment"]["wind_velocity_y"]["factor_std"])
    )
    
    # Setup Stochastic Rocket
    stoch_rocket = StochasticRocket(
        rocket=flight.rocket,
        mass=(flight.rocket.mass, mc_cfg["vehicle"]["mass"]["std"]),
        power_off_drag_factor=(1.0, mc_cfg["vehicle"]["power_off_drag_factor"]["std"]),
        power_on_drag_factor=(1.0, mc_cfg["vehicle"]["power_on_drag_factor"]["std"])
    )
    
    # Setup Stochastic Flight
    stoch_flight = StochasticFlight(
        flight=flight,
        inclination=(flight.inclination, mc_cfg["flight"]["inclination"]["std"]),
        heading=(flight.heading, mc_cfg["flight"]["heading"]["std"])
    )
    
    # 4. Run Monte Carlo Simulation
    print(f"\\n[Monte Carlo] Starting simulation of {num_simulations} flights...")
    mc = MonteCarlo(
        filename=str(PROJECT_DIR / "monte_carlo_results"),
        environment=stoch_env,
        rocket=stoch_rocket,
        flight=stoch_flight,
        export_list=[
            "apogee",
            "apogee_time",
            "x_impact",
            "y_impact",
            "impact_velocity",
            "max_mach_number"
        ]
    )
    
    # Run in parallel if possible
    mc.simulate(num_simulations, parallel=True)
    
    # 5. Export Dispersion Ellipses
    kml_path = PROJECT_DIR / "dispersion_ellipses.kml"
    try:
        mc.export_ellipses_to_kml(
            filename=str(kml_path),
            origin_lat=flight.env.latitude,
            origin_lon=flight.env.longitude,
            type="impact"
        )
        print(f"\\n[Monte Carlo] Dispersion ellipses saved to: {kml_path}")
        
        # 5b. Generate PDF Map with Staticmap
        from staticmap import StaticMap, Polygon
        from rocketpy.simulation.monte_carlo import (
            generate_monte_carlo_ellipses,
            generate_monte_carlo_ellipses_coordinates
        )
        import numpy as np
        
        impact_x = np.array(mc.results.get('x_impact', []))
        impact_y = np.array(mc.results.get('y_impact', []))
        
        if len(impact_x) > 0 and len(impact_y) > 0:
            # Generate the raw ellipse objects (1, 2, 3 sigma)
            impact_ellipses, _ = generate_monte_carlo_ellipses(
                impact_x=impact_x,
                impact_y=impact_y,
                n_impact=[1, 2, 3]
            )
            
            # Convert to lat/lon coordinates
            ellipses_coords = generate_monte_carlo_ellipses_coordinates(
                impact_ellipses,
                origin_lat=flight.env.latitude,
                origin_lon=flight.env.longitude,
                resolution=100
            )
            
            from staticmap import CircleMarker
            m = StaticMap(1200, 1200)
            
            # Using tuple colors (R, G, B, A) to ensure Pillow compatibility
            colors = [(255, 0, 0, 80), (255, 128, 0, 80), (255, 255, 0, 80)]
            
            # Draw larger ellipses first so they don't cover the smaller ones (reversed order)
            for idx, coord_list in reversed(list(enumerate(ellipses_coords))):
                poly_coords = [[lon, lat] for lat, lon in coord_list]
                color = colors[min(idx, len(colors)-1)]
                p = Polygon(poly_coords, color, 'red')
                m.add_polygon(p)
                
            # Add Launch Pad
            m.add_marker(CircleMarker((flight.env.longitude, flight.env.latitude), 'blue', 6))
            
            pdf_path = PROJECT_DIR / "dispersion_map.pdf"
            img = m.render()
            
            # Bake transparency into RGB before exporting to PDF
            img.convert("RGB").save(str(pdf_path), "PDF", resolution=100.0)
            print(f"[Monte Carlo] Dispersion PDF map saved to: {pdf_path}")
            
    except Exception as e:
        print(f"\\n[Monte Carlo] Warning during Ellipse generation: {e}")
        
    # 6. Compress huge raw output files
    import gzip
    import shutil
    print("\\n[Monte Carlo] Compressing large log files...")
    for file_ext in [".inputs.txt", ".outputs.txt", ".errors.txt"]:
        raw_file = PROJECT_DIR / f"monte_carlo_results{file_ext}"
        if raw_file.exists():
            gz_file = raw_file.with_suffix('.txt.gz')
            with raw_file.open('rb') as f_in:
                with gzip.open(gz_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            raw_file.unlink() # Delete original
            print(f"  -> Compressed {raw_file.name} to .gz")
    
    return mc

if __name__ == "__main__":
    main()
