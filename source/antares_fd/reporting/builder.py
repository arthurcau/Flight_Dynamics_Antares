import os
from pathlib import Path
from typing import Dict, Any, List
from reportlab.platypus import SimpleDocTemplate, PageBreak, Spacer, Paragraph, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

from antares_fd.analysis.flight_metrics import FlightMetrics
from antares_fd.analysis.requirements import RequirementDB, EvaluatedRequirement
from antares_fd.analysis.provenance import collect_reproducibility_data, evaluate_model_validity
from antares_fd.reporting.theme import setup_report_styles, BaseReportDocTemplate
from antares_fd.reporting import plot_registry, tables

class ReportContext:
    def __init__(self, project_dir: Path, metrics: FlightMetrics, req_db: RequirementDB):
        self.project_dir = project_dir
        self.metrics = metrics
        self.req_db = req_db
        self.requirements = req_db.evaluate(metrics)
        self.provenance = collect_reproducibility_data(project_dir)
        self.validity = evaluate_model_validity(metrics)
        self.output_dir = project_dir / "results"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.fig_dir = self.output_dir / ".figures"
        self.fig_dir.mkdir(parents=True, exist_ok=True)


class FlightDynamicsReportBuilder:
    def __init__(self, context: ReportContext):
        self.ctx = context
        self.styles = setup_report_styles()
        self.flowables = []

    def build_deterministic_report(self, output_pdf: Path):
        """Constructs phases 0-14 for standard flight."""
        # Note: A real implementation would invoke separate section builder modules here.
        self._add_cover("Deterministi Flight Analysis")
        self._add_executive_summary()
        self._add_flight_kinematics()
        self._add_mass_propulsion()
        self._add_aero_loads()
        self._add_stability()
        self._add_atmosphere()
        self._add_recovery()
        
        doc = BaseReportDocTemplate(
            str(output_pdf),
            pagesize=A4,
            leftMargin=1.5 * cm,
            rightMargin=1.5 * cm,
            topMargin=3.0 * cm,
            bottomMargin=2.0 * cm,
        )
        doc.build(self.flowables)

    def _add_cover(self, title: str):
        self.flowables.append(Spacer(1, 4 * cm))
        self.flowables.append(Paragraph(self.ctx.metrics.project_name.replace("_", " ").upper(), self.styles["CoverTitle"]))
        self.flowables.append(Paragraph(title, self.styles["CoverSubtitle"]))
        self.flowables.append(Spacer(1, 2 * cm))
        self.flowables.append(PageBreak())

    def _add_executive_summary(self):
        self.flowables.append(Paragraph("1. Executive Summary", self.styles["Heading1"]))
        
        # Requirements Table
        self.flowables.append(Paragraph("Requirement Compliance Matrix", self.styles["Heading2"]))
        table_data = [["ID", "Description", "Result", "Margin", "Status"]]
        for req in self.ctx.requirements:
            margin_str = f"{req.margin:+.2f} {req.units}" if req.margin is not None else "-"
            val_str = f"{req.value:.2f} {req.units}" if isinstance(req.value, float) else str(req.value)
            table_data.append([req.req_id, req.description, val_str, margin_str, req.status])
        
        self.flowables.append(tables.create_standard_table(table_data))
        self.flowables.append(PageBreak())
        
    def _add_flight_kinematics(self):
        self.flowables.append(Paragraph("2. Flight Kinematics & Trajectory", self.styles["Heading1"]))
        fig_path = self.ctx.fig_dir / "kinematics.png"
        plot_registry.generate_kinematics_chart(self.ctx.metrics, fig_path)
        self.flowables.append(Image(str(fig_path), width=16*cm, height=12*cm))
        self.flowables.append(PageBreak())

    def _add_mass_propulsion(self):
        self.flowables.append(Paragraph("3. Mass & Propulsion Dynamics", self.styles["Heading1"]))
        fig_path = self.ctx.fig_dir / "propulsion.png"
        plot_registry.generate_mass_and_propulsion_chart(self.ctx.metrics, fig_path)
        self.flowables.append(Image(str(fig_path), width=16*cm, height=11*cm))
        self.flowables.append(PageBreak())

    def _add_aero_loads(self):
        self.flowables.append(Paragraph("4. Aerodynamic Loads (Max Q & Bending)", self.styles["Heading1"]))
        fig_path = self.ctx.fig_dir / "aero_loads.png"
        plot_registry.generate_propulsion_and_loads_chart(self.ctx.metrics, fig_path)
        self.flowables.append(Image(str(fig_path), width=16*cm, height=10*cm))
        self.flowables.append(PageBreak())
        
    def _add_stability(self):
        self.flowables.append(Paragraph("5. Stability & Attitude Dynamics", self.styles["Heading1"]))
        fig_path = self.ctx.fig_dir / "stability.png"
        plot_registry.generate_stability_and_attitude_chart(self.ctx.metrics, fig_path)
        self.flowables.append(Image(str(fig_path), width=16*cm, height=10*cm))
        self.flowables.append(PageBreak())
        
    def _add_atmosphere(self):
        self.flowables.append(Paragraph("6. MAGI Atmospheric Profile", self.styles["Heading1"]))
        fig_path = self.ctx.fig_dir / "atmosphere.png"
        plot_registry.generate_full_atmosphere_chart(self.ctx.metrics, fig_path)
        self.flowables.append(Image(str(fig_path), width=16*cm, height=13*cm))
        self.flowables.append(PageBreak())
        
    def _add_recovery(self):
        self.flowables.append(Paragraph("7. Recovery Profile", self.styles["Heading1"]))
        fig_path = self.ctx.fig_dir / "recovery.png"
        plot_registry.generate_recovery_descent_chart(self.ctx.metrics, fig_path)
        self.flowables.append(Image(str(fig_path), width=16*cm, height=9*cm))
        self.flowables.append(PageBreak())
