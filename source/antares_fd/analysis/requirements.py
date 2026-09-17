import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from antares_fd.analysis.flight_metrics import FlightMetrics

@dataclass
class EvaluatedRequirement:
    req_id: str
    description: str
    metric_name: str
    operator: str
    limit: Any
    units: str
    source: str
    req_type: str
    value: Any
    status: str  # "SATISFIED", "MARGINAL", "VIOLATED", "NOT EVALUATED"
    margin: Optional[float]
    
    @property
    def is_critical(self) -> bool:
        return self.status == "VIOLATED" and self.req_type == "requirement"

class RequirementDB:
    def __init__(self, yaml_path: Path):
        self.requirements = {}
        if yaml_path.exists():
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data and 'requirements' in data:
                    self.requirements = data['requirements']

    def evaluate(self, metrics: FlightMetrics) -> List[EvaluatedRequirement]:
        results = []
        for key, req in self.requirements.items():
            metric_name = req.get('metric', '')
            val = getattr(metrics, metric_name, None)
            
            # Sub-field extraction logic (e.g. for parachute sink rates not directly in root)
            if val is None:
                if "drogue_sink_rate" in metric_name and metrics.drogue_event:
                    val = metrics.drogue_event.steady_sink_rate
                elif "main_sink_rate" in metric_name and metrics.main_event:
                    val = metrics.main_event.steady_sink_rate

            if val is None:
                results.append(EvaluatedRequirement(
                    req_id=req.get('id', key),
                    description=req.get('description', ''),
                    metric_name=metric_name,
                    operator=req.get('operator', ''),
                    limit=req.get('limit', ''),
                    units=req.get('units', ''),
                    source=req.get('source', ''),
                    req_type=req.get('type', 'requirement'),
                    value=None,
                    status="NOT EVALUATED",
                    margin=None
                ))
                continue

            op = req.get('operator')
            limit = req.get('limit')
            status = "NOT EVALUATED"
            margin = None

            try:
                if op == ">=":
                    margin = float(val) - float(limit)
                    status = "SATISFIED" if margin >= 0 else "VIOLATED"
                elif op == "<=":
                    margin = float(limit) - float(val)
                    status = "SATISFIED" if margin >= 0 else "VIOLATED"
                elif op == "between":
                    margin = min(float(val) - float(limit[0]), float(limit[1]) - float(val))
                    status = "SATISFIED" if (float(limit[0]) <= float(val) <= float(limit[1])) else "VIOLATED"
            except Exception:
                status = "NOT EVALUATED"

            # Check if it was slightly violated (warnings for guidelines)
            if status == "VIOLATED" and req.get('type') == 'guideline':
                status = "MARGINAL"

            results.append(EvaluatedRequirement(
                req_id=req.get('id', key),
                description=req.get('description', ''),
                metric_name=metric_name,
                operator=op,
                limit=limit,
                units=req.get('units', ''),
                source=req.get('source', ''),
                req_type=req.get('type', 'requirement'),
                value=val,
                status=status,
                margin=margin
            ))
        return results
