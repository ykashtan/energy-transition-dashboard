"""
app.py — Entry point for the Energy Transition Dashboard (Dash).

Performance strategy:
  - All Parquet files are pre-loaded at startup via data_loader.preload_all().
  - Homepage KPIs are read from kpis.json only — no Parquet reads per request.
  - clientside_callback is used for all interactions that don't require new server data.

Deployment:
  - Local: python app.py
  - Render.com / Hugging Face: gunicorn app:server (see Procfile)
"""

import dash
import dash_bootstrap_components as dbc

# Pre-load all data files at startup (not per-request)
from utils.data_loader import preload_all, get_country_meta
from components.world_map import build_map_figure

# Initialize the Dash app
# - use_pages=True enables Dash Pages (multi-page routing via pages/ directory)
# - FLATLY theme: clean, professional, good contrast
# - Bootstrap Icons CDN added via external_stylesheets
app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[
        dbc.themes.FLATLY,
        dbc.icons.BOOTSTRAP,   # Bootstrap Icons (bi-* classes for info icons etc.)
    ],
    # Improve SEO and accessibility
    title="Energy Transition Dashboard",
    update_title=None,
    # Suppress callback exceptions — country pages use dynamic routes
    suppress_callback_exceptions=True,
    # Meta tags for mobile responsiveness (critical — without this, mobile layout breaks)
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
        {"name": "description", "content": (
            "A birds-eye view of the global energy transition: emissions, renewables, "
            "costs, investment, and health impacts."
        )},
    ],
)

# gunicorn needs access to the Flask server object
server = app.server

# Navigation bar
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Home", href="/")),
        dbc.NavItem(dbc.NavLink("Spotlights", href="/spotlight")),
        dbc.NavItem(dbc.NavLink("Tipping Points", href="/tipping-points")),
        dbc.NavItem(dbc.NavLink("Trajectories", href="/trajectories")),
        dbc.NavItem(dbc.NavLink("Compare", href="/compare")),
        dbc.NavItem(dbc.NavLink("Methodology", href="/methodology")),
    ],
    brand="Energy Transition Dashboard",
    brand_href="/",
    color="primary",
    dark=True,
    fluid=True,
    className="mb-0",
    id="main-navbar",
)

# App layout: navbar + page container
# dash.page_container renders the active page's layout() function
app.layout = dbc.Container(
    [
        navbar,
        dash.page_container,
    ],
    fluid=True,
    className="px-0",
)


# ---------------------------------------------------------------------------
# clientside_callback: map theme button active state
# ---------------------------------------------------------------------------
# This runs entirely in the browser — no server round-trip on button clicks.
# Pattern: update the "active" class on map theme buttons based on which was clicked.

app.clientside_callback(
    """
    function() {
        const triggered = dash_clientside.callback_context.triggered;
        const buttons = [
            "map-btn-emissions", "map-btn-renewables", "map-btn-total-energy",
            "map-btn-costs", "map-btn-health", "map-btn-damages", "map-btn-vulnerability"
        ];
        if (!triggered || triggered.length === 0) {
            return buttons.map((id, i) => i === 0 ? "map-theme-btn active" : "map-theme-btn");
        }
        const triggeredId = triggered[0].prop_id.split(".")[0];
        return buttons.map(id =>
            id === triggeredId ? "map-theme-btn active" : "map-theme-btn"
        );
    }
    """,
    [
        dash.Output("map-btn-emissions", "className"),
        dash.Output("map-btn-renewables", "className"),
        dash.Output("map-btn-total-energy", "className"),
        dash.Output("map-btn-costs", "className"),
        dash.Output("map-btn-health", "className"),
        dash.Output("map-btn-damages", "className"),
        dash.Output("map-btn-vulnerability", "className"),
    ],
    [
        dash.Input("map-btn-emissions", "n_clicks"),
        dash.Input("map-btn-renewables", "n_clicks"),
        dash.Input("map-btn-total-energy", "n_clicks"),
        dash.Input("map-btn-costs", "n_clicks"),
        dash.Input("map-btn-health", "n_clicks"),
        dash.Input("map-btn-damages", "n_clicks"),
        dash.Input("map-btn-vulnerability", "n_clicks"),
    ],
    prevent_initial_call=True,
)


# ---------------------------------------------------------------------------
# clientside_callback: update URL search param when a map theme button is clicked
# ---------------------------------------------------------------------------
# This writes ?metric=<key> into the URL so the link is shareable.
# Runs in the browser — no server round-trip.

app.clientside_callback(
    """
    function() {
        const ctx = dash_clientside.callback_context;
        if (!ctx || !ctx.triggered || ctx.triggered.length === 0) {
            return window.location.search || "?metric=emissions";
        }
        const id_to_key = {
            "map-btn-emissions":     "emissions",
            "map-btn-renewables":    "renewables",
            "map-btn-total-energy":  "total_energy",
            "map-btn-costs":         "cost",
            "map-btn-health":        "health",
            "map-btn-damages":       "damages",
            "map-btn-vulnerability": "vulnerability"
        };
        const triggeredId = ctx.triggered[0].prop_id.split(".")[0];
        const key = id_to_key[triggeredId] || "emissions";
        return "?metric=" + key;
    }
    """,
    dash.Output("home-loc", "search"),
    [
        dash.Input("map-btn-emissions", "n_clicks"),
        dash.Input("map-btn-renewables", "n_clicks"),
        dash.Input("map-btn-total-energy", "n_clicks"),
        dash.Input("map-btn-costs", "n_clicks"),
        dash.Input("map-btn-health", "n_clicks"),
        dash.Input("map-btn-damages", "n_clicks"),
        dash.Input("map-btn-vulnerability", "n_clicks"),
    ],
    prevent_initial_call=False,
)


# ---------------------------------------------------------------------------
# Server callback: build choropleth figure based on active metric (from URL)
# ---------------------------------------------------------------------------
# Reads ?metric=<key> from the URL search string and returns the correct figure.
# Data is already in memory (pre-loaded at startup) — figure build is fast.

@app.callback(
    dash.Output("world-map", "figure"),
    dash.Output("map-methodology-bar", "children"),
    dash.Input("home-loc", "search"),
    prevent_initial_call=False,
)
def update_map_figure(search: str):
    """Build and return the choropleth figure + methodology description."""
    from dash import html
    # Parse ?metric=<key> from search string
    metric_key = "emissions"
    if search:
        import urllib.parse
        params = urllib.parse.parse_qs(search.lstrip("?"))
        metric_key = params.get("metric", ["emissions"])[0]

    valid_keys = {"emissions", "renewables", "total_energy", "cost", "health", "investment", "damages", "vulnerability"}
    if metric_key not in valid_keys:
        metric_key = "emissions"

    country_meta = get_country_meta()
    fig = build_map_figure(metric_key, country_meta)

    # Build methodology bar from METRIC_REGISTRY
    from components.world_map import METRIC_REGISTRY
    cfg = METRIC_REGISTRY.get(metric_key, METRIC_REGISTRY["emissions"])
    desc = cfg.get("description", "")
    source_url = cfg.get("source_url", "")
    methodology_bar = [
        html.Strong(f"{cfg.get('label', '')}: "),
        desc,
        " ",
        html.A("Source →", href=source_url, target="_blank",
               className="text-primary", style={"textDecoration": "none"})
        if source_url else "",
    ]

    return fig, methodology_bar


# ---------------------------------------------------------------------------
# clientside_callback: map click → navigate to country page
# ---------------------------------------------------------------------------
# When the user clicks a country on the choropleth, extract the ISO3 code
# and navigate to /country/<iso3>. Runs in browser — no server round-trip.

app.clientside_callback(
    """
    function(clickData) {
        if (!clickData || !clickData.points || clickData.points.length === 0) {
            return dash_clientside.no_update;
        }
        const iso3 = clickData.points[0].location;
        if (!iso3) {
            return dash_clientside.no_update;
        }
        // Navigate to country detail page
        window.location.href = "/country/" + iso3;
        return dash_clientside.no_update;
    }
    """,
    dash.Output("home-loc", "pathname"),
    dash.Input("world-map", "clickData"),
    prevent_initial_call=True,
)


# ---------------------------------------------------------------------------
# Homepage callbacks (registered here because Dash 4.x Pages `dash.callback`
# does not auto-register; app.callback is required)
# ---------------------------------------------------------------------------

from pages.home import (
    toggle_hero_modal,
    switch_emissions_chart, switch_energy_chart,
    switch_investment_chart, switch_predictions_chart,
    switch_health_chart, switch_electrification_chart,
    EMISSIONS_SECTION_KEYS, ENERGY_SECTION_KEYS,
    INVESTMENT_SECTION_KEYS, PREDICTIONS_SECTION_KEYS,
    HEALTH_SECTION_KEYS,
    ELECTRIFICATION_CARD_IDS, ELECTRIFICATION_BTN_IDS,
)
from components.kpi_card import HERO_KEYS

# Hero card clicks → open modal with historical trendline
for _hero_key in HERO_KEYS:
    app.callback(
        dash.Output(f"hero-modal-{_hero_key}", "is_open"),
        dash.Input(f"hero-card-{_hero_key}", "n_clicks"),
        dash.State(f"hero-modal-{_hero_key}", "is_open"),
        prevent_initial_call=True,
    )(toggle_hero_modal)

# Section card clicks → switch section charts
app.callback(
    dash.Output("emissions-section-figure", "figure"),
    [dash.Input(f"section-card-emissions-{k}", "n_clicks") for k in EMISSIONS_SECTION_KEYS]
    + [dash.Input("emissions-reset-btn", "n_clicks")],
    prevent_initial_call=True,
)(switch_emissions_chart)

app.callback(
    dash.Output("energy-section-figure", "figure"),
    [
        dash.Input("energy-gen-solar", "n_clicks"),
        dash.Input("energy-gen-wind", "n_clicks"),
        dash.Input("energy-gen-hydro", "n_clicks"),
        dash.Input("energy-gen-gas", "n_clicks"),
        dash.Input("energy-gen-coal", "n_clicks"),
        dash.Input("energy-gen-nuclear", "n_clicks"),
        dash.Input("energy-reset-btn", "n_clicks"),
    ],
    prevent_initial_call=True,
)(switch_energy_chart)

app.callback(
    dash.Output("investment-section-figure", "figure"),
    [dash.Input(f"section-card-investment-{k}", "n_clicks") for k in INVESTMENT_SECTION_KEYS]
    + [
        dash.Input("inv-card-clean", "n_clicks"),
        dash.Input("inv-card-fossil", "n_clicks"),
        dash.Input("inv-card-share", "n_clicks"),
        dash.Input("inv-card-regional", "n_clicks"),
    ],
    prevent_initial_call=True,
)(switch_investment_chart)

app.callback(
    dash.Output("predictions-section-figure", "figure"),
    [dash.Input(f"section-card-predictions-{k}", "n_clicks") for k in PREDICTIONS_SECTION_KEYS]
    + [
        dash.Input("home-pred-btn-solar", "n_clicks"),
        dash.Input("home-pred-btn-wind", "n_clicks"),
        dash.Input("home-pred-btn-ccs", "n_clicks"),
    ],
    prevent_initial_call=True,
)(switch_predictions_chart)

app.callback(
    dash.Output("health-section-figure", "figure"),
    [dash.Input(f"section-card-health-{k}", "n_clicks") for k in HEALTH_SECTION_KEYS],
    prevent_initial_call=True,
)(switch_health_chart)

app.callback(
    dash.Output("electrification-section-figure", "figure"),
    [dash.Input(cid, "n_clicks") for cid in ELECTRIFICATION_CARD_IDS]
    + [dash.Input(bid, "n_clicks") for bid in ELECTRIFICATION_BTN_IDS],
    prevent_initial_call=True,
)(switch_electrification_chart)


# ---------------------------------------------------------------------------
# Country page: lazy tab loading callback
# ---------------------------------------------------------------------------
from pages.country import build_tab_content

app.callback(
    dash.Output("country-tab-content", "children"),
    dash.Input("country-tabs", "active_tab"),
    dash.Input("country-iso3-store", "data"),
)(build_tab_content)


# ---------------------------------------------------------------------------
# Technology Trajectories page: scenario explorer callback
# ---------------------------------------------------------------------------
# Wired in Phase 2 — trajectory_scenario_figure callback goes here

try:
    from pages.trajectories import update_trajectory_figure
    app.callback(
        dash.Output("trajectory-scenario-figure", "figure"),
        dash.Input("trajectory-tech-selector", "value"),
        prevent_initial_call=True,
    )(update_trajectory_figure)
except (ImportError, Exception):
    pass  # Page not yet built — skip


# ---------------------------------------------------------------------------
# Country Comparison page: update comparison callback
# ---------------------------------------------------------------------------
# Wired in Phase 2 — comparison callback goes here

try:
    from pages.compare import update_comparison
    app.callback(
        dash.Output("compare-content", "children"),
        [dash.Input(f"compare-country-{i}", "value") for i in range(4)],
        prevent_initial_call=True,
    )(update_comparison)
except (ImportError, Exception):
    pass  # Page not yet built — skip


# ---------------------------------------------------------------------------
# Download CSV: pattern-matching callback for all download buttons
# ---------------------------------------------------------------------------

try:
    from components.download_button import csv_with_header
    from utils.data_loader import (
        get_emissions, get_energy_mix, get_capacity, get_health,
        get_investment, get_vulnerability,
    )

    _DOWNLOAD_REGISTRY = {
        "emissions": ("emissions", get_emissions, "Global Carbon Budget / OWID", "CC-BY 4.0"),
        "energy_mix": ("energy_mix", get_energy_mix, "Our World in Data", "CC-BY 4.0"),
        "capacity": ("capacity", get_capacity, "IRENA / OWID", "CC-BY 4.0"),
        "health": ("health", get_health, "IHME GBD 2023", "CC-BY 4.0"),
        "investment": ("investment", get_investment, "IEA World Energy Investment 2025", "See IEA for terms"),
        "vulnerability": ("vulnerability", get_vulnerability, "ND-GAIN", "CC-BY 4.0"),
    }

    @app.callback(
        dash.Output({"type": "download-csv", "index": dash.MATCH}, "data"),
        dash.Input({"type": "download-btn", "index": dash.MATCH}, "n_clicks"),
        dash.State({"type": "download-data-key", "index": dash.MATCH}, "data"),
        prevent_initial_call=True,
    )
    def download_csv(n_clicks, data_key):
        if not n_clicks or data_key not in _DOWNLOAD_REGISTRY:
            return dash.no_update
        name, getter, source, license_info = _DOWNLOAD_REGISTRY[data_key]
        df = getter()
        if df.empty:
            return dash.no_update
        return csv_with_header(df, f"{name}.csv", source, license_info)
except (ImportError, Exception):
    pass


# ---------------------------------------------------------------------------
# Pre-load data at import time (works for both `python app.py` AND gunicorn)
# ---------------------------------------------------------------------------
preload_all()


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os

    # Run the development server
    # debug=True enables hot reload and error messages
    # For production, gunicorn handles this (see Procfile)
    # use_reloader=False avoids orjson circular-import bug in Dash 4.x debug mode
    port = int(os.environ.get("PORT", 8050))
    app.run(debug=True, host="0.0.0.0", port=port, use_reloader=False)
