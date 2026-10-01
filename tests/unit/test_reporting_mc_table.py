import json

from antares_fd.reporting.tables import build_mc_output_table


def _table_text(table):
    return [
        [cell.getPlainText() for cell in row]
        for row in table._cellvalues
    ]


def test_mc_output_table_shows_per_metric_valid_count_without_zero_fallback(tmp_path):
    outputs = tmp_path / "mc_sim.outputs.txt"
    outputs.write_text(
        json.dumps({"apogee": 120.0, "max_mach_number": 0.6}) + "\n"
        + json.dumps({"max_mach_number": 0.7}) + "\n",
        encoding="utf-8",
    )

    rows = _table_text(build_mc_output_table(outputs))

    assert rows[0] == ["Variable", "N", "Mean", "Std", "P05", "P50", "P95"]
    assert rows[1] == ["Apogee AGL (m)", "1", "120.00", "N/A", "120.00", "120.00", "120.00"]
    assert rows[3][0] == "Max Mach (M)"
    assert rows[3][1] == "2"


def test_mc_output_table_does_not_hide_corrupt_jsonl_rows(tmp_path):
    outputs = tmp_path / "mc_sim.outputs.txt"
    outputs.write_text('{"apogee": 120}\ninvalid\n', encoding="utf-8")

    try:
        build_mc_output_table(outputs)
    except ValueError as exc:
        assert "mc_sim.outputs.txt:2: invalid JSON" in str(exc)
    else:
        raise AssertionError("corrupt Monte Carlo output should fail visibly")
