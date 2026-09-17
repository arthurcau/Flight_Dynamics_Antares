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
    source_type: str
    source: str
    revision: str
    notes: str
    value: Any
    status: str  # "SATISFIED", "MARGINAL", "VIOLATED", "NOT EVALUATED", "WITHIN GUIDELINE", "OUTSIDE GUIDELINE", "WITHIN MODEL RANGE", "MODEL RANGE EXCEEDED"
    margin: Optional[float]
    
    @property
    def is_critical(self) -> bool:
        return self.status in ["VIOLATED", "OUTSIDE GUIDELINE", "MODEL RANGE EXCEEDED"]

class RequirementDB:
    def __init__(self, yaml_path: Path):
        self.requirements = {}
        if yaml_path.exists():
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data and 'requirements' in data:
                    self.requirements = data['requirements']
                # Additionally ingest model validity boundaries if they exist under a different header, but let's centralize them
                if data and 'model_validity' in data:
                    for k, v in data['model_validity'].items():
                        v['source_type'] = 'MODEL_VALIDITY_LIMIT'
                        self.requirements[k] = v

    def evaluate(self, metrics: FlightMetrics) -> List[EvaluatedRequirement]:
        results = []
        for key, req in self.requirements.items():
            metric_name = req.get('metric', '')
            val = getattr(metrics, metric_name, None)
            
            source_type = str(req.get('source_type', 'ENGINEERING_GUIDELINE')).upper()
            
            if val is None:
                results.append(EvaluatedRequirement(
                    req_id=req.get('id', key),
                    description=req.get('description', ''),
                    metric_name=metric_name,
                    operator=req.get('operator', ''),
                    limit=req.get('limit', ''),
                    units=req.get('unit', req.get('units', '')),
                    source_type=source_type,
                    source=req.get('source', ''),
                    revision=req.get('revision', ''),
                    notes=req.get('notes', ''),
                    value=None,
                    status="NOT EVALUATED",
                    margin=None
                ))
                continue

            op = req.get('operator')
            limit = req.get('limit')
            tolerance = float(req.get('tolerance', 0.0))
            status = "NOT EVALUATED"
            margin = None

            try:
                # Minimum bound
                if op == ">=":
                    margin = float(val) - float(limit)
                # Maximum bound
                elif op == "<=":
                    margin = float(limit) - float(val)
                elif op == "between" and isinstance(limit, list):
                    margin = min(float(val) - float(limit[0]), float(limit[1]) - float(val))
                    
                if margin is not None:
                    # Positive margin is healthy. 
                    # If margin is negative but bounded by tolerance, it's MARGINAL.
                    is_nominal = (margin >= 0)
                    is_marginal = (not is_nominal) and (abs(margin) <= tolerance)
                    is_failed = (margin < -tolerance)

                    if source_type in ["FORMAL_REQUIREMENT", "ANTARES_REQUIREMENT", "HARDWARE_QUALIFICATION_LIMIT"]:
                        if is_nominal: status = "SATISFIED"
                        elif is_marginal: status = "MARGINAL"
                        else: status = "VIOLATED"
                    elif "GUIDELINE" in source_type:
                        if is_nominal or is_marginal: status = "WITHIN GUIDELINE"
                        else: status = "OUTSIDE GUIDELINE"
                    elif "VALIDITY" in source_type:
                        if is_nominal or is_marginal: status = "WITHIN MODEL RANGE"
                        else: status = "MODEL RANGE EXCEEDED"
                    else:
                        status = "SATISFIED" if (is_nominal or is_marginal) else "VIOLATED"
            except Exception as e:
                status = "NOT EVALUATED"

            results.append(EvaluatedRequirement(
                req_id=req.get('id', key),
                description=req.get('description', ''),
                metric_name=metric_name,
                operator=op,
                limit=limit,
                units=req.get('unit', req.get('units', '')),
                source_type=source_type,
                source=req.get('source', ''),
                revision=req.get('revision', ''),
                notes=req.get('notes', ''),
                value=val,
                status=status,
                margin=margin
            ))
        return results
