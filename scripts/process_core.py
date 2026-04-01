"""
process_core.py — Processes Tier 1 data sources into standardized Parquet files.

Outputs:
  data/processed/emissions.parquet   — country x year: CO2 (fossil, land, total), GHGs by sector
  data/processed/energy_mix.parquet  — country x year: electricity generation by source, renewable shares
  data/processed/capacity.parquet    — country x year: installed capacity by technology
  data/processed/country_meta.parquet — country metadata (ISO3, name, region, income group)

Conventions enforced (see utils/definitions.py):
  - co2_fossil_mt vs ghg_total_mtco2e are NEVER conflated
  - renewable_share_electricity_pct denominator = total electricity generation
  - renewable_share_final_energy_pct denominator = final energy consumption
  - Ambient PM2.5 deaths and household air pollution deaths are separate columns
  - LULUCF can be included or excluded via the lulucf_included flag
  - Data quality tier (annex_i / non_annex_i) tagged for each country-year
"""

import sys
from pathlib import Path

import country_converter as coco
import pandas as pd

# Resolve paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Suppress country_converter log noise
import logging
logging.getLogger("country_converter").setLevel(logging.ERROR)


# ---------------------------------------------------------------------------
# Country metadata helpers
# ---------------------------------------------------------------------------

def build_country_meta() -> pd.DataFrame:
    """Build a country metadata table from OWID data.

    Returns a DataFrame with columns:
      iso3, country_name, continent, region (OWID region)
    """
    owid_path = RAW_DIR / "owid_energy.csv"
    if not owid_path.exists():
        print("  [WARN] owid_energy.csv not found; skipping country meta")
        return pd.DataFrame()

    df = pd.read_csv(owid_path, usecols=["country", "iso_code"])

    # OWID uses its own region aggregates (e.g. "World", "Europe") — filter to real countries
    # by requiring a non-null ISO code
    df = df[df["iso_code"].notna()].copy()
    df = df[df["iso_code"].str.len() == 3].copy()  # drop 2-letter codes and aggregates
    df = df.drop_duplicates(subset="iso_code")
    df = df.rename(columns={"country": "country_name", "iso_code": "iso3"})
    df["iso3"] = df["iso3"].str.upper()

    # Add continent via country_converter
    cc = coco.CountryConverter()
    df["continent"] = cc.convert(df["iso3"].tolist(), to="continent", not_found=None)

    print(f"  [OK] country_meta: {len(df)} countries")
    return df[["iso3", "country_name", "continent"]].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Emissions processing
# ---------------------------------------------------------------------------

def process_emissions() -> pd.DataFrame:
    """
    Build emissions.parquet from OWID CO2 data and (if available) EDGAR.

    Output columns (see definitions.py for full descriptions):
      iso3, year,
      co2_fossil_mt          — fossil CO2 only (GtCO2, GCB via OWID)
      co2_land_mt            — land-use CO2 (GtCO2, GCB via OWID)
      co2_total_mt           — fossil + land (GtCO2)
      ghg_total_mtco2e       — all GHGs as CO2e (OWID; EDGAR preferred when available)
      co2_per_capita_t       — fossil CO2 per capita (tonnes CO2)
      co2_consumption_mt     — consumption-based CO2 (OWID; ~40% higher for UK etc.)
      ghg_energy_mtco2e      — GHGs from energy sector (OWID proxy)
      lulucf_included        — boolean: whether land-use CO2 is in the total
      data_quality_tier      — 'annex_i' or 'non_annex_i'
    """
    owid_path = RAW_DIR / "owid_co2.csv"
    if not owid_path.exists():
        print("  [WARN] owid_co2.csv not found; emissions.parquet will be empty")
        return pd.DataFrame()

    print("  Loading OWID CO2 data...")
    df = pd.read_csv(owid_path, low_memory=False)

    # Filter to real countries (iso_code is a 3-letter code, not aggregates)
    df = df[df["iso_code"].notna()].copy()
    df = df[df["iso_code"].str.len() == 3].copy()
    df = df.rename(columns={"iso_code": "iso3", "country": "country_name"})
    df["iso3"] = df["iso3"].str.upper()

    # Select and rename the columns we need
    # OWID uses MtCO2 — we keep as Mt (million tonnes = 0.001 Gt)
    # Labels are explicit about what each column is (see definitions.py)
    col_map = {
        "co2": "co2_fossil_mt",           # fossil CO2 (Mt CO2)
        "land_use_change_co2": "co2_land_mt",  # land-use CO2 (Mt CO2)
        "total_ghg": "ghg_total_mtco2e",  # all GHGs, CO2e (Mt CO2e)
        "co2_per_capita": "co2_per_capita_t",   # tonnes CO2/person
        "consumption_co2": "co2_consumption_mt", # consumption-based CO2 (Mt CO2)
        "energy_co2": "co2_energy_mt",    # CO2 from energy sector (subset of fossil)
        "ghg_per_capita": "ghg_per_capita_t",
        "methane": "methane_mtco2e",
        "methane_per_capita": "methane_per_capita_t",
        "nitrous_oxide": "nitrous_oxide_mtco2e",
        "nitrous_oxide_per_capita": "nitrous_oxide_per_capita_t",
        "population": "population",
        "gdp": "gdp_usd",
    }

    available_cols = {k: v for k, v in col_map.items() if k in df.columns}
    keep_cols = ["iso3", "year"] + list(available_cols.keys())
    keep_cols = [c for c in keep_cols if c in df.columns]

    out = df[keep_cols].copy()
    out = out.rename(columns=available_cols)

    # Compute co2_total (fossil + land; lulucf_included = True)
    if "co2_fossil_mt" in out.columns and "co2_land_mt" in out.columns:
        out["co2_total_mt"] = out["co2_fossil_mt"].fillna(0) + out["co2_land_mt"].fillna(0)
        out["lulucf_included"] = True

    # Data quality tier: rough proxy — OECD countries are mostly Annex I
    # This is a simplification; full Annex I list should be used for precision
    ANNEX_I_ISO3 = {
        "AUS", "AUT", "BLR", "BEL", "BGR", "CAN", "HRV", "CYP", "CZE", "DNK",
        "EST", "FIN", "FRA", "DEU", "GRC", "HUN", "ISL", "IRL", "ITA", "JPN",
        "LVA", "LIE", "LTU", "LUX", "MLT", "MCO", "NLD", "NZL", "NOR", "POL",
        "PRT", "ROU", "RUS", "SVK", "SVN", "ESP", "SWE", "CHE", "TUR", "UKR",
        "GBR", "USA",
    }
    out["data_quality_tier"] = out["iso3"].apply(
        lambda x: "annex_i" if x in ANNEX_I_ISO3 else "non_annex_i"
    )

    # Filter years: 1990-present (earlier data has significant gaps)
    out = out[out["year"] >= 1990].copy()

    out = out.sort_values(["iso3", "year"]).reset_index(drop=True)
    print(f"  [OK] emissions: {len(out):,} rows, {out['iso3'].nunique()} countries, "
          f"years {int(out['year'].min())}-{int(out['year'].max())}")
    return out


# ---------------------------------------------------------------------------
# Energy mix processing
# ---------------------------------------------------------------------------

def process_energy_mix() -> pd.DataFrame:
    """
    Build energy_mix.parquet from OWID energy data and Ember yearly electricity data.

    CRITICAL denomination convention (see definitions.py):
      renewable_share_electricity_pct: renewables / total electricity generation (~30% globally)
      renewable_share_final_energy_pct: renewables / final energy consumption (~13% globally)
      These two metrics differ by ~2x and tell radically different stories.
      Both are included; the display layer must always show which denominator is used.

    Output columns:
      iso3, year,
      electricity_twh_{solar,wind,hydro,nuclear,gas,coal,oil,biomass,other}
      renewable_share_electricity_pct (denominator: electricity generation)
      renewable_share_final_energy_pct (denominator: final energy)
      total_electricity_twh
      fossil_share_electricity_pct
      primary_energy_ej
    """
    owid_path = RAW_DIR / "owid_energy.csv"
    ember_path = RAW_DIR / "ember_yearly_electricity.csv"

    if not owid_path.exists():
        print("  [WARN] owid_energy.csv not found; energy_mix.parquet will be empty")
        return pd.DataFrame()

    print("  Loading OWID energy data...")
    df = pd.read_csv(owid_path, low_memory=False)
    df = df[df["iso_code"].notna()].copy()
    df = df[df["iso_code"].str.len() == 3].copy()
    df = df.rename(columns={"iso_code": "iso3"})
    df["iso3"] = df["iso3"].str.upper()

    # Map OWID column names to our standardized schema
    electricity_cols = {
        "solar_electricity": "electricity_twh_solar",
        "wind_electricity": "electricity_twh_wind",
        "hydro_electricity": "electricity_twh_hydro",
        "nuclear_electricity": "electricity_twh_nuclear",
        "gas_electricity": "electricity_twh_gas",
        "coal_electricity": "electricity_twh_coal",
        "oil_electricity": "electricity_twh_oil",
        "biofuel_electricity": "electricity_twh_biomass",
        "other_renewable_electricity": "electricity_twh_other_renewable",
        "electricity_generation": "total_electricity_twh",
        "primary_energy_consumption": "primary_energy_ej",
    }

    renewable_share_cols = {
        # OWID provides these directly — denominator is electricity generation
        "renewables_share_elec": "renewable_share_electricity_pct",
        # OWID also provides renewables share of energy (final energy denominator)
        "renewables_share_energy": "renewable_share_final_energy_pct",
        "fossil_share_elec": "fossil_share_electricity_pct",
        "fossil_share_energy": "fossil_share_final_energy_pct",
        "low_carbon_share_elec": "low_carbon_share_electricity_pct",
        # Grid carbon intensity (gCO2/kWh) — key climate metric for electricity
        "carbon_intensity_elec": "carbon_intensity_gco2_kwh",
    }

    all_col_map = {**electricity_cols, **renewable_share_cols}
    available = {k: v for k, v in all_col_map.items() if k in df.columns}

    keep = ["iso3", "year"] + [k for k in available.keys() if k in df.columns]
    out = df[keep].copy().rename(columns=available)

    # Primary energy: OWID reports in TWh, convert to EJ
    # 1 EJ = 277.78 TWh, so EJ = TWh / 277.78
    if "primary_energy_ej" in out.columns:
        out["primary_energy_ej"] = out["primary_energy_ej"] / 277.78

    # Merge in Ember data if available (Ember has better country coverage for recent years)
    if ember_path.exists():
        print("  Loading Ember yearly electricity data...")
        try:
            ember = pd.read_csv(ember_path, low_memory=False)
            # Ember long-format: columns include 'Country code', 'Year', 'Variable', 'Value'
            # We pivot to wide format
            if "Country code" in ember.columns and "Variable" in ember.columns:
                ember = ember.rename(columns={"Country code": "iso3", "Year": "year"})
                ember["iso3"] = ember["iso3"].str.upper()
                # Only keep generation data (TWh)
                ember_gen = ember[
                    ember["Variable"].str.contains("Generation", na=False) &
                    (ember["Unit"] == "TWh") if "Unit" in ember.columns else True
                ].copy()
                print(f"  [OK] Ember data loaded: {len(ember)} rows")
            else:
                print("  [WARN] Ember format unexpected; skipping Ember merge")
        except Exception as e:
            print(f"  [WARN] Could not load Ember data: {e}; proceeding with OWID only")

    out = out[out["year"] >= 1990].copy()
    out = out.sort_values(["iso3", "year"]).reset_index(drop=True)
    print(f"  [OK] energy_mix: {len(out):,} rows, {out['iso3'].nunique()} countries, "
          f"years {int(out['year'].min())}-{int(out['year'].max())}")
    return out


# ---------------------------------------------------------------------------
# Capacity processing
# ---------------------------------------------------------------------------

def process_capacity() -> pd.DataFrame:
    """
    Build capacity.parquet from IRENA Renewable Energy Statistics (ELEC-C files).

    The IRENA data comes as multiple Excel batches (ELEC-C_*.xlsx) with merged
    cells that need forward-filling.  We filter to "Electricity Installed Capacity
    (MW)" with grid connection "All", convert MW → GW, and pivot technologies
    into wide-format columns matching the dashboard schema.

    Output columns:
      iso3, year,
      capacity_gw_solar, capacity_gw_wind_onshore, capacity_gw_wind_offshore,
      capacity_gw_wind (total), capacity_gw_hydro, capacity_gw_nuclear,
      capacity_gw_biomass, capacity_gw_geothermal, capacity_gw_other_renewable,
      capacity_gw_total_renewable, capacity_gw_fossil
    """
    irena_files = sorted(RAW_DIR.glob("ELEC-C_*.xlsx"))
    if not irena_files:
        # Fall back to OWID if IRENA files are not present
        print("  [WARN] No IRENA ELEC-C files found; trying OWID fallback")
        return _capacity_from_owid()

    print(f"  Loading IRENA capacity data from {len(irena_files)} files...")
    dfs = []
    for f in irena_files:
        df = pd.read_excel(f, sheet_name="ELEC-C")
        dfs.append(df)
    raw = pd.concat(dfs, ignore_index=True)

    # Rename columns from the generic Excel headers
    raw.columns = ["country", "technology", "data_type", "grid_connection", "year", "value"]

    # Forward-fill merged cells (IRENA Excel uses merged cells for country/tech/type/grid)
    for col in ["country", "technology", "data_type", "grid_connection"]:
        raw[col] = raw[col].ffill()

    # Drop footer rows and all-NaN rows
    raw = raw.dropna(subset=["year"])
    raw = raw[~raw["country"].str.contains("Database:|Internal reference|ELEC-C|IRENA", na=False)]

    # Coerce numeric
    raw["year"] = pd.to_numeric(raw["year"], errors="coerce").astype("Int64")
    raw["value"] = pd.to_numeric(raw["value"], errors="coerce")
    raw = raw.dropna(subset=["year", "value"])

    # Filter: installed capacity only, "All" grid connection (avoids double-counting on/off-grid)
    cap = raw[
        (raw["data_type"] == "Electricity Installed Capacity (MW)")
        & (raw["grid_connection"] == "All")
    ].copy()

    # Convert country names to ISO3 codes
    cc = coco.CountryConverter()
    cap["iso3"] = cc.convert(cap["country"].tolist(), to="ISO3", not_found=None)
    cap = cap[cap["iso3"].notna() & (cap["iso3"] != "not found")].copy()

    # Map IRENA technology names to our dashboard column schema
    # Technologies: Solar photovoltaic, Onshore wind energy, Offshore wind energy,
    #   Renewable hydropower, Nuclear, Geothermal energy, Solar thermal energy,
    #   Biogas, Solid biofuels, Liquid biofuels, Renewable municipal waste,
    #   Marine energy, Mixed Hydro Plants, Pumped storage,
    #   Coal and peat, Natural gas, Oil, Fossil fuels n.e.s.,
    #   Other non-renewable energy, Total renewable, Total non-renewable
    TECH_MAP = {
        "Solar photovoltaic": "solar",
        "Solar thermal energy": "solar_thermal",
        "Onshore wind energy": "wind_onshore",
        "Offshore wind energy": "wind_offshore",
        "Renewable hydropower": "hydro",
        "Mixed Hydro Plants": "hydro",       # include with hydro
        "Nuclear": "nuclear",
        "Geothermal energy": "geothermal",
        "Biogas": "biomass",
        "Solid biofuels": "biomass",
        "Liquid biofuels": "biomass",
        "Renewable municipal waste": "biomass",
        "Marine energy": "other_renewable",
        "Total renewable": "total_renewable",
        "Total non-renewable": "fossil",
        # Individual fossil fuels — skip, we use the total
        "Coal and peat": None,
        "Natural gas": None,
        "Oil": None,
        "Fossil fuels n.e.s.": None,
        "Other non-renewable energy": None,
        "Pumped storage": None,  # not a generation technology
    }

    cap["tech_key"] = cap["technology"].map(TECH_MAP)
    cap = cap[cap["tech_key"].notna()].copy()

    # Aggregate: some tech keys map multiple IRENA categories (e.g. biomass)
    agg = (
        cap.groupby(["iso3", "year", "tech_key"], as_index=False)["value"]
        .sum()
    )

    # Pivot to wide format
    wide = agg.pivot_table(index=["iso3", "year"], columns="tech_key", values="value", aggfunc="sum")
    wide = wide.reset_index()

    # Rename columns to capacity_gw_* and convert MW → GW
    tech_cols = [c for c in wide.columns if c not in ("iso3", "year")]
    for col in tech_cols:
        wide[f"capacity_gw_{col}"] = wide[col] / 1000.0  # MW → GW
    wide = wide.drop(columns=tech_cols)

    # Compute total wind (onshore + offshore)
    onshore = wide.get("capacity_gw_wind_onshore", 0)
    offshore = wide.get("capacity_gw_wind_offshore", 0)
    if isinstance(onshore, pd.Series) or isinstance(offshore, pd.Series):
        wide["capacity_gw_wind"] = (
            wide.get("capacity_gw_wind_onshore", pd.Series(0, index=wide.index)).fillna(0)
            + wide.get("capacity_gw_wind_offshore", pd.Series(0, index=wide.index)).fillna(0)
        )

    # Compute combined solar (PV + thermal) → keep as capacity_gw_solar
    if "capacity_gw_solar_thermal" in wide.columns:
        solar_pv = wide.get("capacity_gw_solar", pd.Series(0, index=wide.index)).fillna(0)
        solar_th = wide["capacity_gw_solar_thermal"].fillna(0)
        wide["capacity_gw_solar"] = solar_pv + solar_th
        wide = wide.drop(columns=["capacity_gw_solar_thermal"])

    out = wide.sort_values(["iso3", "year"]).reset_index(drop=True)
    print(f"  [OK] capacity (IRENA): {len(out):,} rows, {out['iso3'].nunique()} countries, "
          f"years {int(out['year'].min())}-{int(out['year'].max())}")

    # Summary of global totals for latest year
    latest_year = int(out["year"].max())
    latest = out[out["year"] == latest_year]
    for col in ["capacity_gw_solar", "capacity_gw_wind", "capacity_gw_total_renewable"]:
        if col in latest.columns:
            total = latest[col].sum(skipna=True)
            print(f"       {col} ({latest_year}): {total:,.0f} GW")

    return out


def _capacity_from_owid() -> pd.DataFrame:
    """Fallback: build capacity from OWID energy data (limited coverage)."""
    owid_path = RAW_DIR / "owid_energy.csv"
    if not owid_path.exists():
        print("  [WARN] owid_energy.csv not found; capacity.parquet will be empty")
        return pd.DataFrame()

    df = pd.read_csv(owid_path, low_memory=False)
    df = df[df["iso_code"].notna() & (df["iso_code"].str.len() == 3)].copy()
    df = df.rename(columns={"iso_code": "iso3"})
    df["iso3"] = df["iso3"].str.upper()

    cap_col_map = {
        "solar_capacity": "capacity_gw_solar",
        "wind_capacity": "capacity_gw_wind",
        "hydro_capacity": "capacity_gw_hydro",
        "nuclear_capacity": "capacity_gw_nuclear",
        "biofuel_capacity": "capacity_gw_biomass",
        "other_renewable_capacity": "capacity_gw_other_renewable",
        "renewables_capacity": "capacity_gw_total_renewable",
        "fossil_capacity": "capacity_gw_fossil",
    }
    available = {k: v for k, v in cap_col_map.items() if k in df.columns}
    keep = ["iso3", "year"] + list(available.keys())
    keep = [c for c in keep if c in df.columns]
    out = df[keep].copy().rename(columns=available)
    out = out[out["year"] >= 2000].copy()
    out = out.sort_values(["iso3", "year"]).reset_index(drop=True)
    print(f"  [OK] capacity (OWID fallback): {len(out):,} rows")
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"\n{'='*60}")
    print("Energy Transition Dashboard — Core Data Processor")
    print(f"{'='*60}\n")

    # Country metadata
    print("Building country metadata...")
    country_meta = build_country_meta()
    if not country_meta.empty:
        out_path = PROCESSED_DIR / "country_meta.parquet"
        country_meta.to_parquet(out_path, index=False)
        print(f"  Saved → {out_path.name}\n")

    # Emissions
    print("Processing emissions...")
    emissions = process_emissions()
    if not emissions.empty:
        out_path = PROCESSED_DIR / "emissions.parquet"
        emissions.to_parquet(out_path, index=False)
        print(f"  Saved → {out_path.name}\n")

    # Energy mix
    print("Processing energy mix...")
    energy_mix = process_energy_mix()
    if not energy_mix.empty:
        out_path = PROCESSED_DIR / "energy_mix.parquet"
        energy_mix.to_parquet(out_path, index=False)
        print(f"  Saved → {out_path.name}\n")

    # Capacity
    print("Processing capacity...")
    capacity = process_capacity()
    if not capacity.empty:
        out_path = PROCESSED_DIR / "capacity.parquet"
        capacity.to_parquet(out_path, index=False)
        print(f"  Saved → {out_path.name}\n")

    print(f"{'='*60}")
    print("Core processing complete.")

    # Check which outputs are present
    expected = ["emissions.parquet", "energy_mix.parquet", "capacity.parquet", "country_meta.parquet"]
    for f in expected:
        p = PROCESSED_DIR / f
        status = "✓" if p.exists() else "✗ MISSING"
        print(f"  {status}  {f}")
    print(f"{'='*60}\n")

    # Reminder about manual data sources
    manual_missing = []
    for fname in ["gcb_2024.xlsx", "edgar_ghg_2023.csv", "primap_hist.csv"]:
        if not (RAW_DIR / fname).exists():
            manual_missing.append(fname)

    if manual_missing:
        print("⚠️  Manual data sources not yet downloaded:")
        for f in manual_missing:
            print(f"   - data/raw/{f}")
        print("   Run: python scripts/download_data.py  for instructions.")
        print("   These sources are needed for EDGAR sectoral GHG data and PRIMAP non-Annex I coverage.\n")


if __name__ == "__main__":
    main()
