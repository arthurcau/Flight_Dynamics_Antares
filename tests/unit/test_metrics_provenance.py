from pathlib import Path
from types import SimpleNamespace

import pytest

from antares_fd.analysis.metrics import extract_flight_metrics


def test_metrics_never_labels_unproven_landing_coordinates_as_field_validation() -> None:
    def constant(value):
        return lambda _time: value

    environment = SimpleNamespace(
        elevation=100.0,
        latitude=-21.0,
        longitude=-48.0,
        atmospheric_model_type="custom_atmosphere",
        antares_atmosphere={"altitude_bounds_asl_m": [100.0, 250.0]},
        wind_velocity_x=constant(1.0),
        wind_velocity_y=constant(2.0),
        density=constant(1.1),
        speed_of_sound=constant(340.0),
    )
    motor = SimpleNamespace(
        burn_out_time=1.0,
        burn_start_time=0.0,
        thrust=lambda time: 100.0 if time < 1.0 else 0.0,
        name="test motor",
        total_impulse=100.0,
        average_thrust=100.0,
        max_thrust=100.0,
        propellant_initial_mass=1.0,
    )
    rocket = SimpleNamespace(
        name="test rocket",
        motor=motor,
        total_mass=lambda time: 10.0 - 0.1 * min(time, 1.0),
        center_of_mass=constant(0.4),
        cp_position=constant(0.5),
    )
    flight = SimpleNamespace(
        rocket=rocket,
        env=environment,
        name="synthetic test flight",
        out_of_rail_time=0.5,
        out_of_rail_velocity=30.0,
        apogee_time=2.0,
        t_final=3.0,
        parachute_events=[],
        z=lambda time: 100.0 + 100.0 * min(time, 2.0),
        x=lambda time: 2.0 * time,
        y=lambda time: time,
        vz=lambda time: 100.0 if time <= 2.0 else -20.0,
        speed=lambda time: abs(100.0 if time <= 2.0 else -20.0),
        mach_number=lambda time: abs(100.0 if time <= 2.0 else -20.0) / 340.0,
        ax=constant(0.0),
        ay=constant(0.0),
        az=constant(10.0),
        dynamic_pressure=lambda time: 100.0 * time,
        angle_of_attack=constant(0.01),
        static_margin=constant(0.5),
    )

    metrics = extract_flight_metrics(
        flight, project_dir=Path("/repo/projects/neblina_1"),
    )

    assert metrics.validation is None
    assert metrics.atmosphere.coverage_status == "PROFILE_LIMITED_TO_DECLARED_COVERAGE"
    assert metrics.atmosphere.coverage_bounds_asl_m == (100.0, 250.0)
    assert metrics.atmosphere.density.min() == pytest.approx(1.1)

