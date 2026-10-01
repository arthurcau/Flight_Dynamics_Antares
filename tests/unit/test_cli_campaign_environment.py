import os
from types import SimpleNamespace

import pytest

from antares_fd import cli


def test_mc_cli_restores_environment_and_records_failed_scenario(tmp_path, monkeypatch):
    project = tmp_path / "projects/fixture"
    (project / "config").mkdir(parents=True)
    writes = []
    child_writes = []
    campaigns = []

    class FakeCampaign:
        def __init__(self, project_name, root, seed, profile, **kwargs):
            self.project = project_name
            self.root = root
            self.master_seed = seed
            self.profile = profile
            self.target_samples = self.min_samples = self.max_samples = 2
            self.scenario_ids = tuple(kwargs["scenario_ids"])
            self.campaign_id = "campaign"
            self.path = root / "results" / project_name / self.campaign_id
            self.child_statuses = {scenario: {"status": "SAMPLING"} for scenario in self.scenario_ids}
            campaigns.append(self)

        def snapshot_config(self, _project_dir):
            return {"vehicle.yaml": "hash"}

        def ensure_samples(self, _registry):
            return [1, 2]

        def write_manifest(self, status, **extra):
            writes.append((status, extra))

        def finalize_paired_comparison(self):
            return {}

        def scenario(self, scenario_id):
            parent = self

            class FakeScenario:
                path = parent.path / "scenarios" / scenario_id

                def write_manifest(self, status, extra=None):
                    child_writes.append((scenario_id, status, extra or {}))
                    parent.child_statuses[scenario_id] = {"status": status, **(extra or {})}

            return FakeScenario()

        def scenario_manifests(self):
            return self.child_statuses

    monkeypatch.setattr(
        "antares_fd.config.load_project_config",
        lambda _path: SimpleNamespace(monte_carlo={"random_seed": 19}),
    )
    monkeypatch.setattr(
        "antares_fd.simulation.scenarios.scenario_ids",
        lambda _config: ("nominal", "ballistic"),
    )
    monkeypatch.setattr("antares_fd.simulation.uq_campaign.StochasticScenarioCampaign", FakeCampaign)

    calls = []

    def run_script(_project_dir):
        calls.append(os.environ["ANTARES_MC_SCENARIO"])
        if calls[-1] == "nominal":
            campaigns[0].child_statuses["nominal"] = {"status": "COMPLETE"}
        if calls[-1] == "ballistic":
            raise RuntimeError("synthetic scenario failure")

    monkeypatch.setattr(cli, "_run_script", run_script)
    sentinels = {key: f"prior:{key}" for key in cli.MC_CAMPAIGN_ENVIRONMENT_KEYS}
    for key, value in sentinels.items():
        monkeypatch.setenv(key, value)

    with pytest.raises(RuntimeError, match="synthetic scenario failure"):
        cli.main([
            "--repo-root", str(tmp_path), "mc", "fixture", "--profile", "debug",
            "--workers", "3", "--all-scenarios",
        ])

    assert {key: os.environ[key] for key in sentinels} == sentinels
    assert writes[-1][0] == "PARTIAL"
    assert writes[-1][1]["completed_scenario_ids"] == ["nominal"]
    assert writes[-1][1]["failed_scenario_id"] == "ballistic"
    assert writes[-1][1]["failure_phase"] == "scenario_execution"
    assert writes[-1][1]["failure"]["type"] == "RuntimeError"
    assert writes[-1][1]["scenario_summaries"]["ballistic"]["status"] == "FAILED"
    assert child_writes == [("ballistic", "FAILED", {"failure": writes[-1][1]["failure"], "failure_phase": "scenario_execution"})]


def test_mc_cli_marks_single_nominal_campaign_complete(tmp_path, monkeypatch):
    project = tmp_path / "projects/fixture"
    (project / "config").mkdir(parents=True)
    writes = []

    class FakeCampaign:
        def __init__(self, project_name, root, seed, profile, **kwargs):
            self.profile = profile
            self.target_samples = self.min_samples = self.max_samples = 1
            self.campaign_id = "campaign"
            self.path = root / "results" / project_name / self.campaign_id

        def snapshot_config(self, _project_dir):
            return {"vehicle.yaml": "hash"}

        def ensure_samples(self, _registry):
            return [1]

        def write_manifest(self, status, **extra):
            writes.append((status, extra))

        def finalize_paired_comparison(self):
            raise AssertionError("single-scenario run must not finalize paired comparison")

        def scenario_manifests(self):
            return {"nominal": {"status": "COMPLETE"}}

    monkeypatch.setattr(
        "antares_fd.config.load_project_config",
        lambda _path: SimpleNamespace(monte_carlo={"random_seed": 19}),
    )
    monkeypatch.setattr("antares_fd.simulation.scenarios.scenario_ids", lambda _config: ("nominal",))
    monkeypatch.setattr("antares_fd.simulation.uq_campaign.StochasticScenarioCampaign", FakeCampaign)
    monkeypatch.setattr(cli, "_run_script", lambda _project_dir: None)

    assert cli.main(["--repo-root", str(tmp_path), "mc", "fixture", "--profile", "debug"]) == 0
    assert [status for status, _ in writes] == ["SAMPLING", "COMPLETE"]
    assert writes[-1][1]["paired_comparison"] is None
    assert writes[-1][1]["scenario_summaries"] == {"nominal": {"status": "COMPLETE"}}


def test_mc_cli_writes_failed_manifest_if_sampling_fails(tmp_path, monkeypatch):
    project = tmp_path / "projects/fixture"
    (project / "config").mkdir(parents=True)
    writes = []

    class FakeCampaign:
        def __init__(self, project_name, root, seed, profile, **kwargs):
            self.profile = profile
            self.target_samples = self.min_samples = self.max_samples = 1
            self.campaign_id = "campaign"
            self.path = root / "results" / project_name / self.campaign_id

        def snapshot_config(self, _project_dir):
            return {"vehicle.yaml": "hash"}

        def ensure_samples(self, _registry):
            raise OSError("synthetic sample write failure")

        def write_manifest(self, status, **extra):
            writes.append((status, extra))

        def scenario_manifests(self):
            return {"nominal": {"status": "NOT AVAILABLE"}}

    monkeypatch.setattr(
        "antares_fd.config.load_project_config",
        lambda _path: SimpleNamespace(monte_carlo={"random_seed": 19}),
    )
    monkeypatch.setattr("antares_fd.simulation.scenarios.scenario_ids", lambda _config: ("nominal",))
    monkeypatch.setattr("antares_fd.simulation.uq_campaign.StochasticScenarioCampaign", FakeCampaign)
    monkeypatch.setattr(cli, "_run_script", lambda _project_dir: pytest.fail("runner called after sample failure"))

    with pytest.raises(OSError, match="synthetic sample write failure"):
        cli.main(["--repo-root", str(tmp_path), "mc", "fixture", "--profile", "debug"])

    assert [status for status, _ in writes] == ["FAILED"]
    assert writes[-1][1]["failure_phase"] == "sample_preparation"
    assert writes[-1][1]["failure"]["type"] == "OSError"


def test_archive_cli_refuses_missing_manifest_without_creating_archive_path(tmp_path):
    (tmp_path / "projects/fixture").mkdir(parents=True)
    with pytest.raises(SystemExit, match="Campaign manifest not found"):
        cli.main([
            "--repo-root", str(tmp_path), "archive", "missing", "--project", "fixture",
        ])

    assert not (tmp_path / "results/fixture/missing").exists()


def test_archive_cli_rejects_campaign_path_traversal(tmp_path):
    (tmp_path / "projects/fixture").mkdir(parents=True)
    with pytest.raises(SystemExit) as error:
        cli.main([
            "--repo-root", str(tmp_path), "archive", "../escape", "--project", "fixture",
        ])
    assert error.value.code == 2
    assert not (tmp_path / "escape").exists()


def test_resume_cli_rejects_campaign_path_traversal(tmp_path, monkeypatch):
    (tmp_path / "projects/fixture/config").mkdir(parents=True)
    monkeypatch.setattr(
        "antares_fd.config.load_project_config",
        lambda _path: SimpleNamespace(monte_carlo={"random_seed": 19}),
    )

    with pytest.raises(SystemExit) as error:
        cli.main([
            "--repo-root", str(tmp_path), "mc", "fixture", "--resume", "../escape",
        ])
    assert error.value.code == 2
    assert not (tmp_path / "results/escape").exists()
