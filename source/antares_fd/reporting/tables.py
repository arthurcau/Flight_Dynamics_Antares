"""
ReportLab Table Formatters for Antares Engineering Reports.
"""

from typing import Any, Dict, List, Optional
import numpy as np
from pathlib import Path
from reportlab.lib import colors
from reportlab.platypus import Table, LongTable, TableStyle, Paragraph
from reportlab.lib.styles import ParagraphStyle
import yaml
import pandas as pd

from antares_fd.analysis.flight_metrics import FlightMetrics
from antares_fd.analysis.uq import finite_numeric_values, summarize_finite_values
from antares_fd.storage import read_jsonl_objects
from .theme import (
    NAVY_PRIMARY, BG_LIGHT, TEXT_DARK
)


def _get_badge(status: str, style_base: ParagraphStyle) -> Paragraph:
    """Generates a color-coded status badge Paragraph."""
    s = str(status).upper().strip()

    pass_tags = ["SATISFIED", "PASS", "VALID", "QUALIFIED", "WITHIN GUIDELINE", "WITHIN MODEL RANGE", "COVERED", "COMPLETE"]
    warn_tags = ["MARGINAL", "WARNING", "WARN (DRIFT)", "PARTIAL", "ENGINEERING_ESTIMATE"]
    fail_tags = ["VIOLATED", "FAIL", "CRITICAL FLAG", "CRITICAL FAIL", "OUTSIDE GUIDELINE", "MODEL RANGE EXCEEDED", "NOT COVERED", "FAILED", "LEGACY_ASSUMPTION"]

    if s in pass_tags:
        fg = "#065F46"
    elif s in warn_tags:
        fg = "#92400E"
    elif s in fail_tags:
        fg = "#991B1B"
    else:
        fg = "#1E40AF"

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


def _cell(value: Any, header: bool = False) -> Any:
    """Converta um valor em célula ReportLab com quebra de texto.

    Mantém Paragraph existente; nos demais casos, aplica estilo de cabeçalho
    ou corpo e escapa ampersands. Retorna Paragraph para uso na tabela.
    """
    if isinstance(value, Paragraph):
        return value
    style = ParagraphStyle(
        name="ReportTableHeader" if header else "ReportTableCell",
        fontName="Helvetica-Bold" if header else "Helvetica",
        fontSize=7.2 if header else 7.0,
        leading=8.6 if header else 8.4,
        textColor=colors.white if header else TEXT_DARK,
        wordWrap="CJK",
    )
    return Paragraph(str(value).replace("&", "&amp;"), style)


def create_standard_table(data_matrix: List[List[Any]], col_widths: Optional[List[float]] = None, landscape: bool = False) -> Table:
    """Construa uma tabela paginável com cabeçalho repetido.

    Preenche linhas curtas com células vazias e calcula larguras proporcionais
    quando col_widths não é informado. landscape seleciona a largura útil.
    Retorna LongTable estilizada; matriz vazia produz indicação NO DATA.
    """
    if not data_matrix:
        return Table([["NO DATA"]])

    ncols = max(len(row) for row in data_matrix)
    normalized = [list(row) + [""] * (ncols - len(row)) for row in data_matrix]
    if col_widths is None:
        from reportlab.lib.units import cm
        available = (24.5 if landscape else 17.0) * cm
        weights = []
        for col in range(ncols):
            max_len = max(len(str(row[col])) for row in normalized)
            weights.append(min(max(max_len, 8), 42))
        total = sum(weights) or 1.0
        col_widths = [available * weight / total for weight in weights]

    normalized = [[_cell(value, row_index == 0) for value in row] for row_index, row in enumerate(normalized)]
    t = LongTable(normalized, colWidths=col_widths, repeatRows=1, splitByRow=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    return t

def build_model_validity_envelope_table(validity_data: List[Dict[str, Any]], styles: Any) -> Table:
    """Formate limites e avaliações de validade física em uma tabela.

    Percorre validity_data, acrescenta domínio, pico, limite, status e nota
    e aplica indicadores de classificação com os estilos recebidos.
    """
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
    """Formate a rastreabilidade dos parâmetros de entrada.

    Transforma quality_data em linhas de parâmetro, origem, classe e confiança.
    Retorna tabela sem promover estimativas a dados medidos.
    """
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
    """Apresente as métricas escalares de desempenho com unidades.

    Lê o objeto FlightMetrics e cria linhas formatadas para o relatório.
    Não calcula uma nova trajetória nem altera as métricas.
    """
    data = [["KPI", "Value"]]
    data.append(["Apogee AGL", f"{metrics.apogee_agl:.1f} m"])
    data.append(["Max Mach", f"{metrics.max_mach:.2f} M"])
    data.append(["Max Velocity", f"{metrics.max_velocity:.1f} m/s"])
    data.append(["Max Total Acceleration (ascent)", f"{metrics.max_total_acceleration:.1f} g"])
    data.append(["Max Dynamic Pressure (Max-Q)", f"{metrics.max_dynamic_pressure/1000.0:.1f} kPa"])
    data.append(["Rail Exit Velocity", f"{metrics.rail_exit_velocity:.1f} m/s"])
    data.append(["Flight Duration", f"{metrics.flight_duration:.1f} s"])
    data.append(["Ground Drift", f"{metrics.landing_distance:.1f} m"])
    return create_standard_table(data)

def build_stability_table(metrics: FlightMetrics) -> Table:
    """Apresente margens de estabilidade nos instantes canônicos do voo.

    Lê FlightMetrics, formata os valores e retorna uma tabela ReportLab
    para comparação com os limites de engenharia.
    """
    data = [["KPI", "Value"]]
    data.append(["Static Margin (Rail Exit)", f"{metrics.static_margin_rail_exit:.2f} cal"])
    data.append(["Static Margin (Max-Q)", f"{metrics.static_margin_max_q:.2f} cal"])
    data.append(["Static Margin (Burnout)", f"{metrics.static_margin_burnout:.2f} cal"])
    data.append(["Max Angle of Attack (Ascent)", f"{metrics.max_angle_of_attack:.1f} deg"])
    return create_standard_table(data)

def build_recovery_table(metrics: FlightMetrics) -> Table:
    """Apresente eventos e resultados de recuperação disponíveis.

    Percorre as métricas de paraquedas e impacto, preserva campos sem avaliação
    e retorna uma tabela ReportLab com unidades declaradas.
    """
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
    """Formate o inventário de disponibilidade das métricas.

    Converte o mapeamento completeness em linhas com indicador de status,
    utilizando styles para a apresentação. Não preenche dados ausentes.
    """
    data = [["Subsystem", "Status"]]
    for k, v in completeness.items():
        data.append([k, _get_badge(v, styles["TableCell"])])
    return create_standard_table(data)

def build_mc_input_table(project_dir: Path, styles: Any) -> Table:
    """Apresente as distribuições declaradas no YAML Monte Carlo do projeto.

    Lê project_dir/config/monte_carlo.yaml, percorre os grupos e formata
    parâmetros e dispersões; falha de leitura produz indicação na tabela.
    """
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
    """Apresente estatísticas finitas das saídas Monte Carlo salvas.

    Lê objetos JSONL por contrato estrito, seleciona métricas numéricas
    e calcula contagem, média, desvio e percentis. Não executa simulações.
    """
    data = [["Variable", "N", "Mean", "Std", "P05", "P50", "P95"]]

    if not outputs_file.exists():
        data.append(["File Missing", "-", "-", "-", "-", "-", "-"])
        return create_standard_table(data)

    if outputs_file.suffix.lower() == ".parquet":
        records = pd.read_parquet(outputs_file).to_dict("records")
    else:
        records = read_jsonl_objects(outputs_file)

    if not records:
        data.append(["No Records", "-", "-", "-", "-", "-", "-"])
        return create_standard_table(data)

    metric_definitions = (
        ("Apogee AGL (m)", ("apogee", "apogee_agl"), 1.0),
        ("Rail Exit Vel (m/s)", ("out_of_rail_velocity", "rail_exit_velocity"), 1.0),
        ("Max Mach (M)", ("max_mach_number", "max_mach"), 1.0),
        ("Max-Q (kPa)", ("max_dynamic_pressure",), 0.001),
        ("Landing X (m)", ("x_impact", "landing_east"), 1.0),
        ("Landing Y (m)", ("y_impact", "landing_north"), 1.0),
        ("Touchdown (m/s)", ("impact_velocity", "touchdown_velocity"), 1.0),
        ("Flight Time (s)", ("t_final", "flight_duration"), 1.0),
    )
    for label, keys, scale in metric_definitions:
        raw_values = [
            next((record[key] for key in keys if key in record), None)
            for record in records
        ]
        values = finite_numeric_values(raw_values, label) * scale
        count, mean, standard_deviation = summarize_finite_values(values, label, ddof=1)
        if count:
            percentiles = np.percentile(values, [5, 50, 95])
            if not np.isfinite(percentiles).all():
                raise ValueError(f"Metric {label!r} percentile calculation overflowed finite range")
            mean_text = f"{mean:.2f}" if mean is not None else "N/A"
            std_text = f"{standard_deviation:.2f}" if standard_deviation is not None else "N/A"
            percentile_text = [f"{value:.2f}" for value in percentiles]
        else:
            mean_text = std_text = "N/A"
            percentile_text = ["N/A", "N/A", "N/A"]
        data.append([
            label,
            str(count),
            mean_text,
            std_text,
            *percentile_text,
        ])

    return create_standard_table(data)
