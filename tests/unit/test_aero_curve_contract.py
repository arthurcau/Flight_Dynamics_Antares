from pathlib import Path

import pandas as pd
import pytest

from antares_fd.reconstruction.aero import CurveSpec, load_cd_curve, compare_cd_curves


def _curve(path: Path, values: list[tuple[float, float]]) -> None:
    pd.DataFrame(values, columns=["mach", "Cd"]).to_csv(path, index=False)


def test_curve_comparison_uses_only_shared_mach_domain_and_matching_area(tmp_path: Path) -> None:
    current = tmp_path / "current.csv"
    external = tmp_path / "external.csv"
    _curve(current, [(0, 0.4), (1, 0.6)])
    _curve(external, [(0.5, 0.5), (1.5, 0.7)])
    spec_a = CurveSpec("current", "CURRENT_MODEL", "power_off", 0.02, "project config", "N1", "zero_aoa_re1e6")
    spec_b = CurveSpec("candidate", "OPENROCKET", "power_off", 0.02, "exported 2026-09-26", "N1", "zero_aoa_re1e6")
    comparison = compare_cd_curves(load_cd_curve(current, spec_a), load_cd_curve(external, spec_b))
    assert comparison["mach"].tolist() == [0.5, 1.0]
    assert comparison["candidate_minus_current_cd"].tolist() == pytest.approx([0.0, 0.0])


def test_curve_comparison_rejects_different_reference_areas(tmp_path: Path) -> None:
    path = tmp_path / "curve.csv"
    _curve(path, [(0, 0.4), (1, 0.6)])
    first = load_cd_curve(path, CurveSpec("a", "CURRENT_MODEL", "power_off", 0.02, "source", "N1", "condition-a"))
    second = load_cd_curve(path, CurveSpec("b", "CFD", "power_off", 0.03, "mesh report", "N1", "condition-a"))
    with pytest.raises(ValueError, match="reference areas"):
        compare_cd_curves(first, second)


def test_curve_contract_rejects_missing_provenance_and_nonmonotonic_mach(tmp_path: Path) -> None:
    path = tmp_path / "curve.csv"
    _curve(path, [(1, 0.6), (0, 0.4)])
    with pytest.raises(ValueError, match="increasing"):
        load_cd_curve(path, CurveSpec("bad", "RASAERO", "power_on", 0.02, "export", "N1", "condition-a"))
    with pytest.raises(ValueError, match="provenance"):
        load_cd_curve(path, CurveSpec("bad", "RASAERO", "power_on", 0.02, "", "N1", "condition-a"))


def test_curve_comparison_requires_matching_geometry_and_conditions(tmp_path: Path) -> None:
    path = tmp_path / "curve.csv"
    _curve(path, [(0, 0.4), (1, 0.6)])
    first = load_cd_curve(path, CurveSpec("a", "CURRENT_MODEL", "power_off", 0.02, "source", "N1", "condition-a"))
    different_geometry = load_cd_curve(path, CurveSpec("b", "CFD", "power_off", 0.02, "mesh report", "N2", "condition-a"))
    different_conditions = load_cd_curve(path, CurveSpec("c", "CFD", "power_off", 0.02, "mesh report", "N1", "condition-b"))
    with pytest.raises(ValueError, match="geometry"):
        compare_cd_curves(first, different_geometry)
    with pytest.raises(ValueError, match="condition"):
        compare_cd_curves(first, different_conditions)


def test_flight_derived_curve_is_rejected_without_an_identification_contract(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="source"):
        CurveSpec("flight", "FLIGHT_DERIVED", "power_off", 0.02, "telemetry", "N1", "condition-a")


def test_curve_values_and_hash_come_from_the_same_read(tmp_path: Path, monkeypatch) -> None:
    import hashlib
    import io

    path = tmp_path / "curve.csv"
    original = b"mach,Cd\n0,0.4\n1,0.6\n"
    path.write_bytes(original)
    real_read_bytes = Path.read_bytes

    def replace_after_read(target):
        result = real_read_bytes(target)
        target.write_text("mach,Cd\n0,9\n1,9\n", encoding="utf-8")
        return result

    real_read_csv = pd.read_csv
    seen_buffer = []

    def capture(buffer, *args, **kwargs):
        seen_buffer.append(buffer)
        return real_read_csv(buffer, *args, **kwargs)

    monkeypatch.setattr(Path, "read_bytes", replace_after_read)
    monkeypatch.setattr(pd, "read_csv", capture)
    curve = load_cd_curve(
        path, CurveSpec("current", "CURRENT_MODEL", "power_off", 0.02, "source", "N1", "condition-a")
    )
    assert isinstance(seen_buffer[0], io.BytesIO)
    assert curve.source_sha256 == hashlib.sha256(original).hexdigest()
    assert curve.points["Cd"].tolist() == [0.4, 0.6]
