"""
ANTARES FLIGHT DYNAMICS
Unified Campaign Runner - Neblina 1.

Executes all flight simulation scenarios in this folder (deterministic + Monte Carlo)
and generates a single, consolidated results directory with a single master engineering PDF report.
"""
import sys
from pathlib import Path

# Ensures core packages ('source' and 'MAGI' root) can be imported
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SOURCE_DIR = PROJECT_ROOT / "source"
if str(SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from antares_fd.simulation.campaign import run_project_campaign


def main():
    simulations_dir = Path(__file__).resolve().parent
    run_project_campaign(simulations_dir)


if __name__ == "__main__":
    main()
