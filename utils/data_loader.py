"""
data_loader.py — Module-level data loading for the Energy Transition Dashboard.

All Parquet files are loaded ONCE at app startup and cached in module-level variables.
No Dash callback should ever read a Parquet file directly — use these accessor functions.

Homepage KPIs are pre-computed (kpis.json) and never require Parquet reads at request time.
"""

import json
from pathlib import Path
from functools import lru_cache

import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


# ---------------------------------------------------------------------------
# Module-level cache (loaded once at import time)
# ---------------------------------------------------------------------------

_CACHE: dict[str, pd.DataFrame] = {}
_KPI_CACHE: dict = {}


def _load(name: str) -> pd.DataFrame:
    """Load a Parquet file into the module cache. Returns empty DataFrame if missing."""
    if name not in _CACHE:
        path = PROCESSED_DIR / name
        if path.exists():
            _CACHE[name] = pd.read_parquet(path)
        else:
            print(f"[data_loader] WARNING: {name} not found. Run scripts/process_core.py first.")
            _CACHE[name] = pd.DataFrame()
    return _CACHE[name]


def _load_kpis() -> dict:
    """Load pre-computed KPIs from kpis.json."""
    global _KPI_CACHE
    if not _KPI_CACHE:
        path = PROCESSED_DIR / "kpis.json"
        if path.exists():
            with open(path) as f:
                _KPI_CACHE = json.load(f)
        else:
            print("[data_loader] WARNING: kpis.json not found. Run scripts/compute_kpis.py first.")
            _KPI_CACHE = {}
    return _KPI_CACHE


# ---------------------------------------------------------------------------
# Public accessors
# ---------------------------------------------------------------------------

def get_kpis() -> dict:
    """Return the pre-computed homepage KPI dictionary."""
    return _load_kpis()


def get_emissions() -> pd.DataFrame:
    """Return emissions data (country x year)."""
    return _load("emissions.parquet")


def get_energy_mix() -> pd.DataFrame:
    """Return energy mix data (country x year)."""
    return _load("energy_mix.parquet")


def get_capacity() -> pd.DataFrame:
    """Return installed capacity data (country x year)."""
    return _load("capacity.parquet")


def get_country_meta() -> pd.DataFrame:
    """Return country metadata (iso3, name, continent)."""
    return _load("country_meta.parquet")


def get_costs() -> pd.DataFrame:
    """Return cost data (LCOE, WACC). Empty until process_costs.py is run."""
    return _load("costs.parquet")


def get_finance() -> pd.DataFrame:
    """Return finance data (investment, subsidies, carbon price). Empty until process_finance.py."""
    return _load("finance.parquet")


def get_scenarios() -> pd.DataFrame:
    """Return IPCC scenario data. Empty until process_scenarios.py is run."""
    return _load("scenarios.parquet")


def get_nze_milestones() -> pd.DataFrame:
    """Return IEA NZE 2050 renewable capacity milestones."""
    return _load("nze_milestones.parquet")


def get_health() -> pd.DataFrame:
    """Return health data (ambient PM2.5 deaths, household deaths — separate columns).
    Empty until process_health.py is run.
    """
    return _load("health.parquet")


def get_damages() -> pd.DataFrame:
    """Return climate economic damage projections (Burke et al. 2015)."""
    return _load("damages.parquet")


def get_lancet_heat_mortality() -> pd.DataFrame:
    """Return global heat-related mortality time series (Lancet Countdown)."""
    return _load("lancet_heat_mortality.parquet")


_HEAT_REF_CACHE: dict = {}

def get_heat_deaths_reference() -> dict:
    """Return Lancet Countdown heat mortality reference data (from JSON)."""
    global _HEAT_REF_CACHE
    if not _HEAT_REF_CACHE:
        path = PROCESSED_DIR / "heat_deaths_reference.json"
        if path.exists():
            with open(path) as f:
                _HEAT_REF_CACHE = json.load(f)
        else:
            _HEAT_REF_CACHE = {}
    return _HEAT_REF_CACHE


def get_predictions() -> pd.DataFrame:
    """Return historical forecast vs actual data for solar, wind, and CCS.
    Run scripts/process_predictions.py to generate.
    """
    return _load("predictions.parquet")


def get_investment() -> pd.DataFrame:
    """Return IEA World Energy Investment data (global + regional, 2015-2025).
    Run scripts/process_investment.py to generate.
    """
    return _load("investment.parquet")


def get_subsidies() -> pd.DataFrame:
    """Return IEA fossil fuel subsidies by country (2010-2024).
    Run scripts/process_investment.py to generate.
    """
    return _load("subsidies.parquet")


def get_subsidy_indicators() -> pd.DataFrame:
    """Return subsidy indicators (rate, per capita, GDP share) for 2024.
    Run scripts/process_investment.py to generate.
    """
    return _load("subsidy_indicators.parquet")


def get_imf_subsidies() -> pd.DataFrame:
    """Return IMF fossil fuel subsidies (explicit + implicit) by country, 2015-2024.
    Covers 186 countries. Includes underpriced externalities (air pollution, climate).
    Source: IMF CPAT database.
    """
    return _load("imf_subsidies.parquet")


def get_imf_health_reference() -> pd.DataFrame:
    """Return IMF CPAT per-country fossil fuel death counts (2024 snapshot).
    Broader scope than McDuffie (includes household + ozone mortality).
    Source: IMF CPAT database, 'Baseline mortality, fossil fuels'.
    """
    return _load("imf_health_reference.parquet")


def get_ccus_projects() -> pd.DataFrame:
    """Return processed CCUS project data (IEA database).
    Run scripts/process_ccus.py to generate.
    """
    return _load("ccus_projects.parquet")


def get_vulnerability() -> pd.DataFrame:
    """Return ND-GAIN climate vulnerability/readiness data by country-year.
    Run scripts/process_ndgain.py to generate.
    """
    return _load("vulnerability.parquet")


def get_climate_disasters() -> pd.DataFrame:
    """Return EM-DAT climate disaster data aggregated by country-year.
    Run scripts/process_emdat.py to generate.
    """
    return _load("climate_disasters.parquet")


def get_callahan_damages() -> pd.DataFrame:
    """Return Callahan & Mankin (2022) historical temperature-GDP damages.
    Country-level cumulative and annualized GDP impact from warming (1990-2014).
    Source: Callahan & Mankin, Climatic Change, 2022.
    """
    return _load("climate_damages_callahan.parquet")


# ---------------------------------------------------------------------------
# Country-specific accessors
# ---------------------------------------------------------------------------

def get_country_emissions(iso3: str) -> pd.DataFrame:
    """Return emissions time series for a single country."""
    df = get_emissions()
    if df.empty:
        return df
    return df[df["iso3"] == iso3.upper()].copy()


def get_country_energy_mix(iso3: str) -> pd.DataFrame:
    """Return energy mix time series for a single country."""
    df = get_energy_mix()
    if df.empty:
        return df
    return df[df["iso3"] == iso3.upper()].copy()


def get_country_capacity(iso3: str) -> pd.DataFrame:
    """Return capacity time series for a single country."""
    df = get_capacity()
    if df.empty:
        return df
    return df[df["iso3"] == iso3.upper()].copy()


def get_country_finance(iso3: str) -> pd.DataFrame:
    """Return finance data (carbon pricing) for a single country."""
    df = get_finance()
    if df.empty:
        return df
    return df[df["iso3"] == iso3.upper()].copy()


def get_country_health(iso3: str) -> pd.DataFrame:
    """Return health data time series for a single country."""
    df = get_health()
    if df.empty:
        return df
    return df[df["iso3"] == iso3.upper()].copy()


def is_valid_iso3(iso3: str) -> bool:
    """Check if an ISO3 code exists in our country metadata."""
    meta = get_country_meta()
    if meta.empty:
        return False
    return iso3.upper() in meta["iso3"].values


def get_latest_year_map(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """
    For a country x year DataFrame, return the most recent non-null value
    of `col` for each country. Useful for choropleth map data.
    """
    if df.empty or col not in df.columns:
        return pd.DataFrame(columns=["iso3", col])

    result = (
        df[df[col].notna()]
        .sort_values("year")
        .groupby("iso3")
        .last()
        .reset_index()[["iso3", col]]
    )
    return result


# ---------------------------------------------------------------------------
# Trigger loading at import time so first dashboard request is fast
# ---------------------------------------------------------------------------

def get_ev_sales_share() -> pd.DataFrame:
    """Return EV sales share data (region x year, %)."""
    return _load("ev_sales_share.parquet")


def get_ev_sales() -> pd.DataFrame:
    """Return EV sales data (region x mode x year, absolute)."""
    return _load("ev_sales.parquet")


def get_ev_stock() -> pd.DataFrame:
    """Return EV stock data (region x year)."""
    return _load("ev_stock.parquet")


def get_electrification_kpis() -> dict:
    """Return pre-computed electrification KPIs."""
    if "electrification_kpis" not in _KPI_CACHE:
        path = PROCESSED_DIR / "electrification_kpis.json"
        if path.exists():
            with open(path) as f:
                _KPI_CACHE["electrification_kpis"] = json.load(f)
        else:
            _KPI_CACHE["electrification_kpis"] = {}
    return _KPI_CACHE["electrification_kpis"]


# ---------------------------------------------------------------------------
# S-curve / Trajectories page data (JSON)
# ---------------------------------------------------------------------------

_SCURVE_PARAMS_CACHE: dict = {}
_NASCENT_TECH_CACHE: dict = {}
_EXPERT_FORECASTS_CACHE: dict = {}
_TEMP_TRAJECTORY_CACHE: dict = {}


def get_scurve_params() -> dict:
    """Return pre-fitted S-curve parameters (from fit_scurves.py)."""
    global _SCURVE_PARAMS_CACHE
    if not _SCURVE_PARAMS_CACHE:
        path = PROCESSED_DIR / "scurve_params.json"
        if path.exists():
            with open(path) as f:
                _SCURVE_PARAMS_CACHE = json.load(f)
    return _SCURVE_PARAMS_CACHE


def get_nascent_tech_data() -> dict:
    """Return editorial data for nascent technologies (SAF, shipping, etc.)."""
    global _NASCENT_TECH_CACHE
    if not _NASCENT_TECH_CACHE:
        path = PROCESSED_DIR / "nascent_tech_data.json"
        if path.exists():
            with open(path) as f:
                _NASCENT_TECH_CACHE = json.load(f)
    return _NASCENT_TECH_CACHE


def get_expert_forecasts() -> dict:
    """Return expert forecast ranges (IEA, RMI, RethinkX, BNEF)."""
    global _EXPERT_FORECASTS_CACHE
    if not _EXPERT_FORECASTS_CACHE:
        path = PROCESSED_DIR / "expert_forecasts.json"
        if path.exists():
            with open(path) as f:
                _EXPERT_FORECASTS_CACHE = json.load(f)
    return _EXPERT_FORECASTS_CACHE


def get_temperature_trajectory() -> dict:
    """Return S-curve-based temperature trajectory data."""
    global _TEMP_TRAJECTORY_CACHE
    if not _TEMP_TRAJECTORY_CACHE:
        path = PROCESSED_DIR / "temperature_trajectory.json"
        if path.exists():
            with open(path) as f:
                _TEMP_TRAJECTORY_CACHE = json.load(f)
    return _TEMP_TRAJECTORY_CACHE


# ---------------------------------------------------------------------------
# Preload all data
# ---------------------------------------------------------------------------

def preload_all():
    """Pre-load all available Parquet files into cache. Call at app startup."""
    files = [
        "emissions.parquet", "energy_mix.parquet", "capacity.parquet",
        "country_meta.parquet", "costs.parquet", "finance.parquet",
        "scenarios.parquet", "nze_milestones.parquet", "health.parquet",
        "predictions.parquet", "damages.parquet", "lancet_heat_mortality.parquet",
        "investment.parquet", "subsidies.parquet", "subsidy_indicators.parquet",
        "ccus_projects.parquet", "vulnerability.parquet", "climate_disasters.parquet",
        "imf_subsidies.parquet", "imf_health_reference.parquet",
        "ev_sales_share.parquet", "ev_sales.parquet", "ev_stock.parquet",
    ]
    for f in files:
        _load(f)
    _load_kpis()
    get_electrification_kpis()
    # Load trajectory JSON files (silently skip if not yet generated)
    get_scurve_params()
    get_nascent_tech_data()
    get_expert_forecasts()
    get_temperature_trajectory()
    print("[data_loader] All available data files pre-loaded.")
