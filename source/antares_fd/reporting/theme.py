"""
Styling, Themes, and Color Schemes for Antares Reports.

Consistent aerospace theme inspired by engineering publications:
Clean typography, high-contrast curves, muted backgrounds, clear grids.
"""

from reportlab.lib import colors
import matplotlib.pyplot as plt

# ReportLab Palette
NAVY_PRIMARY = colors.HexColor("#0B2545")
NAVY_SECONDARY = colors.HexColor("#134074")
BLUE_ACCENT = colors.HexColor("#007ACC")
GRAY_DARK = colors.HexColor("#1D2D44")
GRAY_LIGHT = colors.HexColor("#EEF4F8")
BG_LIGHT = colors.HexColor("#EEF4F8")
TEXT_DARK = colors.HexColor("#1D2D44")
GRAY_BORDER = colors.HexColor("#CBD5E1")
GRAY_TEXT = colors.HexColor("#475569")
WHITE = colors.HexColor("#FFFFFF")

STATUS_PASS = colors.HexColor("#065F46")
STATUS_WARN = colors.HexColor("#92400E")
STATUS_FAIL = colors.HexColor("#991B1B")
STATUS_INFO = colors.HexColor("#075985")

STATUS_PASS_BG = colors.HexColor("#D1FAE5")
STATUS_PASS_FG = colors.HexColor("#065F46")
STATUS_WARN_BG = colors.HexColor("#FEF3C7")
STATUS_WARN_FG = colors.HexColor("#92400E")
STATUS_FAIL_BG = colors.HexColor("#FEE2E2")
STATUS_FAIL_FG = colors.HexColor("#991B1B")
STATUS_INFO_BG = colors.HexColor("#E0F2FE")
STATUS_INFO_FG = colors.HexColor("#075985")

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph

def setup_report_styles():
    from reportlab.lib.styles import StyleSheet1
    styles = StyleSheet1()
    styles.add(ParagraphStyle(name="CoverTitle", fontName="Helvetica-Bold", fontSize=24, leading=28, alignment=1, spaceAfter=20, textColor=NAVY_PRIMARY))
    styles.add(ParagraphStyle(name="CoverSubtitle", fontName="Helvetica-Bold", fontSize=18, leading=22, alignment=1, spaceAfter=10, textColor=NAVY_SECONDARY))
    styles.add(ParagraphStyle(name="Heading1", fontName="Helvetica-Bold", fontSize=16, leading=20, spaceBefore=15, spaceAfter=10, textColor=NAVY_PRIMARY))
    styles.add(ParagraphStyle(name="Heading2", fontName="Helvetica-Bold", fontSize=14, leading=18, spaceBefore=10, spaceAfter=6, textColor=NAVY_SECONDARY))
    styles.add(ParagraphStyle(name="TableHeader", fontName="Helvetica-Bold", fontSize=8, textColor=WHITE))
    styles.add(ParagraphStyle(name="TableCell", fontName="Helvetica", fontSize=7.5, textColor=TEXT_DARK))
    styles.add(ParagraphStyle(name="TableCellBold", fontName="Helvetica-Bold", fontSize=7.5, textColor=TEXT_DARK))
    return styles

class BaseReportDocTemplate(BaseDocTemplate):
    def handle_pageBegin(self):
        self._handle_pageBegin()
    def build(self, flowables, **kwargs):
        self._calc()
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="normal")
        
        def footer(canvas, doc):
            canvas.saveState()
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(GRAY_TEXT)
            canvas.drawString(doc.leftMargin, doc.bottomMargin - 0.5 * 28.35, "Antares Flight Dynamics Automated Report")
            canvas.drawRightString(doc.pagesize[0] - doc.rightMargin, doc.bottomMargin - 0.5 * 28.35, f"Page {doc.page}")
            canvas.restoreState()
            
        self.addPageTemplates([PageTemplate(id="First", frames=frame, onPage=footer)])
        super().build(flowables, **kwargs)

def setup_matplotlib_theme():
    """Configures matplotlib rcParams for publication-quality figures."""
    plt.rcParams.update({
        "font.size": 9,
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
        "axes.labelsize": 9,
        "axes.labelweight": "semibold",
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "figure.titlesize": 12,
        "figure.titleweight": "bold",
        "grid.color": "#CBD5E1",
        "grid.linestyle": "--",
        "grid.alpha": 0.6,
        "axes.grid": True,
        "axes.edgecolor": "#94A3B8",
        "axes.linewidth": 0.8,
        "figure.dpi": 200,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
    })
