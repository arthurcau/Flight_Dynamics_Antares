"""Canonical campaign metadata, deterministic sampling and resumable paths."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import sys
import time
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from antares_fd.simulation.uq_storage import write_json_atomic, write_parquet_atomic
from antares_fd.simulation.uncertainty import SamplingPlan, UncertaintyRegistry
from antares_fd.simulation.scenarios import REQUIRED_SCENARIOS, SCENARIOS
from antares_fd.config.input_files import collect_project_model_inputs


PROFILES: dict[str, dict[str, Any]] = {
    "debug": {"target_samples": 50, "min_samples": 50, "max_samples": 50, "adaptive_stop": False, "convergence": False},
    "development": {"target_samples": 500, "min_samples": 500, "max_samples": 500, "adaptive_stop": False, "convergence": True},
    "engineering": {"target_samples": 2000, "min_samples": 2000, "max_samples": 2000, "adaptive_stop": False, "convergence": True},
    "official": {"target_samples": 10000, "min_samples": 10000, "max_samples": 20000, "adaptive_stop": True, "convergence": True, "statistical_verification": True},
}

CAMPAIGN_STATUSES = {
    "CREATED", "SAMPLING", "RUNNING", "PARTIAL", "COMPLETE",
    "COMPLETE_NOT_CONVERGED", "FAILED",
}


def _hash_file(path: Path) -> str:
    """Calcule SHA-256 de uma entrada para identificar a população da campanha.

    Lê blocos binários e retorna digest hexadecimal, sem incluir caminhos
    absolutos no conteúdo identificado.
    """
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _path_component(value: str, label: str) -> str:
    """Valide um identificador usado como componente de caminho.

    Rejeita vazio, separadores e referências que escapem do diretório.
    Retorna texto seguro para organização dos artefatos da campanha.
    """
    if (
        not isinstance(value, str)
        or not value.strip()
        or value in {".", ".."}
        or "/" in value
        or "\\" in value
        or "\0" in value
        or Path(value).is_absolute()
    ):
        raise ValueError(f"{label} must be a single safe path component")
    return value


def _results_root(root: Path) -> Path:
    """Resolva a raiz autorizada de resultados de um projeto.

    Resolve root/results e rejeita links simbólicos na raiz de resultados.
    Retorna Path para criação dos diretórios da campanha.
    """
    repository = Path(root).resolve()
    results = repository / "results"
    if results.is_symlink():
        raise ValueError(f"Campaign artifacts cannot use a symlinked results directory: {results}")
    return results


def _results_artifact_path(root: Path, path: Path) -> Path:
    """Resolve one campaign artifact path and reject escapes or symlink hops."""
    repository = Path(root).resolve()
    results = _results_root(repository)
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = repository / candidate
    lexical = Path(os.path.abspath(candidate))
    if not lexical.is_relative_to(results):
        raise ValueError(f"Campaign artifact path must remain below results/: {path}")
    current = results
    for part in lexical.relative_to(results).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"Campaign artifact path cannot traverse symlinks: {current}")
    resolved_results = results.resolve()
    resolved = lexical.resolve()
    if not resolved.is_relative_to(resolved_results):
        raise ValueError(f"Campaign artifact path resolves outside results/: {path}")
    return lexical


def campaign_path_for(root: Path, project: str, campaign_id: str) -> Path:
    """Return a validated campaign path beneath the repository results area."""
    project_name = _path_component(project, "Project name")
    run_id = _path_component(campaign_id, "Campaign id")
    repository = Path(root).resolve()
    return _results_artifact_path(repository, repository / "results" / project_name / run_id)


def _git_metadata(root: Path) -> dict[str, Any]:
    """Obtenha revisão Git e estado de trabalho para a proveniência.

    Delega ao coletor compartilhado que registra commit, alterações e snapshot.
    Retorna metadados sem modificar o repositório.
    """
    from antares_fd.analysis.provenance import get_git_provenance

    provenance = get_git_provenance(Path(root))
    dirty_state = provenance.get("dirty", "unknown")
    dirty = dirty_state == "dirty" if dirty_state in {"dirty", "clean"} else None
    return {
        "commit": provenance.get("commit", "unknown"),
        "branch": provenance.get("branch", "unknown"),
        "dirty": dirty,
        "working_tree_snapshot_sha256": provenance.get("working_tree_snapshot_sha256", "unknown"),
    }


@dataclass
class MonteCarloCampaign:
    """Own immutable samples and resumable batch artifacts for one campaign."""

    project: str
    root: Path
    master_seed: int = 42
    profile: str = "development"
    campaign_id: str | None = None
    config: Mapping[str, Any] = field(default_factory=dict)
    scenario_id: str | None = None

    def __post_init__(self) -> None:
        """Prepare a configuração resolvida e os diretórios da campanha Monte Carlo.

        Resolve perfil, limites de amostragem, hashes e estado de retomada;
        valida consistência antes de criar ou reutilizar os artefatos canônicos.
        """
        if self.profile not in PROFILES:
            raise ValueError(f"Unknown Monte Carlo profile: {self.profile}")
        settings = {**PROFILES[self.profile], **dict(self.config)}
        self.settings = settings
        self.started_monotonic = time.perf_counter()
        project_name = _path_component(self.project, "Project name")
        if self.scenario_id is not None:
            self.scenario_id = _path_component(self.scenario_id, "Scenario id")
        if self.campaign_id is None:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
            base_id = f"{stamp}_{project_name}_{self.master_seed}"
            suffix = 0
            while True:
                candidate = base_id if suffix == 0 else f"{base_id}_{suffix:02d}"
                candidate_root = campaign_path_for(self.root, project_name, candidate)
                try:
                    candidate_root.mkdir(parents=True, exist_ok=False)
                except FileExistsError:
                    if not candidate_root.exists():
                        raise
                    suffix += 1
                    continue
                self.campaign_id = candidate
                self.root_path = candidate_root
                break
        else:
            self.campaign_id = _path_component(self.campaign_id, "Campaign id")
            self.root_path = campaign_path_for(self.root, project_name, self.campaign_id)
            self.root_path.mkdir(parents=True, exist_ok=True)
        raw_path = self.root_path / "scenarios" / self.scenario_id if self.scenario_id else self.root_path
        self.path = _results_artifact_path(self.root, raw_path)
        # A multi-scenario campaign has one immutable sample table at its root;
        # every scenario campaign points to that same file.
        self.samples_path = _results_artifact_path(
            self.root, self.root_path / "samples" / "inputs.parquet",
        )
        self.batches_path = _results_artifact_path(self.root, self.path / "batches")
        self.path.mkdir(parents=True, exist_ok=True)
        self.samples_path.parent.mkdir(parents=True, exist_ok=True)
        self.batches_path.mkdir(parents=True, exist_ok=True)
        for directory_name in ("config_snapshot", "plots", "logs"):
            directory = _results_artifact_path(self.root, self.path / directory_name)
            directory.mkdir(parents=True, exist_ok=True)

    @property
    def is_scenario_campaign(self) -> bool:
        """Informe se a campanha usa o layout compartilhado por cenários.

        Retorna bool a partir do estado configurado; a propriedade determina
        como os diretórios e manifestos devem ser organizados.
        """
        return self.scenario_id is not None

    def snapshot_config(self, project_dir: Path) -> dict[str, str]:
        """Snapshot all project-local model inputs without replacing prior bytes."""
        hashes: dict[str, str] = {}
        project_dir = Path(project_dir).resolve()
        destination = _results_artifact_path(self.root, self.root_path / "config_snapshot")
        destination.mkdir(parents=True, exist_ok=True)
        for source in collect_project_model_inputs(project_dir):
            relative = source.relative_to(project_dir)
            target = _results_artifact_path(self.root, destination / relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            source_hash = _hash_file(source)
            if target.exists():
                if _hash_file(target) != source_hash:
                    raise ValueError(f"Campaign model input changed after snapshot: {relative.as_posix()}")
            else:
                shutil.copy2(source, target)
                if _hash_file(source) != source_hash or _hash_file(target) != source_hash:
                    raise RuntimeError(f"Campaign model input changed while snapshotting: {relative.as_posix()}")
            hashes[relative.as_posix()] = source_hash
        return hashes

    def next_target(self, completed: int, converged: bool = False) -> int:
        """Return the next bounded target for an adaptive official campaign."""
        completed = int(completed)
        if self.profile != "official" or not self.settings.get("adaptive_stop", True):
            return min(self.max_samples, self.target_samples)
        if completed < self.min_samples:
            return self.min_samples
        if converged:
            return completed
        batch = int(self.settings.get("batch_size", 1000))
        return min(self.max_samples, completed + max(1, batch))

    @property
    def target_samples(self) -> int:
        """Retorne a meta de casos definida pelo perfil e pelas opções de execução.

        Converte o valor configurado em inteiro; a meta é usada pelo controlador
        de lotes, sem gerar amostras nesta consulta.
        """
        return int(self.settings.get("target_samples", self.settings.get("min_samples", 0)))

    @property
    def min_samples(self) -> int:
        """Retorne o mínimo de casos exigido antes da parada por convergência.

        Obtém o valor do perfil configurado e o converte em inteiro.
        A consulta não avalia a convergência dos resultados.
        """
        return int(self.settings.get("min_samples", self.target_samples))

    @property
    def max_samples(self) -> int:
        """Retorne o limite superior de casos autorizado para a campanha.

        Obtém o limite do perfil e opções resolvidas; o controlador de lotes
        usa esse valor para impedir crescimento ilimitado da população.
        """
        return int(self.settings.get("max_samples", self.target_samples))

    def make_samples(self, registry_path: Path | None, count: int | None = None, ensemble_size: int = 0) -> pd.DataFrame:
        """Create the immutable input table, including a case-local seed."""
        self.samples_path = _results_artifact_path(self.root, self.samples_path)
        if self.samples_path.exists():
            return pd.read_parquet(self.samples_path)
        count = int(count or self.max_samples)
        if registry_path is not None and Path(registry_path).exists():
            registry = UncertaintyRegistry(Path(registry_path))
            samples = SamplingPlan(registry, count, self.master_seed, ensemble_size).samples.copy()
        else:
            children = np.random.SeedSequence(self.master_seed).spawn(count)
            samples = pd.DataFrame({"case_id": range(count), "seed": [int(child.generate_state(1, dtype=np.uint64)[0]) for child in children]})
        write_parquet_atomic(samples, self.samples_path)
        return samples

    def completed_case_ids(self) -> set[int]:
        """Recupere IDs concluídos nas saídas canônicas já salvas.

        Lê os lotes disponíveis e retorna os identificadores para planejamento
        de retomada, sem contar arquivos como substitutos de casos.
        """
        completed: set[int] = set()
        batches_path = _results_artifact_path(self.root, self.batches_path)
        for file in sorted(batches_path.glob("batch_*.parquet")):
            file = _results_artifact_path(self.root, file)
            if file.is_symlink():
                raise ValueError(f"Campaign batch cannot be a symlink: {file}")
            try:
                batch = pd.read_parquet(file, columns=["case_id"])
                completed.update(batch["case_id"].astype(int).tolist())
            except Exception as exc:
                raise ValueError(f"Cannot read campaign batch file: {file}") from exc
        return completed

    def write_batch(self, batch_number: int, results: pd.DataFrame) -> Path:
        """Grave um lote canônico de resultados em Parquet.

        Organiza o nome do lote no diretório da campanha e utiliza escrita atômica.
        O arquivo só substitui o destino depois da gravação completa.
        """
        path = _results_artifact_path(
            self.root, self.batches_path / f"batch_{int(batch_number):05d}.parquet",
        )
        return write_parquet_atomic(results, path)

    def write_manifest(self, status: str, samples: pd.DataFrame | None = None, extra: Mapping[str, Any] | None = None) -> Path:
        """Publique o manifesto da campanha com o estado de execução atual.

        Reúne configuração resolvida, população, proveniência e detalhes recebidos
        e escreve JSON de forma atômica para permitir auditoria e retomada.
        """
        sample_count = int(len(samples)) if samples is not None else self.max_samples
        previous: dict[str, Any] = {}
        manifest_path = _results_artifact_path(self.root, self.path / "manifest.json")
        if manifest_path.is_symlink():
            raise ValueError(f"Campaign manifest cannot be a symlink: {manifest_path}")
        if manifest_path.exists():
            try:
                previous = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                previous = {}
        manifest = {
            "campaign_id": self.campaign_id, "project": self.project, "status": status,
            "master_seed": self.master_seed, "profile": self.profile,
            "requested_samples": self.target_samples, "min_samples": self.min_samples,
            "max_samples": self.max_samples, "sample_table": str(self.samples_path.relative_to(self.root_path)),
            "completed_samples": len(self.completed_case_ids()), "sample_table_rows": sample_count,
            "python": sys.version, "platform": platform.platform(), "git": _git_metadata(Path(self.root)),
            "created_utc": datetime.now(timezone.utc).isoformat(),
        }
        if previous.get("configuration_hashes"):
            manifest["configuration_hashes"] = previous["configuration_hashes"]
        if extra:
            manifest.update(dict(extra))
        return write_json_atomic(manifest, self.path / "manifest.json")

    def artifact_hashes(self) -> dict[str, str]:
        """Hash canonical files so an archived campaign can be verified."""
        self.path = _results_artifact_path(self.root, self.path)
        hashes = {}
        for file in sorted(self.path.rglob("*")):
            if file.is_symlink():
                raise ValueError(f"Campaign artifact cannot be a symlink: {file}")
            if file.is_file() and file.name != "manifest.json" and ".tmp" not in file.name:
                hashes[str(file.relative_to(self.path))] = _hash_file(file)
        return hashes

    def archive(self, destination: Path | None = None) -> Path:
        """Create a portable ZIP containing canonical campaign evidence."""
        self.path = _results_artifact_path(self.root, self.path)
        manifest_path = self.path / "manifest.json"
        if manifest_path.is_symlink():
            raise ValueError(f"Campaign manifest cannot be a symlink: {manifest_path}")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Cannot archive campaign without a manifest: {manifest_path}") from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Cannot archive campaign with an unreadable manifest: {manifest_path}") from exc
        terminal_statuses = {"PARTIAL", "COMPLETE", "COMPLETE_NOT_CONVERGED", "FAILED"}
        if not isinstance(manifest, dict) or manifest.get("status") not in terminal_statuses:
            raise ValueError(
                f"Cannot archive campaign without a recognized terminal status: {manifest_path}"
            )
        destination = Path(destination) if destination is not None else Path(f"{self.path}.zip")
        if not destination.is_absolute():
            destination = Path(self.root).resolve() / destination
        destination = _results_artifact_path(self.root, destination)
        if destination == self.path or destination.is_relative_to(self.path):
            raise ValueError("Campaign archive must be outside its source campaign directory")
        if destination.exists():
            raise FileExistsError(f"Campaign archive already exists: {destination}")
        for path in self.path.rglob("*"):
            if path.is_symlink():
                raise ValueError(f"Campaign archive cannot contain symlinked artifacts: {path}")
        manifest["artifact_hashes"] = self.artifact_hashes()
        write_json_atomic(manifest, manifest_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED) as archive:
            for file in sorted(self.path.rglob("*")):
                if file.is_file() and ".tmp" not in file.name:
                    archive.write(file, file.relative_to(self.path))
        return destination


@dataclass
class StochasticScenarioCampaign:
    """Own one immutable sample population and comparable scenario campaigns."""

    project: str
    root: Path
    master_seed: int = 42
    profile: str = "development"
    campaign_id: str | None = None
    config: Mapping[str, Any] = field(default_factory=dict)
    scenario_ids: tuple[str, ...] = REQUIRED_SCENARIOS

    def __post_init__(self) -> None:
        """Prepare uma campanha estocástica com uma população comum entre cenários.

        Normaliza os IDs solicitados, rejeita cenários desconhecidos e instancia
        a campanha base. Não executa trajetórias durante a inicialização.
        """
        requested = tuple(dict.fromkeys(str(item).lower() for item in self.scenario_ids))
        unknown = [item for item in requested if item not in SCENARIOS]
        if unknown:
            raise ValueError(f"Unsupported scenario_id(s): {unknown}")
        self.scenario_ids = requested or REQUIRED_SCENARIOS
        self.base = MonteCarloCampaign(
            self.project, self.root, self.master_seed, self.profile,
            self.campaign_id, self.config, None,
        )
        self.campaign_id = self.base.campaign_id

    @property
    def path(self) -> Path:
        """Retorne o diretório raiz da campanha base.

        A propriedade encaminha base.root_path, permitindo que manifestos
        e comparações pareadas compartilhem a mesma raiz.
        """
        return self.base.root_path

    @property
    def samples_path(self) -> Path:
        """Retorne o caminho da população compartilhada de amostras.

        Encaminha a referência da campanha pai para que os cenários usem
        os mesmos case_id e sementes.
        """
        return self.base.samples_path

    @property
    def target_samples(self) -> int:
        """Consulte a meta de casos da campanha pai.

        Retorna a propriedade correspondente sem manter uma segunda configuração
        que possa divergir entre cenários.
        """
        return self.base.target_samples

    @property
    def min_samples(self) -> int:
        """Consulte o mínimo de amostras da campanha pai.

        Retorna o mesmo limite usado por todos os cenários da população pareada;
        a consulta não altera o estado da campanha.
        """
        return self.base.min_samples

    @property
    def max_samples(self) -> int:
        """Consulte o teto de amostras da campanha pai.

        Retorna o limite compartilhado que restringe a execução do cenário,
        sem ampliar automaticamente a população.
        """
        return self.base.max_samples

    def snapshot_config(self, project_dir: Path) -> dict[str, str]:
        """Encaminhe a criação do snapshot de entradas à campanha pai.

        Evita cópias conflitantes da configuração entre cenários; retorna
        a referência produzida pelo método compartilhado.
        """
        return self.base.snapshot_config(project_dir)

    def scenario(self, scenario_id: str) -> MonteCarloCampaign:
        """Crie a visão MonteCarloCampaign de um cenário autorizado.

        Normaliza o nome, exige associação a scenario_ids e instancia a visão
        com projeto, semente, perfil, configuração e ID de campanha compartilhados.
        """
        scenario_id = str(scenario_id).lower()
        if scenario_id not in self.scenario_ids:
            raise ValueError(f"Scenario is not part of this campaign: {scenario_id}")
        return MonteCarloCampaign(
            self.project, self.root, self.master_seed, self.profile,
            self.campaign_id, self.config, scenario_id,
        )

    def ensure_samples(self, registry_path: Path | None, ensemble_size: int = 0) -> pd.DataFrame:
        """Generate the complete shared sample table exactly once."""
        return self.base.make_samples(registry_path, self.base.max_samples, ensemble_size)

    def write_manifest(self, status: str = "CREATED", **extra: Any) -> Path:
        """Grave o estado terminal ou intermediário de um cenário.

        Reúne ID, parâmetros compartilhados e detalhes de execução e publica
        o manifesto no diretório do cenário com escrita atômica.
        """
        manifest_path = _results_artifact_path(self.root, self.path / "manifest.json")
        if manifest_path.is_symlink():
            raise ValueError(f"Campaign manifest cannot be a symlink: {manifest_path}")
        previous: dict[str, Any] = {}
        if manifest_path.exists():
            try:
                previous = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                previous = {}
        payload = {
            "campaign_id": self.campaign_id,
            "project": self.project,
            "profile": self.profile,
            "scenario_ids": list(self.scenario_ids),
            "master_seed": self.master_seed,
            "requested_samples": self.base.target_samples,
            "min_samples": self.base.min_samples,
            "max_samples": self.base.max_samples,
            "shared_sample_table": str(self.samples_path.relative_to(self.path)),
            "sample_table_rows": int(len(pd.read_parquet(self.samples_path))) if self.samples_path.exists() else 0,
            "paired_realizations": True,
            "python": sys.version,
            "platform": platform.platform(),
            "git": _git_metadata(Path(self.root)),
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "status": status,
        }
        if previous.get("configuration_hashes"):
            payload["configuration_hashes"] = previous["configuration_hashes"]
        payload.update(extra)
        return write_json_atomic(payload, manifest_path)

    def scenario_manifests(self) -> dict[str, dict[str, Any]]:
        """Liste os manifestos de cenário disponíveis na campanha pai.

        Delega a consulta compartilhada e retorna os documentos salvos,
        sem reexecutar os cenários.
        """
        result: dict[str, dict[str, Any]] = {}
        for scenario_id in self.scenario_ids:
            campaign = self.scenario(scenario_id)
            manifest = campaign.path / "manifest.json"
            if manifest.exists():
                try:
                    result[scenario_id] = json.loads(manifest.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    result[scenario_id] = {"status": "FAILED"}
            else:
                result[scenario_id] = {"status": "NOT AVAILABLE"}
        return result

    def finalize_paired_comparison(self) -> dict[str, Any]:
        """Persist paired deltas and a compact comparison summary."""
        from antares_fd.analysis.scenario_uq import paired_comparison_statistics, paired_scenario_comparison

        frames: dict[str, pd.DataFrame] = {}
        for scenario_id in self.scenario_ids:
            output = self.scenario(scenario_id).path / "outputs.parquet"
            if output.exists():
                frames[scenario_id] = pd.read_parquet(output)
        comparison_dir = self.path / "paired_comparison"
        comparison_dir.mkdir(parents=True, exist_ok=True)
        paired = paired_scenario_comparison(frames)
        write_parquet_atomic(paired, comparison_dir / "paired_deltas.parquet")
        write_parquet_atomic(paired_comparison_statistics(paired), comparison_dir / "comparison_statistics.parquet")
        comparison_status = paired.get("comparison_status", pd.Series(dtype=str))
        if comparison_status.eq("PAIRED_COMMON_RANDOM_NUMBERS").any():
            status = "PAIRED_COMMON_RANDOM_NUMBERS"
        elif comparison_status.eq("PAIRED_COMMON_RANDOM_NUMBERS_PARTIAL").any():
            status = "PAIRED_COMMON_RANDOM_NUMBERS_PARTIAL"
        else:
            status = "UNPAIRED / NOT DIRECTLY COMPARABLE"
        summary = {
            "status": status,
            "scenario_ids": list(self.scenario_ids),
            "paired_case_count": int(len(paired)) if status.startswith("PAIRED_COMMON_RANDOM_NUMBERS") else 0,
            "artifacts": {
                "paired_deltas": "paired_comparison/paired_deltas.parquet",
                "comparison_statistics": "paired_comparison/comparison_statistics.parquet",
            },
        }
        write_json_atomic(summary, comparison_dir / "summary.json")
        return summary
