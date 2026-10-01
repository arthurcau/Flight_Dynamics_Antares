"""
ANTARES FLIGHT DYNAMICS
Unified Campaign Runner - Neblina 1.

The shared campaign runner selects declared entry points, executes the
deterministic cases before Monte Carlo, and collects their artifacts under one
results directory. Review notes by Cau.
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
    """Start one consolidated campaign for the Neblina 1 simulations folder."""
    simulations_dir = Path(__file__).resolve().parent
    run_project_campaign(simulations_dir)


if __name__ == "__main__":
    main()
