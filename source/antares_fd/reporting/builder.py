import os
from pathlib import Path
from typing import Dict, Any, List
import json
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
        self.scenario_metrics: Dict[str, FlightMetrics] = {}
        self.mc_results_dir: Path = None


class FlightDynamicsReportBuilder:
    def __init__(self, context: ReportContext):
        self.ctx = context
        self.styles = setup_report_styles()
        self.flowables = []

    def build_deterministic_report(self, output_pdf: Path):
        """Constructs phases 0-14 for standard flight."""
        self._add_cover("Flight Dynamics Evidence Package")
        self._add_executive_summary()
        self._add_provenance_and_validity()
        
        self._add_flight_kinematics()
        self._add_mass_propulsion()
        self._add_aero_loads()
        self._add_stability()
        self._add_atmosphere()
        self._add_recovery()
        
        if self.ctx.scenario_metrics and len(self.ctx.scenario_metrics) > 1:
            self._add_multi_scenario()
            
        if self.ctx.mc_results_dir:
            self._add_monte_carlo()
        
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
            table_data.append([req.req_id, req.description, val_str, margin_str, tables._get_badge(req.status, self.styles['TableCell'])])
        
        self.flowables.append(tables.create_standard_table(table_data))
        self.flowables.append(PageBreak())
        
    def _add_provenance_and_validity(self):
        self.flowables.append(Paragraph("2. Model Provenance & Input Quality", self.styles["Heading1"]))
        # Model Validity Checks
        self.flowables.append(Paragraph("Physical Domain Validity Envelopes", self.styles["Heading2"]))
        val_data = [["Domain & Parameter", "Simulated Peak", "Validity Envelope", "Status", "Note"]]
        for check in self.ctx.validity:
            val_data.append([check["domain"] + ": " + check["parameter"], check["simulated"], check["validity_limit"], check["status"], check["note"]])
        self.flowables.append(tables.build_model_validity_envelope_table(self.ctx.validity, self.styles))
        self.flowables.append(Spacer(1, 1 * cm))
        
        # Input Quality Classification
        self.flowables.append(Paragraph("Input Quality Classification", self.styles["Heading2"]))
        qual_data = [["Parameter", "Source", "Classification", "Confidence"]]
        for q in self.ctx.provenance["input_quality"]:
            qual_data.append([q["parameter"], q["source"], q["classification"], q["confidence"]])
        self.flowables.append(tables.build_model_input_quality_table(self.ctx.provenance['input_quality'], self.styles))
        self.flowables.append(PageBreak())
        
    def _add_flight_kinematics(self):
        self.flowables.append(Paragraph("3. Flight Kinematics & Trajectory", self.styles["Heading1"]))
        fig_path = self.ctx.fig_dir / "kinematics.png"
        plot_registry.generate_kinematics_chart(self.ctx.metrics, fig_path)
        if fig_path.exists():
            self.flowables.append(Image(str(fig_path), width=16*cm, height=12*cm))
            
        fig2_path = self.ctx.fig_dir / "views.png"
        plot_registry.generate_trajectory_views_chart(self.ctx.metrics, fig2_path)
        if fig2_path.exists():
            self.flowables.append(Image(str(fig2_path), width=16*cm, height=8*cm))
        self.flowables.append(PageBreak())

    def _add_mass_propulsion(self):
        self.flowables.append(Paragraph("4. Mass & Propulsion Dynamics", self.styles["Heading1"]))
        fig_path = self.ctx.fig_dir / "propulsion.png"
        plot_registry.generate_mass_and_propulsion_chart(self.ctx.metrics, fig_path)
        if fig_path.exists():
            self.flowables.append(Image(str(fig_path), width=16*cm, height=11*cm))
        self.flowables.append(PageBreak())

    def _add_aero_loads(self):
        self.flowables.append(Paragraph("5. Aerodynamic Loads (Max Q & Bending)", self.styles["Heading1"]))
        fig_path = self.ctx.fig_dir / "aero_loads.png"
        plot_registry.generate_propulsion_and_loads_chart(self.ctx.metrics, fig_path)
        if fig_path.exists():
            self.flowables.append(Image(str(fig_path), width=16*cm, height=10*cm))
        self.flowables.append(PageBreak())
        
    def _add_stability(self):
        self.flowables.append(Paragraph("6. Stability & Attitude Dynamics", self.styles["Heading1"]))
        fig_path = self.ctx.fig_dir / "stability.png"
        plot_registry.generate_stability_and_attitude_chart(self.ctx.metrics, fig_path)
        if fig_path.exists():
            self.flowables.append(Image(str(fig_path), width=16*cm, height=10*cm))
        self.flowables.append(PageBreak())
        
    def _add_atmosphere(self):
        self.flowables.append(Paragraph("7. MAGI Atmospheric Profile", self.styles["Heading1"]))
        fig_path = self.ctx.fig_dir / "atmosphere.png"
        plot_registry.generate_full_atmosphere_chart(self.ctx.metrics, fig_path)
        if fig_path.exists():
            self.flowables.append(Image(str(fig_path), width=16*cm, height=13*cm))
        self.flowables.append(PageBreak())
        
    def _add_recovery(self):
        self.flowables.append(Paragraph("8. Recovery Profile", self.styles["Heading1"]))
        fig_path = self.ctx.fig_dir / "recovery.png"
        plot_registry.generate_recovery_descent_chart(self.ctx.metrics, fig_path)
        if fig_path.exists():
            self.flowables.append(Image(str(fig_path), width=16*cm, height=9*cm))
        self.flowables.append(PageBreak())
        
    def _add_multi_scenario(self):
        self.flowables.append(Paragraph("9. Multi-Scenario Comparative Flight", self.styles["Heading1"]))
        fig_path = self.ctx.fig_dir / "multi_scenario.png"
        plot_registry.generate_multi_scenario_chart(self.ctx.scenario_metrics, fig_path)
        if fig_path.exists():
            self.flowables.append(Image(str(fig_path), width=16*cm, height=12*cm))
        self.flowables.append(PageBreak())

    def _add_monte_carlo(self):
        self.flowables.append(Paragraph("10. Monte Carlo Stochastic Analysis", self.styles["Heading1"]))
        mc_file = self.ctx.mc_results_dir / "monte_carlo_results.json"
        if not mc_file.exists():
            self.flowables.append(Paragraph("Monte Carlo execution completed, but results JSON is missing.", self.styles["TableCell"]))
            return
            
        fig_disp = self.ctx.fig_dir / "mc_dispersion.png"
        plot_registry.generate_mc_dispersion_chart(mc_file, fig_disp, "MC", self.ctx.metrics.validation)
        if fig_disp.exists():
            self.flowables.append(Image(str(fig_disp), width=16*cm, height=12*cm))
            self.flowables.append(Spacer(1, 1 * cm))
            
        fig_dist = self.ctx.fig_dir / "mc_distributions.png"
        plot_registry.generate_mc_distributions_chart(mc_file, fig_dist)
        if fig_dist.exists():
            self.flowables.append(Image(str(fig_dist), width=16*cm, height=11*cm))
            self.flowables.append(PageBreak())
            
        fig_conv = self.ctx.fig_dir / "mc_convergence.png"
        plot_registry.generate_mc_convergence_chart(mc_file, fig_conv)
        if fig_conv.exists():
            self.flowables.append(Image(str(fig_conv), width=16*cm, height=10*cm))
            self.flowables.append(PageBreak())
            
        # Optional: Sensitivity Tornado
        sens_file = self.ctx.mc_results_dir / "sensitivity_analysis.json"
        if sens_file.exists():
            with open(sens_file, "r") as f:
                sens_data = json.load(f)
            fig_sens = self.ctx.fig_dir / "mc_sensitivity.png"
            plot_registry.generate_sensitivity_tornado_chart(sens_data, fig_sens)
            if fig_sens.exists():
                self.flowables.append(Image(str(fig_sens), width=16*cm, height=8*cm))
        self.flowables.append(PageBreak())
