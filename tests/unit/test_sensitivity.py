import warnings

import pytest

from antares_fd.analysis.sensitivity import analyze_monte_carlo_sensitivity


def test_sensitivity_analysis_rejects_malformed_output_record(tmp_path):
    outputs = tmp_path / "mc_sim.outputs.txt"
    outputs.write_text('{"apogee": 100}\ncorrupt\n', encoding="utf-8")

    with pytest.raises(ValueError, match=r"mc_sim\.outputs\.txt:2: invalid JSON"):
        analyze_monte_carlo_sensitivity(outputs)


def test_sensitivity_analysis_rejects_unpaired_input_output_counts(tmp_path):
    outputs = tmp_path / "mc_sim.outputs.txt"
    inputs = tmp_path / "mc_sim.inputs.txt"
    outputs.write_text('{"apogee": 100}\n', encoding="utf-8")
    inputs.write_text('{"mass": 1}\n{"mass": 2}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="record counts differ: 2 inputs vs 1 outputs"):
        analyze_monte_carlo_sensitivity(outputs, inputs)


def test_sensitivity_analysis_reports_missing_explicit_input_file(tmp_path):
    outputs = tmp_path / "mc_sim.outputs.txt"
    inputs = tmp_path / "missing.inputs.txt"
    outputs.write_text('{"apogee": 100}\n', encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="missing.inputs.txt"):
        analyze_monte_carlo_sensitivity(outputs, inputs)


def test_sensitivity_uses_pairwise_valid_rows_and_reports_pair_count(tmp_path):
    outputs = tmp_path / "mc_sim.outputs.txt"
    inputs = tmp_path / "mc_sim.inputs.txt"
    outputs.write_text(
        '{"index":0,"apogee":10}\n{"index":1,"apogee":20}\n'
        '{"index":2,"apogee":30}\n{"index":3,"apogee":40}\n',
        encoding="utf-8",
    )
    inputs.write_text(
        '{"index":0,"mass":1}\n{"index":1,"mass":2}\n'
        '{"index":2,"mass":3}\n{"index":3,"mass":null}\n',
        encoding="utf-8",
    )

    result = analyze_monte_carlo_sensitivity(outputs, inputs, target_metric="apogee")
    mass = result["sensitivity_ranking"][0]
    assert mass["parameter"] == "mass"
    assert mass["sample_count"] == 3
    assert abs(mass["pearson_r"] - 1.0) < 1e-12


def test_sensitivity_rejects_nonnumeric_metric_instead_of_dropping_it(tmp_path):
    outputs = tmp_path / "mc_sim.outputs.txt"
    outputs.write_text('{"apogee":100}\n{"apogee":"bad"}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="non-numeric"):
        analyze_monte_carlo_sensitivity(outputs)


def test_sensitivity_summary_uses_overflow_safe_statistics(tmp_path):
    outputs = tmp_path / "mc_sim.outputs.txt"
    outputs.write_text('{"apogee":1e308}\n{"apogee":1e308}\n', encoding="utf-8")

    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        result = analyze_monte_carlo_sensitivity(outputs)
    summary = result["statistics"]["apogee"]
    assert summary["mean"] == 1e308
    assert summary["std"] == 0.0
