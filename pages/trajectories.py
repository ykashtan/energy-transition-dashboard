"""
trajectories.py -- Technology Trajectories page.

S-curve adoption analysis and scenario exploration for clean energy technologies.
Shows historical adoption curves with fitted logistic overlays, a "5-to-50" speed
comparison, scenario projections, and expert forecast consensus.
"""

import dash
from dash import html, dcc, callback_context
import dash_bootstrap_components as dbc

from utils.chart_styles import (
    CHART_FONT, CHART_MARGIN, PAPER_BG, PLOT_BG, GRID_COLOR, GRAPH_CONFIG,
    GREEN, YELLOW, RED, BLUE, GRAY, PRIMARY,
)
from utils.data_loader import (
    get_ev_sales_share, get_energy_mix,
    get_scurve_params, get_nascent_tech_data, get_expert_forecasts,
    get_temperature_trajectory,
)
from components.scurve_charts import (
    historical_scurve_gallery, five_to_fifty_chart,
    trajectory_scenario_figure, expert_consensus_chart,
    temperature_trajectory_chart,
)


dash.register_page(
    __name__,
    path="/trajectories",
    title="Technology Trajectories \u2014 Energy Transition Dashboard",
    description="S-curve adoption analysis and scenario exploration for clean energy technologies.",
)


# ---------------------------------------------------------------------------
# Module-level figure cache (built once on first request)
# ---------------------------------------------------------------------------

_GALLERY_CACHE = None
_FIVE_TO_FIFTY_CACHE = None
_EXPERT_CHARTS_CACHE = None
_TEMP_CHART_CACHE = None


def _ensure_gallery():
    """Build gallery figures once, then cache."""
    global _GALLERY_CACHE
    if _GALLERY_CACHE is None:
        ev_df = get_ev_sales_share()
        mix_df = get_energy_mix()
        params = get_scurve_params()
        _GALLERY_CACHE = historical_scurve_gallery(ev_df, mix_df, params)
    return _GALLERY_CACHE


def _ensure_five_to_fifty():
    """Build five-to-fifty chart once, then cache."""
    global _FIVE_TO_FIFTY_CACHE
    if _FIVE_TO_FIFTY_CACHE is None:
        ev_df = get_ev_sales_share()
        _FIVE_TO_FIFTY_CACHE = five_to_fifty_chart(ev_df)
    return _FIVE_TO_FIFTY_CACHE


def _ensure_expert_charts():
    """Build expert consensus charts once, then cache."""
    global _EXPERT_CHARTS_CACHE
    if _EXPERT_CHARTS_CACHE is None:
        forecasts = get_expert_forecasts()
        _EXPERT_CHARTS_CACHE = {}
        for key in forecasts:
            _EXPERT_CHARTS_CACHE[key] = expert_consensus_chart(forecasts, metric_key=key)
    return _EXPERT_CHARTS_CACHE


def _ensure_temp_chart():
    """Build temperature trajectory chart once, then cache."""
    global _TEMP_CHART_CACHE
    if _TEMP_CHART_CACHE is None:
        traj = get_temperature_trajectory()
        _TEMP_CHART_CACHE = temperature_trajectory_chart(traj)
    return _TEMP_CHART_CACHE


# ---------------------------------------------------------------------------
# Dropdown options for Scenario Explorer
# ---------------------------------------------------------------------------

_SCENARIO_OPTIONS = [
    {"label": "Global EV Sales Share", "value": "ev_share_World"},
    {"label": "Norway EV Sales Share", "value": "ev_share_Norway"},
    {"label": "China EV Sales Share", "value": "ev_share_China"},
    {"label": "USA EV Sales Share", "value": "ev_share_USA"},
    {"label": "Sweden EV Sales Share", "value": "ev_share_Sweden"},
    {"label": "UK EV Sales Share", "value": "ev_share_United_Kingdom"},
    {"label": "France EV Sales Share", "value": "ev_share_France"},
    {"label": "Germany EV Sales Share", "value": "ev_share_Germany"},
    {"label": "Global Solar Electricity Share", "value": "solar_share_global"},
    {"label": "Global Wind Electricity Share", "value": "wind_share_global"},
    {"label": "Global Renewable Electricity Share", "value": "renewable_share_global"},
]


# ---------------------------------------------------------------------------
# Nascent technology progress cards
# ---------------------------------------------------------------------------

def _nascent_progress_card(key, info):
    """Build a small card showing current vs threshold for a nascent technology."""
    current = info.get("current_share_pct", 0)
    threshold = info.get("next_milestone_pct", info.get("threshold_pct", 5))
    pct_of_threshold = min(100, current / threshold * 100) if threshold > 0 else 0

    # Color based on proximity to threshold
    if pct_of_threshold >= 80:
        bar_color = "success"
    elif pct_of_threshold >= 40:
        bar_color = "warning"
    else:
        bar_color = "danger"

    # Confidence badge
    conf = info.get("confidence", "medium")
    conf_color = {"high": "success", "medium": "warning", "low": "secondary"}.get(conf, "secondary")

    return dbc.Col(
        dbc.Card([
            dbc.CardBody([
                html.H6(info.get("name", key), className="mb-1"),
                html.P(
                    f"{current}% → next milestone: {threshold}%",
                    className="text-muted small mb-2",
                ),
                dbc.Progress(
                    value=pct_of_threshold,
                    color=bar_color,
                    className="mb-2",
                    style={"height": "8px"},
                ),
                html.Div([
                    html.Small(
                        info.get("next_milestone_label", info.get("threshold_label", "")),
                        className="text-muted",
                    ),
                    dbc.Badge(conf, color=conf_color, pill=True, className="ms-2"),
                ], className="d-flex align-items-center justify-content-between"),
                html.P(
                    [
                        html.Small(
                            info.get("methodology_note", ""),
                            className="text-muted",
                        ),
                    ],
                    className="mt-2 mb-0",
                ),
                html.A(
                    html.Small("Source \u2192"),
                    href=info.get("source_url", "#"),
                    target="_blank",
                    className="text-primary small",
                    style={"textDecoration": "none"},
                ) if info.get("source_url") else None,
            ]),
        ], className="h-100 shadow-sm"),
        md=6, lg=4, className="mb-3",
    )


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def layout(**kwargs):
    """Build the Technology Trajectories page layout."""

    # Build cached figures
    gallery = _ensure_gallery()
    five_to_fifty = _ensure_five_to_fifty()
    expert_charts = _ensure_expert_charts()
    temp_chart = _ensure_temp_chart()
    temp_data = get_temperature_trajectory()

    # Load nascent tech data
    nascent_data = get_nascent_tech_data()

    params = get_scurve_params()

    return dbc.Container([

        # ===================================================================
        # Section 1: Header
        # ===================================================================
        dbc.Row(
            dbc.Col([
                html.H2(
                    "Technology Trajectories: Where Are We on the S-Curve?",
                    className="mt-4 mb-3",
                ),
                html.P([
                    "Technology adoption typically follows an ",
                    html.Strong("S-curve"),
                    " pattern: slow initial growth, rapid acceleration after a "
                    "tipping point (often around ",
                    html.Strong("5% market share"),
                    "), then saturation as the market matures. This page fits "
                    "logistic curves to real adoption data and explores what "
                    "historical patterns imply for the pace of the energy transition.",
                ], className="lead"),
                dbc.Alert([
                    html.I(className="bi bi-info-circle me-2"),
                    "S-curves are a descriptive tool, not a crystal ball. Many factors ",
                    "(policy changes, supply constraints, geopolitical shocks) can accelerate ",
                    "or stall adoption. All projections on this page are ",
                    html.Strong("exploratory scenarios"),
                    ", not forecasts.",
                ], color="info", className="mb-4"),
            ]),
            className="mb-2",
        ),

        # ===================================================================
        # Section 1b: Temperature Implications
        # ===================================================================
        html.H3("What Do These S-Curves Mean for Temperature?", className="mb-3"),
        html.P(
            "If clean technologies continue following their current S-curve trajectories, "
            "displacing fossil fuels sector by sector, what warming pathway results? "
            "This bottom-up model projects temperature based on technology adoption "
            "rates — not policy assumptions.",
            className="text-muted mb-3",
        ),
        dcc.Graph(
            figure=temp_chart,
            config=GRAPH_CONFIG,
            style={"height": "450px"},
            className="mb-3",
        ),
        dbc.Alert([
            html.Strong("Key finding: "),
            f"If current technology S-curves continue, peak warming reaches "
            f"~{temp_data.get('scenarios', {}).get('scurve_central', {}).get('peak_temp_c', '?')}°C "
            f"— about {3.1 - temp_data.get('scenarios', {}).get('scurve_central', {}).get('peak_temp_c', 3.1):.1f}°C "
            f"less than the current-policies estimate of 3.1°C. Technology momentum matters, "
            f"but it's not enough for 1.5°C without additional policy action.",
        ], color="info", className="mb-2"),
        html.Details([
            html.Summary(
                html.Strong("Sector breakdown and assumptions"),
                style={"cursor": "pointer"},
            ),
            html.Div([
                html.P(
                    "This model maps S-curve adoption rates to emissions displacement "
                    "in 8 sectors, then converts cumulative CO2 to temperature using TCRE "
                    "(0.45°C per 1000 GtCO2, IPCC AR6). Key assumptions:",
                    className="small text-muted mt-2",
                ),
                html.Ul([
                    html.Li("Electricity: renewable share displaces fossil generation (fitted S-curve)"),
                    html.Li("Road transport: EV sales share with 12-year fleet turnover lag"),
                    html.Li("Aviation: SAF adoption following EV-analogue S-curve, lagged ~15 years"),
                    html.Li("Shipping: alternative fuel adoption (methanol, ammonia)"),
                    html.Li("Industry: green H2 + EAF electrification (slowest sector)"),
                    html.Li("Buildings: heat pump adoption displacing gas heating"),
                    html.Li("Agriculture: 0.5%/yr reduction (slow, policy-dependent)"),
                    html.Li("Demand growth: 1.5% declining to 0% over 50 years"),
                ], className="small text-muted"),
                html.P([
                    html.Strong("This is intentionally simple "),
                    "— a thought experiment showing what happens if S-curves continue, "
                    "not a full integrated assessment model. It differs from UNEP's 3.1°C "
                    "because UNEP assumes current ",
                    html.Em("policies"),
                    " while this model assumes current ",
                    html.Em("technology trajectories"),
                    ".",
                ], className="small text-muted"),
            ]),
        ], className="mb-4"),

        html.Hr(className="my-4"),

        # ===================================================================
        # Section 2: S-Curve Gallery
        # ===================================================================
        html.H3("Historical Adoption Curves", className="mb-3"),
        html.P(
            "Each panel shows actual data (dots) and a fitted logistic curve (line). "
            "The dashed horizontal line marks the 5% tipping point. "
            "R\u00b2 measures how well the logistic model fits the data.",
            className="text-muted mb-3",
        ),

        dbc.Row([
            dbc.Col(
                dcc.Graph(
                    figure=fig,
                    config=GRAPH_CONFIG,
                    style={"height": "320px"},
                    className="mb-3",
                ),
                md=6, lg=4,
            )
            for key, fig in gallery
        ]),

        html.Hr(className="my-4"),

        # ===================================================================
        # Section 3: "5-to-50 Rule"
        # ===================================================================
        html.H3("The 5-to-Current Rule: Speed of Adoption", className="mb-3"),
        dbc.Row([
            dbc.Col([
                html.P([
                    "Once a technology passes ",
                    html.Strong("5% market share"),
                    ", adoption tends to accelerate sharply. "
                    "This chart shows how many years each country took from "
                    "crossing 5% EV sales share to its current level. "
                    "Shorter bars indicate faster adoption \u2014 often driven by "
                    "strong policy support, charging infrastructure, and consumer momentum.",
                ], className="text-muted"),
            ], md=4),
            dbc.Col(
                dcc.Graph(
                    figure=five_to_fifty,
                    config=GRAPH_CONFIG,
                ),
                md=8,
            ),
        ]),

        html.Hr(className="my-4"),

        # ===================================================================
        # Section 4: Nascent Technologies
        # ===================================================================
        html.H3("Nascent Technologies: Distance to Tipping Point", className="mb-3"),
        html.P(
            "These technologies have not yet reached their S-curve inflection "
            "point. The progress bars show how close each is to its estimated "
            "tipping point threshold.",
            className="text-muted mb-3",
        ),

        dbc.Row([
            _nascent_progress_card(key, info)
            for key, info in nascent_data.items()
            if not key.startswith("_")  # skip metadata keys like _methodology
        ]) if nascent_data else dbc.Alert(
            "Nascent technology data not loaded.", color="secondary"
        ),

        html.Hr(className="my-4"),

        # ===================================================================
        # Section 5: Expert Consensus
        # ===================================================================
        html.H3("Expert Forecast Consensus", className="mb-3"),
        html.P(
            "How do major forecasters compare? Each bar shows the low, central, "
            "and high projections from a given organization for a 2030 target. "
            "Wide disagreement between organizations highlights genuine uncertainty "
            "about the pace of transition.",
            className="text-muted mb-3",
        ),

        dbc.Tabs([
            dbc.Tab(
                dcc.Graph(figure=chart, config=GRAPH_CONFIG),
                label=forecasts_data.get(key, {}).get("metric", key),
            )
            for key, chart in expert_charts.items()
            for forecasts_data in [get_expert_forecasts()]
        ], className="mb-4") if expert_charts else dbc.Alert(
            "Expert forecast data not loaded.", color="secondary"
        ),

        html.Hr(className="my-4"),

        # ===================================================================
        # Section 6: Methodology & Limitations
        # ===================================================================
        html.H3("Methodology & Limitations", className="mb-3"),

        dbc.Accordion([
            dbc.AccordionItem([
                html.P([
                    "All adoption curves are fit using the ",
                    html.Strong("logistic function"),
                    ":",
                ]),
                html.P(
                    "S(t) = K / (1 + exp(-r \u00d7 (t \u2212 t\u2080)))",
                    className="font-monospace text-center fs-5 my-3",
                ),
                html.Ul([
                    html.Li([html.Strong("K"), " = carrying capacity (maximum share %)"]),
                    html.Li([html.Strong("r"), " = growth rate (steepness of the curve)"]),
                    html.Li([html.Strong("t\u2080"), " = inflection point (year of fastest growth)"]),
                ]),
                html.P(
                    "Parameters are estimated using scipy.optimize.curve_fit with "
                    "constrained bounds. R\u00b2 is reported for each fit."
                ),
            ], title="Logistic Model"),

            dbc.AccordionItem([
                html.P(
                    "S-curves are a useful heuristic but can fail for several reasons:"
                ),
                html.Ul([
                    html.Li([
                        html.Strong("Policy discontinuities: "),
                        "Sudden subsidy removals, tariffs, or regulatory changes "
                        "can abruptly alter adoption trajectories. Germany's EV share "
                        "declined in 2023\u20132024 after subsidy cuts.",
                    ]),
                    html.Li([
                        html.Strong("Supply constraints: "),
                        "Battery mineral shortages, grid bottlenecks, or manufacturing "
                        "capacity limits can create plateaus.",
                    ]),
                    html.Li([
                        html.Strong("Competing technologies: "),
                        "Multiple clean technologies may compete for the same market "
                        "(e.g., hydrogen vs battery electric trucks), making single-technology "
                        "S-curves misleading.",
                    ]),
                    html.Li([
                        html.Strong("Non-logistic dynamics: "),
                        "Some transitions follow Gompertz curves, Bass diffusion models, "
                        "or multi-stage adoption patterns that logistic curves cannot capture.",
                    ]),
                ]),
            ], title="Why S-Curves Can Fail"),

            dbc.AccordionItem([
                html.Ul([
                    html.Li([
                        html.Strong("EV sales share: "),
                        "IEA Global EV Outlook 2025 via Global EV Data Explorer. "
                        "Share = battery + plug-in hybrid sales / total car sales.",
                    ]),
                    html.Li([
                        html.Strong("Solar & wind share: "),
                        "Our World in Data (from Ember Global Electricity Review). "
                        "Share = TWh from source / total electricity TWh.",
                    ]),
                    html.Li([
                        html.Strong("Expert forecasts: "),
                        "IEA World Energy Outlook (STEPS scenario), RMI X-Change series, "
                        "BloombergNEF annual outlooks, RethinkX disruption models, "
                        "IRENA World Energy Transitions Outlook.",
                    ]),
                    html.Li([
                        html.Strong("Nascent technologies: "),
                        "Editorially curated from IEA, IATA, Global Maritime Forum, "
                        "and World Steel Association reports. Assessment date and "
                        "confidence level noted for each.",
                    ]),
                ]),
            ], title="Data Sources"),

            dbc.AccordionItem([
                html.P("The three scenario bands are constructed as follows:"),
                html.Ul([
                    html.Li([
                        html.Strong("Fast: "),
                        "Growth rate (r) multiplied by 1.5\u00d7. Represents adoption "
                        "speed comparable to the fastest historical examples "
                        "(Norway EVs, China solar).",
                    ]),
                    html.Li([
                        html.Strong("Moderate: "),
                        "Growth rate unchanged from the fitted trend. Represents "
                        "continuation of current dynamics.",
                    ]),
                    html.Li([
                        html.Strong("Slow: "),
                        "Growth rate multiplied by 0.6\u00d7. Represents policy "
                        "headwinds, supply constraints, or macroeconomic disruption.",
                    ]),
                ]),
                html.P([
                    "The carrying capacity (K) is held constant across scenarios. "
                    "In reality, K itself may shift \u2014 for example, if range anxiety "
                    "limits EV adoption below 100%, the effective ceiling changes. "
                    "These scenarios are ",
                    html.Strong("illustrative"),
                    ", not predictive.",
                ]),
            ], title="What Fast / Moderate / Slow Means"),

            dbc.AccordionItem([
                html.P(
                    "For EV adoption curves, the saturation level (K) is set to a minimum "
                    "of 70-80% based on fleet-turnover dynamics and policy mandates "
                    "(EU, UK, and China all have ICE phase-out targets by 2035-2040). "
                    "Norway (K=99%) validates that near-complete adoption is achievable."
                ),
                html.P(
                    "For solar and wind share of electricity, fitting K purely from "
                    "historical data produces unrealistically low values (solar: 24%, "
                    "wind: 13%) because these technologies are still in early exponential "
                    "growth. Instead, K is set based on the convergence of major energy "
                    "forecasts:"
                ),
                html.Ul([
                    html.Li([
                        html.Strong("Solar K = 40%: "),
                        "IEA NZE 2050: 43%, DNV best-estimate 2050: 40%, BNEF base case: "
                        "22% (floor). Solar's cost advantage is accelerating relative to "
                        "wind, and battery storage is making it dispatchable.",
                    ]),
                    html.Li([
                        html.Strong("Wind K = 30%: "),
                        "IEA NZE 2050: 31%, DNV best-estimate 2050: 29%, IRENA 1.5\u00b0C: "
                        "35%. Wind growth (~8%/yr) is slower than solar (~29%/yr) and faces "
                        "more siting and permitting constraints.",
                    ]),
                    html.Li([
                        html.Strong("Renewables K = 80-100%: "),
                        "IEA NZE 2050: ~90%, DNV 2050: 69%+. The remainder comes from "
                        "hydro, nuclear, biomass, geothermal, and residual fossil with CCS.",
                    ]),
                ]),
                html.P([
                    "Charts annotate when each technology reaches ",
                    html.Strong("80% of its estimated maximum"),
                    " share \u2014 the point at which the transition in that technology "
                    "is substantially complete. For technologies with K \u2265 80%, the "
                    "annotation shows when 80% absolute share is reached.",
                ]),
                html.P([
                    html.Strong("Sources: "),
                    "IEA World Energy Outlook 2025, DNV Energy Transition Outlook 2025, "
                    "IRENA World Energy Transitions Outlook 2024, BloombergNEF New Energy "
                    "Outlook 2025.",
                ], className="text-muted small"),
            ], title="Saturation Levels (K) \u2014 How Maximum Share Is Determined"),

        ], start_collapsed=True, className="mb-5"),

    ], fluid=True, className="pb-5")


# ---------------------------------------------------------------------------
# Callback: update scenario figure when dropdown changes
# ---------------------------------------------------------------------------

def update_trajectory_figure(tech_key):
    """
    Callback function wired in app.py:
      Input:  trajectory-tech-selector.value
      Output: trajectory-scenario-figure.figure
    """
    if not tech_key:
        tech_key = "ev_share_World"

    params = get_scurve_params()
    nascent_data = get_nascent_tech_data()

    return trajectory_scenario_figure(tech_key, params, nascent_data)
