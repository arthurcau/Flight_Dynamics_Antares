"""Fixtures de workspace para testar a estação sem alterar projetos da equipe."""
from pathlib import Path
import shutil

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def engineering_workspace(tmp_path):
    """Copie o modelo congelado de referência e configure uma atmosfera determinística."""
    project = tmp_path / "projects/reference"
    for name in ("config", "aero", "motors"):
        shutil.copytree(ROOT / "tests/fixtures/reference_project" / name, project / name)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/GUI.md").write_text("# Guia local de teste\n")
    (tmp_path / "catalog").mkdir()
    (tmp_path / "catalog/datasets.yaml").write_text("schema_version: 1\ndatasets: []\n")
    return tmp_path


@pytest.fixture
def write_project_config():
    """Forneça edição de YAML restrita ao workspace temporário de cada teste."""
    def write(root, name, document):
        path = root / "projects/reference/config" / (name + ".yaml")
        path.write_text(yaml.safe_dump(document, sort_keys=False))
    return write
