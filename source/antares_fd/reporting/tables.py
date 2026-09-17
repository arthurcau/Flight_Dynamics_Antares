"""
ReportLab Table Formatters for Antares Engineering Reports.
"""

from typing import Any, Dict, List, Optional
import json
import numpy as np
from pathlib import Path
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import ParagraphStyle
import yaml

from antares_fd.analysis.flight_metrics import FlightMetrics
from .theme import (
    NAVY_PRIMARY, BLUE_ACCENT, BG_LIGHT, TEXT_DARK,
    STATUS_PASS, STATUS_WARN, STATUS_FAIL, STATUS_INFO
)


def _get_badge(status: str, style_base: ParagraphStyle) -> Paragraph:
    """Generates a color-coded status badge Paragraph."""
    s = str(status).upper().strip()
    
    pass_tags = ["SATISFIED", "PASS", "VALID", "QUALIFIED", "WITHIN GUIDELINE", "WITHIN MODEL RANGE", "COVERED", "COMPLETE"]
    warn_tags = ["MARGINAL", "WARNING", "WARN (DRIFT)", "PARTIAL", "ENGINEERING_ESTIMATE"]
    fail_tags = ["VIOLATED", "FAIL", "CRITICAL FLAG", "CRITICAL FAIL", "OUTSIDE GUIDELINE", "MODEL RANGE EXCEEDED", "NOT COVERED", "FAILED", "LEGACY_ASSUMPTION"]
    info_tags = ["UNKNOWN", "NOT EVALUATED", "NOT AVAILABLE"]
    
    if s in pass_tags:
        fg, bg = ("#065F46", "#D1FAE5")
    elif s in warn_tags:
        fg, bg = ("#92400E", "#FEF3C7")
    elif s in fail_tags:
        fg, bg = ("#991B1B", "#FEE2E2")
    else:
        fg, bg = ("#1E40AF", "#DBEAFE")
        
    text = f'<font color="{fg}"><b>{status}</b></font>'
    badge_style = ParagraphStyle(
        name=f"Badge_{status}",
        parent=style_base,
        fontName="Helvetica-Bold",
        fontSize=6.5,
        leading=8,
        alignment=1,  # Centered
    )
    return Paragraph(text, badge_style)


def create_standard_table(data_matrix: List[List[Any]]) -> Table:
    if not data_matrix:
        return Table([["NO DATA"]])
    
    t = Table(data_matrix, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    return t

def build_model_validity_envelope_table(validity_data: List[Dict[str, Any]], styles: Any) -> Table:
    table_data = [["Domain & Parameter", "Simulated Peak", "Validity Envelope", "Status", "Note"]]
    style_base = styles["TableCell"]
    
    for check in validity_data:
        domain_param = f"{check.get('domain', '')}: {check.get('parameter', '')}"
        sim = str(check.get('simulated', 'N/A'))
        limit = str(check.get('validity_limit', 'None'))
        status_val = str(check.get('status', 'INFO')).upper()
        note = Paragraph(str(check.get('note', '')), style_base)
        
        status_badge = _get_badge(status_val, style_base)
        table_data.append([domain_param, sim, limit, status_badge, note])
        
    return create_standard_table(table_data)

def build_model_input_quality_table(quality_data: List[Dict[str, Any]], styles: Any) -> Table:
    table_data = [["Parameter", "Source", "Classification", "Confidence"]]
    style_base = styles["TableCell"]
    
    for q in quality_data:
        param = str(q.get('parameter', ''))
        source = str(q.get('source', ''))
        classification = str(q.get('classification', ''))
        confidence_val = str(q.get('confidence', '')).upper()
        
        conf_badge = _get_badge(confidence_val, style_base)
        table_data.append([param, source, classification, conf_badge])
        
    return create_standard_table(table_data)

def build_flight_performance_table(metrics: FlightMetrics) -> Table:
    data = [["KPI", "Value"]]
    data.append(["Apogee AGL", f"{metrics.apogee_agl:.1f} m"])
    data.append(["Max Mach", f"{metrics.max_mach:.2f} M"])
    data.append(["Max Velocity", f"{metrics.max_velocity:.1f} m/s"])
    data.append(["Max Total Acceleration", f"{metrics.max_total_acceleration:.1f} g"])
    data.append(["Max Dynamic Pressure (Max-Q)", f"{metrics.max_dynamic_pressure/1000.0:.1f} kPa"])
    data.append(["Rail Exit Velocity", f"{metrics.rail_exit_velocity:.1f} m/s"])
    data.append(["Flight Duration", f"{metrics.flight_duration:.1f} s"])
    data.append(["Ground Drift", f"{metrics.landing_distance:.1f} m"])
    return create_standard_table(data)

def build_stability_table(metrics: FlightMetrics) -> Table:
    data = [["KPI", "Value"]]
    data.append(["Static Margin (Rail Exit)", f"{metrics.static_margin_rail_exit:.2f} cal"])
    data.append(["Static Margin (Max-Q)", f"{metrics.static_margin_max_q:.2f} cal"])
    data.append(["Static Margin (Burnout)", f"{metrics.static_margin_burnout:.2f} cal"])
    data.append(["Max Angle of Attack (Ascent)", f"{metrics.max_angle_of_attack:.1f} deg"])
    return create_standard_table(data)

def build_recovery_table(metrics: FlightMetrics) -> Table:
    data = [["KPI", "Value"]]
    d_descent = metrics.drogue_descent_rate
    m_descent = metrics.main_descent_rate
    data.append(["Drogue Descent Rate", f"{d_descent:.1f} m/s" if d_descent else "N/A"])
    data.append(["Main Descent Rate", f"{m_descent:.1f} m/s" if m_descent else "N/A"])
    data.append(["Touchdown Velocity", f"{metrics.touchdown_velocity:.1f} m/s"])
    data.append(["Touchdown Energy", f"{metrics.touchdown_energy:.1f} J"])
    
    if metrics.drogue_event or metrics.main_event:
        d_sg = metrics.drogue_event.numerical_transient_shock_g if metrics.drogue_event else 0.0
        m_sg = metrics.main_event.numerical_transient_shock_g if metrics.main_event else 0.0
        max_sg = max(d_sg, m_sg)
        if max_sg > 0.1:
            data.append(["Recovery Opening Shock", "NOT PHYSICALLY RESOLVED BY CURRENT MODEL"])
    return create_standard_table(data)

def build_completeness_table(completeness: Dict[str, str], styles: Any) -> Table:
    data = [["Subsystem", "Status"]]
    for k, v in completeness.items():
        data.append([k, _get_badge(v, styles["TableCell"])])
    return create_standard_table(data)

def build_mc_input_table(project_dir: Path, styles: Any) -> Table:
    unc_path = project_dir / "config" / "uncertainties.yaml"
    data = [["Parameter", "Distribution", "Uncertainty Limits", "Units", "Status"]]
    style_base = styles["TableCell"]
    
    if not unc_path.exists():
        data.append(["No Config", "-", "-", "-", "UNKNOWN"])
        return create_standard_table(data)
        
    try:
        with open(unc_path, 'r', encoding='utf-8') as f:
            d = yaml.safe_load(f)
            uncs = d.get('uncertainties', {})
            for k, v in uncs.items():
                if not v.get('enabled', False):
                    continue
                dist = v.get('distribution', 'unknown')
                units = v.get('units', '-')
                prov = v.get('provenance', {})
                status = prov.get('type', 'UNKNOWN').upper()
                
                limits = "..."
                if dist == 'normal':
                    limits = f"N({v.get('mean', 1.0)}, {v.get('sigma', 0.1):.3f})"
                elif dist == 'uniform':
                    limits = f"U[{v.get('min', 0.0):.1f}, {v.get('max', 1.0):.1f}]"
                elif dist == 'categorical':
                    limits = "Ensemble"
                    
                data.append([
                    k,
                    dist,
                    limits,
                    units,
                    _get_badge(status, style_base)
                ])
    except Exception as e:
         data.append(["Error", "-", str(e), "-", "ERROR"])
         
    return create_standard_table(data)

def build_mc_output_table(outputs_file: Path) -> Table:
    data = [["Variable", "Mean", "Std", "P05", "P50", "P95"]]
    
    if not outputs_file.exists():
        data.append(["File Missing", "-", "-", "-", "-", "-"])
        return create_standard_table(data)
        
    records = []
    try:
        with open(outputs_file, "r") as f:
            for line in f:
                if not line.strip(): continue
                try:
                    records.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        pass
        
    if not records:
        data.append(["No Records", "-", "-", "-", "-", "-"])
        return create_standard_table(data)
        
    var_map = {
        "apogee": ("Apogee AGL (m)", lambda r: r.get("apogee", 0.0)),
        "rail_exit": ("Rail Exit Vel (m/s)", lambda r: r.get("out_of_rail_velocity", 0.0)),
        "max_mach": ("Max Mach (M)", lambda r: r.get("max_mach_number", 0.0)),
        "max_q": ("Max-Q (kPa)", lambda r: r.get("max_dynamic_pressure", 0.0)/1000.0),
        "landing_east": ("Landing X (m)", lambda r: r.get("x_impact", 0.0)),
        "landing_north": ("Landing Y (m)", lambda r: r.get("y_impact", 0.0)),
        "v_impact": ("Touchdown (m/s)", lambda r: r.get("impact_velocity", 0.0)),
        "t_final": ("Flight Time (s)", lambda r: r.get("t_final", 0.0))
    }
    
    def _pct(arr, p):
        return np.percentile(arr, p) if len(arr) > 0 else 0.0
        
    for k, (label, extractor) in var_map.items():
        arr = np.array([extractor(r) for r in records])
        if len(arr) == 0: continue
        
        mean = np.mean(arr)
        std = np.std(arr)
        p05 = _pct(arr, 5)
        p50 = _pct(arr, 50)
        p95 = _pct(arr, 95)
        
        data.append([
            label,
            f"{mean:.2f}",
            f"{std:.2f}",
            f"{p05:.2f}",
            f"{p50:.2f}",
            f"{p95:.2f}"
        ])

    return create_standard_table(data)
