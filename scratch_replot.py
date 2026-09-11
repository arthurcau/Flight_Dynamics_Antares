import sys
from pathlib import Path

# Add source to path
sys.path.insert(0, str(Path("source").resolve()))
from antares_fd.simulation.plotters import plot_monte_carlo_dispersion

def replot_last_run(project_name="neblina_1"):
    results_dir = Path("results") / project_name
    # Find the most recent directory that has mc_sim.outputs.txt
    dirs = [d for d in results_dir.iterdir() if d.is_dir() and (d / "mc_sim.outputs.txt").exists()]
    if not dirs:
        print("No results found.")
        return
        
    latest_dir = sorted(dirs, key=lambda d: d.name)[-1]
    print(f"Re-plotting for {latest_dir.name}...")
    
    # We won't have the nominal_flight or all_flights easily without reloading the pickle,
    # but we can plot the dispersion of the impacts
    plot_monte_carlo_dispersion(latest_dir / "mc_sim.outputs.txt", latest_dir, latest_dir.name)
    print("Done!")

if __name__ == "__main__":
    replot_last_run()
