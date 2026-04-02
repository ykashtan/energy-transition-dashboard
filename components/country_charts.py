"""
country_charts.py — Chart builders for country detail pages.

All functions accept pre-filtered DataFrames for a single country and return
go.Figure objects ready to embed in pages/country.py.

Design rules:
- Consistent color palette for energy sources (used in stacked area + donut).
- config={'responsive': True} required on all dcc.Graph wrappers.
- Empty/missing data returns a placeholder figure, never crashes.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

# Energy source colors — consistent across stacked area and donut
SOURCE_COLORS = {
    "solar":           "#f4a261",   # amber
    "wind":            "#4cc9f0",   # sky blue
    "hydro":           "#457b9d",   # steel blue
    "nuclear":         "#9b5de5",   # purple
    "gas":             "#e9c46a",   # yellow
    "coal":            "#264653",   # charcoal
    "oil":             "#6c757d",   # gray
    "biomass":         "#81b29a",   # sage green
    "other_renewable": "#90be6d",   # lime green
}

SOURCE_LABELS = {
    "solar":           "Solar",
    "wind":            "Wind",
    "hydro":           "Hydro",
    "nuclear":         "Nuclear",
    "gas":             "Natural Gas",
    "coal":            "Coal",
    "oil":             "Oil",
    "biomass":         "Biomass",
    "other_renewable": "Other Renewables",
}

# Stacking order: renewables first (bottom), fossil last (top)
SOURCE_ORDER = [
    "solar", "wind", "hydro", "biomass", "other_renewable",
    "nuclear", "gas", "oil", "coal",
]

CHART_FONT = dict(family="Inter, Helvetica Neue, Arial, sans-serif", size=12)
CHART_MARGIN = dict(l=55, r=20, t=40, b=75)

# Shared legend config for clean, readable legends across all country charts
LEGEND_DEFAULTS = dict(
    orientation="h",
    yanchor="top",
    y=-0.15,
    xanchor="center",
    x=0.5,
    font=dict(size=11),
    itemwidth=50,
    tracegroupgap=16,
    itemsizing="constant",
    traceorder="normal",
)
PAPER_BG = "rgba(0,0,0,0)"
PLOT_BG = "#ffffff"


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _empty_figure(message: str = "No data available") -> go.Figure:
    """Blank figure with a centered muted message."""
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


def placeholder_figure(message: str = "Insufficient data for this visualization") -> go.Figure:
    """Empty state figure with a styled annotation box."""
    fig = go.Figure()
    fig.add_annotation(
        text=(
            "<b style='font-size:15px'>Data Unavailable</b><br>"
            f"<span style='color:#6c757d; font-size:12px'>{message}</span>"
        ),
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        align="center",
        bgcolor="rgba(248,249,250,0.95)",
        bordercolor="#dee2e6",
        borderwidth=1,
        borderpad=18,
    )
    fig.update_layout(
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        xaxis=dict(visible=False, range=[0, 1]),
        yaxis=dict(visible=False, range=[0, 1]),
        height=300,
        margin=dict(l=10, r=10, t=10, b=10),
        font=CHART_FONT,
    )
    return fig


# ---------------------------------------------------------------------------
# Emissions tab
# ---------------------------------------------------------------------------

def emissions_time_series(df: pd.DataFrame, country_name: str) -> go.Figure:
    """
    Line chart: GHG total emissions (MtCO₂e/yr) and fossil CO₂ over time.

    Two traces:
    - Red solid line: total GHG (ghg_total_mtco2e)
    - Blue dotted line: fossil CO₂ only (co2_fossil_mt)
    """
    if df.empty or "year" not in df.columns:
        return _empty_figure("No emissions data available for this country.")

    df = df.sort_values("year")
    fig = go.Figure()

    # Total GHG
    if "ghg_total_mtco2e" in df.columns:
        mask = df["ghg_total_mtco2e"].notna()
        if mask.any():
            fig.add_trace(go.Scatter(
                x=df.loc[mask, "year"],
                y=df.loc[mask, "ghg_total_mtco2e"],
                name="Total GHG (CO₂e)",
                mode="lines+markers",
                line=dict(color="#e63946", width=2.5),
                marker=dict(size=4),
                hovertemplate="%{x}: <b>%{y:.1f} MtCO₂e</b><extra>Total GHG</extra>",
            ))

    # Fossil CO₂
    if "co2_fossil_mt" in df.columns:
        mask = df["co2_fossil_mt"].notna()
        if mask.any():
            fig.add_trace(go.Scatter(
                x=df.loc[mask, "year"],
                y=df.loc[mask, "co2_fossil_mt"],
                name="Fossil CO₂",
                mode="lines+markers",
                line=dict(color="#457b9d", width=2, dash="dot"),
                marker=dict(size=4),
                hovertemplate="%{x}: <b>%{y:.1f} MtCO₂</b><extra>Fossil CO₂</extra>",
            ))

    if not fig.data:
        return _empty_figure("No emissions data available for this country.")

    fig.update_layout(
        title=dict(text=f"GHG Emissions — {country_name}", font=dict(size=14), x=0),
        xaxis=dict(title="Year", tickformat="d", showgrid=True, gridcolor="#f0f0f0"),
        yaxis=dict(title="Mt CO₂e / yr", showgrid=True, gridcolor="#f0f0f0", rangemode="tozero"),
        legend=dict(**LEGEND_DEFAULTS),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=CHART_FONT,
        margin=CHART_MARGIN,
        height=360,
        hovermode="x unified",
    )
    return fig


# ---------------------------------------------------------------------------
# Energy Mix tab
# ---------------------------------------------------------------------------

def energy_mix_stacked_area(df: pd.DataFrame, country_name: str) -> go.Figure:
    """
    Stacked area chart: electricity generation by source (TWh/yr) over time.
    Sources rendered bottom-to-top: renewables first, nuclear, then fossil.
    """
    if df.empty or "year" not in df.columns:
        return _empty_figure("No electricity generation data available.")

    df = df.sort_values("year")

    available = [s for s in SOURCE_ORDER if f"electricity_twh_{s}" in df.columns]
    if not available:
        return _empty_figure("No electricity source breakdown available.")

    fig = go.Figure()

    for source in available:
        col = f"electricity_twh_{source}"
        y_vals = df[col].fillna(0)
        # Skip sources that are effectively zero for this country
        if y_vals.sum() < 0.1:
            continue
        fig.add_trace(go.Scatter(
            x=df["year"],
            y=y_vals,
            name=SOURCE_LABELS.get(source, source.title()),
            mode="lines",
            stackgroup="one",
            fillcolor=SOURCE_COLORS.get(source, "#adb5bd"),
            line=dict(color=SOURCE_COLORS.get(source, "#adb5bd"), width=0.5),
            hovertemplate=f"{SOURCE_LABELS.get(source, source)}: %{{y:.1f}} TWh<extra></extra>",
        ))

    if not fig.data:
        return _empty_figure("No generation data to display.")

    fig.update_layout(
        title=dict(
            text=f"Electricity Generation by Source — {country_name}",
            font=dict(size=14), x=0,
        ),
        xaxis=dict(title="Year", tickformat="d", showgrid=True, gridcolor="#f0f0f0"),
        yaxis=dict(title="TWh / yr", showgrid=True, gridcolor="#f0f0f0"),
        legend=dict(**LEGEND_DEFAULTS),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=CHART_FONT,
        margin=dict(l=55, r=20, t=70, b=80),
        height=380,
        hovermode="x unified",
    )
    return fig


def energy_mix_donut(df: pd.DataFrame, country_name: str) -> go.Figure:
    """
    Donut chart: electricity generation mix for the latest available year.
    Only sources with non-trivial generation are shown.
    """
    if df.empty or "year" not in df.columns:
        return _empty_figure("No electricity generation data available.")

    available = [s for s in SOURCE_ORDER if f"electricity_twh_{s}" in df.columns]
    if not available:
        return _empty_figure("No source breakdown available.")

    latest = df.sort_values("year").iloc[-1]
    latest_year = int(latest["year"])

    values, labels, colors = [], [], []
    for source in SOURCE_ORDER:
        col = f"electricity_twh_{source}"
        if col not in latest.index:
            continue
        val = latest.get(col, 0)
        if pd.isna(val) or val < 0.1:
            continue
        values.append(float(val))
        labels.append(SOURCE_LABELS.get(source, source.title()))
        colors.append(SOURCE_COLORS.get(source, "#adb5bd"))

    if not values:
        return _empty_figure(f"No generation data for {latest_year}.")

    fig = go.Figure(go.Pie(
        values=values,
        labels=labels,
        marker_colors=colors,
        hole=0.45,
        textposition="inside",
        textinfo="percent",
        hovertemplate="<b>%{label}</b><br>%{value:.1f} TWh (%{percent})<extra></extra>",
        sort=False,
    ))

    # Center annotation: year label
    fig.add_annotation(
        text=f"<b>{latest_year}</b><br><span style='font-size:11px'>Mix</span>",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=14, color="#212529"),
        align="center",
    )

    fig.update_layout(
        title=dict(text=f"Generation Mix ({latest_year})", font=dict(size=14), x=0),
        paper_bgcolor=PAPER_BG,
        font=CHART_FONT,
        legend=dict(orientation="v", font=dict(size=10)),
        margin=dict(l=0, r=0, t=40, b=10),
        height=340,
    )
    return fig


# ---------------------------------------------------------------------------
# Renewables tab
# ---------------------------------------------------------------------------

def renewables_trend_chart(df: pd.DataFrame, country_name: str) -> go.Figure:
    """
    Dual-axis chart:
    - Left axis: renewable share of electricity (%) — green line
    - Right axis: solar and wind generation (TWh/yr) — dotted lines

    Installed capacity data (GW) will replace this when capacity.parquet is populated.
    """
    if df.empty or "year" not in df.columns:
        return _empty_figure("No renewables data available for this country.")

    df = df.sort_values("year")
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Renewable share (left axis)
    if "renewable_share_electricity_pct" in df.columns:
        mask = df["renewable_share_electricity_pct"].notna()
        if mask.any():
            fig.add_trace(
                go.Scatter(
                    x=df.loc[mask, "year"],
                    y=df.loc[mask, "renewable_share_electricity_pct"],
                    name="Renewable share (%)",
                    mode="lines+markers",
                    line=dict(color="#2ca02c", width=2.5),
                    marker=dict(size=4),
                    hovertemplate="%{x}: <b>%{y:.1f}%</b><extra>Renewable share</extra>",
                ),
                secondary_y=False,
            )

    # Solar TWh (right axis)
    if "electricity_twh_solar" in df.columns:
        mask = df["electricity_twh_solar"].notna() & (df["electricity_twh_solar"] > 0)
        if mask.any():
            fig.add_trace(
                go.Scatter(
                    x=df.loc[mask, "year"],
                    y=df.loc[mask, "electricity_twh_solar"],
                    name="Solar (TWh)",
                    mode="lines",
                    line=dict(color=SOURCE_COLORS["solar"], width=1.8, dash="dot"),
                    hovertemplate="%{x}: <b>%{y:.1f} TWh</b><extra>Solar</extra>",
                ),
                secondary_y=True,
            )

    # Wind TWh (right axis)
    if "electricity_twh_wind" in df.columns:
        mask = df["electricity_twh_wind"].notna() & (df["electricity_twh_wind"] > 0)
        if mask.any():
            fig.add_trace(
                go.Scatter(
                    x=df.loc[mask, "year"],
                    y=df.loc[mask, "electricity_twh_wind"],
                    name="Wind (TWh)",
                    mode="lines",
                    line=dict(color=SOURCE_COLORS["wind"], width=1.8, dash="dot"),
                    hovertemplate="%{x}: <b>%{y:.1f} TWh</b><extra>Wind</extra>",
                ),
                secondary_y=True,
            )

    if not fig.data:
        return _empty_figure("No renewables data available for this country.")

    fig.update_yaxes(
        title_text="Renewable share (%)",
        secondary_y=False,
        showgrid=True,
        gridcolor="#f0f0f0",
        rangemode="tozero",
    )
    fig.update_yaxes(
        title_text="Solar + Wind (TWh/yr)",
        secondary_y=True,
        showgrid=False,
        rangemode="tozero",
    )
    fig.update_layout(
        title=dict(text=f"Renewables Trend — {country_name}", font=dict(size=14), x=0),
        xaxis=dict(title="Year", tickformat="d", showgrid=True, gridcolor="#f0f0f0"),
        legend=dict(**LEGEND_DEFAULTS),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=CHART_FONT,
        margin=CHART_MARGIN,
        height=360,
        hovermode="x unified",
    )
    return fig


# ---------------------------------------------------------------------------
# Peer Comparison tab
# ---------------------------------------------------------------------------

def peer_comparison_bars(
    iso3: str,
    country_name: str,
    continent: str,
    all_emissions: pd.DataFrame,
    all_mix: pd.DataFrame,
    country_meta: pd.DataFrame,
) -> go.Figure:
    """
    Side-by-side horizontal bar charts:
    - Left panel: Fossil CO₂ per capita (tCO₂/yr)
    - Right panel: Renewable share of electricity (%)

    Comparison group: this country, global average, regional average (same continent),
    and the top 5 global emitters by total GHG.
    The selected country's bar is highlighted in a distinct color.
    """
    if all_emissions.empty and all_mix.empty:
        return _empty_figure("No data available for peer comparison.")

    snap = _build_snapshot(all_emissions, all_mix, country_meta)
    if snap.empty:
        return _empty_figure("Insufficient data for peer comparison.")

    # --- Compute averages ---
    global_avg = snap.mean(numeric_only=True)
    regional = snap[snap.get("continent", pd.Series()) == continent] if "continent" in snap.columns else pd.DataFrame()
    regional_avg = regional.mean(numeric_only=True) if not regional.empty else global_avg

    # Top 5 emitters by total GHG, excluding the selected country
    top_emitters = pd.DataFrame()
    if "ghg_total_mtco2e" in snap.columns:
        top_emitters = (
            snap[snap["iso3"] != iso3]
            .dropna(subset=["ghg_total_mtco2e"])
            .nlargest(5, "ghg_total_mtco2e")
        )

    # --- Build comparison rows ---
    rows = []

    this_row = snap[snap["iso3"] == iso3]
    if not this_row.empty:
        r = this_row.iloc[0]
        rows.append({
            "label": f"▶ {country_name}",
            "co2_per_capita": _safe_float(r.get("co2_per_capita_t")),
            "renewable_share": _safe_float(r.get("renewable_share_electricity_pct")),
            "highlight": True,
        })

    rows.append({
        "label": "Global Average",
        "co2_per_capita": _safe_float(global_avg.get("co2_per_capita_t")),
        "renewable_share": _safe_float(global_avg.get("renewable_share_electricity_pct")),
        "highlight": False,
    })

    if not regional.empty:
        rows.append({
            "label": f"{continent} Average",
            "co2_per_capita": _safe_float(regional_avg.get("co2_per_capita_t")),
            "renewable_share": _safe_float(regional_avg.get("renewable_share_electricity_pct")),
            "highlight": False,
        })

    for _, emitter in top_emitters.iterrows():
        name = emitter.get("country_name", emitter.get("iso3", "Unknown"))
        rows.append({
            "label": str(name),
            "co2_per_capita": _safe_float(emitter.get("co2_per_capita_t")),
            "renewable_share": _safe_float(emitter.get("renewable_share_electricity_pct")),
            "highlight": False,
        })

    comp_df = pd.DataFrame(rows)

    # --- Build 2-panel figure ---
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=["Fossil CO₂ per Capita (tCO₂/yr)", "Renewable Share of Electricity (%)"],
        horizontal_spacing=0.12,
    )

    labels = comp_df["label"].tolist()

    # Left: CO₂ per capita
    co2_colors = ["#e63946" if r["highlight"] else "#457b9d" for _, r in comp_df.iterrows()]
    fig.add_trace(
        go.Bar(
            y=labels,
            x=comp_df["co2_per_capita"].tolist(),
            orientation="h",
            marker_color=co2_colors,
            hovertemplate="%{y}: <b>%{x:.1f} tCO₂/yr</b><extra></extra>",
            showlegend=False,
        ),
        row=1, col=1,
    )

    # Right: Renewable share
    ren_colors = ["#2ca02c" if r["highlight"] else "#81b29a" for _, r in comp_df.iterrows()]
    fig.add_trace(
        go.Bar(
            y=labels,
            x=comp_df["renewable_share"].tolist(),
            orientation="h",
            marker_color=ren_colors,
            hovertemplate="%{y}: <b>%{x:.1f}%</b><extra></extra>",
            showlegend=False,
        ),
        row=1, col=2,
    )

    n_rows = len(labels)
    chart_height = max(280, 60 + n_rows * 40)

    fig.update_layout(
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=CHART_FONT,
        margin=dict(l=10, r=20, t=50, b=20),
        height=chart_height,
        bargap=0.3,
    )
    fig.update_xaxes(showgrid=True, gridcolor="#f0f0f0")
    fig.update_yaxes(automargin=True)

    return fig


# ---------------------------------------------------------------------------
# Emissions with scenario overlay (Climate tab)
# ---------------------------------------------------------------------------

# Colors for IPCC categories (reused from context_charts.py pattern)
_SCENARIO_COLORS = {"C1": "#2dc653", "C3": "#f4a261", "C5": "#e63946"}
_SCENARIO_LABELS = {
    "C1": "1.5°C-compatible (C1)",
    "C3": "2°C-compatible (C3)",
    "C5": "2.5°C-compatible (C5)",
}


def emissions_time_series_with_scenarios(
    df: pd.DataFrame,
    country_name: str,
    scenarios_df: pd.DataFrame,
) -> go.Figure:
    """
    Country emissions time series with IPCC global pathway bands.

    Shows two actual emissions traces:
      - Total GHG (CO₂e) — the primary metric, scenario bands anchor here
      - Fossil CO₂ — for context

    The IIASA pathways are CO₂-only (Emissions|CO2). To anchor them to the
    total GHG line, we:
      1. Compute country share = country_GHG / global_GHG at 2020
      2. Scale CO₂ pathway × (global_GHG / global_CO₂) × country_share
    This approximates what the country's total GHG pathway would look like,
    assuming the non-CO₂ fraction declines proportionally with CO₂.
    """
    if df.empty or "year" not in df.columns:
        return _empty_figure("No emissions data available for this country.")

    df = df.sort_values("year")
    fig = go.Figure()

    # ------------------------------------------------------------------
    # Compute country share of global total GHG, and a scaling factor
    # to convert CO₂-only pathways to approximate GHG pathways.
    # ------------------------------------------------------------------
    country_share = None
    _GHG_CO2_RATIO = 1.268  # global GHG/CO₂ ratio at 2020 (50.6/39.9 Gt)

    if "ghg_total_mtco2e" in df.columns and not scenarios_df.empty:
        row_2020 = df[df["year"] == 2020]
        if not row_2020.empty and pd.notna(row_2020.iloc[0].get("ghg_total_mtco2e")):
            country_ghg_2020_mt = float(row_2020.iloc[0]["ghg_total_mtco2e"])
            global_ghg_2020_mt = 50600.0  # ~50.6 GtCO₂e (OWID/EDGAR 2020)
            if global_ghg_2020_mt > 0:
                country_share = country_ghg_2020_mt / global_ghg_2020_mt

    # ------------------------------------------------------------------
    # Scenario bands (scaled by country share, converted to MtCO₂)
    # Drawn first so actual lines render on top
    # ------------------------------------------------------------------
    if country_share is not None and not scenarios_df.empty:
        for category in ["C5", "C3", "C1"]:
            df_cat = (
                scenarios_df[scenarios_df["category"] == category]
                .sort_values("year")
            )
            if df_cat.empty:
                continue
            color = _SCENARIO_COLORS.get(category, "#999999")
            label = _SCENARIO_LABELS.get(category, category)

            years  = df_cat["year"].tolist()
            # Scale global CO₂ pathway → country approx GHG pathway:
            # GtCO₂ × 1000 → MtCO₂ × GHG/CO₂_ratio × country_GHG_share
            scale = 1000 * _GHG_CO2_RATIO * country_share
            p25_mt = (df_cat["p25"] * scale).tolist()
            p75_mt = (df_cat["p75"] * scale).tolist()
            p50_mt = (df_cat["p50"] * scale).tolist()

            # Shaded band p25–p75
            x_band = years + years[::-1]
            y_band = p75_mt + p25_mt[::-1]
            fig.add_trace(go.Scatter(
                x=x_band,
                y=y_band,
                fill="toself",
                fillcolor=f"rgba({_hex_to_rgb_cc(color)},0.15)",
                line=dict(color="rgba(0,0,0,0)"),
                name=f"{label} (proportional share, p25–p75)",
                legendgroup=category,
                showlegend=True,
                hoverinfo="skip",
                mode="lines",
            ))

            # Dashed median line
            fig.add_trace(go.Scatter(
                x=years,
                y=p50_mt,
                name=f"{label} (median)",
                legendgroup=category,
                showlegend=False,
                mode="lines",
                line=dict(color=color, width=1.5, dash="dash"),
                hovertemplate=(
                    f"<b>{label} median</b><br>"
                    "%{x}: %{y:.1f} MtCO₂e/yr<br>"
                    "<i>Approx. GHG pathway (country share × CO₂ scenario × 1.28)</i>"
                    "<extra></extra>"
                ),
            ))

    # ------------------------------------------------------------------
    # Actual country emissions traces
    # ------------------------------------------------------------------
    if "ghg_total_mtco2e" in df.columns:
        mask = df["ghg_total_mtco2e"].notna()
        if mask.any():
            fig.add_trace(go.Scatter(
                x=df.loc[mask, "year"],
                y=df.loc[mask, "ghg_total_mtco2e"],
                name="Total GHG (CO₂e)",
                mode="lines+markers",
                line=dict(color="#e63946", width=2.5),
                marker=dict(size=4),
                hovertemplate="%{x}: <b>%{y:.1f} MtCO₂e</b><extra>Total GHG</extra>",
            ))

    # Fossil CO₂ for context (dotted, secondary)
    if "co2_fossil_mt" in df.columns:
        mask = df["co2_fossil_mt"].notna()
        if mask.any():
            fig.add_trace(go.Scatter(
                x=df.loc[mask, "year"],
                y=df.loc[mask, "co2_fossil_mt"],
                name="Fossil CO₂ only",
                mode="lines+markers",
                line=dict(color="#457b9d", width=1.5, dash="dot"),
                marker=dict(size=3),
                hovertemplate="%{x}: <b>%{y:.1f} MtCO₂</b><extra>Fossil CO₂</extra>",
            ))

    if not fig.data:
        return _empty_figure("No emissions data available for this country.")

    # Scenario context note in title if scenario data was added
    scenario_note = ""
    if country_share is not None and not scenarios_df.empty:
        share_pct = country_share * 100
        scenario_note = (
            f" <span style='font-size:10px; color:#6c757d'>"
            f"Pathway bands = {share_pct:.1f}% of global GHG "
            f"(scaled from IPCC CO₂ pathways; anchored to Total GHG line)</span>"
        )

    fig.update_layout(
        title=dict(
            text=f"GHG Emissions — {country_name}{scenario_note}",
            font=dict(size=14), x=0,
        ),
        xaxis=dict(title="Year", tickformat="d", showgrid=True, gridcolor="#f0f0f0",
                   range=[1990, 2105]),
        yaxis=dict(title="Mt CO₂e / yr", showgrid=True, gridcolor="#f0f0f0",
                   zeroline=True, zerolinecolor="#cccccc", zerolinewidth=1),
        legend={**LEGEND_DEFAULTS, "font": dict(size=9), "itemwidth": 30},
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=CHART_FONT,
        margin=dict(l=55, r=20, t=40, b=80),
        height=430,
        hovermode="x unified",
    )
    return fig


def _hex_to_rgb_cc(hex_color: str) -> str:
    """Convert '#rrggbb' → 'r,g,b' string for rgba()."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"{r},{g},{b}"


def _safe_float(val):
    """Return float or None for missing/NaN values."""
    if val is None:
        return None
    try:
        f = float(val)
        return None if pd.isna(f) else f
    except (TypeError, ValueError):
        return None


def _build_snapshot(
    all_emissions: pd.DataFrame,
    all_mix: pd.DataFrame,
    country_meta: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build a latest-year per-country snapshot for peer comparison.
    Returns one row per country with: iso3, co2_per_capita_t, ghg_per_capita_t,
    ghg_total_mtco2e, renewable_share_electricity_pct, country_name, continent.
    """
    snap = None

    if not all_emissions.empty and "iso3" in all_emissions.columns and "year" in all_emissions.columns:
        metric_cols = [c for c in ["co2_per_capita_t", "ghg_per_capita_t", "ghg_total_mtco2e"]
                       if c in all_emissions.columns]
        if metric_cols:
            em_snap = (
                all_emissions[["iso3", "year"] + metric_cols]
                .dropna(subset=metric_cols, how="all")
                .sort_values("year")
                .groupby("iso3")[metric_cols]
                .last()
                .reset_index()
            )
            snap = em_snap

    if not all_mix.empty and "iso3" in all_mix.columns and "year" in all_mix.columns:
        metric_cols = [c for c in ["renewable_share_electricity_pct", "fossil_share_electricity_pct"]
                       if c in all_mix.columns]
        if metric_cols:
            mix_snap = (
                all_mix[["iso3", "year"] + metric_cols]
                .dropna(subset=metric_cols, how="all")
                .sort_values("year")
                .groupby("iso3")[metric_cols]
                .last()
                .reset_index()
            )
            if snap is None:
                snap = mix_snap
            else:
                snap = snap.merge(mix_snap, on="iso3", how="outer")

    if snap is None or snap.empty:
        return pd.DataFrame()

    if not country_meta.empty and "continent" in country_meta.columns:
        snap = snap.merge(
            country_meta[["iso3", "country_name", "continent"]],
            on="iso3",
            how="left",
        )

    return snap


# ---------------------------------------------------------------------------
# Final Energy Mix chart
# ---------------------------------------------------------------------------

def methane_trend_chart(emissions_df: pd.DataFrame, country_name: str) -> go.Figure:
    """
    Line chart: country-level methane (CH₄) and nitrous oxide (N₂O) emissions over time.

    Two traces:
    - Orange solid line: CH₄ (methane_mtco2e)
    - Blue dashed line: N₂O (nitrous_oxide_mtco2e)
    """
    if emissions_df.empty or "year" not in emissions_df.columns:
        return _empty_figure("No methane data available for this country.")

    has_ch4 = "methane_mtco2e" in emissions_df.columns
    has_n2o = "nitrous_oxide_mtco2e" in emissions_df.columns
    if not has_ch4 and not has_n2o:
        return _empty_figure("No methane or N₂O data available for this country.")

    df = emissions_df.sort_values("year")
    fig = go.Figure()

    if has_ch4:
        ch4 = df[df["methane_mtco2e"].notna()]
        if not ch4.empty:
            fig.add_trace(go.Scatter(
                x=ch4["year"], y=ch4["methane_mtco2e"],
                name="CH₄ emissions",
                mode="lines+markers",
                line=dict(color="#e76f51", width=2.5),
                marker=dict(size=3),
                hovertemplate="<b>%{x}</b>: %{y:,.1f} MtCO₂e<extra>CH₄</extra>",
            ))

    if has_n2o:
        n2o = df[df["nitrous_oxide_mtco2e"].notna()]
        if not n2o.empty:
            fig.add_trace(go.Scatter(
                x=n2o["year"], y=n2o["nitrous_oxide_mtco2e"],
                name="N₂O emissions",
                mode="lines",
                line=dict(color="#457b9d", width=2, dash="dash"),
                hovertemplate="<b>%{x}</b>: %{y:,.1f} MtCO₂e<extra>N₂O</extra>",
            ))

    fig.update_layout(
        title=dict(
            text=f"{country_name} — Methane (CH₄) and N₂O Emissions",
            font=dict(size=14), x=0,
        ),
        xaxis=dict(title="Year", showgrid=True, gridcolor="#f0f0f0", tickformat="d"),
        yaxis=dict(title="MtCO₂e / yr (GWP100)", showgrid=True, gridcolor="#f0f0f0",
                   tickformat=","),
        legend=dict(**LEGEND_DEFAULTS),
        paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
        font=CHART_FONT, margin=CHART_MARGIN,
        height=380, hovermode="x unified",
    )
    return fig


def methane_per_capita_chart(emissions_df: pd.DataFrame, country_name: str) -> go.Figure:
    """
    Line chart: per-capita methane emissions over time, with global context.
    """
    if (emissions_df.empty or "year" not in emissions_df.columns
            or "methane_per_capita_t" not in emissions_df.columns):
        return _empty_figure("No per-capita methane data for this country.")

    df = emissions_df.sort_values("year")
    ch4pc = df[df["methane_per_capita_t"].notna()]
    if ch4pc.empty:
        return _empty_figure("No per-capita methane data for this country.")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ch4pc["year"], y=ch4pc["methane_per_capita_t"],
        name=f"{country_name}",
        mode="lines+markers",
        line=dict(color="#e76f51", width=2.5),
        marker=dict(size=3),
        hovertemplate="<b>%{x}</b>: %{y:.2f} tCO₂e/person<extra>CH₄ per capita</extra>",
    ))

    fig.update_layout(
        title=dict(
            text=f"{country_name} — Methane Emissions per Capita",
            font=dict(size=14), x=0,
        ),
        xaxis=dict(title="Year", showgrid=True, gridcolor="#f0f0f0", tickformat="d"),
        yaxis=dict(title="tCO₂e / person / yr (GWP100)", showgrid=True, gridcolor="#f0f0f0"),
        legend=dict(**LEGEND_DEFAULTS),
        paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
        font=CHART_FONT, margin=CHART_MARGIN,
        height=350, hovermode="x unified",
    )
    return fig


def final_energy_shares_chart(mix_df: pd.DataFrame, country_name: str) -> go.Figure:
    """
    Line chart showing renewable vs fossil share of total final energy over time.
    This is distinct from electricity mix — it includes transport, heating, industry.
    """
    if mix_df.empty:
        return _empty_figure(f"No final energy data for {country_name}")

    df = mix_df.sort_values("year")
    fig = go.Figure()

    traces = [
        ("renewable_share_final_energy_pct", "Renewable share of final energy", "#2dc653", "solid"),
        ("fossil_share_final_energy_pct", "Fossil share of final energy", "#6c757d", "dash"),
    ]

    has_data = False
    for col, name, color, dash in traces:
        if col not in df.columns:
            continue
        series = df[col].dropna()
        if series.empty:
            continue
        has_data = True
        years = df.loc[series.index, "year"]
        fig.add_trace(go.Scatter(
            x=years, y=series, name=name,
            mode="lines+markers",
            line=dict(color=color, width=2.5, dash=dash),
            marker=dict(size=4, color=color),
            hovertemplate=f"<b>{name}</b><br>%{{x}}: %{{y:.1f}}%<extra></extra>",
        ))

    if not has_data:
        return _empty_figure(f"Final energy share data not available for {country_name}")

    # Add primary energy if available
    if "primary_energy_ej" in df.columns:
        pe_series = df["primary_energy_ej"].dropna()
        if not pe_series.empty:
            fig.add_trace(go.Scatter(
                x=df.loc[pe_series.index, "year"], y=pe_series,
                name="Total primary energy (EJ)",
                mode="lines",
                line=dict(color="#f4a261", width=1.5, dash="dot"),
                yaxis="y2",
                hovertemplate="<b>Primary energy</b><br>%{x}: %{y:.2f} EJ<extra></extra>",
            ))

    fig.update_layout(
        title=dict(text=f"{country_name} — Final Energy Shares", font=dict(size=14), x=0),
        xaxis=dict(title="Year", tickformat="d", showgrid=True, gridcolor="#f0f0f0"),
        yaxis=dict(title="% of total final energy", showgrid=True, gridcolor="#f0f0f0",
                   range=[0, 105]),
        yaxis2=dict(title="Primary energy (EJ)", overlaying="y", side="right",
                    showgrid=False, titlefont=dict(color="#f4a261"),
                    tickfont=dict(color="#f4a261")),
        legend=dict(**LEGEND_DEFAULTS),
        paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
        font=CHART_FONT, margin=CHART_MARGIN,
        height=360, hovermode="x unified",
    )
    return fig


# ---------------------------------------------------------------------------
# Health tab charts
# ---------------------------------------------------------------------------

# Deaths/TWh reference values for comparison bar chart
# Source: Markandya & Wilkinson (2007); Sovacool (2008); OWID
# Shown as orders-of-magnitude comparison only — tooltip required on every instance
_DEATHS_PER_TWH_REF = {
    "Coal":    24.6,
    "Oil":     18.4,
    "Gas":      2.8,
    "Biomass":  4.5,
    "Nuclear":  0.07,
    "Hydro":    0.02,
    "Wind":     0.04,
    "Solar":    0.02,
}

_DEATHS_PER_TWH_COLORS = {
    "Coal":    "#264653",
    "Oil":     "#6c757d",
    "Gas":     "#e9c46a",
    "Biomass": "#81b29a",
    "Nuclear": "#9b5de5",
    "Hydro":   "#457b9d",
    "Wind":    "#4cc9f0",
    "Solar":   "#f4a261",
}


def health_mortality_chart(health_df: pd.DataFrame, country_name: str) -> go.Figure:
    """
    Time-series chart: ambient PM2.5 deaths (all sources).

    Household air pollution removed — it is a poverty/clean-cooking issue,
    not a fossil fuel combustion issue.
    """
    if health_df.empty or "year" not in health_df.columns:
        return _empty_figure(f"No health data available for {country_name}.")

    df = health_df.sort_values("year")
    has_ambient = "deaths_ambient_pm25" in df.columns and df["deaths_ambient_pm25"].notna().any()

    if not has_ambient:
        return placeholder_figure(
            "Ambient PM2.5 mortality data — "
            "download GBD/IHME data to populate (see scripts/process_health.py)"
        )

    fig = go.Figure()

    # Ambient PM2.5 (all sources)
    mask = df["deaths_ambient_pm25"].notna()
    vals = df.loc[mask, "deaths_ambient_pm25"]
    fig.add_trace(go.Scatter(
        x=df.loc[mask, "year"],
        y=vals,
        name="Ambient PM2.5 deaths (all sources)",
        mode="lines+markers",
        line=dict(color="#d62728", width=2.5),
        marker=dict(size=5),
        hovertemplate=(
            "%{x}: <b>%{y:.1f}K deaths/yr</b><br>"
            "<i>All outdoor PM2.5 sources (fossil fuels ~33%, plus dust, fires, agriculture)</i>"
            "<extra></extra>"
        ),
    ))

    # Fossil fuel subset annotation if available
    if "fossil_fuel_deaths" in df.columns:
        latest_ff = df.dropna(subset=["fossil_fuel_deaths"]).sort_values("year")
        if not latest_ff.empty:
            ff_val = latest_ff.iloc[-1]["fossil_fuel_deaths"]
            fig.add_annotation(
                xref="paper", yref="paper", x=0.02, y=0.98,
                text=f"Fossil fuel subset: ~{ff_val:.1f}K/yr (McDuffie 2021, ~33% of total)",
                showarrow=False, font=dict(size=9, color="#6c757d"),
                bgcolor="rgba(255,255,255,0.85)", borderpad=4, align="left",
            )

    fig.update_layout(
        title=dict(
            text=f"Outdoor PM2.5 Mortality (All Sources) — {country_name}",
            font=dict(size=14),
            x=0,
            pad=dict(l=0),
        ),
        xaxis=dict(title="Year", showgrid=False),
        yaxis=dict(
            title="Deaths per year (thousands)",
            showgrid=True,
            gridcolor="#f0f0f0",
        ),
        legend=dict(**LEGEND_DEFAULTS),
        hovermode="x unified",
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=CHART_FONT,
        margin=CHART_MARGIN,
        height=340,
    )
    return fig


def health_access_chart(health_df: pd.DataFrame, country_name: str) -> go.Figure:
    """
    Dual time-series: electricity access (%) and clean cooking access (%) over time.

    Both use percentage with access (% of population).
    Energy access gap is a key EJ indicator — lags behind electricity in most low-income countries.
    """
    if health_df.empty or "year" not in health_df.columns:
        return _empty_figure(f"No energy access data for {country_name}.")

    df = health_df.sort_values("year")
    has_elec = "pct_electricity_access" in df.columns and df["pct_electricity_access"].notna().any()
    has_cook = "pct_clean_cooking" in df.columns and df["pct_clean_cooking"].notna().any()

    if not has_elec and not has_cook:
        return placeholder_figure(
            "Electricity and clean cooking access data — "
            "World Bank WDI data should populate automatically (re-run process_health.py)"
        )

    fig = go.Figure()

    if has_elec:
        mask = df["pct_electricity_access"].notna()
        fig.add_trace(go.Scatter(
            x=df.loc[mask, "year"],
            y=df.loc[mask, "pct_electricity_access"],
            name="Electricity access (% of population)",
            mode="lines+markers",
            line=dict(color="#2ca02c", width=2.5),
            marker=dict(size=5),
            hovertemplate="%{x}: <b>%{y:.1f}%</b> with electricity access<extra></extra>",
        ))

    # Clean cooking access removed — it's a poverty/clean-cooking issue,
    # not directly relevant to the fossil fuel energy transition.

    # WHO guideline reference line at 100% (universal access target)
    fig.add_hline(
        y=100,
        line_dash="dash",
        line_color="#cccccc",
        annotation_text="SDG7 target: 100%",
        annotation_position="bottom right",
        annotation_font_size=10,
    )

    fig.update_layout(
        title=dict(
            text=f"Energy Access — {country_name}",
            font=dict(size=14),
            x=0,
        ),
        xaxis=dict(title="Year", showgrid=False),
        yaxis=dict(
            title="% of population with access",
            range=[0, 105],
            showgrid=True,
            gridcolor="#f0f0f0",
        ),
        legend=dict(**LEGEND_DEFAULTS),
        hovermode="x unified",
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=CHART_FONT,
        margin=CHART_MARGIN,
        height=320,
    )
    return fig


def health_pm25_trend(health_df: pd.DataFrame, country_name: str) -> go.Figure:
    """
    Time series of mean annual PM2.5 exposure (μg/m³) with WHO guideline annotation.
    """
    if health_df.empty or "year" not in health_df.columns:
        return _empty_figure(f"No PM2.5 data for {country_name}.")

    df = health_df.sort_values("year")
    col = "pm25_annual_mean_ugm3"

    if col not in df.columns or df[col].notna().sum() < 2:
        return placeholder_figure(
            "PM2.5 annual mean exposure data — World Bank WDI (re-run process_health.py)"
        )

    mask = df[col].notna()
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df.loc[mask, "year"],
        y=df.loc[mask, col],
        name="Annual mean PM2.5",
        mode="lines+markers",
        line=dict(color="#8c564b", width=2.5),
        marker=dict(size=5),
        fill="tozeroy",
        fillcolor="rgba(140,86,75,0.12)",
        hovertemplate="%{x}: <b>%{y:.1f} μg/m³</b><extra></extra>",
    ))

    # WHO 2021 annual guideline: 5 μg/m³
    fig.add_hline(
        y=5,
        line_dash="dash",
        line_color="#e74c3c",
        annotation_text="WHO 2021 guideline: 5 μg/m³",
        annotation_position="bottom right",
        annotation_font_size=10,
        annotation_font_color="#e74c3c",
    )

    fig.update_layout(
        title=dict(
            text=f"Annual Mean PM2.5 Exposure — {country_name}",
            font=dict(size=14),
            x=0,
        ),
        xaxis=dict(title="Year", showgrid=False),
        yaxis=dict(
            title="PM2.5 (μg/m³)",
            showgrid=True,
            gridcolor="#f0f0f0",
            rangemode="tozero",
        ),
        hovermode="x unified",
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=CHART_FONT,
        margin=CHART_MARGIN,
        height=290,
    )
    return fig


def deaths_per_twh_comparison(health_df: pd.DataFrame, country_name: str,
                               energy_mix_df: pd.DataFrame) -> go.Figure:
    """
    Horizontal bar chart comparing deaths/TWh by energy source (OWID reference values),
    with a marker for this country's estimated energy-mix deaths/TWh.

    CRITICAL DISPLAY REQUIREMENTS (from definitions.py):
    - Present as "orders of magnitude" comparison — not precision mortality rates
    - Every instance requires a caveat tooltip linking to OWID methodology
    - Coal is ~1000× more deaths per TWh than wind/solar
    - Log scale required (values span 3+ orders of magnitude)
    - Full methodology caveat must appear alongside this chart
    """
    # Build the reference bars (always shown)
    sources = list(_DEATHS_PER_TWH_REF.keys())
    values = [_DEATHS_PER_TWH_REF[s] for s in sources]
    colors = [_DEATHS_PER_TWH_COLORS[s] for s in sources]

    # Sort by deaths (ascending) for readability
    sorted_pairs = sorted(zip(values, sources, colors))
    values_s, sources_s, colors_s = zip(*sorted_pairs)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=list(values_s),
        y=list(sources_s),
        orientation="h",
        marker_color=list(colors_s),
        hovertemplate=(
            "<b>%{y}</b>: %{x:.2f} deaths/TWh<br>"
            "<i>OWID reference value — order of magnitude only</i>"
            "<extra></extra>"
        ),
        name="Reference deaths/TWh (OWID)",
    ))

    # Add country energy-mix estimate if available
    country_dptwh = None
    if not health_df.empty and "deaths_per_twh_energy_mix" in health_df.columns:
        series = health_df["deaths_per_twh_energy_mix"].dropna()
        if not series.empty:
            country_dptwh = float(series.iloc[-1])

    if country_dptwh is not None and country_dptwh > 0:
        fig.add_vline(
            x=country_dptwh,
            line_dash="dash",
            line_color="#17becf",
            line_width=2,
            annotation_text=f"{country_name} mix: {country_dptwh:.2f}",
            annotation_position="top",
            annotation_font_size=10,
            annotation_font_color="#17becf",
        )

    fig.update_layout(
        title=dict(
            text="Deaths per TWh by Energy Source",
            font=dict(size=14),
            x=0,
        ),
        xaxis=dict(
            title="Deaths per TWh (log scale)",
            type="log",
            showgrid=True,
            gridcolor="#f0f0f0",
        ),
        yaxis=dict(title=""),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=CHART_FONT,
        margin=dict(l=80, r=20, t=40, b=45),
        height=320,
        showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# Climate-attributable heatwave days (Lancet Countdown 2025)
# ---------------------------------------------------------------------------

def heatwave_days_chart(health_df: pd.DataFrame, country_name: str) -> go.Figure:
    """
    Bar chart: heatwave days attributable to climate change per year.

    Source: Lancet Countdown 2025 — Indicator 1.1.1
    Shows how many additional heatwave days are caused by climate change
    compared to a no-climate-change counterfactual.
    """
    if health_df.empty or "year" not in health_df.columns:
        return _empty_figure(f"No heatwave data for {country_name}.")

    col = "heatwave_days_cc"
    if col not in health_df.columns or health_df[col].notna().sum() == 0:
        return placeholder_figure(
            "Heatwave data not available for this country. "
            "Source: Lancet Countdown 2025 (Indicator 1.1.1)."
        )

    df = health_df[health_df[col].notna()].sort_values("year")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["year"],
        y=df[col],
        marker_color="#e63946",
        hovertemplate=(
            "%{x}: <b>%{y:.1f} additional exposure days</b><br>"
            "<i>Heatwave exposure days attributable to climate change</i><br>"
            "<i>(exposure metric, not deaths — see note below)</i>"
            "<extra></extra>"
        ),
        name="Climate-attributable heatwave exposure days",
    ))

    fig.update_layout(
        title=dict(
            text=f"Heatwave Exposure Days Attributable to Climate Change — {country_name}",
            font=dict(size=14),
            x=0,
        ),
        xaxis=dict(title="Year", tickformat="d", showgrid=False),
        yaxis=dict(
            title="Additional heatwave exposure days",
            showgrid=True,
            gridcolor="#f0f0f0",
            rangemode="tozero",
        ),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=CHART_FONT,
        margin=CHART_MARGIN,
        height=300,
        showlegend=False,
    )

    # Add source annotation
    fig.add_annotation(
        text="Source: Lancet Countdown 2025 (Indicator 1.1.1)",
        xref="paper", yref="paper",
        x=1, y=-0.12,
        showarrow=False,
        font=dict(size=9, color="#999"),
        xanchor="right",
    )

    return fig


# ---------------------------------------------------------------------------
# Investment & subsidy charts (country-level)
# ---------------------------------------------------------------------------

def country_subsidies_chart(subsidies_df: pd.DataFrame, country_name: str) -> go.Figure:
    """
    Stacked area chart of fossil fuel subsidies by product for a single country.
    Source: IEA Fossil Fuel Subsidies Database.
    """
    if subsidies_df.empty:
        return _empty_figure(f"No fossil fuel subsidy data for {country_name}")

    # Exclude Total and All Products rows
    product_data = subsidies_df[
        ~subsidies_df["product"].isin(["Total", "All Products"])
    ].copy()
    if product_data.empty:
        return _empty_figure(f"No fossil fuel subsidy data for {country_name}")

    colors = {"Oil": "#6c757d", "Electricity": "#e9c46a", "Natural Gas": "#457b9d",
              "Gas": "#457b9d", "Coal": "#264653"}

    fig = go.Figure()
    for product in ["Coal", "Gas", "Natural Gas", "Electricity", "Oil"]:
        pdata = product_data[product_data["product"] == product].sort_values("year")
        if pdata.empty:
            continue
        fig.add_trace(go.Scatter(
            x=pdata["year"],
            y=pdata["subsidy_million_usd"] / 1000,
            name=product,
            stackgroup="one",
            fillcolor=colors.get(product, "#999"),
            line=dict(color=colors.get(product, "#999"), width=1),
            hovertemplate=f"{product}: $%{{y:.1f}}B<br>%{{x}}<extra></extra>",
        ))

    fig.update_layout(
        title=dict(
            text=f"{country_name}: Fossil Fuel Subsidies by Product",
            font=dict(size=14, family="Inter, Helvetica Neue, Arial, sans-serif"),
        ),
        yaxis=dict(title="Billion USD (2024 real)", gridcolor="#f0f0f0", rangemode="tozero"),
        xaxis=dict(title="", gridcolor="#f0f0f0"),
        legend=dict(**LEGEND_DEFAULTS),
        height=360,
        margin=dict(l=55, r=20, t=60, b=75),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=CHART_FONT,
        hovermode="x unified",
    )

    return fig


def regional_investment_chart(investment_df: pd.DataFrame, region_name: str) -> go.Figure:
    """
    Clean vs fossil investment trend for a region.
    Source: IEA World Energy Investment 2025.
    """
    if investment_df.empty:
        return _empty_figure(f"No investment data for {region_name}")

    region = investment_df[investment_df["region"] == region_name].sort_values("year")
    if region.empty:
        return _empty_figure(f"No investment data for {region_name}")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=region["year"], y=region["clean_energy_investment_bn"],
        name="Clean Energy",
        fill="tozeroy",
        fillcolor="rgba(46, 164, 79, 0.3)",
        line=dict(color="#2ea44f", width=2),
        mode="lines+markers",
        marker=dict(size=4),
        hovertemplate="Clean: $%{y:.0f}B<br>%{x}<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=region["year"], y=region["fossil_fuel_investment_bn"],
        name="Fossil Fuels",
        fill="tozeroy",
        fillcolor="rgba(108, 117, 125, 0.15)",
        line=dict(color="#6c757d", width=2),
        mode="lines+markers",
        marker=dict(size=4),
        hovertemplate="Fossil: $%{y:.0f}B<br>%{x}<extra></extra>",
    ))

    fig.update_layout(
        title=dict(
            text=f"{region_name}: Clean vs Fossil Fuel Investment",
            font=dict(size=14, family="Inter, Helvetica Neue, Arial, sans-serif"),
        ),
        yaxis=dict(title="Billion USD (2024 real)", gridcolor="#f0f0f0", rangemode="tozero"),
        xaxis=dict(title="", dtick=1, gridcolor="#f0f0f0"),
        legend=dict(**LEGEND_DEFAULTS),
        height=360,
        margin=dict(l=55, r=20, t=60, b=75),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=CHART_FONT,
        hovermode="x unified",
    )

    return fig
