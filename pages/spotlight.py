"""
spotlight.py — Country Spotlights page for the Energy Transition Dashboard.

Showcases 18 compelling energy transition stories from around the world,
organized by 6 narrative themes. Each country card shows a headline takeaway,
key metrics from existing data, and links to the full country detail page.

Content is hardcoded from research/country_spotlight_synthesis.md rather than
dynamically generated — this keeps the page fast and the narratives curated.
"""

from __future__ import annotations

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from typing import Optional

from utils.data_loader import (
    get_emissions, get_energy_mix, get_capacity, get_country_meta,
)

dash.register_page(
    __name__,
    path="/spotlight",
    title="Country Spotlights — Energy Transition Dashboard",
)

# ---------------------------------------------------------------------------
# Graph config (consistent with rest of dashboard)
# ---------------------------------------------------------------------------
_GRAPH_CONFIG = {"responsive": True, "displayModeBar": False, "displaylogo": False}

# ---------------------------------------------------------------------------
# Flag emoji lookup (ISO2 letter offsets -> regional indicator symbols)
# ---------------------------------------------------------------------------
_ISO3_TO_ISO2 = {
    "KEN": "KE", "NGA": "NG", "PAK": "PK", "ZAF": "ZA", "URY": "UY",
    "DNK": "DK", "USA": "US", "VNM": "VN", "CHN": "CN", "IND": "IN",
    "DEU": "DE", "SAU": "SA", "IDN": "ID", "CHL": "CL", "AUS": "AU",
    "POL": "PL", "ETH": "ET", "CRI": "CR", "COL": "CO",
}

def _flag(iso3: str) -> str:
    """Return flag emoji for an ISO3 code."""
    iso2 = _ISO3_TO_ISO2.get(iso3, "")
    if len(iso2) == 2:
        return chr(0x1F1E6 + ord(iso2[0]) - ord("A")) + chr(0x1F1E6 + ord(iso2[1]) - ord("A"))
    return ""


# ---------------------------------------------------------------------------
# Spotlight data: 18 countries organized by 6 narrative themes
# ---------------------------------------------------------------------------

THEMES = [
    {
        "name": "Electrostates",
        "subtitle": "Scale that reshapes global markets",
        "color": "#e65100",
        "icon": "bi-graph-up-arrow",
        "countries": [
            {
                "iso3": "CHN",
                "name": "China",
                "headline": "Installed 210 GW of solar in H1 2025 alone — more than the entire US has "
                            "ever installed. Clean energy now equals 11.4% of GDP and drove over a third "
                            "of economic growth. Yet China simultaneously added record coal capacity.",
                "metrics": ["solar_capacity", "emissions_total", "renewable_share"],
            },
            {
                "iso3": "IND",
                "name": "India",
                "headline": "Non-fossil capacity crossed 50% in June 2025, five years ahead of target. "
                            "Coal power fell for the first time outside COVID, and emissions growth hit a "
                            "20-year low. The race between clean supply and surging demand defines the global trajectory.",
                "metrics": ["solar_capacity", "renewable_share", "emissions_total"],
            },
        ],
    },
    {
        "name": "Leapfroggers",
        "subtitle": "Building new systems, not converting old ones",
        "color": "#2e7d32",
        "icon": "bi-rocket-takeoff",
        "countries": [
            {
                "iso3": "KEN",
                "name": "Kenya",
                "headline": "A 92% renewable grid — cleaner than virtually any industrialized nation. "
                            "Geothermal provides always-on baseload while M-KOPA's mobile-money "
                            "pay-as-you-go solar model has disbursed $1.6B to 4.8 million off-grid customers.",
                "metrics": ["renewable_share", "co2_per_capita", "solar_capacity"],
            },
            {
                "iso3": "NGA",
                "name": "Nigeria",
                "headline": "96% of installed solar is off-grid — the decentralized transition IS the "
                            "transition. The national grid collapsed 12 times in 2024, making off-grid "
                            "the rational economic choice for Africa's largest population.",
                "metrics": ["renewable_share", "co2_per_capita", "emissions_total"],
            },
            {
                "iso3": "PAK",
                "name": "Pakistan",
                "headline": "Satellite imagery revealed 22-32 GW of distributed solar — 2-3x what "
                            "officials tracked. Solar went from 4% to ~24% of generation in 3 years, "
                            "driven by an energy price crisis, not policy.",
                "metrics": ["solar_capacity", "renewable_share", "emissions_total"],
            },
            {
                "iso3": "ETH",
                "name": "Ethiopia",
                "headline": "Africa's largest hydropower project (GERD, 5,150 MW) more than doubled "
                            "national capacity — while the country banned gasoline vehicle imports "
                            "entirely, the world's most aggressive vehicle electrification mandate.",
                "metrics": ["renewable_share", "co2_per_capita", "emissions_total"],
            },
        ],
    },
    {
        "name": "Crisis Catalysts",
        "subtitle": "Failure and disruption as accelerants",
        "color": "#c62828",
        "icon": "bi-lightning-charge",
        "countries": [
            {
                "iso3": "ZAF",
                "name": "South Africa",
                "headline": "Load shedding cost $155B in 2023 and drove distributed solar from 1.2 GW "
                            "to 6.1 GW in just 3 years. The market moved faster than policy in a country "
                            "still 82% coal-dependent with 90,000 mining jobs at stake.",
                "metrics": ["coal_share", "solar_capacity", "co2_per_capita"],
            },
            {
                "iso3": "POL",
                "name": "Poland",
                "headline": "Coal's cultural heartland achieved a 1,000-fold solar growth in a decade "
                            "via 1.5 million prosumer households. Renewables outproduced coal for the "
                            "first time in June 2025 — a bottom-up revolution in politically hostile terrain.",
                "metrics": ["renewable_share", "coal_share", "solar_capacity"],
            },
            {
                "iso3": "CRI",
                "name": "Costa Rica",
                "headline": "Near-100% renewable electricity for over a decade — then the 2024 El Nino "
                            "crashed it from 98% to 86%, revealing the climate vulnerability of "
                            "hydro-dependent clean grids. Recovery to 98.6% in 2025 demonstrated system resilience.",
                "metrics": ["renewable_share", "co2_per_capita", "emissions_total"],
            },
        ],
    },
    {
        "name": "Policy Architects",
        "subtitle": "Where institutional design made or broke the transition",
        "color": "#1565c0",
        "icon": "bi-bank2",
        "countries": [
            {
                "iso3": "URY",
                "name": "Uruguay",
                "headline": "From fossil-dependent and energy-rationing in 2008 to 99% renewable electricity "
                            "in 2024 — with no silver bullet technology. Just institutional design, "
                            "long-term contracts, and cross-partisan commitment. Energy costs halved.",
                "metrics": ["renewable_share", "wind_capacity", "emissions_trend"],
            },
            {
                "iso3": "DNK",
                "name": "Denmark",
                "headline": "From the 1973 oil crisis to 88% renewable electricity and a 51% GHG cut. "
                            "Created the global wind industry (Vestas, Orsted) and passed the world's "
                            "first agricultural carbon tax. 50 years of consistent industrial policy.",
                "metrics": ["renewable_share", "wind_capacity", "emissions_trend"],
            },
            {
                "iso3": "USA",
                "name": "United States",
                "headline": "93% of new power capacity is clean, and 85% of IRA clean energy investment "
                            "went to Republican districts — yet those legislators voted to roll it back. "
                            "Market momentum is strong, but policy whiplash tests whether economics alone suffice.",
                "metrics": ["solar_capacity", "wind_capacity", "emissions_total"],
            },
            {
                "iso3": "VNM",
                "name": "Vietnam",
                "headline": "A 600-fold increase in solar capacity in 3 years — then a 5-year investment "
                            "freeze when the feed-in tariff expired with no replacement. A cautionary tale "
                            "about deployment without policy continuity.",
                "metrics": ["solar_capacity", "renewable_share", "coal_share"],
            },
            {
                "iso3": "DEU",
                "name": "Germany",
                "headline": "Simultaneously exiting nuclear, coal, AND Russian gas dependence — no other "
                            "major economy is attempting all three at once. Hit 62.7% renewable electricity "
                            "in 2024, but high costs and slow transport decarbonization show the price of "
                            "managing a multi-front energy transition.",
                "metrics": ["renewable_share", "emissions_total", "wind_capacity"],
            },
        ],
    },
    {
        "name": "Petrostate Paradoxes",
        "subtitle": "Fossil wealth meets clean energy",
        "color": "#37474f",
        "icon": "bi-signpost-split",
        "countries": [
            {
                "iso3": "SAU",
                "name": "Saudi Arabia",
                "headline": "Solar at ~1 cent/kWh — among the cheapest electricity anywhere. The world's "
                            "largest green hydrogen plant is 90% complete. Yet renewables still provide "
                            "only ~2% of electricity and emissions keep rising.",
                "metrics": ["solar_capacity", "renewable_share", "co2_per_capita"],
            },
            {
                "iso3": "COL",
                "name": "Colombia",
                "headline": "The first major fossil fuel producer to suspend new oil/gas exploration "
                            "licenses and endorse the Fossil Fuel Non-Proliferation Treaty — an "
                            "unprecedented policy experiment in a country where 75% of electricity "
                            "is already renewable.",
                "metrics": ["renewable_share", "co2_per_capita", "emissions_trend"],
            },
            {
                "iso3": "IDN",
                "name": "Indonesia",
                "headline": "The global EV transition's most uncomfortable supply chain story: 97% of "
                            "nickel smelter electricity comes from captive coal that tripled since 2019. "
                            "Indonesia sits on 40% of the world's geothermal resources — only 11% developed.",
                "metrics": ["coal_share", "renewable_share", "emissions_total"],
            },
        ],
    },
    {
        "name": "Success Creates New Challenges",
        "subtitle": "What happens after you \"win\"",
        "color": "#00838f",
        "icon": "bi-trophy",
        "countries": [
            {
                "iso3": "CHL",
                "name": "Chile",
                "headline": "Exceeded its own 2035 renewable target a decade early (68% in 2024), "
                            "then hit a $562M/year curtailment wall. The first country to fully demonstrate "
                            "that building generation is easier than building the system around it.",
                "metrics": ["renewable_share", "solar_capacity", "emissions_trend"],
            },
            {
                "iso3": "AUS",
                "name": "South Australia",
                "subtitle": "(State spotlight)",
                "headline": "From 1% to 74% renewable in ~16 years. Ran on 100% renewables for ~99 days "
                            "in 2024. Grid-forming batteries (the 'Big Battery') proved that batteries can "
                            "provide grid stability — a world first with global implications.",
                "metrics": ["renewable_share", "solar_capacity", "wind_capacity"],
            },
        ],
    },
]


# ---------------------------------------------------------------------------
# Metric extraction helpers — pull latest values from parquet data
# ---------------------------------------------------------------------------

def _get_latest(df: pd.DataFrame, iso3: str, col: str):
    """Get the most recent non-null value of `col` for a country."""
    if df.empty or col not in df.columns:
        return None
    subset = df[(df["iso3"] == iso3) & df[col].notna()].sort_values("year")
    if subset.empty:
        return None
    return subset.iloc[-1][col]


def _get_latest_year(df: pd.DataFrame, iso3: str, col: str):
    """Get the year of the most recent non-null value."""
    if df.empty or col not in df.columns:
        return None
    subset = df[(df["iso3"] == iso3) & df[col].notna()].sort_values("year")
    if subset.empty:
        return None
    return int(subset.iloc[-1]["year"])


def _emissions_trend_pct(df: pd.DataFrame, iso3: str, window: int = 10) -> Optional[str]:
    """Compute % change in total CO2 over the last `window` years."""
    if df.empty or "co2_fossil_mt" not in df.columns:
        return None
    subset = df[(df["iso3"] == iso3) & df["co2_fossil_mt"].notna()].sort_values("year")
    if len(subset) < 2:
        return None
    recent = subset.iloc[-1]
    # Find a row ~window years back
    target_year = recent["year"] - window
    older = subset[subset["year"] <= target_year]
    if older.empty:
        older_row = subset.iloc[0]
    else:
        older_row = older.iloc[-1]
    if older_row["co2_fossil_mt"] == 0:
        return None
    pct = (recent["co2_fossil_mt"] - older_row["co2_fossil_mt"]) / older_row["co2_fossil_mt"] * 100
    years = int(recent["year"] - older_row["year"])
    sign = "+" if pct > 0 else ""
    return f"{sign}{pct:.0f}% over {years}yr"


def _hex_to_rgba(hex_color: str, alpha: float = 0.1) -> str:
    """Convert #RRGGBB to rgba(r,g,b,alpha)."""
    h = hex_color.lstrip("#")
    if len(h) == 6:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"
    return f"rgba(0,0,0,{alpha})"


_SPARKLINE_CACHE: dict = {}

def _sparkline_figure(df: pd.DataFrame, iso3: str, col: str, color: str = "#1565c0"):
    """Build a tiny sparkline figure for a metric, or return None if no data. Cached."""
    cache_key = f"{iso3}_{col}_{color}"
    if cache_key in _SPARKLINE_CACHE:
        return _SPARKLINE_CACHE[cache_key]
    if df.empty or col not in df.columns:
        return None
    subset = df[(df["iso3"] == iso3) & df[col].notna()].sort_values("year")
    # Use last 20 years max for a cleaner sparkline
    if len(subset) > 20:
        subset = subset.tail(20)
    if len(subset) < 3:
        return None

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=subset["year"],
        y=subset[col],
        mode="lines",
        line=dict(color=color, width=2),
        fill="tozeroy",
        fillcolor=_hex_to_rgba(color, 0.1),
        hoverinfo="skip",
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=45,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
    )
    _SPARKLINE_CACHE[cache_key] = fig
    return fig


def _get_country_metrics(iso3: str, metric_keys: list[str], theme_color: str) -> list:
    """Build metric display elements for a country card."""
    emissions = get_emissions()
    energy = get_energy_mix()
    capacity = get_capacity()

    items = []
    for key in metric_keys:
        if key == "renewable_share":
            val = _get_latest(energy, iso3, "renewable_share_electricity_pct")
            yr = _get_latest_year(energy, iso3, "renewable_share_electricity_pct")
            if val is not None:
                items.append(_metric_badge(f"Renewable: {val:.0f}%", yr, "bi-lightning-charge"))
                spark = _sparkline_figure(energy, iso3, "renewable_share_electricity_pct", theme_color)
                if spark:
                    items.append(dcc.Graph(figure=spark, config=_GRAPH_CONFIG,
                                           style={"height": "45px", "width": "100%"}))
            else:
                items.append(_metric_badge("Renewable share: N/A", None, "bi-lightning-charge"))

        elif key == "co2_per_capita":
            val = _get_latest(emissions, iso3, "co2_per_capita_t")
            yr = _get_latest_year(emissions, iso3, "co2_per_capita_t")
            if val is not None:
                items.append(_metric_badge(f"CO\u2082/capita: {val:.1f} t", yr, "bi-person"))
            else:
                items.append(_metric_badge("CO\u2082/capita: N/A", None, "bi-person"))

        elif key == "emissions_total":
            val = _get_latest(emissions, iso3, "co2_fossil_mt")
            yr = _get_latest_year(emissions, iso3, "co2_fossil_mt")
            if val is not None:
                if val >= 1000:
                    items.append(_metric_badge(f"CO\u2082: {val / 1000:.1f} Gt", yr, "bi-cloud"))
                else:
                    items.append(_metric_badge(f"CO\u2082: {val:.0f} Mt", yr, "bi-cloud"))
            else:
                items.append(_metric_badge("CO\u2082 emissions: N/A", None, "bi-cloud"))

        elif key == "emissions_trend":
            trend = _emissions_trend_pct(emissions, iso3)
            if trend is not None:
                items.append(_metric_badge(f"CO\u2082 trend: {trend}", None, "bi-graph-down-arrow"))
            else:
                items.append(_metric_badge("CO\u2082 trend: N/A", None, "bi-graph-down-arrow"))

        elif key == "solar_capacity":
            val = _get_latest(capacity, iso3, "capacity_gw_solar")
            yr = _get_latest_year(capacity, iso3, "capacity_gw_solar")
            if val is not None:
                items.append(_metric_badge(f"Solar: {val:.1f} GW", yr, "bi-sun"))
            else:
                items.append(_metric_badge("Solar capacity: N/A", None, "bi-sun"))

        elif key == "wind_capacity":
            val = _get_latest(capacity, iso3, "capacity_gw_wind")
            yr = _get_latest_year(capacity, iso3, "capacity_gw_wind")
            if val is not None:
                items.append(_metric_badge(f"Wind: {val:.1f} GW", yr, "bi-wind"))
            else:
                items.append(_metric_badge("Wind capacity: N/A", None, "bi-wind"))

        elif key == "coal_share":
            # Compute coal share from energy mix
            total = _get_latest(energy, iso3, "total_electricity_twh")
            coal = _get_latest(energy, iso3, "electricity_twh_coal")
            yr = _get_latest_year(energy, iso3, "total_electricity_twh")
            if total and coal and total > 0:
                share = coal / total * 100
                items.append(_metric_badge(f"Coal: {share:.0f}%", yr, "bi-minecart-loaded"))
            else:
                items.append(_metric_badge("Coal share: N/A", None, "bi-minecart-loaded"))

    return items


def _metric_badge(text: str, year: Optional[int], icon: str) -> html.Div:
    """Create a small metric display element."""
    year_str = f" ({year})" if year else ""
    return html.Div(
        [
            html.I(className=f"{icon} me-1", style={"fontSize": "0.8rem"}),
            html.Span(text, style={"fontSize": "0.8rem", "fontWeight": "600"}),
            html.Span(year_str, style={"fontSize": "0.7rem", "color": "#6c757d"}) if year else None,
        ],
        className="d-flex align-items-center mb-1",
        style={"lineHeight": "1.4"},
    )


# ---------------------------------------------------------------------------
# Card builder
# ---------------------------------------------------------------------------

def _country_card(country: dict, theme_color: str) -> dbc.Col:
    """Build a single country spotlight card."""
    iso3 = country["iso3"]
    name = country["name"]
    flag = _flag(iso3)
    headline = country["headline"]
    metric_keys = country.get("metrics", [])
    subtitle = country.get("subtitle", "")

    # For South Australia, note that data is for all of Australia
    is_south_australia = (iso3 == "AUS" and "South Australia" in name)
    data_note = ""
    if is_south_australia:
        data_note = "Data shown is for Australia nationally"

    metrics = _get_country_metrics(iso3, metric_keys, theme_color)

    card_content = [
        dbc.CardHeader(
            html.Div([
                html.Span(f"{flag} ", style={"fontSize": "1.3rem"}),
                html.Strong(name, style={"fontSize": "1.05rem"}),
                html.Span(f"  {subtitle}", className="text-muted",
                          style={"fontSize": "0.8rem"}) if subtitle else None,
            ]),
            style={"backgroundColor": f"{theme_color}0d", "borderBottom": f"2px solid {theme_color}"},
        ),
        dbc.CardBody([
            html.P(headline, className="small mb-2", style={"lineHeight": "1.6", "color": "#495057"}),
            html.Div(metrics, className="mb-2") if metrics else None,
            html.Small(data_note, className="text-muted d-block mb-2") if data_note else None,
            dcc.Link(
                html.Span([
                    "View Full Profile ",
                    html.I(className="bi-arrow-right"),
                ]),
                href=f"/country/{iso3}",
                className="text-decoration-none fw-bold",
                style={"color": theme_color, "fontSize": "0.85rem"},
            ),
        ]),
    ]

    return dbc.Col(
        dbc.Card(card_content, className="h-100 shadow-sm spotlight-card"),
        md=6, lg=4, className="mb-4",
    )


# ---------------------------------------------------------------------------
# Theme section builder
# ---------------------------------------------------------------------------

def _theme_section(theme: dict) -> html.Div:
    """Build a themed section with its country cards."""
    name = theme["name"]
    subtitle = theme["subtitle"]
    color = theme["color"]
    icon = theme["icon"]
    countries = theme["countries"]

    cards = [_country_card(c, color) for c in countries]

    return html.Div([
        html.Div([
            html.H3(
                [html.I(className=f"{icon} me-2"), name],
                className="fw-bold mb-1",
                style={"color": color},
            ),
            html.P(subtitle, className="text-muted mb-3", style={"fontSize": "0.95rem"}),
        ]),
        dbc.Row(cards, className="g-3"),
    ], className="mb-5")


# ---------------------------------------------------------------------------
# "Why These 18 Countries?" justification section
# ---------------------------------------------------------------------------

def _why_these_countries_section() -> dbc.Card:
    """Build the analytical framework justification card."""
    return dbc.Card([
        dbc.CardHeader(
            html.H4(
                [html.I(className="bi-question-circle me-2"), "Why These 18 Countries?"],
                className="fw-bold mb-0",
                style={"color": "#37474f"},
            ),
            style={"backgroundColor": "#f8f9fa", "borderBottom": "2px solid #dee2e6"},
        ),
        dbc.CardBody([
            html.P([
                "These 18 countries are organized into six analytical archetypes — Electrostates, "
                "Leapfroggers, Crisis Catalysts, Policy Architects, Petrostate Paradoxes, and "
                "Success Creates New Challenges — rather than by geography or alphabetical order. "
                "Each archetype captures a distinct mechanism by which the energy transition "
                "advances (or stalls), drawn from the WEF Energy Transition Index classification "
                "system, the Carnegie Endowment's 'electrostate' concept, and the broader "
                "literature on crisis-driven versus policy-led transitions.",
            ], className="mb-3", style={"lineHeight": "1.7", "color": "#495057"}),
            html.P([
                "Selection criteria prioritized countries that are narratively distinctive, "
                "data-rich within our dashboard's sources (OWID, IRENA, Ember), and globally "
                "representative across income levels, regions, and energy system types. Each "
                "country was chosen because it illustrates something that no other country "
                "in the set demonstrates as clearly.",
            ], className="mb-3", style={"lineHeight": "1.7", "color": "#495057"}),
            html.P([
                "Notable exclusions: Morocco was the 19th candidate but its flagship projects "
                "are mostly in pre-deployment phases with limited operational data. The United "
                "Kingdom is important but overlaps substantially with Denmark's wind industry "
                "story. Bangladesh was analytically interesting (green factories on a fossil grid) "
                "but had limited coverage in our dashboard data sources. Turkey has strong data "
                "but its transition narrative overlaps with the Poland and Pakistan archetypes.",
            ], className="mb-0", style={"lineHeight": "1.7", "color": "#495057"}),
        ]),
    ], className="shadow-sm mb-5")


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

def layout(**kwargs):
    # Build all theme sections
    sections = [_theme_section(t) for t in THEMES]

    return html.Div([
        dbc.Container([
            # Page header
            dbc.Row([
                dbc.Col([
                    html.H1(
                        "Country Spotlights",
                        className="display-5 fw-bold mt-4 mb-1",
                    ),
                    html.P(
                        "Eighteen compelling energy transition stories from around the world — "
                        "organized into six narrative themes that define how the global energy "
                        "transition is actually unfolding on the ground.",
                        className="lead text-muted mb-2",
                    ),
                    html.P([
                        "Click any country to explore its full data profile. Metrics shown are ",
                        "the latest available from ",
                        html.A("Our World in Data", href="https://github.com/owid/energy-data",
                               target="_blank", className="text-primary"),
                        " and ",
                        html.A("IRENA", href="https://www.irena.org/Data", target="_blank",
                               className="text-primary"),
                        " datasets.",
                    ], className="small text-muted mb-3"),
                ], md=10, lg=9),
            ]),

            html.Hr(className="mb-4"),

            # All theme sections
            *sections,

            # "Why These 18 Countries?" justification section
            _why_these_countries_section(),

            # Footer note
            html.Div([
                html.Hr(),
                html.P([
                    html.I(className="bi-info-circle me-1"),
                    "Country narratives synthesized from regional research (April 2026). "
                    "'South Australia' uses national Australian data "
                    "as a proxy — state-level data is not available in this dataset.",
                ], className="small text-muted mb-4"),
                dcc.Link(
                    html.Span(["Back to Home ", html.I(className="bi-house")]),
                    href="/",
                    className="btn btn-outline-primary btn-sm me-2",
                ),
                dcc.Link(
                    html.Span(["Methodology ", html.I(className="bi-book")]),
                    href="/methodology",
                    className="btn btn-outline-secondary btn-sm",
                ),
            ], className="mb-5"),

        ], fluid=True, className="px-3 px-md-4"),
    ])
