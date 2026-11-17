"""Regressões para contratos inválidos identificados na revisão completa."""

import datetime
from types import SimpleNamespace
from typing import get_type_hints
from unittest.mock import Mock

import numpy as np
import pytest
import yaml

from antares_fd.analysis.flight_metrics import FlightMetrics
from antares_fd.analysis.requirements import RequirementDB
from antares_fd.builders.recovery import add_recovery_system
from antares_fd.config.exceptions import ConfigurationError
from antares_fd.environment.atmosphere import AtmosphericProfile
from antares_fd.reporting.tables import create_standard_table
from antares_fd.simulation.statistics import calculate_covariance_ellipse


def profile(**changes):
    """Crie um perfil mínimo para isolar validações de forma e propriedade."""
    values = dict(
        altitude_asl_m=[0, 100], pressure_pa=[100000, 99000],
        temperature_k=[290, 289], wind_u_mps=[1, 2], wind_v_mps=[0, 0],
        source="test", source_type="fixture", model=None, run_time_utc=None,
        valid_time_utc=datetime.datetime.now(datetime.UTC),
        latitude_deg=0, longitude_deg=0, member_id=None,
    )
    return AtmosphericProfile(**(values | changes))


def test_profile_normalizes_lists_and_owns_read_only_vectors():
    """Alterar o array de origem não deve invalidar um perfil já validado."""
    source = np.array([0.0, 100.0])
    result = profile(altitude_asl_m=source, specific_humidity_kg_kg=[0.01, 0.009])
    source[1] = -100
    np.testing.assert_array_equal(result.altitude_asl_m, [0, 100])
    assert isinstance(result.specific_humidity_kg_kg, np.ndarray)
    with pytest.raises(ValueError, match="read-only"):
        result.pressure_pa[0] = -1


@pytest.mark.parametrize("bad", [1.0, [[0, 100]], [0, np.inf], [0, "bad"]])
def test_profile_rejects_bad_shape_or_values_as_configuration_error(bad):
    with pytest.raises(ConfigurationError):
        profile(altitude_asl_m=bad)


@pytest.mark.parametrize("x,y", [([0, np.nan], [1, 2]), ([0, 1], [1, np.inf]),
                                  ([[0, 1]], [[1, 2]]), (1.0, [1, 2])])
def test_covariance_ellipse_rejects_invalid_coordinates(x, y):
    with pytest.raises(ValueError):
        calculate_covariance_ellipse(x, y, 0.95)


def test_collinear_covariance_has_finite_nonnegative_dimensions():
    """Uma nuvem sobre uma reta deve gerar elipse degenerada, sem NaN."""
    x = np.linspace(-10, 10, 100)
    result = calculate_covariance_ellipse(x, 3 * x, 0.95)
    assert np.isfinite(result["width"])
    assert np.isfinite(result["height"])
    assert result["height"] >= 0
    assert result["height"] < 1e-5


@pytest.mark.parametrize("value,limit", [(np.nan, 5), (np.inf, 5), (5, np.inf),
                                         (5, np.nan), ("bad", 5)])
def test_nonfinite_requirements_are_not_evaluated(tmp_path, value, limit):
    path = tmp_path / "requirements.yaml"
    path.write_text(yaml.safe_dump({"requirements": {"R": {
        "metric": "apogee", "operator": "<=", "limit": limit,
        "source_type": "FORMAL_REQUIREMENT",
    }}}))
    result = RequirementDB(path).evaluate(SimpleNamespace(apogee=value))[0]
    assert result.status == "NOT EVALUATED"
    assert result.margin is None


def test_negative_requirement_margin_is_not_hidden_by_tolerance(tmp_path):
    path = tmp_path / "requirements.yaml"
    path.write_text(yaml.safe_dump({"requirements": {"R": {
        "metric": "apogee", "operator": ">=", "limit": 10,
        "tolerance": 100, "source_type": "FORMAL_REQUIREMENT",
    }}}))
    result = RequirementDB(path).evaluate(SimpleNamespace(apogee=9))[0]
    assert result.status == "VIOLATED"
    assert result.margin == -1


def test_standard_table_pads_ragged_rows_before_sizing():
    table = create_standard_table([["a", "b", "c"], ["x"], ["y", "z"]])
    assert table._ncols == 3
    assert all(len(row) == 3 for row in table._cellvalues)


def test_flight_metric_annotations_are_resolvable():
    assert get_type_hints(FlightMetrics)["timeseries"]


def recovery_device(**changes):
    """Crie um dispositivo mínimo de teste, sem simular um voo."""
    return dict(type="parachute", name="test", aerodynamics={"method": "cd_s", "cd_s": 1},
                trigger={"type": "apogee"}, deployment={"lag": 1}) | changes


@pytest.mark.parametrize("changes", [
    {"aerodynamics": {"method": "cd_s", "cd_s": np.nan}},
    {"aerodynamics": {"drag_coefficient": -1, "reference_area": -1}},
    {"sampling": {"rate": 0}}, {"deployment": {"lag": -1}},
    {"trigger": {"type": "altitude", "altitude": {"value": np.inf}}},
    {"sensor_model": {"pressure": {"noise_enabled": True, "time_correlation": 2}}},
])
def test_invalid_recovery_device_does_not_partially_modify_rocket(changes):
    rocket = Mock()
    config = {"enabled": True, "devices": [recovery_device(), recovery_device(**changes)]}
    with pytest.raises(ConfigurationError):
        add_recovery_system(rocket, config)
    rocket.add_parachute.assert_not_called()
