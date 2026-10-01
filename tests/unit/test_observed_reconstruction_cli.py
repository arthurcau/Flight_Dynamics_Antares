from __future__ import annotations

from pathlib import Path

from antares_fd import cli


def test_telemetry_process_uses_declared_marker_and_explicit_audit(tmp_path: Path, monkeypatch, capsys) -> None:
    project = tmp_path / "projects" / "fixture" / "telemetry" / "metadata"
    project.mkdir(parents=True)
    (project / "dataset.yaml").write_text("section_markers: [FLIGHT]\n", encoding="utf-8")
    fake_cli = tmp_path / "source" / "antares_fd" / "cli.py"
    fake_cli.parent.mkdir(parents=True)
    fake_cli.touch()
    monkeypatch.setattr(cli, "__file__", str(fake_cli))
    calls = {}

    def fake_process(audit, *, repo_root, section_marker, output_dir):
        calls.update(audit=audit, repo_root=repo_root, section_marker=section_marker, output_dir=output_dir)
        return tmp_path / "results" / "processed"

    monkeypatch.setattr("antares_fd.reconstruction.artifacts.process_audit_section", fake_process)
    result = cli.main(["telemetry", "process", "fixture", "--audit", "audit-input"])

    assert result == 0
    assert calls["section_marker"] == "FLIGHT"
    assert calls["audit"] == Path("audit-input")
    assert "processed" in capsys.readouterr().out
