"""
home.py — Homepage layout for the Energy Transition Dashboard.

Structure (per finalized plan):
  1. Hero Statistics (5 headline numbers above the fold)
  2. Interactive World Map (thematic buttons, not dropdown)
  3. Thematic Sections (below the fold):
     - Emissions & Pathways
     - Clean Energy Momentum
     - Costs & Finance
     - Health & Environmental Justice (dedicated narrative section)
  4. Context Charts

Design principles applied:
  - Mobile-first: responsive columns, mobile breakpoints in custom.css
  - No server callbacks for KPI display (kpis.json driven)
  - Health/EJ is a standalone named section, NOT a row in a grid
  - Accessibility: aria-labels on all interactive elements
"""

import dash
from dash import html, dcc, callback, Output, Input, State, no_update, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd

from utils.data_loader import (
    get_kpis, get_emissions, get_capacity, get_scenarios,
    get_energy_mix, get_nze_milestones, get_costs, get_predictions,
    get_health, get_latest_year_map, get_investment, get_subsidies,
    get_heat_deaths_reference, get_lancet_heat_mortality,
    get_climate_disasters,
)
from components.kpi_card import make_hero_stats_row, make_thematic_stats_row, HERO_KEYS
from components.context_charts import (
    emissions_vs_pathways, deployment_tracker, cost_revolution,
    investment_clean_vs_fossil, investment_regional_bars,
    subsidies_top_countries, subsidies_time_series,
    health_global_mortality_trend, health_deaths_per_twh_bars,
    health_heat_mortality_trend,
)
from components.predictions_charts import predictions_preview, fan_chart

dash.register_page(__name__, path="/", title="Energy Transition Dashboard")


# ---------------------------------------------------------------------------
# Figure builders — called once per page load; data is pre-loaded in memory
# ---------------------------------------------------------------------------

def _build_emissions_pathways_fig():
    """Build the global emissions vs IPCC pathway bands figure."""
    try:
        return emissions_vs_pathways(get_emissions(), get_scenarios())
    except Exception as exc:
        # Defensive: never crash the homepage over a chart error
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_annotation(
            text=f"Chart unavailable: {exc}",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=12, color="#6c757d"),
        )
        fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="#ffffff",
                          xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig


def _build_cost_revolution_fig():
    """Build the clean energy cost revolution (LCOE) chart."""
    try:
        return cost_revolution(get_costs())
    except Exception as exc:
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_annotation(
            text=f"Chart unavailable: {exc}",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=12, color="#6c757d"),
        )
        fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="#ffffff",
                          xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig


def _build_investment_fig():
    """Build the global clean vs fossil investment chart."""
    try:
        return investment_clean_vs_fossil(get_investment())
    except Exception as exc:
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_annotation(
            text=f"Chart unavailable: {exc}",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=12, color="#6c757d"),
        )
        fig.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#ffffff",
                          xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig


def _build_regional_investment_fig():
    """Build the regional investment breakdown chart."""
    try:
        return investment_regional_bars(get_investment())
    except Exception as exc:
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_annotation(
            text=f"Chart unavailable: {exc}",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=12, color="#6c757d"),
        )
        fig.update_layout(height=380, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#ffffff",
                          xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig


def _build_subsidies_countries_fig():
    """Build the top subsidized countries chart."""
    try:
        return subsidies_top_countries(get_subsidies())
    except Exception as exc:
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_annotation(
            text=f"Chart unavailable: {exc}",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=12, color="#6c757d"),
        )
        fig.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#ffffff",
                          xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig


def _build_subsidies_time_fig():
    """Build the global subsidies time series chart."""
    try:
        return subsidies_time_series(get_subsidies())
    except Exception as exc:
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_annotation(
            text=f"Chart unavailable: {exc}",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=12, color="#6c757d"),
        )
        fig.update_layout(height=360, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#ffffff",
                          xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig


def _get_investment_kpis() -> dict:
    """Extract headline investment numbers from real data."""
    inv = get_investment()
    result = {}
    if inv.empty:
        return result
    world = inv[inv["region"] == "World"].sort_values("year")
    if world.empty:
        return result
    latest = world.iloc[-1]
    result["clean_bn"] = latest.get("clean_energy_investment_bn")
    result["fossil_bn"] = latest.get("fossil_fuel_investment_bn")
    result["year"] = int(latest["year"])
    result["clean_share"] = latest.get("clean_share_pct")
    # Year-over-year growth
    if len(world) >= 2:
        prev = world.iloc[-2]
        if prev.get("clean_energy_investment_bn") and prev["clean_energy_investment_bn"] > 0:
            result["clean_yoy_pct"] = (
                (latest["clean_energy_investment_bn"] - prev["clean_energy_investment_bn"])
                / prev["clean_energy_investment_bn"] * 100
            )
    return result


def _predictions_preview_fig():
    """Build the compact predictions preview chart for the homepage."""
    try:
        return predictions_preview(get_predictions())
    except Exception as exc:
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_annotation(
            text=f"Chart unavailable: {exc}",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=12, color="#6c757d"),
        )
        fig.update_layout(height=260, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#ffffff",
                          xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig


def _build_predictions_preview_fig():
    """Build the compact predictions preview chart for the homepage."""
    try:
        return predictions_preview(get_predictions())
    except Exception as exc:
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_annotation(
            text=f"Chart unavailable: {exc}",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=12, color="#6c757d"),
        )
        fig.update_layout(height=260, paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="#ffffff",
                          xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig


def _build_deployment_tracker_fig():
    """Build the renewable deployment tracker figure."""
    try:
        return deployment_tracker(get_capacity(), get_nze_milestones(), get_energy_mix())
    except Exception as exc:
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_annotation(
            text=f"Chart unavailable: {exc}",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=12, color="#6c757d"),
        )
        fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="#ffffff",
                          xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig


def _build_hero_trendline(key: str) -> go.Figure:
    """Build a historical trendline figure for a hero KPI modal popup."""
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#ffffff",
        font=dict(family="Inter, Helvetica Neue, Arial, sans-serif", size=12),
        margin=dict(l=60, r=24, t=40, b=50), height=350, hovermode="x unified",
        xaxis=dict(showgrid=True, gridcolor="#f0f0f0", tickformat="d"),
        yaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
    )

    if key == "current_policies_warming_c":
        # Show HadCRUT5 historical temperature anomaly, rebased to 1850-1900
        from pathlib import Path
        hadcrut_path = Path("data/raw/hadcrut5_global_annual.csv")
        if hadcrut_path.exists():
            try:
                df = pd.read_csv(hadcrut_path)
                df = df.rename(columns={df.columns[0]: "year", df.columns[1]: "anomaly"})
                df = df[df["anomaly"].notna()].sort_values("year")
                if not df.empty:
                    # Rebase from 1961-1990 baseline to 1850-1900 (IPCC AR6 standard)
                    # The offset is the mean anomaly over 1850-1900 relative to 1961-1990
                    baseline_offset = df[df["year"].between(1850, 1900)]["anomaly"].mean()
                    df["anomaly_rebased"] = df["anomaly"] - baseline_offset

                    # Confidence band (also rebased)
                    lower = df.iloc[:, 2] if len(df.columns) > 2 else None
                    upper = df.iloc[:, 3] if len(df.columns) > 3 else None
                    if lower is not None and upper is not None:
                        lower_rebased = lower - baseline_offset
                        upper_rebased = upper - baseline_offset
                        fig.add_trace(go.Scatter(
                            x=pd.concat([df["year"], df["year"][::-1]]),
                            y=pd.concat([upper_rebased, lower_rebased[::-1]]),
                            fill="toself", fillcolor="rgba(255,0,0,0.08)",
                            line=dict(width=0), showlegend=False,
                            hoverinfo="skip",
                        ))
                    fig.add_trace(go.Scatter(
                        x=df["year"], y=df["anomaly_rebased"],
                        mode="lines", line=dict(color="#d32f2f", width=2.5),
                        name="Temperature anomaly",
                        hovertemplate="<b>%{x}</b>: %{y:.2f}°C<extra></extra>",
                    ))
                    # 1.5°C and 2°C reference lines
                    fig.add_hline(y=1.5, line_dash="dash", line_color="#ff9800",
                                  annotation_text="1.5°C target", annotation_position="top left")
                    fig.add_hline(y=2.0, line_dash="dash", line_color="#f44336",
                                  annotation_text="2°C limit", annotation_position="top left")
                    fig.update_layout(
                        title=dict(text="Global Temperature Anomaly (HadCRUT5)", font=dict(size=14)),
                        yaxis_title="°C above 1850–1900 baseline",
                    )
                    return fig
            except Exception:
                pass

    elif key == "renewable_share_electricity_pct":
        df = get_energy_mix()
        if not df.empty:
            yearly = df.groupby("year").agg(
                total_re=("total_electricity_twh", lambda x: (
                    df.loc[x.index, "renewable_share_electricity_pct"].fillna(0) / 100
                    * df.loc[x.index, "total_electricity_twh"].fillna(0)
                ).sum()),
                total_gen=("total_electricity_twh", "sum"),
            ).reset_index()
            yearly["pct"] = yearly["total_re"] / yearly["total_gen"] * 100
            yearly = yearly[yearly["total_gen"] > 0].sort_values("year")
            # Filter out incomplete years (e.g. 2025 with few countries reporting)
            if not yearly.empty:
                max_gen = yearly["total_gen"].max()
                yearly = yearly[yearly["total_gen"] > max_gen * 0.5]
            if not yearly.empty:
                fig.add_trace(go.Scatter(
                    x=yearly["year"], y=yearly["pct"],
                    mode="lines+markers", line=dict(color="#2e7d32", width=2.5),
                    marker=dict(size=4), name="Renewable share",
                    hovertemplate="<b>%{x}</b>: %{y:.1f}%<extra></extra>",
                ))
                fig.update_layout(
                    title=dict(text="Renewable Share of Electricity Generation", font=dict(size=14)),
                    yaxis_title="% of electricity",
                )
                return fig

    elif key == "renewable_share_total_energy_pct":
        # Total energy renewable share — approximate from OWID
        df = get_energy_mix()
        re_col = "renewable_share_final_energy_pct" if "renewable_share_final_energy_pct" in df.columns else "renewable_share_energy_pct"
        en_col = "primary_energy_ej" if "primary_energy_ej" in df.columns else "primary_energy_twh"
        if not df.empty and re_col in df.columns and en_col in df.columns:
            yearly = df.groupby("year").agg(
                total_re=(en_col, lambda x: (
                    df.loc[x.index, re_col].fillna(0) / 100
                    * df.loc[x.index, en_col].fillna(0)
                ).sum()),
                total_en=(en_col, "sum"),
            ).reset_index()
            yearly["pct"] = yearly["total_re"] / yearly["total_en"] * 100
            yearly = yearly[yearly["total_en"] > 0].sort_values("year")
            # Filter out incomplete years
            if not yearly.empty:
                max_en = yearly["total_en"].max()
                yearly = yearly[yearly["total_en"] > max_en * 0.5]
            if not yearly.empty:
                fig.add_trace(go.Scatter(
                    x=yearly["year"], y=yearly["pct"],
                    mode="lines+markers", line=dict(color="#1565c0", width=2.5),
                    marker=dict(size=4), name="Renewable share (total energy)",
                    hovertemplate="<b>%{x}</b>: %{y:.1f}%<extra></extra>",
                ))
                fig.update_layout(
                    title=dict(text="Renewable Share of Total Energy Consumption", font=dict(size=14)),
                    yaxis_title="% of total energy",
                )
                return fig

    elif key == "clean_energy_investment_t":
        inv = get_investment()
        if not inv.empty:
            world = inv[inv["region"] == "World"].sort_values("year")
            if not world.empty and "clean_energy_investment_bn" in world.columns:
                world = world[world["clean_energy_investment_bn"].notna()]
                fig.add_trace(go.Scatter(
                    x=world["year"], y=world["clean_energy_investment_bn"] / 1000,
                    mode="lines+markers", line=dict(color="#2e7d32", width=2.5),
                    marker=dict(size=5), name="Clean energy",
                    hovertemplate="<b>%{x}</b>: $%{y:.2f}T<extra></extra>",
                ))
                if "fossil_fuel_investment_bn" in world.columns:
                    fossil = world[world["fossil_fuel_investment_bn"].notna()]
                    fig.add_trace(go.Scatter(
                        x=fossil["year"], y=fossil["fossil_fuel_investment_bn"] / 1000,
                        mode="lines+markers", line=dict(color="#795548", width=2.5),
                        marker=dict(size=5), name="Fossil fuel",
                        hovertemplate="<b>%{x}</b>: $%{y:.2f}T<extra></extra>",
                    ))
                fig.update_layout(
                    title=dict(text="Global Energy Investment", font=dict(size=14)),
                    yaxis_title="$T/yr",
                )
                return fig

    elif key == "health_deaths_fossil_pm25":
        # Show the same 4-line climate-attributable deaths chart as the health section
        return _build_health_mortality_fig()

    # Fallback: no data available
    fig.add_annotation(
        text="Historical time series not available for this metric.",
        xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
        font=dict(size=13, color="#6c757d"),
    )
    fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig


def _build_hero_modals() -> list:
    """Build modal dialogs for each hero KPI card."""
    kpis = get_kpis()
    # Custom modal titles that better describe the trendline shown
    _modal_titles = {
        "current_policies_warming_c": "Historical Temperature Anomaly (HadCRUT5)",
        "health_deaths_fossil_pm25": "Climate-Attributable Deaths (global)",
    }
    modals = []
    for key in HERO_KEYS:
        kpi = kpis.get(key, {})
        label = _modal_titles.get(key, kpi.get("label", key))
        source = kpi.get("source", "")
        note = kpi.get("note", "")

        modal = dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle(label)),
            dbc.ModalBody([
                dcc.Graph(
                    id=f"hero-modal-chart-{key}",
                    figure=_build_hero_trendline(key),
                    config={"responsive": True, "displayModeBar": True, "displaylogo": False},
                ),
                html.P(note, className="small text-muted mt-2") if note else None,
                html.Small(f"Source: {source}", className="text-muted fst-italic") if source else None,
            ]),
        ], id=f"hero-modal-{key}", size="lg", is_open=False)
        modals.append(modal)
    return modals


def _safe_fig(builder, height=380):
    """Wrap a chart builder in error handling."""
    try:
        return builder()
    except Exception as exc:
        fig = go.Figure()
        fig.add_annotation(
            text=f"Chart unavailable: {exc}",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=12, color="#6c757d"),
        )
        fig.update_layout(height=height, paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="#ffffff",
                          xaxis=dict(visible=False), yaxis=dict(visible=False))
        return fig


def _build_health_mortality_fig():
    return _safe_fig(lambda: health_global_mortality_trend(
        get_health(), get_lancet_heat_mortality(), get_climate_disasters()))


def _build_health_deaths_twh_fig():
    return _safe_fig(lambda: health_deaths_per_twh_bars())


def _build_health_heat_fig():
    return _safe_fig(lambda: health_heat_mortality_trend(get_lancet_heat_mortality()))


def _build_predictions_fan_fig(tech="solar"):
    return _safe_fig(lambda: fan_chart(get_predictions(), tech))


def _fmt_kpi_value(kpis: dict, key: str, fallback: str) -> str:
    """Format a KPI value for display, falling back to hardcoded reference if data unavailable."""
    kpi = kpis.get(key, {})
    val = kpi.get("value")
    unit = kpi.get("unit", "")
    if val is None:
        return fallback
    return f"~{val:.1f} {unit}"


def _kpi_source_note(kpis: dict, key: str, fallback_source: str) -> str:
    """Return the source note for a KPI, falling back if needed."""
    kpi = kpis.get(key, {})
    status = kpi.get("status", "")
    source = kpi.get("source", fallback_source)
    if kpi.get("value") is None:
        return f"{source} (data pending)"
    year = kpi.get("year")
    return f"Source: {source}{f' ({year})' if year else ''}"


def _build_generation_hero_cards() -> html.Div:
    """Build clickable generation cards (TWh) for all major sources.

    Each card has a click ID so the callback can show a historical trendline.
    """
    try:
        em = get_energy_mix()
        if em.empty:
            return html.Div()

        gen_cols = [
            "electricity_twh_solar", "electricity_twh_wind",
            "electricity_twh_coal", "electricity_twh_gas", "electricity_twh_hydro",
            "electricity_twh_nuclear",
        ]
        available_cols = [c for c in gen_cols if c in em.columns]
        if not available_cols:
            return html.Div()

        # Count reporting countries per year to detect incomplete years
        country_counts = em.dropna(subset=available_cols, how="all").groupby("year").size()
        yearly = em.groupby("year")[available_cols].sum().reset_index()
        yearly = yearly.sort_values("year")
        while len(yearly) >= 2:
            ly = int(yearly.iloc[-1]["year"])
            py = int(yearly.iloc[-2]["year"])
            lc = country_counts.get(ly, 0)
            pc = country_counts.get(py, 0)
            if pc > 0 and lc < pc * 0.7:
                yearly = yearly.iloc[:-1]
            else:
                break

        if yearly.empty:
            return html.Div()

        latest_yr = int(yearly.iloc[-1]["year"])
        latest = yearly[yearly["year"] == latest_yr].iloc[0]
        prev_yr = latest_yr - 1
        prev_row = yearly[yearly["year"] == prev_yr]

        source_defs = [
            ("electricity_twh_solar", "Solar", "bi-sun-fill", "text-warning", "solar"),
            ("electricity_twh_wind", "Wind", "bi-wind", "text-success", "wind"),
            ("electricity_twh_hydro", "Hydro", "bi-water", "text-info", "hydro"),
            ("electricity_twh_gas", "Gas", "bi-fire", "text-secondary", "gas"),
            ("electricity_twh_coal", "Coal", "bi-gem", "text-secondary", "coal"),
            ("electricity_twh_nuclear", "Nuclear", "bi-radioactive", "text-purple", "nuclear"),
        ]

        cards = []
        for col, label, icon_cls, color, key in source_defs:
            if col not in available_cols:
                continue
            val = latest.get(col, 0)
            if val <= 0:
                continue
            val_str = f"{val:,.0f} TWh"
            yoy = ""
            if not prev_row.empty:
                prev_val = prev_row.iloc[0].get(col, 0)
                if prev_val > 0:
                    pct = (val - prev_val) / prev_val * 100
                    yoy = f"{pct:+.1f}%"

            card = dbc.Card(dbc.CardBody([
                html.Div([
                    html.I(className=f"bi {icon_cls} me-1 {color} small"),
                    html.Small(f"{label}", className="text-muted"),
                ], className="d-flex align-items-center"),
                html.Div(val_str, className="fs-5 fw-bold mt-1"),
                html.Small(f"{latest_yr} {yoy}", className="text-muted"),
                html.Div(
                    html.Small("Click for trend", className="text-primary"),
                    style={"fontSize": "0.65rem"},
                ),
            ], className="py-2 px-3"),
                className="kpi-card kpi-card-thematic h-100 border-0 shadow-sm",
                style={"cursor": "pointer"})

            cards.append(dbc.Col(
                html.Div(card, id=f"energy-gen-{key}", n_clicks=0),
                xs=6, sm=4, lg=True, className="mb-2",
            ))

        return html.Div([
            html.Small("Electricity generation by source (TWh/yr):",
                       className="text-muted fw-bold d-block mb-1"),
            dbc.Row(cards, className="g-2"),
        ], className="mt-2")
    except Exception:
        return html.Div()


def _build_health_ej_cards(kpis: dict) -> html.Div:
    """
    Build the Health section cards focused on fossil fuel health impacts.

    Three clear categories:
      1. Deaths from fossil fuel PM2.5 (range: McDuffie to Vohra)
      2. Climate-attributable heat deaths (Lancet Countdown)
      3. Deaths from all outdoor PM2.5 (GBD context)

    Household air pollution removed — it's a poverty/clean-cooking issue,
    not a fossil fuel combustion issue.
    """
    ambient_val  = _fmt_kpi_value(kpis, "deaths_ambient_pm25_m", "~4.9 million")
    ambient_src  = _kpi_source_note(kpis, "deaths_ambient_pm25_m", "IHME Global Burden of Disease 2023")

    return html.Div([
        dbc.Row([
            # Card 1: Fossil fuel PM2.5 deaths (range)
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Deaths from fossil fuel PM2.5",
                                className="fw-bold text-danger"),
                        html.Div("1.3–8.7M/yr", className="fs-3 fw-bold"),
                        html.P([
                            "Premature deaths from outdoor PM2.5 ",
                            html.Strong("attributed to fossil fuel combustion"),
                            ". The range reflects methodology differences: ",
                            html.A("McDuffie et al. 2021",
                                   href="https://doi.org/10.1038/s41467-021-23853-y",
                                   target="_blank", className="text-muted"),
                            " (~1.3M, GBD sector attribution); ",
                            html.A("Lelieveld et al. 2023",
                                   href="https://doi.org/10.1136/bmj-2023-077784",
                                   target="_blank", className="text-muted"),
                            " (~5.1M, atmospheric chemistry model); ",
                            html.A("Vohra et al. 2021",
                                   href="https://doi.org/10.1016/j.envres.2021.110754",
                                   target="_blank", className="text-muted"),
                            " (~8.7M, updated CRFs). ",
                            "Does not include NO\u2082, SO\u2082, or ozone.",
                        ], className="small text-muted mb-1"),
                    ])
                ], className="h-100 border-danger"),
            ], xs=12, md=6, className="mb-3"),

            # Card 2: All-source outdoor PM2.5 (GBD context)
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Deaths from all outdoor PM2.5 (GBD)",
                                className="fw-bold"),
                        html.Div(ambient_val, className="fs-3 fw-bold"),
                        html.P([
                            "GBD total from ", html.Strong("all sources"),
                            " of outdoor PM2.5: fossil fuels, dust, wildfires, agriculture, "
                            "biomass. Fossil fuels = ~33% of this total (",
                            html.A("McDuffie 2021",
                                   href="https://doi.org/10.1038/s41467-021-23853-y",
                                   target="_blank", className="text-muted"),
                            ").",
                        ], className="small text-muted mb-1"),
                        html.Small(ambient_src, className="text-muted fst-italic"),
                    ])
                ], className="h-100"),
            ], xs=12, md=6, className="mb-3"),
        ], className="g-3 mb-2"),
    ])


def _build_climate_deaths_alert() -> dbc.Alert:
    """
    Build the climate deaths context alert using real Lancet Countdown data
    when available, falling back to hardcoded reference values.
    """
    heat_ref = get_heat_deaths_reference()

    if heat_ref and heat_ref.get("avg_3yr_deaths"):
        avg_deaths = heat_ref["avg_3yr_deaths"]
        period = heat_ref.get("avg_3yr_period", "recent")
        # Format deaths as readable number
        deaths_str = f"~{avg_deaths:,}"
    else:
        deaths_str = "~546,000"  # Fallback: Lancet Countdown 2025 (2019-2023 avg)
        period = None

    # Compute climate-attributable fraction (37%, Vicedo-Cabrera 2021)
    climate_deaths = int(float(deaths_str.replace("~", "").replace(",", "")) * 0.37) if deaths_str else 200000
    climate_str = f"~{climate_deaths:,}"

    content = [
        html.Strong("Heat deaths (separate from air pollution): "),
        f"Total heat-related mortality: {deaths_str}/yr globally",
    ]
    if period:
        content.append(f" ({period} average)")
    content.extend([
        " (",
        html.A("Lancet Countdown 2025",
               href="https://lancetcountdown.org/2025-report/",
               target="_blank", className="alert-link"),
        f"). Of these, ~37% ({climate_str}) are attributable to anthropogenic "
        "climate change (",
        html.A("Vicedo-Cabrera et al. 2021",
               href="https://doi.org/10.1038/s41558-021-01058-x",
               target="_blank", className="alert-link"),
        ").",
    ])

    return dbc.Alert(content, color="warning", className="small mt-2")


def _build_investment_kpi_cards(inv_kpis: dict) -> dbc.Row:
    """Build headline investment KPI cards from real IEA data."""
    clean_bn = inv_kpis.get("clean_bn")
    fossil_bn = inv_kpis.get("fossil_bn")
    year = inv_kpis.get("year", "")
    clean_share = inv_kpis.get("clean_share")
    yoy = inv_kpis.get("clean_yoy_pct")

    # Fallback values from IEA World Energy Investment 2025
    clean_str = f"${clean_bn/1000:.1f}T" if clean_bn else "$2.2T"   # IEA WEI 2025
    fossil_str = f"${fossil_bn/1000:.1f}T" if fossil_bn else "$1.0T" # IEA WEI 2025
    share_str = f"{clean_share:.0f}%" if clean_share else "65%"      # IEA WEI 2025
    yoy_str = f"+{yoy:.0f}% YoY" if yoy else ""
    yr_str = str(year) if year else "2025"

    def _inv_card(card_id, icon_cls, icon_color, label, value_str, value_color,
                   subtitle, source_label, source_url):
        """Build a single clickable investment KPI card."""
        card = dbc.Card(dbc.CardBody([
            html.Div([
                html.I(className=f"bi {icon_cls} me-1 {icon_color} small"),
                html.Small(label, className="text-muted"),
            ], className="d-flex align-items-center"),
            html.Div(value_str, className=f"fs-3 fw-bold mt-1 {value_color}"),
            html.Small(subtitle, className="text-muted"),
            html.Div(html.A(
                source_label, href=source_url,
                target="_blank", style={"fontSize": "0.7rem", "textDecoration": "none"},
                className="text-muted",
            ), className="mt-1"),
        ], className="py-2 px-3"), className="country-stat-card h-100",
            style={"cursor": "pointer"})
        return html.Div(card, id=card_id, n_clicks=0)

    return dbc.Row([
        dbc.Col(
            _inv_card(
                "inv-card-clean", "bi-graph-up-arrow", "text-success",
                "Clean energy investment", clean_str, "text-success",
                f"{yr_str} (est.) — {yoy_str}" if yoy_str else f"{yr_str} (est.)",
                "IEA WEI 2025",
                "https://www.iea.org/reports/world-energy-investment-2025",
            ),
            xs=12, sm=6, md=3, className="mb-3",
        ),
        dbc.Col(
            _inv_card(
                "inv-card-fossil", "bi-fuel-pump", "text-secondary",
                "Fossil fuel investment", fossil_str, "",
                f"{yr_str} (est.)",
                "IEA WEI 2025",
                "https://www.iea.org/reports/world-energy-investment-2025",
            ),
            xs=12, sm=6, md=3, className="mb-3",
        ),
        dbc.Col(
            _inv_card(
                "inv-card-share", "bi-pie-chart-fill", "text-primary",
                "Clean energy share", share_str, "text-primary",
                f"of total energy investment ({yr_str})",
                "IEA WEI 2025",
                "https://www.iea.org/reports/world-energy-investment-2025",
            ),
            xs=12, sm=6, md=3, className="mb-3",
        ),
        dbc.Col(
            _inv_card(
                "inv-card-regional", "bi-globe-americas", "text-info",
                "Regional breakdown", "By region", "text-info",
                "Click for regional split",
                "IEA WEI 2025",
                "https://www.iea.org/reports/world-energy-investment-2025",
            ),
            xs=12, sm=6, md=3, className="mb-3",
        ),
    ], className="g-3")


def layout(**kwargs):
    kpis = get_kpis()
    inv_kpis = _get_investment_kpis()

    return html.Div([

        # =====================================================================
        # Page intro
        # =====================================================================
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1(
                        "The Global Energy Transition",
                        className="display-5 fw-bold mt-4 mb-1",
                    ),
                    html.P(
                        "A real-time birds-eye view of where we are, where we need to be, "
                        "and how fast we're moving — from emissions and clean energy to costs, "
                        "investment, and the human health stakes.",
                        className="lead text-muted mb-2",
                    ),
                    # Honesty note: momentum is real but adequacy is not
                    dbc.Alert(
                        [
                            html.Strong("⚠️ The gap: "),
                            "Under current implemented policies, the world is on track for ~3.1°C of "
                            "warming (UNEP 2024). Clean energy is accelerating — but not fast enough. "
                            "This dashboard shows both.",
                        ],
                        color="warning",
                        className="mb-3 py-2 small",
                    ),
                ], md=10, lg=8),
            ]),
        ], fluid=False),

        # =====================================================================
        # Section 1: Hero Statistics (5 numbers above the fold)
        # =====================================================================
        dbc.Container([
            html.Hr(className="mb-3"),
            make_hero_stats_row(kpis),
            # Modals for hero card clicks (historical trendlines)
            *_build_hero_modals(),
        ], fluid=False, className="mb-2"),

        # =====================================================================
        # Section 2: Interactive World Map
        # =====================================================================
        dbc.Container([
            html.Div(className="thematic-section", children=[
                html.H2("Where in the World", className="section-heading"),
                html.P(
                    "Select a theme to explore the global picture. Click any country for a full profile.",
                    className="section-subheading",
                ),
                # dcc.Location tracks the URL search string for shareable map links.
                # refresh=False: updating ?metric=... does not reload the page.
                dcc.Location(id="home-loc", refresh=False),
                html.Div(
                    [
                        html.Div(
                            className="map-theme-buttons",
                            children=[
                                dbc.Button("Emissions", id="map-btn-emissions", n_clicks=0,
                                           className="map-theme-btn active"),
                                dbc.Button("Electricity Mix", id="map-btn-renewables", n_clicks=0,
                                           className="map-theme-btn"),
                                dbc.Button("Total Energy Mix", id="map-btn-total-energy", n_clicks=0,
                                           className="map-theme-btn"),
                                dbc.Button("Carbon Pricing", id="map-btn-costs", n_clicks=0,
                                           className="map-theme-btn"),
                                dbc.Button("Health", id="map-btn-health", n_clicks=0,
                                           className="map-theme-btn"),
                                dbc.Button("Damages", id="map-btn-damages", n_clicks=0,
                                           className="map-theme-btn"),
                                dbc.Button("Vulnerability", id="map-btn-vulnerability", n_clicks=0,
                                           className="map-theme-btn"),
                            ],
                        ),
                        html.Div(
                            id="world-map-container",
                            className="map-container",
                            **{"aria-label": "Interactive world map showing energy transition data by country"},
                            children=dcc.Graph(
                                id="world-map",
                                config={
                                    "responsive": True,
                                    "displayModeBar": True,
                                    "modeBarButtonsToRemove": [
                                        "zoom2d", "pan2d", "select2d", "lasso2d",
                                        "zoomIn2d", "zoomOut2d", "autoScale2d",
                                    ],
                                    "displaylogo": False,
                                    "toImageButtonOptions": {
                                        "format": "png",
                                        "filename": "energy_transition_map",
                                        "height": 500,
                                        "width": 900,
                                    },
                                },
                                style={"height": "460px"},
                            ),
                        ),
                        # Small legend note below map
                        html.Div(
                            [
                                html.Small(
                                    "Click any country to open its full profile. "
                                    "Gray countries = data unavailable for this metric.",
                                    className="text-muted",
                                ),
                            ],
                            className="mt-2 px-1",
                        ),
                        # Methodology description (updated by callback per tab)
                        html.Div(
                            id="map-methodology-bar",
                            className="mt-2 px-2 py-2 small text-muted",
                            style={
                                "backgroundColor": "#f8f9fa",
                                "borderRadius": "6px",
                                "border": "1px solid #e9ecef",
                            },
                        ),
                    ]
                ),
            ]),
        ], fluid=False),

        # =====================================================================
        # Section 3: Emissions & Pathways
        # =====================================================================
        dbc.Container([
            html.Div(className="thematic-section", children=[
                html.H2("Emissions & Pathways", className="section-heading"),
                html.P(
                    "Where emissions stand today, and how far they need to fall.",
                    className="section-subheading",
                ),
                make_thematic_stats_row(kpis, [
                    "co2_fossil_gt",
                    "ghg_total_gtco2e",
                    "atmospheric_co2_ppm",
                    "temperature_anomaly_c",
                ], section_id="emissions"),
                # Reset button to restore scenarios view
                html.Div(
                    dbc.Button(
                        "Show pathways",
                        id="emissions-reset-btn",
                        size="sm", outline=True, color="secondary",
                        className="mt-2",
                    ),
                    className="d-flex justify-content-end",
                ),
                # Emissions vs IPCC pathways chart (switchable by section card clicks)
                html.Div(
                    id="emissions-pathways-chart",
                    className="context-chart-card mt-1",
                    **{"aria-label": "Chart showing global CO₂ emissions compared to IPCC 1.5°C, 2°C, and 2.5°C pathway ranges"},
                    children=dcc.Graph(
                        id="emissions-section-figure",
                        figure=_build_emissions_pathways_fig(),
                        config={"responsive": True, "displayModeBar": True,
                                "modeBarButtonsToRemove": ["lasso2d", "select2d"],
                                "displaylogo": False},
                    ),
                ),
                # Methodology note about scenarios
                dbc.Alert(
                    [
                        html.Strong("About these scenario bands: "),
                        "Shaded regions show the interquartile range (p25–p75, darker) "
                        "and p10–p90 (lighter); dashed lines show the median. "
                        "C1 scenarios require temperature overshoot and 8–10 GtCO₂/yr of "
                        "carbon removal by 2050 — they are NOT 'below 1.5\u00b0C' pathways. "
                        "Current CDR capacity is ~2 GtCO₂/yr. ",
                        "Scenario data from the ",
                        html.A("IIASA AR6 Scenario Explorer v1.1",
                               href="https://data.ece.iiasa.ac.at/ar6/",
                               target="_blank", className="alert-link"),
                        " (",
                        html.A("Byers et al. 2022",
                               href="https://doi.org/10.5281/zenodo.5886911",
                               target="_blank", className="alert-link"),
                        "). See ",
                        html.A("methodology", href="/methodology", className="alert-link"),
                        ".",
                    ],
                    color="secondary",
                    className="small py-2 mt-2",
                ),
            ]),
        ], fluid=False),

        # =====================================================================
        # Section 4: Clean Energy Momentum
        # =====================================================================
        dbc.Container([
            html.Div(className="thematic-section", children=[
                html.H2("Clean Energy Momentum", className="section-heading"),
                html.P(
                    "Renewable capacity, generation, and what share of energy it's actually displacing.",
                    className="section-subheading",
                ),
                # Generation by source (TWh/yr) — clickable, show historical trendlines
                _build_generation_hero_cards(),
                # Renewable share framing note
                dbc.Alert(
                    [
                        html.Strong("Note on 'renewable share': "),
                        "The ~30% renewable share of electricity is in the hero bar above. "
                        "Renewables' share of all final energy consumption is ~13% — "
                        "because electricity is only part of total energy use. Both metrics matter. "
                        "See the methodology page for details.",
                    ],
                    color="info",
                    className="small py-2 mt-2",
                ),
                # Reset button to restore NZE milestones view
                html.Div(
                    dbc.Button(
                        "Show NZE milestones",
                        id="energy-reset-btn",
                        size="sm", outline=True, color="secondary",
                        className="mt-2",
                    ),
                    className="d-flex justify-content-end",
                ),
                html.Div(
                    id="deployment-tracker-chart",
                    className="context-chart-card mt-1",
                    **{"aria-label": "Chart showing global renewable capacity vs IEA Net Zero milestones"},
                    children=dcc.Graph(
                        id="energy-section-figure",
                        figure=_build_deployment_tracker_fig(),
                        config={"responsive": True, "displayModeBar": False},
                    ),
                ),
                dbc.Alert(
                    [
                        html.Strong("Note: "),
                        "IEA NZE milestones shown are approximate values from the published IEA "
                        "Net Zero by 2050 report. On-track/off-track assessment is based on "
                        "recent annual addition pace vs pace needed to reach the 2030 milestone.",
                    ],
                    color="secondary",
                    className="small py-2 mt-2",
                ),
            ]),
        ], fluid=False),

        # =====================================================================
        # Section 5: Investment & Subsidies (merged)
        # =====================================================================
        dbc.Container([
            html.Div(className="thematic-section", children=[
                html.H2("Investment & Subsidies", className="section-heading"),
                html.P(
                    "Where the money is going: clean energy investment has overtaken fossil fuels "
                    "globally, but governments still subsidize fossil fuels at massive scale.",
                    className="section-subheading",
                ),
                # Investment KPI cards (clickable — switch the chart)
                _build_investment_kpi_cards(inv_kpis),
                # Subsidies KPI cards (clickable — switch the chart)
                make_thematic_stats_row(kpis, [
                    "subsidies_global_bn",
                    "subsidies_implicit_tn",
                    "subsidies_top_country",
                ], section_id="investment"),
                # Single switchable chart area
                html.Div(
                    id="investment-chart-container",
                    className="context-chart-card mt-3",
                    **{"aria-label": "Investment and subsidies chart"},
                    children=dcc.Graph(
                        id="investment-section-figure",
                        figure=_build_investment_fig(),
                        config={"responsive": True, "displayModeBar": False},
                    ),
                ),
                dbc.Alert([
                    html.Strong("Sources: "),
                    html.A(
                        "IEA World Energy Investment 2025",
                        href="https://www.iea.org/reports/world-energy-investment-2025",
                        target="_blank", className="alert-link",
                    ),
                    " (investment); ",
                    html.A(
                        "IEA Fossil Fuel Subsidies Database",
                        href="https://www.iea.org/data-and-statistics/data-product/fossil-fuel-subsidies-database",
                        target="_blank", className="alert-link",
                    ),
                    " (explicit subsidies); ",
                    html.A(
                        "IMF 2023",
                        href="https://www.imf.org/en/Topics/climate-change/energy-subsidies",
                        target="_blank", className="alert-link",
                    ),
                    " ($7T/yr including implicit costs). "
                    "All investment in 2024 real USD. ",
                    html.Br(),
                    html.Small(
                        "Note: IEA subsidy data uses the price-gap method (consumer price vs. supply cost), "
                        "covering 48 countries with direct price subsidies. The USA and most OECD nations "
                        "provide fossil fuel support primarily through production-side tax measures, "
                        "which are tracked separately by the OECD and IMF.",
                        className="text-muted",
                    ),
                ], color="secondary", className="small py-2 mt-2"),
            ]),
        ], fluid=False),

        # =====================================================================
        # Section 7: Costs
        # =====================================================================
        dbc.Container([
            html.Div(className="thematic-section", children=[
                html.H2("Costs", className="section-heading"),
                html.P(
                    "The cost revolution: solar and wind are now the cheapest new power sources ever built.",
                    className="section-subheading",
                ),
                dbc.Row([
                    dbc.Col(
                        dbc.Card(dbc.CardBody([
                            html.Div([
                                html.I(className="bi bi-sun-fill me-1 text-warning small"),
                                html.Small("Solar LCOE", className="text-muted"),
                            ], className="d-flex align-items-center"),
                            html.Div("$48/MWh", className="fs-3 fw-bold mt-1"),
                            html.Small("2023 \u2014 down 90% since 2010 (2025 USD)", className="text-muted"),
                            html.Div(html.A(
                                "IRENA 2023",
                                href="https://www.irena.org/publications/2024/Sep/Renewable-Power-Generation-Costs-in-2023",
                                target="_blank", style={"fontSize": "0.7rem", "textDecoration": "none"},
                                className="text-muted",
                            ), className="mt-1"),
                        ], className="py-2 px-3"), className="h-100",
                            style={"borderStyle": "dashed", "borderColor": "#dee2e6"}),
                        xs=12, sm=6, md=3, className="mb-3",
                    ),
                    dbc.Col(
                        dbc.Card(dbc.CardBody([
                            html.Div([
                                html.I(className="bi bi-wind me-1 text-success small"),
                                html.Small("Onshore wind LCOE", className="text-muted"),
                            ], className="d-flex align-items-center"),
                            html.Div("$36/MWh", className="fs-3 fw-bold mt-1"),
                            html.Small("2023 \u2014 70% decline since 2010 (2025 USD)", className="text-muted"),
                            html.Div(html.A(
                                "IRENA 2023",
                                href="https://www.irena.org/publications/2024/Sep/Renewable-Power-Generation-Costs-in-2023",
                                target="_blank", style={"fontSize": "0.7rem", "textDecoration": "none"},
                                className="text-muted",
                            ), className="mt-1"),
                        ], className="py-2 px-3"), className="h-100",
                            style={"borderStyle": "dashed", "borderColor": "#dee2e6"}),
                        xs=12, sm=6, md=3, className="mb-3",
                    ),
                    dbc.Col(
                        dbc.Card(dbc.CardBody([
                            html.Div([
                                html.I(className="bi bi-gem me-1 text-secondary small"),
                                html.Small("New coal LCOE", className="text-muted"),
                            ], className="d-flex align-items-center"),
                            html.Div("$121/MWh", className="fs-3 fw-bold mt-1"),
                            html.Small("2023 \u2014 2.5\u00d7 more expensive than solar (2025 USD)", className="text-muted"),
                            html.Div(html.A(
                                "IEA / IRENA 2023",
                                href="https://www.irena.org/publications/2024/Sep/Renewable-Power-Generation-Costs-in-2023",
                                target="_blank", style={"fontSize": "0.7rem", "textDecoration": "none"},
                                className="text-muted",
                            ), className="mt-1"),
                        ], className="py-2 px-3"), className="h-100",
                            style={"borderStyle": "dashed", "borderColor": "#dee2e6"}),
                        xs=12, sm=6, md=3, className="mb-3",
                    ),
                    dbc.Col(
                        dbc.Card(dbc.CardBody([
                            html.Div([
                                html.I(className="bi bi-fire me-1 text-secondary small"),
                                html.Small("Gas CCGT LCOE", className="text-muted"),
                            ], className="d-flex align-items-center"),
                            html.Div("$76/MWh", className="fs-3 fw-bold mt-1"),
                            html.Small("2023 \u2014 approx. (IEA/IRENA, 2025 USD)", className="text-muted"),
                            html.Div(html.A(
                                "IEA 2020",
                                href="https://www.iea.org/reports/projected-costs-of-generating-electricity-2020",
                                target="_blank", style={"fontSize": "0.7rem", "textDecoration": "none"},
                                className="text-muted",
                            ), className="mt-1"),
                        ], className="py-2 px-3"), className="h-100",
                            style={"borderStyle": "dashed", "borderColor": "#dee2e6"}),
                        xs=12, sm=6, md=3, className="mb-3",
                    ),
                    dbc.Col(
                        dbc.Card(dbc.CardBody([
                            html.Div([
                                html.I(className="bi bi-radioactive me-1 text-purple small"),
                                html.Small("Nuclear LCOE", className="text-muted"),
                            ], className="d-flex align-items-center"),
                            html.Div("$190/MWh", className="fs-3 fw-bold mt-1"),
                            html.Small("2023 \u2014 new build (Lazard v16, 2025 USD)", className="text-muted"),
                            html.Div(html.A(
                                "Lazard v16 2023",
                                href="https://www.lazard.com/research-insights/levelized-cost-of-energyplus-lcoeplus/",
                                target="_blank", style={"fontSize": "0.7rem", "textDecoration": "none"},
                                className="text-muted",
                            ), className="mt-1"),
                        ], className="py-2 px-3"), className="h-100",
                            style={"borderStyle": "dashed", "borderColor": "#dee2e6"}),
                        xs=12, sm=6, md=3, className="mb-3",
                    ),
                ], className="g-3"),
                html.Div(
                    id="cost-revolution-chart",
                    className="context-chart-card mt-3",
                    **{"aria-label": "Chart showing LCOE cost declines for solar, wind, and battery storage since 2010"},
                    children=dcc.Graph(
                        id="cost-revolution-figure",
                        figure=_build_cost_revolution_fig(),
                        config={
                            "responsive": True,
                            "displayModeBar": True,
                            "displaylogo": False,
                            "modeBarButtonsToRemove": [
                                "lasso2d", "select2d", "pan2d",
                                "zoomIn2d", "zoomOut2d",
                            ],
                        },
                    ),
                ),
                dbc.Alert([
                    html.Strong("Note on LCOE: "),
                    "Levelized Cost of Energy (LCOE) is a global capacity-weighted average for ",
                    html.Em("new"),
                    " installations \u2014 it does not reflect the full system cost (grid integration, "
                    "backup, storage). Battery cost is pack cost in $/kWh (different unit, shown "
                    "on same log axis). Gas CCGT values are approximate (see note in chart title) "
                    "\u2014 gas LCOE is highly region-dependent due to fuel price variability. "
                    "All values in 2025 USD (adjusted from source dollar-years using CPI-U). "
                    "Sources: IRENA RPGC 2023 (solar/wind); IEA Projected Costs 2020 (coal/gas); BloombergNEF (battery).",
                ], color="secondary", className="small py-2 mt-2"),
            ]),
        ], fluid=False),

        # =====================================================================
        # Section 8: Predictions vs Reality
        # =====================================================================
        dbc.Container([
            html.Div(className="thematic-section", children=[
                html.H2("Predictions vs Reality", className="section-heading"),
                html.P(
                    "Official energy forecasts have systematically underestimated clean energy "
                    "and overestimated fossil fuel technologies like CCS.",
                    className="section-subheading",
                ),
                make_thematic_stats_row(kpis, [
                    "predictions_solar_ratio",
                    "predictions_wind_ratio",
                    "predictions_ccs_shortfall",
                ], section_id="predictions"),
                # Technology toggle buttons
                html.Div(
                    className="d-flex gap-2 mt-2 mb-2",
                    children=[
                        dbc.Button(
                            "Solar PV", id="home-pred-btn-solar", n_clicks=0,
                            color="warning", outline=True, size="sm",
                        ),
                        dbc.Button(
                            "Wind", id="home-pred-btn-wind", n_clicks=0,
                            color="success", outline=True, size="sm",
                        ),
                        dbc.Button(
                            "CCS", id="home-pred-btn-ccs", n_clicks=0,
                            color="danger", outline=True, size="sm",
                        ),
                    ],
                ),
                html.Div(
                    id="predictions-chart-container",
                    className="context-chart-card mt-1",
                    **{"aria-label": "Predictions vs reality chart"},
                    children=dcc.Graph(
                        id="predictions-section-figure",
                        figure=_build_predictions_fan_fig("solar"),
                        config={"responsive": True, "displayModeBar": True,
                                "modeBarButtonsToRemove": ["lasso2d", "select2d"],
                                "displaylogo": False},
                    ),
                ),
                dbc.Alert([
                    html.Strong("How to read: "),
                    "Each dotted line is one IEA WEO edition's projection "
                    "(older = red, newer = blue). Dashed lines = independent forecasters "
                    "(RMI, Seba, RethinkX). Thick black = actual. "
                    "Toggle traces in the legend.",
                ], color="secondary", className="small py-2 mt-2"),
            ]),
        ], fluid=False),

        # =====================================================================
        # Section 9: Health
        # =====================================================================
        dbc.Container([
            html.Div(className="thematic-section", children=[
                html.H2("Health", className="section-heading"),
                html.P(
                    "Fossil fuels impose enormous health costs \u2014 from air pollution deaths "
                    "to heat-related mortality from climate change.",
                    className="section-subheading",
                ),
                make_thematic_stats_row(kpis, [
                    "health_deaths_fossil_pm25",
                    "health_heat_deaths",
                    "health_disaster_deaths",
                    "health_cumulative_climate_deaths",
                ], section_id="health"),
                html.Div(
                    id="health-chart-container",
                    className="context-chart-card mt-3",
                    **{"aria-label": "Health impact chart"},
                    children=dcc.Graph(
                        id="health-section-figure",
                        figure=_build_health_mortality_fig(),
                        config={"responsive": True, "displayModeBar": False},
                    ),
                ),
                dbc.Alert([
                    html.Strong("What the chart shows: "),
                    html.Ul([
                        html.Li([
                            html.Strong("Fossil fuel PM2.5 (red): "),
                            "Derived as ~33% of GBD annual ambient PM2.5 deaths "
                            "(McDuffie et al. 2021 fossil fraction applied to GBD time series). "
                            "This is an approximation \u2014 the true fraction may vary year-to-year. "
                            "Hero bar shows the full range across methods: 1.3\u20138.7M/yr.",
                        ]),
                        html.Li([
                            html.Strong("Climate-attributable heat (orange): "),
                            "~200K/yr. Total heat deaths ~546K/yr (Lancet Countdown 2025); "
                            "37% attributable to anthropogenic warming (",
                            html.A("Vicedo-Cabrera et al. 2021",
                                   href="https://doi.org/10.1038/s41558-021-01058-x",
                                   target="_blank", className="alert-link"),
                            "). This is a widely-cited counterfactual approach.",
                        ]),
                        html.Li([
                            html.Strong("Weather/climate disasters (blue): "),
                            "~75K/yr avg (EM-DAT). Floods, storms, droughts, wildfires. "
                            "Highly variable. Not all individually attributable to climate.",
                        ]),
                        html.Li([
                            html.Strong("Total (black): "),
                            "Sum of above three lines. Uses conservative PM2.5 estimate.",
                        ]),
                    ], className="mb-0 ps-3 mt-1"),
                    html.A("See methodology", href="/methodology", className="alert-link mt-1"),
                ], color="secondary", className="small py-2 mt-2"),
                html.Div(
                    dbc.Button("Explore health data by country \u2192", href="/country/USA",
                               color="primary", size="sm", outline=True),
                    className="mt-2",
                ),
            ]),
        ], fluid=False),

        # =====================================================================
        # Footer
        # =====================================================================
        html.Footer(
            dbc.Container([
                dbc.Row([
                    dbc.Col([
                        html.Strong("Energy Transition Dashboard"),
                        html.Br(),
                        html.Small(
                            "Data from OWID, Ember, EDGAR, GCB, IRENA, "
                            "IEA, GBD/IHME, and others. See ",
                            className="text-muted",
                        ),
                        html.A("methodology", href="/methodology",
                               className="text-muted"),
                        html.Small(" for sources, definitions, and caveats.", className="text-muted"),
                    ], md=8),
                    dbc.Col([
                        html.Small("Data is refreshed monthly.", className="text-muted"),
                    ], md=4, className="text-md-end"),
                ]),
            ]),
            className="dashboard-footer",
        ),

    ])  # end main Div


# =========================================================================
# Callback functions — registered in app.py via app.callback()
# (Dash 4.x Pages `dash.callback` does not auto-register; must use app.callback)
# =========================================================================

EMISSIONS_SECTION_KEYS = [
    "co2_fossil_gt", "ghg_total_gtco2e", "atmospheric_co2_ppm", "temperature_anomaly_c",
]

ENERGY_SECTION_KEYS = []  # GW cards removed; generation cards use direct IDs

INVESTMENT_SECTION_KEYS = [
    "subsidies_global_bn", "subsidies_implicit_tn", "subsidies_top_country",
]

PREDICTIONS_SECTION_KEYS = [
    "predictions_solar_ratio", "predictions_wind_ratio", "predictions_ccs_shortfall",
]

HEALTH_SECTION_KEYS = [
    "health_deaths_fossil_pm25", "health_heat_deaths",
    "health_disaster_deaths", "health_cumulative_climate_deaths",
]


def toggle_hero_modal(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open


def switch_emissions_chart(*args):
    """Switch the Emissions section chart based on which KPI card was clicked."""
    triggered_id = ctx.triggered_id or ""

    # Reset button restores the default emissions vs pathways chart
    if "emissions-reset-btn" in str(triggered_id):
        return _build_emissions_pathways_fig()

    _std_layout = dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#ffffff",
        font=dict(family="Inter, Helvetica Neue, Arial, sans-serif", size=12),
        margin=dict(l=60, r=24, t=40, b=50), height=400, hovermode="x unified",
        xaxis=dict(showgrid=True, gridcolor="#f0f0f0", tickformat="d"),
        yaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
    )

    if "co2_fossil_gt" in triggered_id:
        df = get_emissions()
        if not df.empty:
            yearly = df.groupby("year")["co2_fossil_mt"].sum().reset_index()
            yearly["gt"] = yearly["co2_fossil_mt"] / 1000
            yearly = yearly.sort_values("year")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=yearly["year"], y=yearly["gt"],
                mode="lines+markers", line=dict(color="#d32f2f", width=2.5),
                marker=dict(size=4), name="Fossil CO₂",
                hovertemplate="<b>%{x}</b>: %{y:.1f} GtCO₂<extra></extra>",
            ))
            fig.update_layout(title=dict(text="Global Fossil CO₂ Emissions", font=dict(size=14)),
                              yaxis_title="GtCO₂/yr", **_std_layout)
            return fig

    elif "ghg_total_gtco2e" in triggered_id:
        df = get_emissions()
        if not df.empty:
            yearly = df.groupby("year")["ghg_total_mtco2e"].sum().reset_index()
            yearly["gt"] = yearly["ghg_total_mtco2e"] / 1000
            yearly = yearly.sort_values("year")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=yearly["year"], y=yearly["gt"],
                mode="lines+markers", line=dict(color="#e65100", width=2.5),
                marker=dict(size=4), name="Total GHGs",
                hovertemplate="<b>%{x}</b>: %{y:.1f} GtCO₂e<extra></extra>",
            ))
            fig.update_layout(title=dict(text="Total Greenhouse Gas Emissions", font=dict(size=14)),
                              yaxis_title="GtCO₂e/yr", **_std_layout)
            return fig

    elif "atmospheric_co2_ppm" in triggered_id:
        from pathlib import Path
        noaa_path = Path("data/raw/noaa_co2_global_mean.csv")
        if noaa_path.exists():
            try:
                ndf = pd.read_csv(noaa_path, comment="#", sep=r"\s+",
                                  header=None, names=["year", "mean", "unc"])
                ndf = ndf[ndf["mean"].notna()].sort_values("year")
                if not ndf.empty:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=ndf["year"], y=ndf["mean"],
                        mode="lines", line=dict(color="#1565c0", width=2.5),
                        name="CO₂ concentration",
                        hovertemplate="<b>%{x}</b>: %{y:.1f} ppm<extra></extra>",
                    ))
                    fig.update_layout(title=dict(text="Atmospheric CO₂ (NOAA)", font=dict(size=14)),
                                      yaxis_title="ppm", **_std_layout)
                    return fig
            except Exception:
                pass

    elif "temperature_anomaly_c" in triggered_id:
        return _build_hero_trendline("current_policies_warming_c")

    # Default: show the emissions vs pathways chart
    return _build_emissions_pathways_fig()


def switch_energy_chart(*args):
    """Switch the Clean Energy section chart based on generation card or reset button."""
    triggered_id = str(ctx.triggered_id or "")

    # Reset button restores the default deployment tracker with NZE milestones
    if "energy-reset-btn" in triggered_id:
        return _build_deployment_tracker_fig()

    _std_layout = dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#ffffff",
        font=dict(family="Inter, Helvetica Neue, Arial, sans-serif", size=12),
        margin=dict(l=60, r=24, t=40, b=50), height=400, hovermode="x unified",
        xaxis=dict(showgrid=True, gridcolor="#f0f0f0", tickformat="d"),
        yaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
    )

    # Map generation card IDs to data columns and display settings
    gen_map = {
        "energy-gen-solar": ("electricity_twh_solar", "Solar Generation", "#ff9800"),
        "energy-gen-wind":  ("electricity_twh_wind",  "Wind Generation",  "#2e7d32"),
        "energy-gen-hydro": ("electricity_twh_hydro", "Hydro Generation", "#1565c0"),
        "energy-gen-gas":   ("electricity_twh_gas",   "Gas Generation",   "#795548"),
        "energy-gen-coal":    ("electricity_twh_coal",    "Coal Generation",    "#6c757d"),
        "energy-gen-nuclear": ("electricity_twh_nuclear", "Nuclear Generation", "#9b59b6"),
    }

    for card_id, (col, label, color) in gen_map.items():
        if card_id in triggered_id:
            em = get_energy_mix()
            if em.empty or col not in em.columns:
                break
            yearly = em.groupby("year")[col].sum().reset_index()
            yearly = yearly[yearly[col] > 0].sort_values("year")
            # Drop incomplete latest years (if value drops >30% from prior)
            while len(yearly) >= 2:
                if yearly.iloc[-1][col] < yearly.iloc[-2][col] * 0.7:
                    yearly = yearly.iloc[:-1]
                else:
                    break
            if yearly.empty:
                break
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=yearly["year"], y=yearly[col],
                mode="lines+markers", line=dict(color=color, width=2.5),
                marker=dict(size=4), name=label,
                hovertemplate=f"<b>%{{x}}</b>: %{{y:,.0f}} TWh<extra></extra>",
            ))
            fig.update_layout(
                title=dict(text=f"Global {label} (TWh/yr)", font=dict(size=14)),
                yaxis_title="TWh/yr", **_std_layout,
            )
            return fig

    # Default: deployment tracker
    return _build_deployment_tracker_fig()


def switch_investment_chart(*args):
    """Switch the Investment & Subsidies section chart based on KPI card click."""
    triggered_id = str(ctx.triggered_id or "")

    if "subsidies_top_country" in triggered_id:
        return _build_subsidies_countries_fig()
    elif "subsidies_global_bn" in triggered_id or "inv-card-subsidies-overview" in triggered_id:
        return _build_subsidies_time_fig()
    elif "subsidies_implicit_tn" in triggered_id:
        # IMF implicit subsidies time series (published estimates, not annual)
        # IMF Working Papers: Coady et al. 2015 ($5.3T for 2015), 2019 ($5.2T for 2017),
        # Black et al. 2023 ($7.0T for 2022). Includes unpriced externalities.
        imf_years = [2015, 2017, 2022]
        imf_vals = [5.3, 5.2, 7.0]
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=imf_years, y=imf_vals,
            mode="lines+markers", line=dict(color="#d32f2f", width=2.5),
            marker=dict(size=8), name="IMF total subsidies (incl. implicit)",
            hovertemplate="<b>%{x}</b>: $%{y:.1f}T/yr<extra></extra>",
        ))
        fig.add_annotation(
            xref="paper", yref="paper", x=0.02, y=0.98,
            text=(
                "<b>Includes:</b> explicit subsidies + unpriced externalities<br>"
                "(air pollution health costs, climate damage, forgone<br>"
                "consumption taxes). Source: IMF Working Papers."
            ),
            showarrow=False, font=dict(size=9, color="#6c757d"),
            bgcolor="rgba(255,255,255,0.90)", borderpad=4, align="left",
        )
        fig.update_layout(
            title=dict(text="IMF Total Fossil Fuel Subsidies (explicit + implicit)", font=dict(size=14)),
            yaxis_title="$T/yr", height=400,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#ffffff",
            font=dict(family="Inter, Helvetica Neue, Arial, sans-serif", size=12),
            margin=dict(l=60, r=24, t=40, b=50), hovermode="x unified",
            xaxis=dict(showgrid=True, gridcolor="#f0f0f0", tickformat="d"),
            yaxis=dict(showgrid=True, gridcolor="#f0f0f0", rangemode="tozero"),
        )
        return fig
    elif "inv-card-fossil" in triggered_id:
        # Show fossil investment time series
        inv = get_investment()
        if not inv.empty:
            world = inv[inv["region"] == "World"].sort_values("year")
            if "fossil_fuel_investment_bn" in world.columns:
                world = world[world["fossil_fuel_investment_bn"].notna()]
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=world["year"], y=world["fossil_fuel_investment_bn"],
                    mode="lines+markers", line=dict(color="#795548", width=2.5),
                    marker=dict(size=5), name="Fossil fuel investment",
                    hovertemplate="<b>%{x}</b>: $%{y:.0f}B<extra></extra>",
                ))
                fig.update_layout(
                    title=dict(text="Global Fossil Fuel Investment", font=dict(size=14)),
                    yaxis_title="$B/yr", height=400,
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#ffffff",
                    font=dict(family="Inter, Helvetica Neue, Arial, sans-serif", size=12),
                    margin=dict(l=60, r=24, t=40, b=50), hovermode="x unified",
                    xaxis=dict(showgrid=True, gridcolor="#f0f0f0", tickformat="d"),
                    yaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
                )
                return fig
    elif "inv-card-share" in triggered_id:
        # Show clean share percentage over time
        inv = get_investment()
        if not inv.empty:
            world = inv[inv["region"] == "World"].sort_values("year")
            if "clean_energy_investment_bn" in world.columns and "fossil_fuel_investment_bn" in world.columns:
                world = world.dropna(subset=["clean_energy_investment_bn", "fossil_fuel_investment_bn"])
                world["share"] = (world["clean_energy_investment_bn"]
                                  / (world["clean_energy_investment_bn"] + world["fossil_fuel_investment_bn"])
                                  * 100)
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=world["year"], y=world["share"],
                    mode="lines+markers", line=dict(color="#1565c0", width=2.5),
                    marker=dict(size=5), name="Clean energy share",
                    hovertemplate="<b>%{x}</b>: %{y:.1f}%<extra></extra>",
                ))
                fig.add_hline(y=50, line_dash="dash", line_color="#aaa",
                              annotation_text="50% crossover", annotation_position="top left")
                fig.update_layout(
                    title=dict(text="Clean Energy Share of Total Energy Investment", font=dict(size=14)),
                    yaxis_title="% of total", height=400,
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#ffffff",
                    font=dict(family="Inter, Helvetica Neue, Arial, sans-serif", size=12),
                    margin=dict(l=60, r=24, t=40, b=50), hovermode="x unified",
                    xaxis=dict(showgrid=True, gridcolor="#f0f0f0", tickformat="d"),
                    yaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
                )
                return fig
    elif "inv-card-regional" in triggered_id:
        return _build_regional_investment_fig()
    elif "inv-card-clean" in triggered_id:
        # Show clean investment time series
        inv = get_investment()
        if not inv.empty:
            world = inv[inv["region"] == "World"].sort_values("year")
            if "clean_energy_investment_bn" in world.columns:
                world = world[world["clean_energy_investment_bn"].notna()]
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=world["year"], y=world["clean_energy_investment_bn"],
                    mode="lines+markers", line=dict(color="#2ea44f", width=2.5),
                    marker=dict(size=5), name="Clean energy investment",
                    hovertemplate="<b>%{x}</b>: $%{y:.0f}B<extra></extra>",
                ))
                fig.update_layout(
                    title=dict(text="Global Clean Energy Investment", font=dict(size=14)),
                    yaxis_title="$B/yr", height=400,
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#ffffff",
                    font=dict(family="Inter, Helvetica Neue, Arial, sans-serif", size=12),
                    margin=dict(l=60, r=24, t=40, b=50), hovermode="x unified",
                    xaxis=dict(showgrid=True, gridcolor="#f0f0f0", tickformat="d"),
                    yaxis=dict(showgrid=True, gridcolor="#f0f0f0"),
                )
                return fig
    # Default: investment overview (clean vs fossil)
    return _build_investment_fig()


def switch_predictions_chart(*args):
    """Switch the Predictions section chart based on KPI card or toggle button click."""
    triggered_id = str(ctx.triggered_id or "")

    if "predictions_wind_ratio" in triggered_id or "pred-btn-wind" in triggered_id:
        return _build_predictions_fan_fig("wind")
    elif "predictions_ccs_shortfall" in triggered_id or "pred-btn-ccs" in triggered_id:
        return _build_predictions_fan_fig("ccs")
    return _build_predictions_fan_fig("solar")


def switch_health_chart(*args):
    """Switch the Health section chart based on which KPI card was clicked."""
    triggered_id = str(ctx.triggered_id or "")

    if "health_heat_deaths" in triggered_id:
        return _build_health_heat_fig()
    elif "health_disaster_deaths" in triggered_id:
        # Show disaster deaths time series only
        try:
            cd = get_climate_disasters()
            if not cd.empty and "total_deaths" in cd.columns:
                dd = cd.groupby("year")["total_deaths"].sum().reset_index()
                dd = dd[dd["year"] >= 2000].sort_values("year")
                dd = dd[dd["year"] <= 2024]
                dd["deaths_k"] = dd["total_deaths"] / 1000.0
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=dd["year"], y=dd["deaths_k"],
                    mode="lines+markers", line=dict(color="#1565c0", width=2.5),
                    marker=dict(size=4),
                    name="Weather/climate disaster deaths",
                    hovertemplate="<b>%{x}</b>: %{y:,.0f}K deaths<extra></extra>",
                ))
                fig.update_layout(
                    title=dict(text="Weather/Climate-Related Disaster Deaths (EM-DAT)", font=dict(size=14)),
                    yaxis_title="Thousand deaths/yr", height=380,
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#ffffff",
                    font=dict(family="Inter, Helvetica Neue, Arial, sans-serif", size=12),
                    margin=dict(l=60, r=24, t=40, b=50), hovermode="x unified",
                    xaxis=dict(showgrid=True, gridcolor="#f0f0f0", tickformat="d"),
                    yaxis=dict(showgrid=True, gridcolor="#f0f0f0", rangemode="tozero"),
                )
                return fig
        except Exception:
            pass
    # PM2.5, cumulative total, or default: show the full 4-line chart
    return _build_health_mortality_fig()
