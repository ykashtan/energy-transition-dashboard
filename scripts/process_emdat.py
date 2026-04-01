"""
process_emdat.py — Process EM-DAT climate disaster data.

Extracts climate-related natural disasters (floods, storms, droughts, extreme
temperatures, wildfires) and aggregates by country-year for the dashboard map.
Excludes technological disasters and non-climate natural disasters (earthquakes,
volcanoes).

Source: EM-DAT, CRED / UCLouvain, Brussels, Belgium
  https://www.emdat.be/

Output: data/processed/climate_disasters.parquet

Schema:
  iso3                    : str   — ISO 3166-1 alpha-3 country code
  year                    : int   — year
  n_disasters             : int   — number of climate disaster events
  total_deaths            : float — total deaths from climate disasters
  total_affected          : float — total people affected
  total_damage_adj_musd   : float — total adjusted damage (million USD, CPI-adjusted)
"""

from pathlib import Path
import pandas as pd
import numpy as np

RAW_PATH = Path(__file__).parent.parent / "data" / "raw"
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "processed" / "climate_disasters.parquet"


# Climate-related disaster types to include
# These are the disaster subtypes/types most directly linked to climate change
CLIMATE_DISASTER_TYPES = {
    "Flood", "Storm", "Drought", "Extreme temperature",
    "Wildfire", "Mass movement (wet)",
}


def process_emdat() -> pd.DataFrame:
    """Process EM-DAT data into country-year climate disaster summaries."""

    # Find the EM-DAT file
    emdat_files = list(RAW_PATH.glob("public_emdat_custom_request_*.xlsx"))
    if not emdat_files:
        raise FileNotFoundError("No EM-DAT file found in data/raw/")

    raw = pd.read_excel(emdat_files[0], sheet_name="EM-DAT Data")

    # Filter to natural disasters only, then to climate-related types
    climate = raw[
        (raw["Disaster Group"] == "Natural") &
        (raw["Disaster Type"].isin(CLIMATE_DISASTER_TYPES))
    ].copy()

    # Use ISO column for country code
    iso_col = "ISO" if "ISO" in climate.columns else "Iso"
    climate = climate.rename(columns={iso_col: "iso3"})

    # Use Start Year for temporal aggregation
    climate = climate.rename(columns={"Start Year": "year"})

    # Parse numeric columns
    for col in ["Total Deaths", "Total Affected", "Total Damage, Adjusted ('000 US$)"]:
        if col in climate.columns:
            climate[col] = pd.to_numeric(climate[col], errors="coerce")

    # Aggregate by country-year
    agg = climate.groupby(["iso3", "year"]).agg(
        n_disasters=("Disaster Type", "count"),
        total_deaths=("Total Deaths", "sum"),
        total_affected=("Total Affected", "sum"),
        total_damage_adj_musd=("Total Damage, Adjusted ('000 US$)", lambda x: x.sum() / 1000),  # '000 USD -> M USD
    ).reset_index()

    # Replace 0 with NaN for damage (often means "not reported" not "zero damage")
    agg.loc[agg["total_damage_adj_musd"] == 0, "total_damage_adj_musd"] = np.nan

    # Sort
    agg = agg.sort_values(["iso3", "year"]).reset_index(drop=True)

    return agg


if __name__ == "__main__":
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df = process_emdat()
    df.to_parquet(OUTPUT_PATH, index=False)
    print(f"[process_emdat] Wrote {len(df)} rows → {OUTPUT_PATH}")
    print(f"  Countries: {df['iso3'].nunique()}")
    print(f"  Years: {df['year'].min()}–{df['year'].max()}")

    # Totals
    print(f"  Total climate disaster events: {df['n_disasters'].sum():,.0f}")
    print(f"  Total deaths: {df['total_deaths'].sum():,.0f}")
    print(f"  Total affected: {df['total_affected'].sum():,.0f}")
    reported_dmg = df['total_damage_adj_musd'].dropna()
    print(f"  Total reported damage: ${reported_dmg.sum():,.0f}M USD "
          f"({len(reported_dmg)}/{len(df)} country-years have damage data)")
