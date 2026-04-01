"""
kpi_card.py — Reusable KPI card component for the Energy Transition Dashboard.

Cards are driven entirely by kpis.json — no Parquet reads, no server callbacks.
All interactivity (tooltips) is clientside.

Each card displays:
  - Large headline value + unit
  - Year-over-year trend arrow + % change
  - Source label
  - Info button that opens a tooltip with the full definition/caveats

Hero cards (top 5): click opens a modal with historical trendline.
Thematic cards (section): click switches the section's main chart via callback.

Accessibility:
  - aria-label on the card div describing the metric
  - Tooltip text is readable by screen readers
  - WCAG AA contrast ratios on all colors (verified against custom.css palette)
"""

import dash_bootstrap_components as dbc
from dash import html

from utils.formatting import fmt_pct_change, trend_color


# Map source text patterns to methodology page anchor IDs
_SOURCE_ANCHOR_MAP = {
    "UNEP": "source-emissions-climate",
    "HadCRUT": "source-emissions-climate",
    "NOAA": "source-emissions-climate",
    "OWID": "source-emissions-climate",
    "GCB": "source-emissions-climate",
    "EDGAR": "source-emissions-climate",
    "Ember": "source-clean-energy",
    "IRENA": "source-clean-energy",
    "IEA Net Zero": "source-clean-energy",
    "IEA World Energy Investment": "source-costs-finance",
    "IEA WEI": "source-costs-finance",
    "IEA Fossil Fuel": "source-costs-finance",
    "IEA Subsidies": "source-costs-finance",
    "IMF": "source-costs-finance",
    "BloombergNEF": "source-costs-finance",
    "World Bank": "source-health-ej",
    "Lelieveld": "source-health-ej",
    "Vohra": "source-health-ej",
    "GBD": "source-health-ej",
    "IHME": "source-health-ej",
    "Lancet": "source-health-ej",
    "McDuffie": "source-health-ej",
    "EM-DAT": "source-climate-impacts",
    "ND-GAIN": "source-climate-impacts",
    "CCUS": "source-climate-impacts",
    "IEA WEO": "source-scenarios-predictions",
    "IIASA": "source-scenarios-predictions",
    "Way et al": "source-scenarios-predictions",
    "Global CCS": "source-scenarios-predictions",
}


def _source_to_methodology_anchor(source: str) -> str:
    """Map a source string to a methodology page anchor link."""
    if not source:
        return "/methodology"
    source_lower = source.lower()
    for pattern, anchor in _SOURCE_ANCHOR_MAP.items():
        if pattern.lower() in source_lower:
            return f"/methodology#{anchor}"
    return "/methodology"


def make_kpi_card(
    kpi_key: str,
    kpi_data: dict,
    card_size: str = "hero",   # "hero" (large, above fold) or "thematic" (smaller)
    clickable_id: str = None,  # if set, card gets this id for callback targeting
) -> dbc.Card:
    """
    Build a KPI card component.

    Args:
        kpi_key: The key in kpis.json (used for aria-label and tooltip ID)
        kpi_data: The KPI dict from kpis.json
        card_size: "hero" for 5 headline stats; "thematic" for section stats
        clickable_id: if set, card gets this id so callbacks can detect clicks
    """
    value = kpi_data.get("value")
    unit = kpi_data.get("unit", "")
    label = kpi_data.get("label", kpi_key)
    year = kpi_data.get("year")
    pct_chg = kpi_data.get("pct_change")
    trend = kpi_data.get("trend", "→")
    source = kpi_data.get("source", "")
    source_url = kpi_data.get("source_url", "")
    note = kpi_data.get("note", "")
    status = kpi_data.get("status", "live")

    # Format value for display
    if value is None:
        display_value = "—"
        display_unit = "pending data"
    else:
        # Format with commas for large numbers; strings pass through as-is
        if isinstance(value, float):
            display_value = f"{value:,.2f}".rstrip("0").rstrip(".")
        elif isinstance(value, (int,)):
            display_value = f"{value:,}"
        else:
            display_value = str(value)
        display_unit = unit

    # Trend indicator
    trend_arrow = "↑" if "↑" in trend else ("↓" if "↓" in trend else "→")
    trend_cls = "text-success" if "good" in trend else ("text-danger" if "bad" in trend else "text-muted")

    # Year label
    year_label = f"({year})" if year else ""

    # Build tooltip content
    tooltip_parts = []
    if note:
        tooltip_parts.append(note)
    if source:
        tooltip_parts.append(f"Source: {source}")
    tooltip_text = " | ".join(tooltip_parts) if tooltip_parts else label

    tooltip = dbc.Tooltip(
        tooltip_text,
        target=f"kpi-info-{kpi_key}",
        placement="top",
        style={"maxWidth": "350px"},
    )

    # Card size styling
    if card_size == "hero":
        value_class = "display-5 fw-bold"
        unit_class = "fs-5 text-muted"
        label_class = "fs-6 text-muted mt-1"
        card_class = "kpi-card kpi-card-hero h-100 border-0 shadow-sm"
    else:
        value_class = "fs-3 fw-bold"
        unit_class = "fs-6 text-muted"
        label_class = "small text-muted mt-1"
        card_class = "kpi-card kpi-card-thematic h-100 border-0 shadow-sm"

    # Pending state styling
    if status == "placeholder":
        card_class += " kpi-card-pending"
        value_class += " text-muted"

    card_props = {"className": card_class, "style": {"cursor": "pointer"}}

    card = dbc.Card(
        dbc.CardBody([
            # Info button (top right)
            html.Div(
                html.I(
                    className="bi bi-info-circle text-muted",
                    id=f"kpi-info-{kpi_key}",
                    style={"cursor": "pointer", "fontSize": "0.85rem"},
                    **{"aria-label": f"More information about {label}"}
                ),
                className="d-flex justify-content-end mb-1",
            ),
            tooltip,

            # Main value
            html.Div(
                [
                    html.Span(display_value, className=value_class),
                    html.Span(f" {display_unit}", className=unit_class),
                ],
                className="d-flex align-items-baseline gap-1",
            ),

            # Label
            html.Div(label, className=label_class),

            # Trend + year (only if we have a value)
            html.Div(
                [
                    html.Span(trend_arrow, className=f"me-1 {trend_cls}"),
                    html.Span(
                        f"{fmt_pct_change(pct_chg)} vs prior yr",
                        className=f"small {trend_cls}",
                    ) if pct_chg else html.Span(""),
                    html.Span(f" {year_label}", className="small text-muted ms-1") if year_label else html.Span(""),
                ],
                className="mt-2 d-flex align-items-center",
            ) if value is not None else html.Div(
                html.Small("Awaiting data download", className="text-muted fst-italic"),
                className="mt-2",
            ),

            # Source link → links to methodology page section (not external URL)
            html.Div(
                html.A(
                    source.split("(")[0].strip() if source else "",
                    href=_source_to_methodology_anchor(source),
                    className="text-muted",
                    style={"fontSize": "0.7rem", "textDecoration": "none"},
                ),
                className="mt-1",
            ) if source else None,

            # Click hint for hero cards
            html.Div(
                html.Small("Click for historical trend", className="text-primary"),
                className="mt-1",
                style={"fontSize": "0.65rem"},
            ) if card_size == "hero" and value is not None else None,
        ]),
        **card_props,
    )

    # Wrap in html.Div with the clickable ID so Dash can track n_clicks.
    # dbc.Card does not propagate n_clicks in DBC 2.x; html.Div does.
    if clickable_id:
        card = html.Div(card, id=clickable_id, n_clicks=0)

    return card


# Top 5 hero KPI keys — one per dashboard section
HERO_KEYS = [
    "current_policies_warming_c",        # Emissions & Pathways
    "renewable_share_electricity_pct",    # Clean Energy Momentum (electricity)
    "renewable_share_total_energy_pct",   # Clean Energy Momentum (total energy)
    "clean_energy_investment_t",          # Investment
    "health_deaths_fossil_pm25",         # Health & EJ
]


def make_hero_stats_row(kpis: dict) -> dbc.Row:
    """
    Build the 5-card hero statistics row (above the fold).

    One representative metric per section:
      1. Projected warming (°C) — Emissions & Pathways
      2. Renewable share of electricity (%) — Clean Energy
      3. Renewable share of total energy (%) — Clean Energy (total)
      4. Clean energy investment ($T) — Investment
      5. Premature deaths from fossil fuel air pollution — Health & EJ
    """
    cols = []
    for key in HERO_KEYS:
        kpi_data = kpis.get(key, {"label": key, "value": None, "status": "placeholder"})
        card = make_kpi_card(key, kpi_data, card_size="hero",
                            clickable_id=f"hero-card-{key}")
        cols.append(
            dbc.Col(card, xs=12, sm=6, lg=True, className="mb-3")
        )

    return dbc.Row(cols, className="g-3 hero-stats-row")


def make_thematic_stats_row(kpis: dict, keys: list[str], section_id: str = None) -> dbc.Row:
    """Build a row of thematic (smaller) KPI cards for a section.

    If section_id is provided, each card gets a clickable ID so callbacks
    can detect which card was clicked and switch the section chart.
    """
    cols = []
    for key in keys:
        kpi_data = kpis.get(key, {"label": key, "value": None, "status": "placeholder"})
        click_id = f"section-card-{section_id}-{key}" if section_id else None
        card = make_kpi_card(key, kpi_data, card_size="thematic", clickable_id=click_id)
        cols.append(
            dbc.Col(card, xs=12, sm=6, md=4, lg=3, className="mb-3")
        )
    return dbc.Row(cols, className="g-3")
