"""
FlightDynamicsReport entrypoint.
Constructs the deterministc PDF report using the strict, single-source-of-truth FlightMetrics architecture.
"""
from pathlib import Path
from typing import Any, Optional
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
    def __init__(self, flight: Any, project_dir: Optional[Path] = None, run_id: str = "nominal"):
        self.flight = flight
        self.project_dir = project_dir or Path.cwd()
        self.run_id = run_id
        
        # Phase 1: Explicit Extractions
        self.metrics = extract_flight_metrics(flight, project_dir=self.project_dir)
        
        # Phase 2: Load Requirements
        req_yaml = self.project_dir.parents[1] / "source" / "antares_fd" / "reporting" / "data" / "requirements.yaml"
        self.req_db = RequirementDB(req_yaml)
        
        # Context Initialization
        self.ctx = ReportContext(self.project_dir, self.metrics, self.req_db)
        
    def generate(self, output_path: Path):
        """Builds PDF and exports raw validated metrics."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Export single-source-of-truth JSON
        json_path = output_path.parent / "master_metrics.json"
        
        # We don't want to dump the entire timeseries array to JSON as it is too large and only for plotting
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

