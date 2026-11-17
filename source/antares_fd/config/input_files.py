"""Resolve project-local files that directly affect flight model execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def _project_file(project_dir: Path, relative: Any) -> Path:
    """Resolva uma referência de entrada dentro do diretório do projeto.

    Normaliza relative e verifica contenção e existência do arquivo. Retorna
    Path ou lança ValueError ou FileNotFoundError, evitando snapshots de caminhos externos.
    """
    if not isinstance(relative, str) or not relative.strip():
        raise ValueError("Model input path must be nonempty relative text")
    project_root = project_dir.resolve()
    path = (project_root / relative).resolve()
    if not path.is_relative_to(project_root):
        raise ValueError(f"Model input is outside project: {relative}")
    if not path.is_file():
        raise FileNotFoundError(f"Model input is missing: {relative}")
    return path


def _mapping(path: Path) -> dict[str, Any]:
    """Leia um documento YAML que deve conter um mapeamento.

    Usa safe_load no arquivo path e rejeita estruturas incompatíveis. O retorno
    é usado apenas para descobrir entradas referenciadas pelo modelo.
    """
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(value, dict):
        raise ValueError(f"Model configuration must contain a mapping: {path}")
    return value


def collect_project_model_inputs(project_dir: Path) -> tuple[Path, ...]:
    """List config YAML plus the configured thrust and file-backed drag curves.

    Paths are resolved within the project directory. A referenced symlink may
    point within the project, but references that resolve outside it are
    rejected so snapshots remain portable and bounded.
    """
    project_root = Path(project_dir).resolve()
    config_dir = project_root / "config"
    yaml_files = sorted(
        _project_file(project_root, path.relative_to(project_root).as_posix())
        for path in config_dir.glob("*.yaml")
    )
    if not yaml_files:
        raise FileNotFoundError(f"No YAML configuration files in {config_dir}")

    inputs = set(yaml_files)
    motor_path = config_dir / "motor.yaml"
    if motor_path.is_file():
        motor = _mapping(motor_path)
        motor = motor.get("motor", motor)
        if not isinstance(motor, dict):
            raise ValueError(f"Motor configuration must contain a mapping: {motor_path}")
        if motor.get("thrust_source"):
            inputs.add(_project_file(project_root, motor["thrust_source"]))

    vehicle_path = config_dir / "vehicle.yaml"
    if vehicle_path.is_file():
        vehicle = _mapping(vehicle_path)
        vehicle = vehicle.get("vehicle", vehicle)
        if not isinstance(vehicle, dict):
            raise ValueError(f"Vehicle configuration must contain a mapping: {vehicle_path}")
        drag = vehicle.get("drag", {})
        if not isinstance(drag, dict):
            raise ValueError(f"Vehicle drag configuration must contain a mapping: {vehicle_path}")
        for mode in ("power_on", "power_off"):
            entry = drag.get(mode, {})
            if not isinstance(entry, dict):
                raise ValueError(f"Vehicle {mode} drag configuration must contain a mapping: {vehicle_path}")
            if entry.get("source_type") == "file":
                inputs.add(_project_file(project_root, entry.get("file")))

    return tuple(sorted(inputs))
