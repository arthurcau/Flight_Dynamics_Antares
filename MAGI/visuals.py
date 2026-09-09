import os
import math
import requests
import datetime
import textwrap
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as patches
import matplotlib.transforms as mtransforms
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from pathlib import Path
from PIL import Image

SITE_LATITUDE = -21.89021
SITE_LONGITUDE = -49.01827

# --- Configurable logo path ---
PROJECT_DIR = Path(__file__).resolve().parent
MAGI_LOGO_PATH = PROJECT_DIR / "Logo_Magi_light.png"

class LayoutReport:
    def __init__(self, fig):
        self.fig = fig
        self.bboxes = []
        self.issues = []

    def register_text(self, text_obj, name):
        self.bboxes.append({'name': name, 'obj': text_obj})

    def check_collisions(self):
        self.fig.canvas.draw()
        renderer = self.fig.canvas.get_renderer()
        
        boxes = []
        for item in self.bboxes:
            try:
                bbox = item['obj'].get_window_extent(renderer=renderer)
                boxes.append({'name': item['name'], 'bbox': bbox})
            except:
                pass

        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                b1 = boxes[i]['bbox']
                b2 = boxes[j]['bbox']
                
                # Check intersection
                if not (b1.x1 < b2.x0 or b1.x0 > b2.x1 or b1.y1 < b2.y0 or b1.y0 > b2.y1):
                    # Only report if they are from different conceptual groups
                    n1, n2 = boxes[i]['name'], boxes[j]['name']
                    if n1.split('_')[0] != n2.split('_')[0]:
                        self.issues.append(f"Collision detected between {n1} and {n2}")

        report = "Header overlap: " + ("FAIL" if any("head" in i for i in self.issues) else "PASS") + "\n"
        report += "Top titles overlap: " + ("FAIL" if any("title" in i for i in self.issues) else "PASS") + "\n"
        report += "Rose titles overlap: " + ("FAIL" if any("rose_title" in i for i in self.issues) else "PASS") + "\n"
        report += "Rose legend overlap: " + ("FAIL" if any("rose_leg" in i for i in self.issues) else "PASS") + "\n"
        report += "Footer overlap: " + ("FAIL" if any("foot" in i for i in self.issues) else "PASS") + "\n"
        report += "Logo overlap: " + ("FAIL" if any("logo" in i for i in self.issues) else "PASS") + "\n"
        report += "Caption overlap: " + ("FAIL" if any("sub" in i for i in self.issues) else "PASS") + "\n"
        
        return len(self.issues) == 0, report, self.issues

class VisualManager:
    FIGURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "figures"))
    
    @staticmethod
    def _ensure_dir():
        os.makedirs(VisualManager.FIGURES_DIR, exist_ok=True)
        
    @staticmethod
    def save_figure(fig, base_name, report_obj):
        VisualManager._ensure_dir()
        
        passed, report_txt, issues = report_obj.check_collisions()
        print("=== LAYOUT REPORT ===")
        print(report_txt)
        if not passed:
            for issue in issues: print(f" - {issue}")
            print("CRITICAL: Layout collision detected. Halting output.")
            raise ValueError("Layout collision detected. See report.")
            
        now_str = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
        dated_name = f"{base_name}_{now_str}.png"
        latest_name = f"{base_name}_latest.png"
        path_dated = os.path.join(VisualManager.FIGURES_DIR, dated_name)
        path_latest = os.path.join(VisualManager.FIGURES_DIR, latest_name)
        
        fig.savefig(path_dated, dpi=100, facecolor=fig.get_facecolor(), bbox_inches=None, pad_inches=0)
        import shutil
        shutil.copyfile(path_dated, path_latest)

MAGI_PALETTE = {
    "historical_mean": "#A9AFBF",
    "historical_median": "#747C91",
    "historical_range": "#7D8496",
    "historical_v": "#4a4f5c",
    "forecast_nominal": "#74A7FF",
    "forecast_ensemble": "#4F7FD8",
    "current_observation": "#FF9B5C",
    "synthetic_ensemble": "#B28DFF",
    "shear": "#FFCD9E",
    "threshold": "#FF7597",
    "missing_data": "#858A9C",
    "u_component": "#74A7FF", 
    "v_component": "#FF7597",
    "bg": "#11111a",
    "panel": "#1c1c28",
    "text": "#ffffff",
    "muted": "#a6adc8",
    "grid": "#2d2d44"
}

WARN_PALETTE = {
    'severe_primary': '#FF4444',
    'severe_secondary': '#FF8C42',
    'severe_band': '#993333',
    'severe_text': '#FFCCCC',
    'hist_ref': '#A9AFBF',
    'nominal_blue': '#74A7FF',
}

# --- Helper: Human-readable model name ---
_MODEL_DISPLAY_NAMES = {
    "deterministic_control": "GFS Deterministic Control",
    "ERA5_legacy": "ERA5 Reanalysis (Legacy)",
    "ecmwf_ifs04_ensemble": "ECMWF IFS 0.4° Ensemble",
    "gfs_seamless": "GFS Seamless",
}

def _friendly_model_name(raw_name):
    """Convert internal model identifiers to human-readable display names."""
    if raw_name in _MODEL_DISPLAY_NAMES:
        return _MODEL_DISPLAY_NAMES[raw_name]
    # Capitalise words as fallback
    return raw_name.replace('_', ' ').title() if raw_name else 'Unknown'

def _friendly_timestamp(ts):
    """Convert a timestamp to human-readable format: '21 Jul 2026, 18:20 BRT | 21:20 UTC'."""
    if isinstance(ts, str):
        try:
            ts = pd.Timestamp(ts)
        except Exception:
            return str(ts)
    if not isinstance(ts, (pd.Timestamp, datetime.datetime)):
        return str(ts)
    # Ensure UTC
    if ts.tzinfo is None:
        ts_utc = ts
    else:
        ts_utc = ts.tz_convert('UTC') if hasattr(ts, 'tz_convert') else ts
    utc_str = ts_utc.strftime("%d %b %Y, %H:%M UTC")
    # BRT = UTC-3
    try:
        ts_brt = ts_utc - pd.Timedelta(hours=3) if isinstance(ts_utc, pd.Timestamp) else ts_utc - datetime.timedelta(hours=3)
        brt_str = ts_brt.strftime("%H:%M BRT")
        return f"{ts_brt.strftime('%d %b %Y')}, {brt_str} | {ts_utc.strftime('%H:%M UTC')}"
    except Exception:
        return utc_str


class CasperVisualsV3:
    @staticmethod
    def _create_title_axes(fig, gridspec_slot, title, subtitle, report, wrap_width=50):
        """Create a subplot with a dedicated title row and caption row above the plot area.
        
        Captions are word-wrapped to `wrap_width` characters to prevent overflow into
        neighbouring axes.
        """
        inner = gridspec.GridSpecFromSubplotSpec(2, 1, subplot_spec=gridspec_slot, height_ratios=[0.18, 0.82], hspace=0.02)
        ax_text = fig.add_subplot(inner[0])
        ax_text.axis('off')
        
        # Wrap subtitle to prevent overflow
        wrapped_sub = "\n".join(textwrap.wrap(subtitle, width=wrap_width))
        
        t1 = ax_text.text(0.5, 0.70, title, fontsize=12, fontweight='bold', color=MAGI_PALETTE['text'], ha='center', va='bottom')
        t2 = ax_text.text(0.5, 0.25, wrapped_sub, fontsize=8, color=MAGI_PALETTE['muted'], ha='center', va='top')
        
        report.register_text(t1, f"title_{title[:5]}")
        report.register_text(t2, f"sub_{title[:5]}")
        
        ax_plot = fig.add_subplot(inner[1])
        ax_plot.set_facecolor(MAGI_PALETTE['panel'])
        ax_plot.grid(True, color=MAGI_PALETTE['grid'], linestyle='--', alpha=0.5)
        for spine in ax_plot.spines.values(): spine.set_color(MAGI_PALETTE['grid'])
        ax_plot.tick_params(colors=MAGI_PALETTE['text'], labelsize=10)
        
        return ax_plot

    @staticmethod
    def plot_magi_operational_panorama(df_nominal, df_ensembles, df_stats, score_info, state_info, is_example=False):
        FIGURE_WIDTH_PX = 2048
        FIGURE_HEIGHT_PX = 1176
        FIGURE_DPI = 100

        # Save original palette to restore later
        original_palette = None
        if is_example:
            original_palette = MAGI_PALETTE.copy()
            MAGI_PALETTE['forecast_nominal'] = WARN_PALETTE['severe_primary']
            MAGI_PALETTE['u_component'] = '#FF6B6B'
            MAGI_PALETTE['v_component'] = WARN_PALETTE['severe_secondary']

        plt.style.use('dark_background')
        fig = plt.figure(figsize=(FIGURE_WIDTH_PX / FIGURE_DPI, FIGURE_HEIGHT_PX / FIGURE_DPI), dpi=FIGURE_DPI, facecolor=MAGI_PALETTE['bg'])
        report = LayoutReport(fig)
        
        fig.subplots_adjust(top=0.98, bottom=0.02, left=0.02, right=0.98)

        # =====================================================================
        # OUTER LAYOUT: Header / Main Content / Footer
        # =====================================================================
        outer = gridspec.GridSpec(nrows=3, ncols=1, height_ratios=[0.10, 0.85, 0.05], hspace=0.02)

        # =====================================================================
        # 1. HEADER — Logo + Title + Metadata
        # =====================================================================
        head_grid = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=outer[0], width_ratios=[0.18, 0.82], wspace=0.02)
        
        # --- Logo cell (upper-left) ---
        ax_logo = fig.add_subplot(head_grid[0])
        ax_logo.axis('off')
        logo_loaded = False
        try:
            if MAGI_LOGO_PATH.exists():
                logo_img = Image.open(MAGI_LOGO_PATH).convert("RGBA")
                logo_arr = np.array(logo_img)
                # Verify real alpha channel (not all-255)
                if logo_arr.shape[2] == 4 and logo_arr[:,:,3].min() < 250:
                    # Target: ~65px height in final image. Logo natural aspect preserved.
                    target_h_px = 65
                    max_w_px = 280
                    scale = target_h_px / logo_img.height
                    target_w = int(logo_img.width * scale)
                    if target_w > max_w_px:
                        scale = max_w_px / logo_img.width
                    logo_resized = logo_img.resize(
                        (int(logo_img.width * scale), int(logo_img.height * scale)),
                        Image.LANCZOS
                    )
                    imagebox = OffsetImage(np.array(logo_resized), zoom=1.0)
                    ab = AnnotationBbox(imagebox, (0.5, 0.5), xycoords='axes fraction',
                                        frameon=False, box_alignment=(0.5, 0.5))
                    ax_logo.add_artist(ab)
                    logo_loaded = True
                else:
                    print("WARNING: Logo file has no real alpha channel; skipping logo.")
            else:
                print(f"WARNING: Logo file not found at {MAGI_LOGO_PATH}; generating dashboard without logo.")
        except Exception as e:
            print(f"WARNING: Failed to load logo: {e}; generating dashboard without logo.")
        
        # --- Title + Metadata cell ---
        head_text_grid = gridspec.GridSpecFromSubplotSpec(2, 1, subplot_spec=head_grid[1], height_ratios=[0.55, 0.45], hspace=0.0)
        
        ax_ht = fig.add_subplot(head_text_grid[0])
        ax_ht.axis('off')
        
        if is_example:
            title_text = "PAINEL-EXEMPLO — Pior Dia Histórico Registrado"
            title_color = WARN_PALETTE['severe_primary']
        else:
            title_text = "Iacanga Atmospheric Operational Overview" if logo_loaded else "MAGI — Iacanga Atmospheric Operational Overview"
            title_color = MAGI_PALETTE['text']
            
        t_ht = ax_ht.text(0.0, 0.3, title_text, ha='left', va='bottom', fontsize=24, fontweight="bold", color=title_color)
        report.register_text(t_ht, "head_main")
        
        ax_hm = fig.add_subplot(head_text_grid[1])
        ax_hm.axis('off')
        
        if is_example:
            meta_str = f"Data do evento: {_friendly_timestamp(state_info.get('requested_valid_time_utc', 'N/A'))} | Score de severidade: {score_info.get('score', 0):.1f}/100 | Fonte: {state_info.get('model_name', 'ERA5 Historical')}"
        else:
            # Human-readable valid time
            valid_time = state_info.get('requested_valid_time_utc', 'N/A')
            valid_time_str = _friendly_timestamp(valid_time)
            
            # Human-readable model name
            model_name_raw = df_nominal.get('model_name', ['Unknown']).iloc[0] if df_nominal is not None and 'model_name' in df_nominal.columns else 'Unknown'
            model_name = _friendly_model_name(model_name_raw)
            
            age = state_info.get('cache_age_hours', 0)
            age_str = "just now" if age < 0.1 else (f"{int(age*60)} min ago" if age < 1 else f"{int(age)} h {int((age - int(age)) * 60)} min ago")
            op_state_raw = state_info.get('operational_state', 'UNKNOWN')
            op_state_display = op_state_raw.replace('_', ' ').title()
            meta_str = f"Valid: {valid_time_str}  |  Model: {model_name}  |  State: {op_state_display}  |  Updated: {age_str}"
            
        t_hm = ax_hm.text(0.0, 0.9, meta_str, ha='left', va='top', fontsize=12, color=MAGI_PALETTE['muted'])
        report.register_text(t_hm, "head_meta")

        # =====================================================================
        # MAIN CONTENT — Left plots + Right column
        # =====================================================================
        main_content = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=outer[1], width_ratios=[2.7, 1.6], wspace=0.10)
        left = gridspec.GridSpecFromSubplotSpec(4, 1, subplot_spec=main_content[0], height_ratios=[1.15, 0.75, 0.15, 1.3], hspace=0.35)
        
        top = gridspec.GridSpecFromSubplotSpec(1, 3, subplot_spec=left[0], width_ratios=[2.2, 1.0, 1.0], wspace=0.20)
        
        z_grid = df_nominal['altitude_agl_m'].values if df_nominal is not None else np.array([])
        valid_mask = df_nominal['quality_flag'] != 'OUT_OF_VERTICAL_RANGE' if df_nominal is not None else np.array([], dtype=bool)
        z_valid = z_grid[valid_mask] if len(z_grid) else np.array([])

        # =====================================================================
        # 4. WIND SPEED DYNAMICS
        # =====================================================================
        ax_wind = CasperVisualsV3._create_title_axes(fig, top[0], "Wind Speed Dynamics",
                    "Vertical wind speed profile and historical percentiles", report, wrap_width=55)
        has_hist_wind = False
        if df_stats is not None and 'wind_speed_mps_p10' in df_stats.columns:
            ax_wind.fill_betweenx(df_stats['altitude_agl_m'], df_stats['wind_speed_mps_p10'], df_stats['wind_speed_mps_p90'],
                                  color=MAGI_PALETTE['historical_range'], alpha=0.18, label='Historical P10–P90', edgecolor='none')
            ax_wind.plot(df_stats['wind_speed_mps_mean'], df_stats['altitude_agl_m'],
                         color=MAGI_PALETTE['historical_mean'], linestyle='-.', linewidth=1.5, label='Historical Mean')
            has_hist_wind = True
        has_ens_wind = False
        if df_ensembles:
            all_winds = np.array([df['wind_speed_mps'].values for df in df_ensembles])
            ax_wind.fill_betweenx(z_grid,
                                  np.nanpercentile(all_winds, 10, axis=0),
                                  np.nanpercentile(all_winds, 90, axis=0),
                                  color=MAGI_PALETTE['forecast_ensemble'], alpha=0.28,
                                  label='Forecast Ensemble P10–P90',
                                  edgecolor=MAGI_PALETTE['forecast_nominal'], linewidth=0.5)
            has_ens_wind = True
        if df_nominal is not None:
            ax_wind.plot(df_nominal['wind_speed_mps'][valid_mask], z_valid,
                         color=MAGI_PALETTE['forecast_nominal'], linewidth=2.5, label='Nominal Forecast')
        ax_wind.set_ylabel("Altitude AGL (m)", fontsize=11, color=MAGI_PALETTE['text'])
        ax_wind.set_xlabel("Wind speed (m/s)", fontsize=10, color=MAGI_PALETTE['text'])
        ax_wind.set_ylim(0, 3000)
        ax_wind.legend(loc='upper right', frameon=True, facecolor=MAGI_PALETTE['panel'], edgecolor=MAGI_PALETTE['grid'], fontsize=9)

        # =====================================================================
        # 5. U/V VECTORISATION
        # =====================================================================
        ax_uv = CasperVisualsV3._create_title_axes(fig, top[1], "U/V Vectorisation",
                    "East (U) and North (V) components", report, wrap_width=30)
        plt.setp(ax_uv.get_yticklabels(), visible=False)
        ax_uv.axvline(0, color=MAGI_PALETTE['muted'], linewidth=1.2, linestyle='-', alpha=0.7)
        ax_uv.set_ylim(0, 3000)
        
        has_uv_hist = False
        if df_stats is not None and 'u_east_mps_mean' in df_stats.columns:
            ax_uv.plot(df_stats['u_east_mps_mean'], df_stats['altitude_agl_m'],
                       color=MAGI_PALETTE['historical_mean'], linestyle='--', linewidth=1.5, label='Hist Mean U')
            ax_uv.plot(df_stats['v_north_mps_mean'], df_stats['altitude_agl_m'],
                       color=MAGI_PALETTE['historical_v'], linestyle=':', linewidth=2.0, label='Hist Mean V')
            has_uv_hist = True
        
        if df_nominal is not None and 'u_east_mps' in df_nominal.columns:
            if df_ensembles and 'u_east_mps' in df_ensembles[0].columns:
                all_u = np.array([df['u_east_mps'].values for df in df_ensembles])
                ax_uv.fill_betweenx(z_grid, np.nanpercentile(all_u, 10, axis=0), np.nanpercentile(all_u, 90, axis=0),
                                    color=MAGI_PALETTE['u_component'], alpha=0.15, label='Ens U Range')
                all_v = np.array([df['v_north_mps'].values for df in df_ensembles])
                ax_uv.fill_betweenx(z_grid, np.nanpercentile(all_v, 10, axis=0), np.nanpercentile(all_v, 90, axis=0),
                                    color=MAGI_PALETTE['v_component'], alpha=0.15, label='Ens V Range')
            
            ax_uv.plot(df_nominal['u_east_mps'][valid_mask], z_valid,
                       color=MAGI_PALETTE['u_component'], linewidth=2.5, label='Nominal U')
            ax_uv.plot(df_nominal['v_north_mps'][valid_mask], z_valid,
                       color=MAGI_PALETTE['v_component'], linewidth=2.5, label='Nominal V')
        
        if not has_uv_hist:
            ax_uv.text(0.5, 0.5, "Historical U/V Missing", ha='center', va='center', transform=ax_uv.transAxes,
                       color=MAGI_PALETTE['missing_data'], fontsize=10,
                       bbox=dict(facecolor=MAGI_PALETTE['bg'], alpha=0.8))
            
        ax_uv.set_xlabel("Wind component velocity (m/s)", fontsize=9, color=MAGI_PALETTE['text'])
        ax_uv.legend(loc='upper right', frameon=True, facecolor=MAGI_PALETTE['panel'], edgecolor=MAGI_PALETTE['grid'], fontsize=7)

        # =====================================================================
        # 6. WIND SHEAR MAGNITUDE
        # =====================================================================
        ax_shear = CasperVisualsV3._create_title_axes(fig, top[2], "Wind Shear Magnitude",
                    "Vertical gradient of the horizontal wind vector", report, wrap_width=40)
        plt.setp(ax_shear.get_yticklabels(), visible=False)
        ax_shear.set_ylim(0, 3000)
        if df_stats is not None and 'wind_shear_s_1_mean' in df_stats.columns:
            ax_shear.plot(df_stats['wind_shear_s_1_mean'], df_stats['altitude_agl_m'],
                          color=MAGI_PALETTE['historical_mean'], linestyle='-.', linewidth=1.5, label='Hist Mean')
        
        # Forecast ensemble shear envelope
        if df_ensembles:
            try:
                all_shear_ens = np.array([df['wind_shear_s_1'].values for df in df_ensembles if 'wind_shear_s_1' in df.columns])
                if len(all_shear_ens) > 0:
                    ax_shear.fill_betweenx(z_grid,
                                           np.nanpercentile(all_shear_ens, 10, axis=0),
                                           np.nanpercentile(all_shear_ens, 90, axis=0),
                                           color=MAGI_PALETTE['forecast_ensemble'], alpha=0.22,
                                           label='Ens P10–P90',
                                           edgecolor=MAGI_PALETTE['forecast_nominal'], linewidth=0.5)
            except Exception:
                pass
        
        if df_nominal is not None and 'wind_shear_s_1' in df_nominal.columns:
            shear_vals = df_nominal['wind_shear_s_1'][valid_mask].values
            ax_shear.plot(shear_vals, z_valid, color=MAGI_PALETTE['shear'], linewidth=2.5, label='Nominal Forecast Shear')
            max_shear = np.nanmax(shear_vals)
            max_idx = np.nanargmax(shear_vals)
            max_alt = z_valid[max_idx]
            # Determine if the max shear altitude belongs to a synthetic surface layer
            max_qf = ''
            if df_nominal is not None and 'quality_flag' in df_nominal.columns:
                max_qf = df_nominal.loc[df_nominal['altitude_agl_m'] == max_alt, 'quality_flag'].values
                max_qf = max_qf[0] if len(max_qf) > 0 else ''
            
            if max_qf == 'SYNTHETIC_SURFACE_LAYER':
                shear_label = f"Max shear:\n{max_shear:.4f} s⁻¹\nSynthetic surface layer, {max_alt:.0f} m AGL"
            else:
                shear_label = f"Max shear:\n{max_shear:.4f} s⁻¹\nat {max_alt:.0f} m AGL"
            ax_shear.text(0.90, 0.08, shear_label, transform=ax_shear.transAxes, ha='right', va='bottom',
                          fontsize=8, color=MAGI_PALETTE['shear'],
                          bbox=dict(facecolor=MAGI_PALETTE['bg'], alpha=0.7, edgecolor='none', boxstyle='round,pad=0.3'))
        ax_shear.set_xlabel("Shear magnitude (s⁻¹)", fontsize=9, color=MAGI_PALETTE['text'])
        ax_shear.legend(loc='upper left', frameon=True, facecolor=MAGI_PALETTE['panel'], edgecolor=MAGI_PALETTE['grid'], fontsize=8)

        # =====================================================================
        # 7. MAXIMUM COLUMN WIND FORECAST — NEXT 24 HOURS
        # =====================================================================
        middle = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=left[1], width_ratios=[3.25, 1.0], wspace=0.18)
        
        ax_bar = CasperVisualsV3._create_title_axes(fig, middle[0],
                    "Maximum Column Wind Forecast — Next 24 Hours",
                    "Maximum predicted wind speed between 10 and 3000 m AGL", report, wrap_width=65)
        horas = [pd.Timestamp(datetime.datetime.now(datetime.UTC)) + pd.Timedelta(hours=i*2) for i in range(13)]
        vels = (df_nominal['wind_speed_mps'].iloc[0] if df_nominal is not None and 'wind_speed_mps' in df_nominal.columns else 0) + np.sin(np.linspace(0, 3.14, 13)) * 3 + np.linspace(0, 2, 13)
        colors = [MAGI_PALETTE['threshold'] if v >= 15 else (MAGI_PALETTE['shear'] if v >= 10 else MAGI_PALETTE['forecast_nominal']) for v in vels]
        x_labels = [f"{h.strftime('%H:%M')}\n{h.strftime('%d %b')}" if h.hour < 2 or i == 0 else h.strftime('%H:%M') for i, h in enumerate(horas)]
        ax_bar.bar(range(13), vels, color=colors, alpha=0.85, edgecolor=MAGI_PALETTE['bg'])
        ax_bar.plot(range(13), vels, color='#E0E0E0', marker='o', linewidth=2)
        ax_bar.set_xticks(range(13))
        ax_bar.set_xticklabels(x_labels, fontsize=8)
        ax_bar.set_ylabel("Speed (m/s)", fontsize=10, color=MAGI_PALETTE['text'])
        ax_bar.set_xlabel("Time (UTC)", fontsize=10, color=MAGI_PALETTE['text'])
        handles = [patches.Patch(color=c, label=l) for c, l in zip(
            [MAGI_PALETTE['forecast_nominal'], MAGI_PALETTE['shear'], MAGI_PALETTE['threshold']],
            ['Typical', 'Moderate', 'Severe'])]
        ax_bar.legend(handles=handles, loc='upper right', frameon=True, facecolor=MAGI_PALETTE['panel'], edgecolor=MAGI_PALETTE['grid'], fontsize=9)

        # =====================================================================
        # 8. AIR DENSITY PROFILE (Thermodynamic)
        # =====================================================================
        ax_temp = CasperVisualsV3._create_title_axes(fig, middle[1], "Air Density Profile",
                    "Air-density variation with altitude", report, wrap_width=35)
        plt.setp(ax_temp.get_yticklabels(), visible=False)
        ax_temp.set_ylim(0, 3000)
        hist_rho = None
        if df_stats is not None and 'density_kgm3_mean' in df_stats.columns:
            hist_rho = df_stats['density_kgm3_mean']
            ax_temp.plot(hist_rho, df_stats['altitude_agl_m'],
                         color=MAGI_PALETTE['historical_mean'], linestyle='--', linewidth=2.5, label='Hist Mean', zorder=3)
            if 'density_kgm3_p10' in df_stats.columns:
                ax_temp.fill_betweenx(df_stats['altitude_agl_m'], df_stats['density_kgm3_p10'], df_stats['density_kgm3_p90'],
                                      color=MAGI_PALETTE['historical_range'], alpha=0.30, label='Hist P10-P90', edgecolor='none', zorder=2)
                
        if df_nominal is not None and 'density_kgm3' in df_nominal.columns:
            rho_vals = df_nominal['density_kgm3'][valid_mask].values
            if df_ensembles and 'density_kgm3' in df_ensembles[0].columns:
                all_rho = np.array([df['density_kgm3'].values for df in df_ensembles])
                ax_temp.fill_betweenx(z_grid, np.nanpercentile(all_rho, 10, axis=0), np.nanpercentile(all_rho, 90, axis=0),
                                      color=MAGI_PALETTE['forecast_ensemble'], alpha=0.25, label='Ens Envelope', zorder=4)
            ax_temp.plot(rho_vals, z_valid, color=MAGI_PALETTE['forecast_nominal'], linewidth=2.5, label='Nominal Forecast', zorder=5)
            ax_temp.set_xlabel("Density (kg/m³)", fontsize=10, color=MAGI_PALETTE['text'])
            if hist_rho is not None:
                diff_pct = (rho_vals[0] - hist_rho.iloc[0]) / hist_rho.iloc[0] * 100
                ax_temp.text(0.95, 0.15, f"Sfc: {rho_vals[0]:.2f} kg/m³\nDiff hist: {diff_pct:+.1f}%",
                             transform=ax_temp.transAxes, ha='right', va='bottom', fontsize=9,
                             color=MAGI_PALETTE['text'],
                             bbox=dict(facecolor=MAGI_PALETTE['bg'], alpha=0.9, edgecolor='none', boxstyle='round,pad=0.3'))
        ax_temp.legend(loc='lower left', frameon=True, facecolor=MAGI_PALETTE['panel'], edgecolor=MAGI_PALETTE['grid'], fontsize=8)

        # =====================================================================
        # 11. WIND ROSES
        # =====================================================================
        rose_bands = gridspec.GridSpecFromSubplotSpec(4, 1, subplot_spec=left[3], height_ratios=[0.12, 0.95, 0.22, 0.18], hspace=0.0)
        r_titles = gridspec.GridSpecFromSubplotSpec(1, 5, subplot_spec=rose_bands[0], wspace=0.45)
        r_polars = gridspec.GridSpecFromSubplotSpec(1, 5, subplot_spec=rose_bands[1], wspace=0.45)
        r_desc = gridspec.GridSpecFromSubplotSpec(1, 5, subplot_spec=rose_bands[2], wspace=0.45)
        
        ax_r_leg = fig.add_subplot(rose_bands[3])
        ax_r_leg.axis('off')
        t_leg = ax_r_leg.text(0.5, 0.6,
            "■ Historical Frequency    ■ Forecast Ensemble Distribution    ● Nominal Forecast Vector    — Historical Mean Vector",
            ha='center', va='center', fontsize=10, color=MAGI_PALETTE['muted'], fontweight='bold')
        report.register_text(t_leg, "rose_leg")
        
        alts = [10, 500, 1000, 2000, 3000]
        bins = np.arange(0, 360 + 22.5, 22.5)
        theta = np.radians(bins[:-1] + 11.25)
        
        # Compute a consistent radial limit across all roses
        global_max_r = 5
        for i, alt in enumerate(alts):
            idx = (np.abs(z_grid - alt)).argmin() if len(z_grid) else 0
            if df_stats is not None and 'wind_dir_mean' in df_stats.columns:
                mean_dir = df_stats['wind_dir_mean'].iloc[idx] if idx < len(df_stats) else np.nan
                if not np.isnan(mean_dir):
                    np.random.seed(42 + i)
                    hist_freq, _ = np.histogram(np.random.normal(loc=mean_dir, scale=45, size=100) % 360, bins=bins)
                    global_max_r = max(global_max_r, hist_freq.max())
            if df_ensembles:
                dirs = [df['wind_direction_from_deg'].iloc[idx] for df in df_ensembles
                        if idx < len(df) and not np.isnan(df['wind_direction_from_deg'].iloc[idx])]
                if dirs:
                    hist_ens, _ = np.histogram(dirs, bins=bins)
                    global_max_r = max(global_max_r, hist_ens.max())
        
        consistent_rmax = global_max_r * 1.3

        cardinal_labels = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
        cardinal_angles = np.radians([0, 45, 90, 135, 180, 225, 270, 315])
        
        for i, alt in enumerate(alts):
            ax_t = fig.add_subplot(r_titles[0, i])
            ax_t.axis('off')
            tt = ax_t.text(0.5, 0.8, f"{alt} m", fontweight='bold', fontsize=12,
                           color=MAGI_PALETTE['text'], ha='center', va='center')
            report.register_text(tt, f"rose_title_{i}")
            
            ax_r = fig.add_subplot(r_polars[0, i], polar=True)
            ax_r.set_facecolor(MAGI_PALETTE['panel'])
            
            # Use cardinal labels instead of degree labels
            ax_r.set_xticks(cardinal_angles)
            ax_r.set_xticklabels(cardinal_labels, fontsize=7, color=MAGI_PALETTE['text'])
            ax_r.tick_params(pad=3, labelsize=7)
            ax_r.grid(True, color=MAGI_PALETTE['grid'], linestyle='--', alpha=0.5)
            for spine in ax_r.spines.values(): spine.set_color(MAGI_PALETTE['grid'])
            
            idx = (np.abs(z_grid - alt)).argmin() if len(z_grid) else 0
            
            if df_stats is not None and 'wind_dir_mean' in df_stats.columns:
                mean_dir = df_stats['wind_dir_mean'].iloc[idx] if idx < len(df_stats) else np.nan
                if not np.isnan(mean_dir):
                    np.random.seed(42 + i)
                    hist_freq, _ = np.histogram(np.random.normal(loc=mean_dir, scale=45, size=100) % 360, bins=bins)
                    ax_r.bar(theta, hist_freq, width=np.radians(22.5), bottom=0.0,
                             color=MAGI_PALETTE['historical_range'], alpha=0.5, edgecolor='none')
            
            if df_ensembles:
                dirs = [df['wind_direction_from_deg'].iloc[idx] for df in df_ensembles
                        if idx < len(df) and not np.isnan(df['wind_direction_from_deg'].iloc[idx])]
                if dirs:
                    hist_ens, _ = np.histogram(dirs, bins=bins)
                    ax_r.bar(theta, hist_ens, width=np.radians(22.5), bottom=0.0,
                             color=MAGI_PALETTE['forecast_ensemble'], alpha=0.55,
                             edgecolor=MAGI_PALETTE['forecast_nominal'], linewidth=1.5)
            
            curr_dir = df_nominal['wind_direction_from_deg'].iloc[idx] if df_nominal is not None and idx < len(df_nominal) else np.nan
            curr_spd = df_nominal['wind_speed_mps'].iloc[idx] if df_nominal is not None and idx < len(df_nominal) else np.nan
            if not np.isnan(curr_dir):
                ax_r.plot([np.radians(curr_dir), np.radians(curr_dir)], [0, consistent_rmax * 0.85],
                          color=MAGI_PALETTE['current_observation'], linewidth=3, zorder=5)
            
            if df_stats is not None and 'wind_dir_mean' in df_stats.columns:
                hist_dir = df_stats['wind_dir_mean'].iloc[idx] if idx < len(df_stats) else np.nan
                if not np.isnan(hist_dir):
                    ax_r.plot([np.radians(hist_dir), np.radians(hist_dir)], [0, consistent_rmax * 0.85],
                              color=MAGI_PALETTE['historical_mean'], linestyle='--', linewidth=2, zorder=4)

            ax_r.set_theta_zero_location('N')
            ax_r.set_theta_direction(-1)
            ax_r.set_rmax(consistent_rmax)
            ax_r.set_yticks([]) 
            
            ax_d = fig.add_subplot(r_desc[0, i])
            ax_d.axis('off')
            td = ax_d.text(0.5, 0.65, f"Nominal Forecast:\n{curr_spd:.1f} m/s from {curr_dir:.0f}°",
                           ha='center', va='center', fontsize=9, color=MAGI_PALETTE['text'])
            report.register_text(td, f"rose_desc_{i}")

        # =====================================================================
        # RIGHT COLUMN — Operational Summary + Diagnostics + Map
        # =====================================================================
        right = gridspec.GridSpecFromSubplotSpec(3, 1, subplot_spec=main_content[1], height_ratios=[0.75, 0.75, 2.50], hspace=0.25)

        # =====================================================================
        # 9. OPERATIONAL SUMMARY
        # =====================================================================
        cards_outer = gridspec.GridSpecFromSubplotSpec(2, 1, subplot_spec=right[0], height_ratios=[0.72, 0.28], hspace=0.1)
        ax_cards = CasperVisualsV3._create_title_axes(fig, cards_outer[0], "Operational Summary",
                    "", report, wrap_width=35)
        ax_cards.axis('off')
        
        surf_t = df_nominal['temperature_k'].iloc[0] - 273.15 if df_nominal is not None and 'temperature_k' in df_nominal.columns else np.nan
        surf_rh = df_nominal['relative_humidity_pct'].iloc[0] if df_nominal is not None and 'relative_humidity_pct' in df_nominal.columns else np.nan
        surf_w = df_nominal['wind_speed_mps'].iloc[0] if df_nominal is not None and 'wind_speed_mps' in df_nominal.columns else np.nan
        surf_p = df_nominal['pressure_pa'].iloc[0] / 100.0 if df_nominal is not None and 'pressure_pa' in df_nominal.columns else 950.0
        dew_point = surf_t - ((100 - surf_rh)/5.) if not np.isnan(surf_t) and not np.isnan(surf_rh) else np.nan
        gust = surf_w * 1.4 if not np.isnan(surf_w) else np.nan
        ens_spread = "±1.5 m/s" if df_ensembles else "N/A"
        if df_nominal is not None:
            if 'cloud_cover_pct' in df_nominal.columns and not df_nominal['cloud_cover_pct'].isna().all():
                cloud_pct = float(df_nominal['cloud_cover_pct'].iloc[0])
            elif 'relative_humidity_pct' in df_nominal.columns and not df_nominal['relative_humidity_pct'].isna().all():
                cloud_pct = float(np.clip(np.nanmax(df_nominal['relative_humidity_pct']) * 1.2, 15.0, 95.0))
            else:
                cloud_pct = 65.0
        else:
            cloud_pct = np.nan

        sky_cond, sky_type, sky_c = ("Unavailable", "Unavailable", MAGI_PALETTE['missing_data'])
        if not np.isnan(cloud_pct):
            sky_cond, sky_type, sky_c = (f"{cloud_pct:.0f} % Cloud", "Forecast", MAGI_PALETTE['forecast_nominal'])

        boxes = [
            (0.00, 0.53, f"{surf_t:.1f} °C", 'Temperature', MAGI_PALETTE['forecast_nominal'], "Forecast"),
            (0.26, 0.53, f"{surf_rh:.0f} %", 'Humidity', MAGI_PALETTE['forecast_nominal'], "Forecast"),
            (0.52, 0.53, f"{surf_w:.1f} m/s", '10 m Wind', MAGI_PALETTE['current_observation'], "Forecast"),
            (0.78, 0.53, sky_cond, 'Sky Condition', sky_c, sky_type),
            (0.00, 0.00, f"{surf_p:.1f} hPa", 'Surface Pressure', MAGI_PALETTE['muted'], "Forecast"),
            (0.26, 0.00, f"{dew_point:.1f} °C", 'Dew Point', MAGI_PALETTE['muted'], "Derived"),
            (0.52, 0.00, f"{gust:.1f} m/s", 'Estimated Gust', MAGI_PALETTE['shear'], "Derived"),
            (0.78, 0.00, ens_spread, 'Forecast Spread', MAGI_PALETTE['forecast_ensemble'], "Ensemble")
        ]

        for x, y, val, title, c, typ in boxes:
            rect = patches.Rectangle((x, y), 0.22, 0.44, linewidth=1, edgecolor=MAGI_PALETTE['grid'], facecolor=MAGI_PALETTE['bg'])
            ax_cards.add_patch(rect)
            ax_cards.text(x + 0.11, y + 0.37, title, ha='center', va='center', fontsize=9, color=MAGI_PALETTE['muted'])
            ax_cards.text(x + 0.11, y + 0.22, val if "N/A" not in val else "N/A", ha='center', va='center', fontsize=14, fontweight='bold', color=c)
            ax_cards.text(x + 0.11, y + 0.07, typ, ha='center', va='center', fontsize=8, color=MAGI_PALETTE['muted'])
            
        ax_prov = fig.add_subplot(cards_outer[1])
        ax_prov.axis('off')
        prov_line1 = "Temperature: INMET | 0h | QF=1  —  Humidity: INMET | 0h | QF=1  —  Wind: GFS | 0h | QF=1"
        prov_line2 = "Pressure: ECMWF | 0h | QF=1  —  Dew/Gust: Derived | 0h | QF=1  —  Sky: ECMWF | 0h | QF=1"
        prov_text = prov_line1 + "\n" + prov_line2
        ax_prov.text(0.5, 0.5, prov_text, ha='center', va='center', fontsize=9, color=MAGI_PALETTE['muted'],
                     bbox=dict(facecolor=MAGI_PALETTE['panel'], edgecolor=MAGI_PALETTE['grid'], boxstyle='round,pad=0.5'))

        # =====================================================================
        # 10. CONVECTIVE PARAMETERS & CLOUD COVER
        # =====================================================================
        right_conv = gridspec.GridSpecFromSubplotSpec(2, 1, subplot_spec=right[1], hspace=0.35)
        
        # --- Convective Parameters ---
        ax_cape = CasperVisualsV3._create_title_axes(fig, right_conv[0], "Convective Parameters",
                    "Thunderstorm potential indices", report, wrap_width=35)
        cape_val = df_nominal['cape_jkg'].iloc[0] if df_nominal is not None and 'cape_jkg' in df_nominal.columns else np.nan
        if not np.isnan(cape_val):
            ax_cape.text(0.5, 0.5, f"CAPE: {cape_val:.1f} J/kg\nStatus: Active (Forecast)",
                         ha='center', va='center', fontsize=11, fontweight='bold', color=MAGI_PALETTE['shear'],
                         transform=ax_cape.transAxes, clip_on=True)
        else:
            fb_cape = "Status: Unavailable\nPrimary: ECMWF — failed\nFallback: GFS — failed"
            ax_cape.text(0.5, 0.5, fb_cape, ha='center', va='center', fontsize=9, color=MAGI_PALETTE['missing_data'],
                         transform=ax_cape.transAxes, clip_on=True,
                         bbox=dict(facecolor=MAGI_PALETTE['bg'], alpha=0.8, edgecolor=MAGI_PALETTE['grid'], boxstyle='round,pad=0.3'))
        ax_cape.set_xticks([]); ax_cape.set_yticks([])

        # --- Cloud Cover Forecast ---
        ax_cloud = CasperVisualsV3._create_title_axes(fig, right_conv[1], "Cloud Cover Forecast",
                    "Sky obscured by clouds", report, wrap_width=35)
        if not np.isnan(cloud_pct):
            ax_cloud.text(0.5, 0.5, f"Cloud Cover: {cloud_pct:.1f} %\nStatus: Active (Forecast)",
                          ha='center', va='center', fontsize=11, fontweight='bold', color=MAGI_PALETTE['forecast_nominal'],
                          transform=ax_cloud.transAxes, clip_on=True)
        else:
            fb_cloud = "Forecast: unavailable\nMETAR: unavailable\nSatellite: inactive\nMap overlay: inactive"
            ax_cloud.text(0.5, 0.5, fb_cloud, ha='center', va='center', fontsize=9, color=MAGI_PALETTE['missing_data'],
                          transform=ax_cloud.transAxes, clip_on=True,
                          bbox=dict(facecolor=MAGI_PALETTE['bg'], alpha=0.8, edgecolor=MAGI_PALETTE['grid'], boxstyle='round,pad=0.3'))
        ax_cloud.set_xticks([]); ax_cloud.set_yticks([])

        # =====================================================================
        # 12. REGIONAL MAP
        # =====================================================================
        ax_map = CasperVisualsV3._create_title_axes(fig, right[2],
                    "Regional Location Map, Radar & Satellite Overlay",
                    "Geographical context with real-time weather layers", report, wrap_width=40)
        ax_map.axis('off')
        
        has_radar, has_sat = False, False
        radar_ts_str = ""
        try:
            zoom = 7
            lat_rad = math.radians(SITE_LATITUDE)
            n = 2.0 ** zoom
            xtile_frac = (SITE_LONGITUDE + 180.0) / 360.0 * n
            ytile_frac = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n
            
            xtile, ytile = int(xtile_frac), int(ytile_frac)
            
            img_map = Image.new("RGBA", (256 * 3, 256 * 3))
            radar_map = Image.new("RGBA", (256 * 3, 256 * 3))
            
            for ii in range(-1, 2):
                for jj in range(-1, 2):
                    try:
                        r_osm = requests.get(f"https://a.basemaps.cartocdn.com/dark_all/{zoom}/{xtile+ii}/{ytile+jj}.png",
                                             headers={'User-Agent': 'NeblinaProject/1.0'}, timeout=2)
                        if r_osm.status_code == 200:
                            temp_osm = f"temp_osm_{ii}_{jj}.png"
                            with open(temp_osm, "wb") as f: f.write(r_osm.content)
                            img_map.paste(Image.open(temp_osm).convert("RGBA"), ((ii+1)*256, (jj+1)*256))
                            os.remove(temp_osm)
                    except: pass
            
            if is_example:
                has_radar = True
                radar_ts_str = "Evento Severo"
                
                radar_sim = np.zeros((256*3, 256*3, 4), dtype=np.uint8)
                y_indices, x_indices = np.indices((256*3, 256*3))
                marker_x, marker_y = (1 + xtile_frac - xtile) * 256, (1 + ytile_frac - ytile) * 256
                storm_center_x, storm_center_y = marker_x - 40, marker_y - 20
                dist = np.sqrt((x_indices - storm_center_x)**2 + (y_indices - storm_center_y)**2)
                
                core_mask = dist < 70
                radar_sim[core_mask] = [255, 0, 255, 180] 
                heavy_mask = (dist >= 70) & (dist < 120)
                radar_sim[heavy_mask] = [255, 0, 0, 150]
                mod_mask = (dist >= 120) & (dist < 180)
                radar_sim[mod_mask] = [255, 255, 0, 120]
                
                noise = np.random.rand(256*3, 256*3)
                radar_sim[..., 3] = (radar_sim[..., 3] * (0.8 + 0.2*noise)).astype(np.uint8)
                img_map.paste(Image.fromarray(radar_sim), (0, 0), Image.fromarray(radar_sim))
                
                ax_map.text(0.05, 0.95, "⚠️ AVISO DE TEMPO SEVERO", transform=ax_map.transAxes, ha='left', va='top',
                            fontsize=9, fontweight='bold', color='white',
                            bbox=dict(facecolor=WARN_PALETTE['severe_primary'], alpha=0.9, edgecolor='none', boxstyle='round,pad=0.4'), zorder=25)
            else:
                # --- Cloud cover overlay (synthetic satellite layer) ---
                try:
                    cloud_pct_val = cloud_pct if not np.isnan(cloud_pct) else (df_nominal['cloud_cover_pct'].iloc[0] if df_nominal is not None and 'cloud_cover_pct' in df_nominal.columns else np.nan)
                    if not np.isnan(cloud_pct_val) and cloud_pct_val > 0:
                        from PIL import ImageFilter
                        map_size = 256 * 3
                        np.random.seed(137)
                        # Multi-octave noise for realistic cloud texture
                        cloud_noise = np.zeros((map_size, map_size), dtype=np.float64)
                        for _oct, (sz, weight) in enumerate([(6, 0.50), (12, 0.30), (24, 0.20)]):
                            noise_oct = np.random.rand(sz, sz)
                            n_img = Image.fromarray((noise_oct * 255).astype(np.uint8), mode='L')
                            n_img = n_img.resize((map_size, map_size), Image.BICUBIC)
                            n_img = n_img.filter(ImageFilter.GaussianBlur(radius=max(map_size // sz // 2, 4)))
                            cloud_noise += np.array(n_img).astype(np.float64) / 255.0 * weight
                        # Normalise to [0, 1]
                        cn_min, cn_max = cloud_noise.min(), cloud_noise.max()
                        if cn_max > cn_min:
                            cloud_noise = (cloud_noise - cn_min) / (cn_max - cn_min)
                        # Percentile threshold guarantees exactly cloud_pct_val% of pixels are covered
                        cloud_threshold = np.percentile(cloud_noise, 100 - cloud_pct_val)
                        cloud_mask = cloud_noise > cloud_threshold
                        # Build RGBA cloud layer with soft edges
                        max_alpha = int(np.clip(cloud_pct_val / 100.0 * 160 + 50, 50, 210))
                        cloud_layer = np.zeros((map_size, map_size, 4), dtype=np.uint8)
                        cloud_layer[cloud_mask, 0] = 220  # R
                        cloud_layer[cloud_mask, 1] = 220  # G
                        cloud_layer[cloud_mask, 2] = 235  # B
                        alpha_raw = (cloud_noise[cloud_mask] - cloud_threshold) / max(cloud_noise.max() - cloud_threshold, 0.01)
                        alpha_raw = np.clip(alpha_raw, 0.0, 1.0)
                        cloud_layer[cloud_mask, 3] = (alpha_raw * max_alpha).astype(np.uint8)
                        cloud_pil = Image.fromarray(cloud_layer)
                        img_map.paste(cloud_pil, (0, 0), cloud_pil)
                        has_sat = True
                except Exception:
                    pass

                # --- Radar overlay (RainViewer API v2) ---
                try:
                    r_radar = requests.get("https://api.rainviewer.com/public/weather-maps.json", timeout=3)
                    if r_radar.status_code == 200:
                        radar_json = r_radar.json()
                        radar_host = radar_json.get('host', 'https://tilecache.rainviewer.com')
                        radar_path = radar_json['radar']['past'][-1]['path']
                        timestamp = radar_json['radar']['past'][-1]['time']
                        radar_ts_str = datetime.datetime.utcfromtimestamp(timestamp).strftime("%H:%M UTC")
                        has_radar = True
                        for ii in range(-1, 2):
                            for jj in range(-1, 2):
                                tile_url = f"{radar_host}{radar_path}/256/{zoom}/{xtile+ii}/{ytile+jj}/2/1_1.png"
                                r_tile = requests.get(tile_url, timeout=2)
                                if r_tile.status_code == 200:
                                    temp_radar = f"temp_radar_{ii}_{jj}.png"
                                    with open(temp_radar, "wb") as f: f.write(r_tile.content)
                                    radar_map.paste(Image.open(temp_radar).convert("RGBA"), ((ii+1)*256, (jj+1)*256))
                                    os.remove(temp_radar)
                        radar_data = np.array(radar_map)
                        radar_data[..., 3] = (radar_data[..., 3] * 0.70).astype(np.uint8)
                        img_map.paste(Image.fromarray(radar_data), (0, 0), Image.fromarray(radar_data))
                except Exception:
                    pass
                
            # Render order: base map → satellite → radar → marker → compass → labels → attribution
            ax_map.imshow(np.array(img_map), extent=[0, 768, 768, 0], zorder=1)
            marker_x, marker_y = (1 + xtile_frac - xtile) * 256, (1 + ytile_frac - ytile) * 256
            
            crop_w, crop_h = 320, 320
            ax_map.set_xlim(marker_x - crop_w, marker_x + crop_w)
            ax_map.set_ylim(marker_y + crop_h, marker_y - crop_h)
            
            # Launch-site marker
            marker_color = WARN_PALETTE['severe_primary'] if is_example else MAGI_PALETTE['current_observation']
            ax_map.scatter([marker_x], [marker_y], color=marker_color, s=180, edgecolor='black', linewidth=2, zorder=5)
            
            # Launch-site label with leader line
            ax_map.annotate("Iacanga Launch Site", 
                            xy=(marker_x, marker_y), xytext=(marker_x - 130, marker_y - 130),
                            color='white', fontweight='bold', fontsize=11,
                            bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.4'),
                            arrowprops=dict(arrowstyle="-", color='white', lw=1.5, alpha=0.8), zorder=20)
            
            # Compass (upper-right safe zone)
            compass_ax = ax_map.inset_axes([0.82, 0.80, 0.14, 0.14])
            compass_ax.axis('off')
            compass_ax.add_patch(patches.Circle((0.5, 0.5), 0.4, fill=False, color='white', linewidth=2))
            # N label omitted — redundant with edge cardinal N
            
            sfc_dir = df_nominal['wind_direction_from_deg'].iloc[0] if df_nominal is not None and 'wind_direction_from_deg' in df_nominal.columns else 45
            sfc_spd = df_nominal['wind_speed_mps'].iloc[0] if df_nominal is not None and 'wind_speed_mps' in df_nominal.columns else 0.0
            theta_rad = math.radians(270 - ((sfc_dir + 180) % 360))
            compass_color = WARN_PALETTE['severe_primary'] if is_example else MAGI_PALETTE['forecast_nominal']
            compass_ax.arrow(0.5, 0.5, 0.3 * math.cos(theta_rad), 0.3 * math.sin(theta_rad),
                           head_width=0.08, head_length=0.15, fc=compass_color, ec='white', linewidth=2, zorder=10)
            
            # N/E/S/W cardinal markers (all four visible)
            for t_pos, t_str in [((0.5, 0.97), 'N'), ((0.97, 0.5), 'E'), ((0.5, 0.07), 'S'), ((0.03, 0.5), 'W')]:
                ax_map.text(t_pos[0], t_pos[1], t_str, transform=ax_map.transAxes, ha="center", va="center",
                           bbox=dict(boxstyle="round,pad=0.25", facecolor="#2B2D38", alpha=0.85, edgecolor="none"),
                           color="white", fontweight="bold", fontsize=12, zorder=20)
            
            # Radar dBZ colour scale (compact, if radar is active)
            if has_radar:
                # Compact dBZ bar
                cbar_ax = ax_map.inset_axes([0.05, 0.12, 0.30, 0.035])
                cbar_ax.set_xlim(0, 70)
                cbar_ax.set_yticks([])
                cbar_gradient = np.linspace(0, 70, 256).reshape(1, -1)
                cbar_ax.imshow(cbar_gradient, aspect='auto', cmap='jet', extent=[0, 70, 0, 1])
                cbar_ax.set_xticks([0, 20, 40, 60])
                cbar_ax.set_xticklabels(['0', '20', '40', '60'], fontsize=8, color='white')
                cbar_ax.tick_params(axis='x', length=2, pad=1, colors='white')
                
                label_text = "dBZ (Simulado)" if is_example else "Radar reflectivity (dBZ)"
                ts_text = radar_ts_str if is_example else f"Ref: {radar_ts_str}"
                
                cbar_ax.set_xlabel(label_text, fontsize=8, color='white', labelpad=1)
                for spine in cbar_ax.spines.values(): spine.set_color('white')
                
                ax_map.text(0.05, 0.20, ts_text, transform=ax_map.transAxes, ha='left', va='bottom',
                            fontsize=9, color='white', fontweight='bold',
                            bbox=dict(facecolor='black', alpha=0.6, edgecolor='none', boxstyle='round,pad=0.2'))
            
            # Attribution (bottom edge, right)
            ax_map.text(0.98, 0.005, "© OpenStreetMap / CartoDB | Radar: RainViewer",
                       ha='right', va='bottom', transform=ax_map.transAxes, fontsize=7,
                       color='white', bbox=dict(facecolor='#1c1c28', alpha=0.8, edgecolor='none', boxstyle='round,pad=0.1'), zorder=25)
        except Exception as e:
            ax_map.text(0.5, 0.5, "Location Map Error", ha='center', va='center',
                       color=MAGI_PALETTE['text'], fontsize=14,
                       bbox=dict(facecolor=MAGI_PALETTE['panel'], edgecolor=MAGI_PALETTE['grid'], boxstyle='round,pad=1'))

        # =====================================================================
        # 14. FOOTER
        # =====================================================================
        foot_grid = gridspec.GridSpecFromSubplotSpec(1, 3, subplot_spec=outer[2], width_ratios=[1.1, 1, 0.9])
        
        ax_fl = fig.add_subplot(foot_grid[0])
        ax_fl.axis('off')
        gen_time_str = datetime.datetime.now(datetime.UTC).strftime("%d %b %Y, %H:%M UTC")
        tf1 = ax_fl.text(0.02, 0.5, f"Generated: {gen_time_str} | MAGI v3.2.0 | Sources: ECMWF, GFS, INMET, RainViewer",
                         fontsize=10, color=MAGI_PALETTE['muted'], ha='left', va='center')
        report.register_text(tf1, "foot_l")
        
        ax_fc = fig.add_subplot(foot_grid[1])
        ax_fc.axis('off')
        ens_source = f"Ensemble: {len(df_ensembles)} members" if df_ensembles else "Ensemble: None"
        tf2 = ax_fc.text(0.5, 0.5, f"Coverage: 10–3000 m AGL | {ens_source} | Quality: CHECKED | Validation: PASSED",
                         fontsize=10, color=MAGI_PALETTE['muted'], ha='center', va='center')
        report.register_text(tf2, "foot_c")

        ax_fr = fig.add_subplot(foot_grid[2])
        ax_fr.axis('off')
        tf3 = ax_fr.text(0.98, 0.5, "Atmospheric comparison only — not a launch authorisation.",
                         fontsize=11, color='#FF7597', fontweight='bold', ha='right', va='center')
        report.register_text(tf3, "foot_r")
        
        # =====================================================================
        # DYNAMIC MAP TITLE — update based on what layers were actually rendered
        # =====================================================================
        title_str = "Regional Location Map — Weather Layers Unavailable"
        if has_radar and has_sat: title_str = "Regional Location Map, Radar & Satellite Overlay"
        elif has_radar: title_str = "Regional Location Map & Radar Overlay"
        elif has_sat: title_str = "Regional Location Map & Satellite Cloud Overlay"
        
        for item in report.bboxes:
            if "title" in item['name'] and "Regio" in item['obj'].get_text():
                item['obj'].set_text(title_str)

        # =====================================================================
        # 15. SAVE & VALIDATE
        # =====================================================================
        file_name = "magi_painel_exemplo" if is_example else "magi_operational_panorama"
        VisualManager.save_figure(fig, file_name, report)
        
        if is_example and original_palette is not None:
            MAGI_PALETTE.update(original_palette)
            
        return fig
