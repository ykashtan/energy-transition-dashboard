"""
compare.py -- Country Comparison page for the Energy Transition Dashboard.

Route: /compare
  Optional URL params: /compare?c1=USA&c2=CHN&c3=IND&c4=DEU

Allows side-by-side comparison of 2-4 countries across:
  - CO2 emissions trajectory
  - Renewable electricity share
  - Electricity mix breakdown
  - CO2 per capita
  - Fossil fuel PM2.5 deaths per 100k
  - Clean energy investment (regional, if available)
  - Climate vulnerability (ND-GAIN score)

Design principles:
  - Chart functions are defined locally (not imported from country_charts).
  - Figures are built on-demand based on user selection.
  - Graceful handling when a country lacks data for a metric.
  - Consistent color palette: 4 distinct country colors.
"""

import dash
from dash import html, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import urllib.parse

from utils.data_loader import (
    get_country_meta,
    get_emissions,
    get_energy_mix,
    get_health,
    get_investment,
    get_vulnerability,
)
from utils.chart_styles import (
    CHART_FONT,
    CHART_MARGIN,
    PAPER_BG,
    PLOT_BG,
    GRID_COLOR,
    GRAPH_CONFIG,
    SOURCE_COLORS,
    empty_figure,
)


dash.register_page(
    __name__,
    path="/compare",
    title="Country Comparison -- Energy Transition Dashboard",
    description="Compare energy transition metrics across 2-4 countries side by side.",
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# 4 distinct colors for compared countries
COUNTRY_COLORS = ["#2c3e50", "#e74c3c", "#3498db", "#27ae60"]

# Default countries (used when no URL params are provided)
_DEFAULTS = ["USA", "CHN", "IND", "DEU"]

# Energy source display order for stacked bars
_ENERGY_SOURCES = ["coal", "oil", "gas", "nuclear", "hydro", "wind", "solar", "biomass", "other_renewable"]

# Map ISO3 codes to IEA WEI regions for investment data
_ISO3_TO_IEA_REGION = {}
_REGION_MAP = {
    "North America": [
        "USA", "CAN", "MEX",
    ],
    "Europe": [
        "AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN", "FRA",
        "DEU", "GRC", "HUN", "IRL", "ITA", "LVA", "LTU", "LUX", "MLT", "NLD",
        "POL", "PRT", "ROU", "SVK", "SVN", "ESP", "SWE", "NOR", "ISL", "GBR",
        "CHE", "TUR",
    ],
    "Central & South America": [
        "ARG", "BOL", "BRA", "CHL", "COL", "ECU", "PRY", "PER", "URY", "VEN",
        "CRI", "PAN", "GTM", "SLV", "HND", "NIC", "DOM", "JAM", "TTO", "CUB",
    ],
    "Africa": [
        "DZA", "AGO", "BEN", "BWA", "CMR", "TCD", "COD", "EGY", "ETH", "GHA",
        "KEN", "LBY", "MDG", "MWI", "MLI", "MAR", "MOZ", "NGA", "SEN", "ZAF",
        "TZA", "TUN", "UGA", "ZMB", "ZWE", "GAB", "NAM", "NER",
    ],
    "Middle East": [
        "SAU", "ARE", "IRN", "IRQ", "KWT", "QAT", "OMN", "BHR", "ISR", "JOR",
        "LBN", "SYR", "YEM",
    ],
    "Eurasia": [
        "RUS", "UKR", "KAZ", "UZB", "TKM", "AZE", "GEO", "ARM", "BLR", "MDA",
    ],
    "Asia Pacific": [
        "JPN", "KOR", "AUS", "NZL", "IND", "IDN", "THA", "VNM", "MYS", "PHL",
        "SGP", "BGD", "PAK", "LKA", "MMR", "NPL", "TWN", "MNG", "KHM", "LAO",
    ],
}
for _region, _isos in _REGION_MAP.items():
    for _iso in _isos:
        _ISO3_TO_IEA_REGION[_iso] = _region
_ISO3_TO_IEA_REGION["CHN"] = "China"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_country_name(iso3: str) -> str:
    """Look up country name from ISO3 code."""
    meta = get_country_meta()
    if meta.empty:
        return iso3
    row = meta[meta["iso3"] == iso3]
    if row.empty:
        return iso3
    return str(row.iloc[0]["country_name"])


def _country_options() -> list[dict]:
    """Build dropdown options from country metadata."""
    meta = get_country_meta()
    if meta.empty:
        return []
    meta_sorted = meta.sort_values("country_name")
    return [
        {"label": row["country_name"], "value": row["iso3"]}
        for _, row in meta_sorted.iterrows()
    ]


def _base_layout(title: str, **kwargs) -> dict:
    """Return a standard Plotly layout dict for comparison charts."""
    layout_dict = dict(
        title=dict(text=title, font={**CHART_FONT, "size": 16}),
        font=CHART_FONT,
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        margin=CHART_MARGIN,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
        yaxis=dict(gridcolor=GRID_COLOR, zeroline=False),
        height=420,
    )
    layout_dict.update(kwargs)
    return layout_dict


def _chart_card(title: str, figure_or_placeholder, source_text: str) -> dbc.Card:
    """Wrap a figure (or placeholder html) in a consistent card layout."""
    if isinstance(figure_or_placeholder, go.Figure) or isinstance(figure_or_placeholder, dict):
        content = dcc.Graph(figure=figure_or_placeholder, config=GRAPH_CONFIG)
    else:
        content = figure_or_placeholder

    return dbc.Card([
        dbc.CardBody([
            content,
            dbc.Alert(
                source_text,
                color="light",
                className="mt-2 mb-0 py-1 px-2 small text-muted",
            ),
        ])
    ], className="mb-4 shadow-sm")


def _no_data_placeholder(metric_name: str, country_name: str) -> html.P:
    """Return a styled placeholder when data is not available."""
    return html.P(
        f"Data not available for {country_name}",
        className="text-muted fst-italic text-center py-4",
    )


# ---------------------------------------------------------------------------
# Chart builders (all defined locally)
# ---------------------------------------------------------------------------

def _co2_trajectory_chart(countries: list[str]) -> go.Figure:
    """Line chart: CO2 emissions trajectory (1990-latest), one line per country."""
    df = get_emissions()
    if df.empty:
        return empty_figure("No emissions data available")

    fig = go.Figure()
    for i, iso3 in enumerate(countries):
        cdf = df[(df["iso3"] == iso3) & (df["year"] >= 1990) & df["co2_fossil_mt"].notna()]
        if cdf.empty:
            continue
        cdf = cdf.sort_values("year")
        fig.add_trace(go.Scatter(
            x=cdf["year"],
            y=cdf["co2_fossil_mt"],
            name=_get_country_name(iso3),
            mode="lines",
            line=dict(color=COUNTRY_COLORS[i % len(COUNTRY_COLORS)], width=2.5),
            hovertemplate="%{x}: %{y:.1f} Mt CO2<extra>%{fullData.name}</extra>",
        ))

    if not fig.data:
        return empty_figure("No CO2 emissions data for selected countries")

    fig.update_layout(**_base_layout(
        "CO2 Emissions Trajectory",
        yaxis_title="Fossil CO2 Emissions (Mt)",
        xaxis_title="Year",
    ))
    return fig


def _renewable_share_chart(countries: list[str]) -> go.Figure:
    """Line chart: renewable electricity share over time, one line per country."""
    df = get_energy_mix()
    if df.empty:
        return empty_figure("No energy mix data available")

    fig = go.Figure()
    for i, iso3 in enumerate(countries):
        cdf = df[(df["iso3"] == iso3) & df["renewable_share_electricity_pct"].notna()]
        if cdf.empty:
            continue
        cdf = cdf.sort_values("year")
        fig.add_trace(go.Scatter(
            x=cdf["year"],
            y=cdf["renewable_share_electricity_pct"],
            name=_get_country_name(iso3),
            mode="lines",
            line=dict(color=COUNTRY_COLORS[i % len(COUNTRY_COLORS)], width=2.5),
            hovertemplate="%{x}: %{y:.1f}%<extra>%{fullData.name}</extra>",
        ))

    if not fig.data:
        return empty_figure("No renewable share data for selected countries")

    fig.update_layout(**_base_layout(
        "Renewable Electricity Share",
        yaxis_title="Renewable Share (%)",
        xaxis_title="Year",
        yaxis=dict(gridcolor=GRID_COLOR, zeroline=False, range=[0, None]),
    ))
    return fig


def _energy_mix_bar_chart(countries: list[str]) -> go.Figure:
    """Grouped/stacked bar chart: electricity mix breakdown (latest year), one group per country."""
    df = get_energy_mix()
    if df.empty:
        return empty_figure("No energy mix data available")

    # For each country, get the latest year with total_electricity_twh
    country_data = {}
    for iso3 in countries:
        cdf = df[(df["iso3"] == iso3) & df["total_electricity_twh"].notna()]
        if cdf.empty:
            continue
        latest = cdf.sort_values("year").iloc[-1]
        country_data[iso3] = latest

    if not country_data:
        return empty_figure("No electricity mix data for selected countries")

    fig = go.Figure()

    # Build stacked bars: each source is a trace, x-axis has country names
    country_names = [_get_country_name(iso3) for iso3 in country_data]

    for source in _ENERGY_SOURCES:
        col = f"electricity_twh_{source}"
        values = []
        for iso3 in country_data:
            val = country_data[iso3].get(col, 0)
            values.append(val if pd.notna(val) else 0)

        display_name = source.replace("_", " ").title()
        color = SOURCE_COLORS.get(source, "#bdc3c7")

        fig.add_trace(go.Bar(
            x=country_names,
            y=values,
            name=display_name,
            marker_color=color,
            hovertemplate=f"{display_name}: %{{y:.1f}} TWh<extra>%{{x}}</extra>",
        ))

    fig.update_layout(**_base_layout(
        "Electricity Mix Breakdown (Latest Year)",
        yaxis_title="Electricity Generation (TWh)",
        barmode="stack",
    ))
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )
    return fig


def _co2_per_capita_bar(countries: list[str]) -> go.Figure:
    """Bar chart: CO2 per capita comparison across countries."""
    df = get_emissions()
    if df.empty:
        return empty_figure("No emissions data available")

    names = []
    values = []
    colors = []
    for i, iso3 in enumerate(countries):
        cdf = df[(df["iso3"] == iso3) & df["co2_per_capita_t"].notna()]
        if cdf.empty:
            continue
        latest = cdf.sort_values("year").iloc[-1]
        names.append(_get_country_name(iso3))
        values.append(latest["co2_per_capita_t"])
        colors.append(COUNTRY_COLORS[i % len(COUNTRY_COLORS)])

    if not names:
        return empty_figure("No CO2 per capita data for selected countries")

    fig = go.Figure(go.Bar(
        x=names,
        y=values,
        marker_color=colors,
        hovertemplate="%{x}: %{y:.1f} t CO2/capita<extra></extra>",
    ))
    fig.update_layout(**_base_layout(
        "CO2 per Capita",
        yaxis_title="Tonnes CO2 per Capita",
    ))
    return fig


def _health_deaths_bar(countries: list[str]) -> go.Figure:
    """Bar chart: fossil fuel PM2.5 deaths per 100k population."""
    df_health = get_health()
    df_emis = get_emissions()
    if df_health.empty or df_emis.empty:
        return empty_figure("No health data available")

    names = []
    values = []
    colors = []
    for i, iso3 in enumerate(countries):
        # Get latest fossil_fuel_deaths (total count in thousands)
        hdf = df_health[(df_health["iso3"] == iso3) & df_health["fossil_fuel_deaths"].notna()]
        if hdf.empty:
            continue
        latest_h = hdf.sort_values("year").iloc[-1]
        death_year = latest_h["year"]

        # Get population for the same year (or closest)
        edf = df_emis[(df_emis["iso3"] == iso3) & df_emis["population"].notna()]
        if edf.empty:
            continue
        pop_row = edf.iloc[(edf["year"] - death_year).abs().argsort().iloc[0]]
        pop = pop_row["population"]

        if pop > 0:
            # fossil_fuel_deaths is in thousands (absolute count in thousands)
            # Convert to per 100k population
            deaths_total_thousands = latest_h["fossil_fuel_deaths"]
            deaths_per_100k = (deaths_total_thousands * 1000) / pop * 100_000
            names.append(_get_country_name(iso3))
            values.append(deaths_per_100k)
            colors.append(COUNTRY_COLORS[i % len(COUNTRY_COLORS)])

    if not names:
        return empty_figure("No fossil fuel PM2.5 death data for selected countries")

    fig = go.Figure(go.Bar(
        x=names,
        y=values,
        marker_color=colors,
        hovertemplate="%{x}: %{y:.1f} deaths per 100k<extra></extra>",
    ))
    fig.update_layout(**_base_layout(
        "Fossil Fuel PM2.5 Deaths per 100k",
        yaxis_title="Deaths per 100,000 Population",
    ))
    return fig


def _investment_bar(countries: list[str]) -> go.Figure:
    """Bar chart: clean energy investment by region (maps countries to IEA regions)."""
    inv = get_investment()
    if inv.empty:
        return empty_figure("No investment data available")

    # Map each country to its IEA region and get the latest clean_energy_investment_bn
    names = []
    values = []
    colors = []
    seen_regions = set()

    for i, iso3 in enumerate(countries):
        region = _ISO3_TO_IEA_REGION.get(iso3)
        if not region or region in seen_regions:
            continue
        seen_regions.add(region)

        rdf = inv[(inv["region"] == region) & inv["clean_energy_investment_bn"].notna()]
        if rdf.empty:
            continue
        latest = rdf.sort_values("year").iloc[-1]
        label = f"{_get_country_name(iso3)} ({region})"
        names.append(label)
        values.append(latest["clean_energy_investment_bn"])
        colors.append(COUNTRY_COLORS[i % len(COUNTRY_COLORS)])

    if not names:
        return empty_figure("No investment data for selected countries' regions")

    fig = go.Figure(go.Bar(
        x=names,
        y=values,
        marker_color=colors,
        hovertemplate="%{x}: $%{y:.1f}B<extra></extra>",
    ))
    fig.update_layout(**_base_layout(
        "Clean Energy Investment (by Region)",
        yaxis_title="Investment ($ Billion)",
    ))
    return fig


def _vulnerability_bar(countries: list[str]) -> go.Figure:
    """Bar chart: ND-GAIN climate vulnerability score comparison."""
    df = get_vulnerability()
    if df.empty:
        return empty_figure("No vulnerability data available")

    names = []
    values = []
    colors = []
    for i, iso3 in enumerate(countries):
        cdf = df[(df["iso3"] == iso3) & df["gain_score"].notna()]
        if cdf.empty:
            continue
        latest = cdf.sort_values("year").iloc[-1]
        names.append(_get_country_name(iso3))
        values.append(latest["gain_score"])
        colors.append(COUNTRY_COLORS[i % len(COUNTRY_COLORS)])

    if not names:
        return empty_figure("No ND-GAIN data for selected countries")

    fig = go.Figure(go.Bar(
        x=names,
        y=values,
        marker_color=colors,
        hovertemplate="%{x}: %{y:.1f}<extra></extra>",
    ))
    fig.update_layout(**_base_layout(
        "Climate Vulnerability Score (ND-GAIN)",
        yaxis_title="ND-GAIN Score (higher = less vulnerable)",
        yaxis=dict(gridcolor=GRID_COLOR, zeroline=False, range=[0, 100]),
    ))
    return fig


# ---------------------------------------------------------------------------
# Summary table builder
# ---------------------------------------------------------------------------

def _build_summary_table(countries: list[str]) -> dbc.Table:
    """Build a summary table of key indicators for selected countries."""
    emissions_df = get_emissions()
    mix_df = get_energy_mix()

    rows = []
    for iso3 in countries:
        name = _get_country_name(iso3)

        # Get latest emissions row
        edf = emissions_df[(emissions_df["iso3"] == iso3)] if not emissions_df.empty else pd.DataFrame()
        latest_e = edf.sort_values("year").iloc[-1] if not edf.empty else pd.Series()

        # Get latest energy mix row
        mdf = mix_df[(mix_df["iso3"] == iso3)] if not mix_df.empty else pd.DataFrame()
        latest_m = mdf[mdf["renewable_share_electricity_pct"].notna()].sort_values("year")
        latest_m = latest_m.iloc[-1] if not latest_m.empty else pd.Series()

        # Population
        pop = latest_e.get("population", None)
        pop_str = f"{pop / 1e6:,.1f}M" if pd.notna(pop) and pop else "--"

        # GDP
        gdp = latest_e.get("gdp_usd", None)
        gdp_str = f"${gdp / 1e12:,.2f}T" if pd.notna(gdp) and gdp else "--"

        # Total GHG
        ghg = latest_e.get("ghg_total_mtco2e", None)
        ghg_str = f"{ghg:,.0f} Mt" if pd.notna(ghg) and ghg else "--"

        # CO2 per capita
        co2pc = latest_e.get("co2_per_capita_t", None)
        co2pc_str = f"{co2pc:.1f} t" if pd.notna(co2pc) else "--"

        # Renewable share
        ren = latest_m.get("renewable_share_electricity_pct", None) if not latest_m.empty else None
        ren_str = f"{ren:.1f}%" if pd.notna(ren) else "--"

        rows.append(html.Tr([
            html.Td(html.Strong(name)),
            html.Td(pop_str),
            html.Td(gdp_str),
            html.Td(ghg_str),
            html.Td(co2pc_str),
            html.Td(ren_str),
        ]))

    header = html.Thead(html.Tr([
        html.Th("Country"),
        html.Th("Population"),
        html.Th("GDP"),
        html.Th("Total GHG"),
        html.Th("CO2/Capita"),
        html.Th("Renewable Share"),
    ]))

    return dbc.Table(
        [header, html.Tbody(rows)],
        bordered=True,
        hover=True,
        responsive=True,
        striped=True,
        className="mb-4",
        size="sm",
    )


# ---------------------------------------------------------------------------
# Main callback function (wired in app.py)
# ---------------------------------------------------------------------------

def update_comparison(c0, c1, c2, c3):
    """
    Build all 7 comparison charts for the selected countries.

    Called by app.callback with inputs from the 4 country selectors.
    Returns an html.Div containing summary table + chart cards.
    """
    # Filter out None/empty selections
    countries = [c for c in [c0, c1, c2, c3] if c]

    if len(countries) < 2:
        return html.Div(
            html.P(
                "Please select at least 2 countries to compare.",
                className="text-muted fst-italic text-center py-5 fs-5",
            )
        )

    # Remove duplicates while preserving order
    seen = set()
    unique_countries = []
    for c in countries:
        if c not in seen:
            seen.add(c)
            unique_countries.append(c)
    countries = unique_countries

    # Build summary table
    summary_table = _build_summary_table(countries)

    # Build all 7 chart cards
    charts = []

    # 1. CO2 Emissions Trajectory
    charts.append(_chart_card(
        "CO2 Emissions Trajectory",
        _co2_trajectory_chart(countries),
        "Source: Global Carbon Budget via Our World in Data (CC-BY 4.0)",
    ))

    # 2. Renewable Electricity Share
    charts.append(_chart_card(
        "Renewable Electricity Share",
        _renewable_share_chart(countries),
        "Source: Ember / Our World in Data (CC-BY 4.0)",
    ))

    # 3. Energy Mix Breakdown
    charts.append(_chart_card(
        "Electricity Mix Breakdown",
        _energy_mix_bar_chart(countries),
        "Source: Ember / Our World in Data (CC-BY 4.0)",
    ))

    # 4. CO2 per Capita
    charts.append(_chart_card(
        "CO2 per Capita",
        _co2_per_capita_bar(countries),
        "Source: Global Carbon Budget via Our World in Data (CC-BY 4.0)",
    ))

    # 5. Fossil Fuel PM2.5 Deaths per 100k
    charts.append(_chart_card(
        "Fossil Fuel PM2.5 Deaths per 100k",
        _health_deaths_bar(countries),
        "Source: McDuffie et al. (2021) via Our World in Data",
    ))

    # 6. Clean Energy Investment
    charts.append(_chart_card(
        "Clean Energy Investment (Regional)",
        _investment_bar(countries),
        "Source: IEA World Energy Investment 2025. Note: data is at the regional level.",
    ))

    # 7. Climate Vulnerability Score
    charts.append(_chart_card(
        "Climate Vulnerability Score (ND-GAIN)",
        _vulnerability_bar(countries),
        "Source: ND-GAIN Country Index, University of Notre Dame",
    ))

    return html.Div([
        html.H5("Key Indicators", className="mt-3 mb-3"),
        summary_table,
        html.H5("Comparison Charts", className="mt-4 mb-3"),
        *charts,
    ])


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

def layout(**kwargs):
    """
    Render the country comparison page.

    Reads optional URL search params (c1, c2, c3, c4) to set default
    dropdown values. Falls back to _DEFAULTS if not provided.
    """
    # Parse URL search params for default country selections
    defaults = list(_DEFAULTS)
    search = kwargs.get("search", "") or ""
    if search:
        params = urllib.parse.parse_qs(search.lstrip("?"))
        for i in range(4):
            key = f"c{i + 1}"
            if key in params:
                val = params[key][0].upper()
                defaults[i] = val

    # Build country dropdown options
    options = _country_options()

    # Options for slots 3 and 4 include an empty "Add country..." option
    options_with_empty = [{"label": "Add country...", "value": ""}] + options

    # Build the 4 country selector dropdowns
    selectors = dbc.Row([
        dbc.Col(
            dbc.Select(
                id=f"compare-country-{i}",
                options=options if i < 2 else options_with_empty,
                value=defaults[i] if i < len(defaults) else "",
                className="mb-2",
            ),
            xs=12, sm=6, md=3,
        )
        for i in range(4)
    ], className="mb-3")

    return html.Div([
        dcc.Location(id="compare-loc", refresh=False),

        dbc.Container([
            # Page header
            html.H2("Country Comparison", className="display-6 fw-bold mt-4 mb-1"),
            html.P(
                "Select 2-4 countries to compare across key energy transition metrics.",
                className="text-muted mb-3",
            ),

            # Country selectors
            selectors,

            html.Hr(className="mt-1 mb-3"),

            # Content area — pre-populated with defaults, updated by callback
            html.Div(
                update_comparison(defaults[0], defaults[1], defaults[2], defaults[3]),
                id="compare-content",
            ),
        ], fluid=False),
    ])
