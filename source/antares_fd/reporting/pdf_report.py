"""
FlightDynamicsReport entrypoint.
Constructs the deterministc PDF report using the strict, single-source-of-truth FlightMetrics architecture,
also handling multiple campaigns and Monte Carlo statistics.
"""
from pathlib import Path
from typing import Any, Optional, Dict
import json
import dataclasses
import numpy as np

from antares_fd.analysis.metrics import extract_flight_metrics
from antares_fd.analysis.requirements import RequirementDB
from antares_fd.reporting.builder import FlightDynamicsReportBuilder, ReportContext

class CustomJSONEncoder(json.JSONEncoder):
    """Handles serialization of dataclasses and numpy arrays for archiving."""
    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if hasattr(obj, "item"):  # numpy scalars
            return obj.item()
        return super().default(obj)

class FlightDynamicsReport:
    """
    Main entrypoint for generating the formal Engineering Report.
    Extracts DataClasses and restricts PDF building completely from the simulation object.
    """
    def __init__(self, flight: Any = None, config: Any = None, project_dir: Optional[Path] = None, mc_results_dir: Optional[Path] = None, run_id: str = "nominal", scenario_flights: Optional[Dict[str, Any]] = None):
        self.flight = flight
        self.config = config
        self.project_dir = project_dir or Path.cwd()
        self.run_id = run_id
        self.mc_results_dir = mc_results_dir
        
        # Scenario metrics mapping
        self.scenario_metrics = {}
        if scenario_flights:
            for name, f_obj in scenario_flights.items():
                self.scenario_metrics[name] = extract_flight_metrics(f_obj, project_dir=self.project_dir)
        
        if self.flight:
            self.metrics = extract_flight_metrics(self.flight, project_dir=self.project_dir)
        elif self.scenario_metrics:
            self.metrics = list(self.scenario_metrics.values())[0]
        else:
            raise ValueError("No Flight provided to report.")
            
        # Phase 2: Load Requirements
        req_yaml = self.project_dir.parents[1] / "source" / "antares_fd" / "reporting" / "data" / "requirements.yaml"
        self.req_db = RequirementDB(req_yaml)
        
        # Context Initialization
        self.ctx = ReportContext(self.project_dir, self.metrics, self.req_db)
        self.ctx.scenario_metrics = self.scenario_metrics
        self.ctx.mc_results_dir = self.mc_results_dir
        
    def generate(self, output_path: Path):
        """Builds PDF and exports raw validated metrics."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Export single-source-of-truth JSON
        json_path = output_path.parent / "master_metrics.json"
        
        # We don't want to dump the entire timeseries array to JSON
        metrics_dict = dataclasses.asdict(self.metrics)
        metrics_dict.pop("timeseries", None)
        metrics_dict.pop("atmosphere", None)
        
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(metrics_dict, f, cls=CustomJSONEncoder, indent=2)
            
        print(f"[Reporting] Master metrics saved: {json_path}")
        
        # Generate the formal report
        builder = FlightDynamicsReportBuilder(self.ctx)
        builder.build_deterministic_report(output_path)
        print(f"[Reporting] Deterministic engineering report generated: {output_path}")
        return output_path
