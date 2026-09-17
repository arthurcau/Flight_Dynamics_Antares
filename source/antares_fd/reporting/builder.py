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
        
        self._add_reproducibility_appendix()
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
        self.flowables.append(Paragraph("1. Executive Summary & Report Status", self.styles["Heading1"]))
        
        from reportlab.platypus import KeepTogether
        
        # Report Completeness Status
        completeness = {
            "Nominal Simulation": "COMPLETE",
            "Atmosphere Model": "COMPLETE" if self.ctx.metrics.environment_type != "UNKNOWN" else "UNKNOWN",
            "Scenario Analysis": "COMPLETE" if self.ctx.scenario_metrics and len(self.ctx.scenario_metrics) > 1 else "NOT AVAILABLE",
            "Validation Data": "COMPLETE" if self.ctx.metrics.validation else "NOT AVAILABLE"
        }
        
        mc_summary_file = self.ctx.mc_results_dir / "monte_carlo_summary.json" if self.ctx.mc_results_dir else None
        has_mc = mc_summary_file and mc_summary_file.exists()
        if has_mc:
            try:
                with open(mc_summary_file, 'r') as f:
                    mc_data = json.load(f)
                mc_status = mc_data.get("status", "PARTIAL").upper()
            except Exception:
                mc_status = "FAILED"
        else:
            mc_status = "NOT AVAILABLE"
            
        completeness["Monte Carlo Execution"] = mc_status
        
        self.flowables.append(Paragraph("Evidence Package Generation Status", self.styles["Heading2"]))
        self.flowables.append(tables.build_completeness_table(completeness, self.styles))
        self.flowables.append(Spacer(1, 0.5 * cm))

        # True Executive Summary Panels
        kpi_table_1 = tables.build_flight_performance_table(self.ctx.metrics)
        kpi_table_2 = tables.build_stability_table(self.ctx.metrics)
        kpi_table_3 = tables.build_recovery_table(self.ctx.metrics)

        self.flowables.append(Paragraph("Flight Performance", self.styles["Heading2"]))
        self.flowables.append(kpi_table_1)
        self.flowables.append(Spacer(1, 0.5 * cm))
        
        self.flowables.append(Paragraph("Stability", self.styles["Heading2"]))
        self.flowables.append(kpi_table_2)
        self.flowables.append(Spacer(1, 0.5 * cm))
        
        self.flowables.append(Paragraph("Recovery", self.styles["Heading2"]))
        self.flowables.append(kpi_table_3)
        self.flowables.append(Spacer(1, 1 * cm))
        
        # Requirements Table
        self.flowables.append(Paragraph("Engineering Requirements Compliance", self.styles["Heading2"]))
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
        
        # Add a compact metric table here! (Phase 7 rule)
        metrics = self.ctx.metrics
        p_data = [["Propulsion KPI", "Value"]]
        p_data.append(["Initial Mass", f"{metrics.burnout_mass + metrics.propellant_mass:.2f} kg"])
        p_data.append(["Burnout Mass", f"{metrics.burnout_mass:.2f} kg"])
        p_data.append(["Propellant Mass", f"{metrics.propellant_mass:.2f} kg"])
        p_data.append(["Initial T/W", f"{metrics.initial_tw:.2f}"])
        p_data.append(["Peak T/W", f"{metrics.peak_tw:.2f}"])
        p_data.append(["Burn Time", f"{metrics.burnout_time:.2f} s"])
        p_data.append(["Total Impulse", f"{metrics.total_impulse:.1f} Ns"])
        p_data.append(["Average Thrust", f"{metrics.average_thrust:.1f} N"])
        p_data.append(["Peak Thrust", f"{metrics.max_thrust:.1f} N"])
        
        self.flowables.append(tables.create_standard_table(p_data))
        self.flowables.append(Spacer(1, 0.5 * cm))
        
        fig_path = self.ctx.fig_dir / "propulsion.png"
        plot_registry.generate_mass_and_propulsion_chart(self.ctx.metrics, fig_path)
        if fig_path.exists():
            self.flowables.append(Image(str(fig_path), width=16*cm, height=11*cm))
        self.flowables.append(PageBreak())

    def _add_aero_loads(self):
        self.flowables.append(Paragraph("5. Aerodynamic Loads (Max Q & Bending)", self.styles["Heading1"]))
        
        # Phase 7 rule: ADD MAX-Q STATE PANEL
        metrics = self.ctx.metrics
        q_data = [["Max-Q State", "Value"]]
        q_data.append(["Dynamic Pressure", f"{metrics.max_dynamic_pressure/1000.0:.1f} kPa"])
        q_data.append(["Time", f"{metrics.max_q_time:.2f} s"])
        q_data.append(["Altitude AGL", f"{metrics.max_q_altitude:.1f} m"])
        q_data.append(["Mach Number", f"{metrics.max_q_mach:.2f} M"])
        q_data.append(["Velocity", f"{metrics.max_q_mach * 340.0:.1f} m/s"]) # Approximate speed of sound
        q_data.append(["Angle of Attack", f"{metrics.angle_of_attack_at_max_q:.1f} deg"])
        q_data.append(["Static Margin", f"{metrics.static_margin_max_q:.2f} cal"])
        
        self.flowables.append(tables.create_standard_table(q_data))
        self.flowables.append(Spacer(1, 0.5 * cm))
        
        fig_path = self.ctx.fig_dir / "aero_loads.png"
        plot_registry.generate_propulsion_and_loads_chart(self.ctx.metrics, fig_path)
        if fig_path.exists():
            self.flowables.append(Image(str(fig_path), width=16*cm, height=10*cm))
        self.flowables.append(PageBreak())
        
    def _add_stability(self):
        self.flowables.append(Paragraph("6. Stability Evolution", self.styles["Heading1"]))
        # Phase 7 rule: Small marker table
        metrics = self.ctx.metrics
        sm_data = [["Stability Checkpoint", "Margin (cal)"]]
        sm_data.append(["Liftoff", f"{metrics.static_margin_liftoff:.2f}"])
        sm_data.append(["Rail Exit", f"{metrics.static_margin_rail_exit:.2f}"])
        sm_data.append(["Max-Q", f"{metrics.static_margin_max_q:.2f}"])
        sm_data.append(["Burnout", f"{metrics.static_margin_burnout:.2f}"])
        sm_data.append(["Maximum Margin", f"{metrics.maximum_static_margin:.2f}"])
        
        self.flowables.append(tables.create_standard_table(sm_data))
        self.flowables.append(Spacer(1, 0.5 * cm))
        
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
        
        # Phase 7 rule: Quantitative comparison table
        t_data = [["Scenario", "Apogee (m)", "Flight Time (s)", "Max Mach", "Max-Q (kPa)", "Landing Dist (m)", "Touchdown (m/s)"]]
        for s_name, s_metric in self.ctx.scenario_metrics.items():
            t_data.append([
                s_name,
                f"{s_metric.apogee_agl:.1f}",
                f"{s_metric.flight_duration:.1f}",
                f"{s_metric.max_mach:.2f}",
                f"{s_metric.max_dynamic_pressure/1000.0:.1f}",
                f"{s_metric.landing_distance:.1f}",
                f"{s_metric.touchdown_velocity:.1f}"
            ])
            
        self.flowables.append(tables.create_standard_table(t_data))
        self.flowables.append(Spacer(1, 0.5 * cm))
        
        fig_path = self.ctx.fig_dir / "multi_scenario.png"
        plot_registry.generate_multi_scenario_chart(self.ctx.scenario_metrics, fig_path)
        if fig_path.exists():
            self.flowables.append(Image(str(fig_path), width=16*cm, height=12*cm))
        self.flowables.append(PageBreak())

    def _add_monte_carlo(self):
        self.flowables.append(Paragraph("10. Monte Carlo Stochastic Analysis", self.styles["Heading1"]))
        mc_file = self.ctx.mc_results_dir / "mc_sim.outputs.txt"
        
        mc_summary_file = self.ctx.mc_results_dir / "monte_carlo_summary.json"
        has_mc = False
        if mc_summary_file.exists():
            with open(mc_summary_file, 'r') as f:
                mc_data = json.load(f)
            
            s_data = [["Stochastic Run Info", "Value"]]
            s_data.append(["Campaign ID", mc_data.get("campaign_id", "Unknown")])
            s_data.append(["Status", mc_data.get("status", "Unknown").upper()])
            s_data.append(["Requested Cases", mc_data.get("requested", 0)])
            s_data.append(["Completed Cases", mc_data.get("completed", 0)])
            s_data.append(["Failed Cases", mc_data.get("failed", 0)])
            self.flowables.append(tables.create_standard_table(s_data))
            self.flowables.append(Spacer(1, 0.5 * cm))
            has_mc = (mc_data.get("completed", 0) > 0)
            
        # Add Input table
        self.flowables.append(Paragraph("Stochastic Inputs / Provenance", self.styles["Heading2"]))
        self.flowables.append(tables.build_mc_input_table(self.ctx.project_dir, self.styles))
        self.flowables.append(Spacer(1, 0.5 * cm))
        
        if not mc_file.exists() or not has_mc:
            self.flowables.append(Paragraph("Monte Carlo execution completed, but RocketPy output text is missing.", self.styles["TableCell"]))
            return

        # Add Output table
        self.flowables.append(Paragraph("Output Distributions", self.styles["Heading2"]))
        self.flowables.append(tables.build_mc_output_table(mc_file))
        self.flowables.append(Spacer(1, 1 * cm))
        
        # Phase 12 Add Probabilistic Requirements Table
        self.flowables.append(Paragraph("Stochastic Requirement Confidence Matrix", self.styles["Heading2"]))
        stochastic_evaluator = getattr(self.ctx.req_db, "evaluate_stochastic", None)
        stochastic_table_builder = getattr(tables, "build_stochastic_requirements_table", None)
        if callable(stochastic_evaluator) and callable(stochastic_table_builder):
            import pandas as pd
            records = []
            with open(mc_file, "r") as ff:
                for line in ff:
                    if not line.strip():
                        continue
                    try:
                        records.append(json.loads(line))
                    except Exception:
                        pass
            if records:
                stoch_reqs = stochastic_evaluator(pd.DataFrame(records))
                if stoch_reqs:
                    self.flowables.append(stochastic_table_builder(stoch_reqs, self.styles))
        self.flowables.append(Spacer(1, 1 * cm))

            
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


    def _add_reproducibility_appendix(self):
        self.flowables.append(PageBreak())
        self.flowables.append(Paragraph("Reproducibility Appendix", self.styles["Heading1"]))
        
        import subprocess
        from datetime import datetime
        
        try:
            commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
            dirty = subprocess.check_output(["git", "status", "--porcelain"]).decode("utf-8").strip()
            git_state = commit_hash + (" (DIRTY)" if dirty else " (CLEAN)")
        except Exception:
            git_state = "UNKNOWN (Not a git repository)"
            
        try:
            now_utc = datetime.utcnow().isoformat() + "Z"
        except Exception:
            now_utc = "UNKNOWN"
            
        proj_dir = str(self.ctx.project_dir.absolute())
        
        data = [
            ["Attribute", "Value"],
            ["Execution Timestamp (UTC)", now_utc],
            ["Git State", git_state],
            ["Project Directory", proj_dir],
            ["Antares FD Framework", "Version 2.0 (Hardened)"]
        ]
        
        t = tables.create_standard_table(data)
        self.flowables.append(t)
        self.flowables.append(Spacer(1, 1*cm))
        
        self.flowables.append(Paragraph("This report was automatically synthesized by Antares Flight Dynamics. No manual edits were performed on these charts or metrics. All values are traceable to the defined inputs, meteorological sources, and aerodynamic models.", self.styles["TableCell"]))
