import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.gridspec as gridspec
import pandas as pd
import xarray as xr
from matplotlib.lines import Line2D

def _extract_launch_site_data(dataset, latitude, longitude):
    if latitude is not None and longitude is not None:
        if "latitude" in dataset.dims and "longitude" in dataset.dims:
            ds_loc = dataset.interp(latitude=latitude, longitude=longitude, method="linear")
        else:
            ds_loc = dataset
    else:
        if "latitude" in dataset.dims and "longitude" in dataset.dims:
            ds_loc = dataset.isel(latitude=0, longitude=0)
        else:
            ds_loc = dataset
    return ds_loc

def plot_ensemble_overview(
    ensemble,
    latitude=None,
    longitude=None,
    selected_time=None,
    variable="wind_speed",
    altitude_max=30_000,
    style="report",
    show_hodograph=False,
    show_cube=True
):
    """
    Generate a publication-quality overview of the MAGI atmospheric ensemble.
    """
    # 1. Extract/Interpolate data for the launch site
    ds_loc = _extract_launch_site_data(ensemble, latitude, longitude)

    # 2. Derive wind speed if needed
    if variable == "wind_speed" and "wind_speed" not in ds_loc.data_vars:
        if "u_wind" in ds_loc.data_vars and "v_wind" in ds_loc.data_vars:
            ds_loc["wind_speed"] = np.sqrt(ds_loc["u_wind"]**2 + ds_loc["v_wind"]**2)
            ds_loc["wind_speed"].attrs["units"] = "m/s"
        else:
            raise ValueError("u_wind and v_wind are required in dataset to compute wind_speed")
            
    if variable not in ds_loc.data_vars:
        raise ValueError(f"Variable '{variable}' not found in the dataset.")

    var_data = ds_loc[variable]
    
    # 3. Handle Altitude Coordinate
    # Assuming geopotential_height is in meters
    if "geopotential_height" in ds_loc.data_vars:
        # Create a mean altitude profile across time and members for Z-axis plotting
        alt_mean = ds_loc["geopotential_height"].mean(dim=["member", "time"]).values / 1000.0
    else:
        alt_mean = ds_loc["pressure_level"].values

    # Convert altitude_max to km if needed
    alt_max_km = altitude_max / 1000.0 if altitude_max > 1000 else altitude_max
    alt_mask = alt_mean <= alt_max_km
    
    alt_mean = alt_mean[alt_mask]
    var_data = var_data.isel(pressure_level=alt_mask)
    
    if "geopotential_height" in ds_loc.data_vars:
        z_data = ds_loc["geopotential_height"].isel(pressure_level=alt_mask) / 1000.0
    else:
        z_data = var_data.copy(data=np.broadcast_to(alt_mean, var_data.shape))

    # 4. Time handling
    times = pd.to_datetime(ds_loc["time"].values)
    if len(times) == 0:
        raise ValueError("No time dimension found in the dataset.")
        
    t0 = times[0]
    time_hours = (times - t0).total_seconds() / 3600.0

    if selected_time is None:
        sel_idx = 0
    else:
        sel_time = pd.to_datetime(selected_time)
        sel_idx = np.argmin(np.abs(times - sel_time))
    
    selected_time_hr = time_hours[sel_idx]

    # Minimal Mode
    if style == "profile":
        fig, ax = plt.subplots(figsize=(6, 8))
        _plot_panel_b(ax, var_data, z_data, sel_idx, variable)
        fig.tight_layout()
        return fig
    elif style == "cube":
        fig = plt.figure(figsize=(10, 8))
        axA = fig.add_subplot(111, projection='3d')
        _plot_panel_a(axA, var_data, z_data, time_hours, standalone=True)
        fig.tight_layout()
        return fig

    # 5. Report Mode Layout
    fig = plt.figure(figsize=(14, 10))
    # Remove large suptitle to adhere to "no huge title consuming space"
    
    if show_cube:
        gs = gridspec.GridSpec(2, 2, height_ratios=[1.2, 1], width_ratios=[1.2, 1])
        gs.update(wspace=0.25, hspace=0.35, top=0.9, bottom=0.1, left=0.08, right=0.95)
        
        axA = fig.add_subplot(gs[0, 0], projection='3d')
        _plot_panel_a(axA, var_data, z_data, time_hours)
        
        axB = fig.add_subplot(gs[0, 1])
    else:
        gs = gridspec.GridSpec(2, 1, height_ratios=[1.2, 1])
        gs.update(wspace=0.25, hspace=0.35, top=0.9, bottom=0.1, left=0.1, right=0.9)
        
        axB = fig.add_subplot(gs[0, 0])
        
    _plot_panel_b(axB, var_data, z_data, sel_idx, variable)
    
    if show_hodograph and "u_wind" in ds_loc.data_vars and "v_wind" in ds_loc.data_vars:
        _add_inset_hodograph(axB, ds_loc, sel_idx, alt_mask)
        
    axC = fig.add_subplot(gs[1, :])
    _plot_panel_c(axC, var_data, z_data, time_hours, selected_time_hr, variable)
    
    _add_metadata_header(fig, ds_loc, latitude, longitude)
    
    return fig


def _plot_panel_a(ax, var_data, z_data, time_hours, standalone=False):
    t_len = len(time_hours)
    num_t = min(12, t_len) if not standalone else min(24, t_len)
    t_indices = np.linspace(0, t_len - 1, num_t, dtype=int)
    
    members = var_data["member"].values
    m_len = len(members)
    num_m = min(12, m_len) if not standalone else min(20, m_len)
    m_indices = np.linspace(0, m_len - 1, num_m, dtype=int)
    
    norm = Normalize(vmin=float(var_data.min()), vmax=float(var_data.max()))
    cmap = plt.get_cmap("viridis")
    
    for t_idx in t_indices:
        t_val = time_hours[t_idx]
        
        z_slice = z_data.isel(time=t_idx, member=m_indices).values
        v_slice = var_data.isel(time=t_idx, member=m_indices).values
        
        z_mean_slice = np.nanmean(z_slice, axis=0) # shape: (pressure_levels,)
        
        Y, Z = np.meshgrid(members[m_indices], z_mean_slice)
        X = np.full_like(Y, t_val)
        V = v_slice.T # shape: (len(z_mean_slice), len(m_indices))
        
        ax.plot_surface(X, Y, Z, facecolors=cmap(norm(V)), alpha=0.4, rstride=1, cstride=1, shade=False, edgecolor='none')
            
    ax.set_xlim(time_hours[0], time_hours[-1])
    ax.set_ylim(members[0], members[-1])
    ax.set_zlim(float(z_data.min()), float(z_data.max()))
    
    title_fs = 18 if standalone else 12
    label_fs = 14 if standalone else 10
    tick_fs = 12 if standalone else 9
    pad = 16 if standalone else 10

    ax.set_xlabel("Time [h]", labelpad=pad, fontsize=label_fs)
    ax.set_ylabel("Ensemble Member", labelpad=pad, fontsize=label_fs)
    ax.set_zlabel("Altitude [km]", labelpad=pad, fontsize=label_fs)
    
    title = "MAGI 3D Ensemble Cube" if standalone else "A. 3D Ensemble Cube"
    ax.set_title(title, loc="left", fontweight="bold", fontsize=title_fs)
    
    ax.tick_params(axis='both', which='major', labelsize=tick_fs, pad=pad-8)
    ax.zaxis.set_tick_params(labelsize=tick_fs, pad=pad-8)
    
    ax.view_init(elev=20, azim=-60)
    # Thin axes
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)

def _plot_panel_b(ax, var_data, z_data, sel_idx, variable):
    v_slice = var_data.isel(time=sel_idx)
    z_slice = z_data.isel(time=sel_idx)
    
    for m in range(v_slice.sizes["member"]):
        ax.plot(v_slice.isel(member=m).values, z_slice.isel(member=m).values, 
                color="gray", alpha=0.15, linewidth=1)
        
    v_p10 = v_slice.quantile(0.1, dim="member")
    v_p25 = v_slice.quantile(0.25, dim="member")
    v_p50 = v_slice.median(dim="member")
    v_p75 = v_slice.quantile(0.75, dim="member")
    v_p90 = v_slice.quantile(0.9, dim="member")
    
    z_mean = z_slice.mean(dim="member")
    
    ax.fill_betweenx(z_mean, v_p10, v_p90, color="lightblue", alpha=0.3, label="P10–P90")
    ax.fill_betweenx(z_mean, v_p25, v_p75, color="dodgerblue", alpha=0.5, label="P25–P75")
    ax.plot(v_p50, z_mean, color="darkblue", linewidth=2, label="Median")
    
    member_line = Line2D([0], [0], color="gray", alpha=0.5, linewidth=1, label="Ensemble members")
    handles, labels = ax.get_legend_handles_labels()
    handles.insert(0, member_line)
    labels.insert(0, "Ensemble members")
    
    ax.legend(handles, labels, loc="upper right", frameon=False, fontsize=9)
    
    var_name = variable.replace("_", " ").capitalize()
    if var_name.lower() == "wind speed":
        unit = " [m/s]"
    else:
        unit = ""
        
    ax.set_xlabel(f"{var_name}{unit}")
    ax.set_ylabel("Altitude [km]")
    ax.set_title("B. Vertical Ensemble Profiles", loc="left", fontweight="bold")
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)

def _plot_panel_c(ax, var_data, z_data, time_hours, selected_time_hr, variable):
    v_std = var_data.std(dim="member")
    z_mean = z_data.mean(dim=["member", "time"])
    
    X, Y = np.meshgrid(time_hours, z_mean)
    V = v_std.values.T 
    
    c = ax.pcolormesh(X, Y, V, shading="auto", cmap="magma")
    
    cbar = plt.colorbar(c, ax=ax, pad=0.02, aspect=30)
    var_name = variable.replace("_", " ").capitalize()
    cbar.set_label(f"Ensemble {var_name} Spread", fontsize=10)
    
    ax.axvline(selected_time_hr, color="white", linestyle="--", linewidth=1.5, alpha=0.8)
    ax.text(selected_time_hr, z_mean.max(), " Selected Time", color="white", 
            ha="left", va="top", fontsize=9, alpha=0.9, rotation=90)
    
    ax.set_xlabel("Forecast time [h]")
    ax.set_ylabel("Altitude [km]")
    ax.set_title("C. Time × Altitude Ensemble Evolution", loc="left", fontweight="bold")
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

def _add_inset_hodograph(ax, ds_loc, sel_idx, alt_mask):
    from mpl_toolkits.axes_grid1.inset_locator import inset_axes
    ax_ins = inset_axes(ax, width="35%", height="35%", loc="lower right", borderpad=2)
    
    u_slice = ds_loc["u_wind"].isel(pressure_level=alt_mask, time=sel_idx)
    v_slice = ds_loc["v_wind"].isel(pressure_level=alt_mask, time=sel_idx)
    z_slice = ds_loc["geopotential_height"].isel(pressure_level=alt_mask, time=sel_idx) / 1000.0 if "geopotential_height" in ds_loc.data_vars else None
    
    u_med = u_slice.median(dim="member").values
    v_med = v_slice.median(dim="member").values
    
    if z_slice is not None:
        z_med = z_slice.mean(dim="member").values
        norm = Normalize(vmin=z_med.min(), vmax=z_med.max())
        cmap = plt.get_cmap("viridis")
        
        from matplotlib.collections import LineCollection
        points = np.array([u_med, v_med]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        lc = LineCollection(segments, cmap=cmap, norm=norm, alpha=0.8, linewidth=1.5)
        lc.set_array(z_med[:-1])
        ax_ins.add_collection(lc)
    else:
        ax_ins.plot(u_med, v_med, color="darkblue", linewidth=1.5, alpha=0.8)
        
    ax_ins.plot(u_med[0], v_med[0], marker='o', color='red', markersize=4) # Surface marker
    
    limit = max(np.nanmax(np.abs(u_med)), np.nanmax(np.abs(v_med))) * 1.1
    if np.isnan(limit) or limit == 0:
        limit = 10
    ax_ins.set_xlim(-limit, limit)
    ax_ins.set_ylim(-limit, limit)
    
    ax_ins.axhline(0, color="gray", linestyle="--", linewidth=0.5)
    ax_ins.axvline(0, color="gray", linestyle="--", linewidth=0.5)
    
    ax_ins.set_xticks([])
    ax_ins.set_yticks([])
    ax_ins.set_title("Median Hodograph", fontsize=8, pad=2)

def _add_metadata_header(fig, ds_loc, lat, lon):
    members = ds_loc.sizes.get("member", "N/A")
    horizon = ds_loc.attrs.get("forecast_horizon_hours", "N/A")
    res = ds_loc.attrs.get("temporal_resolution_hours", "N/A")
    init_time = ds_loc.attrs.get("forecast_reference_time", "N/A")
    
    if lat is not None and lon is not None:
        site_str = f"{lat:.4f}°, {lon:.4f}°"
    else:
        site_str = "Selected Location"
        
    text = (f"MAGI ATMOSPHERIC ENSEMBLE OVERVIEW\n"
            f"Members: {members}  |  Forecast horizon: {horizon} h  |  Resolution: {res} h\n"
            f"Location: {site_str}  |  Init: {init_time}")
            
    fig.text(0.5, 0.98, text, ha="center", va="top", fontsize=10, 
             bbox=dict(facecolor='#f8f9fa', alpha=1.0, edgecolor='#dee2e6', boxstyle='round,pad=0.5'))

