from __future__ import annotations

from pathlib import Path

from antares_fd import cli

from test_telemetry import _write_project_fixture


def test_cli_audits_project_metadata_and_prints_artifact_directory(tmp_path: Path, monkeypatch, capsys) -> None:
    _project, _source, output_dir = _write_project_fixture(tmp_path)
    fake_cli_file = tmp_path / "source" / "antares_fd" / "cli.py"
    fake_cli_file.parent.mkdir(parents=True)
    fake_cli_file.write_text("", encoding="utf-8")
    monkeypatch.setattr(cli, "__file__", str(fake_cli_file))

    result = cli.main(["telemetry", "audit", "fixture", "--output", str(output_dir)])

    assert result == 0
    assert output_dir.is_dir()
    assert str(output_dir) in capsys.readouterr().out
