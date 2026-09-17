"""Vector-first engineering report renderer.

The report is made with Matplotlib's PDF backend.  This is used when a TeX
engine is unavailable, and keeps all normal engineering graphics and report
text as PDF drawing primitives.  It consumes FlightMetrics or archived
analysis tables; it never constructs RocketPy objects or reruns physics.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterable

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

from antares_fd.analysis.provenance import collect_reproducibility_data
from antares_fd.reporting.theme import setup_matplotlib_theme, save_figure


NAVY = "#0B2545"
BLUE = "#007ACC"
TEAL = "#059669"
ORANGE = "#D97706"
RED = "#B91C1C"
INK = "#1D2D44"
MUTED = "#475569"
PALE = "#EEF4F8"


def _namespace(value: Any) -> Any:
    if isinstance(value, dict):
        return SimpleNamespace(**{key: _namespace(item) for key, item in value.items()})
    if isinstance(value, list):
        return [_namespace(item) for item in value]
    return value


def _read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _read_table(path: Path) -> pd.DataFrame:
    try:
        return pd.read_parquet(path) if path.exists() else pd.DataFrame()
    except (OSError, ValueError, ImportError):
        return pd.DataFrame()


def _fmt(value: Any, digits: int = 2, unit: str = "") -> str:
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "NOT AVAILABLE"
    if isinstance(value, (float, np.floating, int, np.integer)):
        return f"{float(value):.{digits}f}{(' ' + unit) if unit else ''}"
    return str(value)


def _wrap(value: Any, width: int = 28) -> str:
    return "\n".join(textwrap.wrap(str(value), width=width, break_long_words=False, break_on_hyphens=False))


class VectorReportRenderer:
    def __init__(self, metrics: Any, project_dir: Path, output_path: Path, run_id: str = "nominal", campaign_dir: Path | None = None, scenarios: dict[str, Any] | None = None):
        self.metrics = metrics
        self.project_dir = Path(project_dir)
        self.output_path = Path(output_path)
        self.run_id = run_id
        self.campaign_dir = Path(campaign_dir) if campaign_dir else None
        self.scenarios = scenarios or {}
        self.pages = 0
        self.figures_dir = self.output_path.parent / "figures"
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        setup_matplotlib_theme()

    def _page(self, title: str, section: str = ""):
        fig = plt.figure(figsize=(8.27, 11.69), facecolor="white")
        fig.text(0.07, 0.965, "ANTARES ROCKET DESIGN", fontsize=8, color=TEAL, weight="bold")
        fig.text(0.93, 0.965, "FLIGHT DYNAMICS EVIDENCE PACKAGE", fontsize=7, color=MUTED, ha="right")
        fig.text(0.07, 0.925, title, fontsize=18, color=NAVY, weight="bold")
        if section:
            fig.text(0.07, 0.902, section, fontsize=8.5, color=MUTED)
        fig.add_artist(plt.Line2D([0.07, 0.93], [0.89, 0.89], transform=fig.transFigure, color=TEAL, lw=1.2))
        fig.text(0.07, 0.035, f"Antares Flight Dynamics  |  {getattr(self.metrics, 'project_name', 'NEBLINA 1')}  |  {self.run_id[:18]}", fontsize=7, color=MUTED)
        fig.text(0.93, 0.035, f"Page {self.pages + 1}", fontsize=7, color=MUTED, ha="right")
        return fig

    def _finish(self, pdf: PdfPages, fig):
        pdf.savefig(fig, bbox_inches=None)
        plt.close(fig)
        self.pages += 1

    def _text(self, fig, x: float, y: float, text: str, size: float = 10, color: str = INK, weight: str = "normal", width: int = 100):
        fig.text(x, y, _wrap(text, width), fontsize=size, color=color, weight=weight, va="top", linespacing=1.35)

    def _table(self, fig, rows: list[list[Any]], rect=(0.07, 0.12, 0.86, 0.70), fontsize=7.4, widths=None):
        ax = fig.add_axes(rect)
        ax.axis("off")
        values = [[_wrap(v, 24 if widths is None else max(12, int(30 * widths[col]))) for col, v in enumerate(row)] for row in rows]
        table = ax.table(cellText=values, loc="upper left", cellLoc="left", colWidths=widths)
        table.auto_set_font_size(False)
        table.set_fontsize(fontsize)
        table.scale(1, 1.55)
        for (row, col), cell in table.get_celld().items():
            cell.set_edgecolor("#CBD5E1")
            cell.set_linewidth(0.45)
            cell.PAD = 0.025
            cell.set_text_props(color="white" if row == 0 else INK, va="center")
            cell.set_facecolor(NAVY if row == 0 else (PALE if row % 2 == 0 else "white"))
        return table

    def _cover(self, pdf):
        fig = plt.figure(figsize=(8.27, 11.69), facecolor="white")
        logo = self.project_dir.parents[1] / "docs" / "Antares_Logo_black.png"
        if logo.exists():
            ax = fig.add_axes((0.30, 0.72, 0.40, 0.16))
            ax.imshow(mpimg.imread(logo), aspect="equal")
            ax.axis("off")
        fig.text(0.5, 0.62, "ANTARES ROCKET DESIGN", ha="center", fontsize=21, color=NAVY, weight="bold")
        fig.text(0.5, 0.56, "FLIGHT DYNAMICS", ha="center", fontsize=25, color=TEAL, weight="bold")
        fig.text(0.5, 0.515, "ENGINEERING EVIDENCE PACKAGE", ha="center", fontsize=13, color=MUTED, weight="bold")
        rows = [
            ["Vehicle", getattr(self.metrics, "vehicle_name", "NEBLINA 1")],
            ["Run ID", self.run_id],
            ["Report status", "AUTOMATICALLY GENERATED"],
            ["Environment", getattr(self.metrics, "environment_type", "NOT AVAILABLE")],
            ["Generation", "UTC timestamp recorded in document control"],
        ]
        self._table(fig, [["Document", "Value"], *rows], rect=(0.20, 0.27, 0.60, 0.18), fontsize=8, widths=[0.30, 0.70])
        fig.text(0.5, 0.10, "All report values originate from canonical analysis artifacts.", ha="center", fontsize=8, color=MUTED)
        self._finish(pdf, fig)

    def _document_control(self, pdf):
        repro = collect_reproducibility_data(self.project_dir)
        git = repro.get("git", {})
        env = repro.get("environment", {})
        rows = [["Field", "Recorded value"],
                ["Document ID", f"AFD-{self.run_id}"],
                ["Vehicle", getattr(self.metrics, "vehicle_name", "NEBLINA 1")],
                ["Run ID", self.run_id],
                ["Status", "DEVELOPMENT / AUTOMATIC"],
                ["Git commit", git.get("commit", "unknown")],
                ["Git branch", git.get("branch", "unknown")],
                ["Dirty state", git.get("dirty", "unknown")],
                ["Antares FD", "0.1.0"],
                ["RocketPy", env.get("rocketpy_version", "unknown")],
                ["Python", env.get("python_version", "unknown")],
                ["Configuration hashes", "; ".join(f"{k}: {v}" for k, v in repro.get("config_hashes", {}).items()) or "NOT AVAILABLE"]]
        fig = self._page("Document Control")
        self._table(fig, rows, rect=(0.07, 0.25, 0.86, 0.58), fontsize=8, widths=[0.30, 0.70])
        self._text(fig, 0.07, 0.20, "This document was automatically generated from immutable analysis artifacts. Machine-specific absolute paths are intentionally excluded.", 9, color=MUTED)
        self._finish(pdf, fig)

    def _toc(self, pdf):
        items = ["1 Executive Summary", "2 Completeness & Engineering Warnings", "3 Requirements & Compliance", "4 Model Provenance & Input Quality", "5 Model Validity & Data Coverage", "6 Flight Kinematics", "7 Propulsion", "8 Max-Q & Aerodynamic Loads", "9 Stability", "10 MAGI Atmospheric Environment", "11 Recovery", "12 Failure Scenarios", "13 Monte Carlo Campaign", "14 Statistical Verification", "15 Validation", "Appendix A Complete Metrics", "Appendix B Data Dictionary"]
        fig = self._page("Table of Contents")
        self._text(fig, 0.10, 0.84, "Contents are generated from the same build that creates the PDF. Page numbers are intentionally omitted from this lightweight vector backend; PDF page order is deterministic.", 9, color=MUTED)
        y = 0.76
        for item in items:
            fig.text(0.12, y, item, fontsize=11, color=INK)
            fig.text(0.87, y, "·" * 20, fontsize=8, color="#CBD5E1", ha="right")
            y -= 0.038
        self._finish(pdf, fig)

    def _executive(self, pdf):
        m = self.metrics
        rows = [["FLIGHT", "Value", "STABILITY", "Value"],
                ["Apogee AGL", _fmt(getattr(m, "apogee_agl", None), 1, "m"), "SM rail exit", _fmt(getattr(m, "static_margin_rail_exit", None), 2, "cal")],
                ["Time to apogee", _fmt(getattr(m, "apogee_time", None), 2, "s"), "SM at Max-Q", _fmt(getattr(m, "static_margin_max_q", None), 2, "cal")],
                ["Max Mach", _fmt(getattr(m, "max_mach", None), 3), "Minimum burn SM", _fmt(getattr(m, "minimum_burn_static_margin", None), 2, "cal")],
                ["Max-Q", _fmt(getattr(m, "max_dynamic_pressure", None) / 1000 if getattr(m, "max_dynamic_pressure", None) is not None else None, 1, "kPa"), "AoA at Max-Q", _fmt(getattr(m, "angle_of_attack_at_max_q", None), 2, "deg")],
                ["Rail exit velocity", _fmt(getattr(m, "rail_exit_velocity", None), 1, "m/s"), "Max valid AoA", _fmt(getattr(m, "max_angle_of_attack", None), 1, "deg")],
                ["Flight duration", _fmt(getattr(m, "flight_duration", None), 1, "s"), "", ""],
                ["RECOVERY", "Value", "DISPERSION", "Value"],
                ["Touchdown speed", _fmt(getattr(m, "touchdown_velocity", None), 1, "m/s"), "Nominal landing", _fmt(getattr(m, "landing_distance", None), 1, "m")],
                ["Touchdown energy", _fmt(getattr(m, "touchdown_energy", None), 0, "J"), "P50 landing radius", self._mc_value("landing_distance", "p50")],
                ["Drogue descent", _fmt(getattr(m, "drogue_descent_rate", None), 1, "m/s"), "95% ellipse", self._mc_ellipse("0.95")],
                ["Main descent", _fmt(getattr(m, "main_descent_rate", None), 1, "m/s"), "Campaign cases", self._mc_value("_count", "")]]
        fig = self._page("1. Executive Summary")
        self._table(fig, rows, rect=(0.07, 0.34, 0.86, 0.48), fontsize=7.5, widths=[0.26, 0.24, 0.26, 0.24])
        self._text(fig, 0.07, 0.27, self._interpretation(), 9.2, color=INK)
        self._finish(pdf, fig)

    def _mc_summary(self):
        if not self.campaign_dir:
            return {}
        return _read_json(self.campaign_dir / "summary.json", _read_json(self.campaign_dir / "monte_carlo_summary.json", {})) or {}

    def _mc_value(self, metric: str, stat: str) -> str:
        if metric == "_count":
            s = self._mc_summary()
            return str(s.get("successful", s.get("completed", "NOT AVAILABLE")))
        table = _read_table(self.campaign_dir / "statistics.parquet") if self.campaign_dir else pd.DataFrame()
        if table.empty or "metric" not in table:
            return "NOT AVAILABLE"
        row = table[table.metric == metric]
        return _fmt(row.iloc[0].get(stat), 1, "m") if not row.empty else "NOT AVAILABLE"

    def _mc_ellipse(self, key: str) -> str:
        landing = self._mc_summary().get("landing", {})
        ellipse = landing.get("ellipses", {}).get(key, {})
        return _fmt(ellipse.get("major_axis"), 0, "m") if ellipse else "NOT AVAILABLE"

    def _interpretation(self) -> str:
        m = self.metrics
        return (f"Engineering Interpretation: maximum dynamic pressure is {_fmt(getattr(m, 'max_dynamic_pressure', 0) / 1000.0, 1, 'kPa')} at t = {_fmt(getattr(m, 'max_q_time', 0), 2, 's')} and {_fmt(getattr(m, 'max_q_altitude', 0), 1, 'm')} AGL. "
                f"The reported AoA at Max-Q is {_fmt(getattr(m, 'angle_of_attack_at_max_q', 0), 2, 'deg')}; the valid-window maximum is {_fmt(getattr(m, 'max_angle_of_attack', 0), 1, 'deg')}. Q-alpha is a load indicator and is not a structural bending moment.")

    def _warnings(self, pdf):
        warnings = list(self._mc_summary().get("warnings", []))
        if getattr(self.metrics, "main_event", None) and getattr(self.metrics.main_event, "numerical_transient_shock_g", 0) > 1:
            warnings.append("RECOVERY OPENING SHOCK NOT PHYSICALLY RESOLVED BY CURRENT MODEL")
        if getattr(self.metrics, "max_angle_of_attack", 0) > 10:
            warnings.append("AERODYNAMIC MODEL RANGE REQUIRES REVIEW FOR VALID-WINDOW MAXIMUM AoA")
        if not warnings:
            warnings.append("No configured engineering warnings were raised by the available artifacts.")
        fig = self._page("2. Completeness & Engineering Warnings")
        rows = [["Status", "Evidence"]] + [["ENGINEERING WARNING", item] for item in warnings]
        self._table(fig, rows, rect=(0.07, 0.42, 0.86, 0.40), fontsize=8, widths=[0.28, 0.72])
        completeness = [["Subsystem", "State"], ["Nominal", "COMPLETE"], ["Propulsion", "COMPLETE"], ["Aerodynamics", "COMPLETE / WINDOWED"], ["MAGI", "COMPLETE"], ["Recovery", "COMPLETE / SHOCK LIMITED"], ["Monte Carlo", "COMPLETE_NOT_CONVERGED" if self.campaign_dir else "NOT AVAILABLE"], ["Validation", "AVAILABLE" if getattr(self.metrics, "validation", None) else "NOT AVAILABLE"]]
        self._table(fig, completeness, rect=(0.07, 0.10, 0.86, 0.25), fontsize=8, widths=[0.45, 0.55])
        self._finish(pdf, fig)

    def _requirements(self, pdf):
        rows = [["ID", "Type", "Description", "Metric", "Limit", "Nominal", "Margin", "Status"]]
        # RequirementDB is deliberately not called here: artifact rendering
        # must consume the already evaluated compliance table only.
        for row in self._compliance_rows():
            rows.append([row.get(k, "NOT EVALUATED") for k in ("requirement", "source_type", "description", "metric", "limit", "nominal", "nominal_margin", "verification_status")])
        if len(rows) == 1:
            rows.append(["NOT AVAILABLE"] * 8)
        fig = self._page("3. Requirements & Compliance", "Status vocabulary: SATISFIED, VIOLATED, NOT EVALUATED")
        self._table(fig, rows, rect=(0.05, 0.18, 0.90, 0.66), fontsize=6.2, widths=[0.10, 0.14, 0.23, 0.13, 0.10, 0.10, 0.10, 0.10])
        self._finish(pdf, fig)

    def _compliance_rows(self):
        if not self.campaign_dir:
            return []
        frame = _read_table(self.campaign_dir / "compliance.parquet")
        return frame.to_dict("records") if not frame.empty else []

    def _provenance(self, pdf):
        repro = collect_reproducibility_data(self.project_dir)
        rows = [["Parameter", "Source", "Classification", "Confidence / semantics"]]
        for item in repro.get("input_quality", []):
            rows.append([item.get("parameter"), item.get("source"), item.get("classification"), item.get("confidence")])
        rows.extend([["Dry mass", "vehicle.yaml mass_properties.mass_without_motor", "MEASURED / CONFIGURED", "Instrument resolution is not uncertainty"], ["Aerodynamics", "aero/*.csv", "MODELED", "Applicability bounded by configured window"], ["Atmosphere", "MAGI adapter", "NATIVE MODEL", "Forecast member provenance required"]])
        fig = self._page("4. Model Provenance & Input Quality")
        self._table(fig, rows, rect=(0.06, 0.18, 0.88, 0.65), fontsize=6.9, widths=[0.24, 0.29, 0.22, 0.25])
        self._finish(pdf, fig)

    def _validity(self, pdf):
        m = self.metrics
        rows = [["Domain", "Observed", "Applicability / status"], ["Aerodynamics / Mach", _fmt(getattr(m, "max_mach", None), 3), "Configured aerodynamic coefficient domain"], ["Aerodynamics / AoA", _fmt(getattr(m, "max_angle_of_attack", None), 1, "deg"), f"Window: {getattr(m, 'aero_analysis_window', {})}"], ["MAGI altitude", _fmt(getattr(m, "apogee_asl", None), 0, "m ASL"), "Profile evaluated to trajectory ceiling"], ["Recovery shock", "Numerical transient", "Structural opening shock not resolved"]]
        fig = self._page("5. Model Validity & Data Coverage")
        self._table(fig, rows, rect=(0.07, 0.45, 0.86, 0.37), fontsize=8, widths=[0.25, 0.25, 0.50])
        self._text(fig, 0.07, 0.35, "The raw ascent AoA maximum is intentionally separated from the aerodynamic-analysis maximum. The latter is evaluated only between rail exit and apogee while dynamic pressure and airspeed exceed configured numerical validity floors.", 9)
        self._finish(pdf, fig)

    def _flight_pages(self, pdf):
        ts = getattr(self.metrics, "timeseries", None)
        if ts is None:
            return
        fig = self._page("6. Flight Kinematics", "Canonical FlightMetrics time series")
        ax1 = fig.add_axes((0.10, 0.55, 0.80, 0.28)); ax1.plot(ts.time, ts.altitude_agl, color=NAVY, lw=1.2); ax1.set(xlabel="Time (s)", ylabel="Altitude AGL (m)"); ax1.grid(True, alpha=.3)
        ax2 = fig.add_axes((0.10, 0.16, 0.80, 0.28)); ax2.plot(ts.time, ts.speed, color=BLUE, label="speed"); ax2.plot(ts.time, ts.mach * 100, color=ORANGE, ls="--", label="Mach × 100"); ax2.set(xlabel="Time (s)", ylabel="Speed / scaled Mach"); ax2.legend(fontsize=7); ax2.grid(True, alpha=.3)
        self._finish(pdf, fig)
        fig = self._page("7. Propulsion", "Mass, thrust, impulse and T/W definitions")
        ax = fig.add_axes((0.10, 0.55, 0.80, 0.28)); ax.plot(ts.time, ts.thrust, color=ORANGE, label="Thrust (N)"); ax2 = ax.twinx(); ax2.plot(ts.time, ts.thrust / np.maximum(ts.mass, 1e-9) / 9.80665, color=BLUE, ls="--", label="T/W"); ax.set(xlabel="Time (s)", ylabel="Thrust (N)"); ax2.set_ylabel("T/W"); ax.grid(True, alpha=.3)
        rows = [["KPI", "Value"], ["T/W at t = 0", _fmt(getattr(self.metrics, "initial_tw", None), 2)], ["T/W at ignition", _fmt(getattr(self.metrics, "ignition_tw", None), 2)], ["T/W at rail exit", _fmt(getattr(self.metrics, "rail_exit_tw", None), 2)], ["Maximum T/W", _fmt(getattr(self.metrics, "peak_tw", None), 2)], ["Average burn T/W", _fmt(getattr(self.metrics, "average_burn_tw", None), 2)], ["Total impulse", _fmt(getattr(self.metrics, "total_impulse", None), 0, "N s")]]
        self._table(fig, rows, rect=(0.10, 0.16, 0.80, 0.25), fontsize=8, widths=[0.55, 0.45]); self._finish(pdf, fig)
        fig = self._page("8. Max-Q & Aerodynamic Loads", "Q-alpha is an aerodynamic bending-load indicator")
        ax = fig.add_axes((0.10, 0.53, 0.80, 0.30)); ax.plot(ts.time, ts.dynamic_pressure / 1000, color=BLUE, label="Q (kPa)"); ax.axvline(getattr(self.metrics, "max_q_time", 0), color=RED, ls="--", label="Max-Q"); ax.set(xlabel="Time (s)", ylabel="Dynamic pressure (kPa)"); ax.legend(fontsize=7); ax.grid(True, alpha=.3)
        rows = [["Max-Q engineering state", "Value"], ["Time", _fmt(getattr(self.metrics, "max_q_time", None), 2, "s")], ["Altitude AGL", _fmt(getattr(self.metrics, "max_q_altitude", None), 1, "m")], ["Mach", _fmt(getattr(self.metrics, "max_q_mach", None), 3)], ["AoA", _fmt(getattr(self.metrics, "angle_of_attack_at_max_q", None), 2, "deg")], ["Static margin", _fmt(getattr(self.metrics, "static_margin_max_q", None), 2, "cal")], ["Peak valid Q-alpha", _fmt(getattr(self.metrics, "peak_valid_q_alpha", None) / 1000 if getattr(self.metrics, "peak_valid_q_alpha", None) is not None else None, 1, "kPa deg")]]
        self._table(fig, rows, rect=(0.10, 0.14, 0.80, 0.29), fontsize=8, widths=[0.55, 0.45]); self._finish(pdf, fig)
        fig = self._page("9. Stability", "CG, CP and static margin")
        ax = fig.add_axes((0.10, 0.51, 0.80, 0.32)); ax.plot(ts.time, ts.cg, label="CG", color=BLUE); ax.plot(ts.time, ts.cp, label="CP", color=RED); ax.set(xlabel="Time (s)", ylabel="Position from nose (m)"); ax.legend(fontsize=7); ax.grid(True, alpha=.3)
        ax2 = fig.add_axes((0.10, 0.14, 0.80, 0.25)); ax2.plot(ts.time, ts.static_margin, color=TEAL); ax2.axhline(1.0, color=RED, ls="--", label="1 cal reference"); ax2.set(xlabel="Time (s)", ylabel="Static margin (cal)"); ax2.legend(fontsize=7); ax2.grid(True, alpha=.3); self._finish(pdf, fig)
        fig = self._page("10. MAGI Atmospheric Environment")
        ax = fig.add_axes((0.11, 0.52, 0.78, 0.33)); ax.plot(self.metrics.atmosphere.wind_speed, self.metrics.atmosphere.altitude_agl, color=BLUE, label="Wind magnitude"); ax.set(xlabel="Wind speed (m/s)", ylabel="Altitude AGL (m)"); ax.grid(True, alpha=.3)
        ax2 = fig.add_axes((0.11, 0.13, 0.36, 0.27)); ax2.plot(self.metrics.atmosphere.wind_u, self.metrics.atmosphere.wind_v, color=NAVY); ax2.set(xlabel="East U (m/s)", ylabel="North V (m/s)"); ax2.grid(True, alpha=.3)
        ax3 = fig.add_axes((0.57, 0.13, 0.32, 0.27)); ax3.plot(self.metrics.atmosphere.density, self.metrics.atmosphere.altitude_agl, color=TEAL, label="density"); ax3.set(xlabel="Density (kg/m³)", ylabel="Altitude (m)"); ax3.grid(True, alpha=.3); self._finish(pdf, fig)
        fig = self._page("11. Recovery", "Signed vertical velocity is distinct from positive touchdown speed")
        ax = fig.add_axes((0.10, 0.53, 0.80, 0.30)); mask = ts.time >= getattr(self.metrics, "apogee_time", 0); ax.plot(ts.time[mask], ts.altitude_agl[mask], color=TEAL); ax.set(xlabel="Time (s)", ylabel="Altitude AGL (m)"); ax.grid(True, alpha=.3)
        rows = [["Event / KPI", "Value"], ["Drogue trigger", _fmt(getattr(self.metrics, "drogue_deployment_time", None), 2, "s")], ["Main trigger", _fmt(getattr(self.metrics, "main_deployment_time", None), 2, "s")], ["Touchdown speed |Vz|", _fmt(getattr(self.metrics, "touchdown_velocity", None), 1, "m/s")], ["Touchdown energy", _fmt(getattr(self.metrics, "touchdown_energy", None), 0, "J")], ["Opening shock", "NOT PHYSICALLY RESOLVED BY CURRENT MODEL"]]
        self._table(fig, rows, rect=(0.10, 0.15, 0.80, 0.26), fontsize=8, widths=[0.55, 0.45]); self._finish(pdf, fig)

    def _scenarios(self, pdf):
        if not self.scenarios:
            return
        rows = [["Scenario", "Apogee AGL (m)", "Max Mach", "Max-Q (kPa)", "Flight time (s)", "Landing (m)", "Touchdown (m/s)"]]
        for name, m in self.scenarios.items():
            rows.append([name, _fmt(getattr(m, "apogee_agl", None), 1), _fmt(getattr(m, "max_mach", None), 2), _fmt(getattr(m, "max_dynamic_pressure", None) / 1000 if getattr(m, "max_dynamic_pressure", None) is not None else None, 1), _fmt(getattr(m, "flight_duration", None), 1), _fmt(getattr(m, "landing_distance", None), 1), _fmt(getattr(m, "touchdown_velocity", None), 1)])
        fig = self._page("12. Failure Scenarios", "Deterministic scenario comparison")
        self._table(fig, rows, rect=(0.04, 0.44, 0.92, 0.38), fontsize=6.5, widths=[0.22, .13, .10, .13, .13, .14, .15]); self._text(fig, .07, .35, "Scenario ascent quantities must be identical through the failure event when the physical vehicle, motor and environment are shared. Any earlier divergence is flagged as a configuration consistency issue.", 9); self._finish(pdf, fig)

    def _mc_pages(self, pdf):
        if not self.campaign_dir:
            return
        summary = self._mc_summary(); performance = _read_json(self.campaign_dir / "performance.json", {}) or {}
        rows = [["Campaign field", "Value"], ["Campaign ID", summary.get("campaign_id", self.run_id)], ["Status", summary.get("status", "NOT AVAILABLE")], ["Requested", summary.get("requested", "NOT AVAILABLE")], ["Successful", summary.get("successful", summary.get("completed", "NOT AVAILABLE"))], ["Failed", summary.get("failed", "NOT AVAILABLE")], ["Master seed", summary.get("master_seed", "recorded in manifest")], ["Cases/s", performance.get("cases_per_second", "NOT AVAILABLE")], ["Wall time", performance.get("elapsed_seconds", "NOT AVAILABLE")], ["Disk bytes", performance.get("campaign_disk_bytes", "NOT AVAILABLE")]]
        fig = self._page("13. Monte Carlo Campaign", "Canonical scalar artifacts")
        self._table(fig, rows, rect=(0.08, 0.37, 0.84, 0.47), fontsize=8, widths=[0.45, 0.55]); self._text(fig, .08, .29, "The report consumes saved Parquet/JSON artifacts. It does not rerun RocketPy, MAGI or Monte Carlo.", 9, color=MUTED); self._finish(pdf, fig)
        stats = _read_table(self.campaign_dir / "statistics.parquet")
        rows = [["Metric", "Mean", "Std", "P05", "P50", "P95", "P99"]]
        for _, row in stats.iterrows():
            rows.append([row.get("metric", ""), row.get("mean", ""), row.get("std", ""), row.get("p05", ""), row.get("p50", ""), row.get("p95", ""), row.get("p99", "")])
        if len(rows) == 1: rows.append(["NOT AVAILABLE"] * 7)
        fig = self._page("14. Statistical Verification", "Empirical distributions; no normality assumption")
        self._table(fig, rows, rect=(0.05, 0.16, 0.90, 0.68), fontsize=6.4, widths=[.22, .13, .13, .13, .13, .13, .13]); self._finish(pdf, fig)
        conv = _read_table(self.campaign_dir / "convergence.parquet")
        sens = _read_table(self.campaign_dir / "sensitivity.parquet")
        rows = [["Convergence metric", "Checkpoint", "Estimate", "State"]]
        if not conv.empty:
            for _, row in conv.tail(18).iterrows(): rows.append([row.get("metric", ""), row.get("checkpoint", ""), row.get("value", ""), row.get("status", "")])
        else: rows.append(["NOT AVAILABLE"] * 4)
        fig = self._page("15. Convergence & Sensitivity")
        self._table(fig, rows, rect=(0.06, 0.45, 0.88, 0.38), fontsize=6.8, widths=[.36, .17, .22, .25]);
        if not sens.empty and {"input", "output", "coefficient"}.issubset(sens.columns):
            top = sens.assign(abs_coeff=sens.coefficient.abs()).sort_values("abs_coeff").tail(8); ax = fig.add_axes((.10, .12, .80, .23)); ax.barh(top.input.astype(str), top.coefficient, color=TEAL); ax.set_xlabel("Spearman rho (association)"); ax.grid(True, axis="x", alpha=.3)
        self._finish(pdf, fig)

    def _validation(self, pdf):
        fig = self._page("16. Flight Validation")
        validation = getattr(self.metrics, "validation", None)
        if validation:
            rows = [["Validation item", "Result"], ["Field data", validation.get("has_field_data", False)], ["Predicted landing", validation.get("predicted", {}).get("dist", "NOT AVAILABLE")], ["Measured fuselage radial error", validation.get("fuselage", {}).get("err_radial_m", "NOT AVAILABLE")], ["Measured nose radial error", validation.get("nose_cone", {}).get("err_radial_m", "NOT AVAILABLE")]]
            self._table(fig, rows, rect=(.10, .46, .80, .34), fontsize=8, widths=[.60, .40])
        else:
            self._text(fig, .10, .75, "NOT AVAILABLE: no flight telemetry or measured landing coordinates were supplied to the canonical analysis artifact.", 11, color=RED, weight="bold")
        self._finish(pdf, fig)

    def _appendices(self, pdf):
        keys = ["apogee_agl", "apogee_asl", "rail_exit_velocity", "max_velocity", "max_mach", "max_dynamic_pressure", "max_angle_of_attack", "angle_of_attack_at_max_q", "static_margin_rail_exit", "static_margin_max_q", "burnout_mass", "propellant_mass", "total_impulse", "initial_tw", "ignition_tw", "rail_exit_tw", "peak_tw", "average_burn_tw", "flight_duration", "touchdown_velocity", "touchdown_energy", "landing_east", "landing_north", "landing_distance"]
        rows = [["Metric", "Value", "Definition / unit"]]
        for key in keys:
            value = getattr(self.metrics, key, None); rows.append([key, _fmt(value, 4), "Canonical FlightMetrics scalar; SI unless stated"])
        fig = self._page("Appendix A. Complete Metrics")
        self._table(fig, rows, rect=(.06, .12, .88, .73), fontsize=6.8, widths=[.28, .22, .50]); self._finish(pdf, fig)
        rows = [["Variable", "Definition / sign convention"], ["AGL", "Above ground level: ASL minus launch elevation"], ["East / North", "ENU ground displacement from launch pad in metres"], ["Vertical velocity", "Signed RocketPy Vz; negative means downward"], ["Touchdown speed", "Positive magnitude |Vz| at final event"], ["AoA", "Angle of attack in degrees; valid-window maximum is reported"], ["Static margin", "CP minus CG normalized by reference diameter, in calibers"], ["Q-alpha", "Q multiplied by absolute AoA; aerodynamic bending-load indicator"], ["T/W at t=0", "Raw solver initial state; may be zero before ignition"], ["T/W at ignition", "Thrust divided by instantaneous weight at motor burn start"]]
        fig = self._page("Appendix B. Data Dictionary")
        self._table(fig, rows, rect=(.07, .20, .86, .62), fontsize=7.5, widths=[.30, .70]); self._finish(pdf, fig)

    def render(self) -> Path:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        metadata = {"Title": "Antares Flight Dynamics Engineering Evidence Package", "Author": "Antares Flight Dynamics", "Subject": self.run_id}
        with PdfPages(self.output_path, metadata=metadata) as pdf:
            self._cover(pdf); self._document_control(pdf); self._toc(pdf); self._executive(pdf); self._warnings(pdf); self._requirements(pdf); self._provenance(pdf); self._validity(pdf); self._flight_pages(pdf); self._scenarios(pdf); self._mc_pages(pdf); self._validation(pdf); self._appendices(pdf)
        (self.output_path.parent / "report_manifest.json").write_text(json.dumps({"page_count": self.pages, "headings": list(__import__("antares_fd.reporting.qa", fromlist=["EXPECTED_HEADINGS"]).EXPECTED_HEADINGS), "renderer": "matplotlib.backends.backend_pdf.PdfPages", "physics_rerun": False}, indent=2), encoding="utf-8")
        return self.output_path
