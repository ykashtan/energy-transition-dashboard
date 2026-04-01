"""
stat.py — Historical trend page for a single KPI statistic.

Dynamic route: /stat/<key>
  e.g., /stat/atmospheric_co2_ppm, /stat/carbon_intensity_gco2_kwh

Shows the KPI value over time (global), with source citation and context.
Linked from the hero stats row on the homepage.
"""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd

from utils.data_loader import (
    get_kpis, get_emissions, get_energy_mix, get_health, get_finance,
)

dash.register_page(
    __name__,
    path_template="/stat/<key>",
    title="Statistic Detail — Energy Transition Dashboard",
)

_GRAPH_CONFIG = {"responsive": True, "displayModeBar": True, "displaylogo": False}

# Map KPI keys to data extraction functions
# Each returns (years, values, y_label, source_text, source_url)
def _get_series(key: str):
    """Return a time series for a KPI key."""

    if key == "atmospheric_co2_ppm":
        # NOAA raw CSV is whitespace-delimited: year, mean, unc (no header row)
        from pathlib import Path
        noaa_path = Path("data/raw/noaa_co2_global_mean.csv")
        if noaa_path.exists():
            try:
                df = pd.read_csv(
                    noaa_path, comment="#", sep=r"\s+",
                    header=None, names=["year", "mean", "unc"],
                )
                df = df[df["mean"].notna()].sort_values("year")
                if not df.empty:
                    return df["year"], df["mean"], "ppm", "NOAA Global Mean CO₂", "https://gml.noaa.gov/ccgg/trends/gl_trend.html"
            except Exception:
                pass
        return None, None, "ppm", "", ""

    if key == "co2_fossil_gt":
        df = get_emissions()
        if df.empty:
            return None, None, "", "", ""
        global_co2 = df.groupby("year")["co2_fossil_mt"].sum().reset_index()
        global_co2["gt"] = global_co2["co2_fossil_mt"] / 1000
        global_co2 = global_co2.sort_values("year")
        return global_co2["year"], global_co2["gt"], "GtCO₂/yr", "OWID (GCB)", "https://github.com/owid/co2-data"

    if key == "ghg_total_gtco2e":
        df = get_emissions()
        if df.empty:
            return None, None, "", "", ""
        global_ghg = df.groupby("year")["ghg_total_mtco2e"].sum().reset_index()
        global_ghg["gt"] = global_ghg["ghg_total_mtco2e"] / 1000
        global_ghg = global_ghg.sort_values("year")
        return global_ghg["year"], global_ghg["gt"], "GtCO₂e/yr", "OWID (EDGAR/GCB)", "https://github.com/owid/co2-data"

    if key == "renewable_share_electricity_pct":
        df = get_energy_mix()
        if df.empty:
            return None, None, "", "", ""
        # Global average weighted by generation
        yearly = df.groupby("year").agg(
            total_re=("total_electricity_twh", lambda x: (
                df.loc[x.index, "renewable_share_electricity_pct"].fillna(0) / 100
                * df.loc[x.index, "total_electricity_twh"].fillna(0)
            ).sum()),
            total_gen=("total_electricity_twh", "sum"),
        ).reset_index()
        yearly["pct"] = yearly["total_re"] / yearly["total_gen"] * 100
        yearly = yearly[yearly["total_gen"] > 0].sort_values("year")
        return yearly["year"], yearly["pct"], "% of electricity", "OWID (Ember/IRENA)", "https://github.com/owid/energy-data"

    if key == "carbon_intensity_gco2_kwh":
        df = get_energy_mix()
        if df.empty:
            return None, None, "", "", ""
        # Global weighted average
        yearly = df.groupby("year").agg(
            total_co2_kwh=("carbon_intensity_gco2_kwh", lambda x: (
                df.loc[x.index, "carbon_intensity_gco2_kwh"].fillna(0)
                * df.loc[x.index, "total_electricity_twh"].fillna(0)
            ).sum()),
            total_gen=("total_electricity_twh", "sum"),
        ).reset_index()
        yearly["gco2"] = yearly["total_co2_kwh"] / yearly["total_gen"]
        yearly = yearly[yearly["total_gen"] > 0].sort_values("year")
        return yearly["year"], yearly["gco2"], "gCO₂/kWh", "OWID (Ember)", "https://github.com/owid/energy-data"

    if key == "clean_energy_investment_t":
        df = get_finance()
        if df.empty:
            return None, None, "", "", ""
        world = df[df["iso3"] == "WORLD"].sort_values("year")
        if "clean_investment_usd_b" in world.columns:
            series = world["clean_investment_usd_b"].dropna()
            years = world.loc[series.index, "year"]
            return years, series / 1000, "$T/yr", "IEA World Energy Investment", "https://www.iea.org/reports/world-energy-investment-2024"
        return None, None, "", "", ""

    if key == "deaths_fossil_fuel_m":
        # Vohra et al. / Lelieveld et al. are single-year estimates. No public time series.
        return None, None, "", "", ""

    if key == "deaths_ambient_pm25_m":
        # GBD 2023 has country-level data 1990-2023. Aggregate to global total.
        df = get_health()
        if df.empty or "deaths_ambient_pm25" not in df.columns:
            return None, None, "", "", ""
        has_data = df["deaths_ambient_pm25"].notna()
        if not has_data.any():
            return None, None, "", "", ""
        yearly = df[has_data].groupby("year")["deaths_ambient_pm25"].sum().reset_index()
        yearly = yearly.sort_values("year")
        # deaths_ambient_pm25 is in thousands; convert to millions for display
        return (
            yearly["year"], yearly["deaths_ambient_pm25"] / 1000,
            "Million deaths/yr (all outdoor PM2.5)",
            "IHME Global Burden of Disease 2023",
            "https://vizhub.healthdata.org/gbd-results/",
        )

    if key == "temperature_anomaly_c":
        # Prefer HadCRUT5 if available (1850-present, official observational record)
        from pathlib import Path
        hadcrut_path = Path("data/raw/hadcrut5_global_annual.csv")
        if hadcrut_path.exists():
            try:
                df = pd.read_csv(hadcrut_path)
                df = df.rename(columns={df.columns[0]: "year", df.columns[1]: "anomaly"})
                df = df[df["anomaly"].notna()].sort_values("year")
                if not df.empty:
                    return (
                        df["year"], df["anomaly"],
                        "°C above 1850–1900",
                        "HadCRUT5 (Met Office / University of East Anglia)",
                        "https://www.metoffice.gov.uk/hadobs/hadcrut5/",
                    )
            except Exception:
                pass
        # Fallback: OWID
        owid_path = Path("data/raw/owid_co2.csv")
        if owid_path.exists():
            try:
                df = pd.read_csv(owid_path, usecols=["country", "year", "temperature_change_from_ghg"])
                world = df[df["country"] == "World"].dropna(subset=["temperature_change_from_ghg"])
                world = world.sort_values("year")
                if not world.empty:
                    return (
                        world["year"], world["temperature_change_from_ghg"],
                        "°C above pre-industrial",
                        "OWID (derived from Jones et al. 2023, ESSD)",
                        "https://github.com/owid/co2-data",
                    )
            except Exception:
                pass
        return None, None, "", "", ""

    if key == "current_policies_warming_c":
        # Show HadCRUT5 historical temperature anomaly as context for the projection
        from pathlib import Path
        hadcrut_path = Path("data/raw/hadcrut5_global_annual.csv")
        if hadcrut_path.exists():
            try:
                df = pd.read_csv(hadcrut_path)
                df = df.rename(columns={df.columns[0]: "year", df.columns[1]: "anomaly"})
                df = df[df["anomaly"].notna()].sort_values("year")
                if not df.empty:
                    return (
                        df["year"], df["anomaly"],
                        "°C above 1850–1900",
                        "HadCRUT5 (Met Office / University of East Anglia)",
                        "https://www.metoffice.gov.uk/hadobs/hadcrut5/",
                    )
            except Exception:
                pass
        return None, None, "", "", ""

    return None, None, "", "", ""


def layout(key: str = "atmospheric_co2_ppm", **kwargs):
    kpis = get_kpis()
    kpi = kpis.get(key, {})

    if not kpi:
        return html.Div([
            dbc.Container([
                dbc.Button([html.I(className="bi bi-arrow-left me-2"), "Back"],
                           href="/", color="outline-secondary", size="sm", className="mt-3 mb-3"),
                html.H2(f"Statistic not found: {key}", className="text-danger"),
            ]),
        ])

    label = kpi.get("label", key)
    value = kpi.get("value")
    unit = kpi.get("unit", "")
    year = kpi.get("year")
    source = kpi.get("source", "")
    source_url = kpi.get("source_url", "")
    note = kpi.get("note", "")

    # Get time series
    years, values, y_label, series_source, series_url = _get_series(key)

    # Build chart
    fig = go.Figure()
    has_chart = years is not None and values is not None and len(years) > 0

    if has_chart:
        fig.add_trace(go.Scatter(
            x=years, y=values,
            mode="lines+markers",
            line=dict(color="#1565c0", width=3),
            marker=dict(size=4),
            hovertemplate=f"<b>%{{x}}</b>: %{{y:,.2f}} {y_label}<extra></extra>",
            name=label,
        ))

        # Add current value annotation
        if value is not None and year is not None:
            fig.add_annotation(
                x=year, y=value if y_label == unit else None,
                text=f"<b>{value:,.2f} {unit}</b> ({year})",
                showarrow=True, arrowhead=2, arrowcolor="#1565c0",
                ax=-80, ay=-40,
                font=dict(size=11, color="#1565c0"),
                bgcolor="rgba(255,255,255,0.92)",
                bordercolor="#1565c0", borderpad=4,
            )

        fig.update_layout(
            title=dict(text=f"{label} — Historical Trend", font=dict(size=15), x=0),
            xaxis=dict(title="Year", tickformat="d", showgrid=True, gridcolor="#f0f0f0"),
            yaxis=dict(title=y_label, showgrid=True, gridcolor="#f0f0f0"),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#ffffff",
            font=dict(family="Inter, Helvetica Neue, Arial, sans-serif", size=12),
            margin=dict(l=60, r=24, t=54, b=50),
            height=420, hovermode="x unified",
        )

    return html.Div([
        dbc.Container([
            dbc.Button([html.I(className="bi bi-arrow-left me-2"), "Back to dashboard"],
                       href="/", color="outline-secondary", size="sm", className="mt-3 mb-3"),

            # Header
            html.H1(label, className="display-6 fw-bold mb-1"),
            html.Div([
                html.Span(f"{value:,.2f} {unit}" if isinstance(value, float) else f"{value:,} {unit}",
                          className="fs-2 fw-bold text-primary me-3") if value else None,
                html.Span(f"({year})", className="fs-5 text-muted") if year else None,
            ], className="mb-2"),

            # Note
            html.P(note, className="text-muted mb-3") if note else None,

            # Chart
            html.Div(
                dcc.Graph(figure=fig, config=_GRAPH_CONFIG),
                className="context-chart-card mb-3",
            ) if has_chart else dbc.Alert(
                "Historical time series not available for this metric. "
                "See the source link below for the original data.",
                color="info", className="mb-3",
            ),

            # Source citation
            html.Div([
                html.Strong("Source: "),
                html.A(series_source or source,
                       href=series_url or source_url,
                       target="_blank") if (series_url or source_url) else html.Span(series_source or source),
            ], className="small text-muted mb-2"),

            # Methodology link
            html.Div(
                html.A("See full methodology and data sources →",
                       href="/methodology", className="small"),
                className="mb-5",
            ),

        ], fluid=False),
    ])
