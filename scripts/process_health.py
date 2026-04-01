"""
process_health.py — Processes health and environmental justice datasets.

Outputs:
  data/processed/health.parquet    — country × year health/EJ data
  data/processed/deaths_per_twh.json — reference deaths/TWh values by energy source
  data/processed/heat_deaths_reference.json — Lancet Countdown heat mortality reference

Schema for health.parquet:
  iso3, year,
  deaths_ambient_pm25      — ambient (outdoor) PM2.5 deaths (thousands/yr) — GBD/IHME placeholder
  deaths_household_air     — household air pollution deaths (thousands/yr) — GBD/IHME placeholder
  pm25_annual_mean_ugm3    — population-weighted mean PM2.5 exposure (μg/m³) — World Bank WDI
  pct_electricity_access   — % population with electricity access — World Bank WDI
  pct_clean_cooking        — % population with clean cooking fuel access — World Bank WDI
  deaths_per_twh_energy_mix — estimated deaths/TWh for this country's electricity mix
                               (comparative framing only; see caveats in deaths_per_twh.json)
  heatwave_days_cc         — heatwave days attributable to climate change — Lancet Countdown 2025
  fossil_fuel_deaths       — PM2.5 deaths attributable to fossil fuel combustion (thousands/yr)
                              — McDuffie et al. 2021, 2017 cross-section
  fossil_fuel_pct          — % of ambient PM2.5 deaths from fossil fuel sectors — McDuffie et al. 2021

CRITICAL SCIENTIFIC CONVENTIONS (enforced here and everywhere downstream):
  - deaths_ambient_pm25 and deaths_household_air are SEPARATE columns, NEVER summed
    when contextualizing energy transition impacts.
  - deaths_ambient_pm25: directly reducible by electricity decarbonization / industry
  - deaths_household_air: requires clean cooking access programs; NOT an electricity-
    transition issue
  - deaths_per_twh_energy_mix: comparative orders of magnitude only, not precision
    mortality. Tooltip and caveat required on every display instance.
  - Avoided deaths are NOT calculated here. For US: use EPA COBRA/AVERT pipeline.
    For non-US: present current fossil health burden as context only.
  - heatwave_days_cc: climate change attribution only; separate from air pollution

Data sources:
  1. World Bank WDI (API): electricity access %, clean cooking access %, PM2.5 exposure
     — Downloaded automatically; no registration required.
  2. GBD/IHME mortality data: requires free IHME account + manual download.
     — This script creates a correctly-schemed placeholder and prints instructions.
     — GBD 2023 bulk download (IHME-GBD_2023_DATA-*.csv) parsed if available,
       but country-level air pollution data requires a specific GBD query.
  3. OWID deaths/TWh reference values: embedded (Markandya & Wilkinson 2007, Sovacool 2008,
     updated GBD estimates via OWID). Used for comparative country energy-mix calculation.
  4. Country energy mix: from energy_mix.parquet (already processed by process_core.py).
  5. Lancet Countdown 2025: heatwave days attributable to climate change (country-level),
     heat-related mortality (global reference).
     https://lancetcountdown.org/2025-report/
"""

import json
import sys
import time
from pathlib import Path

import pandas as pd
import numpy as np
import requests

PROJECT_ROOT = Path(__file__).parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

import logging
logging.getLogger("country_converter").setLevel(logging.ERROR)


# ---------------------------------------------------------------------------
# Deaths per TWh reference values (OWID / Markandya & Wilkinson 2007 / GBD)
# ---------------------------------------------------------------------------
# These are comparative orders of magnitude, NOT precision mortality rates.
# Uncertainty spans an order of magnitude for some sources.
# Coal estimate reflects global average; dominated by older coal plants in Asia.
# See: https://ourworldindata.org/safest-sources-of-energy

DEATHS_PER_TWH = {
    "coal":    24.6,   # deaths per TWh — Markandya & Wilkinson (2007), updated GBD
    "oil":     18.4,
    "gas":      2.8,
    "nuclear":  0.07,
    "wind":     0.04,
    "solar":    0.02,
    "hydro":    0.02,   # global average; excludes Banqiao dam outlier
    "biomass":  4.5,    # traditional biomass; large uncertainty
    "other":    2.0,    # conservative placeholder
}

DEATHS_PER_TWH_METADATA = {
    "source": "Markandya & Wilkinson (2007) Lancet; Sovacool (2008); GBD-based OWID estimates",
    "owid_url": "https://ourworldindata.org/safest-sources-of-energy",
    "methodology_note": (
        "These are comparative orders of magnitude derived from lifecycle analysis studies "
        "with heterogeneous methodologies. Estimates reflect central tendency across studies; "
        "uncertainty spans an order of magnitude for some sources (especially nuclear). "
        "Coal estimate dominated by older Chinese plants; modern coal rates lower. "
        "Do NOT use these to calculate avoided deaths directly — see AVOIDED_DEATHS_METHODOLOGY "
        "in utils/definitions.py."
    ),
    "use_guidance": (
        "Present as: 'Coal causes roughly 1,000× more deaths per unit of energy than wind/solar.' "
        "Always link to OWID methodology. Never present as precision mortality rates."
    ),
    "values": DEATHS_PER_TWH,
}


# ---------------------------------------------------------------------------
# World Bank WDI API helper
# ---------------------------------------------------------------------------

WB_API_BASE = "http://api.worldbank.org/v2/country/all/indicator/{indicator}"
WB_INDICATORS = {
    "pct_electricity_access": "EG.ELC.ACCS.ZS",   # Access to electricity (% of population)
    "pct_clean_cooking":      "EG.CFT.ACCS.ZS",   # Access to clean fuels for cooking (%)
    "pm25_annual_mean_ugm3":  "EN.ATM.PM25.MC.M3", # PM2.5 air pollution, mean annual (μg/m³)
}


def fetch_wb_indicator(indicator_code: str, start_year: int = 1990, end_year: int = 2023,
                       retries: int = 3) -> pd.DataFrame:
    """
    Download a World Bank WDI indicator for all countries.

    Returns a DataFrame with columns: iso3, year, value
    """
    url = WB_API_BASE.format(indicator=indicator_code)
    params = {
        "format": "json",
        "per_page": 20000,
        "date": f"{start_year}:{end_year}",
        "mrv": 34,  # most recent values going back 34 years
    }

    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=60)
            resp.raise_for_status()
            data = resp.json()

            # WB API response: [metadata_dict, [records...]]
            if not data or len(data) < 2 or not data[1]:
                print(f"  [WARN] No data returned for indicator {indicator_code}")
                return pd.DataFrame(columns=["iso3", "year", "value"])

            records = []
            for rec in data[1]:
                if rec.get("value") is None:
                    continue
                country = rec.get("countryiso3code") or (rec.get("country", {}) or {}).get("id", "")
                if not country or len(country) != 3:
                    continue
                try:
                    year = int(rec["date"])
                    val = float(rec["value"])
                    records.append({"iso3": country.upper(), "year": year, "value": val})
                except (ValueError, TypeError):
                    continue

            return pd.DataFrame(records)

        except requests.RequestException as e:
            print(f"  [WARN] WB API attempt {attempt+1}/{retries} failed for {indicator_code}: {e}")
            if attempt < retries - 1:
                time.sleep(5 * (attempt + 1))

    return pd.DataFrame(columns=["iso3", "year", "value"])


def download_world_bank_data() -> pd.DataFrame:
    """Download all WB WDI health indicators and merge into a single country×year DataFrame."""
    frames = {}
    for col_name, code in WB_INDICATORS.items():
        print(f"  Downloading World Bank {col_name} ({code})...")
        df = fetch_wb_indicator(code)
        if df.empty:
            print(f"    → No data retrieved; column will be NaN")
        else:
            print(f"    → {len(df):,} country-year records")
        frames[col_name] = df

    # Build a full country×year grid from all available ISO3s and years
    all_iso3 = set()
    all_years = set()
    for df in frames.values():
        if not df.empty:
            all_iso3.update(df["iso3"].unique())
            all_years.update(df["year"].unique())

    if not all_iso3:
        return pd.DataFrame()

    # Create full grid
    grid = pd.DataFrame(
        [(iso3, year) for iso3 in all_iso3 for year in sorted(all_years)],
        columns=["iso3", "year"],
    )

    # Merge each indicator
    for col_name, df in frames.items():
        if not df.empty:
            df_renamed = df.rename(columns={"value": col_name})
            grid = grid.merge(df_renamed[["iso3", "year", col_name]], on=["iso3", "year"], how="left")
        else:
            grid[col_name] = np.nan

    return grid


# ---------------------------------------------------------------------------
# GBD/IHME mortality data (manual download required)
# ---------------------------------------------------------------------------

GBD_INSTRUCTIONS = """
================================================================================
GBD/IHME Health Data — Manual Download Required
================================================================================

GBD (Global Burden of Disease) mortality data requires a free IHME account.
Follow these steps to download and integrate the data:

1. Create a free account at: https://vizhub.healthdata.org/gbd-results/

2. Use the GBD Results Tool to download:
   Query A (ambient PM2.5):
     - Measure: Deaths
     - Cause: Air pollution (ambient particulate matter pollution)
     - Location: All countries
     - Age: All ages (age-standardized)
     - Sex: Both
     - Year: 1990-2023
     - Format: CSV
   Save as: data/raw/gbd_deaths_ambient_pm25.csv

   Query B (household air pollution):
     - Measure: Deaths
     - Cause: Air pollution (household air pollution from solid fuels)
     - Location: All countries
     - Age: All ages
     - Sex: Both
     - Year: 1990-2023
     - Format: CSV
   Save as: data/raw/gbd_deaths_household_air.csv

3. Alternative: State of Global Air (HEI) — built on GBD 2023:
   https://www.stateofglobalair.org/data
   → "Burden of Disease" → "Air Pollution" → Download CSV
   Save as: data/raw/state_of_global_air.csv

4. After downloading, re-run:  python scripts/process_health.py

IMPORTANT: Keep ambient PM2.5 deaths and household air pollution deaths
SEPARATE in all analysis and display. They have different policy levers:
  - Ambient PM2.5: reduced by decarbonizing electricity/industry
  - Household: requires clean cooking access programs (unrelated to grid)
================================================================================
"""

GBD_PLACEHOLDER_VALUES = {
    # Approximate 2019 GBD values (millions/yr) for reference placeholder
    # Source: GBD 2019 Lancet, Cohen et al. 2017, HEI State of Global Air 2023
    # These are GLOBAL estimates only; country-level requires manual GBD download
    "global_deaths_ambient_pm25_m": 4.14,   # ~4.1M/yr ambient PM2.5 (GBD 2019)
    "global_deaths_household_air_m": 3.2,   # ~3.2M/yr household solid fuels (GBD 2019)
    "data_year": 2019,
    "note": "Global totals only — country-level data requires GBD manual download",
}


def build_gbd_placeholder(country_iso3_list: list) -> pd.DataFrame:
    """
    Create a correctly-schemed placeholder GBD DataFrame.
    All values are NaN until the user downloads and integrates GBD data.
    """
    years = list(range(1990, 2024))
    records = [
        {"iso3": iso3, "year": year,
         "deaths_ambient_pm25": np.nan,
         "deaths_household_air": np.nan}
        for iso3 in country_iso3_list
        for year in years
    ]
    return pd.DataFrame(records)


def try_load_gbd_csv(filename: str, cause_type: str) -> pd.DataFrame:
    """
    Attempt to load a manually-downloaded GBD CSV.
    Returns empty DataFrame (correctly schemed) if file not found.

    cause_type: 'ambient' or 'household'
    col_name maps to: deaths_ambient_pm25 or deaths_household_air
    """
    col_name = "deaths_ambient_pm25" if cause_type == "ambient" else "deaths_household_air"
    path = RAW_DIR / filename
    if not path.exists():
        return pd.DataFrame(columns=["iso3", "year", col_name])

    try:
        df = pd.read_csv(path, low_memory=False)
        print(f"  Loaded {filename} ({len(df)} rows)")

        # Detect GBD column names (they vary slightly by download version)
        # Standard GBD columns include: location_name, location_id, year, val, cause_name
        col_map = {}
        for c in df.columns:
            cl = c.strip().lower()
            if cl in ("val", "value", "mean"):
                col_map["val"] = c
            elif cl in ("year", "year_id"):
                col_map["year"] = c
            elif cl in ("location_name",):
                col_map["location"] = c
            elif cl in ("iso3", "location_iso3"):
                col_map["iso3"] = c

        # Convert location names to ISO3 if needed
        if "iso3" not in col_map and "location" in col_map:
            import country_converter as coco
            df["iso3"] = coco.convert(df[col_map["location"]].tolist(), to="ISO3",
                                      not_found=None)
        elif "iso3" in col_map:
            df["iso3"] = df[col_map["iso3"]]

        if "val" not in col_map or "year" not in col_map or "iso3" not in df.columns:
            print(f"  [WARN] Could not parse {filename}: unexpected columns {list(df.columns)[:8]}")
            return pd.DataFrame(columns=["iso3", "year", col_name])

        result = df[["iso3", col_map["year"], col_map["val"]]].copy()
        result.columns = ["iso3", "year", col_name]
        result["iso3"] = result["iso3"].str.upper()
        result["year"] = result["year"].astype(int)
        # GBD reports deaths in raw counts; convert to thousands
        result[col_name] = pd.to_numeric(result[col_name], errors="coerce") / 1000
        return result[result["iso3"].notna() & (result["iso3"] != "NONE")]

    except Exception as e:
        print(f"  [WARN] Failed to parse {filename}: {e}")
        return pd.DataFrame(columns=["iso3", "year", col_name])


# ---------------------------------------------------------------------------
# GBD 2023 bulk download handler
# ---------------------------------------------------------------------------

GBD_BULK_DIR = RAW_DIR / "gbd_unzipped"

def try_load_gbd_bulk() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Attempt to parse the GBD 2023 bulk download (IHME-GBD_2023_DATA-*.csv).

    The GBD bulk download may contain global-level or country-level data
    depending on what was queried. This function detects the structure and
    extracts air-pollution-attributable deaths if the correct risk factors
    are present.

    Returns:
        (ambient_df, household_df) — each with columns [iso3, year, deaths_*]
        Empty DataFrames if the file doesn't contain air pollution data.
    """
    import glob as glob_mod
    pattern = str(GBD_BULK_DIR / "IHME-GBD_*.csv")
    files = glob_mod.glob(pattern)
    if not files:
        return pd.DataFrame(), pd.DataFrame()

    csv_path = files[0]
    try:
        df = pd.read_csv(csv_path, low_memory=False)
        print(f"  Loaded GBD bulk file: {Path(csv_path).name} ({len(df):,} rows)")
    except Exception as e:
        print(f"  [WARN] Failed to read GBD bulk file: {e}")
        return pd.DataFrame(), pd.DataFrame()

    # Check if this contains air pollution risk factor data
    cause_col = "cause_name" if "cause_name" in df.columns else None
    if cause_col is None:
        print("  [WARN] GBD bulk file missing 'cause_name' column")
        return pd.DataFrame(), pd.DataFrame()

    causes = df[cause_col].unique()
    # GBD risk factor names for air pollution
    ambient_causes = [c for c in causes if "ambient" in c.lower() and "particulate" in c.lower()]
    household_causes = [c for c in causes if "household" in c.lower() and "air" in c.lower()]

    # Check for country-level data
    n_locations = df["location_name"].nunique() if "location_name" in df.columns else 0
    print(f"  GBD bulk: {n_locations} location(s), {len(causes)} cause(s)")

    if ambient_causes:
        print(f"  ✓ Found ambient air pollution causes: {ambient_causes}")
    else:
        print(f"  ✗ No ambient air pollution risk factor causes found")
        print(f"    Available causes include: {list(causes[:5])}...")
        print(f"    This GBD download contains disease outcomes, not air pollution risk attributions.")
        print(f"    To get air pollution deaths, download from GBD Results Tool with:")
        print(f"      Cause = 'Ambient particulate matter pollution'")

    if household_causes:
        print(f"  ✓ Found household air pollution causes: {household_causes}")
    else:
        print(f"  ✗ No household air pollution causes found")

    ambient_df = pd.DataFrame()
    household_df = pd.DataFrame()

    if n_locations <= 1:
        print(f"  [INFO] GBD file is global-level only — cannot extract country-level data")
        return ambient_df, household_df

    # If we have country-level air pollution data, extract it
    import country_converter as coco

    for cause_list, col_name, label in [
        (ambient_causes, "deaths_ambient_pm25", "ambient"),
        (household_causes, "deaths_household_air", "household"),
    ]:
        if not cause_list:
            continue
        subset = df[
            (df[cause_col].isin(cause_list)) &
            (df["measure_name"] == "Deaths") &
            (df["metric_name"] == "Number") &
            (df["sex_name"] == "Both") &
            (df["age_name"] == "All ages")
        ].copy()
        if subset.empty:
            continue

        # Convert location names to ISO3
        subset["iso3"] = coco.convert(subset["location_name"].tolist(), to="ISO3", not_found=None)
        subset = subset[subset["iso3"].notna() & (subset["iso3"] != "not found")]

        result = subset[["iso3", "year", "val"]].copy()
        result.columns = ["iso3", "year", col_name]
        result[col_name] = pd.to_numeric(result[col_name], errors="coerce") / 1000  # to thousands

        if label == "ambient":
            ambient_df = result
        else:
            household_df = result

    return ambient_df, household_df


# ---------------------------------------------------------------------------
# Lancet Countdown 2025 data loaders
# ---------------------------------------------------------------------------

LANCET_ATTRIBUTABLE_PATH = RAW_DIR / "lancet_countdown_attributable.xlsx"
LANCET_HEAT_MORTALITY_PATH = RAW_DIR / "lancet_countdown_heat_mortality.xlsx"

LANCET_CITATION = {
    "report": "The 2025 report of the Lancet Countdown on health and climate change",
    "url": "https://lancetcountdown.org/2025-report/",
    "indicators": {
        "heatwave_days": "Indicator 1.1.1: Exposure of Vulnerable Populations to Heatwaves",
        "heat_mortality": "Indicator 1.1.5: Heat Related Mortality",
    },
}


def load_lancet_heatwave_days() -> pd.DataFrame:
    """
    Load Lancet Countdown 2025 heatwave days attributable to climate change.

    Returns country × year DataFrame with columns: iso3, year, heatwave_days_cc
    (number of additional heatwave days attributable to climate change).

    Source: Lancet Countdown 2025 — Indicator 1.1.1
    """
    if not LANCET_ATTRIBUTABLE_PATH.exists():
        return pd.DataFrame(columns=["iso3", "year", "heatwave_days_cc"])

    try:
        df = pd.read_excel(
            LANCET_ATTRIBUTABLE_PATH,
            sheet_name="2025_Report_Data_Country",
        )
        print(f"  Loaded lancet_countdown_attributable.xlsx ({len(df):,} rows)")

        # Expected columns: Country, ISO3, WHO region, HDI level, Year,
        #                    Observed, Counterfactual, Attributable_to_CC
        if "ISO3" not in df.columns or "Attributable_to_CC" not in df.columns:
            print(f"  [WARN] Unexpected columns: {list(df.columns)}")
            return pd.DataFrame(columns=["iso3", "year", "heatwave_days_cc"])

        result = df[["ISO3", "Year", "Attributable_to_CC"]].copy()
        result.columns = ["iso3", "year", "heatwave_days_cc"]
        result["iso3"] = result["iso3"].str.upper()
        result["year"] = result["year"].astype(int)
        result["heatwave_days_cc"] = pd.to_numeric(result["heatwave_days_cc"], errors="coerce")
        result = result.dropna(subset=["iso3", "heatwave_days_cc"])
        print(f"  ✓ Lancet heatwave days: {len(result):,} country-year records, "
              f"{result['iso3'].nunique()} countries, {result['year'].min()}-{result['year'].max()}")
        return result

    except Exception as e:
        print(f"  [WARN] Failed to parse lancet_countdown_attributable.xlsx: {e}")
        return pd.DataFrame(columns=["iso3", "year", "heatwave_days_cc"])


def load_lancet_heat_mortality() -> dict:
    """
    Load Lancet Countdown 2025 global heat-related mortality reference data.

    Returns a dict with the latest year's attributable heat deaths (global)
    and the full time series for reference.

    Source: Lancet Countdown 2025 — Indicator 1.1.5
    AF = attributable fraction, AN = attributable number of deaths
    """
    if not LANCET_HEAT_MORTALITY_PATH.exists():
        return {}

    try:
        df = pd.read_excel(
            LANCET_HEAT_MORTALITY_PATH,
            sheet_name="2025 Report Data_Global",
        )
        print(f"  Loaded lancet_countdown_heat_mortality.xlsx ({len(df):,} rows)")

        # Columns: Year, AF, AN
        if "AN" not in df.columns:
            print(f"  [WARN] Expected 'AN' column (attributable number), got: {list(df.columns)}")
            return {}

        latest = df.sort_values("Year").iloc[-1]
        # Average of last 3 years for more stable estimate
        recent = df.sort_values("Year").tail(3)
        avg_deaths = int(recent["AN"].mean())

        result = {
            "latest_year": int(latest["Year"]),
            "latest_deaths": int(latest["AN"]),
            "latest_af": round(float(latest["AF"]), 2),
            "avg_3yr_deaths": avg_deaths,
            "avg_3yr_period": f"{int(recent['Year'].min())}-{int(recent['Year'].max())}",
            "time_series": [
                {"year": int(row["Year"]), "deaths": int(row["AN"]), "af": round(float(row["AF"]), 2)}
                for _, row in df.iterrows()
            ],
            "source": LANCET_CITATION["report"],
            "source_url": LANCET_CITATION["url"],
            "indicator": LANCET_CITATION["indicators"]["heat_mortality"],
            "note": (
                "Heat-related mortality attributable to climate change. "
                "AN = attributable number of deaths; AF = attributable fraction (%). "
                "These are SEPARATE from air pollution deaths. "
                "Global estimate only — not country-level."
            ),
        }
        print(f"  ✓ Lancet heat mortality: latest {result['latest_year']} = "
              f"{result['latest_deaths']:,} deaths, 3yr avg = {avg_deaths:,}")
        return result

    except Exception as e:
        print(f"  [WARN] Failed to parse lancet_countdown_heat_mortality.xlsx: {e}")
        return {}


# ---------------------------------------------------------------------------
# Compute country-level deaths/TWh from energy mix
# ---------------------------------------------------------------------------

def compute_country_deaths_per_twh(energy_mix: pd.DataFrame) -> pd.DataFrame:
    """
    Estimate deaths/TWh for each country×year based on their electricity generation mix.

    This is a COMPARATIVE FRAMING metric only — not a precision mortality estimate.
    It applies OWID reference deaths/TWh values to each country's generation shares.

    Method:
      deaths_per_twh = sum(share_source_i × deaths_per_twh_source_i)

    Critical caveats (shown in tooltip on every display):
      - Assumes country mortality rates equal OWID global averages — not true
      - Coal dominates; small changes in coal share dominate the estimate
      - Modern plants lower than older estimates; regional variation large
      - See definitions.py DEATHS_PER_TWH_TOOLTIP
    """
    if energy_mix.empty:
        return pd.DataFrame(columns=["iso3", "year", "deaths_per_twh_energy_mix"])

    dptwh = DEATHS_PER_TWH
    results = []

    # Map energy_mix column names to DEATHS_PER_TWH keys
    source_cols = {
        "electricity_twh_coal":    dptwh["coal"],
        "electricity_twh_oil":     dptwh["oil"],
        "electricity_twh_gas":     dptwh["gas"],
        "electricity_twh_nuclear": dptwh["nuclear"],
        "electricity_twh_wind":    dptwh["wind"],
        "electricity_twh_solar":   dptwh["solar"],
        "electricity_twh_hydro":   dptwh["hydro"],
        "electricity_twh_biomass": dptwh["biomass"],
        "electricity_twh_other":   dptwh["other"],
    }

    # Only compute for columns that exist
    available = {col: rate for col, rate in source_cols.items() if col in energy_mix.columns}
    if not available:
        print("  [WARN] No electricity_twh_* columns found in energy_mix.parquet; skipping deaths/TWh")
        return pd.DataFrame(columns=["iso3", "year", "deaths_per_twh_energy_mix"])

    for _, row in energy_mix[["iso3", "year"] + list(available.keys())].iterrows():
        iso3 = row["iso3"]
        year = row["year"]
        total_twh = sum(
            row[col] for col in available if pd.notna(row[col]) and row[col] > 0
        )
        if total_twh <= 0:
            results.append({"iso3": iso3, "year": year, "deaths_per_twh_energy_mix": np.nan})
            continue

        weighted_deaths = sum(
            row[col] * rate / total_twh
            for col, rate in available.items()
            if pd.notna(row[col]) and row[col] > 0
        )
        results.append({"iso3": iso3, "year": year, "deaths_per_twh_energy_mix": round(weighted_deaths, 4)})

    return pd.DataFrame(results)


# ---------------------------------------------------------------------------
# McDuffie et al. 2021 — Fossil fuel PM2.5 deaths by country
# ---------------------------------------------------------------------------
# Source: McDuffie et al. (2021) Nature Communications 12, 3594
# DOI: 10.1038/s41467-021-23853-y
# Supplementary Data 1: sector & fuel contributions to PM2.5 mortality (2017)
#
# Fossil fuel sectors summed: Energy (coal + non-coal), Industry (coal + non-coal),
# Road transport, Non-road transport, Residential coal, Commercial combustion,
# International shipping.
# Excluded: Agriculture, Residential biofuel, Agricultural waste burning,
# Other open fire, Windblown dust, AFCID dust, Solvent, Waste.

_MCDUFFIE_FOSSIL_SECTORS = [
    "energy_coal_pct", "energy_noncoal_pct",
    "industry_coal_pct", "industry_noncoal_pct",
    "road_transport_pct", "nonroad_transport_pct",
    "res_coal_pct", "commercial_pct", "shipping_pct",
]

# GBD region names to exclude (keep only country-level rows)
_GBD_REGION_NAMES = {
    "Central_Asia", "Central_Europe", "Eastern_Europe", "Australasia",
    "High_income_Asia_Pacific", "High_income_North_America",
    "Southern_Latin_America", "Western_Europe", "Andean_Latin_America",
    "Caribbean", "Central_Latin_America", "Tropical_Latin_America",
    "North_Africa_and_Middle_East", "South_Asia", "Southeast_Asia",
    "East_Asia", "Oceania", "Central_Sub-Saharan_Africa",
    "Eastern_Sub-Saharan_Africa", "Southern_Sub-Saharan_Africa",
    "Western_Sub-Saharan_Africa", "Global",
    # Also exclude sub-Saharan variants without hyphens
    "Central_Sub_Saharan_Africa", "Eastern_Sub_Saharan_Africa",
    "Southern_Sub_Saharan_Africa", "Western_Sub_Saharan_Africa",
}


def load_mcduffie_fossil_deaths() -> pd.DataFrame:
    """
    Load McDuffie et al. 2021 supplementary data and compute fossil fuel
    PM2.5 deaths per country for the year 2017.

    Returns DataFrame with columns: iso3, year, fossil_fuel_deaths, fossil_fuel_pct
    """
    import country_converter as coco

    xlsx_path = RAW_DIR / "mcduffie_supplementary_data1.xlsx"
    if not xlsx_path.exists():
        print("  [WARN] mcduffie_supplementary_data1.xlsx not found")
        return pd.DataFrame(columns=["iso3", "year", "fossil_fuel_deaths", "fossil_fuel_pct"])

    df = pd.read_excel(xlsx_path, header=None, skiprows=6)
    col_names = [
        "country_name", "pm25_pwm",
        "agr_pct", "energy_coal_pct", "energy_noncoal_pct",
        "industry_coal_pct", "industry_noncoal_pct",
        "nonroad_transport_pct", "road_transport_pct",
        "res_coal_pct", "res_biofuel_pct", "res_other_pct",
        "commercial_pct", "other_combustion_pct", "solvent_pct", "waste_pct",
        "shipping_pct", "ag_waste_burn_pct", "other_fire_pct",
        "afcid_dust_pct", "windblown_dust_pct", "remaining_pct",
        "total_deaths_gbd", "total_deaths_lower", "total_deaths_upper",
        "total_deaths_gemm",
        "copd_gbd", "copd_gemm", "dm_gbd", "dm_gemm",
        "lri_gbd", "lri_gemm", "lc_gbd", "lc_gemm",
        "ihd_gbd", "ihd_gemm", "stroke_gbd", "stroke_gemm",
        "preterm_gbd", "preterm_gemm", "lbw_gbd", "lbw_gemm",
    ]
    df.columns = col_names

    # Drop repeated header row
    df = df[df["country_name"] != "Country Name"].copy()

    # Convert numeric columns
    for c in col_names[1:]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Keep only country rows (exclude GBD regions and Global)
    df = df[~df["country_name"].isin(_GBD_REGION_NAMES)].copy()
    df = df[df["total_deaths_gbd"].notna()].copy()

    # Compute fossil fuel fraction and deaths
    df["fossil_fuel_pct"] = df[_MCDUFFIE_FOSSIL_SECTORS].sum(axis=1)
    df["fossil_fuel_deaths"] = df["total_deaths_gbd"] * df["fossil_fuel_pct"] / 100

    # Convert country names to ISO3
    # Replace underscores with spaces for better matching
    clean_names = df["country_name"].str.replace("_", " ").tolist()
    df["iso3"] = coco.convert(clean_names, to="ISO3", not_found=None)
    df = df[df["iso3"].notna()].copy()

    # McDuffie data is for 2017
    df["year"] = 2017

    # Convert deaths from absolute to thousands (to match deaths_ambient_pm25 units)
    df["fossil_fuel_deaths"] = df["fossil_fuel_deaths"] / 1000.0

    result = df[["iso3", "year", "fossil_fuel_deaths", "fossil_fuel_pct"]].copy()
    result = result.drop_duplicates(subset=["iso3"])
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"\n{'='*60}")
    print("Health & EJ Data Processing")
    print(f"{'='*60}\n")

    # -----------------------------------------------------------------------
    # 1. World Bank WDI: electricity access, clean cooking, PM2.5 exposure
    # -----------------------------------------------------------------------
    print("Step 1: Downloading World Bank WDI indicators...")
    wb_df = download_world_bank_data()
    if wb_df.empty:
        print("  [WARN] World Bank download failed; using empty DataFrame")
        wb_df = pd.DataFrame(columns=["iso3", "year",
                                       "pct_electricity_access",
                                       "pct_clean_cooking",
                                       "pm25_annual_mean_ugm3"])
    else:
        print(f"  World Bank: {len(wb_df):,} country-year records across {wb_df['iso3'].nunique()} countries")

    # -----------------------------------------------------------------------
    # 2. GBD/IHME mortality data
    # -----------------------------------------------------------------------
    print("\nStep 2: Loading GBD/IHME mortality data...")

    ambient_df = try_load_gbd_csv("gbd_deaths_ambient_pm25.csv", "ambient")
    household_df = try_load_gbd_csv("gbd_deaths_household_air.csv", "household")

    # Try GBD 2023 bulk download (may or may not contain air pollution data)
    if ambient_df.empty or household_df.empty:
        print("  Checking GBD 2023 bulk download...")
        bulk_ambient, bulk_household = try_load_gbd_bulk()
        if not bulk_ambient.empty and ambient_df.empty:
            ambient_df = bulk_ambient
        if not bulk_household.empty and household_df.empty:
            household_df = bulk_household

    # Try State of Global Air as alternative
    soga_path = RAW_DIR / "state_of_global_air.csv"
    if soga_path.exists() and ambient_df.empty:
        print(f"  Found state_of_global_air.csv — attempting to parse...")
        try:
            soga = pd.read_csv(soga_path, low_memory=False)
            print(f"  State of Global Air: {len(soga)} rows, columns: {list(soga.columns)[:8]}")
            if "deaths_ambient_pm25" in soga.columns and "iso3" in soga.columns:
                ambient_df = soga[["iso3", "year", "deaths_ambient_pm25"]].dropna()
        except Exception as e:
            print(f"  [WARN] Failed to parse state_of_global_air.csv: {e}")

    ambient_have = not ambient_df.empty and "deaths_ambient_pm25" in ambient_df.columns
    household_have = not household_df.empty and "deaths_household_air" in household_df.columns

    if not ambient_have:
        print("  ⏳ GBD ambient PM2.5 data not found.")
        print("  → deaths_ambient_pm25 will be NaN (placeholder schema only)")
        print(GBD_INSTRUCTIONS)
    else:
        print(f"  ✓ Ambient PM2.5 deaths: {len(ambient_df):,} country-year records")

    if not household_have:
        print("  ⏳ GBD household air pollution data not found.")
        print("  → deaths_household_air will be NaN (placeholder schema only)")
    else:
        print(f"  ✓ Household air pollution deaths: {len(household_df):,} country-year records")

    # -----------------------------------------------------------------------
    # 2b. Lancet Countdown 2025 data
    # -----------------------------------------------------------------------
    print("\nStep 2b: Loading Lancet Countdown 2025 data...")

    lancet_heatwave_df = load_lancet_heatwave_days()
    lancet_heat_mortality = load_lancet_heat_mortality()

    heatwave_have = not lancet_heatwave_df.empty

    # -----------------------------------------------------------------------
    # 3. Energy mix → deaths/TWh computation
    # -----------------------------------------------------------------------
    print("\nStep 3: Computing country deaths/TWh from energy mix...")
    em_path = PROCESSED_DIR / "energy_mix.parquet"
    if em_path.exists():
        energy_mix = pd.read_parquet(em_path)
        dptwh_df = compute_country_deaths_per_twh(energy_mix)
        print(f"  deaths_per_twh_energy_mix: {len(dptwh_df):,} country-year records")
    else:
        print("  [WARN] energy_mix.parquet not found; run process_core.py first")
        dptwh_df = pd.DataFrame(columns=["iso3", "year", "deaths_per_twh_energy_mix"])

    # -----------------------------------------------------------------------
    # 3b. McDuffie et al. 2021 — Fossil fuel PM2.5 deaths
    # -----------------------------------------------------------------------
    print("\nStep 3b: Loading McDuffie et al. 2021 fossil fuel deaths...")
    mcduffie_df = load_mcduffie_fossil_deaths()
    mcduffie_have = not mcduffie_df.empty
    if mcduffie_have:
        print(f"  ✓ Fossil fuel deaths: {len(mcduffie_df)} countries (2017 cross-section)")
    else:
        print("  [WARN] McDuffie data not found; fossil_fuel_deaths will be NaN")

    # -----------------------------------------------------------------------
    # 4. Build country list for placeholder scaffold
    # -----------------------------------------------------------------------
    meta_path = PROCESSED_DIR / "country_meta.parquet"
    if meta_path.exists():
        meta = pd.read_parquet(meta_path)
        country_iso3_list = sorted(meta["iso3"].dropna().unique().tolist())
    elif not wb_df.empty:
        country_iso3_list = sorted(wb_df["iso3"].unique().tolist())
    else:
        country_iso3_list = []

    # -----------------------------------------------------------------------
    # 5. Merge all sources into health.parquet
    # -----------------------------------------------------------------------
    print("\nStep 4: Merging into health.parquet...")

    # Start with WB data (has the most country×year coverage)
    if wb_df.empty and country_iso3_list:
        years = list(range(1990, 2024))
        wb_df = pd.DataFrame(
            [{"iso3": iso3, "year": yr} for iso3 in country_iso3_list for yr in years]
        )

    health = wb_df.copy()

    # Merge GBD mortality (left join to preserve WB country×year grid)
    if ambient_have:
        health = health.merge(
            ambient_df[["iso3", "year", "deaths_ambient_pm25"]],
            on=["iso3", "year"], how="left"
        )
    else:
        # Placeholder: correct schema, all NaN
        gbd_placeholder = build_gbd_placeholder(
            health["iso3"].unique().tolist() if not health.empty else country_iso3_list
        )
        health = health.merge(
            gbd_placeholder[["iso3", "year", "deaths_ambient_pm25"]],
            on=["iso3", "year"], how="left"
        )

    if household_have:
        health = health.merge(
            household_df[["iso3", "year", "deaths_household_air"]],
            on=["iso3", "year"], how="left"
        )
    else:
        health["deaths_household_air"] = np.nan

    # Merge deaths/TWh
    if not dptwh_df.empty:
        health = health.merge(dptwh_df, on=["iso3", "year"], how="left")
    else:
        health["deaths_per_twh_energy_mix"] = np.nan

    # Merge Lancet heatwave days
    if heatwave_have:
        health = health.merge(
            lancet_heatwave_df[["iso3", "year", "heatwave_days_cc"]],
            on=["iso3", "year"], how="left"
        )
    else:
        health["heatwave_days_cc"] = np.nan

    # Merge McDuffie fossil fuel deaths (2017 cross-section applied to all years)
    if mcduffie_have:
        mcduffie_for_merge = mcduffie_df[["iso3", "fossil_fuel_deaths", "fossil_fuel_pct"]].copy()
        health = health.merge(mcduffie_for_merge, on="iso3", how="left")
    else:
        health["fossil_fuel_deaths"] = np.nan
        health["fossil_fuel_pct"] = np.nan

    # Ensure all required columns are present
    required_cols = [
        "iso3", "year",
        "deaths_ambient_pm25", "deaths_household_air",
        "pm25_annual_mean_ugm3", "pct_electricity_access", "pct_clean_cooking",
        "deaths_per_twh_energy_mix",
        "heatwave_days_cc",
        "fossil_fuel_deaths", "fossil_fuel_pct",
    ]
    for col in required_cols:
        if col not in health.columns:
            health[col] = np.nan

    # Final cleanup
    health = health[required_cols].drop_duplicates(subset=["iso3", "year"])
    health = health.sort_values(["iso3", "year"]).reset_index(drop=True)

    # -----------------------------------------------------------------------
    # 6. Save health.parquet
    # -----------------------------------------------------------------------
    out_path = PROCESSED_DIR / "health.parquet"
    health.to_parquet(out_path, index=False)
    print(f"\n  ✓ Saved {out_path.name}")
    print(f"    → {len(health):,} country-year records, {health['iso3'].nunique()} countries")

    # Report data coverage
    for col in required_cols[2:]:
        n_non_null = health[col].notna().sum()
        pct = n_non_null / len(health) * 100 if len(health) > 0 else 0
        status = "✓" if pct > 10 else "⏳"
        print(f"    {status} {col}: {n_non_null:,} non-null values ({pct:.0f}% coverage)")

    # -----------------------------------------------------------------------
    # 7. Save deaths_per_twh.json reference values
    # -----------------------------------------------------------------------
    dptwh_out = PROCESSED_DIR / "deaths_per_twh.json"
    with open(dptwh_out, "w") as f:
        json.dump(DEATHS_PER_TWH_METADATA, f, indent=2)
    print(f"\n  ✓ Saved {dptwh_out.name} (reference deaths/TWh values)")

    # -----------------------------------------------------------------------
    # 8. Save Lancet heat mortality reference
    # -----------------------------------------------------------------------
    if lancet_heat_mortality:
        heat_ref_out = PROCESSED_DIR / "heat_deaths_reference.json"
        with open(heat_ref_out, "w") as f:
            json.dump(lancet_heat_mortality, f, indent=2)
        print(f"  ✓ Saved {heat_ref_out.name} (Lancet Countdown heat mortality reference)")

    print(f"\n{'='*60}")
    print("Health data processing complete.")
    if not ambient_have or not household_have:
        print("\n⚠️  GBD mortality columns are placeholders.")
        print("   Run with GBD files downloaded to get real values:")
        print("   See instructions above or in docs/data_sources.md")
    if heatwave_have:
        print("\n✓ Lancet Countdown heatwave days integrated (country-level).")
    if lancet_heat_mortality:
        print(f"✓ Lancet heat mortality reference saved "
              f"({lancet_heat_mortality['avg_3yr_deaths']:,} deaths/yr, "
              f"{lancet_heat_mortality['avg_3yr_period']} avg).")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
