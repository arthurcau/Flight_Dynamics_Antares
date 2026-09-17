"""
ReportLab Table Formatters for Antares Engineering Reports.

Formats all quantitative tables using Platypus Table objects with clean typography,
proper column alignments, unit indicators, and status badges.
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
    badge_colors = {
        "SATISFIED": ("#065F46", "#D1FAE5"),
        "PASS": ("#065F46", "#D1FAE5"),
        "MARGINAL": ("#92400E", "#FEF3C7"),
        "WARNING": ("#92400E", "#FEF3C7"),
        "WARN (DRIFT)": ("#92400E", "#FEF3C7"),
        "CRITICAL FLAG": ("#991B1B", "#FEE2E2"),
        "CRITICAL FAIL": ("#991B1B", "#FEE2E2"),
        "FAIL": ("#991B1B", "#FEE2E2"),
        "VIOLATED": ("#991B1B", "#FEE2E2"),
        "QUALIFIED": ("#065F46", "#D1FAE5"),
        "INFO": ("#1E40AF", "#DBEAFE"),
    }
    fg, bg = badge_colors.get(status, ("#334155", "#F1F5F9"))
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
    t = Table(data_matrix)
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

# Rest of the old tables below (or we can just keep only this generic one if rewriting)
