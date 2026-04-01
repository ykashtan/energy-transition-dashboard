"""
world_map.py — Choropleth map builder for the Energy Transition Dashboard.

Builds go.Choropleth figures for the thematic map views:
  - Emissions: total GHG per capita
  - Renewables: grid carbon intensity
  - Total Energy Mix: renewable share of total final energy
  - Cost / Carbon Pricing: carbon pricing by country
  - Health: fossil-fuel PM2.5 deaths as % of all deaths + climate disaster deaths
  - Damages: climate-related economic damage as % of GDP
  - Vulnerability: ND-GAIN climate vulnerability score

All functions return a complete go.Figure with Equal Earth (natural earth) projection.
Missing/unavailable data countries render as gray with a "Data unavailable" tooltip.
"""

import plotly.graph_objects as go
import pandas as pd

from utils.data_loader import (
    get_emissions, get_energy_mix, get_finance, get_health, get_damages,
    get_vulnerability, get_climate_disasters, get_callahan_damages,
    get_latest_year_map,
)


# ---------------------------------------------------------------------------
# Metric registry — one entry per map theme button
# ---------------------------------------------------------------------------

METRIC_REGISTRY = {
    "emissions": {
        "label": "GHG Emissions per Capita",
        "column": "ghg_per_capita_t",
        "unit": "tCO₂e/yr",
        "colorscale": [
            [0.0, "#fff5f0"],
            [0.15, "#fcc3a0"],
            [0.35, "#f87d54"],
            [0.6,  "#d93c1e"],
            [0.85, "#9b1313"],
            [1.0,  "#5c0000"],
        ],
        "reversescale": False,
        "zmin": 0,
        "zmax": 30,  # tCO2e — saturates at ~30 for extreme outliers like Qatar/Kuwait
        "colorbar_title": "tCO₂e/yr<br>per capita",
        "description": (
            "Total GHG emissions per capita (CO₂, CH₄, N₂O, F-gases, AR6 GWP100). "
            "Source: EDGAR + PRIMAP-hist via Our World in Data."
        ),
        "dataset": "emissions",
        "secondary": [
            ("co2_fossil_mt", "Fossil CO₂", ".0f", "MtCO₂/yr"),
            ("co2_per_capita_t", "Fossil CO₂ per capita", ".1f", "tCO₂/yr"),
        ],
        "source_url": "https://github.com/owid/co2-data",
    },
    "renewables": {
        "label": "Grid Carbon Intensity",
        "column": "carbon_intensity_gco2_kwh",
        "unit": "gCO₂/kWh",
        "colorscale": [
            [0.0,  "#00441b"],
            [0.05, "#006d2c"],
            [0.12, "#2ca02c"],
            [0.25, "#74c476"],
            [0.4,  "#f7fcf0"],
            [0.55, "#f4a261"],
            [0.7,  "#e76f51"],
            [0.85, "#d62828"],
            [1.0,  "#6a040f"],
        ],
        "reversescale": False,
        "zmin": 0,
        "zmax": 900,
        "colorbar_title": "gCO₂/kWh",
        "description": (
            "Carbon intensity of electricity generation (gCO₂ per kWh). "
            "Lower = cleaner grid. Global avg: ~472 gCO₂/kWh. "
            "France ~42 (nuclear/hydro), Norway ~29 (hydro), India ~707 (coal). "
            "Source: Our World in Data (Ember)."
        ),
        "dataset": "energy_mix",
        "secondary": [
            ("renewable_share_electricity_pct", "Renewable share", ".1f", "%"),
            ("fossil_share_electricity_pct", "Fossil share", ".1f", "%"),
        ],
        "source_url": "https://github.com/owid/energy-data",
    },
    "total_energy": {
        "label": "Renewable Share of Total Energy",
        "column": "renewable_share_final_energy_pct",
        "unit": "%",
        "colorscale": [
            [0.0,  "#f7fbf2"],
            [0.15, "#d9f0a3"],
            [0.3,  "#addd8e"],
            [0.5,  "#78c679"],
            [0.7,  "#31a354"],
            [0.85, "#006d2c"],
            [1.0,  "#00441b"],
        ],
        "reversescale": False,
        "zmin": 0,
        "zmax": 80,
        "colorbar_title": "% of total<br>final energy",
        "description": (
            "Renewables as share of total final energy consumption (not just electricity). "
            "~13% globally — much lower than the ~30% share of electricity, because "
            "electricity is only ~20% of total energy use. Transport, industrial heat, "
            "and buildings account for the rest. Source: Our World in Data."
        ),
        "dataset": "energy_mix",
        "secondary": [
            ("renewable_share_electricity_pct", "Renewable share of electricity", ".1f", "%"),
            ("fossil_share_final_energy_pct", "Fossil share of total energy", ".1f", "%"),
        ],
        "source_url": "https://github.com/owid/energy-data",
    },
    "cost": {
        "label": "Carbon Pricing",
        "column": "carbon_price_usd_tco2",
        "unit": "$/tCO₂",
        "colorscale": [
            [0.0,  "#f7fbff"],
            [0.15, "#c6dbef"],
            [0.35, "#6baed6"],
            [0.6,  "#2171b5"],
            [0.85, "#08519c"],
            [1.0,  "#08306b"],
        ],
        "reversescale": False,
        "zmin": 0,
        "zmax": 140,
        "colorbar_title": "$/tCO₂",
        "description": (
            "Effective carbon price (ETS or carbon tax) in USD/tCO₂e. "
            "Gray = no national carbon pricing scheme. "
            "Global clean energy investment: $2.2T in 2025 (IEA WEI 2025), "
            "now exceeding fossil fuel investment (~$1.1T). "
            "Source: World Bank Carbon Pricing Dashboard 2023."
        ),
        "dataset": "finance",
        "secondary": [],
        "source_url": "https://carbonpricingdashboard.worldbank.org/",
    },
    "health": {
        "label": "Air Pollution & Climate Deaths",
        "column": "fossil_fuel_death_pct_all",
        "unit": "% of all deaths",
        "colorscale": [
            [0.0,  "#fff5f0"],
            [0.1,  "#fee0d2"],
            [0.2,  "#fcbba1"],
            [0.35, "#fc9272"],
            [0.5,  "#fb6a4a"],
            [0.65, "#ef3b2c"],
            [0.8,  "#cb181d"],
            [1.0,  "#67000d"],
        ],
        "reversescale": False,
        "zmin": 0,
        "zmax": 8,  # most countries 0-8%; extreme outliers like China ~5-6%
        "colorbar_title": "% of all<br>deaths",
        "description": (
            "Fossil fuel PM2.5 deaths as a share of all deaths in each country. "
            "Deaths are attributed to fossil fuel combustion only (~33% of all ambient "
            "PM2.5 deaths globally, ~1.27M/yr; McDuffie et al. 2021). PM2.5 only — does "
            "not include NO₂, SO₂, or ozone mortality. PM2.5 exposure in hover is from ALL "
            "sources (not fossil-fuel only). Source: McDuffie et al. 2021; population from OWID."
        ),
        "dataset": "health_enriched",
        "secondary": [
            ("fossil_fuel_deaths", "Fossil fuel PM2.5 deaths", ",.0f", "thousands/yr"),
            ("climate_disaster_deaths", "Weather/climate disaster deaths (cumul. 2000–2025)", ",.0f", ""),
            ("climate_disaster_death_pct_all", "Weather/climate disaster deaths (% of all deaths/yr)", ".3f", "%"),
            ("pm25_annual_mean_ugm3", "PM2.5 exposure (total, all sources)", ".1f", "μg/m³"),
        ],
        "health_caveat": (
            "Fossil fuel combustion (coal, oil, gas) accounts for ~33% of global "
            "ambient PM2.5 deaths (~1.3M of ~4.9M; McDuffie et al. 2021). "
            "Higher estimates (5–9M; Vohra et al. 2021, Lelieveld et al. 2023) use "
            "different concentration-response functions. PM2.5 exposure shown is from "
            "ALL sources (not fossil-fuel only). Does not include NO₂, SO₂, or ozone "
            "mortality. Climate disaster deaths (EM-DAT) are cumulative since 2000."
        ),
        "source_url": "https://doi.org/10.1038/s41467-021-23853-y",
    },
    "investment": {
        "label": "Carbon Pricing & Investment",
        "column": "carbon_price_usd_tco2",
        "unit": "$/tCO₂",
        "colorscale": [
            [0.0,  "#f7fcf5"],
            [0.15, "#c7e9c0"],
            [0.35, "#74c476"],
            [0.6,  "#31a354"],
            [0.85, "#006d2c"],
            [1.0,  "#00441b"],
        ],
        "reversescale": False,
        "zmin": 0,
        "zmax": 140,
        "colorbar_title": "$/tCO₂",
        "description": (
            "Carbon pricing by country overlaid with global clean energy investment context. "
            "Global clean energy investment reached $2.2T in 2025 (IEA WEI 2025), "
            "now exceeding fossil fuel investment (~$1.1T). "
            "Gray = no national carbon pricing scheme. "
            "Source: World Bank 2023; IEA World Energy Investment 2025."
        ),
        "dataset": "finance",
        "secondary": [],
        "source_url": "https://www.iea.org/reports/world-energy-investment-2025",
    },
    "damages": {
        "label": "Climate Economic Damages",
        "column": "climate_damage_pct_gdp",
        "unit": "% of GDP/yr",
        "colorscale": [
            [0.0,  "#67000d"],   # dark red = most damaged (negative values, hot countries)
            [0.15, "#d62828"],
            [0.3,  "#f4a261"],
            [0.45, "#fddbc7"],
            [0.5,  "#f7f7f7"],   # white = neutral (zero impact)
            [0.55, "#c6dbef"],
            [0.7,  "#4292c6"],
            [0.85, "#2171b5"],
            [1.0,  "#08306b"],   # dark blue = most benefited (positive values, cold countries)
        ],
        "reversescale": False,
        "zmin": -2,
        "zmax": 2,  # ±2% of GDP/yr; diverging scale centered on 0
        "colorbar_title": "% GDP/yr<br>(warming<br>impact)",
        "description": (
            "Historical economic impact of warming (1990–2014) using the Burke et al. "
            "(2015) temperature-GDP damage function applied to observed country-level "
            "temperature changes. Hot countries lose GDP; cold countries gain. Annualized "
            "average as % of current GDP. Based on top 20 emitters (~90% of global emissions). "
            "Source: Callahan & Mankin (2022), Climatic Change."
        ),
        "dataset": "callahan_damages",
        "secondary": [
            ("cumul_climate_gdp_change_bn", "Cumulative GDP change (1990–2014)", "+,.0f", "$B"),
            ("annual_climate_gdp_change_bn", "Annual avg GDP change", "+,.1f", "$B/yr"),
        ],
        "source_url": "https://link.springer.com/article/10.1007/s10584-022-03387-y",
    },
    "vulnerability": {
        "label": "Climate Vulnerability (ND-GAIN)",
        "column": "vulnerability",
        "unit": "score",
        "colorscale": [
            [0.0,  "#f7fcf5"],
            [0.15, "#d9f0a3"],
            [0.3,  "#addd8e"],
            [0.5,  "#f4a261"],
            [0.7,  "#e76f51"],
            [0.85, "#d62828"],
            [1.0,  "#67000d"],
        ],
        "reversescale": False,
        "zmin": 0.2,
        "zmax": 0.65,
        "colorbar_title": "Vulnerability<br>(0–1)",
        "description": (
            "ND-GAIN climate vulnerability score (0–1, higher = more vulnerable). "
            "Combines exposure, sensitivity, and adaptive capacity across food, "
            "water, health, infrastructure, habitat, and ecosystems. "
            "Source: Notre Dame Global Adaptation Initiative (ND-GAIN) 2023."
        ),
        "dataset": "vulnerability",
        "secondary": [
            ("readiness", "Climate readiness", ".2f", "(0–1)"),
            ("gain_score", "ND-GAIN score", ".1f", "(0–100)"),
        ],
        "source_url": "https://gain.nd.edu/our-work/country-index/",
    },
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_raw_df(dataset: str) -> pd.DataFrame:
    """Return the raw DataFrame for a given dataset key."""
    if dataset == "emissions":
        return get_emissions()
    if dataset == "energy_mix":
        return get_energy_mix()
    if dataset == "finance":
        return get_finance()
    if dataset == "callahan_damages":
        return get_callahan_damages()
    if dataset == "health":
        return get_health()
    if dataset == "damages":
        return get_damages()
    if dataset == "vulnerability":
        return get_vulnerability()
    if dataset == "climate_disasters_total":
        # Aggregate EM-DAT to cumulative totals per country
        df = get_climate_disasters()
        if df.empty:
            return df
        totals = df.groupby("iso3").agg(
            total_deaths=("total_deaths", "sum"),
            total_affected=("total_affected", "sum"),
            n_disasters=("n_disasters", "sum"),
            total_damage_adj_musd=("total_damage_adj_musd", "sum"),
        ).reset_index()
        return totals

    if dataset == "health_enriched":
        return _build_health_enriched()

    if dataset == "damages_enriched":
        return _build_damages_enriched()

    return pd.DataFrame()


# Global average crude death rate ~8.1 per 1,000 (WHO 2020 estimate).
# Used to approximate total deaths per country when country-specific rates
# are unavailable. This is rough — actual rates range from ~2/1000 (Qatar)
# to ~15/1000 (some Sub-Saharan African countries).
_CRUDE_DEATH_RATE_PER_1000 = 8.1


def _build_health_enriched() -> pd.DataFrame:
    """Build enriched health dataset with death fractions and climate disaster deaths."""
    health = get_health()
    emissions = get_emissions()
    disasters = get_climate_disasters()

    if health.empty:
        return health

    # Get latest fossil_fuel_deaths per country from health data
    health_latest = get_latest_year_map(health, "fossil_fuel_deaths")

    # Add PM2.5 exposure
    if "pm25_annual_mean_ugm3" in health.columns:
        pm25 = get_latest_year_map(health, "pm25_annual_mean_ugm3")
        health_latest = health_latest.merge(pm25[["iso3", "pm25_annual_mean_ugm3"]], on="iso3", how="left")

    # Get latest population per country
    if not emissions.empty and "population" in emissions.columns:
        pop = get_latest_year_map(emissions, "population")
        health_latest = health_latest.merge(pop[["iso3", "population"]], on="iso3", how="left")

        # Compute fossil fuel deaths as % of all deaths
        # fossil_fuel_deaths is in thousands; population in absolute numbers
        # estimated total deaths = population * crude_death_rate / 1000
        health_latest["est_total_deaths"] = (
            health_latest["population"] * _CRUDE_DEATH_RATE_PER_1000 / 1000
        )
        health_latest["fossil_fuel_death_pct_all"] = (
            health_latest["fossil_fuel_deaths"] * 1000
            / health_latest["est_total_deaths"]
            * 100
        )
    else:
        health_latest["fossil_fuel_death_pct_all"] = float("nan")

    # Add cumulative climate disaster deaths + annualized fraction
    if not disasters.empty:
        disaster_totals = disasters.groupby("iso3").agg(
            climate_disaster_deaths=("total_deaths", "sum"),
        ).reset_index()
        health_latest = health_latest.merge(disaster_totals, on="iso3", how="left")

        # Annualize disaster deaths over the period (~25 years, 2000-2025)
        # and compute as % of estimated annual deaths
        n_years = 25
        if "est_total_deaths" in health_latest.columns:
            health_latest["climate_disaster_death_pct_all"] = (
                health_latest["climate_disaster_deaths"] / n_years
                / health_latest["est_total_deaths"]
                * 100
            )
        else:
            health_latest["climate_disaster_death_pct_all"] = float("nan")
    else:
        health_latest["climate_disaster_deaths"] = float("nan")
        health_latest["climate_disaster_death_pct_all"] = float("nan")

    return health_latest


def _build_damages_enriched() -> pd.DataFrame:
    """Build enriched damages dataset with economic damage as % of GDP."""
    disasters = get_climate_disasters()
    emissions = get_emissions()

    if disasters.empty:
        return disasters

    # Aggregate EM-DAT to cumulative totals per country
    totals = disasters.groupby("iso3").agg(
        total_deaths=("total_deaths", "sum"),
        total_affected=("total_affected", "sum"),
        n_disasters=("n_disasters", "sum"),
        total_damage_musd=("total_damage_adj_musd", "sum"),
    ).reset_index()

    # Merge with latest GDP
    if not emissions.empty and "gdp_usd" in emissions.columns:
        gdp = get_latest_year_map(emissions, "gdp_usd")
        totals = totals.merge(gdp[["iso3", "gdp_usd"]], on="iso3", how="left")

        # Compute cumulative damage as % of latest annual GDP
        # total_damage_musd is in millions of USD; gdp_usd is in USD
        totals["damage_pct_gdp"] = (
            totals["total_damage_musd"] * 1e6
            / totals["gdp_usd"]
            * 100
        )
    else:
        totals["damage_pct_gdp"] = float("nan")

    return totals


def _format_val(val, fmt: str, unit: str) -> str:
    """Format a single value for tooltip display."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "n/a"
    try:
        formatted = f"{val:{fmt}}"
        return f"{formatted} {unit}".strip()
    except (ValueError, TypeError):
        return f"{val} {unit}".strip()


def _build_hover_text(row: pd.Series, cfg: dict) -> str:
    """Build multi-line hover tooltip for a single country row."""
    name = row.get("country_name", row.get("iso3", "Unknown"))
    primary_col = cfg["column"]
    pval = row.get(primary_col) if primary_col else None

    if pval is None or (isinstance(pval, float) and pd.isna(pval)):
        header = f"<b>{name}</b><br><span style='color:#999'>Data unavailable</span>"
        return header

    lines = [
        f"<b>{name}</b>",
        f"{cfg['label']}: {_format_val(pval, '.2f', cfg['unit'])}",
    ]
    for col, label, fmt, unit in cfg.get("secondary", []):
        sval = row.get(col)
        lines.append(f"{label}: {_format_val(sval, fmt, unit)}")

    # Add caveat note for health metric
    if cfg.get("health_caveat"):
        lines.append(
            f"<span style='color:#999; font-size:0.85em'>"
            f"Note: PM2.5 exposure is total (all sources).</span>"
        )

    return "<br>".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_map_figure(metric_key: str, country_meta: pd.DataFrame) -> go.Figure:
    """
    Build a go.Choropleth figure for the given metric key.

    Parameters
    ----------
    metric_key : str
        One of: 'emissions', 'renewables', 'cost', 'health', 'investment'
    country_meta : pd.DataFrame
        country_meta.parquet with columns: iso3, country_name, continent

    Returns
    -------
    go.Figure
        Ready-to-render Plotly figure. Gray countries = missing data.
    """
    cfg = METRIC_REGISTRY.get(metric_key, METRIC_REGISTRY["emissions"])

    # --- No data available state ---
    if cfg["column"] is None or cfg["dataset"] is None:
        return _build_coming_soon_figure(cfg)

    # --- Load and flatten data ---
    raw_df = _get_raw_df(cfg["dataset"])
    if raw_df.empty:
        return _build_coming_soon_figure(cfg)

    # Get most recent non-null value per country for primary column
    # Some datasets (e.g., damages) are already flat (one row per country, no year)
    if "year" in raw_df.columns:
        map_df = get_latest_year_map(raw_df, cfg["column"])
    else:
        # Flat dataset: just select iso3 + primary column
        map_df = raw_df[["iso3", cfg["column"]]].dropna(subset=[cfg["column"]]).copy()

    # Add secondary columns (latest available value per country)
    for col, *_ in cfg.get("secondary", []):
        if col in raw_df.columns:
            if "year" in raw_df.columns:
                sec = get_latest_year_map(raw_df, col)
            else:
                sec = raw_df[["iso3", col]].dropna(subset=[col])
            if not sec.empty:
                map_df = map_df.merge(sec[["iso3", col]], on="iso3", how="left")

    # --- Build display DataFrame: all countries, gray for missing ---
    # Starting from country_meta ensures gray rendering for countries with no data
    if not country_meta.empty:
        display_df = country_meta[["iso3", "country_name"]].merge(
            map_df, on="iso3", how="left"
        )
    else:
        display_df = map_df.copy()
        display_df["country_name"] = display_df["iso3"]

    # Build hover text
    display_df["_hover"] = display_df.apply(
        lambda row: _build_hover_text(row, cfg), axis=1
    )

    z_vals = display_df[cfg["column"]].tolist()

    # Build choropleth trace
    trace = go.Choropleth(
        locations=display_df["iso3"],
        z=z_vals,
        locationmode="ISO-3",
        colorscale=cfg["colorscale"],
        reversescale=cfg["reversescale"],
        zmin=cfg.get("zmin"),
        zmax=cfg.get("zmax"),
        hovertext=display_df["_hover"],
        hovertemplate="%{hovertext}<extra></extra>",
        marker_line_color="white",
        marker_line_width=0.5,
        colorbar=dict(
            title=dict(
                text=cfg["colorbar_title"],
                side="right",
                font=dict(size=11),
            ),
            thickness=14,
            len=0.55,
            y=0.5,
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#dee2e6",
            borderwidth=1,
        ),
    )

    fig = go.Figure(trace)
    _apply_geo_layout(fig)
    return fig


def _build_coming_soon_figure(cfg: dict) -> go.Figure:
    """Return a figure with a centered informational message when data is unavailable."""
    fig = go.Figure()
    # Empty choropleth to render the base map (all gray)
    fig.add_trace(go.Choropleth(
        locations=[],
        z=[],
        locationmode="ISO-3",
        colorscale=[[0, "#e8e8e8"], [1, "#e8e8e8"]],
        showscale=False,
    ))
    fig.add_annotation(
        text=(
            f"<b>{cfg['label']}</b><br>"
            f"<span style='font-size:13px; color:#6c757d'>{cfg['description']}</span>"
        ),
        xref="paper", yref="paper",
        x=0.5, y=0.15,
        showarrow=False,
        font=dict(size=15, color="#343a40"),
        align="center",
        bgcolor="rgba(255,255,255,0.92)",
        bordercolor="#dee2e6",
        borderwidth=1,
        borderpad=12,
    )
    _apply_geo_layout(fig)
    return fig


def _apply_geo_layout(fig: go.Figure):
    """Apply consistent geo projection and layout to any choropleth figure."""
    fig.update_geos(
        projection_type="natural earth",
        showcoastlines=True,
        coastlinecolor="rgba(255,255,255,0.7)",
        coastlinewidth=0.5,
        showland=True,
        landcolor="#d4d4d4",    # gray for countries with no data / base land
        showocean=True,
        oceancolor="#dceeff",
        showlakes=False,
        showframe=False,
        bgcolor="rgba(0,0,0,0)",
        lataxis_range=[-60, 85],  # clip Antarctica — saves ~20% vertical space
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        geo_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Helvetica Neue, Arial, sans-serif", size=12),
        height=460,
        dragmode=False,  # disable drag to pan — feels broken on mobile
        modebar_remove=[
            "zoom", "pan", "select", "lasso2d", "zoomIn2d", "zoomOut2d",
            "autoScale2d", "resetScale2d",
        ],
    )
