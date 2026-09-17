"""
Unit tests for Antares Flight Dynamics Analysis, Compliance, Provenance and PDF Reporting.
"""

from pathlib import Path
import numpy as np
import pytest

from antares_fd.analysis.compliance import evaluate_compliance, ComplianceItem
from antares_fd.analysis.provenance import collect_reproducibility_data, evaluate_model_validity
from antares_fd.analysis.sensitivity import analyze_monte_carlo_sensitivity
from antares_fd.reporting.pdf_report import FlightDynamicsReport


def test_compliance_evaluation_pass():
    metrics = {
        "rail_dynamics": {
            "rail_exit_velocity_ms": 32.5,
            "crosswind_ratio": 5.2,
            "crosswind_speed_ms": 6.2,
        },
        "mass_and_stability": {
            "static_margin_rail_exit_cal": 2.4,
            "static_margin_burnout_cal": 3.1,
            "static_margin_min_burn_cal": 1.8,
        },
        "aerodynamic_loads": {
            "max_dynamic_pressure_pa": 24000.0,
            "static_margin_at_max_q_cal": 2.2,
        },
        "kinematics": {
            "max_mach": 0.67,
            "max_ascent_acceleration_g": 12.8,
        },
        "timeline": {
            "apogee_s": 23.5,
        },
        "recovery": {
            "drogue": {"trigger_time": 23.6},
            "main_deploy_shock_g": 34.0,
            "touchdown_velocity_ms": 6.8,
            "touchdown_kinetic_energy_j": 750.0,
        },
    }

    items = evaluate_compliance(metrics)
    assert len(items) >= 10

    # Ensure all have valid Requirement IDs and sources
    for item in items:
        assert item.req_id.startswith(("FD-REQ-", "STR-REQ-", "AER-REQ-", "REC-REQ-"))
        assert len(item.source) > 0
        assert item.classification in ["FORMAL REQUIREMENT", "ENGINEERING GUIDELINE"]

    # Verify all items pass
    assert all(i.status == "SATISFIED" for i in items)


def test_compliance_evaluation_flags():
    metrics = {
        "rail_dynamics": {
            "rail_exit_velocity_ms": 22.0,  # Below 25 m/s -> CRITICAL FLAG
            "crosswind_ratio": 2.1,        # Below 2.5 -> CRITICAL FLAG
            "crosswind_speed_ms": 10.5,
        },
        "mass_and_stability": {
            "static_margin_rail_exit_cal": 0.7,  # Below 1.0 -> CRITICAL FLAG
            "static_margin_burnout_cal": 0.9,
            "static_margin_min_burn_cal": 0.6,
        },
        "aerodynamic_loads": {
            "max_dynamic_pressure_pa": 60000.0,  # > 50 kPa -> CRITICAL FLAG
            "static_margin_at_max_q_cal": 0.9,
        },
        "kinematics": {
            "max_mach": 0.85,
            "max_ascent_acceleration_g": 24.5,   # > 22 g -> CRITICAL FLAG
        },
        "timeline": {
            "apogee_s": 20.0,
        },
        "recovery": {
            "drogue": {"trigger_time": 24.0},
            "main_deploy_shock_g": 55.0,         # > 50 g -> CRITICAL FLAG
            "touchdown_velocity_ms": 14.2,       # > 11 m/s -> CRITICAL FLAG
            "touchdown_kinetic_energy_j": 2800.0,
        },
    }

    items = evaluate_compliance(metrics)
    status_map = {i.req_id: i.status for i in items}
    assert status_map["FD-REQ-001"] == "CRITICAL FLAG"
    assert status_map["FD-REQ-003"] == "CRITICAL FLAG"
    assert status_map["STR-REQ-012"] == "CRITICAL FLAG"
    assert status_map["REC-REQ-003"] == "CRITICAL FLAG"


def test_reproducibility_data_collection(tmp_path):
    # Test provenance data collection on a dummy project directory
    proj_dir = tmp_path / "test_proj"
    config_dir = proj_dir / "config"
    config_dir.mkdir(parents=True)

    dummy_cfg = config_dir / "vehicle.yaml"
    dummy_cfg.write_text("name: TestRocket\nmass: 20.0\n")

    repro = collect_reproducibility_data(proj_dir)
    assert "git" in repro
    assert "environment" in repro
    assert "vehicle.yaml" in repro["config_hashes"]
    assert len(repro["input_quality"]) >= 5


def test_model_validity_bounds():
    metrics = {
        "kinematics": {"max_mach": 0.67},
        "aerodynamic_loads": {"max_angle_of_attack_ascent_deg": 1.5},
        "trajectory": {"apogee_asl_m": 3100.0},
        "rail_dynamics": {"rail_exit_velocity_ms": 32.0},
    }
    checks = evaluate_model_validity(metrics)
    assert len(checks) == 4
    for c in checks:
        assert c["status"] == "QUALIFIED"


def test_monte_carlo_sensitivity_analysis(tmp_path):
    outputs_file = tmp_path / "mc_sim.outputs.txt"
    inputs_file = tmp_path / "mc_sim.inputs.txt"

    import json
    np.random.seed(42)
    n_samples = 40

    with open(inputs_file, "w") as f_in, open(outputs_file, "w") as f_out:
        for _ in range(n_samples):
            mass = float(np.random.normal(30.0, 2.0))
            impulse = float(np.random.normal(5000.0, 50.0))
            f_in.write(json.dumps({"rocket_dry_mass": mass, "motor_total_impulse": impulse}) + "\n")

            # Apogee strongly positively correlated with impulse, negatively with mass
            apogee = 3000.0 + 1.0 * (impulse - 5000.0) - 80.0 * (mass - 30.0) + float(np.random.normal(0, 2))
            f_out.write(json.dumps({
                "apogee": apogee,
                "out_of_rail_velocity": 32.0,
                "max_mach_number": 0.65,
                "impact_velocity": 6.5,
                "x_impact": 100.0,
                "y_impact": 200.0,
            }) + "\n")

    res = analyze_monte_carlo_sensitivity(outputs_file, inputs_file, target_metric="apogee")
    assert res["num_cases"] == n_samples
    assert "statistics" in res
    assert "apogee" in res["statistics"]

    ranking = res["sensitivity_ranking"]
    assert len(ranking) == 2
    param_r = {r["parameter"]: r["pearson_r"] for r in ranking}
    assert param_r["motor_total_impulse"] > 0.1
    assert param_r["rocket_dry_mass"] < -0.5
