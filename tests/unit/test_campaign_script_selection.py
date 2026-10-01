import os
from pathlib import Path

import pytest

from antares_fd.simulation import campaign
from antares_fd.simulation.campaign import select_campaign_scripts


def test_campaign_selects_only_declared_flight_entrypoints(tmp_path: Path) -> None:
    for name in ("nominal.py", "balistic.py", "monte_carlo.py", "monte_carlo_failure.py", "plot_flight_data.py", "separation_at_main_opening.py"):
        (tmp_path / name).touch()

    deterministic, stochastic = select_campaign_scripts(tmp_path)

    assert [path.name for path in deterministic] == ["nominal.py", "balistic.py"]
    assert [path.name for path in stochastic] == ["monte_carlo.py"]


def test_campaign_requires_nominal_instead_of_relabeling_failure(tmp_path: Path) -> None:
    (tmp_path / "balistic.py").touch()
    (tmp_path / "monte_carlo_failure.py").touch()

    with pytest.raises(FileNotFoundError, match="nominal.py"):
        select_campaign_scripts(tmp_path)


def test_campaign_prefers_canonical_ballistic_alias(tmp_path: Path) -> None:
    for name in ("nominal.py", "balistic.py", "ballistic.py"):
        (tmp_path / name).touch()
    deterministic, _ = select_campaign_scripts(tmp_path)
    assert [path.name for path in deterministic] == ["nominal.py", "ballistic.py"]


def test_campaign_restores_environment_after_failure(monkeypatch, tmp_path: Path) -> None:
    sentinels = {
        "ANTARES_CAMPAIGN_DIR": "outer-dir",
        "ANTARES_CAMPAIGN_ACTIVE": "outer-active",
        "ANTARES_CAMPAIGN_RUN_ID": "outer-run",
        "ANTARES_COMPACT_OUTPUTS": "0",
        "ANTARES_CURRENT_SCENARIO": "outer-scenario",
        "ANTARES_MC_SCENARIO": "outer-mc-scenario",
        "ANTARES_MC_TARGET": "outer-target",
        "ANTARES_MC_PROFILE": "outer-profile",
        "ANTARES_MC_WORKERS": "7",
        "ANTARES_MC_MAX": "outer-max",
    }
    for key, value in sentinels.items():
        monkeypatch.setenv(key, value)

    def fail_after_activation(_directory):
        for key in campaign.CAMPAIGN_ENVIRONMENT_KEYS:
            monkeypatch.setenv(key, "mutated")
        raise RuntimeError("simulated campaign failure")

    monkeypatch.setattr(campaign, "_run_project_campaign_impl", fail_after_activation)
    with pytest.raises(RuntimeError, match="simulated campaign failure"):
        campaign.run_project_campaign(tmp_path)
    assert {key: os.environ[key] for key in sentinels} == sentinels
