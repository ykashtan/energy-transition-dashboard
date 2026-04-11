"""
scurve_charts.py -- Chart builders for the Technology Trajectories page.

Functions:
  1. historical_scurve_gallery  — Small-multiple adoption curves with logistic overlays
  2. five_to_fifty_chart        — Horizontal bar: years from 5% to current share
  3. trajectory_scenario_figure — 3-scenario projection bands for a selected technology
  4. expert_consensus_chart     — Range bars comparing forecaster projections

All figures use shared styling from utils.chart_styles.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from utils.chart_styles import (
    CHART_FONT, CHART_MARGIN, PAPER_BG, PLOT_BG, GRID_COLOR,
    GREEN, YELLOW, RED, BLUE, GRAY, PRIMARY,
)


# ---------------------------------------------------------------------------
# Color palette for technologies
# ---------------------------------------------------------------------------

_TECH_COLORS = {
    "ev_share_Norway":         "#1a9850",
    "ev_share_China":          "#e74c3c",
    "ev_share_World":          "#2c3e50",
    "ev_share_USA":            "#3498db",
    "ev_share_Germany":        "#f39c12",
    "ev_share_Sweden":         "#2980b9",
    "solar_share_global":      "#f1c40f",
    "wind_share_global":       "#3498db",
    "renewable_share_global":  "#27ae60",
}

_TECH_LABELS = {
    "ev_share_Norway":         "Norway EVs",
    "ev_share_China":          "China EVs",
    "ev_share_World":          "Global EVs",
    "ev_share_USA":            "USA EVs",
    "ev_share_Germany":        "Germany EVs",
    "ev_share_Sweden":         "Sweden EVs",
    "ev_share_France":         "France EVs",
    "ev_share_United_Kingdom": "UK EVs",
    "solar_share_global":      "Global Solar",
    "wind_share_global":       "Global Wind",
    "renewable_share_global":  "Global Renewables",
}


def _logistic(t, K, r, t0):
    """Logistic S-curve: S(t) = K / (1 + exp(-r * (t - t0)))"""
    return K / (1.0 + np.exp(-r * (t - t0)))


def _empty_chart(message: str, height: int = 350) -> go.Figure:
    """Return a minimal empty figure with a centered message."""
    fig = go.Figure()
    fig.add_annotation(
        text=f"<span style='color:#6c757d'>{message}</span>",
        xref="paper", yref="paper", x=0.5, y=0.5,
        showarrow=False, font=dict(size=13),
    )
    fig.update_layout(
        paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        height=height, margin=dict(l=10, r=10, t=10, b=10), font=CHART_FONT,
    )
    return fig


# ---------------------------------------------------------------------------
# 1. Historical S-Curve Gallery
# ---------------------------------------------------------------------------

def _build_single_scurve(
    years, values, params, key, title, height=320
) -> go.Figure:
    """
    Build a single adoption curve figure with data points + fitted logistic.
    """
    fig = go.Figure()
    color = _TECH_COLORS.get(key, PRIMARY)

    # Scatter: actual data points
    fig.add_trace(go.Scatter(
        x=years, y=values,
        mode="markers",
        name="Actual",
        marker=dict(color=color, size=7, line=dict(width=1, color="white")),
        hovertemplate="<b>%{x}</b>: %{y:.1f}%<extra>Actual</extra>",
    ))

    # Line: fitted logistic curve — extend forward until it crosses 80%
    if params is not None:
        K, r, t0 = params["K"], params["r"], params["t0"]
        r_sq = params.get("r_squared", 0)

        # Calculate the year the curve crosses 80% (solve logistic for y=80)
        target_pct = min(80.0, K * 0.95)  # can't exceed K; use 95% of K if K < 84
        # Inverse logistic: t = t0 - ln(K/y - 1) / r
        if K > target_pct and r > 0:
            year_at_80 = t0 - np.log(K / target_pct - 1) / r
        else:
            year_at_80 = max(years) + 30  # fallback: far future

        # Extend curve to at least the 80% crossing year (+ 3yr margin)
        t_end = max(max(years) + 5, year_at_80 + 3)
        # Cap at 2060 to avoid absurdly long projections
        t_end = min(t_end, 2060)
        t_fit = np.linspace(min(years) - 1, t_end, 300)
        y_fit = _logistic(t_fit, K, r, t0)

        # Split into historical fit (solid) and projection (dashed)
        last_data_year = max(years)
        mask_hist = t_fit <= last_data_year
        mask_proj = t_fit >= last_data_year

        fig.add_trace(go.Scatter(
            x=t_fit[mask_hist], y=y_fit[mask_hist],
            mode="lines",
            name="Logistic fit",
            line=dict(color=color, width=2.5, dash="solid"),
            opacity=0.7,
            hovertemplate="<b>%{x:.0f}</b>: %{y:.1f}%<extra>Fitted</extra>",
        ))
        fig.add_trace(go.Scatter(
            x=t_fit[mask_proj], y=y_fit[mask_proj],
            mode="lines",
            name="Projection",
            line=dict(color=color, width=2, dash="dash"),
            opacity=0.5,
            hovertemplate="<b>%{x:.0f}</b>: %{y:.1f}%<extra>Projected</extra>",
        ))

        # Annotate estimated 80% crossing
        if K >= 80 and year_at_80 <= 2058:
            # Curve reaches 80% — annotate that milestone
            fig.add_vline(
                x=year_at_80, line_dash="dot", line_color=GREEN, line_width=1,
            )
            fig.add_annotation(
                text=f"80% by ~{year_at_80:.0f}",
                x=year_at_80, y=80,
                showarrow=True,
                arrowhead=2, arrowcolor=GREEN, arrowwidth=1.5,
                ax=40, ay=-30,
                font=dict(size=10, color=GREEN, family="Inter, sans-serif"),
                bgcolor="white", bordercolor=GREEN, borderwidth=1, borderpad=3,
            )
        elif K < 80 and K >= 5:
            # Curve saturates below 80% — annotate when it reaches 80% of K
            near_sat = K * 0.80
            if r > 0:
                near_sat_year = t0 - np.log(K / near_sat - 1) / r
            else:
                near_sat_year = max(years) + 30
            if near_sat_year <= 2058:
                fig.add_vline(
                    x=near_sat_year, line_dash="dot", line_color=GREEN,
                    line_width=1,
                )
                fig.add_annotation(
                    text=f"{near_sat:.0f}% by ~{near_sat_year:.0f} (of ~{K:.0f}% est. max)",
                    x=near_sat_year, y=near_sat,
                    showarrow=True,
                    arrowhead=2, arrowcolor=GREEN, arrowwidth=1.5,
                    ax=45, ay=-30,
                    font=dict(size=9, color=GREEN, family="Inter, sans-serif"),
                    bgcolor="white", bordercolor=GREEN, borderwidth=1, borderpad=3,
                )

        # Annotate R-squared
        fig.add_annotation(
            text=f"R\u00b2 = {r_sq:.3f}",
            xref="paper", yref="paper",
            x=0.98, y=0.05,
            showarrow=False,
            font=dict(size=10, color=GRAY),
            xanchor="right",
        )

    # 5% threshold line
    fig.add_hline(
        y=5, line_dash="dot", line_color=GRAY, line_width=1,
        annotation_text="5% tipping point",
        annotation_position="bottom right",
        annotation_font=dict(size=9, color=GRAY),
    )

    # 80% dominance threshold line (only shown if curve reaches 80%)
    if params is not None and params.get("K", 0) >= 80:
        fig.add_hline(
            y=80, line_dash="dot", line_color="#e74c3c", line_width=1, opacity=0.4,
            annotation_text="80% dominance",
            annotation_position="top right",
            annotation_font=dict(size=9, color="#e74c3c"),
        )

    fig.update_layout(
        title=dict(text=title, font=dict(size=13), x=0),
        xaxis=dict(
            title=None, tickformat="d", showgrid=True, gridcolor=GRID_COLOR,
        ),
        yaxis=dict(
            title="Share (%)", showgrid=True, gridcolor=GRID_COLOR,
            rangemode="tozero",
        ),
        paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
        font=CHART_FONT,
        margin=dict(l=50, r=15, t=40, b=35),
        height=height,
        showlegend=False,
        hovermode="x unified",
    )

    return fig


def historical_scurve_gallery(ev_share_df, energy_mix_df, params):
    """
    Build a list of (key, figure) tuples for the S-curve gallery.

    Parameters
    ----------
    ev_share_df  : DataFrame from get_ev_sales_share()
    energy_mix_df: DataFrame from get_energy_mix()
    params       : dict from get_scurve_params()

    Returns
    -------
    list of (str, go.Figure) — key and figure pairs
    """
    figures = []

    if ev_share_df.empty and energy_mix_df.empty:
        return [("empty", _empty_chart("No data available. Run data processing scripts first."))]

    # --- EV share panels ---
    ev_gallery_regions = [
        ("Norway", "ev_share_Norway", "Norway: EV Sales Share"),
        ("China", "ev_share_China", "China: EV Sales Share"),
        ("World", "ev_share_World", "Global: EV Sales Share"),
        ("USA", "ev_share_USA", "USA: EV Sales Share"),
        ("Sweden", "ev_share_Sweden", "Sweden: EV Sales Share"),
        ("United Kingdom", "ev_share_United_Kingdom", "UK: EV Sales Share"),
    ]

    for region, key, title in ev_gallery_regions:
        sub = ev_share_df[ev_share_df["region"] == region].sort_values("year")
        if sub.empty:
            continue
        p = params.get(key)
        fig = _build_single_scurve(
            sub["year"].values, sub["ev_share_pct"].values, p, key, title
        )
        figures.append((key, fig))

    # --- Global solar / wind share ---
    if not energy_mix_df.empty:
        # Compute global solar and wind shares
        global_agg = energy_mix_df.groupby("year").agg({
            "electricity_twh_solar": "sum",
            "electricity_twh_wind": "sum",
            "total_electricity_twh": "sum",
        }).reset_index()

        # Drop incomplete years (2025 partial data)
        if 2025 in global_agg["year"].values and 2024 in global_agg["year"].values:
            t24 = global_agg.loc[global_agg["year"] == 2024, "total_electricity_twh"].iloc[0]
            t25 = global_agg.loc[global_agg["year"] == 2025, "total_electricity_twh"].iloc[0]
            if t25 < t24 * 0.5:
                global_agg = global_agg[global_agg["year"] <= 2024]

        global_agg["solar_share"] = (
            global_agg["electricity_twh_solar"] / global_agg["total_electricity_twh"] * 100
        )
        global_agg["wind_share"] = (
            global_agg["electricity_twh_wind"] / global_agg["total_electricity_twh"] * 100
        )

        # Solar panel (from 2000 onward)
        solar = global_agg[global_agg["year"] >= 2000].copy()
        if not solar.empty:
            fig = _build_single_scurve(
                solar["year"].values, solar["solar_share"].values,
                params.get("solar_share_global"), "solar_share_global",
                "Global: Solar Share of Electricity",
            )
            figures.append(("solar_share_global", fig))

        # Wind panel (from 2000 onward)
        wind = global_agg[global_agg["year"] >= 2000].copy()
        if not wind.empty:
            fig = _build_single_scurve(
                wind["year"].values, wind["wind_share"].values,
                params.get("wind_share_global"), "wind_share_global",
                "Global: Wind Share of Electricity",
            )
            figures.append(("wind_share_global", fig))

    return figures


# ---------------------------------------------------------------------------
# 2. Five-to-Fifty Chart
# ---------------------------------------------------------------------------

def five_to_fifty_chart(ev_share_df) -> go.Figure:
    """
    Horizontal bar chart showing how many years each country/technology took
    to go from 5% to its current share. Color by speed (fewer years = greener).
    """
    if ev_share_df.empty:
        return _empty_chart("No EV sales share data available.")

    records = []
    for region in ["Norway", "China", "Sweden", "Germany", "France",
                    "United Kingdom", "USA", "World"]:
        sub = ev_share_df[ev_share_df["region"] == region].sort_values("year")
        if sub.empty:
            continue

        # Find first year >= 5%
        above_5 = sub[sub["ev_share_pct"] >= 5.0]
        if above_5.empty:
            continue  # hasn't reached 5% yet

        year_5 = int(above_5["year"].iloc[0])
        latest = sub.iloc[-1]
        current_share = float(latest["ev_share_pct"])
        current_year = int(latest["year"])
        years_elapsed = current_year - year_5

        label = region if region != "United Kingdom" else "UK"
        records.append({
            "label": label,
            "year_5pct": year_5,
            "current_share": current_share,
            "years_elapsed": years_elapsed,
        })

    if not records:
        return _empty_chart("No countries have passed 5% EV share in the data.")

    df = pd.DataFrame(records).sort_values("years_elapsed", ascending=True)

    # Color gradient: fewer years = darker green, more years = lighter/yellow
    max_years = df["years_elapsed"].max()
    colors = []
    for y in df["years_elapsed"]:
        ratio = y / max_years if max_years > 0 else 0
        if ratio < 0.33:
            colors.append(GREEN)
        elif ratio < 0.66:
            colors.append(YELLOW)
        else:
            colors.append("#e67e22")

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=df["label"],
        x=df["years_elapsed"],
        orientation="h",
        marker=dict(color=colors, line=dict(width=1, color="white")),
        text=[
            f"{row['years_elapsed']}y ({row['year_5pct']}\u2192{row['year_5pct']+row['years_elapsed']})"
            f"  |  Now: {row['current_share']:.0f}%"
            for _, row in df.iterrows()
        ],
        textposition="outside",
        textfont=dict(size=11),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Years from 5%%: %{x}<br>"
            "<extra></extra>"
        ),
    ))

    fig.update_layout(
        title=dict(
            text="Years from 5% EV Share to Current Level",
            font=dict(size=14), x=0,
        ),
        xaxis=dict(
            title="Years since crossing 5%",
            showgrid=True, gridcolor=GRID_COLOR,
        ),
        yaxis=dict(title=None, autorange="reversed"),
        paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
        font=CHART_FONT,
        margin=dict(l=80, r=120, t=50, b=40),
        height=350,
        showlegend=False,
    )

    return fig


# ---------------------------------------------------------------------------
# 3. Trajectory Scenario Figure
# ---------------------------------------------------------------------------

# Speed multipliers for scenario bands (relative to fitted r)
_SCENARIO_DEFS = {
    "fast": {
        "label": "Fast (Norway/China-like)",
        "r_mult": 1.5,
        "color": GREEN,
    },
    "moderate": {
        "label": "Moderate (fitted trend)",
        "r_mult": 1.0,
        "color": BLUE,
    },
    "slow": {
        "label": "Slow (policy headwinds)",
        "r_mult": 0.6,
        "color": YELLOW,
    },
}


def trajectory_scenario_figure(tech_key, params, nascent_data, analogues=None):
    """
    Projection figure showing 3 scenario bands (fast/moderate/slow)
    based on the fitted logistic parameters for a given technology.

    Parameters
    ----------
    tech_key    : str — key into params dict (e.g. "ev_share_World")
    params      : dict — fitted S-curve parameters
    nascent_data: dict — nascent technology data (for techs not in params)
    analogues   : dict — optional analogue parameters for scenario shaping

    Returns
    -------
    go.Figure
    """
    p = params.get(tech_key)
    label = _TECH_LABELS.get(tech_key, tech_key)

    if p is None:
        return _empty_chart(f"No S-curve parameters available for {label}.")

    K, r, t0 = p["K"], p["r"], p["t0"]
    year_end = p.get("year_end", 2024)

    fig = go.Figure()

    # Project from year_end to 2040
    t_future = np.linspace(year_end, 2040, 200)

    # Draw bands from slowest to fastest (so fast is on top)
    for scenario_key in ["slow", "moderate", "fast"]:
        sdef = _SCENARIO_DEFS[scenario_key]
        r_adj = r * sdef["r_mult"]
        y_scenario = _logistic(t_future, K, r_adj, t0)

        fig.add_trace(go.Scatter(
            x=t_future, y=y_scenario,
            mode="lines",
            name=sdef["label"],
            line=dict(color=sdef["color"], width=2.5 if scenario_key == "moderate" else 1.8),
            opacity=0.85,
            hovertemplate=(
                f"<b>{sdef['label']}</b><br>"
                "%{x:.0f}: %{y:.1f}%<extra></extra>"
            ),
        ))

    # Fill between fast and slow for uncertainty band
    y_fast = _logistic(t_future, K, r * _SCENARIO_DEFS["fast"]["r_mult"], t0)
    y_slow = _logistic(t_future, K, r * _SCENARIO_DEFS["slow"]["r_mult"], t0)

    fig.add_trace(go.Scatter(
        x=np.concatenate([t_future, t_future[::-1]]),
        y=np.concatenate([y_fast, y_slow[::-1]]),
        fill="toself",
        fillcolor="rgba(52, 152, 219, 0.1)",
        line=dict(width=0),
        name="Scenario range",
        showlegend=False,
        hoverinfo="skip",
    ))

    # 5% threshold line
    fig.add_hline(
        y=5, line_dash="dot", line_color=GRAY, line_width=1,
        annotation_text="5% tipping point",
        annotation_position="top right",
        annotation_font=dict(size=9, color=GRAY),
    )

    # Disclaimer annotation
    fig.add_annotation(
        text=(
            "EXPLORATORY SCENARIOS ONLY \u2014 Not predictions. "
            "Based on simple logistic extrapolation."
        ),
        xref="paper", yref="paper",
        x=0.5, y=-0.12,
        showarrow=False,
        font=dict(size=9, color=RED),
        xanchor="center",
    )

    fig.update_layout(
        title=dict(
            text=f"{label}: Scenario Trajectories (2024\u20132040)",
            font=dict(size=14), x=0,
        ),
        xaxis=dict(
            title="Year", tickformat="d",
            showgrid=True, gridcolor=GRID_COLOR,
        ),
        yaxis=dict(
            title="Share (%)", showgrid=True, gridcolor=GRID_COLOR,
            rangemode="tozero",
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="left", x=0, font=dict(size=10),
        ),
        paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
        font=CHART_FONT,
        margin=dict(l=55, r=20, t=55, b=60),
        height=450,
        hovermode="x unified",
    )

    return fig


# ---------------------------------------------------------------------------
# 4. Expert Consensus Chart
# ---------------------------------------------------------------------------

# Colors for each forecaster
_FORECASTER_COLORS = {
    "IEA":          "#2c3e50",
    "RMI":          "#2980b9",
    "BloombergNEF": "#27ae60",
    "RethinkX":     "#e74c3c",
    "IRENA":        "#f39c12",
}


def expert_consensus_chart(forecasts_data, metric_key=None) -> go.Figure:
    """
    Range bars showing forecast ranges from multiple organizations for a metric.

    Parameters
    ----------
    forecasts_data : dict — from get_expert_forecasts()
    metric_key     : str — key into forecasts_data (e.g. "ev_sales_share_global")
                     If None, uses the first available key.

    Returns
    -------
    go.Figure
    """
    if not forecasts_data:
        return _empty_chart("No expert forecast data available.")

    if metric_key is None:
        metric_key = list(forecasts_data.keys())[0]

    entry = forecasts_data.get(metric_key)
    if entry is None:
        return _empty_chart(f"No forecasts found for {metric_key}.")

    metric_label = entry.get("metric", metric_key)
    forecasts = entry.get("forecasts", [])
    if not forecasts:
        return _empty_chart(f"No forecast entries for {metric_label}.")

    fig = go.Figure()

    # Sort by central value (highest at top)
    forecasts_sorted = sorted(forecasts, key=lambda f: f.get("value_central", 0))

    for i, fc in enumerate(forecasts_sorted):
        org = fc["organization"]
        color = _FORECASTER_COLORS.get(org, GRAY)
        low = fc.get("value_low", 0)
        central = fc.get("value_central", 0)
        high = fc.get("value_high", 0)
        target_yr = fc.get("target_year", "")
        report = fc.get("report", "")

        # Range bar (low to high)
        fig.add_trace(go.Scatter(
            x=[low, high],
            y=[org, org],
            mode="lines",
            line=dict(color=color, width=8),
            showlegend=False,
            hoverinfo="skip",
        ))

        # Central marker
        fig.add_trace(go.Scatter(
            x=[central],
            y=[org],
            mode="markers+text",
            marker=dict(color=color, size=14, symbol="diamond",
                        line=dict(width=2, color="white")),
            text=[f"{central}%"],
            textposition="top center",
            textfont=dict(size=10, color=color),
            showlegend=False,
            hovertemplate=(
                f"<b>{org}</b> ({report})<br>"
                f"Target: {target_yr}<br>"
                f"Range: {low}\u2013{high}%<br>"
                f"Central: {central}%"
                "<extra></extra>"
            ),
        ))

        # Low and high text
        fig.add_annotation(
            x=low, y=org,
            text=f"{low}%", showarrow=False,
            xanchor="right", xshift=-8,
            font=dict(size=9, color=GRAY),
        )
        fig.add_annotation(
            x=high, y=org,
            text=f"{high}%", showarrow=False,
            xanchor="left", xshift=8,
            font=dict(size=9, color=GRAY),
        )

    target_year = forecasts[0].get("target_year", "2030") if forecasts else "2030"

    fig.update_layout(
        title=dict(
            text=f"Expert Forecasts: {metric_label} by {target_year}",
            font=dict(size=14), x=0,
        ),
        xaxis=dict(
            title=metric_label,
            showgrid=True, gridcolor=GRID_COLOR,
        ),
        yaxis=dict(title=None),
        paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
        font=CHART_FONT,
        margin=dict(l=120, r=50, t=50, b=50),
        height=300,
    )

    return fig


# ---------------------------------------------------------------------------
# 5. Temperature Trajectory Chart
# ---------------------------------------------------------------------------

def temperature_trajectory_chart(traj_data) -> go.Figure:
    """
    Build a temperature trajectory chart showing S-curve-implied warming
    vs current policies (3.1°C) and Paris targets.
    """
    if not traj_data or "scenarios" not in traj_data:
        return _empty_chart("Temperature trajectory data not available.")

    scenarios = traj_data["scenarios"]
    fig = go.Figure()

    fast = scenarios.get("scurve_fast", {}).get("trajectory", [])
    slow = scenarios.get("scurve_slow", {}).get("trajectory", [])
    central = scenarios.get("scurve_central", {}).get("trajectory", [])

    if not central:
        return _empty_chart("No trajectory data.")

    years_c = [p["year"] for p in central]
    temps_c = [p["temp_c"] for p in central]

    # Shaded band between fast and slow scenarios
    if fast and slow:
        temps_f = [p["temp_c"] for p in fast]
        temps_s = [p["temp_c"] for p in slow]

        fig.add_trace(go.Scatter(
            x=[p["year"] for p in slow], y=temps_s,
            mode="lines", line=dict(width=0),
            showlegend=False, hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=[p["year"] for p in fast], y=temps_f,
            mode="lines", line=dict(width=0),
            fill="tonexty", fillcolor="rgba(52,152,219,0.15)",
            showlegend=False, hoverinfo="skip",
        ))

    # Central S-curve scenario
    fig.add_trace(go.Scatter(
        x=years_c, y=temps_c,
        mode="lines", name="S-curve trajectory",
        line=dict(color=BLUE, width=3),
        hovertemplate="<b>%{x}</b>: %{y:.2f}°C<extra>S-curve</extra>",
    ))

    # Current policies reference (3.1°C)
    cp_temp = scenarios.get("current_policies", {}).get("temp_2100", 3.1)
    fig.add_hline(
        y=cp_temp, line_dash="dot", line_color=RED, line_width=2,
        annotation_text=f"Current policies: {cp_temp}°C",
        annotation_position="top left",
        annotation_font=dict(size=11, color=RED),
    )

    # Paris targets
    fig.add_hline(y=1.5, line_dash="dash", line_color=GREEN, line_width=1.5,
        annotation_text="1.5°C Paris target", annotation_position="bottom left",
        annotation_font=dict(size=10, color=GREEN))
    fig.add_hline(y=2.0, line_dash="dash", line_color="#f39c12", line_width=1.5,
        annotation_text="2.0°C guardrail", annotation_position="bottom left",
        annotation_font=dict(size=10, color="#f39c12"))

    # Annotate peak
    peak = scenarios.get("scurve_central", {})
    peak_temp = peak.get("peak_temp_c", 0)
    peak_year = peak.get("peak_year", 2100)
    fig.add_annotation(
        text=f"S-curve peak: {peak_temp:.1f}°C ({peak_year})",
        x=peak_year, y=peak_temp,
        showarrow=True, arrowhead=2, arrowcolor=BLUE, arrowwidth=1.5,
        ax=-60, ay=-35,
        font=dict(size=11, color=BLUE),
        bgcolor="white", bordercolor=BLUE, borderwidth=1, borderpad=4,
    )

    fig.update_layout(
        title=dict(text="Temperature Trajectory: S-Curve Adoption vs Current Policies",
                   font=dict(size=15), x=0),
        xaxis=dict(title=None, showgrid=True, gridcolor=GRID_COLOR,
                   tickformat="d", range=[2024, 2100]),
        yaxis=dict(title="°C above pre-industrial", showgrid=True,
                   gridcolor=GRID_COLOR, range=[1.0, 3.5]),
        paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
        font=CHART_FONT, margin=dict(l=55, r=20, t=50, b=40),
        height=450, hovermode="x unified",
        legend=dict(x=0.02, y=0.98, bgcolor="rgba(255,255,255,0.8)"),
    )

    return fig
