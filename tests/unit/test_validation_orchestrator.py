"""Injected environments let archived profiles replay without MAGI I/O."""

from types import SimpleNamespace

from antares_fd.simulation import orchestrator


def test_execute_scenario_uses_explicit_environment(monkeypatch, tmp_path):
    config = SimpleNamespace(vehicle={}, motor={}, recovery={}, launch={}, simulation={}, environment={})
    environment = object()
    calls = []

    def forbidden_environment(*args):
        raise AssertionError("MAGI build must be bypassed for archived profile replay")

    monkeypatch.setattr(orchestrator, "build_environment", forbidden_environment)
    monkeypatch.setattr(orchestrator, "build_motor", lambda *args: object())
    monkeypatch.setattr(orchestrator, "build_vehicle", lambda *args: object())
    monkeypatch.setattr(orchestrator, "add_recovery_system", lambda *args: None)

    def fake_run(rocket, selected_environment, launch, simulation):
        calls.append(selected_environment)
        return object()

    monkeypatch.setattr(orchestrator, "run_flight", fake_run)
    orchestrator.execute_scenario(
        config, tmp_path, print_summary=False, environment=environment,
    )
    assert calls == [environment]
