"""
Engineering Requirements & Compliance Matrix Evaluation.

Evaluates flight metrics against formal aerospace requirements,
range safety standards, and team engineering design guidelines.
Every check is assigned an explicit Requirement ID, Source citation,
Classification, and physical rationale.
"""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class ComplianceItem:
    req_id: str
    source: str
    classification: str  # 'FORMAL REQUIREMENT' or 'ENGINEERING GUIDELINE'
    category: str
    criterion: str
    value_str: str
    threshold_str: str
    status: str  # 'SATISFIED', 'MARGINAL', 'CRITICAL FLAG', 'INFO'
    rationale: str


def evaluate_compliance(metrics: Dict[str, Any]) -> List[ComplianceItem]:
    """
    Evaluates a flight's metrics dictionary against safety and performance requirements.

    Returns:
        A list of ComplianceItem records with traceable Requirement IDs and Sources.
    """
    items: List[ComplianceItem] = []

    # 1. FD-REQ-001: Rail Exit Velocity
    v_rail = metrics.get("rail_dynamics", {}).get("rail_exit_velocity_ms", 0.0)
    if v_rail >= 30.0:
        status = "SATISFIED"
        msg = f"Velocity ({v_rail:.1f} m/s) sufficient to resist wind tip-off and rail drop."
    elif v_rail >= 25.0:
        status = "MARGINAL"
        msg = f"Marginal exit velocity ({v_rail:.1f} m/s). Susceptible to moderate crosswinds."
    else:
        status = "CRITICAL FLAG"
        msg = f"Unsafe exit velocity ({v_rail:.1f} m/s < 25.0 m/s). Severe risk of rod whip / rod tip-off."
    items.append(ComplianceItem(
        req_id="FD-REQ-001",
        source="LASC 2027 Section 4.2 / Range Safety",
        classification="FORMAL REQUIREMENT",
        category="Launch Dynamics",
        criterion="Rail Exit Velocity",
        value_str=f"{v_rail:.1f} m/s",
        threshold_str="\u2265 30.0 m/s",
        status=status,
        rationale=msg,
    ))

    # 2. FD-REQ-002: Crosswind Ratio at Rail Exit
    cw_ratio = metrics.get("rail_dynamics", {}).get("crosswind_ratio", 999.0)
    w_speed = metrics.get("rail_dynamics", {}).get("crosswind_speed_ms", 0.0)
    if w_speed < 0.5:
        status = "SATISFIED"
        msg = "Calm atmospheric conditions at launch rail height."
    elif cw_ratio >= 4.0:
        status = "SATISFIED"
        msg = f"Robust crosswind authority (v_rail / v_wind = {cw_ratio:.1f} \u2265 4.0)."
    elif cw_ratio >= 2.5:
        status = "MARGINAL"
        msg = f"Moderate crosswind sensitivity (Ratio: {cw_ratio:.1f} < 4.0). Noticeable weathercocking likely."
    else:
        status = "CRITICAL FLAG"
        msg = f"Severe weathercocking hazard (Ratio: {cw_ratio:.1f} < 2.5). Launch abort recommended."
    items.append(ComplianceItem(
        req_id="FD-REQ-002",
        source="NASA-SP-8007 / SAC Flight Safety",
        classification="ENGINEERING GUIDELINE",
        category="Launch Dynamics",
        criterion="Crosswind Safety Ratio (v_rail / v_wind)",
        value_str=f"{cw_ratio:.1f}" if cw_ratio < 900 else "N/A (Calm)",
        threshold_str="\u2265 4.0",
        status=status,
        rationale=msg,
    ))

    # 3. FD-REQ-003: Rail Exit Static Margin
    sm_rail = metrics.get("mass_and_stability", {}).get("static_margin_rail_exit_cal", 0.0)
    if 1.5 <= sm_rail <= 4.0:
        status = "SATISFIED"
        msg = f"Optimal aerodynamic stability at rail departure ({sm_rail:.2f} cal)."
    elif 1.0 <= sm_rail < 1.5:
        status = "MARGINAL"
        msg = f"Low static margin at exit ({sm_rail:.2f} cal). Susceptible to gust-induced coning."
    elif 4.0 < sm_rail <= 5.5:
        status = "MARGINAL"
        msg = f"High static margin ({sm_rail:.2f} cal). May increase weathercocking turning."
    elif sm_rail < 1.0:
        status = "CRITICAL FLAG"
        msg = f"Vehicle is statically unstable or marginal at rail exit ({sm_rail:.2f} cal < 1.0 cal)!"
    else:
        status = "MARGINAL"
        msg = f"Excessive static margin ({sm_rail:.2f} cal > 5.5 cal). Over-stabilized."
    items.append(ComplianceItem(
        req_id="FD-REQ-003",
        source="SAC Rules Section 3.1 / Range Safety",
        classification="FORMAL REQUIREMENT",
        category="Flight Stability",
        criterion="Rail Exit Static Margin",
        value_str=f"{sm_rail:.2f} cal",
        threshold_str="1.5 to 4.0 cal",
        status=status,
        rationale=msg,
    ))

    # 4. FD-REQ-004: Minimum Propelled Phase Static Margin
    sm_min = metrics.get("mass_and_stability", {}).get("static_margin_min_burn_cal", 0.0)
    if sm_min >= 1.0:
        status = "SATISFIED"
        msg = f"Positive static stability maintained throughout propellant burn (Min = {sm_min:.2f} cal)."
    elif sm_min >= 0.8:
        status = "MARGINAL"
        msg = f"Marginal stability during burn (Min = {sm_min:.2f} cal < 1.0 cal). Fin aeroelastic deflection risk."
    else:
        status = "CRITICAL FLAG"
        msg = f"Aerodynamic instability during burn (Min = {sm_min:.2f} cal < 0.8 cal). High tumbling risk."
    items.append(ComplianceItem(
        req_id="FD-REQ-004",
        source="Antares Flight Dynamics Design Standard",
        classification="ENGINEERING GUIDELINE",
        category="Flight Stability",
        criterion="Min Burn-Phase Stability Margin",
        value_str=f"{sm_min:.2f} cal",
        threshold_str="\u2265 1.0 cal",
        status=status,
        rationale=msg,
    ))

    # 5. FD-REQ-005: Static Margin at Max-Q
    sm_max_q = metrics.get("aerodynamic_loads", {}).get("static_margin_at_max_q_cal", 0.0)
    if sm_max_q >= 1.5:
        status = "SATISFIED"
        msg = f"High stability margin ({sm_max_q:.2f} cal) at peak aerodynamic loading."
    elif sm_max_q >= 1.0:
        status = "MARGINAL"
        msg = f"Acceptable but reduced margin ({sm_max_q:.2f} cal) during Max-Q."
    else:
        status = "CRITICAL FLAG"
        msg = f"Inadequate stability ({sm_max_q:.2f} cal < 1.0 cal) at peak dynamic pressure."
    items.append(ComplianceItem(
        req_id="FD-REQ-005",
        source="Antares Aeroelastic Standard",
        classification="ENGINEERING GUIDELINE",
        category="Flight Stability",
        criterion="Static Margin at Max-Q",
        value_str=f"{sm_max_q:.2f} cal",
        threshold_str="\u2265 1.2 cal",
        status=status,
        rationale=msg,
    ))

    # 6. STR-REQ-010: Maximum Dynamic Pressure (Max Q)
    max_q = metrics.get("aerodynamic_loads", {}).get("max_dynamic_pressure_pa", 0.0)
    if max_q <= 40000.0:
        status = "SATISFIED"
        msg = f"Dynamic pressure ({max_q/1000.0:.1f} kPa) well within airframe skin & fin aero limits."
    elif max_q <= 50000.0:
        status = "MARGINAL"
        msg = f"Elevated dynamic pressure ({max_q/1000.0:.1f} kPa). Ensure fin flutter margin > 1.5."
    else:
        status = "CRITICAL FLAG"
        msg = f"Excessive dynamic pressure ({max_q/1000.0:.1f} kPa > 50.0 kPa). Airframe structural limit exceeded."
    items.append(ComplianceItem(
        req_id="STR-REQ-010",
        source="Antares Airframe Structural Limit STR-010",
        classification="ENGINEERING GUIDELINE",
        category="Aerodynamics & Loads",
        criterion="Max Dynamic Pressure (Max Q)",
        value_str=f"{max_q / 1000.0:.1f} kPa",
        threshold_str="\u2264 50.0 kPa",
        status=status,
        rationale=msg,
    ))

    # 7. STR-REQ-012: Maximum Ascent Acceleration
    # Evaluates thrust/aerodynamic boost acceleration (excludes parachute opening shock)
    max_ascent_g = metrics.get("kinematics", {}).get("max_total_acceleration", 0.0)
    if max_ascent_g <= 18.0:
        status = "SATISFIED"
        msg = f"Ascent thrust g-load ({max_ascent_g:.1f} g) within structural airframe and avionics envelope."
    elif max_ascent_g <= 22.0:
        status = "MARGINAL"
        msg = f"Elevated ascent g-load ({max_ascent_g:.1f} g). Verify battery bracket and motor mount safety factors."
    else:
        status = "CRITICAL FLAG"
        msg = f"Excessive ascent acceleration ({max_ascent_g:.1f} g > 22.0 g). Airframe design envelope exceeded."
    items.append(ComplianceItem(
        req_id="STR-REQ-012",
        source="Antares Airframe & Avionics Qualification",
        classification="FORMAL REQUIREMENT",
        category="Structural Integrity",
        criterion="Max Ascent Total Acceleration",
        value_str=f"{max_ascent_g:.1f} g",
        threshold_str="\u2264 20.0 g",
        status=status,
        rationale=msg,
    ))

    # 8. AER-REQ-001: Flight Mach Regime
    max_mach = metrics.get("kinematics", {}).get("max_mach", 0.0)
    if max_mach < 0.80:
        status = "SATISFIED"
        msg = f"Subsonic flight regime (M = {max_mach:.2f}). Slender-body linear aero database valid."
    elif max_mach <= 1.05:
        status = "MARGINAL"
        msg = f"Transonic regime reached (M = {max_mach:.2f}). Compressibility shock waves and wave drag present."
    else:
        status = "INFO"
        msg = f"Supersonic flight regime (M = {max_mach:.2f}). Wave drag divergence and aerodynamic heating active."
    items.append(ComplianceItem(
        req_id="AER-REQ-001",
        source="Aerodynamic Database Validity Limit",
        classification="ENGINEERING GUIDELINE",
        category="Aerodynamics & Loads",
        criterion="Maximum Flight Mach Number",
        value_str=f"{max_mach:.2f} M",
        threshold_str="\u2264 0.80 M (Subsonic)",
        status=status,
        rationale=msg,
    ))

    # 9. REC-REQ-001: Drogue Deployment Timing
    t_ap = metrics.get("timeline", {}).get("apogee_s", 0.0)
    drogue = metrics.get("recovery", {}).get("drogue")
    if drogue:
        t_drogue = drogue.get("trigger_time", 0.0)
        dt_drogue = abs(t_drogue - t_ap)
        if dt_drogue <= 1.0:
            status = "SATISFIED"
            msg = f"Near-apogee deployment (|\u0394t| = {dt_drogue:.2f}s). Minimal dynamic pressure at ejection."
        elif dt_drogue <= 2.5:
            status = "MARGINAL"
            msg = f"Delayed drogue trigger (|\u0394t| = {dt_drogue:.2f}s). Check deployment dynamic pressure."
        else:
            status = "CRITICAL FLAG"
            msg = f"Severe deployment offset (|\u0394t| = {dt_drogue:.2f}s > 2.5s)! High-speed ejection risk."
        items.append(ComplianceItem(
            req_id="REC-REQ-001",
            source="SAC Recovery Rules / Range Safety",
            classification="FORMAL REQUIREMENT",
            category="Recovery Subsystem",
            criterion="Drogue Deployment Timing",
            value_str=f"|\u0394t| = {dt_drogue:.2f} s",
            threshold_str="|\u0394t| \u2264 1.0 s from Apogee",
            status=status,
            rationale=msg,
        ))

    # 10. REC-REQ-002: Main Parachute Opening Shock
    shock_g = metrics.get("recovery", {}).get("main_deploy_shock_g", 0.0)
    if shock_g <= 40.0:
        status = "SATISFIED"
        msg = f"Canopy opening shock ({shock_g:.1f} g) within recovery bridle & shock cord rating."
    elif shock_g <= 50.0:
        status = "MARGINAL"
        msg = f"Elevated opening shock ({shock_g:.1f} g). Inspect harness attachment bulkheads and shear pins."
    else:
        status = "CRITICAL FLAG"
        msg = f"Excessive deployment shock ({shock_g:.1f} g > 50.0 g). High probability of harness rupture."
    items.append(ComplianceItem(
        req_id="REC-REQ-002",
        source="Antares Recovery Bridle Rating",
        classification="FORMAL REQUIREMENT",
        category="Recovery Subsystem",
        criterion="Main Parachute Opening Shock",
        value_str=f"{shock_g:.1f} g",
        threshold_str="\u2264 45.0 g",
        status=status,
        rationale=msg,
    ))

    # 11. REC-REQ-003: Touchdown Velocity
    v_touch = metrics.get("recovery", {}).get("touchdown_velocity_ms", 0.0)
    if v_touch <= 8.0:
        status = "SATISFIED"
        msg = f"Safe touchdown sink rate ({v_touch:.1f} m/s). Minimal impact landing damage."
    elif v_touch <= 11.0:
        status = "MARGINAL"
        msg = f"Hard landing risk ({v_touch:.1f} m/s). Potential fin or airframe damage on rocky soil."
    else:
        status = "CRITICAL FLAG"
        msg = f"Ballistic impact velocity ({v_touch:.1f} m/s > 11.0 m/s)! Unacceptable recovery failure."
    items.append(ComplianceItem(
        req_id="REC-REQ-003",
        source="LASC / SAC Range Safety Standard",
        classification="FORMAL REQUIREMENT",
        category="Recovery Subsystem",
        criterion="Touchdown Vertical Velocity",
        value_str=f"{v_touch:.1f} m/s",
        threshold_str="\u2264 8.0 m/s",
        status=status,
        rationale=msg,
    ))

    # 12. REC-REQ-004: Touchdown Kinetic Energy
    e_k = metrics.get("recovery", {}).get("touchdown_energy_j", 0.0)
    if e_k <= 1000.0:
        status = "SATISFIED"
        msg = f"Touchdown kinetic energy ({e_k:.0f} J) well below range safety hazard threshold."
    elif e_k <= 1500.0:
        status = "MARGINAL"
        msg = f"Moderate impact energy ({e_k:.0f} J). Qualified recovery landing."
    else:
        status = "CRITICAL FLAG"
        msg = f"Excessive kinetic energy ({e_k:.0f} J > 1500 J). Potential hazard to ground recovery teams."
    items.append(ComplianceItem(
        req_id="REC-REQ-004",
        source="Range Safety Kinetic Hazard Guideline",
        classification="ENGINEERING GUIDELINE",
        category="Recovery Subsystem",
        criterion="Touchdown Kinetic Energy",
        value_str=f"{e_k:.0f} J",
        threshold_str="\u2264 1500 J",
        status=status,
        rationale=msg,
    ))

    return items
