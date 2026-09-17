import itertools
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, Callable

@dataclass
class UncertaintyDef:
    name: str
    enabled: bool
    units: str
    distribution: str
    provenance: dict
    params: dict

class UncertaintyRegistry:
    def __init__(self, yaml_path: Path):
        self.yaml_path = yaml_path
        self.schema_version = 1
        self.registry: Dict[str, UncertaintyDef] = {}
        self.load()

    def load(self):
        with open(self.yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            
        self.schema_version = data.get("schema_version", 1)
        uncs = data.get("uncertainties", {})
        
        for k, v in uncs.items():
            if not v.get("enabled", True):
                continue
                
            self.registry[k] = UncertaintyDef(
                name=k,
                enabled=True,
                units=v.get("units", ""),
                distribution=v.get("distribution", "uniform"),
                provenance=v.get("provenance", {}),
                params={pk: pv for pk, pv in v.items() if pk not in ["enabled", "units", "distribution", "provenance", "nominal_yaml_path"]}
            )

class SamplingPlan:
    """Pre-generates all N samples deterministically before touching RocketPy."""
    def __init__(self, registry: UncertaintyRegistry, num_samples: int, seed: int = 42, env_ensemble_size: int = 0):
        self.registry = registry
        self.num_samples = num_samples
        self.seed = seed
        self.env_ensemble_size = env_ensemble_size
        self.rng = np.random.default_rng(self.seed)
        self.samples = pd.DataFrame()
        self._generate()

    def _generate(self):
        data = {"case_id": np.arange(self.num_samples) + 1}
        
        for name, u in self.registry.registry.items():
            if u.distribution == "uniform":
                data[name] = self.rng.uniform(u.params.get("min", 0), u.params.get("max", 1), self.num_samples)
            elif u.distribution == "normal":
                mean = u.params.get("mean", 0.0)
                sigma = u.params.get("sigma", 1.0)
                # Some are multipliers where mean=1.0. 
                # If they are physical dims, mean might be missing (assumed injected later).
                # To handle pure delta perturbations vs absolute:
                data[name] = self.rng.normal(mean, sigma, self.num_samples)
            elif u.distribution == "categorical":
                if name == "atmosphere_ensemble":
                    if self.env_ensemble_size > 0:
                        data[name] = self.rng.integers(0, self.env_ensemble_size, self.num_samples)
                    else:
                        data[name] = np.zeros(self.num_samples, dtype=int)
            else:
                 raise ValueError(f"Unsupported distribution: {u.distribution}")
                 
        self.samples = pd.DataFrame(data)

    def export(self, path: Path):
        self.samples.to_csv(path, index=False)
