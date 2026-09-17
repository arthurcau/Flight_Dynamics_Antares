"""
ReportLab Table Formatters for Antares Engineering Reports.
"""

from typing import Any, Dict, List, Optional
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import ParagraphStyle

from antares_fd.analysis.compliance import ComplianceItem
from .theme import (
    NAVY_PRIMARY, BLUE_ACCENT, BG_LIGHT, TEXT_DARK,
    STATUS_PASS, STATUS_WARN, STATUS_FAIL, STATUS_INFO
)


def _get_badge(status: str, style_base: ParagraphStyle) -> Paragraph:
    """Generates a color-coded status badge Paragraph."""
    s = str(status).upper().strip()
    
    # Vocabulary mappings for mechanical semantic evaluation
    pass_tags = ["SATISFIED", "PASS", "VALID", "QUALIFIED", "WITHIN GUIDELINE", "WITHIN MODEL RANGE", "COVERED"]
    warn_tags = ["MARGINAL", "WARNING", "WARN (DRIFT)", "PARTIAL"]
    fail_tags = ["VIOLATED", "FAIL", "CRITICAL FLAG", "CRITICAL FAIL", "OUTSIDE GUIDELINE", "MODEL RANGE EXCEEDED", "NOT COVERED"]
    
    if s in pass_tags:
        fg, bg = ("#065F46", "#D1FAE5")
    elif s in warn_tags:
        fg, bg = ("#92400E", "#FEF3C7")
    elif s in fail_tags:
        fg, bg = ("#991B1B", "#FEE2E2")
    else:
        # INFO / NOT EVALUATED / UNKNOWN
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
