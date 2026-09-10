import datetime
from pathlib import Path
import yaml
import subprocess
import numpy as np
import random

from antares_fd.builders import build_environment, build_motor, build_vehicle, add_recovery_system
from antares_fd.config.exceptions import ConfigurationError

from rocketpy import Flight, StochasticEnvironment, StochasticSolidMotor, StochasticRocket, StochasticFlight, MonteCarlo

def execute_monte_carlo(config, project_dir):
    """
    Central orchestrator for Monte Carlo campaigns.
    Reads config.monte_carlo and the standard nominal configs to construct
    the Stochastic inputs, then runs a full Monte Carlo campaign using RocketPy.
    """
    mc_cfg = config.monte_carlo if config.monte_carlo else {}
    if not mc_cfg:
        raise ConfigurationError("Monte Carlo configuration (monte_carlo.yaml) is missing or empty.")
        
    num_sims = mc_cfg.get("num_simulations", 10)
    seed = mc_cfg.get("random_seed", 42)
    
    # Force seed reproducibility
    np.random.seed(seed)
    random.seed(seed)

    print(f"\n[Monte Carlo] Building Nominal Models and Stochastics...")

    # 1. Environment
    env = build_environment(config.environment, config.launch)
    
    env_cfg = mc_cfg.get("environment", {})
    wx_f = env_cfg.get("wind_velocity_x", {}).get("factor_std", 0.0)
    wy_f = env_cfg.get("wind_velocity_y", {}).get("factor_std", 0.0)
    
    stoch_env = StochasticEnvironment(
        env,
        wind_velocity_x_factor=(1.0, wx_f) if wx_f else None,
        wind_velocity_y_factor=(1.0, wy_f) if wy_f else None,
    )

    # 2. Motor
    motor = build_motor(config.motor, project_dir)
    mot_cfg = mc_cfg.get("motor", {})
    imp_std_factor = mot_cfg.get("total_impulse_scale", {}).get("std", 0.0)
    
    stoch_motor = StochasticSolidMotor(
        motor,
        total_impulse=(motor.total_impulse, motor.total_impulse * imp_std_factor) if imp_std_factor else None,
    )

    # 3. Vehicle
    rocket = build_vehicle(config.vehicle, motor, project_dir)
    add_recovery_system(rocket, config.recovery)
    
    veh_cfg = mc_cfg.get("vehicle", {})
    mass_std = veh_cfg.get("mass", {}).get("std", 0.0)
    drag_off_std = veh_cfg.get("power_off_drag_factor", {}).get("std", 0.0)
    drag_on_std = veh_cfg.get("power_on_drag_factor", {}).get("std", 0.0)

    stoch_rocket = StochasticRocket(
        rocket,
        mass=(rocket.mass, mass_std) if mass_std else None,
        power_off_drag_factor=(1.0, drag_off_std) if drag_off_std else None,
        power_on_drag_factor=(1.0, drag_on_std) if drag_on_std else None,
    )
    stoch_rocket.add_motor(stoch_motor, position=rocket.motor_position)

    # 4. Flight
    flight = Flight(rocket, env, rail_length=config.launch.get("rail_length", 5.2), inclination=config.launch.get("inclination", 85.0), heading=config.launch.get("heading", 0.0))
    flt_cfg = mc_cfg.get("flight", {})
    inc_std = flt_cfg.get("inclination", {}).get("std", 0.0)
    hdg_std = flt_cfg.get("heading", {}).get("std", 0.0)

    stoch_flight = StochasticFlight(
        flight,
        inclination=(config.launch.get("inclination", 85.0), inc_std) if inc_std else None,
        heading=(config.launch.get("heading", 0.0), hdg_std) if hdg_std else None,
    )

    # 5. Output directory structure
    run_timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H%M%SZ')
    run_id = f"{run_timestamp}_{project_dir.name}_montecarlo"
    results_dir = project_dir.parents[0].parent / "results" / project_dir.name / run_id
    results_dir.mkdir(parents=True, exist_ok=True)
    
    filename = str(results_dir / "mc_sim")
    
    # 6. Run Monte Carlo
    print(f"[Monte Carlo] Starting {num_sims} simulations. Seed={seed}")
    mc = MonteCarlo(
        filename=filename,
        environment=stoch_env,
        rocket=stoch_rocket,
        flight=stoch_flight,
        export_list=['apogee', 'apogee_time', 'x_impact', 'y_impact', 'impact_velocity', 'max_mach_number', 't_final', 'out_of_rail_velocity', 'max_dynamic_pressure', 'max_speed'],
    )
    
    mc.simulate(number_of_simulations=num_sims, append=False)
    
    # 7. Write Manifest and Traceability
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(project_dir)).decode().strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=str(project_dir)).decode().strip())
    except:
        commit = "unknown"
        dirty = False

    manifest = {
        "run": {
            "id": run_id,
            "timestamp_utc": datetime.datetime.utcnow().isoformat(),
            "status": "completed",
            "requested_cases": num_sims,
            "completed_cases": len(mc.outputs_log) if hasattr(mc, 'outputs_log') else num_sims,
            "failed_cases": len(mc.errors_log) if hasattr(mc, 'errors_log') else 0,
        },
        "git": {
            "commit": commit,
            "dirty_worktree": dirty,
        },
        "monte_carlo": {
            "enabled": True,
            "seed": seed,
            "simulations": num_sims
        }
    }
    
    with open(results_dir / "manifest.yaml", "w") as f:
        yaml.dump(manifest, f, default_flow_style=False)
        
    print(f"[Monte Carlo] Campaign finished. Results saved to: {results_dir}")
    return mc
