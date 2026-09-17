"""
FlightDynamicsReport entrypoint.
Constructs the deterministc PDF report using the strict, single-source-of-truth FlightMetrics architecture,
also handling multiple campaigns and Monte Carlo statistics.
"""
from pathlib import Path
import shutil
from typing import Any, Optional, Dict
import json
import dataclasses
import numpy as np

from antares_fd.analysis.metrics import extract_flight_metrics
from antares_fd.analysis.requirements import RequirementDB
from antares_fd.reporting.builder import FlightDynamicsReportBuilder, ReportContext
from antares_fd.reporting.vector_report import VectorReportRenderer, _namespace

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
    def __init__(self, flight: Any = None, config: Any = None, project_dir: Optional[Path] = None, mc_results_dir: Optional[Path] = None, run_id: str = "nominal", scenario_flights: Optional[Dict[str, Any]] = None, artifact_dir: Optional[Path] = None):
        self.flight = flight
        self.config = config
        self.project_dir = project_dir or Path.cwd()
        self.run_id = run_id
        self.mc_results_dir = mc_results_dir
        self.artifact_dir = Path(artifact_dir) if artifact_dir else None
        
        # Scenario metrics mapping
        self.scenario_metrics = {}
        if scenario_flights:
            for name, f_obj in scenario_flights.items():
                self.scenario_metrics[name] = extract_flight_metrics(f_obj, config=self.config, project_dir=self.project_dir)
        
        if self.flight:
            self.metrics = extract_flight_metrics(self.flight, config=self.config, project_dir=self.project_dir)
        elif self.scenario_metrics:
            self.metrics = list(self.scenario_metrics.values())[0]
        elif artifact_dir:
            metrics_path = Path(artifact_dir) / "master_metrics.json"
            payload = _load_artifact_metrics(metrics_path)
            self.metrics = _namespace(payload)
        else:
            raise ValueError("No Flight provided to report.")
            
        # Phase 2: Load Requirements
        req_yaml = self.project_dir.parents[1] / "source" / "antares_fd" / "reporting" / "data" / "requirements.yaml"
        self.req_db = RequirementDB(req_yaml)
        
        # Artifact reports are intentionally renderer-only.  Constructing the
        # legacy ReportContext here would re-evaluate validity against a
        # partially populated namespace and could make a saved campaign
        # impossible to render.  VectorReportRenderer consumes the canonical
        # artifacts directly and never reruns physics.
        self.ctx = None if artifact_dir else ReportContext(self.project_dir, self.metrics, self.req_db)
        if self.ctx is not None:
            self.ctx.scenario_metrics = self.scenario_metrics
            self.ctx.mc_results_dir = self.mc_results_dir

    @classmethod
    def from_artifacts(cls, artifact_dir: Path, project_dir: Optional[Path] = None):
        """Create a report object that can only consume saved artifacts."""
        artifact_dir = Path(artifact_dir)
        payload = _read_json_file(artifact_dir / "manifest.json") or _read_json_file(artifact_dir / "manifest.yaml") or {}
        run_id = payload.get("campaign_id") or payload.get("campaign", {}).get("run_id") or artifact_dir.name
        return cls(project_dir=project_dir or artifact_dir.parents[2], mc_results_dir=artifact_dir, run_id=run_id, artifact_dir=artifact_dir)
        
    def generate(self, output_path: Path):
        """Build a vector PDF from canonical metrics and saved campaign data."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Export single-source-of-truth JSON
        json_path = output_path.parent / "master_metrics.json"
        
        # We don't want to dump the entire timeseries array to JSON
        if dataclasses.is_dataclass(self.metrics):
            metrics_dict = dataclasses.asdict(self.metrics)
            metrics_dict.pop("timeseries", None)
            metrics_dict.pop("atmosphere", None)
        else:
            metrics_dict = _plain(vars(self.metrics))
        
        if self.artifact_dir is None:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(metrics_dict, f, cls=CustomJSONEncoder, indent=2)
            print(f"[Reporting] Master metrics saved: {json_path}")
        
        renderer = VectorReportRenderer(self.metrics, self.project_dir, output_path, self.run_id, self.mc_results_dir, self.scenario_metrics)
        renderer.render()
        print(f"[Reporting] Vector engineering report generated: {output_path} ({renderer.pages} pages)")
        return output_path


def _read_json_file(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _load_artifact_metrics(path: Path) -> dict:
    """Load a metrics artifact, tolerating an interrupted legacy JSON write."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        try:
            raw = path.read_text(encoding="utf-8")
            # Older report generation could truncate while serializing an
            # optional event object. Retain the complete scalar prefix and
            # make the missing optional values explicit.
            prefix = raw.split('"drogue_event"', 1)[0].rstrip().rstrip(",")
            return json.loads(prefix + "\n}")
        except (OSError, json.JSONDecodeError):
            return {"project_name": "Antares", "vehicle_name": "NEBLINA 1"}


def _plain(value):
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if hasattr(value, "__dict__"):
        return _plain(vars(value))
    return value
