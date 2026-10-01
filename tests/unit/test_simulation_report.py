import json
from types import SimpleNamespace

import pytest
import pandas as pd

from antares_fd.simulation.report import (
    _summarize_metric,
    generate_latex_report,
)
from antares_fd.storage import read_jsonl_objects


def test_output_record_loader_preserves_valid_records_and_ignores_blank_lines(tmp_path):
    output = tmp_path / "mc_sim.outputs.txt"
    output.write_text(
        '\n{"apogee": 10}\n\n{"apogee": 20}\n',
        encoding="utf-8",
    )

    assert read_jsonl_objects(output) == [{"apogee": 10}, {"apogee": 20}]


def test_output_record_loader_reports_malformed_json_with_line_number(tmp_path):
    output = tmp_path / "mc_sim.outputs.txt"
    output.write_text('{"apogee": 10}\nnot-json\n', encoding="utf-8")

    with pytest.raises(ValueError, match=r"mc_sim\.outputs\.txt:2: invalid JSON"):
        read_jsonl_objects(output)


def test_output_record_loader_requires_json_objects(tmp_path):
    output = tmp_path / "mc_sim.outputs.txt"
    output.write_text(json.dumps([1, 2, 3]) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match=r"mc_sim\.outputs\.txt:1: expected a JSON object"):
        read_jsonl_objects(output)


@pytest.mark.parametrize(
    "record",
    ['{"apogee": NaN}', '{"apogee": Infinity}', '{"apogee": 1e999}'],
)
def test_output_record_loader_rejects_non_finite_numbers(tmp_path, record):
    output = tmp_path / "mc_sim.outputs.txt"
    output.write_text(record + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match=r"mc_sim\.outputs\.txt:1: non-finite"):
        read_jsonl_objects(output)


def test_output_record_loader_rejects_integer_outside_finite_float_range(tmp_path):
    output = tmp_path / "mc_sim.outputs.txt"
    output.write_text('{"apogee": ' + ("9" * 400) + "}\n", encoding="utf-8")

    with pytest.raises(ValueError, match=r"mc_sim\.outputs\.txt:1: non-finite"):
        read_jsonl_objects(output)


def test_report_writes_a_valid_latex_document_ending(tmp_path, monkeypatch):
    monkeypatch.setattr("antares_fd.simulation.report.subprocess.run", lambda *a, **k: None)

    generate_latex_report(SimpleNamespace(monte_carlo={}), tmp_path, "test_run")

    report = (tmp_path / "report_test_run.tex").read_text(encoding="utf-8")
    assert report.endswith("\\end{document}\n")


def test_report_discloses_valid_sample_count_for_each_metric(tmp_path, monkeypatch):
    monkeypatch.setattr("antares_fd.simulation.report.subprocess.run", lambda *a, **k: None)
    output = tmp_path / "mc_sim.outputs.txt"
    output.write_text(
        '{"apogee": 10}\n{"apogee": null}\n{"apogee": 20}\n',
        encoding="utf-8",
    )

    generate_latex_report(SimpleNamespace(monte_carlo={}), tmp_path, "test_run")

    report = (tmp_path / "report_test_run.tex").read_text(encoding="utf-8")
    assert "Parameter} & \\textbf{N} & \\textbf{Mean}" in report
    assert "Apogee & 2 & 15.00 & 7.07" in report


def test_report_rejects_overflowed_statistics(tmp_path, monkeypatch):
    monkeypatch.setattr("antares_fd.simulation.report.subprocess.run", lambda *a, **k: None)
    output = tmp_path / "mc_sim.outputs.txt"
    output.write_text('{"apogee": 1.7e308}\n{"apogee": -1.7e308}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="summary statistics overflow"):
        generate_latex_report(SimpleNamespace(monte_carlo={}), tmp_path, "test_run")


def test_metric_summary_avoids_intermediate_overflow_for_large_values():
    count, mean, standard_deviation = _summarize_metric(
        pd.Series([1e308, 1e308]), "apogee"
    )

    assert count == 2
    assert mean == 1e308
    assert standard_deviation == 0


def test_metric_summary_rejects_list_values_with_clear_error():
    with pytest.raises(ValueError, match="contains a non-numeric value"):
        _summarize_metric(pd.Series([[1, 2]]), "apogee")


def test_text_fallback_discloses_valid_sample_count(tmp_path, monkeypatch):
    def no_latex(*args, **kwargs):
        raise FileNotFoundError("pdflatex unavailable")

    monkeypatch.setattr("antares_fd.simulation.report.subprocess.run", no_latex)
    output = tmp_path / "mc_sim.outputs.txt"
    output.write_text('{"apogee": 10}\n{"apogee": null}\n{"apogee": 20}\n', encoding="utf-8")

    generate_latex_report(SimpleNamespace(monte_carlo={}), tmp_path, "test_run")

    report = (tmp_path / "report_test_run.txt").read_text(encoding="utf-8")
    assert "Apogee: N = 2 | Mean = 15.00 | Std Dev = 7.07" in report
