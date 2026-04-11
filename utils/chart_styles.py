"""
chart_styles.py — Shared chart styling constants for the Energy Transition Dashboard.

All chart-building modules should import from here to ensure visual consistency.
"""

# Font family used across all Plotly figures
CHART_FONT = dict(family="Inter, Helvetica Neue, Arial, sans-serif", size=12)

# Default margins (page-level charts)
CHART_MARGIN = dict(l=60, r=24, t=54, b=50)

# Compact margins (country-level and embedded charts)
CHART_MARGIN_COMPACT = dict(l=55, r=20, t=40, b=75)

# Background colors
PAPER_BG = "rgba(0,0,0,0)"
PLOT_BG = "#ffffff"

# Grid color for axes
GRID_COLOR = "#f0f0f0"

# Standard graph config (no mode bar, responsive)
GRAPH_CONFIG = {"responsive": True, "displayModeBar": False, "displaylogo": False}

# Graph config with mode bar (for stat/detail pages where download is useful)
GRAPH_CONFIG_WITH_MODEBAR = {"responsive": True, "displayModeBar": True, "displaylogo": False}


# ---------------------------------------------------------------------------
# Dashboard color palette (FLATLY theme)
# ---------------------------------------------------------------------------

# Status colors (tipping points, KPIs)
GREEN = "#18bc9c"
YELLOW = "#f39c12"
RED = "#e74c3c"
BLUE = "#3498db"
GRAY = "#95a5a6"
PRIMARY = "#2c3e50"

# Energy source colors (consistent across all charts)
SOURCE_COLORS = {
    "solar":   "#f1c40f",
    "wind":    "#3498db",
    "hydro":   "#1abc9c",
    "nuclear": "#9b59b6",
    "gas":     "#e67e22",
    "coal":    "#7f8c8d",
    "oil":     "#2c3e50",
    "biomass": "#27ae60",
    "other":   "#bdc3c7",
}

# Tipping point status colors
STATUS_COLORS = {
    "crossed": GREEN,
    "approaching": BLUE,
    "contested": YELLOW,
    "not_yet": GRAY,
}


def empty_figure(message: str = "No data available") -> dict:
    """Return a minimal empty Plotly figure with a centered message."""
    import plotly.graph_objects as go

    fig = go.Figure()
    fig.add_annotation(
        text=message, xref="paper", yref="paper", x=0.5, y=0.5,
        showarrow=False, font=dict(size=14, color=GRAY),
    )
    fig.update_layout(
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
        height=300, margin=dict(l=0, r=0, t=0, b=0),
    )
    return fig
