from .runner import run_flight
from .results import print_flight_summary
from .orchestrator import execute_scenario
from .uq_campaign import MonteCarloCampaign

def run_project_campaign(*args, **kwargs):
    """Lazy wrapper that avoids importing reporting during package startup."""
    from .campaign import run_project_campaign as _run_project_campaign
    return _run_project_campaign(*args, **kwargs)

__all__ = ["run_flight", "print_flight_summary", "execute_scenario", "run_project_campaign", "MonteCarloCampaign"]
