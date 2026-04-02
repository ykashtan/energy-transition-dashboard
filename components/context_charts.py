"""
context_charts.py — Homepage context charts for the Energy Transition Dashboard.

Two charts:
  1. emissions_vs_pathways() — Global fossil CO₂ actual trajectory + IPCC C1/C3/C5 bands
  2. deployment_tracker()    — Global renewable capacity actual + IEA NZE milestones

Label conventions (per definitions.py):
  C1 = "1.5°C-compatible range (C1)"  — involves overshoot + massive CDR; NOT "below 1.5°C"
  C3 = "2°C-compatible range (C3)"
  C5 = "2.5°C-compatible range (C5)"
  Every scenario band has a tooltip explaining overshoot and CDR requirements.

Gap annotation: 2023 actual emissions (~37.4 GtCO₂) are near record-high —
  charts do NOT imply a declining trend toward pathways.
"""

import plotly.graph_objects as go
import pandas as pd

# ---------------------------------------------------------------------------
# Shared styling
# ---------------------------------------------------------------------------

CHART_FONT   = dict(family="Inter, Helvetica Neue, Arial, sans-serif", size=12)
CHART_MARGIN = dict(l=60, r=24, t=54, b=50)
PAPER_BG     = "rgba(0,0,0,0)"
PLOT_BG      = "#ffffff"
GRID_COLOR   = "#f0f0f0"

# Colors per IPCC category
SCENARIO_COLORS = {
    "C1": "#2dc653",   # green  — most aggressive mitigation
    "C3": "#f4a261",   # amber
    "C5": "#e63946",   # red
    "C7": "#6c757d",   # gray   — ~current-policy trajectory
    "C8": "#495057",   # dark gray — business-as-usual
}

# Labels for display (hover text, legend)
SCENARIO_LABELS = {
    "C1": "1.5°C-compatible range (C1)",
    "C3": "2°C-compatible range (C3)",
    "C5": "2.5°C-compatible range (C5)",
    "C7": "~3°C range (C7)",
    "C8": ">3°C (C8)",
}

# Tooltip for each category (shown on hover over the band)
SCENARIO_TOOLTIPS = {
    "C1": (
        "<b>1.5°C-compatible range (C1)</b><br>"
        "Limits warming to 1.5°C with >50% probability by 2100.<br>"
        "⚠️ Most scenarios involve temperature <i>overshoot</i> before<br>"
        "returning to 1.5°C via large-scale carbon removal (CDR).<br>"
        "Required CDR: 8–10 GtCO₂/yr by 2050.<br>"
        "Current CDR capacity: ~2 GtCO₂/yr.<br>"
        "<i>These are NOT scenarios where we stay below 1.5°C.</i>"
    ),
    "C3": (
        "<b>2°C-compatible range (C3)</b><br>"
        "Limits warming to 2°C with >67% probability by 2100.<br>"
        "Requires deep emissions cuts but less CDR than C1."
    ),
    "C5": (
        "<b>2.5°C-compatible range (C5)</b><br>"
        "Limits warming to ~2.5°C with >50% probability by 2100.<br>"
        "Current policy trajectories (~3.1°C) exceed this range."
    ),
    "C7": (
        "<b>~3°C range (C7)</b><br>"
        "Limits warming to 3°C with >67% probability by 2100.<br>"
        "Close to the trajectory under current implemented policies."
    ),
    "C8": (
        "<b>>3°C (C8)</b><br>"
        "Exceeds 3°C warming by 2100.<br>"
        "Business-as-usual high-emissions pathway."
    ),
}

# Fill opacity for scenario bands
BAND_OPACITY = 0.18


# ---------------------------------------------------------------------------
# Helper: add one scenario band (p25–p75 fill + p50 dashed line)
# ---------------------------------------------------------------------------

def _add_scenario_band(
    fig: go.Figure,
    df_cat: pd.DataFrame,
    category: str,
    show_legend: bool = True,
    legendgroup: str = "",
) -> None:
    """
    Add shaded p25–p75 band (+ lighter p10–p90 envelope if available)
    and dashed p50 median line for one IPCC category.

    Parameters
    ----------
    fig       : Plotly Figure to mutate.
    df_cat    : Rows from scenarios_df for this category (sorted by year).
    category  : 'C1', 'C3', 'C5', 'C7', or 'C8'.
    show_legend : Whether to show this trace in the legend.
    legendgroup : Group name for linked show/hide in legend.
    """
    color   = SCENARIO_COLORS.get(category, "#999999")
    label   = SCENARIO_LABELS.get(category, category)
    tooltip = SCENARIO_TOOLTIPS.get(category, "")
    grp     = legendgroup or category

    years = df_cat["year"].tolist()

    # --- Lighter outer envelope: p10 to p90 (if columns exist) ---
    if "p10" in df_cat.columns and "p90" in df_cat.columns:
        x_outer = years + years[::-1]
        y_outer = df_cat["p90"].tolist() + df_cat["p10"].tolist()[::-1]
        fig.add_trace(go.Scatter(
            x=x_outer,
            y=y_outer,
            fill="toself",
            fillcolor=f"rgba({_hex_to_rgb(color)},{BAND_OPACITY * 0.4})",
            line=dict(color="rgba(0,0,0,0)"),
            name=f"{label} (p10–p90)",
            legendgroup=grp,
            showlegend=False,
            hoverinfo="skip",
            mode="lines",
        ))

    # --- Shaded band: p25 to p75 ---
    x_band = years + years[::-1]
    y_band = df_cat["p75"].tolist() + df_cat["p25"].tolist()[::-1]

    # Include scenario count in legend label if available
    n_label = ""
    if "n_scenarios" in df_cat.columns:
        n = int(df_cat["n_scenarios"].max())
        n_label = f" [n={n}]"

    fig.add_trace(go.Scatter(
        x=x_band,
        y=y_band,
        fill="toself",
        fillcolor=f"rgba({_hex_to_rgb(color)},{BAND_OPACITY})",
        line=dict(color="rgba(0,0,0,0)"),
        name=f"{label}{n_label}",
        legendgroup=grp,
        showlegend=show_legend,
        hoverinfo="skip",
        mode="lines",
    ))

    # --- Dashed median line (p50) ---
    fig.add_trace(go.Scatter(
        x=years,
        y=df_cat["p50"].tolist(),
        name=f"{label} (median)",
        legendgroup=grp,
        showlegend=False,
        mode="lines",
        line=dict(color=color, width=1.8, dash="dash"),
        hovertemplate=(
            f"{tooltip}"
            "<br><b>Median: %{y:.1f} GtCO₂/yr</b> (%{x})"
            "<extra></extra>"
        ),
    ))


def _hex_to_rgb(hex_color: str) -> str:
    """Convert '#rrggbb' to 'r,g,b' string for rgba()."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"{r},{g},{b}"


# ---------------------------------------------------------------------------
# Chart 1: Emissions vs Pathways
# ---------------------------------------------------------------------------

def emissions_vs_pathways(
    emissions_df: pd.DataFrame,
    scenarios_df: pd.DataFrame,
) -> go.Figure:
    """
    Global fossil CO₂ actual trajectory overlaid on IPCC C1/C3/C5 scenario bands.

    Actual line: thick, dark. Covers 1990–latest year in emissions_df.
    Scenario bands: shaded p25–p75 fills + dashed p50 lines, 2020–2100.
    Annotations:
      - "Record high: ~37.4 GtCO₂ in 2023" (per GCB 2023)
      - "Current policies → ~3.1°C (UNEP 2024)"
      - CDR requirement callout

    Parameters
    ----------
    emissions_df : emissions.parquet DataFrame (all countries).
    scenarios_df : scenarios.parquet DataFrame.
    """
    fig = go.Figure()

    # ------------------------------------------------------------------
    # Compute global total fossil CO₂ by summing across all countries.
    # We use co2_fossil_mt (Mt CO₂/yr) and convert to Gt (/1000).
    # Missing countries are dropped (tend to be small emitters).
    # ------------------------------------------------------------------
    global_totals = pd.DataFrame()
    if not emissions_df.empty and "co2_fossil_mt" in emissions_df.columns:
        global_totals = (
            emissions_df
            .groupby("year", as_index=False)["co2_fossil_mt"]
            .sum()
        )
        global_totals["co2_fossil_gt"] = global_totals["co2_fossil_mt"] / 1000.0
        global_totals = global_totals.sort_values("year")

    # ------------------------------------------------------------------
    # Scenario bands (drawn first so actual line renders on top)
    # Render from least to most ambitious so wider bands are behind
    # ------------------------------------------------------------------
    if not scenarios_df.empty:
        available_cats = scenarios_df["category"].unique()
        # Draw order: background (high warming) to foreground (low warming)
        draw_order = ["C8", "C7", "C5", "C3", "C1"]
        for category in draw_order:
            if category not in available_cats:
                continue
            df_cat = (
                scenarios_df[scenarios_df["category"] == category]
                .sort_values("year")
            )
            if not df_cat.empty:
                _add_scenario_band(fig, df_cat, category, show_legend=True)

    # ------------------------------------------------------------------
    # Actual global emissions line
    # ------------------------------------------------------------------
    if not global_totals.empty:
        fig.add_trace(go.Scatter(
            x=global_totals["year"],
            y=global_totals["co2_fossil_gt"],
            name="Actual fossil CO₂ (observed)",
            mode="lines+markers",
            line=dict(color="#1a1a2e", width=3),
            marker=dict(size=4, color="#1a1a2e"),
            hovertemplate=(
                "<b>%{x}: %{y:.1f} GtCO₂/yr</b><br>"
                "Source: OWID / Global Carbon Budget<br>"
                "Fossil CO₂ only (does not include land-use change)"
                "<extra>Actual emissions</extra>"
            ),
        ))

    # ------------------------------------------------------------------
    # Annotations
    # ------------------------------------------------------------------
    # Record-high annotation at 2023
    fig.add_annotation(
        x=2023, y=38.5,
        text="⚠️ ~37.4 GtCO₂ in 2023<br><b>Near record high</b>",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=1.5,
        arrowcolor="#e63946",
        ax=40, ay=-50,
        font=dict(size=10, color="#e63946"),
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor="#e63946",
        borderpad=4,
    )

    # Current policies gap annotation
    fig.add_annotation(
        x=2100, y=30,
        text="Current policies<br>→ ~3.1°C<br>(UNEP 2024)",
        showarrow=False,
        font=dict(size=9, color="#6c757d"),
        bgcolor="rgba(248,249,250,0.9)",
        bordercolor="#dee2e6",
        borderpad=4,
        xanchor="right",
    )

    # CDR callout — note for C1 requirements
    fig.add_annotation(
        x=2050, y=-8,
        text="C1 pathways require<br>8–10 GtCO₂/yr CDR<br>by 2050<br>(current: ~2 GtCO₂/yr)",
        showarrow=True,
        arrowhead=2,
        arrowsize=0.8,
        arrowwidth=1.2,
        arrowcolor="#2dc653",
        ax=-90, ay=0,
        font=dict(size=9, color="#2dc653"),
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor="#2dc653",
        borderpad=4,
    )

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    fig.update_layout(
        title=dict(
            text=(
                "Global CO₂ Emissions vs IPCC AR6 Pathway Ranges"
                " <span style='font-size:10px; color:#6c757d'>"
                "(Source: IIASA AR6 Scenario Database v1.1)</span>"
            ),
            font=dict(size=14),
            x=0,
        ),
        xaxis=dict(
            title="Year",
            tickformat="d",
            showgrid=True,
            gridcolor=GRID_COLOR,
            range=[1990, 2105],
        ),
        yaxis=dict(
            title="GtCO₂ / yr  (net anthropogenic CO₂)",
            showgrid=True,
            gridcolor=GRID_COLOR,
            zeroline=True,
            zerolinecolor="#888888",
            zerolinewidth=1.5,
        ),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            font=dict(size=10),
            traceorder="reversed",   # show C1 first (most important)
        ),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=CHART_FONT,
        margin=dict(l=60, r=220, t=54, b=50),
        height=420,
        hovermode="x unified",
    )

    # Reference line at zero (net zero)
    fig.add_hline(
        y=0,
        line=dict(color="#888888", width=1, dash="dot"),
        annotation_text="Net zero CO₂",
        annotation_position="right",
        annotation_font_size=9,
        annotation_font_color="#888888",
    )

    return fig


# ---------------------------------------------------------------------------
# Chart 2: Renewable Deployment Tracker
# ---------------------------------------------------------------------------

def deployment_tracker(
    capacity_df: pd.DataFrame,
    nze_df: pd.DataFrame,
    energy_mix_df: pd.DataFrame = None,
) -> go.Figure:
    """
    Global renewable deployment (actual) vs IEA NZE 2050 milestones.

    Prefers installed capacity (GW) from capacity_df when available.
    Falls back to renewable electricity generation (TWh/yr) from energy_mix_df
    if capacity data is not populated (IRENA data not yet downloaded).

    Parameters
    ----------
    capacity_df   : capacity.parquet DataFrame (all countries).
    nze_df        : nze_milestones.parquet DataFrame.
    energy_mix_df : energy_mix.parquet DataFrame (fallback when no GW capacity).
    """
    fig = go.Figure()

    # ------------------------------------------------------------------
    # Determine whether to use GW capacity or TWh generation
    # ------------------------------------------------------------------
    has_capacity = (
        not capacity_df.empty
        and "capacity_gw_total_renewable" in capacity_df.columns
        and capacity_df["capacity_gw_total_renewable"].notna().any()
    )

    if has_capacity:
        # Use GW capacity data
        metric_col      = "capacity_gw_total_renewable"
        nze_metric_col  = "total_renewable_gw"
        y_label         = "GW installed capacity"
        hover_unit      = "GW"
        actual_source   = "IRENA Renewable Energy Statistics 2025"
        actual_name     = "Actual total renewable capacity"
        global_actual = (
            capacity_df
            .groupby("year", as_index=False)[metric_col]
            .sum()
            .sort_values("year")
        )
        nze_milestone_col = nze_metric_col

    else:
        # Fallback: use total renewable electricity generation (TWh/yr)
        # Computed from energy_mix by summing renewables across all countries
        actual_name   = "Actual renewable electricity generation"
        y_label       = "TWh / yr (renewable generation)"
        hover_unit    = "TWh"
        actual_source = "OWID / Ember"
        nze_milestone_col = "total_renewable_twh"

        global_actual = pd.DataFrame()
        if energy_mix_df is not None and not energy_mix_df.empty:
            # Sum all renewable electricity columns by year
            re_cols = [c for c in energy_mix_df.columns
                       if c.startswith("electricity_twh_")
                       and any(src in c for src in
                               ["solar", "wind", "hydro", "biomass", "other_renewable"])]
            if re_cols:
                tmp = energy_mix_df[["year"] + re_cols].copy()
                tmp["total_re_twh"] = tmp[re_cols].sum(axis=1)
                global_actual = (
                    tmp.groupby("year", as_index=False)["total_re_twh"]
                    .sum()
                    .rename(columns={"total_re_twh": "actual_value"})
                    .sort_values("year")
                )

    # ------------------------------------------------------------------
    # IEA NZE milestone line
    # ------------------------------------------------------------------
    if not nze_df.empty and nze_milestone_col in nze_df.columns:
        nze_sorted = nze_df.dropna(subset=[nze_milestone_col]).sort_values("year")
        fig.add_trace(go.Scatter(
            x=nze_sorted["year"],
            y=nze_sorted[nze_milestone_col],
            name=f"IEA Net Zero 2050 milestone ({y_label.split()[0]})",
            mode="lines+markers",
            line=dict(color="#f4a261", width=2, dash="dash"),
            marker=dict(
                size=9,
                color="#f4a261",
                symbol="diamond",
                line=dict(color="#ffffff", width=1.5),
            ),
            hovertemplate=(
                f"<b>%{{x}}: %{{y:,.0f}} {hover_unit}</b><br>"
                "IEA NZE 2050 milestone (total renewables)<br>"
                "<i>Source: IEA Net Zero by 2050 (approximate milestones)</i>"
                "<extra>NZE milestone</extra>"
            ),
        ))

    # ------------------------------------------------------------------
    # Actual line (exclude incomplete years where value drops >30% from prior)
    # ------------------------------------------------------------------
    if not global_actual.empty:
        actual_col = "capacity_gw_total_renewable" if has_capacity else "actual_value"
        if actual_col in global_actual.columns:
            plot_actual = global_actual.copy()
            if len(plot_actual) >= 2:
                last_v = float(plot_actual.iloc[-1][actual_col])
                prev_v = float(plot_actual.iloc[-2][actual_col])
                if prev_v > 0 and last_v < prev_v * 0.7:
                    plot_actual = plot_actual.iloc[:-1]
            fig.add_trace(go.Scatter(
                x=plot_actual["year"],
                y=plot_actual[actual_col],
                name=actual_name,
                mode="lines+markers",
                line=dict(color="#2dc653", width=3),
                marker=dict(size=4, color="#2dc653"),
                hovertemplate=(
                    f"<b>%{{x}}: %{{y:,.0f}} {hover_unit}</b><br>"
                    f"Source: {actual_source}"
                    "<extra>Actual</extra>"
                ),
            ))

            # On-track annotation
            _annotate_ontrack_generic(
                fig, global_actual, actual_col, nze_df,
                nze_milestone_col, hover_unit,
            )

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    unit_label = "GW" if has_capacity else "TWh"
    fig.update_layout(
        title=dict(
            text=f"Global Renewable Deployment ({unit_label}) vs IEA Net Zero Milestones",
            font=dict(size=14),
            x=0,
        ),
        xaxis=dict(
            title="Year",
            tickformat="d",
            showgrid=True,
            gridcolor=GRID_COLOR,
        ),
        yaxis=dict(
            title=y_label,
            showgrid=True,
            gridcolor=GRID_COLOR,
            tickformat=",d",
            rangemode="tozero",
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="left",
            x=0,
            font=dict(size=10),
        ),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=CHART_FONT,
        margin=dict(l=60, r=24, t=54, b=80),
        height=400,
        hovermode="x unified",
    )

    return fig


def _annotate_ontrack_generic(
    fig: go.Figure,
    global_actual: pd.DataFrame,
    actual_col: str,
    nze_df: pd.DataFrame,
    nze_col: str,
    unit: str,
) -> None:
    """Add on-track / off-track annotation."""
    if global_actual.empty or nze_df.empty or actual_col not in global_actual.columns:
        return

    # Filter out incomplete years: if the latest value drops >30% from prior, skip it
    ga = global_actual.copy()
    if len(ga) >= 2:
        last_val = float(ga.iloc[-1][actual_col])
        prev_val = float(ga.iloc[-2][actual_col])
        if prev_val > 0 and last_val < prev_val * 0.7:
            ga = ga.iloc[:-1]  # drop incomplete latest year

    latest = ga.iloc[-1]
    latest_year = int(latest["year"])
    latest_val  = float(latest[actual_col])

    nze_2030_rows = nze_df[nze_df["year"] == 2030]
    if nze_2030_rows.empty or nze_col not in nze_2030_rows.columns:
        return
    nze_2030 = float(nze_2030_rows.iloc[0][nze_col])

    years_to_2030 = max(2030 - latest_year, 1)
    required_annual = (nze_2030 - latest_val) / years_to_2030

    recent = global_actual[global_actual["year"] >= (latest_year - 3)]
    if len(recent) >= 2:
        current_annual = (
            recent.iloc[-1][actual_col] - recent.iloc[0][actual_col]
        ) / max(len(recent) - 1, 1)
    else:
        current_annual = 0

    on_track = current_annual >= 0.80 * required_annual
    status_text  = "✅ On track" if on_track else "❌ Off track"
    status_color = "#2dc653" if on_track else "#e63946"

    # Compute YoY growth rates (more meaningful for logistic adoption curves)
    current_yoy_pct = ""
    required_yoy_pct = ""
    if latest_val > 0 and len(recent) >= 2:
        start_val = float(recent.iloc[0][actual_col])
        n_years = max(len(recent) - 1, 1)
        if start_val > 0:
            current_cagr = ((latest_val / start_val) ** (1 / n_years) - 1) * 100
            current_yoy_pct = f" ({current_cagr:+.1f}%/yr)"
    if latest_val > 0 and nze_2030 > latest_val:
        required_cagr = ((nze_2030 / latest_val) ** (1 / years_to_2030) - 1) * 100
        required_yoy_pct = f" ({required_cagr:+.1f}%/yr)"

    # Build detail text with growth rate context
    growth_context = ""
    if current_yoy_pct and required_yoy_pct:
        # Extract numeric values for comparison
        try:
            curr_g = float(current_yoy_pct.strip(" ()%/yr+"))
            req_g = float(required_yoy_pct.strip(" ()%/yr+"))
            if req_g > 0 and curr_g > 0:
                pct_of_needed = curr_g / req_g * 100
                growth_context = f"<br><i>Growth rate: {pct_of_needed:.0f}% of what's needed</i>"
        except (ValueError, ZeroDivisionError):
            pass

    detail_text  = (
        f"Needed: +{required_annual:,.0f} {unit}/yr{required_yoy_pct}<br>"
        f"Current pace: {current_annual:+,.0f} {unit}/yr{current_yoy_pct}"
        f"{growth_context}"
    )

    fig.add_annotation(
        x=latest_year,
        y=latest_val,
        text=f"<b>{status_text}</b> for NZE 2030<br>{detail_text}",
        showarrow=True,
        arrowhead=2,
        arrowcolor=status_color,
        ax=60, ay=-60,
        font=dict(size=10, color=status_color),
        bgcolor="rgba(255,255,255,0.90)",
        bordercolor=status_color,
        borderpad=5,
        align="left",
    )


# ---------------------------------------------------------------------------
# Chart 3: Clean Energy Cost Revolution
# ---------------------------------------------------------------------------

def cost_revolution(costs_df: pd.DataFrame) -> go.Figure:
    """
    LCOE over time for solar PV, onshore wind, offshore wind, and coal (log scale).

    Log scale makes the exponential decline visually legible — linear scale
    flattens recent years (where the story is just as important).

    Parameters
    ----------
    costs_df : costs.parquet DataFrame (wide format, one row per year).
    """
    fig = go.Figure()

    if costs_df.empty:
        return _empty_chart("LCOE data not available. Run scripts/process_costs.py.")

    df = costs_df.sort_values("year")

    # ------------------------------------------------------------------
    # Trace definitions: (column, display name, color, dash style, width)
    # ------------------------------------------------------------------
    traces = [
        ("nuclear_lcoe_usd_mwh",      "Nuclear (new build)",    "#9b59b6", "dot",    2.5),
        ("coal_lcoe_usd_mwh",         "Coal (new plant)",       "#6c757d", "dot",    3),
        ("gas_ccgt_lcoe_usd_mwh",     "Gas CCGT",               "#795548", "dashdot", 2.5),
        ("offshore_wind_lcoe_usd_mwh", "Offshore wind",          "#0077b6", "solid",  2.5),
        ("onshore_wind_lcoe_usd_mwh",  "Onshore wind",           "#2dc653", "solid",  2.5),
        ("solar_lcoe_usd_mwh",         "Solar PV (utility)",     "#f4a261", "solid",  3),
    ]

    for col, name, color, dash, width in traces:
        if col not in df.columns:
            continue
        series = df[col].dropna()
        years  = df.loc[series.index, "year"]
        fig.add_trace(go.Scatter(
            x=years,
            y=series,
            name=name,
            mode="lines+markers",
            line=dict(color=color, width=width, dash=dash),
            marker=dict(size=3, color=color),
            hovertemplate=(
                f"<b>{name}</b><br>"
                "%{x}: $%{y:.0f}/MWh<br>"
                "<i>Source: IRENA / IEA</i>"
                "<extra></extra>"
            ),
        ))

    # ------------------------------------------------------------------
    # Battery storage — on primary y-axis (log scale accommodates range)
    # Note: battery is $/kWh (different unit from LCOE $/MWh)
    # ------------------------------------------------------------------
    if "battery_cost_usd_kwh" in df.columns:
        batt = df[["year", "battery_cost_usd_kwh"]].dropna(subset=["battery_cost_usd_kwh"])
        if not batt.empty:
            fig.add_trace(go.Scatter(
                x=batt["year"],
                y=batt["battery_cost_usd_kwh"],
                name="Battery storage ($/kWh)",
                mode="lines+markers",
                line=dict(color="#9b59b6", width=2, dash="dash"),
                marker=dict(size=3, color="#9b59b6"),
                hovertemplate=(
                    "<b>Battery storage</b><br>"
                    "%{x}: $%{y:.0f}/kWh<br>"
                    "<i>Source: BloombergNEF LCOS Survey</i>"
                    "<extra></extra>"
                ),
            ))

    # ------------------------------------------------------------------
    # Annotations
    # ------------------------------------------------------------------
    # Solar + wind callout — positioned in open space (middle-left of chart)
    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.42, y=0.12,
        text="Solar & onshore wind are now the<br><b>cheapest new power sources</b> in history",
        showarrow=False,
        font=dict(size=10, color="#343a40"),
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor="#dee2e6",
        borderpad=6,
        align="center",
    )

    # Solar 2023 value label — right margin callout
    if "solar_lcoe_usd_mwh" in df.columns and not df["solar_lcoe_usd_mwh"].isna().all():
        solar_2023 = df[df["year"] == 2023]["solar_lcoe_usd_mwh"]
        if not solar_2023.empty:
            fig.add_annotation(
                x=2023.3, y=solar_2023.values[0],
                text=f"<b>${solar_2023.values[0]:.0f}</b>",
                showarrow=False,
                font=dict(size=9, color="#f4a261"),
                bgcolor="rgba(255,255,255,0.85)",
            )

    # Battery 2023 value label
    if "battery_cost_usd_kwh" in df.columns:
        batt_2023 = df[df["year"] == 2023]["battery_cost_usd_kwh"]
        if not batt_2023.empty and not pd.isna(batt_2023.values[0]):
            fig.add_annotation(
                x=2023.3, y=batt_2023.values[0],
                text=f"<b>${batt_2023.values[0]:.0f}</b>",
                showarrow=False,
                font=dict(size=9, color="#9b59b6"),
                bgcolor="rgba(255,255,255,0.85)",
            )

    # ------------------------------------------------------------------
    # Layout — taller chart to give log scale more visual spread
    # ------------------------------------------------------------------
    fig.update_layout(
        title=dict(
            text=(
                "The Clean Energy Cost Revolution — LCOE 2010–2023"
                " <span style='font-size:11px; color:#6c757d'>"
                "(log scale; 2025 USD; IRENA global averages for solar/wind; "
                "IEA estimates for coal/gas)</span>"
            ),
            font=dict(size=14),
            x=0,
        ),
        xaxis=dict(
            title="Year",
            tickformat="d",
            showgrid=True,
            gridcolor=GRID_COLOR,
            tickvals=list(range(2010, 2024, 2)),
        ),
        yaxis=dict(
            title="Cost — log scale ($/MWh for LCOE; $/kWh for battery)",
            type="log",
            showgrid=True,
            gridcolor=GRID_COLOR,
            range=[1.2, 3.15],  # log10(~16) to log10(~1400)
            tickvals=[20, 30, 50, 75, 100, 150, 200, 300, 500, 800, 1200],
            ticktext=["$20", "$30", "$50", "$75", "$100", "$150", "$200", "$300", "$500", "$800", "$1,200"],
            # Prevent Plotly from adding intermediate auto-ticks on zoom/reset
            tickmode="array",
            minor=dict(showgrid=False),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(size=10),
        ),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=CHART_FONT,
        margin=dict(l=60, r=50, t=70, b=50),
        height=480,
        hovermode="x unified",
    )

    return fig


# ---------------------------------------------------------------------------
# Utility: empty figure for missing data
# ---------------------------------------------------------------------------

def _empty_chart(message: str) -> go.Figure:
    """Return a blank figure with a centered muted message."""
    fig = go.Figure()
    fig.add_annotation(
        text=f"<span style='color:#6c757d'>{message}</span>",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=13),
        align="center",
    )
    fig.update_layout(
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=300,
        margin=dict(l=10, r=10, t=10, b=10),
        font=CHART_FONT,
    )
    return fig


# ---------------------------------------------------------------------------
# Investment charts
# ---------------------------------------------------------------------------

def investment_clean_vs_fossil(investment_df: pd.DataFrame) -> go.Figure:
    """
    Global clean energy vs fossil fuel investment, stacked area with gap annotation.
    Source: IEA World Energy Investment 2025.
    """
    if investment_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Investment data not available", x=0.5, y=0.5,
                           xref="paper", yref="paper", showarrow=False)
        fig.update_layout(height=360, paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG)
        return fig

    world = investment_df[investment_df["region"] == "World"].sort_values("year").copy()
    if world.empty:
        fig = go.Figure()
        fig.add_annotation(text="No global investment data", x=0.5, y=0.5,
                           xref="paper", yref="paper", showarrow=False)
        fig.update_layout(height=360, paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG)
        return fig

    fig = go.Figure()

    # Clean energy investment
    fig.add_trace(go.Scatter(
        x=world["year"], y=world["clean_energy_investment_bn"],
        name="Clean Energy",
        fill="tozeroy",
        fillcolor="rgba(46, 164, 79, 0.3)",
        line=dict(color="#2ea44f", width=2.5),
        mode="lines+markers",
        marker=dict(size=5),
        hovertemplate="Clean Energy: $%{y:.0f}B<br>%{x}<extra></extra>",
    ))

    # Fossil fuel investment
    fig.add_trace(go.Scatter(
        x=world["year"], y=world["fossil_fuel_investment_bn"],
        name="Fossil Fuels",
        fill="tozeroy",
        fillcolor="rgba(108, 117, 125, 0.2)",
        line=dict(color="#6c757d", width=2.5),
        mode="lines+markers",
        marker=dict(size=5),
        hovertemplate="Fossil Fuels: $%{y:.0f}B<br>%{x}<extra></extra>",
    ))

    # Annotate the crossover point
    crossover = world[world["clean_energy_investment_bn"] > world["fossil_fuel_investment_bn"]]
    if not crossover.empty:
        cross_yr = crossover.iloc[0]["year"]
        cross_val = crossover.iloc[0]["clean_energy_investment_bn"]
        fig.add_annotation(
            x=cross_yr, y=cross_val,
            text=f"Clean overtakes fossil ({int(cross_yr)})",
            showarrow=True, arrowhead=2, arrowcolor="#2ea44f",
            font=dict(size=11, color="#2ea44f"),
            ax=40, ay=-40,
        )

    # Latest year annotation
    latest = world.iloc[-1]
    clean_latest = latest["clean_energy_investment_bn"]
    fossil_latest = latest["fossil_fuel_investment_bn"]
    ratio = clean_latest / fossil_latest if fossil_latest > 0 else 0

    fig.add_annotation(
        x=latest["year"], y=clean_latest,
        text=f"${clean_latest/1000:.1f}T<br>({ratio:.1f}x fossil)",
        showarrow=True, arrowhead=2, arrowcolor="#2ea44f",
        font=dict(size=11, color="#2ea44f"),
        ax=0, ay=-50,
    )

    fig.update_layout(
        title=dict(
            text="Global Energy Investment: Clean Energy vs Fossil Fuels",
            font=dict(size=15, family="Inter, Helvetica Neue, Arial, sans-serif"),
        ),
        yaxis=dict(
            title="Billion USD (2024 real)",
            gridcolor=GRID_COLOR,
            rangemode="tozero",
        ),
        xaxis=dict(
            title="",
            dtick=1,
            gridcolor=GRID_COLOR,
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        height=400,
        margin=dict(l=60, r=24, t=72, b=40),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=CHART_FONT,
        hovermode="x unified",
    )

    return fig


def investment_regional_bars(investment_df: pd.DataFrame) -> go.Figure:
    """
    Regional breakdown of clean vs fossil investment for the latest year.
    Source: IEA World Energy Investment 2025.
    """
    if investment_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Investment data not available", x=0.5, y=0.5,
                           xref="paper", yref="paper", showarrow=False)
        fig.update_layout(height=340, paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG)
        return fig

    # Exclude "World" and aggregate groups
    exclude = {"World", "Advanced Economies", "Emerging & Developing"}
    regions = investment_df[~investment_df["region"].isin(exclude)].copy()
    latest_yr = regions["year"].max()
    latest = regions[regions["year"] == latest_yr].sort_values("clean_energy_investment_bn", ascending=True)

    if latest.empty:
        fig = go.Figure()
        fig.add_annotation(text="No regional data available", x=0.5, y=0.5,
                           xref="paper", yref="paper", showarrow=False)
        fig.update_layout(height=340, paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG)
        return fig

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=latest["region"], x=latest["clean_energy_investment_bn"],
        name="Clean Energy", orientation="h",
        marker_color="#2ea44f",
        hovertemplate="%{y}: $%{x:.0f}B<extra>Clean Energy</extra>",
    ))

    fig.add_trace(go.Bar(
        y=latest["region"], x=latest["fossil_fuel_investment_bn"],
        name="Fossil Fuels", orientation="h",
        marker_color="#6c757d",
        hovertemplate="%{y}: $%{x:.0f}B<extra>Fossil Fuels</extra>",
    ))

    fig.update_layout(
        title=dict(
            text=f"Regional Energy Investment ({int(latest_yr)})",
            font=dict(size=14, family="Inter, Helvetica Neue, Arial, sans-serif"),
        ),
        barmode="group",
        xaxis=dict(title="Billion USD (2024 real)", gridcolor=GRID_COLOR),
        yaxis=dict(title=""),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        height=380,
        margin=dict(l=150, r=24, t=62, b=40),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=CHART_FONT,
    )

    return fig


def subsidies_top_countries(imf_subsidies_df: pd.DataFrame, n: int = 12) -> go.Figure:
    """
    Horizontal bar chart of top countries by fossil fuel subsidies (latest year).
    Uses IMF data (explicit + implicit, including underpriced externalities).
    Source: IMF CPAT Fossil Fuel Subsidies Database.
    """
    if imf_subsidies_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Subsidies data not available", x=0.5, y=0.5,
                           xref="paper", yref="paper", showarrow=False)
        fig.update_layout(height=380, paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG)
        return fig

    totals = imf_subsidies_df[imf_subsidies_df["subsidy_type"] == "total"]
    latest_yr = int(totals["year"].max())
    latest = totals[totals["year"] == latest_yr].nlargest(n, "subsidy_billion_usd")
    latest = latest.sort_values("subsidy_billion_usd", ascending=True)

    # Stacked bar: explicit (red) + implicit (orange)
    explicit = imf_subsidies_df[
        (imf_subsidies_df["subsidy_type"] == "explicit") &
        (imf_subsidies_df["year"] == latest_yr)
    ].set_index("iso3")["subsidy_billion_usd"]
    implicit = imf_subsidies_df[
        (imf_subsidies_df["subsidy_type"] == "implicit") &
        (imf_subsidies_df["year"] == latest_yr)
    ].set_index("iso3")["subsidy_billion_usd"]

    latest_exp = latest["iso3"].map(explicit).fillna(0)
    latest_imp = latest["iso3"].map(implicit).fillna(0)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=latest["country_name"],
        x=latest_exp.values,
        name="Explicit (price controls)",
        orientation="h",
        marker_color="#dc3545",
        hovertemplate="%{y}: $%{x:.1f}B explicit<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=latest["country_name"],
        x=latest_imp.values,
        name="Implicit (underpriced externalities)",
        orientation="h",
        marker_color="#ff9800",
        hovertemplate="%{y}: $%{x:.0f}B implicit<extra></extra>",
    ))

    fig.update_layout(
        barmode="stack",
        title=dict(
            text=f"Fossil Fuel Subsidies by Country ({latest_yr}, IMF)",
            font=dict(size=14, family="Inter, Helvetica Neue, Arial, sans-serif"),
        ),
        xaxis=dict(title="Billion USD (2025 real)", gridcolor=GRID_COLOR),
        yaxis=dict(title=""),
        height=440,
        margin=dict(l=130, r=24, t=62, b=40),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=CHART_FONT,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


def subsidies_time_series(subsidies_df: pd.DataFrame) -> go.Figure:
    """
    Global fossil fuel subsidies over time, stacked by product.
    Source: IEA Fossil Fuel Subsidies Database.
    """
    if subsidies_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Subsidies data not available", x=0.5, y=0.5,
                           xref="paper", yref="paper", showarrow=False)
        fig.update_layout(height=340, paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG)
        return fig

    world = subsidies_df[
        (subsidies_df["iso3"] == "WORLD") &
        (subsidies_df["product"] != "All Products") &
        (subsidies_df["product"] != "Total")
    ].copy()

    if world.empty:
        fig = go.Figure()
        fig.add_annotation(text="No global subsidy data", x=0.5, y=0.5,
                           xref="paper", yref="paper", showarrow=False)
        fig.update_layout(height=340, paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG)
        return fig

    colors = {"Oil": "#6c757d", "Electricity": "#e9c46a", "Natural Gas": "#457b9d", "Coal": "#264653"}
    fig = go.Figure()

    for product in ["Coal", "Natural Gas", "Electricity", "Oil"]:
        prod_data = world[world["product"] == product].sort_values("year")
        if prod_data.empty:
            continue
        fig.add_trace(go.Scatter(
            x=prod_data["year"],
            y=prod_data["subsidy_million_usd"] / 1000,  # billions
            name=product,
            stackgroup="one",
            fillcolor=colors.get(product, "#999"),
            line=dict(color=colors.get(product, "#999"), width=1),
            hovertemplate=f"{product}: $%{{y:.0f}}B<br>%{{x}}<extra></extra>",
        ))

    fig.update_layout(
        title=dict(
            text="Global Fossil Fuel Subsidies by Product",
            font=dict(size=14, family="Inter, Helvetica Neue, Arial, sans-serif"),
        ),
        yaxis=dict(title="Billion USD (2024 real)", gridcolor=GRID_COLOR, rangemode="tozero"),
        xaxis=dict(title="", gridcolor=GRID_COLOR),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        height=360,
        margin=dict(l=60, r=24, t=62, b=40),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=CHART_FONT,
        hovermode="x unified",
    )

    return fig


# ---------------------------------------------------------------------------
# Health section charts (global aggregates)
# ---------------------------------------------------------------------------

def health_global_mortality_trend(health_df: pd.DataFrame,
                                  lancet_df=None,
                                  disaster_df=None) -> go.Figure:
    """
    Climate-attributable deaths: 4 lines.

    1. Fossil fuel PM2.5 deaths (McDuffie ~33% of GBD ambient PM2.5)
    2. Climate-attributable heat deaths (Lancet Countdown, Indicator 1.1.5)
    3. Weather/climate-related disaster deaths (EM-DAT)
    4. Total (sum of above)

    Each line has different temporal coverage — the chart shows all available data.
    """
    fig = go.Figure()

    # --- Line 1: Fossil fuel PM2.5 deaths ---
    # McDuffie 2021 provides a single cross-section (~33% of GBD ambient PM2.5).
    # To show a time series, we apply the 33% fraction to GBD's annual totals.
    # This is an approximation — the true fraction may vary year-to-year.
    if "deaths_ambient_pm25" in health_df.columns:
        ap = health_df.dropna(subset=["deaths_ambient_pm25"]).groupby("year")["deaths_ambient_pm25"].sum().reset_index()
        ap = ap[ap["year"] >= 2000].sort_values("year")
        FOSSIL_FRACTION = 0.33  # McDuffie et al. 2021
        # Convert thousands → millions
        ap["fossil_m"] = ap["deaths_ambient_pm25"] * FOSSIL_FRACTION / 1000.0
        if not ap.empty:
            fig.add_trace(go.Scatter(
                x=ap["year"], y=ap["fossil_m"],
                name="Fossil fuel PM2.5 (~33% of GBD, McDuffie)",
                mode="lines+markers",
                line=dict(color="#d62728", width=2.5),
                marker=dict(size=3),
                hovertemplate="Fossil fuel PM2.5: %{y:.2f}M deaths<extra></extra>",
            ))

    # --- Line 2: Climate-attributable heat deaths (Lancet) ---
    if lancet_df is not None and not lancet_df.empty:
        ldf = lancet_df.copy()
        ldf.columns = [c.lower() for c in ldf.columns]
        if "heat_deaths_global" in ldf.columns and "year" in ldf.columns:
            af_col = "heat_deaths_attributable_fraction"
            has_af = af_col in ldf.columns
            ldf = ldf.dropna(subset=["heat_deaths_global"]).sort_values("year")
            # Apply Vicedo-Cabrera 2021 attribution: ~37% of heat deaths
            # are attributable to anthropogenic climate change.
            # (Lancet AF uses different baseline; Vicedo-Cabrera is the standard
            # counterfactual approach used by OWID and widely cited.)
            CLIMATE_FRACTION = 0.37  # Vicedo-Cabrera et al. 2021
            ldf["heat_climate_m"] = ldf["heat_deaths_global"] * CLIMATE_FRACTION / 1_000_000.0
            fig.add_trace(go.Scatter(
                x=ldf["year"], y=ldf["heat_climate_m"],
                name="Climate-attributable heat deaths (37%, Vicedo-Cabrera)",
                mode="lines+markers",
                line=dict(color="#ff9800", width=2.5),
                marker=dict(size=3),
                hovertemplate="Climate heat deaths: %{y:.2f}M<extra></extra>",
            ))

    # --- Line 3: Weather/climate-related disaster deaths (EM-DAT) ---
    if disaster_df is not None and not disaster_df.empty and "total_deaths" in disaster_df.columns:
        dd = disaster_df.groupby("year")["total_deaths"].sum().reset_index()
        dd = dd[dd["year"] >= 2000].sort_values("year")
        # Convert to millions
        dd["deaths_m"] = dd["total_deaths"] / 1_000_000.0
        if not dd.empty:
            fig.add_trace(go.Scatter(
                x=dd["year"], y=dd["deaths_m"],
                name="Weather/climate disaster deaths (EM-DAT)",
                mode="lines+markers",
                line=dict(color="#1565c0", width=2, dash="dash"),
                marker=dict(size=3),
                hovertemplate="Disaster deaths: %{y:.3f}M<extra></extra>",
            ))

    # --- Line 4: Total climate-attributable deaths ---
    # Merge all three on year, sum, plot
    all_years = set()
    series = {}
    if "deaths_ambient_pm25" in health_df.columns:
        ap = health_df.dropna(subset=["deaths_ambient_pm25"]).groupby("year")["deaths_ambient_pm25"].sum()
        series["pm25"] = ap * 0.33 / 1000.0  # McDuffie fossil fraction, thousands→millions
        all_years.update(ap.index)
    if lancet_df is not None and not lancet_df.empty:
        ldf = lancet_df.copy()
        ldf.columns = [c.lower() for c in ldf.columns]
        if "heat_deaths_global" in ldf.columns:
            heat = ldf.set_index("year")["heat_deaths_global"] * 0.37 / 1_000_000.0
            series["heat"] = heat
            all_years.update(heat.index)
    if disaster_df is not None and not disaster_df.empty:
        dd = disaster_df.groupby("year")["total_deaths"].sum() / 1_000_000.0
        series["disaster"] = dd
        all_years.update(dd.index)

    if series:
        all_years = sorted([y for y in all_years if y >= 2000])
        # Only compute total for years where at least 2 of 3 series have data
        # to avoid misleading cliff when one series ends earlier
        totals = []
        for yr in all_years:
            n_present = sum(1 for s in series.values() if yr in s.index and s.get(yr, 0) > 0)
            if n_present >= 2:
                total = sum(s.get(yr, 0) for s in series.values())
                totals.append({"year": yr, "total_k": total})
        if totals:
            tdf = pd.DataFrame(totals)
            fig.add_trace(go.Scatter(
                x=tdf["year"], y=tdf["total_k"],
                name="Total climate-attributable deaths",
                mode="lines",
                line=dict(color="#1a1a2e", width=3),
                hovertemplate="Total: %{y:.2f}M deaths<extra></extra>",
            ))

    fig.update_layout(
        title=dict(text="Climate-Attributable Deaths (global, millions/yr)",
                   font=dict(size=14, family="Inter, Helvetica Neue, Arial, sans-serif")),
        yaxis=dict(title="Million deaths/yr", gridcolor=GRID_COLOR, rangemode="tozero"),
        xaxis=dict(title="", gridcolor=GRID_COLOR),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5,
                    font=dict(size=9)),
        height=420, margin=CHART_MARGIN, paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG, font=CHART_FONT, hovermode="x unified",
    )
    return fig


def health_deaths_per_twh_bars() -> go.Figure:
    """Deaths per TWh comparison across energy sources (static reference data)."""
    sources = ["Coal", "Oil", "Natural Gas", "Biomass", "Hydro", "Wind", "Nuclear", "Solar"]
    deaths = [24.6, 18.4, 2.8, 4.6, 1.3, 0.04, 0.03, 0.02]
    colors_list = ["#495057", "#6c757d", "#adb5bd", "#8B6914", "#0077b6", "#2dc653", "#9b59b6", "#f4a261"]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=sources, y=deaths, marker_color=colors_list,
        text=[f"{d}" for d in deaths], textposition="outside",
        hovertemplate="%{x}: %{y} deaths/TWh<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="Deaths per TWh by Energy Source",
                   font=dict(size=14, family="Inter, Helvetica Neue, Arial, sans-serif")),
        yaxis=dict(title="Deaths per TWh", gridcolor=GRID_COLOR, type="log", dtick=1),
        xaxis=dict(title=""),
        height=380, margin=CHART_MARGIN, paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG, font=CHART_FONT, showlegend=False,
    )
    return fig


def health_heat_mortality_trend(lancet_df: pd.DataFrame) -> go.Figure:
    """Heat-related mortality trend from Lancet Countdown data."""
    if lancet_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Lancet Countdown heat mortality data unavailable",
                           xref="paper", yref="paper", x=0.5, y=0.5,
                           showarrow=False, font=dict(size=12, color="#6c757d"))
        fig.update_layout(height=380, paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
                          xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig

    # Normalize column names to lowercase
    df = lancet_df.copy()
    df.columns = [c.lower() for c in df.columns]

    # Find the deaths column
    if "heat_deaths_global" in df.columns:
        death_col = "heat_deaths_global"
    else:
        death_cols = [c for c in df.columns if "death" in c or "mortality" in c]
        death_col = death_cols[0] if death_cols else None

    if death_col is None or "year" not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="Heat mortality data format not recognized",
                           xref="paper", yref="paper", x=0.5, y=0.5,
                           showarrow=False, font=dict(size=12, color="#6c757d"))
        fig.update_layout(height=380, paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
                          xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig

    # Aggregate if country-level, otherwise use directly
    if "iso3" in df.columns or "iso_code" in df.columns:
        yearly = df.groupby("year")[death_col].sum().reset_index()
    else:
        yearly = df[["year", death_col]].dropna().copy()

    yearly = yearly.sort_values("year")
    yearly["deaths"] = yearly[death_col]
    # Apply Vicedo-Cabrera 2021 climate attribution: 37% of heat deaths
    CLIMATE_FRACTION = 0.37
    yearly["climate_deaths_m"] = yearly["deaths"] * CLIMATE_FRACTION / 1_000_000.0

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=yearly["year"], y=yearly["climate_deaths_m"],
        mode="lines+markers", line=dict(color="#ff9800", width=2.5),
        marker=dict(size=4), name="Climate-attributable heat deaths",
        hovertemplate="Climate heat deaths: %{y:.3f}M (%{customdata:.0f}K total × 37%)<extra></extra>",
        customdata=yearly["deaths"] / 1000,
    ))
    fig.update_layout(
        title=dict(text="Climate-Attributable Heat Deaths (37% of total, Vicedo-Cabrera 2021)",
                   font=dict(size=13, family="Inter, Helvetica Neue, Arial, sans-serif")),
        yaxis=dict(title="Million deaths/yr", gridcolor=GRID_COLOR, rangemode="tozero"),
        xaxis=dict(title="", gridcolor=GRID_COLOR),
        height=380, margin=CHART_MARGIN, paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG, font=CHART_FONT, hovermode="x unified",
    )
    return fig


# ---------------------------------------------------------------------------
# Electrification charts
# ---------------------------------------------------------------------------

# Colors for key regions in electrification charts
_ELEC_REGION_COLORS = {
    "World": "#212529",
    "China": "#e63946",
    "EU27": "#1d3557",
    "USA": "#457b9d",
    "Norway": "#2a9d8f",
    "India": "#e9c46a",
    "Germany": "#6c757d",
    "France": "#264653",
    "United Kingdom": "#f4a261",
    "Japan": "#a8dadc",
    "Korea": "#6d6875",
    "Brazil": "#06d6a0",
    "Thailand": "#118ab2",
    "Indonesia": "#073b4c",
    "Viet Nam": "#ef476f",
}

_ELEC_DASHED = {"India", "Japan", "Korea", "Brazil", "Thailand", "Indonesia", "Viet Nam"}


def ev_adoption_scurves(share_df: pd.DataFrame,
                        regions=None) -> go.Figure:
    """EV sales share S-curves by region. Default shows top regions."""
    fig = go.Figure()

    if share_df.empty:
        return _empty_chart("EV sales share data not available")

    if regions is None:
        regions = [
            "Norway", "China", "EU27", "United Kingdom", "France",
            "Germany", "World", "USA", "India", "Brazil",
        ]

    for region in regions:
        rd = share_df[share_df["region"] == region].sort_values("year")
        if rd.empty:
            continue
        color = _ELEC_REGION_COLORS.get(region, "#adb5bd")
        dash_style = "dash" if region in _ELEC_DASHED else "solid"
        width = 3 if region == "World" else 2
        fig.add_trace(go.Scatter(
            x=rd["year"], y=rd["ev_share_pct"],
            mode="lines+markers", name=region,
            line=dict(color=color, width=width, dash=dash_style),
            marker=dict(size=3 if region != "World" else 5),
            hovertemplate=f"<b>{region}</b> %{{x}}: %{{y:.1f}}%<extra></extra>",
        ))

    # 5% and 10% tipping point reference lines
    fig.add_hline(y=5, line_dash="dot", line_color="#adb5bd", line_width=1,
                  annotation_text="5% tipping point", annotation_position="top left",
                  annotation_font=dict(size=9, color="#6c757d"))
    fig.add_hline(y=10, line_dash="dot", line_color="#adb5bd", line_width=1,
                  annotation_text="10%", annotation_position="top left",
                  annotation_font=dict(size=9, color="#6c757d"))

    fig.update_layout(
        title=dict(
            text="EV Share of New Car Sales by Region (S-curve adoption)",
            font=dict(size=13, family="Inter, Helvetica Neue, Arial, sans-serif"),
        ),
        yaxis=dict(title="% of new car sales", gridcolor=GRID_COLOR, rangemode="tozero"),
        xaxis=dict(title="", gridcolor=GRID_COLOR, tickformat="d"),
        height=420, margin=CHART_MARGIN, paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG, font=CHART_FONT, hovermode="x unified",
        legend=dict(font=dict(size=10)),
    )
    return fig


def ev_sales_by_mode(sales_df: pd.DataFrame) -> go.Figure:
    """Global EV sales by vehicle mode (Cars, Trucks, Buses, Vans) — stacked area."""
    fig = go.Figure()

    if sales_df.empty:
        return _empty_chart("EV sales data not available")

    world = sales_df[sales_df["region"] == "World"].copy()
    if world.empty:
        return _empty_chart("Global EV sales data not available")

    mode_colors = {
        "Cars": "#2e7d32",
        "Trucks": "#1565c0",
        "Buses": "#ff9800",
        "Vans": "#9c27b0",
    }

    for mode in ["Cars", "Trucks", "Buses", "Vans"]:
        md = world[world["mode"] == mode].sort_values("year")
        if md.empty:
            continue
        fig.add_trace(go.Scatter(
            x=md["year"], y=md["ev_sales"] / 1e6,
            mode="lines", name=mode, stackgroup="one",
            line=dict(color=mode_colors.get(mode, "#adb5bd"), width=0.5),
            hovertemplate=f"<b>{mode}</b> %{{x}}: %{{y:.2f}}M<extra></extra>",
        ))

    fig.update_layout(
        title=dict(
            text="Global EV Sales by Vehicle Type (millions/yr)",
            font=dict(size=13, family="Inter, Helvetica Neue, Arial, sans-serif"),
        ),
        yaxis=dict(title="Million vehicles/yr", gridcolor=GRID_COLOR, rangemode="tozero"),
        xaxis=dict(title="", gridcolor=GRID_COLOR, tickformat="d"),
        height=420, margin=CHART_MARGIN, paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG, font=CHART_FONT, hovermode="x unified",
    )
    return fig


def ev_stock_growth(stock_df: pd.DataFrame) -> go.Figure:
    """Global EV stock growth chart (millions)."""
    fig = go.Figure()

    if stock_df.empty:
        return _empty_chart("EV stock data not available")

    world = stock_df[stock_df["region"] == "World"].sort_values("year")
    if world.empty:
        return _empty_chart("Global EV stock data not available")

    fig.add_trace(go.Bar(
        x=world["year"], y=world["ev_stock"] / 1e6,
        marker_color="#2e7d32", name="Global EV fleet",
        hovertemplate="<b>%{x}</b>: %{y:.1f}M EVs<extra></extra>",
    ))

    fig.update_layout(
        title=dict(
            text="Global Electric Car Fleet (millions)",
            font=dict(size=13, family="Inter, Helvetica Neue, Arial, sans-serif"),
        ),
        yaxis=dict(title="Million EVs on road", gridcolor=GRID_COLOR, rangemode="tozero"),
        xaxis=dict(title="", gridcolor=GRID_COLOR, tickformat="d"),
        height=420, margin=CHART_MARGIN, paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG, font=CHART_FONT, hovermode="x unified",
        bargap=0.15,
    )
    return fig


def electrification_sector_overview() -> go.Figure:
    """Sector comparison showing electrification progress across sectors.

    Uses hardcoded milestone data for sectors without time-series data.
    This is a progress/status chart, not a time series.
    """
    fig = go.Figure()

    # Sector data: name, electrification metric, value, color, status
    sectors = [
        ("Passenger cars", "EV share of new sales", 22.0, "#2e7d32", "Past tipping point"),
        ("Trucks", "EV share of new sales", 2.0, "#1565c0", "Early adoption"),
        ("Buses", "EV share of new sales", 5.0, "#ff9800", "At tipping point"),
        ("Heat pumps (US)", "HP outsold gas furnaces", 100, "#9c27b0", "HP > gas furnaces (2024)"),
        ("Steel (EAF)", "EAF share of production", 29, "#795548", "Growing steadily"),
        ("Aviation (SAF)", "SAF share of jet fuel", 0.3, "#e63946", "Pre-tipping (<1%)"),
        ("Shipping (alt-fuel)", "Alt-fuel share of orders", 30, "#0077b6", "LNG-dominated"),
    ]

    names = [s[0] for s in sectors]
    values = [s[2] for s in sectors]
    colors = [s[3] for s in sectors]
    metrics = [s[1] for s in sectors]
    statuses = [s[4] for s in sectors]

    fig.add_trace(go.Bar(
        y=names, x=values, orientation="h",
        marker_color=colors,
        text=[f"{v:.0f}% — {st}" if v < 100 else st for v, st in zip(values, statuses)],
        textposition="auto",
        hovertemplate=[
            f"<b>{n}</b><br>{m}: {v:.1f}%<br>Status: {s}<extra></extra>"
            for n, m, v, s in zip(names, metrics, values, statuses)
        ],
    ))

    # 5% tipping point line
    fig.add_vline(x=5, line_dash="dot", line_color="#e63946", line_width=1,
                  annotation_text="5% tipping point", annotation_position="top",
                  annotation_font=dict(size=9, color="#e63946"))

    fig.update_layout(
        title=dict(
            text="Electrification Progress Across Sectors (latest available data)",
            font=dict(size=13, family="Inter, Helvetica Neue, Arial, sans-serif"),
        ),
        xaxis=dict(title="% electrified / alt-fuel share", gridcolor=GRID_COLOR,
                   range=[0, 105]),
        yaxis=dict(gridcolor=GRID_COLOR, autorange="reversed"),
        height=380, margin=dict(l=140, r=24, t=54, b=50), paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG, font=CHART_FONT, hovermode="closest",
    )

    # Source annotation
    fig.add_annotation(
        xref="paper", yref="paper", x=1.0, y=-0.15,
        text=(
            "Sources: IEA GEVO 2025 (EVs, trucks, buses); AHRI 2024 (heat pumps); "
            "World Steel Assn (EAF); IATA (SAF); Lloyd's Register (shipping)"
        ),
        showarrow=False, font=dict(size=8, color="#6c757d"), align="right",
    )
    return fig


def electrification_milestones() -> go.Figure:
    """Timeline of key electrification milestones for harder-to-electrify sectors."""
    fig = go.Figure()

    milestones = [
        (2013, "Norway crosses 5% EV share", "EVs", "#2a9d8f"),
        (2019, "China crosses 5% EV share", "EVs", "#e63946"),
        (2020, "Pipistrel Velis Electro: first certified electric aircraft", "Aviation", "#6c757d"),
        (2020, "EU crosses 5% EV share", "EVs", "#1d3557"),
        (2021, "Global EV share crosses 5%", "EVs", "#212529"),
        (2022, "US heat pumps outsell gas furnaces for first time", "Heating", "#9c27b0"),
        (2022, "Global EV share crosses 10%", "EVs", "#212529"),
        (2023, "SAF production 0.5 Mt — doubling begins", "Aviation", "#e63946"),
        (2024, "SAF production hits 1 Mt (0.3% of jet fuel)", "Aviation", "#e63946"),
        (2024, "Global EV share reaches 22%", "EVs", "#2e7d32"),
        (2024, "93% of new steel capacity announced is EAF", "Industry", "#795548"),
        (2024, "Electric truck sales reach ~93K globally", "Trucks", "#1565c0"),
        (2025, "EU ReFuelEU Aviation: 2% SAF mandate begins", "Aviation", "#e63946"),
        (2025, "First CCS cement plant operational (Brevik, Norway)", "Industry", "#795548"),
    ]

    for i, (year, text, sector, color) in enumerate(milestones):
        fig.add_trace(go.Scatter(
            x=[year], y=[i],
            mode="markers+text",
            marker=dict(size=12, color=color, symbol="diamond"),
            text=[f"  {text}"],
            textposition="middle right",
            textfont=dict(size=10),
            name=sector,
            showlegend=False,
            hovertemplate=f"<b>{year}</b>: {text}<br>Sector: {sector}<extra></extra>",
        ))

    fig.update_layout(
        title=dict(
            text="Electrification Milestones Across Sectors",
            font=dict(size=13, family="Inter, Helvetica Neue, Arial, sans-serif"),
        ),
        xaxis=dict(title="", gridcolor=GRID_COLOR, tickformat="d",
                   range=[2012, 2027]),
        yaxis=dict(visible=False),
        height=480, margin=dict(l=24, r=280, t=54, b=50),
        paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG, font=CHART_FONT,
        hovermode="closest",
    )
    return fig
