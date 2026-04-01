"""
predictions_charts.py — Charts for the Predictions vs Reality page.

Two chart builders:
  1. fan_chart(df, technology) — Fan of historical WEO projection lines vs actual,
     with independent forecasters (RMI, RethinkX) shown for contrast.
  2. predictions_preview(df) — Compact homepage preview showing the key solar
     underestimation story.

The "fan" visualization:
  - Each IEA WEO edition: thin dashed line, color-coded from orange (early, furthest off)
    to gray (recent, closer to reality)
  - Independent forecasters (RMI, RethinkX/Seba): blue/teal dashed lines
  - Actual: thick dark line drawn on top

Key insight communicated:
  - Solar: early IEA forecasts off by 10–60×; independent forecasters much closer
  - Wind: IEA off by ~2–3× in early editions; relatively better than solar
  - CCS: IEA consistently projected 100–1000× more capture than actually delivered
"""

import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Shared styling (matches context_charts.py conventions)
# ---------------------------------------------------------------------------

CHART_FONT   = dict(family="Inter, Helvetica Neue, Arial, sans-serif", size=12)
CHART_MARGIN = dict(l=60, r=24, t=54, b=50)
PAPER_BG     = "rgba(0,0,0,0)"
PLOT_BG      = "#ffffff"
GRID_COLOR   = "#f0f0f0"

# IEA WEO line color scale: oldest editions are red-orange (far off), newer are gray
_IEA_EDITION_YEARS = list(range(2002, 2023))
_IEA_COLORS = [
    "#d62728",  # 2002 — deepest red
    "#e03524",
    "#e64320",
    "#ed5a1e",
    "#f47420",  # 2006
    "#f48a25",
    "#f4a261",  # 2008
    "#e8a44a",
    "#d4a535",  # 2010
    "#bfa540",
    "#aaa550",  # 2012
    "#95a262",
    "#809f74",  # 2014
    "#6a9c87",
    "#55999a",  # 2016
    "#4090a8",
    "#3586b4",  # 2018
    "#2a7cc0",
    "#2272ca",  # 2020
    "#1a68d4",
    "#1260de",  # 2022
]

def _iea_color(edition_year: int) -> str:
    idx = edition_year - 2002
    if 0 <= idx < len(_IEA_COLORS):
        return _IEA_COLORS[idx]
    return "#888888"


# Independent forecaster colors (blue-teal palette)
_INDEPENDENT_COLORS = {
    "RMI 2011":      "#0077b6",
    "Seba 2014":     "#00b4d8",
    "RethinkX 2020": "#06d6a0",
    "RMI 2021":      "#48cae4",
}


def _empty_chart(message: str, height: int = 400) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=f"<span style='color:#6c757d'>{message}</span>",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False, font=dict(size=13), align="center",
    )
    fig.update_layout(
        paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        height=height, margin=dict(l=10, r=10, t=10, b=10), font=CHART_FONT,
    )
    return fig


# ---------------------------------------------------------------------------
# Config per technology
# ---------------------------------------------------------------------------

_TECH_CONFIG = {
    "solar": {
        "title":       "Solar PV: IEA Projections vs Reality",
        "y_label":     "Global installed capacity (GW)",
        "unit":        "GW",
        "actual_label": "Actual solar PV (IRENA)",
        "actual_color": "#f4a261",   # warm orange — solar
        "x_range":     [2000, 2033],
        "annotation_year": 2023,
        "annotation_text": (
            "<b>Actual 2023: 1,415 GW</b><br>"
            "IEA WEO 2006 projected<br>~142 GW for 2030 — ~10× off"
        ),
        "insight": (
            "IEA's 2006 Reference Scenario projected ~142 GW of solar by 2030.<br>"
            "Reality: 1,415 GW by 2023 — <b>~10× more than predicted.</b><br>"
            "Note: Early WEO editions may have reported in TWh, not GW."
        ),
        "why_wrong": (
            "IEA used linear extrapolation of historical growth, missing<br>"
            "the technology learning curve and economies of scale that drove<br>"
            "solar costs down 90% between 2010 and 2023 (IRENA)."
        ),
    },
    "wind": {
        "title":       "Wind Power: IEA Projections vs Reality",
        "y_label":     "Global installed capacity (GW)",
        "unit":        "GW",
        "actual_label": "Actual wind (IRENA)",
        "actual_color": "#2dc653",   # green — wind
        "x_range":     [2000, 2033],
        "annotation_year": 2023,
        "annotation_text": (
            "<b>Actual 2023: 1,017 GW</b><br>"
            "IEA WEO 2002 projected only<br>450 GW for 2030 — 2.3× off"
        ),
        "insight": (
            "IEA's early wind forecasts were closer than solar but still<br>"
            "consistently low. The 2002 forecast for 2030 was off by ~2×."
        ),
        "why_wrong": (
            "Wind forecasts were better-calibrated than solar because wind<br>"
            "had a longer history. Still, policy acceleration and cost declines<br>"
            "consistently outpaced IEA expectations."
        ),
    },
    "ccs": {
        "title":       "CCS: Forecasts vs Reality (Systematic Overestimation)",
        "y_label":     "CO₂ captured (MtCO₂/yr)",
        "unit":        "MtCO₂/yr",
        "actual_label": "Actual CCS (IEA/Global CCS Institute)",
        "actual_color": "#e63946",   # red — underperforming vs forecasts
        "x_range":     [2005, 2055],
        "annotation_year": 2023,
        "annotation_text": (
            "<b>Actual 2023: ~51 MtCO₂/yr</b> (GCCS)<br>"
            "IEA 2009 roadmap projected<br>150 MtCO₂/yr by 2020 — 3× overestimate"
        ),
        "insight": (
            "While solar/wind were underestimated, CCS has been<br>"
            "<b>massively overestimated.</b> IEA's NZE pathway needs 1,000 Mt/yr<br>"
            "by 2030. Current reality: ~51 Mt/yr (GCCS 2023)."
        ),
        "why_wrong": (
            "CCS faces genuine engineering and economic barriers: high energy<br>"
            "penalty (~25%), storage risks, transport costs, and lack of business<br>"
            "model. Unlike solar/wind, CCS has no self-reinforcing learning curve."
        ),
    },
}


# ---------------------------------------------------------------------------
# Main chart: fan of projections vs actual
# ---------------------------------------------------------------------------

def fan_chart(df: pd.DataFrame, technology: str = "solar") -> go.Figure:
    """
    Fan chart showing historical IEA WEO projection lines vs actual trajectory.
    Independent forecasters (RMI, Seba, RethinkX) shown for contrast.

    Parameters
    ----------
    df         : predictions.parquet DataFrame (all technologies)
    technology : "solar", "wind", or "ccs"
    """
    if df.empty:
        return _empty_chart("Run scripts/process_predictions.py to generate data.")

    cfg = _TECH_CONFIG.get(technology, _TECH_CONFIG["solar"])
    tech_df = df[df["technology"] == technology].copy()

    fig = go.Figure()

    # -----------------------------------------------------------------------
    # 1. IEA WEO projection lines (drawn first — underneath actual)
    # -----------------------------------------------------------------------
    iea_editions = (
        tech_df[
            (tech_df["source_type"] == "IEA_WEO") & (~tech_df["is_actual"])
        ]["edition"].unique()
    )

    # Sort by edition year (ascending) so legend is ordered oldest → newest
    iea_editions = sorted(iea_editions, key=lambda e: int(e.split()[-1]))

    for edition in iea_editions:
        ed_df = tech_df[tech_df["edition"] == edition].sort_values("year")
        if ed_df.empty:
            continue
        edition_year = int(ed_df["edition_year"].iloc[0])
        color = _iea_color(edition_year)

        # Visibility: show only a subset by default to avoid overwhelming chart
        # Show every other edition; user can toggle individual traces
        visible: bool | str = True if edition_year % 4 == 2 else "legendonly"

        fig.add_trace(go.Scatter(
            x=ed_df["year"],
            y=ed_df["value"],
            name=edition,
            legendgroup="IEA WEO",
            legendgrouptitle=dict(text="IEA WEO Projections") if edition == iea_editions[0] else None,
            mode="lines",
            line=dict(color=color, width=1.3, dash="dot"),
            opacity=0.85,
            visible=visible,
            hovertemplate=(
                f"<b>{edition}</b><br>"
                f"%{{x}}: %{{y:,.0f}} {cfg['unit']}<br>"
                "<i>IEA New Policies / STEPS scenario</i>"
                "<extra></extra>"
            ),
        ))

    # -----------------------------------------------------------------------
    # 2. Independent forecaster lines (RMI, RethinkX, Seba)
    # -----------------------------------------------------------------------
    indep_editions = (
        tech_df[
            (tech_df["source_type"] == "independent") & (~tech_df["is_actual"])
        ]["edition"].unique()
    )
    indep_editions = sorted(indep_editions, key=lambda e: int(e.split()[-1]))

    for edition in indep_editions:
        ed_df = tech_df[tech_df["edition"] == edition].sort_values("year")
        if ed_df.empty:
            continue
        color = _INDEPENDENT_COLORS.get(edition, "#00b4d8")

        fig.add_trace(go.Scatter(
            x=ed_df["year"],
            y=ed_df["value"],
            name=edition,
            legendgroup="Independent",
            legendgrouptitle=dict(text="Independent Forecasters") if edition == indep_editions[0] else None,
            mode="lines+markers",
            line=dict(color=color, width=2, dash="dash"),
            marker=dict(size=5, color=color),
            hovertemplate=(
                f"<b>{edition}</b><br>"
                f"%{{x}}: %{{y:,.0f}} {cfg['unit']}<br>"
                "<i>RMI / Tony Seba / RethinkX</i>"
                "<extra></extra>"
            ),
        ))

    # -----------------------------------------------------------------------
    # 3. Actual trajectory (drawn last — on top, thick)
    # -----------------------------------------------------------------------
    actual_df = tech_df[tech_df["is_actual"]].sort_values("year")
    if not actual_df.empty:
        fig.add_trace(go.Scatter(
            x=actual_df["year"],
            y=actual_df["value"],
            name=cfg["actual_label"],
            legendgroup="Actual",
            mode="lines+markers",
            line=dict(color="#1a1a2e", width=3.5),
            marker=dict(size=5, color="#1a1a2e"),
            hovertemplate=(
                f"<b>Actual %{{x}}: %{{y:,.0f}} {cfg['unit']}</b><br>"
                "<i>Source: IRENA / Global CCS Institute</i>"
                "<extra>Actual</extra>"
            ),
        ))

    # -----------------------------------------------------------------------
    # Annotation: key data point callout
    # -----------------------------------------------------------------------
    ann_year = cfg["annotation_year"]
    ann_row = actual_df[actual_df["year"] == ann_year]
    if not ann_row.empty:
        fig.add_annotation(
            x=ann_year,
            y=float(ann_row["value"].iloc[0]),
            text=cfg["annotation_text"],
            showarrow=True,
            arrowhead=2,
            arrowwidth=1.5,
            arrowcolor="#1a1a2e",
            ax=-110, ay=-50,
            font=dict(size=10, color="#1a1a2e"),
            bgcolor="rgba(255,255,255,0.92)",
            bordercolor="#1a1a2e",
            borderpad=4,
            align="left",
        )

    # -----------------------------------------------------------------------
    # Layout
    # -----------------------------------------------------------------------
    fig.update_layout(
        title=dict(
            text=cfg["title"],
            font=dict(size=15),
            x=0,
        ),
        xaxis=dict(
            title="Year",
            tickformat="d",
            showgrid=True,
            gridcolor=GRID_COLOR,
            range=cfg["x_range"],
        ),
        yaxis=dict(
            title=cfg["y_label"],
            showgrid=True,
            gridcolor=GRID_COLOR,
            tickformat=",d",
            rangemode="tozero",
        ),
        legend=dict(
            orientation="v",
            x=1.02, y=1,
            xanchor="left",
            yanchor="top",
            font=dict(size=10),
            groupclick="toggleitem",
            traceorder="grouped",
            itemwidth=30,
        ),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=CHART_FONT,
        margin=dict(l=60, r=200, t=54, b=50),
        height=520,
        hovermode="x unified",
    )

    return fig


# ---------------------------------------------------------------------------
# Preview chart for homepage — compact, shows the key solar story
# ---------------------------------------------------------------------------

def predictions_preview(df: pd.DataFrame) -> go.Figure:
    """
    Compact homepage preview: 3 selected WEO solar lines vs actual.
    Designed to immediately communicate the systematic underestimation story
    without requiring interaction. Height ~260px.
    """
    if df.empty:
        return _empty_chart("Prediction data not loaded.", height=260)

    solar = df[df["technology"] == "solar"].copy()
    fig = go.Figure()

    # Show only 3 representative WEO editions: 2006, 2012, 2018
    for edition_year, label, color in [
        (2006, "WEO 2006", "#d62728"),
        (2012, "WEO 2012", "#aaa550"),
        (2018, "WEO 2018", "#2a7cc0"),
    ]:
        ed_df = solar[solar["edition"] == f"WEO {edition_year}"].sort_values("year")
        if ed_df.empty:
            continue
        fig.add_trace(go.Scatter(
            x=ed_df["year"], y=ed_df["value"],
            name=label,
            mode="lines",
            line=dict(color=color, width=1.5, dash="dot"),
            hovertemplate=f"<b>{label}</b><br>%{{x}}: %{{y:,.0f}} GW<extra></extra>",
        ))

    # Actual line
    actual = solar[solar["is_actual"]].sort_values("year")
    if not actual.empty:
        fig.add_trace(go.Scatter(
            x=actual["year"], y=actual["value"],
            name="Actual (IRENA)",
            mode="lines+markers",
            line=dict(color="#1a1a2e", width=3),
            marker=dict(size=4),
            hovertemplate="<b>Actual %{x}</b>: %{y:,.0f} GW<extra></extra>",
        ))

    # Brief annotation
    fig.add_annotation(
        x=2023, y=1415,
        text="<b>1,415 GW</b> actual<br>vs ~142 GW forecast<br>(WEO 2006 for 2030)",
        showarrow=True,
        arrowhead=2,
        arrowwidth=1.2,
        arrowcolor="#1a1a2e",
        ax=-100, ay=-40,
        font=dict(size=9, color="#1a1a2e"),
        bgcolor="rgba(255,255,255,0.92)",
        bordercolor="#1a1a2e",
        borderpad=3,
        align="left",
    )

    fig.update_layout(
        title=dict(
            text="Solar PV: IEA Systematically Underestimated Growth",
            font=dict(size=12),
            x=0,
        ),
        xaxis=dict(
            title=None, tickformat="d", showgrid=True, gridcolor=GRID_COLOR,
            range=[2000, 2027],
        ),
        yaxis=dict(
            title="GW", showgrid=True, gridcolor=GRID_COLOR,
            tickformat=",d", rangemode="tozero",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="left", x=0,
            font=dict(size=9),
        ),
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=CHART_FONT,
        margin=dict(l=55, r=15, t=44, b=35),
        height=260,
        hovermode="x unified",
    )

    return fig
