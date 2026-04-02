"""
country.py — Country detail page for the Energy Transition Dashboard.

Dynamic route: /country/<iso3>
  e.g., /country/USA, /country/CHN, /country/DEU

Structure:
  - Back button
  - Header: country name + continent
  - Key stats row (5 cards: population, GDP, total GHG, CO₂/capita, renewable share)
  - 2-3 sentence template-based summary of energy transition status
  - Tabbed layout with LAZY loading:
      Tab content is built on demand via a callback (not all at once).
      Only the active tab's figures are built — speeds up initial load.
  - Invalid ISO3 → 404-style message

Design principles:
  - Lazy tab loading: only the selected tab's figures are built per request.
  - config={'responsive': True} on every dcc.Graph for correct mobile sizing.
  - Graceful handling of empty DataFrames throughout.
"""

import dash
from dash import html, dcc, callback, Output, Input, no_update
import dash_bootstrap_components as dbc
import pandas as pd

from utils.data_loader import (
    get_country_meta,
    get_country_emissions,
    get_country_energy_mix,
    get_country_finance,
    get_country_health,
    get_emissions,
    get_energy_mix,
    get_scenarios,
    get_costs,
    get_investment,
    get_subsidies,
    get_subsidy_indicators,
    is_valid_iso3,
)
from components.country_charts import (
    emissions_time_series_with_scenarios,
    energy_mix_stacked_area,
    energy_mix_donut,
    renewables_trend_chart,
    final_energy_shares_chart,
    methane_trend_chart,
    methane_per_capita_chart,
    peer_comparison_bars,
    health_mortality_chart,
    health_access_chart,
    health_pm25_trend,
    deaths_per_twh_comparison,
    heatwave_days_chart,
    country_subsidies_chart,
    regional_investment_chart,
    placeholder_figure,
)
from components.context_charts import cost_revolution

dash.register_page(
    __name__,
    path_template="/country/<iso3>",
    title="Country Profile — Energy Transition Dashboard",
)

# Graph config shared across all charts on this page
_GRAPH_CONFIG = {"responsive": True, "displayModeBar": False}

# Approximate global average fossil CO₂ per capita (tCO₂/yr), 2023
_GLOBAL_CO2_PC_AVG = 4.7

# Map ISO3 codes to IEA WEI regions for investment data context
_ISO3_TO_IEA_REGION = {}
_NORTH_AMERICA = ["USA", "CAN", "MEX"]
_EUROPE = [
    "AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN", "FRA",
    "DEU", "GRC", "HUN", "IRL", "ITA", "LVA", "LTU", "LUX", "MLT", "NLD",
    "POL", "PRT", "ROU", "SVK", "SVN", "ESP", "SWE", "NOR", "ISL", "GBR",
    "CHE", "TUR",
]
_CSA = [
    "ARG", "BOL", "BRA", "CHL", "COL", "ECU", "PRY", "PER", "URY", "VEN",
    "CRI", "PAN", "GTM", "SLV", "HND", "NIC", "DOM", "JAM", "TTO", "CUB",
]
_AFRICA = [
    "DZA", "AGO", "BEN", "BWA", "CMR", "TCD", "COD", "EGY", "ETH", "GHA",
    "KEN", "LBY", "MDG", "MWI", "MLI", "MAR", "MOZ", "NGA", "SEN", "ZAF",
    "TZA", "TUN", "UGA", "ZMB", "ZWE", "GAB", "NAM", "NER",
]
_MIDDLE_EAST = ["SAU", "ARE", "IRN", "IRQ", "KWT", "QAT", "OMN", "BHR", "ISR", "JOR", "LBN", "SYR", "YEM"]
_EURASIA = ["RUS", "UKR", "KAZ", "UZB", "TKM", "AZE", "GEO", "ARM", "BLR", "MDA"]
_ASIA_PACIFIC = [
    "JPN", "KOR", "AUS", "NZL", "IND", "IDN", "THA", "VNM", "MYS", "PHL",
    "SGP", "BGD", "PAK", "LKA", "MMR", "NPL", "TWN", "MNG", "KHM", "LAO",
]

for _iso in _NORTH_AMERICA: _ISO3_TO_IEA_REGION[_iso] = "North America"
for _iso in _EUROPE: _ISO3_TO_IEA_REGION[_iso] = "Europe"
for _iso in _CSA: _ISO3_TO_IEA_REGION[_iso] = "Central & South America"
for _iso in _AFRICA: _ISO3_TO_IEA_REGION[_iso] = "Africa"
for _iso in _MIDDLE_EAST: _ISO3_TO_IEA_REGION[_iso] = "Middle East"
for _iso in _EURASIA: _ISO3_TO_IEA_REGION[_iso] = "Eurasia"
for _iso in _ASIA_PACIFIC: _ISO3_TO_IEA_REGION[_iso] = "Asia Pacific"
_ISO3_TO_IEA_REGION["CHN"] = "China"


# ---------------------------------------------------------------------------
# Tab definitions — order and labels
# ---------------------------------------------------------------------------

_TAB_DEFS = [
    ("tab-emissions",    "Emissions"),
    ("tab-energy-mix",   "Electricity Mix"),
    ("tab-renewables",   "Renewables"),
    ("tab-final-energy", "Final Energy Mix"),
    ("tab-methane",      "Methane & GHGs"),
    ("tab-investment",   "Investment"),
    ("tab-peers",        "Peer Comparison"),
]


# ---------------------------------------------------------------------------
# Page layout (called by Dash for every /country/<iso3> request)
# ---------------------------------------------------------------------------

def layout(iso3: str = "USA", **kwargs):
    """
    Render the country detail page.
    `iso3` is extracted from the URL path by Dash Pages.
    Only the header and tab skeleton are built here — tab content is loaded
    lazily via callback when a tab is selected.
    """
    iso3 = iso3.upper()

    # Validate ISO3 — return 404-style layout for unknown codes
    if not is_valid_iso3(iso3):
        return _invalid_country_layout(iso3)

    # Country metadata
    meta_df = get_country_meta()
    country_row = meta_df[meta_df["iso3"] == iso3].iloc[0]
    country_name = str(country_row["country_name"])
    continent = str(country_row.get("continent", ""))

    # Per-country time series (lightweight — just filtering cached DataFrames)
    emissions_df = get_country_emissions(iso3)
    mix_df = get_country_energy_mix(iso3)

    # Header stats + summary
    stats = _get_latest_stats(emissions_df, mix_df)
    summary = _build_summary(country_name, stats)

    # Build tab list (all tabs shown; content loaded lazily)
    tabs = [
        dbc.Tab(label=label, tab_id=tab_id)
        for tab_id, label in _TAB_DEFS
    ]

    return html.Div([
        # Store the ISO3 so the callback can access it
        dcc.Store(id="country-iso3-store", data=iso3),

        # =================================================================
        # Back button + header
        # =================================================================
        dbc.Container([
            dbc.Button(
                [html.I(className="bi bi-arrow-left me-2"), "Back to map"],
                href="/",
                color="outline-secondary",
                size="sm",
                className="mt-3 mb-3",
            ),

            # Country name + continent badge
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H1(country_name, className="display-6 fw-bold mb-0 d-inline me-2"),
                        dbc.Badge(continent, color="secondary", className="align-middle fs-6"),
                    ]),
                ], xs=12),
            ], className="mb-2"),

            # 5-stat header row
            _make_stats_row(stats),

            # Template-based summary paragraph
            html.P(summary, className="country-summary mt-3 mb-1"),

            html.Hr(className="mt-3 mb-0"),
        ], fluid=False),

        # =================================================================
        # Tabbed layout — content loaded lazily via callback
        # =================================================================
        dbc.Container([
            dbc.Tabs(
                id="country-tabs",
                active_tab="tab-emissions",
                className="country-tabs mt-3",
                children=tabs,
            ),
            # Tab content rendered here by the callback
            dcc.Loading(
                html.Div(id="country-tab-content", className="pb-4"),
                type="default",
                color="#2c3e50",
            ),
        ], fluid=False, className="pb-5"),

    ])  # end main Div


# ---------------------------------------------------------------------------
# Lazy tab callback — builds only the selected tab's content
# ---------------------------------------------------------------------------

def build_tab_content(active_tab: str, iso3: str):
    """Build and return the content for the selected tab. Called by app.callback."""
    if not active_tab or not iso3:
        return no_update

    iso3 = iso3.upper()
    if not is_valid_iso3(iso3):
        return html.P("Invalid country.", className="text-muted mt-3")

    meta_df = get_country_meta()
    country_row = meta_df[meta_df["iso3"] == iso3].iloc[0]
    country_name = str(country_row["country_name"])
    continent = str(country_row.get("continent", ""))

    if active_tab == "tab-emissions":
        return _build_emissions_tab(iso3, country_name)
    elif active_tab == "tab-energy-mix":
        return _build_energy_mix_tab(iso3, country_name)
    elif active_tab == "tab-renewables":
        return _build_renewables_tab(iso3, country_name)
    elif active_tab == "tab-final-energy":
        return _build_final_energy_tab(iso3, country_name)
    elif active_tab == "tab-methane":
        return _build_methane_tab(iso3, country_name)
    elif active_tab == "tab-investment":
        return _build_investment_tab(iso3, country_name)
    elif active_tab == "tab-peers":
        return _build_peers_tab(iso3, country_name, continent)
    else:
        return html.P("Select a tab.", className="text-muted mt-3")


# ---------------------------------------------------------------------------
# Tab content builders — each builds only 1-3 figures
# ---------------------------------------------------------------------------

def _build_emissions_tab(iso3, country_name):
    emissions_df = get_country_emissions(iso3)
    fig = emissions_time_series_with_scenarios(emissions_df, country_name, get_scenarios())
    if not fig.data:
        return html.P(f"No emissions data available for {country_name}.", className="text-muted mt-3")
    return html.Div([
        dcc.Graph(figure=fig, config=_GRAPH_CONFIG),
        dbc.Alert([
            html.Strong("What's shown: "),
            "Total GHG (CO₂, CH₄, N₂O, F-gases) expressed as CO₂e using AR6 "
            "GWP100 values (EDGAR). Fossil CO₂ shows combustion emissions only "
            "(Our World in Data / GCB). Sector-level breakdown coming in a future update.",
        ], color="light", className="small py-2 mt-3 border"),
    ], className="tab-content-inner mt-3")


def _build_energy_mix_tab(iso3, country_name):
    mix_df = get_country_energy_mix(iso3)
    area_fig = energy_mix_stacked_area(mix_df, country_name)
    donut_fig = energy_mix_donut(mix_df, country_name)
    if not area_fig.data:
        return html.P(f"No energy mix data available for {country_name}.", className="text-muted mt-3")
    return html.Div([
        dbc.Row([
            dbc.Col([dcc.Graph(figure=area_fig, config=_GRAPH_CONFIG)], xs=12, lg=8),
            dbc.Col([dcc.Graph(figure=donut_fig, config=_GRAPH_CONFIG)], xs=12, lg=4),
        ]),
        dbc.Alert([
            html.Strong("Note on renewable share: "),
            "The percentage shown here is renewables as a share of ",
            html.Em("electricity generation"),
            " (~30% globally). Renewables' share of all final energy "
            "consumption is ~13% — because electricity is only part of total "
            "energy use. Source: Our World in Data (Ember + BP Statistical Review).",
        ], color="light", className="small py-2 mt-3 border"),
    ], className="tab-content-inner mt-3")


def _build_renewables_tab(iso3, country_name):
    mix_df = get_country_energy_mix(iso3)
    fig = renewables_trend_chart(mix_df, country_name)
    if not fig.data:
        return html.P(f"No renewables data available for {country_name}.", className="text-muted mt-3")
    return html.Div([
        dcc.Graph(figure=fig, config=_GRAPH_CONFIG),
        dbc.Alert([
            html.Strong("Renewable share (left axis): "),
            "Share of total electricity generation from renewables (%). ",
            html.Strong("Solar and wind (right axis): "),
            "Actual generation in TWh/yr. Installed capacity data (GW by "
            "technology) will be added when IRENA IRENASTAT integration is complete.",
        ], color="light", className="small py-2 mt-3 border"),
    ], className="tab-content-inner mt-3")


def _build_final_energy_tab(iso3, country_name):
    mix_df = get_country_energy_mix(iso3)
    fig = final_energy_shares_chart(mix_df, country_name)
    if not fig.data:
        return html.P(f"No final energy data available for {country_name}.", className="text-muted mt-3")
    return html.Div([
        dcc.Graph(figure=fig, config=_GRAPH_CONFIG),
        dbc.Alert([
            html.Strong("Final energy vs electricity: "),
            "This chart shows renewables as a share of ",
            html.Em("total final energy consumption"),
            " (~13% globally) — which includes transport, industrial heat, "
            "and buildings. This is much lower than the ~30% renewable share "
            "of electricity alone, because electricity is only ~20% of total "
            "final energy use. Source: Our World in Data.",
        ], color="light", className="small py-2 mt-3 border"),
    ], className="tab-content-inner mt-3")


def _build_methane_tab(iso3, country_name):
    emissions_df = get_country_emissions(iso3)
    methane_fig = methane_trend_chart(emissions_df, country_name)
    methane_pc_fig = methane_per_capita_chart(emissions_df, country_name)
    children = []
    if methane_fig.data:
        children.append(dcc.Graph(figure=methane_fig, config=_GRAPH_CONFIG))
    if methane_pc_fig.data:
        children.append(dcc.Graph(figure=methane_pc_fig, config=_GRAPH_CONFIG, className="mt-3"))
    if not children:
        return html.P(f"No methane/GHG data available for {country_name}.", className="text-muted mt-3")
    children.append(dbc.Alert([
        html.Strong("Why methane matters: "),
        "CH₄ has a GWP-20 of ~80 — roughly 80× more potent than CO₂ over 20 years. "
        "It has a short atmospheric lifetime (~12 yr), so cutting methane delivers "
        "faster climate benefits than any other GHG reduction. N₂O (GWP-100: 273) "
        "primarily comes from agriculture and industrial processes. Values shown use "
        "GWP-100 weighting (AR6). Source: ",
        html.A("Our World in Data", href="https://github.com/owid/co2-data",
               target="_blank", className="alert-link"),
        " (compiled from EDGAR v8.0, PRIMAP-hist, CAIT/WRI). See the ",
        html.A("global Methane & GHGs page", href="/methane"),
        " for top emitters and sources breakdown.",
    ], color="light", className="small py-2 mt-3 border"))
    return html.Div(children, className="tab-content-inner mt-3")


def _build_investment_tab(iso3, country_name):
    iea_region = _ISO3_TO_IEA_REGION.get(iso3, "")
    investment_df = get_investment()
    all_subsidies = get_subsidies()
    country_subs = all_subsidies[all_subsidies["iso3"] == iso3] if not all_subsidies.empty else pd.DataFrame()
    sub_indicators = get_subsidy_indicators()
    country_indicators = sub_indicators[sub_indicators["iso3"] == iso3] if not sub_indicators.empty else pd.DataFrame()

    children = []
    if iea_region:
        region_inv_fig = regional_investment_chart(investment_df, iea_region)
        children.extend([
            html.H6(f"Energy Investment: {iea_region}", className="fw-bold mb-1"),
            dcc.Graph(figure=region_inv_fig, config=_GRAPH_CONFIG),
        ])
    if not country_subs.empty:
        subsidy_fig = country_subsidies_chart(country_subs, country_name)
        children.extend([
            html.H6(f"{country_name}: Fossil Fuel Subsidies", className="fw-bold mt-4 mb-1"),
            dcc.Graph(figure=subsidy_fig, config=_GRAPH_CONFIG),
            *_build_subsidy_indicators_card(country_indicators, country_name),
        ])
    else:
        children.append(html.Div([
            html.H6("Fossil Fuel Subsidies", className="fw-bold mt-4 mb-1"),
            html.P(f"No fossil fuel subsidy data available for {country_name} "
                   "in the IEA database. This typically means subsidies are minimal "
                   "or the country is not covered.", className="text-muted small"),
        ]))

    if not children:
        return html.P("No investment data available.", className="text-muted mt-3")

    children.append(dbc.Alert([
        html.Strong("Sources: "),
        "Investment: ",
        html.A("IEA World Energy Investment 2025",
               href="https://www.iea.org/reports/world-energy-investment-2025",
               target="_blank", className="alert-link"),
        " (regional data, 2024 real USD). Subsidies: ",
        html.A("IEA Fossil Fuel Subsidies Database",
               href="https://www.iea.org/data-and-statistics/data-product/fossil-fuel-subsidies-database",
               target="_blank", className="alert-link"),
        " (explicit subsidies only, 2024 real USD).",
    ], color="light", className="small py-2 mt-3 border"))
    return html.Div(children, className="tab-content-inner mt-3")


def _build_peers_tab(iso3, country_name, continent):
    meta_df = get_country_meta()
    fig = peer_comparison_bars(
        iso3, country_name, continent,
        get_emissions(), get_energy_mix(), meta_df,
    )
    if not fig.data:
        return html.P(f"No peer comparison data available for {country_name}.", className="text-muted mt-3")
    return html.Div([
        dcc.Graph(figure=fig, config=_GRAPH_CONFIG),
        dbc.Alert([
            html.Strong("Comparison group: "),
            f"Global average, {continent} regional average, and the top 5 "
            "global emitters by total GHG. Latest available year per country. "
            "The selected country's bar is highlighted.",
        ], color="light", className="small py-2 mt-3 border"),
    ], className="tab-content-inner mt-3")


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def _get_latest_stats(emissions_df: pd.DataFrame, mix_df: pd.DataFrame) -> dict:
    """Extract latest-year key stats from country DataFrames for the header row."""
    stats: dict = {}

    if not emissions_df.empty and "year" in emissions_df.columns:
        latest = emissions_df.sort_values("year").iloc[-1]
        stats["ghg_total_mtco2e"] = latest.get("ghg_total_mtco2e")
        stats["co2_per_capita_t"] = latest.get("co2_per_capita_t")
        stats["year"]            = int(latest["year"])

        # Population and GDP: use latest non-null value (may lag by 1-2 years)
        for col in ("population", "gdp_usd"):
            col_series = emissions_df.sort_values("year")[col].dropna()
            stats[col] = col_series.iloc[-1] if not col_series.empty else None

        # GHG value ~10 years prior for trend sentence
        year_now = stats["year"]
        prev_year = year_now - 10
        prev_rows = emissions_df[emissions_df["year"] == prev_year]
        if not prev_rows.empty:
            stats["ghg_prev"]  = prev_rows.iloc[0].get("ghg_total_mtco2e")
            stats["prev_year"] = prev_year

    if not mix_df.empty and "year" in mix_df.columns:
        latest = mix_df.sort_values("year").iloc[-1]
        stats["renewable_pct"] = latest.get("renewable_share_electricity_pct")
        stats["mix_year"]      = int(latest["year"])

        # Carbon intensity (gCO2/kWh) — latest non-null value
        if "carbon_intensity_gco2_kwh" in mix_df.columns:
            ci_series = mix_df.sort_values("year")["carbon_intensity_gco2_kwh"].dropna()
            if not ci_series.empty:
                stats["carbon_intensity"] = float(ci_series.iloc[-1])

    return stats


def _build_summary(country_name: str, stats: dict) -> str:
    """
    Build a 2-3 sentence template-based summary of the country's energy
    transition status. Generated at page render time from data; not AI-generated.
    """
    renewable_pct = stats.get("renewable_pct")
    ghg_latest    = stats.get("ghg_total_mtco2e")
    ghg_prev      = stats.get("ghg_prev")
    year          = stats.get("year", 2023)
    prev_year     = stats.get("prev_year", year - 10)
    co2_pc        = stats.get("co2_per_capita_t")

    # -- Sentence 1: Renewables context --
    s1 = ""
    if renewable_pct is not None and not pd.isna(renewable_pct):
        r = float(renewable_pct)
        if r >= 80:
            s1 = (
                f"{country_name} has achieved an exceptionally high renewable "
                f"electricity share at {r:.0f}%, largely from hydro and/or "
                f"wind/solar resources."
            )
        elif r >= 50:
            s1 = (
                f"{country_name} generates over half its electricity from "
                f"renewables ({r:.0f}%), a strong foundation for decarbonization."
            )
        elif r >= 20:
            s1 = (
                f"{country_name} generates {r:.0f}% of its electricity from "
                f"renewables, with significant room to expand."
            )
        else:
            s1 = (
                f"{country_name}'s electricity system is predominantly fossil fuel-based, "
                f"with renewables accounting for {r:.0f}% of generation."
            )
    else:
        s1 = f"Renewable electricity generation data for {country_name} is limited."

    # -- Sentence 2: GHG trend --
    s2 = ""
    if (ghg_latest is not None and ghg_prev is not None
            and not pd.isna(ghg_latest) and not pd.isna(ghg_prev) and ghg_prev > 0):
        pct_change = (ghg_latest - ghg_prev) / ghg_prev * 100
        if pct_change < -20:
            s2 = f"GHG emissions have fallen sharply — down {abs(pct_change):.0f}% since {prev_year}."
        elif pct_change < -5:
            s2 = f"GHG emissions have declined by {abs(pct_change):.0f}% since {prev_year}."
        elif pct_change <= 5:
            s2 = f"GHG emissions have been roughly stable since {prev_year}."
        elif pct_change <= 20:
            s2 = (
                f"GHG emissions have grown by {pct_change:.0f}% since {prev_year}, "
                f"driven largely by economic expansion."
            )
        else:
            s2 = f"GHG emissions have grown sharply — up {pct_change:.0f}% since {prev_year}."
    else:
        s2 = "Emissions trend data across the past decade is limited."

    # -- Sentence 3: per-capita context --
    s3 = ""
    if co2_pc is not None and not (isinstance(co2_pc, float) and pd.isna(co2_pc)):
        co2_pc_f = float(co2_pc)
        if co2_pc_f > _GLOBAL_CO2_PC_AVG * 2:
            s3 = (
                f"At {co2_pc_f:.1f} t of fossil CO₂ per person annually, "
                f"emissions are more than double the global average of ~{_GLOBAL_CO2_PC_AVG} t."
            )
        elif co2_pc_f > _GLOBAL_CO2_PC_AVG * 1.2:
            s3 = (
                f"Fossil CO₂ per capita stands at {co2_pc_f:.1f} t/yr — "
                f"above the global average of ~{_GLOBAL_CO2_PC_AVG} t."
            )
        elif co2_pc_f > _GLOBAL_CO2_PC_AVG * 0.8:
            s3 = (
                f"At {co2_pc_f:.1f} t of fossil CO₂ per person per year, "
                f"emissions are near the global average of ~{_GLOBAL_CO2_PC_AVG} t."
            )
        else:
            s3 = (
                f"With {co2_pc_f:.1f} t of fossil CO₂ per person per year, "
                f"emissions are below the global average of ~{_GLOBAL_CO2_PC_AVG} t."
            )

    return " ".join(p for p in [s1, s2, s3] if p)


# ---------------------------------------------------------------------------
# Cost tab helpers
# ---------------------------------------------------------------------------

def _get_country_carbon_price(iso3: str):
    """
    Return the carbon price (USD/tCO₂) for a country, or None if not available.
    Looks for the most recent row with a non-null carbon_price_usd_tco2.
    """
    df = get_country_finance(iso3)
    if df.empty or "carbon_price_usd_tco2" not in df.columns:
        return None
    series = df["carbon_price_usd_tco2"].dropna()
    return float(series.iloc[-1]) if not series.empty else None


def _build_country_cost_fig():
    """Build the LCOE cost revolution figure (same global data shown for every country)."""
    try:
        return cost_revolution(get_costs())
    except Exception as exc:
        return placeholder_figure(f"LCOE chart unavailable: {exc}")


def _build_subsidy_indicators_card(indicators_df, country_name: str) -> list:
    """Build subsidy indicators (rate, per capita, GDP share) as small stat cards."""
    if indicators_df.empty:
        return []

    row = indicators_df.iloc[0]

    rate = row.get("subsidy_rate_pct")
    per_cap = row.get("subsidy_per_capita_usd")
    gdp_share = row.get("subsidy_gdp_share_pct")

    items = []
    if rate is not None and pd.notna(rate):
        items.append(("Subsidization rate", f"{rate:.1f}%", "Average price gap vs international reference"))
    if per_cap is not None and pd.notna(per_cap):
        items.append(("Subsidy per capita", f"${per_cap:.0f}/person", "Annual fossil fuel subsidy per person"))
    if gdp_share is not None and pd.notna(gdp_share):
        items.append(("Share of GDP", f"{gdp_share:.1f}%", "Total fossil fuel subsidies as % of GDP"))

    if not items:
        return []

    cols = []
    for label, value, desc in items:
        cols.append(
            dbc.Col(
                dbc.Card(dbc.CardBody([
                    html.Small(label, className="text-muted d-block"),
                    html.Div(value, className="fs-5 fw-bold"),
                    html.Small(desc, className="text-muted", style={"fontSize": "0.7rem"}),
                ], className="py-2 px-3"), className="country-stat-card h-100"),
                xs=12, sm=4, className="mb-2",
            )
        )

    return [
        html.H6("Subsidy Indicators (2024)", className="fw-bold mt-3 mb-2"),
        dbc.Row(cols, className="g-2"),
    ]


def _build_carbon_price_card(iso3: str, country_name: str, price):
    """Build the carbon pricing status card for a country."""
    if price is not None and price > 0:
        badge_color = "success" if price >= 40 else ("warning" if price >= 10 else "secondary")
        if price >= 100:
            context = "High — consistent with cost of carbon damage estimates."
        elif price >= 40:
            context = "Moderate — approaching the range economists consider effective."
        elif price >= 10:
            context = "Low — below levels considered sufficient for deep decarbonization."
        else:
            context = "Very low — largely symbolic; insufficient for material emissions reduction."

        card_body = dbc.CardBody([
            html.Div([
                html.I(className="bi bi-tags-fill me-2 text-success"),
                html.Strong("Carbon Pricing"),
            ], className="d-flex align-items-center mb-2"),
            html.Div([
                dbc.Badge(f"${price:.0f} /tCO₂", color=badge_color, className="fs-5 me-2"),
                html.Small("(effective price, 2023)", className="text-muted"),
            ], className="mb-1"),
            html.P(context, className="small text-muted mb-0"),
        ])
        return dbc.Card(card_body, className="border-success mb-3")
    else:
        card_body = dbc.CardBody([
            html.Div([
                html.I(className="bi bi-x-circle me-2 text-secondary"),
                html.Strong("No national carbon price"),
            ], className="d-flex align-items-center mb-2"),
            html.P(
                f"{country_name} does not have a national carbon pricing scheme "
                "(ETS or carbon tax) as of 2023. Some regions or sectors may have "
                "sub-national or sectoral pricing.",
                className="small text-muted mb-0",
            ),
        ])
        return dbc.Card(card_body, className="border-secondary mb-3")


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------

def _make_stats_row(stats: dict) -> dbc.Row:
    """Build the 5-card header stats row."""
    year     = stats.get("year", "")
    mix_year = stats.get("mix_year", year)

    ci = stats.get("carbon_intensity")
    ci_str = f"{ci:.0f} gCO₂/kWh" if ci is not None else "N/A"

    items = [
        ("Population",       _fmt_population(stats.get("population")),      "",                      "bi bi-people-fill"),
        ("Total GHG",        _fmt_ghg(stats.get("ghg_total_mtco2e")),       f"({year})",              "bi bi-cloud-fill"),
        ("Fossil CO₂/capita", _fmt_co2pc(stats.get("co2_per_capita_t")),   f"({year})",              "bi bi-person-fill"),
        ("Grid carbon intensity", ci_str,                                   f"({mix_year})",          "bi bi-lightning-charge-fill"),
        ("Renewable share",  _fmt_pct(stats.get("renewable_pct")),          f"of electricity ({mix_year})", "bi bi-lightning-fill"),
    ]

    cols = []
    for label, value, note, icon in items:
        cols.append(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.Div([
                            html.I(className=f"{icon} me-1 text-primary small"),
                            html.Small(label, className="text-muted"),
                        ], className="d-flex align-items-center"),
                        html.Div(value, className="fs-5 fw-bold mt-1 lh-1"),
                        html.Small(note, className="text-muted") if note else None,
                    ], className="py-2 px-3"),
                    className="country-stat-card h-100",
                ),
                xs=6, sm=4, md=True,
                className="mb-2",
            )
        )

    return dbc.Row(cols, className="g-2 mt-1")


def _make_health_stats_row(health_df: pd.DataFrame, country_name: str) -> dbc.Row:
    """
    Build a 3-card summary row for the Health tab header.
    Cards: latest PM2.5 exposure, fossil fuel PM2.5 deaths, deaths/TWh.
    All values from health.parquet (latest available year per metric).
    """
    def _latest(col):
        if health_df.empty or col not in health_df.columns:
            return None, None
        series = health_df.sort_values("year")[[col, "year"]].dropna(subset=[col])
        if series.empty:
            return None, None
        return float(series[col].iloc[-1]), int(series["year"].iloc[-1])

    pm25, pm25_yr      = _latest("pm25_annual_mean_ugm3")
    fossil_d, fossil_yr = _latest("fossil_fuel_deaths")
    dptwh, dptwh_yr    = _latest("deaths_per_twh_energy_mix")

    def _pm25_badge(val):
        if val is None:
            return dbc.Badge("N/A", color="secondary")
        if val <= 5:
            return dbc.Badge(f"{val:.1f} μg/m³", color="success")
        if val <= 15:
            return dbc.Badge(f"{val:.1f} μg/m³", color="warning")
        return dbc.Badge(f"{val:.1f} μg/m³", color="danger")

    cards = [
        # PM2.5 exposure
        dbc.Col(
            dbc.Card(dbc.CardBody([
                html.Div([
                    html.I(className="bi bi-cloud-haze2-fill me-1 text-secondary small"),
                    html.Small("Annual mean PM2.5 (all sources)", className="text-muted"),
                ], className="d-flex align-items-center"),
                html.Div(_pm25_badge(pm25), className="mt-1"),
                html.Small(
                    f"({pm25_yr}) WHO guideline: 5 μg/m³" if pm25_yr else "No data",
                    className="text-muted",
                ),
            ], className="py-2 px-3"), className="country-stat-card h-100"),
            xs=12, sm=6, md=3, className="mb-2",
        ),
        # Fossil fuel PM2.5 deaths (from McDuffie et al.)
        dbc.Col(
            dbc.Card(dbc.CardBody([
                html.Div([
                    html.I(className="bi bi-heart-pulse-fill me-1 text-danger small"),
                    html.Small("Fossil fuel PM2.5 deaths", className="text-muted"),
                ], className="d-flex align-items-center"),
                html.Div(
                    f"{fossil_d:.1f}K/yr" if fossil_d is not None else "N/A",
                    className="fs-5 fw-bold mt-1 text-danger",
                ),
                html.Small(
                    f"({fossil_yr}) McDuffie et al. 2021" if fossil_yr else "No data",
                    className="text-muted",
                ),
            ], className="py-2 px-3"), className="country-stat-card h-100"),
            xs=12, sm=6, md=3, className="mb-2",
        ),
        # Deaths/TWh energy mix
        dbc.Col(
            dbc.Card(dbc.CardBody([
                html.Div([
                    html.I(className="bi bi-activity me-1 text-primary small"),
                    html.Small([
                        html.Abbr(
                            "Deaths/TWh",
                            title="Estimated deaths per TWh of electricity generated, based on this country's energy mix and OWID reference mortality rates. Comparative order of magnitude only — not a precision estimate.",
                        ),
                        " (elec. mix)",
                    ], className="text-muted"),
                ], className="d-flex align-items-center"),
                html.Div(
                    f"{dptwh:.2f}" if dptwh is not None else "N/A",
                    className="fs-5 fw-bold mt-1",
                ),
                html.Small(
                    f"({dptwh_yr}) electricity generation only" if dptwh_yr else "Order-of-magnitude only",
                    className="text-muted",
                ),
            ], className="py-2 px-3"), className="country-stat-card h-100"),
            xs=12, sm=6, md=3, className="mb-2",
        ),
    ]
    return dbc.Row(cards, className="g-2 mt-1")


def _invalid_country_layout(iso3: str) -> html.Div:
    """404-style layout for unrecognized ISO3 codes."""
    return html.Div([
        dbc.Container([
            dbc.Button(
                [html.I(className="bi bi-arrow-left me-2"), "Back to map"],
                href="/",
                color="outline-secondary",
                size="sm",
                className="mt-3 mb-4",
            ),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H2("Country not found", className="fw-bold text-danger mb-2"),
                            html.P([
                                "No data found for ISO3 code: ",
                                html.Code(iso3, className="fs-5 ms-1"),
                            ], className="mb-2"),
                            html.P(
                                "Valid examples: USA, CHN, GBR, DEU, IND, AUS. "
                                "Return to the map and click a country to navigate here.",
                                className="text-muted",
                            ),
                            dbc.Button(
                                "← Return to map", href="/", color="primary", className="mt-2",
                            ),
                        ])
                    ], className="border-danger"),
                ], md=7),
            ]),
        ]),
    ])


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _fmt_population(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "N/A"
    v = float(val)
    if v >= 1e9:
        return f"{v / 1e9:.2g}B"
    if v >= 1e6:
        return f"{v / 1e6:.0f}M"
    return f"{v / 1e3:.0f}K"


def _fmt_gdp(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "N/A"
    v = float(val)
    if v >= 1e12:
        return f"${v / 1e12:.2g}T"
    if v >= 1e9:
        return f"${v / 1e9:.0f}B"
    return f"${v / 1e6:.0f}M"


def _fmt_ghg(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "N/A"
    v = float(val)
    if v >= 1000:
        return f"{v / 1000:.2g} GtCO₂e"
    return f"{v:.0f} MtCO₂e"


def _fmt_co2pc(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "N/A"
    return f"{float(val):.1f} t/yr"


def _fmt_pct(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "N/A"
    return f"{float(val):.1f}%"
