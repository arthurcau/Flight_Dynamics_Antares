import pytest

from antares_fd.storage import read_jsonl_objects


def test_jsonl_reader_preserves_object_order_and_skips_blank_lines(tmp_path):
    path = tmp_path / "outputs.jsonl"
    path.write_text('\n{"case": 1}\n\n{"case": 2}\n', encoding="utf-8")

    assert read_jsonl_objects(path) == [{"case": 1}, {"case": 2}]


def test_jsonl_reader_fails_with_source_line_for_malformed_row(tmp_path):
    path = tmp_path / "outputs.jsonl"
    path.write_text('{"case": 1}\nnot-json\n', encoding="utf-8")

    with pytest.raises(ValueError, match=r"outputs\.jsonl:2: invalid JSON"):
        read_jsonl_objects(path)


def test_jsonl_reader_rejects_non_objects_and_nonfinite_values(tmp_path):
    path = tmp_path / "outputs.jsonl"
    path.write_text('[1, 2]\n', encoding="utf-8")
    with pytest.raises(ValueError, match=r"outputs\.jsonl:1: expected a JSON object"):
        read_jsonl_objects(path)

    path.write_text('{"metric": NaN}\n', encoding="utf-8")
    with pytest.raises(ValueError, match=r"outputs\.jsonl:1: non-finite"):
        read_jsonl_objects(path)


def test_jsonl_reader_can_explicitly_allow_a_missing_file(tmp_path):
    path = tmp_path / "missing.jsonl"
    assert read_jsonl_objects(path, missing_ok=True) == []
    with pytest.raises(FileNotFoundError):
        read_jsonl_objects(path)
