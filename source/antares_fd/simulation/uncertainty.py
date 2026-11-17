import yaml
import numpy as np
import pandas as pd
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class UncertaintyDef:
    """One configured random variable, including its provenance fields."""

    name: str
    enabled: bool
    units: str
    distribution: str
    provenance: dict
    params: dict

    @property
    def provenance_type(self) -> str:
        """Retorne a classificação de origem da incerteza.

        Consulta provenance.type e retorna UNKNOWN quando ausente, sem promover
        a distribuição a uma medição experimental.
        """
        return str(self.provenance.get("type", "UNKNOWN"))

    @property
    def correlation_group(self) -> str | None:
        """Retorne o grupo de correlação declarado nos parâmetros.

        Consulta params sem inferir dependências; ausência retorna None.
        O metadado não implementa por si só uma distribuição multivariada.
        """
        return self.params.get("correlation_group")

    @property
    def epistemic_or_aleatory(self) -> str:
        """Retorne a natureza epistemológica declarada da incerteza.

        Lê params.epistemic_or_aleatory e conserva UNKNOWN se não houver
        classificação explícita; não classifica automaticamente a variável.
        """
        return str(self.params.get("epistemic_or_aleatory", "UNKNOWN"))

class UncertaintyRegistry:
    """Load and validate enabled uncertainty definitions from project YAML."""

    def __init__(self, yaml_path: Path):
        """Inicialize e carregue o registro de incertezas de yaml_path.

        Prepara versão de esquema e mapeamento de definições, depois chama load.
        Erros de leitura ou formato interrompem a criação do registro.
        """
        self.yaml_path = yaml_path
        self.schema_version = 1
        self.registry: Dict[str, UncertaintyDef] = {}
        self.load()

    def load(self):
        """Read the uncertainty YAML and populate enabled parameter definitions."""
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
                params={pk: pv for pk, pv in v.items() if pk not in ["enabled", "units", "distribution", "provenance"]}
            )

    def validate(self, strict: bool = True) -> list[str]:
        """Validate supported distribution parameters before trajectory work."""
        errors: list[str] = []
        supported = {"uniform", "normal", "triangular", "empirical", "categorical", "ensemble_member"}
        for name, uncertainty in self.registry.items():
            distribution = uncertainty.distribution.lower()
            params = uncertainty.params
            if distribution not in supported:
                errors.append(f"{name}: unsupported distribution '{distribution}'")
            elif distribution == "uniform" and float(params.get("min", 0.0)) > float(params.get("max", 1.0)):
                errors.append(f"{name}: min must not exceed max")
            elif distribution == "triangular" and not {"left", "mode", "right"}.issubset(params):
                errors.append(f"{name}: triangular requires left, mode and right")
            elif distribution in {"empirical", "categorical", "ensemble_member"} and not params.get("values") and not params.get("categories") and not (name == "atmosphere_ensemble"):
                errors.append(f"{name}: values/categories are required")
        if errors and strict:
            raise ValueError("Invalid uncertainty registry: " + "; ".join(errors))
        return errors

class SamplingPlan:
    """Pre-generates all N samples deterministically before touching RocketPy."""
    def __init__(self, registry: UncertaintyRegistry, num_samples: int, seed: int = 42, env_ensemble_size: int = 0):
        """Prepare uma população reprodutível antes de integrar trajetórias.

        Armazena registro, número de casos, semente e tamanho do ensemble;
        valida distribuições e gera a tabela samples com case_id e seed estáveis.
        """
        self.registry = registry
        self.num_samples = num_samples
        self.seed = seed
        self.env_ensemble_size = env_ensemble_size
        self.samples = pd.DataFrame()
        registry.validate(strict=True)
        self._generate()

    def _generate(self):
        """Gere uma linha por caso com um fluxo aleatório independente.

        SeedSequence deriva sementes filhas da semente raiz; cada Generator
        amostra todas as definições habilitadas daquele caso. Substitui samples
        pelo DataFrame completo, preservando a ordem dos IDs.
        """
        root = np.random.SeedSequence(self.seed)
        children = root.spawn(self.num_samples)
        rows = []
        for case_id, child in enumerate(children):
            rng = np.random.default_rng(child)
            row = {"case_id": case_id, "seed": int(child.generate_state(1, dtype=np.uint64)[0])}
            for name, uncertainty in self.registry.registry.items():
                row[name] = self._sample_value(uncertainty, rng)
            rows.append(row)
        self.samples = pd.DataFrame(rows)

    def _sample_value(self, uncertainty: UncertaintyDef, rng: np.random.Generator) -> Any:
        """Sample one case using only that case's generator."""
        params = uncertainty.params
        distribution = uncertainty.distribution.lower()
        if distribution == "uniform":
            return float(rng.uniform(float(params.get("min", 0.0)), float(params.get("max", 1.0))))
        if distribution == "normal":
            if "mean" not in params and "nominal" not in params:
                # A physical nominal cannot be inferred from a YAML pointer.
                # Keep the row explicit and let the campaign report the
                # unsupported legacy assumption instead of inventing zero.
                return np.nan
            mean = params["mean"] if "mean" in params else params["nominal"]
            return float(rng.normal(float(mean), float(params.get("sigma", 1.0))))
        if distribution == "triangular":
            return float(rng.triangular(float(params["left"]), float(params["mode"]), float(params["right"])))
        if distribution in {"categorical", "ensemble_member"}:
            values = params.get("values", params.get("categories"))
            if values is None and uncertainty.name == "atmosphere_ensemble":
                values = list(range(self.env_ensemble_size)) if self.env_ensemble_size else [0]
            if not values:
                raise ValueError(f"Uncertainty '{uncertainty.name}' has no categorical values")
            return values[int(rng.integers(0, len(values)))]
        if distribution == "empirical":
            values = params.get("values", params.get("samples"))
            if not values:
                raise ValueError(f"Uncertainty '{uncertainty.name}' has no empirical samples")
            return values[int(rng.integers(0, len(values)))]
        raise ValueError(f"Unsupported distribution: {uncertainty.distribution}")

    def export(self, path: Path):
        """Exporte a população amostrada para Parquet ou CSV conforme a extensão.

        Parquet usa pyarrow e compressão zstd; os demais caminhos recebem CSV.
        Não inclui índice pandas; erros de escrita são propagados ao chamador.
        """
        path = Path(path)
        if path.suffix.lower() == ".parquet":
            self.samples.to_parquet(path, engine="pyarrow", compression="zstd", index=False)
        else:
            self.samples.to_csv(path, index=False)
