"""
compute_kpis.py — Pre-computes all homepage KPI values and saves them to data/processed/kpis.json.

The homepage NEVER queries Parquet files at request time — it reads kpis.json only.
This keeps the homepage fast even on Render.com's free tier (no Parquet reads per request).

Run this script after process_core.py to update homepage statistics.

KPIs computed:
  Hero stats (5):
    - atmospheric_co2_ppm      (NOAA global mean)
    - temperature_anomaly_c    (HadCRUT5, rebased to 1850-1900)
    - renewable_share_elec_pct (OWID electricity)
    - deaths_ambient_pm25_m    (GBD/IHME via health.parquet)
    - clean_energy_investment_t (IEA via investment.parquet)

  Thematic sections:
    Emissions & Pathways:
      - co2_fossil_gt, ghg_total_gtco2e, co2_per_capita_t (global)
    Clean Energy Momentum:
      - capacity_solar_gw, capacity_wind_gw, capacity_total_renewable_gw
      - renewable_share_elec_pct (same as hero), renewable_share_final_energy_pct
    Costs & Finance:
      - (placeholder — populated by process_costs.py)
    Health & Equity:
      - (placeholder — populated by process_health.py)
"""

import json
import sys
from pathlib import Path

import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RAW_DIR = PROJECT_ROOT / "data" / "raw"


def safe_val(series, idx=-1):
    """Return a scalar from a series, handling NaN and empty."""
    try:
        val = series.dropna().iloc[idx]
        if pd.isna(val):
            return None
        return float(val)
    except (IndexError, TypeError):
        return None


def pct_change(current, previous):
    """Compute percent change. Returns None if inputs are invalid."""
    try:
        if previous and previous != 0:
            return round((current - previous) / abs(previous) * 100, 1)
    except TypeError:
        pass
    return None


def trend_arrow(pct_chg, positive_is_good: bool) -> str:
    """Return a trend indicator string."""
    if pct_chg is None:
        return "→"
    if pct_chg > 0.5:
        return "↑ good" if positive_is_good else "↑ bad"
    if pct_chg < -0.5:
        return "↓ bad" if positive_is_good else "↓ good"
    return "→ stable"


def fmt_number(val, decimals=1, unit=""):
    """Format a number for display."""
    if val is None:
        return "N/A"
    return f"{val:.{decimals}f}{(' ' + unit) if unit else ''}"


# ---------------------------------------------------------------------------
# Load processed data
# ---------------------------------------------------------------------------

def load_parquet(name: str) -> pd.DataFrame:
    path = PROCESSED_DIR / name
    if not path.exists():
        print(f"  [WARN] {name} not found; some KPIs will be placeholders")
        return pd.DataFrame()
    return pd.read_parquet(path)


def load_noaa_co2() -> dict:
    """Parse NOAA global mean CO2 text file -> most recent annual mean (ppm)."""
    noaa_path = RAW_DIR / "noaa_co2_global_mean.csv"
    if not noaa_path.exists():
        return {"value": None, "year": None}

    try:
        # NOAA annual mean format: year  mean  unc
        # Lines starting with '#' are comments
        rows = []
        with open(noaa_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or not line:
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        year = int(float(parts[0]))
                        mean = float(parts[1])
                        if mean > 0:  # filter fill values
                            rows.append({"year": year, "co2_ppm": mean})
                    except ValueError:
                        continue

        if not rows:
            return {"value": None, "year": None}

        df = pd.DataFrame(rows).sort_values("year")
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) >= 2 else None

        return {
            "value": round(float(latest["co2_ppm"]), 2),
            "year": int(latest["year"]),
            "previous_value": round(float(prev["co2_ppm"]), 2) if prev is not None else None,
            "previous_year": int(prev["year"]) if prev is not None else None,
        }
    except Exception as e:
        print(f"  [WARN] Could not parse NOAA CO2 file: {e}")
        return {"value": None, "year": None}


# ---------------------------------------------------------------------------
# Compute global aggregates from emissions.parquet
# ---------------------------------------------------------------------------

def compute_emissions_kpis(emissions: pd.DataFrame) -> dict:
    """Compute global emissions KPIs from emissions.parquet."""
    if emissions.empty:
        return {}

    # Global totals: sum across all countries (filter out non-country aggregates)
    # Use the most recent year with data for >100 countries
    year_counts = emissions.groupby("year")["iso3"].count()
    valid_years = year_counts[year_counts > 100].index
    if len(valid_years) == 0:
        return {}

    latest_year = int(valid_years.max())
    prev_year = latest_year - 1

    def global_total(col, year):
        sub = emissions[emissions["year"] == year]
        if col not in sub.columns:
            return None
        val = sub[col].sum(skipna=True)
        return round(float(val), 1) if not pd.isna(val) else None

    co2_fossil_latest = global_total("co2_fossil_mt", latest_year)
    co2_fossil_prev = global_total("co2_fossil_mt", prev_year)
    ghg_latest = global_total("ghg_total_mtco2e", latest_year)
    ghg_prev = global_total("ghg_total_mtco2e", prev_year)

    # Convert Mt to Gt for display (divide by 1000)
    def mt_to_gt(val):
        return round(val / 1000, 2) if val else None

    return {
        "co2_fossil_gt": {
            "value": mt_to_gt(co2_fossil_latest),
            "unit": "GtCO₂/yr",
            "label": "Fossil CO₂ emissions",
            "year": latest_year,
            "previous_value": mt_to_gt(co2_fossil_prev),
            "pct_change": pct_change(co2_fossil_latest, co2_fossil_prev),
            "trend": trend_arrow(pct_change(co2_fossil_latest, co2_fossil_prev), positive_is_good=False),
            "source": "OWID (GCB)",
            "note": "Fossil fuel CO₂ only. Does not include land-use change or other GHGs.",
            "definition_key": "co2_fossil_mt",
        },
        "ghg_total_gtco2e": {
            "value": mt_to_gt(ghg_latest),
            "unit": "GtCO₂e/yr",
            "label": "Total GHG emissions",
            "year": latest_year,
            "previous_value": mt_to_gt(ghg_prev),
            "pct_change": pct_change(ghg_latest, ghg_prev),
            "trend": trend_arrow(pct_change(ghg_latest, ghg_prev), positive_is_good=False),
            "source": "OWID (Jones et al. 2025, based on EDGAR v8.0 + GCB)",
            "note": (
                "All greenhouse gases (CO₂, CH₄, N₂O, F-gases) as CO₂e using AR6 GWP100 values. "
                "EXCLUDES land-use change and forestry (LULUCF). "
                "Including LULUCF adds ~4–5 GtCO₂e/yr (UNEP EGR 2024 reports ~59 GtCO₂e with LULUCF). "
                "Different sources report different totals due to: LULUCF inclusion, GWP generation "
                "(AR5 vs AR6), gas coverage, and inventory methodology (EDGAR vs UNFCCC vs PRIMAP)."
            ),
            "definition_key": "ghg_total_mtco2e",
        },
    }


# ---------------------------------------------------------------------------
# Compute energy/renewables KPIs from energy_mix.parquet and capacity.parquet
# ---------------------------------------------------------------------------

def compute_energy_kpis(energy_mix: pd.DataFrame, capacity: pd.DataFrame) -> dict:
    """Compute renewable energy KPIs."""
    kpis = {}

    if not energy_mix.empty and "renewable_share_electricity_pct" in energy_mix.columns:
        # Global renewable share of electricity: weighted mean across countries
        # Use the most recent year with data for >100 countries (typically 1-2 years behind current)
        year_counts_em = energy_mix.groupby("year")["iso3"].count()
        valid_em_years = year_counts_em[year_counts_em > 100].index
        if len(valid_em_years) == 0:
            re_share = None
            re_year = None
        else:
            recent_year = int(valid_em_years.max())
            year_data = energy_mix[
                (energy_mix["year"] == recent_year) &
                energy_mix["renewable_share_electricity_pct"].notna()
            ].copy()
            if "total_electricity_twh" in year_data.columns:
                year_data = year_data[year_data["total_electricity_twh"].notna()]
                if len(year_data) > 10:
                    weighted = (
                        (year_data["renewable_share_electricity_pct"] * year_data["total_electricity_twh"]).sum()
                        / year_data["total_electricity_twh"].sum()
                    )
                    re_share = round(float(weighted), 1) if not pd.isna(weighted) else None
                else:
                    re_share = round(float(year_data["renewable_share_electricity_pct"].mean()), 1)
            else:
                re_share = round(float(year_data["renewable_share_electricity_pct"].mean()), 1)
            re_year = recent_year

        kpis["renewable_share_electricity_pct"] = {
            "value": re_share,
            "unit": "%",
            "label": "Renewable share of electricity generation",
            "year": re_year,
            "source": "OWID (Ember/IRENA)",
            "note": "Denominator: total electricity generation (~30% globally). NOT share of final energy (~13%).",
            "definition_key": "renewable_share_electricity_pct",
            "trend": "↑ good",  # renewables growing globally
        }

    if not capacity.empty:
        # Global solar and wind capacity
        # Filter out OWID aggregate rows; sum across countries
        real_countries = capacity[capacity["iso3"].str.len() == 3]
        latest_cap_year = int(real_countries["year"].max())
        prev_cap_year = latest_cap_year - 1

        def cap_total(col, year):
            sub = real_countries[real_countries["year"] == year]
            if col not in sub.columns:
                return None
            val = sub[col].sum(skipna=True)
            return round(float(val), 0) if not pd.isna(val) else None

        solar_latest = cap_total("capacity_gw_solar", latest_cap_year)
        solar_prev = cap_total("capacity_gw_solar", prev_cap_year)
        wind_latest = cap_total("capacity_gw_wind", latest_cap_year)
        wind_prev = cap_total("capacity_gw_wind", prev_cap_year)
        total_re_latest = cap_total("capacity_gw_total_renewable", latest_cap_year)
        total_re_prev = cap_total("capacity_gw_total_renewable", prev_cap_year)

        kpis["capacity_solar_gw"] = {
            "value": solar_latest,
            "unit": "GW",
            "label": "Solar capacity",
            "year": latest_cap_year,
            "previous_value": solar_prev,
            "pct_change": pct_change(solar_latest, solar_prev),
            "trend": trend_arrow(pct_change(solar_latest, solar_prev), positive_is_good=True),
            "source": "IRENA Renewable Energy Statistics 2025",
        }
        kpis["capacity_wind_gw"] = {
            "value": wind_latest,
            "unit": "GW",
            "label": "Wind capacity",
            "year": latest_cap_year,
            "previous_value": wind_prev,
            "pct_change": pct_change(wind_latest, wind_prev),
            "trend": trend_arrow(pct_change(wind_latest, wind_prev), positive_is_good=True),
            "source": "IRENA Renewable Energy Statistics 2025",
        }
        kpis["capacity_total_renewable_gw"] = {
            "value": total_re_latest,
            "unit": "GW",
            "label": "Total renewable electricity capacity",
            "year": latest_cap_year,
            "previous_value": total_re_prev,
            "pct_change": pct_change(total_re_latest, total_re_prev),
            "trend": trend_arrow(pct_change(total_re_latest, total_re_prev), positive_is_good=True),
            "source": "IRENA Renewable Energy Statistics 2025",
        }

    return kpis


# ---------------------------------------------------------------------------
# Compute health & EJ KPIs from health.parquet
# ---------------------------------------------------------------------------

def _population_weighted_mean(
    health: pd.DataFrame, col: str, year: int, population_df: pd.DataFrame
) -> float | None:
    """
    Compute population-weighted mean of `col` for a given year.

    Falls back to unweighted mean if population data is unavailable.
    This is the standard World Bank / IEA methodology for computing
    global access statistics (electricity, clean cooking).
    """
    year_data = health[
        (health["year"] == year) & health[col].notna()
    ].copy()
    if year_data.empty:
        return None

    if not population_df.empty and "population" in population_df.columns:
        pop_year = population_df[population_df["year"] == year][["iso3", "population"]].copy()
        if pop_year.empty:
            # Try nearest year (population changes slowly)
            pop_year = population_df[
                population_df["year"] == population_df["year"].max()
            ][["iso3", "population"]].copy()

        merged = year_data.merge(pop_year, on="iso3", how="inner")
        merged = merged[merged["population"].notna() & (merged["population"] > 0)]

        if len(merged) > 10:
            weighted = (
                (merged[col] * merged["population"]).sum()
                / merged["population"].sum()
            )
            return round(float(weighted), 1) if not pd.isna(weighted) else None

    # Fallback: unweighted mean (with warning)
    print(f"  [WARN] No population data for {col} year {year}; using unweighted mean (not recommended)")
    val = year_data[col].mean()
    return round(float(val), 1) if not pd.isna(val) else None


def compute_health_kpis(health: pd.DataFrame, population_df: pd.DataFrame = None) -> dict:
    """
    Compute global Health & EJ KPIs from health.parquet.

    Critical constraints (enforced here):
      - deaths_ambient_pm25 and deaths_household_air are ALWAYS separate KPIs
      - Their sum is NEVER presented in the context of energy transition
      - pct_electricity_access and pct_clean_cooking use population-weighted
        global averages (standard World Bank / IEA methodology)
    """
    if population_df is None:
        population_df = pd.DataFrame()
    if health.empty:
        return _health_placeholders()

    kpis = {}

    # Global sums require population weighting, which we don't have in health.parquet.
    # Use mean across countries as a fallback; flag as approximation.
    # For a precise global aggregate, GBD publishes world-level totals directly.

    # Deaths are in thousands/yr per country. Sum to get global total (in thousands),
    # then convert to millions for display.
    year_counts = health.groupby("year")["iso3"].count()
    valid_years = year_counts[year_counts > 50].index  # need reasonable coverage

    # --- Ambient PM2.5 deaths ---
    ambient_col = "deaths_ambient_pm25"
    if ambient_col in health.columns and health[ambient_col].notna().any():
        # Get latest year with reasonable data
        ambient_years = health[health[ambient_col].notna()].groupby("year")["iso3"].count()
        ambient_valid = ambient_years[ambient_years > 50].index
        if len(ambient_valid) > 0:
            latest_yr = int(ambient_valid.max())
            prev_yr = latest_yr - 1
            # Sum deaths (thousands) across countries; convert to millions
            total = health[health["year"] == latest_yr][ambient_col].sum(skipna=True) / 1000
            prev = health[health["year"] == prev_yr][ambient_col].sum(skipna=True) / 1000
            total = round(float(total), 2) if not pd.isna(total) else None
            prev = round(float(prev), 2) if not pd.isna(prev) else None

            kpis["deaths_ambient_pm25_m"] = {
                "value": total,
                "unit": "million/yr",
                "label": "Deaths from ambient (outdoor) PM2.5",
                "year": latest_yr,
                "previous_value": prev,
                "pct_change": pct_change(total, prev) if total and prev else None,
                "trend": trend_arrow(pct_change(total, prev) if total and prev else None,
                                     positive_is_good=False),
                "source": "IHME Global Burden of Disease 2023 (ambient PM2.5)",
                "source_url": "https://vizhub.healthdata.org/gbd-results/",
                "note": (
                    "Outdoor (ambient) PM2.5 deaths only. "
                    "Directly reducible by decarbonizing electricity and industry. "
                    "NOT combined with household air pollution deaths."
                ),
                "definition_key": "deaths_ambient_pm25",
            }
    if "deaths_ambient_pm25_m" not in kpis:
        kpis.update(_health_placeholders(keys=["deaths_ambient_pm25_m"]))

    # --- Household air pollution deaths ---
    household_col = "deaths_household_air"
    if household_col in health.columns and health[household_col].notna().any():
        household_years = health[health[household_col].notna()].groupby("year")["iso3"].count()
        household_valid = household_years[household_years > 50].index
        if len(household_valid) > 0:
            latest_yr = int(household_valid.max())
            prev_yr = latest_yr - 1
            total = health[health["year"] == latest_yr][household_col].sum(skipna=True) / 1000
            prev = health[health["year"] == prev_yr][household_col].sum(skipna=True) / 1000
            total = round(float(total), 2) if not pd.isna(total) else None
            prev = round(float(prev), 2) if not pd.isna(prev) else None

            kpis["deaths_household_air_m"] = {
                "value": total,
                "unit": "million/yr",
                "label": "Deaths from household air pollution (solid fuels)",
                "year": latest_yr,
                "previous_value": prev,
                "pct_change": pct_change(total, prev) if total and prev else None,
                "trend": trend_arrow(pct_change(total, prev) if total and prev else None,
                                     positive_is_good=False),
                "source": "IHME Global Burden of Disease 2023 (household solid fuels)",
                "source_url": "https://vizhub.healthdata.org/gbd-results/",
                "note": (
                    "Household air pollution from solid-fuel cooking. "
                    "NOT directly addressed by electricity decarbonization. "
                    "Requires clean cooking access programs (South Asia, Sub-Saharan Africa)."
                ),
                "definition_key": "deaths_household_air",
            }
    if "deaths_household_air_m" not in kpis:
        kpis.update(_health_placeholders(keys=["deaths_household_air_m"]))

    # --- Energy access: population-weighted global % with electricity ---
    # Standard methodology (World Bank / IEA): weight each country's access rate by its
    # population to compute the global figure. An unweighted country average drastically
    # underestimates access (~88%) because many small, low-access countries pull the mean
    # down. Population-weighted value is ~91% (World Bank WDI 2022).
    if "pct_electricity_access" in health.columns and health["pct_electricity_access"].notna().any():
        ea_years = health[health["pct_electricity_access"].notna()].groupby("year")["iso3"].count()
        ea_valid = ea_years[ea_years > 80].index
        if len(ea_valid) > 0:
            latest_yr = int(ea_valid.max())
            prev_yr = latest_yr - 1

            avg_access = _population_weighted_mean(
                health, "pct_electricity_access", latest_yr, population_df
            )
            prev_access = _population_weighted_mean(
                health, "pct_electricity_access", prev_yr, population_df
            )

            kpis["electricity_access_pct"] = {
                "value": avg_access,
                "unit": "%",
                "label": "Population with electricity access",
                "year": latest_yr,
                "previous_value": prev_access,
                "pct_change": pct_change(avg_access, prev_access),
                "trend": trend_arrow(pct_change(avg_access, prev_access), positive_is_good=True),
                "source": "World Bank WDI (EG.ELC.ACCS.ZS), population-weighted",
                "note": (
                    "Population-weighted global average (standard World Bank / IEA methodology). "
                    "Masks large regional disparities. ~675M without access."
                ),
                "definition_key": "pct_electricity_access",
            }

    # --- Clean cooking access: population-weighted ---
    # Same methodology as electricity access. Unweighted average (~69%) understates global
    # access because populous countries (China, India) have higher access than the average
    # across small nations. Population-weighted value is ~74% (WHO / World Bank).
    if "pct_clean_cooking" in health.columns and health["pct_clean_cooking"].notna().any():
        cc_years = health[health["pct_clean_cooking"].notna()].groupby("year")["iso3"].count()
        cc_valid = cc_years[cc_years > 80].index
        if len(cc_valid) > 0:
            latest_yr = int(cc_valid.max())
            prev_yr = latest_yr - 1

            avg_cc = _population_weighted_mean(
                health, "pct_clean_cooking", latest_yr, population_df
            )
            prev_cc = _population_weighted_mean(
                health, "pct_clean_cooking", prev_yr, population_df
            )

            kpis["clean_cooking_access_pct"] = {
                "value": avg_cc,
                "unit": "%",
                "label": "Population with clean cooking fuel access",
                "year": latest_yr,
                "previous_value": prev_cc,
                "pct_change": pct_change(avg_cc, prev_cc),
                "trend": trend_arrow(pct_change(avg_cc, prev_cc), positive_is_good=True),
                "source": "World Bank WDI (EG.CFT.ACCS.ZS), population-weighted",
                "note": (
                    "Population-weighted global average (WHO / World Bank methodology). "
                    "~2.3 billion people lack clean cooking access. "
                    "Closely linked to household air pollution mortality."
                ),
                "definition_key": "pct_clean_cooking",
            }

    return kpis


def _health_placeholders(keys: list = None) -> dict:
    """Return placeholder health KPIs for when data is not yet available."""
    all_placeholders = {
        "deaths_ambient_pm25_m": {
            "value": None,
            "unit": "million/yr",
            "label": "Deaths from ambient (outdoor) PM2.5",
            "year": None,
            "source": "Pending — download GBD/IHME data (see scripts/process_health.py)",
            "note": (
                "Ambient PM2.5 deaths only (~4M/yr globally based on GBD 2019). "
                "NOT combined with household air pollution deaths (~3.2M/yr). "
                "See definitions.py for why these must be kept separate."
            ),
            "definition_key": "deaths_ambient_pm25",
            "status": "placeholder",
        },
        "deaths_household_air_m": {
            "value": None,
            "unit": "million/yr",
            "label": "Deaths from household air pollution (solid fuels)",
            "year": None,
            "source": "Pending — download GBD/IHME data (see scripts/process_health.py)",
            "note": (
                "Household solid-fuel cooking deaths (~3.2M/yr globally). "
                "NOT an electricity-transition metric. Requires clean cooking programs."
            ),
            "definition_key": "deaths_household_air",
            "status": "placeholder",
        },
    }
    if keys:
        return {k: v for k, v in all_placeholders.items() if k in keys}
    return all_placeholders


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"\n{'='*60}")
    print("Energy Transition Dashboard — KPI Computation")
    print(f"{'='*60}\n")

    kpis = {}

    # --- Atmospheric CO2 (NOAA global mean) ---
    print("Loading NOAA atmospheric CO2...")
    noaa = load_noaa_co2()
    kpis["atmospheric_co2_ppm"] = {
        "value": noaa.get("value"),
        "unit": "ppm",
        "label": "Atmospheric CO₂ concentration",
        "year": noaa.get("year"),
        "previous_value": noaa.get("previous_value"),
        "pct_change": pct_change(noaa.get("value"), noaa.get("previous_value")),
        "source": "NOAA (global mean surface CO₂, not Mauna Loa alone)",
        "note": "Global mean; Mauna Loa single-station value differs slightly.",
        "trend": "↑ bad",  # rising CO2 is always bad
    }
    if noaa.get("value"):
        print(f"  CO2: {noaa['value']} ppm ({noaa['year']})")

    # --- Emissions KPIs ---
    print("\nLoading emissions data...")
    emissions = load_parquet("emissions.parquet")
    emissions_kpis = compute_emissions_kpis(emissions)
    kpis.update(emissions_kpis)

    # --- Energy / Renewables KPIs ---
    print("\nLoading energy mix and capacity data...")
    energy_mix = load_parquet("energy_mix.parquet")
    capacity = load_parquet("capacity.parquet")
    energy_kpis = compute_energy_kpis(energy_mix, capacity)
    kpis.update(energy_kpis)

    # --- Temperature anomaly (HadCRUT5) ---
    print("\nLoading HadCRUT5 temperature data...")
    hadcrut_path = RAW_DIR / "hadcrut5_global_annual.csv"
    if hadcrut_path.exists():
        try:
            hc = pd.read_csv(hadcrut_path)
            # Columns: Time, Anomaly (deg C), Lower confidence limit, Upper confidence limit
            # Rebase from 1961-1990 baseline to 1850-1900 baseline (IPCC AR6 standard)
            # Offset ≈ -0.36°C (mean anomaly over 1850-1900 relative to 1961-1990)
            baseline = hc[(hc["Time"] >= 1850) & (hc["Time"] <= 1900)]["Anomaly (deg C)"].mean()
            hc["anomaly_rebased"] = hc["Anomaly (deg C)"] - baseline
            latest = hc.iloc[-1]
            prev = hc.iloc[-2] if len(hc) >= 2 else None
            temp_val = round(float(latest["anomaly_rebased"]), 2)
            temp_year = int(latest["Time"])
            prev_val = round(float(prev["anomaly_rebased"]), 2) if prev is not None else None
            kpis["temperature_anomaly_c"] = {
                "value": temp_val,
                "unit": "°C above 1850-1900",
                "label": "Global temperature anomaly",
                "year": temp_year,
                "previous_value": prev_val,
                "pct_change": pct_change(temp_val, prev_val),
                "trend": trend_arrow(pct_change(temp_val, prev_val), positive_is_good=False),
                "source": "HadCRUT5 (Met Office / UEA), rebased to 1850-1900",
                "note": "Baseline: 1850-1900 (IPCC AR6 standard).",
                "definition_key": "temperature_anomaly",
            }
            print(f"  Temperature anomaly: {temp_val}°C ({temp_year})")
        except Exception as e:
            print(f"  [WARN] Could not parse HadCRUT5: {e}")
            kpis["temperature_anomaly_c"] = {
                "value": None, "unit": "°C above 1850-1900",
                "label": "Global temperature anomaly", "year": None,
                "source": "Pending — HadCRUT5 parse error",
                "status": "placeholder",
            }
    else:
        kpis["temperature_anomaly_c"] = {
            "value": None, "unit": "°C above 1850-1900",
            "label": "Global temperature anomaly", "year": None,
            "source": "Pending — needs HadCRUT5 data file",
            "status": "placeholder",
        }

    # --- Clean energy investment (IEA via investment.parquet) ---
    print("\nLoading investment data...")
    investment = load_parquet("investment.parquet")
    if not investment.empty and "clean_energy_investment_bn" in investment.columns:
        world = investment[investment["region"] == "World"].sort_values("year")
        if not world.empty:
            latest_inv = world.iloc[-1]
            prev_inv = world.iloc[-2] if len(world) >= 2 else None
            inv_val = round(float(latest_inv["clean_energy_investment_bn"]) / 1000, 2)  # bn -> T
            inv_year = int(latest_inv["year"])
            prev_inv_val = round(float(prev_inv["clean_energy_investment_bn"]) / 1000, 2) if prev_inv is not None else None
            kpis["clean_energy_investment_t"] = {
                "value": inv_val,
                "unit": "$T/yr",
                "label": "Clean energy investment",
                "year": inv_year,
                "previous_value": prev_inv_val,
                "pct_change": pct_change(inv_val, prev_inv_val),
                "trend": trend_arrow(pct_change(inv_val, prev_inv_val), positive_is_good=True),
                "source": "IEA World Energy Investment 2025",
                "note": "Includes renewables, nuclear, efficiency, networks, storage, EVs.",
                "definition_key": "clean_energy_investment",
            }
            print(f"  Clean energy investment: ${inv_val}T ({inv_year})")
        else:
            kpis["clean_energy_investment_t"] = {
                "value": None, "unit": "$T/yr",
                "label": "Clean energy investment", "year": None,
                "source": "Pending — no World row in investment data",
                "status": "placeholder",
            }
    else:
        kpis["clean_energy_investment_t"] = {
            "value": None, "unit": "$T/yr",
            "label": "Clean energy investment", "year": None,
            "source": "Pending — needs IEA Investment Data",
            "status": "placeholder",
        }

    # --- Health & EJ KPIs (from health.parquet) ---
    # Load population data from emissions.parquet for population-weighted access stats
    print("\nLoading health data...")
    population_df = pd.DataFrame()
    if not emissions.empty and "population" in emissions.columns:
        population_df = emissions[["iso3", "year", "population"]].copy()
        print(f"  Population data: {len(population_df):,} country-year rows")
    else:
        print("  [WARN] No population column in emissions.parquet; access stats will use unweighted mean")
    health_kpis = compute_health_kpis(load_parquet("health.parquet"), population_df)
    kpis.update(health_kpis)

    # --- Gap indicator: current trajectory vs 1.5°C ---
    kpis["current_policies_warming_c"] = {
        "value": 3.1,
        "unit": "°C",
        "label": "Projected warming under current policies",
        "year": 2024,
        "source": "UNEP Emissions Gap Report 2024",
        "note": (
            "Under current implemented policies. "
            "Unconditional NDC pledges → ~2.8°C. "
            "Conditional NDC pledges → ~2.6°C. "
            "1.5°C-compatible → requires dramatic additional action."
        ),
        "trend": "↑ bad",
    }

    # --- Save to JSON ---
    out_path = PROCESSED_DIR / "kpis.json"
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Convert numpy types to Python types for JSON serialization
    def convert(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    kpis_clean = json.loads(json.dumps(kpis, default=convert))

    with open(out_path, "w") as f:
        json.dump(kpis_clean, f, indent=2)

    print(f"\n{'='*60}")
    print(f"KPI computation complete → {out_path.name}")
    computed = [k for k, v in kpis.items() if v.get("value") is not None]
    pending = [k for k, v in kpis.items() if v.get("value") is None]
    print(f"  ✓ {len(computed)} KPIs have values")
    if pending:
        print(f"  ⏳ {len(pending)} KPIs pending additional data:")
        for k in pending:
            print(f"       - {k}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
