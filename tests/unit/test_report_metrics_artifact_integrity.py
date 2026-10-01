import json

import pytest

from antares_fd.reporting.pdf_report import _load_artifact_metrics


def test_metrics_artifact_loader_accepts_complete_object(tmp_path):
    path = tmp_path / "metrics.json"
    path.write_text(json.dumps({"apogee_agl": 123.0}), encoding="utf-8")
    assert _load_artifact_metrics(path) == {"apogee_agl": 123.0}


def test_metrics_artifact_loader_rejects_truncated_or_non_object_json(tmp_path):
    path = tmp_path / "metrics.json"
    path.write_text('{"apogee_agl":', encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        _load_artifact_metrics(path)
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON object"):
        _load_artifact_metrics(path)
