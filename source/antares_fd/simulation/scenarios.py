"""Canonical mission scenarios and explicit recovery overrides.

Scenario definitions live here so deterministic simulations, stochastic
campaigns, metrics and reports use the same identifiers and the same physical
configuration changes.  The functions mutate only a deep copy of the loaded
project configuration.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Callable


NOMINAL = "nominal"
MAIN_AT_APOGEE = "main_at_apogee"
ONLY_REEFING = "only_reefing"
BALLISTIC = "ballistic"
DROGUE_ONLY = "drogue_only"

REQUIRED_SCENARIOS = (NOMINAL, MAIN_AT_APOGEE, ONLY_REEFING)
# Project recovery configuration uses the drogue CdS as the reefed effective
# area.  Keep this factor explicit so it is traceable in scenario artifacts.
REEFED_CDS_FACTOR = 0.15


@dataclass(frozen=True)
class ScenarioDefinition:
    scenario_id: str
    title: str
    recovery_description: str
    failure_event: str
    applies_after_ascent: bool
    override: Callable[[dict[str, Any]], None]


def _devices(recovery: dict[str, Any]) -> list[dict[str, Any]]:
    return recovery.setdefault("devices", [])


def _nominal(recovery: dict[str, Any]) -> None:
    return None


def _main_at_apogee(recovery: dict[str, Any]) -> None:
    for device in _devices(recovery):
        device_id = str(device.get("id", "")).lower()
        if device_id == "drogue":
            device["enabled"] = False
        elif device_id == "main":
            device["enabled"] = True
            trigger = device.setdefault("trigger", {})
            trigger["type"] = "apogee"
            trigger.setdefault("apogee", {})["enabled"] = True
            device["name"] = "Main Parachute (At Apogee)"


def _only_reefing(recovery: dict[str, Any]) -> None:
    """Keep the existing two-stage implementation explicit.

    The project represents the reefed state with the drogue device at apogee
    and the fully open main device at the configured main altitude.  The CdS
    reduction is read from the configured main parachute and is therefore part
    of the scenario definition rather than report logic.
    """
    main_cd_s = None
    for device in _devices(recovery):
        if str(device.get("id", "")).lower() == "main":
            main_cd_s = device.get("aerodynamics", {}).get("cd_s")
            device["enabled"] = True
            device["name"] = "Main Parachute (Disreefed)"
    for device in _devices(recovery):
        if str(device.get("id", "")).lower() == "drogue":
            device["enabled"] = True
            device["name"] = "Main Parachute (Reefed)"
            trigger = device.setdefault("trigger", {})
            trigger["type"] = "apogee"
            trigger.setdefault("apogee", {})["enabled"] = True
            if main_cd_s is not None:
                device.setdefault("aerodynamics", {})["cd_s"] = float(main_cd_s) * REEFED_CDS_FACTOR


def _ballistic(recovery: dict[str, Any]) -> None:
    recovery["enabled"] = False
    for device in _devices(recovery):
        device["enabled"] = False


def _drogue_only(recovery: dict[str, Any]) -> None:
    for device in _devices(recovery):
        device["enabled"] = str(device.get("id", "")).lower() == "drogue"


SCENARIOS: dict[str, ScenarioDefinition] = {
    NOMINAL: ScenarioDefinition(NOMINAL, "Nominal Flight", "Configured drogue then main recovery sequence.", "none", False, _nominal),
    MAIN_AT_APOGEE: ScenarioDefinition(MAIN_AT_APOGEE, "Main Parachute at Apogee", "Drogue disabled; main parachute triggers at apogee.", "apogee", True, _main_at_apogee),
    ONLY_REEFING: ScenarioDefinition(ONLY_REEFING, "Only Reefing Recovery", f"Reefed main state uses {REEFED_CDS_FACTOR:.2f} × the configured main CdS at apogee, followed by the configured disreefed main.", "apogee", True, _only_reefing),
    BALLISTIC: ScenarioDefinition(BALLISTIC, "Ballistic Descent", "All recovery devices disabled.", "none", False, _ballistic),
    DROGUE_ONLY: ScenarioDefinition(DROGUE_ONLY, "Drogue Only", "Main parachute disabled; drogue remains configured.", "main_disabled", True, _drogue_only),
}


def get_scenario(scenario_id: str) -> ScenarioDefinition:
    key = str(scenario_id).strip().lower()
    if key not in SCENARIOS:
        raise ValueError(f"Unsupported scenario_id: {scenario_id}")
    return SCENARIOS[key]


def scenario_ids(config: Any, include_optional: bool = True) -> tuple[str, ...]:
    """Return configured canonical IDs, preserving required scenario order."""
    configured = None
    try:
        configured = config.monte_carlo.get("scenarios")
    except AttributeError:
        configured = None
    if not configured:
        return REQUIRED_SCENARIOS
    values = [str(value).strip().lower() for value in configured]
    result = [value for value in REQUIRED_SCENARIOS if value in values]
    if include_optional:
        result.extend(value for value in values if value in SCENARIOS and value not in result)
    return tuple(result or REQUIRED_SCENARIOS)


def apply_scenario(config: Any, scenario_id: str) -> Any:
    """Deep-copy a ``ProjectConfig`` and apply one canonical override."""
    result = copy.deepcopy(config)
    definition = get_scenario(scenario_id)
    recovery = result.recovery
    definition.override(recovery)
    result.scenario_id = definition.scenario_id
    result.scenario_definition = definition
    return result
