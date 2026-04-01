"""
formatting.py — Number formatting helpers for the Energy Transition Dashboard.

All display formatting goes through these functions so units and precision
are consistent across the dashboard.
"""


def fmt_gt(val, decimals=2) -> str:
    """Format GtCO2 value. e.g. 37.4 GtCO₂"""
    if val is None:
        return "N/A"
    return f"{val:.{decimals}f}"


def fmt_pct(val, decimals=1) -> str:
    """Format a percentage. e.g. 30.2%"""
    if val is None:
        return "N/A"
    return f"{val:.{decimals}f}%"


def fmt_gw(val, decimals=0) -> str:
    """Format GW capacity. e.g. 1,200 GW"""
    if val is None:
        return "N/A"
    return f"{val:,.{decimals}f}"


def fmt_ppm(val, decimals=2) -> str:
    """Format ppm (atmospheric CO2). e.g. 422.45 ppm"""
    if val is None:
        return "N/A"
    return f"{val:.{decimals}f}"


def fmt_temperature(val, decimals=2) -> str:
    """Format temperature anomaly. e.g. +1.32°C"""
    if val is None:
        return "N/A"
    sign = "+" if val > 0 else ""
    return f"{sign}{val:.{decimals}f}°C"


def fmt_trillion(val, decimals=1) -> str:
    """Format a value in trillions. e.g. $1.8T"""
    if val is None:
        return "N/A"
    return f"${val:.{decimals}f}T"


def fmt_million(val, decimals=1) -> str:
    """Format a value in millions. e.g. 4.2M"""
    if val is None:
        return "N/A"
    return f"{val:.{decimals}f}M"


def fmt_pct_change(val) -> str:
    """Format a percent change with sign. e.g. +12.3% or -5.1%"""
    if val is None:
        return ""
    sign = "+" if val > 0 else ""
    return f"{sign}{val:.1f}%"


def trend_color(trend_str: str, theme: str = "light") -> str:
    """Return a CSS color string for a trend indicator."""
    if "good" in trend_str:
        return "#2d7d46"   # green
    if "bad" in trend_str:
        return "#c0392b"   # red
    return "#7f8c8d"       # gray for stable
