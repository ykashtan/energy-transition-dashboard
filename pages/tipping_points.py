"""
tipping_points.py — Tipping Points page.

Tracks clean energy tipping points: a curated checklist of whether key thresholds
have been crossed, an S-curve momentum tracker, countdown to milestones, and a
composite optimism meter. Based on research from RMI, RethinkX, Lenton et al.
(Exeter), and the broader tipping-points literature.
"""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from utils.data_loader import get_kpis, get_investment, get_energy_mix, get_capacity

dash.register_page(
    __name__,
    path="/tipping-points",
    title="Tipping Points — Energy Transition Dashboard",
)


# ---------------------------------------------------------------------------
# Color palette (consistent with FLATLY theme)
# ---------------------------------------------------------------------------
GREEN = "#18bc9c"     # Crossed / yes
YELLOW = "#f39c12"    # Contested / approaching
RED = "#e74c3c"       # Not yet
GRAY = "#95a5a6"      # Neutral / distant
PRIMARY = "#2c3e50"   # Text / headings
LIGHT_BG = "#f8f9fa"  # Card backgrounds


# ---------------------------------------------------------------------------
# Section 1: Tipping Points Checklist
# ---------------------------------------------------------------------------
# Each item is editorially curated based on research. Status is one of:
# "crossed", "contested", or "not_yet".

CHECKLIST_ITEMS = [
    {
        "label": "Solar cheaper than new coal in most markets",
        "status": "crossed",
        "year": "2020–2023",
        "detail": (
            "Utility-scale solar LCOE fell to $0.043/kWh (2024), 87% below 2010. "
            "91% of new renewable projects are cheaper than fossil alternatives."
        ),
        "sources": "IRENA 2025; Way et al. 2022 (Joule)",
    },
    {
        "label": "EVs past 5% of new car sales globally",
        "status": "crossed",
        "year": "2021",
        "detail": (
            "Global EV share reached ~22% in 2024 (17M vehicles sold). "
            "Past the 5–10% S-curve inflection point identified by RMI and "
            "Nature Communications (2025) as triggering adoption takeoff."
        ),
        "sources": "IEA Global EV Outlook 2025; RMI X-Change: Cars",
    },
    {
        "label": "EVs past 5% in 15+ national markets",
        "status": "crossed",
        "year": "2023",
        "detail": (
            "Norway (88–97%), China (50%), Sweden (58%), Denmark (56%), "
            "Netherlands (48%), UK (~30%), EU avg (~21%), US (~10%), and "
            "many others have crossed the 5% threshold."
        ),
        "sources": "IEA Global EV Outlook 2025; BloombergNEF",
    },
    {
        "label": "Renewables >50% of new power capacity globally",
        "status": "crossed",
        "year": "2015 →",
        "detail": (
            "Solar alone represented 70% of all new generating capacity worldwide "
            "in 2024. Renewables have dominated new capacity for over a decade."
        ),
        "sources": "IRENA 2025; Ember Global Electricity Review 2025",
    },
    {
        "label": "1 TW of solar installed globally",
        "status": "crossed",
        "year": "2023",
        "detail": (
            "Global solar capacity reached 1,865 GW by end 2024. "
            "First TW took ~15 years; next TW is expected in ~4 years."
        ),
        "sources": "IRENA Renewable Energy Statistics 2025",
    },
    {
        "label": "Clean energy investment > fossil fuel investment",
        "status": "crossed",
        "year": "2023",
        "detail": (
            "Clean energy investment reached $2.15T in 2025 vs ~$1.1T for fossil "
            "fuels — nearly a 2:1 ratio. Renewables-to-fossil electricity "
            "investment ratio is ~10:1."
        ),
        "sources": "IEA World Energy Investment 2025; BloombergNEF",
    },
    {
        "label": "Peak fossil fuel demand reached",
        "status": "contested",
        "year": "~2025?",
        "detail": (
            "IEA projects fossil fuel demand peaks by ~2030 under current policies. "
            "DNV estimates emissions peaked in 2025. Coal demand may have already "
            "peaked. Oil demand peak depends heavily on EV adoption speed and "
            "petrochemical feedstock growth. Contested because some analysts "
            "project continued growth through the 2030s."
        ),
        "sources": "IEA WEO 2025 (STEPS); DNV ETO 2025; RMI 2025",
    },
    {
        "label": "Heat pumps outselling gas boilers in leading markets",
        "status": "crossed",
        "year": "2022–2024",
        "detail": (
            "In the Nordics: 90–97% heat pump market share. European average: "
            "28% (past inflection). In the US, heat pumps outsold gas furnaces "
            "by 30% in 2024. UK still in early adoption (19 per 1,000 households)."
        ),
        "sources": "EHPA 2025; IEA Heat Pumps Tracking",
    },
]


def _checklist_icon(status: str) -> html.Span:
    """Return a colored icon for checklist status."""
    if status == "crossed":
        return html.I(
            className="bi bi-check-circle-fill me-2",
            style={"color": GREEN, "fontSize": "1.3rem"},
        )
    if status == "contested":
        return html.I(
            className="bi bi-question-circle-fill me-2",
            style={"color": YELLOW, "fontSize": "1.3rem"},
        )
    return html.I(
        className="bi bi-x-circle-fill me-2",
        style={"color": RED, "fontSize": "1.3rem"},
    )


def _checklist_badge(status: str, year: str) -> dbc.Badge:
    """Return a badge with the year and status color."""
    color_map = {"crossed": "success", "contested": "warning", "not_yet": "danger"}
    label_map = {"crossed": f"Crossed {year}", "contested": f"Contested — {year}", "not_yet": "Not yet"}
    return dbc.Badge(
        label_map.get(status, ""),
        color=color_map.get(status, "secondary"),
        className="ms-2",
        pill=True,
    )


def _build_checklist_section() -> dbc.Card:
    """Build the tipping-points checklist section."""
    items = []
    for item in CHECKLIST_ITEMS:
        items.append(
            dbc.ListGroupItem([
                html.Div([
                    html.Div([
                        _checklist_icon(item["status"]),
                        html.Span(item["label"], className="fw-bold"),
                        _checklist_badge(item["status"], item["year"]),
                    ], className="d-flex align-items-center"),
                    html.P(
                        item["detail"],
                        className="mb-1 mt-2 small text-muted",
                    ),
                    html.P(
                        [html.Em("Sources: "), item["sources"]],
                        className="mb-0 small text-muted",
                        style={"fontSize": "0.8rem"},
                    ),
                ]),
            ])
        )

    crossed = sum(1 for i in CHECKLIST_ITEMS if i["status"] == "crossed")
    contested = sum(1 for i in CHECKLIST_ITEMS if i["status"] == "contested")
    total = len(CHECKLIST_ITEMS)

    return dbc.Card([
        dbc.CardHeader([
            html.H4([
                html.I(className="bi bi-check2-square me-2"),
                "Clean Energy Tipping Points Checklist",
            ], className="mb-0 fw-bold"),
        ]),
        dbc.CardBody([
            html.P([
                f"{crossed} of {total} tipping points crossed",
                html.Span(
                    f"  •  {contested} contested",
                    className="text-warning",
                ) if contested else "",
            ], className="lead mb-3"),
            html.P(
                "Based on the framework from RMI, Lenton et al. (Exeter), "
                "and Carbon Tracker: technologies reach a catalytic tipping point "
                "at ~5–10% market share, after which adoption accelerates rapidly. "
                "Each item below tracks whether a key clean energy threshold has "
                "been crossed.",
                className="text-muted small mb-3",
            ),
            dbc.ListGroup(items, flush=True),
        ]),
    ], className="mb-4 shadow-sm")


# ---------------------------------------------------------------------------
# Section 2: S-Curve Momentum Tracker
# ---------------------------------------------------------------------------

S_CURVE_STAGES = [
    {
        "stage": "Innovation (<1%)",
        "color": GRAY,
        "icon": "bi-lightbulb",
        "technologies": [
            ("Green hydrogen production", "Very early — cost-competitive for fertilizer still distant"),
            ("Direct air capture", "~0.01 MtCO₂/yr captured vs gigatonnes needed"),
            ("E-fuels (synthetic fuels)", "Pilot scale; niche aviation/shipping use"),
        ],
    },
    {
        "stage": "Early Adoption (1–5%)",
        "color": "#3498db",
        "icon": "bi-graph-up",
        "technologies": [
            ("Heat pumps (global average)", "28% in Europe, but <5% in most of Global South"),
            ("Electric trucks", "Entering market; battery cost declines cascading from passenger EVs"),
            ("Offshore wind (global)", "~8% of total wind; rapid growth in UK, EU, China"),
            ("Battery storage", "50% YoY growth; entering steep S-curve comparable to solar ~2010"),
        ],
    },
    {
        "stage": "Rapid Growth (10–50%)",
        "color": "#27ae60",
        "icon": "bi-rocket-takeoff",
        "technologies": [
            ("EVs (22% globally)", "Past the 5–10% inflection; 50%+ in China, Norway, Sweden"),
            ("Solar PV (~10% of electricity)", "Largest source of new electricity for 3rd consecutive year"),
            ("Wind power (~8% of electricity)", "Mature in Denmark (58%), Germany (23%), US (~11%)"),
            ("Renewables in new capacity (>80%)", "Dominant source of new power globally since ~2015"),
        ],
    },
    {
        "stage": "Mainstream (>50%)",
        "color": GREEN,
        "icon": "bi-check2-all",
        "technologies": [
            ("Renewables in new capacity", ">80% of new power capacity globally"),
            ("EVs in Norway (88–97%)", "Near-saturation; essentially completed S-curve"),
            ("Heat pumps in Nordics (90%+)", "Finland, Sweden, Norway — near-complete adoption"),
            ("LED lighting (~65% globally)", "Rapid transition from 4% (2015) to 65% (2025)"),
        ],
    },
]


_SCURVE_CACHE = None

def _build_scurve_figure() -> go.Figure:
    """Build an idealized S-curve with stage annotations. Cached at module level."""
    global _SCURVE_CACHE
    if _SCURVE_CACHE is not None:
        return _SCURVE_CACHE
    import numpy as np
    x = np.linspace(-6, 6, 200)
    y = 100 / (1 + np.exp(-x))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode="lines",
        line={"color": PRIMARY, "width": 3},
        hoverinfo="skip",
        showlegend=False,
    ))

    # Stage regions (approximate x positions on the S-curve)
    stages = [
        ("Innovation\n<1%", -5, 2, GRAY),
        ("Early\nAdoption\n1–5%", -2.5, 8, "#3498db"),
        ("Rapid\nGrowth\n10–50%", 0.5, 55, "#27ae60"),
        ("Main-\nstream\n>50%", 3.5, 92, GREEN),
    ]
    for label, x_pos, y_pos, color in stages:
        fig.add_annotation(
            x=x_pos, y=y_pos,
            text=label,
            showarrow=False,
            font={"size": 11, "color": color, "family": "Arial"},
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor=color,
            borderwidth=1,
            borderpad=4,
        )

    # Mark specific technologies on the curve
    tech_markers = [
        ("Green H₂", -4.5, 1.5),
        ("Battery\nstorage", -1.8, 14),
        ("EVs\n(global)", 0.8, 22),
        ("Solar PV", 1.2, 30),
        ("RE in new\ncapacity", 3.0, 83),
        ("EVs\n(Norway)", 4.2, 96),
    ]
    for label, x_pos, y_pos in tech_markers:
        fig.add_trace(go.Scatter(
            x=[x_pos], y=[y_pos],
            mode="markers+text",
            marker={"size": 10, "color": PRIMARY, "symbol": "diamond"},
            text=[label],
            textposition="top center",
            textfont={"size": 9},
            hoverinfo="text",
            hovertext=label.replace("\n", " "),
            showlegend=False,
        ))

    fig.update_layout(
        xaxis={"visible": False},
        yaxis={"title": "Market Share (%)", "range": [-2, 105]},
        margin={"l": 50, "r": 20, "t": 30, "b": 20},
        height=350,
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    _SCURVE_CACHE = fig
    return fig


def _build_scurve_section() -> dbc.Card:
    """Build the S-curve momentum tracker section."""
    # Technology cards for each stage
    stage_rows = []
    for stage_info in S_CURVE_STAGES:
        tech_items = []
        for name, detail in stage_info["technologies"]:
            tech_items.append(
                html.Li([
                    html.Strong(name, style={"color": stage_info["color"]}),
                    html.Span(f" — {detail}", className="text-muted small"),
                ], className="mb-1")
            )
        stage_rows.append(
            dbc.Col([
                html.Div([
                    html.H6([
                        html.I(className=f"{stage_info['icon']} me-1"),
                        stage_info["stage"],
                    ], style={"color": stage_info["color"]}, className="fw-bold mb-2"),
                    html.Ul(tech_items, className="ps-3", style={"listStyleType": "none"}),
                ], className="p-2", style={
                    "borderLeft": f"3px solid {stage_info['color']}",
                    "backgroundColor": LIGHT_BG,
                    "borderRadius": "4px",
                }),
            ], md=6, lg=3, className="mb-3")
        )

    return dbc.Card([
        dbc.CardHeader([
            html.H4([
                html.I(className="bi bi-graph-up-arrow me-2"),
                "S-Curve Momentum Tracker",
            ], className="mb-0 fw-bold"),
        ]),
        dbc.CardBody([
            html.P(
                "Technology adoption follows S-curves: slow start, explosive middle, "
                "gradual saturation. The critical insight from RMI and Carbon Tracker: "
                "technologies reaching ~5–10% market share typically accelerate rapidly "
                "toward 50%+. The same time it takes to go from 0% to 5% often equals "
                "the time from 5% to 50%.",
                className="text-muted small mb-3",
            ),
            dcc.Graph(
                figure=_build_scurve_figure(),
                config={"responsive": True, "displayModeBar": False},
                className="mb-3",
            ),
            dbc.Row(stage_rows),
            html.P([
                html.Em("Sources: "),
                "RMI (Bond & Butler-Sloss 2022, ",
                html.Em("Peaking: A Theory of Rapid Transition"),
                "); RethinkX; Rogers (1962), ",
                html.Em("Diffusion of Innovations"),
                "; Way et al. 2022 (",
                html.Em("Joule"),
                "); Carbon Tracker S-Curve analysis.",
            ], className="text-muted small mt-2", style={"fontSize": "0.8rem"}),
        ]),
    ], className="mb-4 shadow-sm")


# ---------------------------------------------------------------------------
# Section 3: Countdown to Key Milestones
# ---------------------------------------------------------------------------

def _build_countdown_section() -> dbc.Card:
    """Build progress bars / gauges toward key milestones using real data."""
    kpis = get_kpis()

    # Temperature
    temp_val = kpis.get("temperature_anomaly_c", {}).get("value", 1.55)
    temp_target = 1.5
    temp_pct = min((temp_val / 2.0) * 100, 100)  # Scale to 2°C as "full bar"

    # Renewable electricity share
    re_share = kpis.get("renewable_share_electricity_pct", {}).get("value", 31.7)

    # Clean energy investment
    clean_inv = kpis.get("clean_energy_investment_t", {}).get("value", 2.15)
    # IEA NZE requires ~$4.5T/yr by 2030
    inv_target = 4.5
    inv_pct = min((clean_inv / inv_target) * 100, 100)

    # Net-zero pledges coverage (editorial — based on research)
    nz_pct_gdp = 88  # ~88% of global GDP covered by net-zero pledges (ECIU)

    # Coal phase-out commitments
    coal_committed = 58   # PPCA members + countries with coal phase-out dates
    coal_dependent = 80   # ~80 countries still using coal power
    coal_pct = min((coal_committed / coal_dependent) * 100, 100)

    milestones = [
        {
            "label": "Global Temperature",
            "current": f"{temp_val}°C",
            "target": "1.5°C Paris target",
            "pct": temp_pct,
            "color": RED if temp_val >= 1.5 else YELLOW,
            "note": (
                f"Already at {temp_val}°C above pre-industrial baseline. The 1.5°C "
                "target is being approached; carbon budget for 50% chance of staying "
                "below 1.5°C is ~250 GtCO₂ (~6 years at current rates)."
            ),
            "source": "HadCRUT5 (Met Office/UEA); IPCC AR6",
        },
        {
            "label": "Renewable Electricity Share",
            "current": f"{re_share}%",
            "target": "100% target",
            "pct": re_share,
            "color": GREEN if re_share > 30 else YELLOW,
            "note": (
                f"Renewables generate {re_share}% of global electricity (2024). "
                "IEA Net Zero scenario requires ~90% by 2050. Growth is accelerating: "
                "+2.3 percentage points in 2024 alone."
            ),
            "source": "OWID (Ember/IRENA)",
        },
        {
            "label": "Clean Energy Investment",
            "current": f"${clean_inv}T/yr",
            "target": f"${inv_target}T/yr needed (IEA NZE 2030)",
            "pct": inv_pct,
            "color": GREEN if inv_pct > 40 else YELLOW,
            "note": (
                f"Global clean energy investment reached ${clean_inv}T in 2025 — "
                "nearly 2x fossil fuel investment. But IEA's Net Zero pathway requires "
                f"~${inv_target}T/yr by 2030, especially in the Global South."
            ),
            "source": "IEA World Energy Investment 2025",
        },
        {
            "label": "Net-Zero Pledges (% of global GDP)",
            "current": f"{nz_pct_gdp}%",
            "target": "100% of global GDP",
            "pct": nz_pct_gdp,
            "color": GREEN,
            "note": (
                "~88% of global GDP is covered by net-zero pledges. However, the "
                "implementation gap remains large — current policies deliver ~3.1°C, "
                "not the ~1.5°C these pledges imply."
            ),
            "source": "Energy & Climate Intelligence Unit (ECIU); UNEP EGR 2024",
        },
        {
            "label": "Coal Phase-Out Commitments",
            "current": f"{coal_committed} countries",
            "target": f"~{coal_dependent} coal-using countries",
            "pct": coal_pct,
            "color": YELLOW,
            "note": (
                f"{coal_committed} countries have committed to coal phase-out or joined "
                "the Powering Past Coal Alliance. Major gaps: China, India, Indonesia, "
                "and the US have not committed to phase-out dates."
            ),
            "source": "Powering Past Coal Alliance; Global Energy Monitor",
        },
    ]

    rows = []
    for m in milestones:
        rows.append(
            dbc.Col([
                html.Div([
                    html.Div([
                        html.Strong(m["label"]),
                        html.Span(
                            f"  {m['current']} / {m['target']}",
                            className="text-muted small ms-2",
                        ),
                    ], className="mb-1"),
                    dbc.Progress(
                        value=m["pct"],
                        color=(
                            "danger" if m["color"] == RED
                            else "warning" if m["color"] == YELLOW
                            else "success"
                        ),
                        striped=True,
                        animated=True,
                        className="mb-1",
                        style={"height": "22px"},
                    ),
                    html.P(m["note"], className="text-muted small mb-1",
                           style={"fontSize": "0.8rem"}),
                    html.P(
                        [html.Em("Source: "), m["source"]],
                        className="text-muted mb-0",
                        style={"fontSize": "0.75rem"},
                    ),
                ], className="p-3", style={
                    "backgroundColor": LIGHT_BG,
                    "borderRadius": "6px",
                }),
            ], md=6, className="mb-3")
        )

    return dbc.Card([
        dbc.CardHeader([
            html.H4([
                html.I(className="bi bi-hourglass-split me-2"),
                "Countdown to Key Milestones",
            ], className="mb-0 fw-bold"),
        ]),
        dbc.CardBody([
            html.P(
                "Progress toward critical energy transition thresholds. "
                "These milestones combine observed data with pathway targets from "
                "the IEA Net Zero scenario, IPCC AR6, and international agreements.",
                className="text-muted small mb-3",
            ),
            dbc.Row(rows),
        ]),
    ], className="mb-4 shadow-sm")


# ---------------------------------------------------------------------------
# Section 4: Optimism Meter (Phase 1 — simple composite)
# ---------------------------------------------------------------------------

def _compute_optimism_score() -> tuple:
    """
    Compute a simple composite optimism score (0–100).

    Methodology (transparent and intentionally simple):
    - Checklist component (40%): proportion of tipping points crossed × 100
    - Momentum component (30%): based on real data — renewable share, investment ratio
    - Gap component (30%): inverted — how far from dangerous thresholds

    Returns (score, breakdown_dict).
    """
    kpis = get_kpis()

    # 1. Checklist score (40 points max)
    crossed = sum(1 for i in CHECKLIST_ITEMS if i["status"] == "crossed")
    contested = sum(1 for i in CHECKLIST_ITEMS if i["status"] == "contested")
    total = len(CHECKLIST_ITEMS)
    checklist_raw = (crossed + 0.5 * contested) / total
    checklist_score = checklist_raw * 40

    # 2. Momentum score (30 points max)
    # Renewable share: 31.7% → score out of 10 (target: 100%)
    re_share = kpis.get("renewable_share_electricity_pct", {}).get("value", 31.7)
    re_score = min(re_share / 100 * 10, 10)

    # Clean energy investment ratio: $2.15T vs $1.1T fossil → score out of 10
    clean_inv = kpis.get("clean_energy_investment_t", {}).get("value", 2.15)
    inv_ratio = clean_inv / 1.1  # ratio to fossil investment
    inv_score = min(inv_ratio / 3 * 10, 10)  # 3:1 ratio = full marks

    # Solar capacity growth: 1865 GW, 32% YoY growth → score out of 10
    solar_growth = kpis.get("capacity_solar_gw", {}).get("pct_change", 32)
    growth_score = min(solar_growth / 30 * 10, 10)  # 30% growth = full marks

    momentum_score = re_score + inv_score + growth_score

    # 3. Gap score (30 points max, inverted — lower warming gap = higher score)
    # Temperature gap: 1.55°C is 77.5% of way to 2°C danger zone
    temp = kpis.get("temperature_anomaly_c", {}).get("value", 1.55)
    temp_score = max(0, (2.0 - temp) / 0.5 * 10)  # 0.5°C buffer = 10 pts

    # Projected warming under current policies: 3.1°C → distance from 2°C
    proj_warming = kpis.get("current_policies_warming_c", {}).get("value", 3.1)
    proj_score = max(0, (4.0 - proj_warming) / 2.0 * 10)  # 2°C = 10, 4°C = 0

    # Emissions trajectory: are emissions growth slowing?
    emissions_growth = kpis.get("co2_fossil_gt", {}).get("pct_change", 1.1)
    emissions_score = max(0, min(10, (5 - emissions_growth) / 5 * 10))  # <0% = 10, 5% = 0

    gap_score = temp_score + proj_score + emissions_score

    total_score = checklist_score + momentum_score + gap_score

    breakdown = {
        "Checklist (40%)": round(checklist_score, 1),
        "Momentum (30%)": round(momentum_score, 1),
        "Gap to targets (30%)": round(gap_score, 1),
        "sub": {
            "Tipping points crossed": f"{crossed}/{total} + {contested} contested",
            "Renewable electricity": f"{re_share}% → {re_score:.1f}/10",
            "Investment ratio": f"{inv_ratio:.1f}:1 clean/fossil → {inv_score:.1f}/10",
            "Solar growth": f"{solar_growth}% YoY → {growth_score:.1f}/10",
            "Temperature buffer": f"{temp}°C of 2°C → {temp_score:.1f}/10",
            "Policy trajectory": f"{proj_warming}°C projected → {proj_score:.1f}/10",
            "Emissions growth": f"{emissions_growth}% → {emissions_score:.1f}/10",
        },
    }
    return round(total_score, 1), breakdown


_GAUGE_CACHE = None

def _build_gauge_figure(score: float) -> go.Figure:
    """Build a gauge / thermometer figure for the optimism score."""
    if score >= 65:
        bar_color = GREEN
    elif score >= 45:
        bar_color = YELLOW
    else:
        bar_color = RED

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"suffix": "/100", "font": {"size": 36, "color": PRIMARY}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": PRIMARY},
            "bar": {"color": bar_color, "thickness": 0.7},
            "bgcolor": "white",
            "borderwidth": 2,
            "bordercolor": GRAY,
            "steps": [
                {"range": [0, 33], "color": "#fadbd8"},
                {"range": [33, 66], "color": "#fef9e7"},
                {"range": [66, 100], "color": "#d5f5e3"},
            ],
            "threshold": {
                "line": {"color": PRIMARY, "width": 3},
                "thickness": 0.8,
                "value": score,
            },
        },
    ))

    fig.update_layout(
        height=250,
        margin={"l": 30, "r": 30, "t": 40, "b": 10},
        paper_bgcolor="white",
        font={"family": "Arial"},
    )
    return fig


def _build_optimism_section() -> dbc.Card:
    """Build the optimism meter section."""
    score, breakdown = _compute_optimism_score()

    # Build breakdown table
    main_rows = []
    for label, value in breakdown.items():
        if label == "sub":
            continue
        main_rows.append(html.Tr([
            html.Td(label, className="small"),
            html.Td(html.Strong(f"{value}"), className="small text-end"),
        ]))

    sub_rows = []
    for label, value in breakdown.get("sub", {}).items():
        sub_rows.append(html.Tr([
            html.Td(f"  → {label}", className="small text-muted", style={"paddingLeft": "1.5rem"}),
            html.Td(value, className="small text-muted text-end"),
        ]))

    return dbc.Card([
        dbc.CardHeader([
            html.H4([
                html.I(className="bi bi-speedometer2 me-2"),
                "Optimism Meter",
            ], className="mb-0 fw-bold"),
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        figure=_build_gauge_figure(score),
                        config={"responsive": True, "displayModeBar": False},
                    ),
                ], md=5),
                dbc.Col([
                    html.H5(f"Score: {score}/100", className="fw-bold mb-3"),
                    dbc.Table(
                        [html.Tbody(main_rows + sub_rows)],
                        bordered=False,
                        size="sm",
                        className="mb-2",
                    ),
                ], md=7),
            ]),
            dbc.Alert([
                html.I(className="bi bi-info-circle me-2"),
                html.Strong("Methodology note: "),
                "This score is meant to be thought-provoking, not definitive. "
                "It combines the proportion of tipping points crossed (40%), "
                "technology and investment momentum indicators (30%), and the "
                "gap between current trajectory and climate targets (30%). "
                "All inputs are transparent and shown above. Weighting choices "
                "are editorial — reasonable people may weight these differently. "
                "See the ",
                dcc.Link("Methodology page", href="/methodology"),
                " for full data source documentation.",
            ], color="info", className="mt-3 small"),
        ]),
    ], className="mb-4 shadow-sm")


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

def layout(**kwargs):
    return html.Div([
        dbc.Container([

            # Header
            dbc.Row([
                dbc.Col([
                    html.H1(
                        "Tipping Points",
                        className="display-5 fw-bold mt-4 mb-1",
                    ),
                    html.P(
                        "Tracking the clean energy thresholds that, once crossed, "
                        "trigger self-reinforcing adoption cascades. Based on research "
                        "from RMI, RethinkX, Lenton et al. (Exeter), and the broader "
                        "S-curve and technology disruption literature.",
                        className="lead text-muted mb-1",
                    ),
                    html.P([
                        "Key insight: technologies reaching ",
                        html.Strong("5–10% market share"),
                        " typically accelerate rapidly toward 50%+. Many clean energy "
                        "technologies have already crossed this threshold.",
                    ], className="text-muted mb-3"),
                ], md=10, lg=9),
            ]),

            html.Hr(),

            # Section 1: Checklist
            _build_checklist_section(),

            # Section 2: S-Curve Tracker
            _build_scurve_section(),

            # Section 3: Countdown
            _build_countdown_section(),

            # Section 4: Optimism Meter
            _build_optimism_section(),

            # Footer note
            dbc.Row([
                dbc.Col([
                    html.Hr(),
                    html.P([
                        html.Strong("A note on framing: "),
                        "Research from the Yale Program on Climate Change Communication "
                        "finds that ",
                        html.Em("constructive hope"),
                        " (seeing real progress and others acting) increases engagement "
                        "and policy support, while ",
                        html.Em("false hope"),
                        " (believing technology alone will save us) decreases it. "
                        "This page aims to pair progress with honest assessment of "
                        "what still needs to happen. The energy transition is real and "
                        "accelerating — and it is not yet fast enough.",
                    ], className="text-muted small mb-4"),
                ], md=10, lg=9),
            ]),

        ], fluid=True, className="px-3 px-md-4"),
    ])
