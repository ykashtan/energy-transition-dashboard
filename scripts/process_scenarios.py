"""
process_scenarios.py — Generate scenarios.parquet, nze_milestones.parquet, and damages.parquet.

DATA SOURCES:
  Scenarios:
    IPCC AR6 WGIII Scenario Database (hosted by IIASA)
    https://data.ece.iiasa.ac.at/ar6/
    Downloaded file: AR6_Scenarios_Database_World_ALL_CLIMATE_v1.1.csv.zip
    Metadata file:   AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx
    License: CC-BY 4.0
    Citation: Byers et al. (2022). AR6 Scenarios Database.
              doi:10.5281/zenodo.5886911

  NZE milestones:
    IEA Net Zero by 2050 (2021, updated 2023).
    Published headline milestones from IEA NZE scenario.

  GDP damage projections:
    Burke, Hsiang & Miguel (2015). "Global non-linear effect of temperature
    on economic production." Nature 527, 235–239.
    doi:10.1038/nature15725
    Data: country-level GDP/cap projections under RCP8.5/SSP5 with and
    without climate change impacts.

LABELING CONVENTIONS (per definitions.py):
  C1 = "1.5°C-compatible range (C1)"
      Limits warming to 1.5°C with >50% probability by 2100.
      MOST involve temperature overshoot; require 8–10 GtCO₂/yr CDR by 2050.
  C3 = "2°C-compatible range (C3)"
      Limits warming to 2°C with >67% probability.
  C5 = "2.5°C-compatible range (C5)"
      Limits warming to ~2.5°C with >50% probability.
  C7 = "3°C-compatible (C7)"
      Limits warming to 3°C with >67% probability.
  C8 = ">3°C (C8)"
      Exceeds 3°C warming. Closest to current-policy trajectory.

Output files:
  scenarios.parquet      — IPCC AR6 pathway envelopes (percentiles by category)
  nze_milestones.parquet — IEA NZE 2050 renewable capacity milestones
  damages.parquet        — Burke et al. GDP damage projections per country
"""

from pathlib import Path
import zipfile
import io

import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Category definitions
# ---------------------------------------------------------------------------

CATEGORY_META = {
    "C1": {
        "label": "1.5°C-compatible range (C1)",
        "tooltip": (
            "C1 scenarios limit warming to 1.5°C with >50% probability by 2100. "
            "Most involve temperature overshoot before returning to 1.5°C via "
            "large-scale carbon removal (CDR). Required CDR: 8–10 GtCO₂/yr by 2050. "
            "Current CDR: ~2 GtCO₂/yr. "
            "These are NOT scenarios where warming stays below 1.5°C."
        ),
        "color": "#2dc653",
    },
    "C3": {
        "label": "2°C-compatible range (C3)",
        "tooltip": (
            "C3 scenarios limit warming to 2°C with >67% probability by 2100. "
            "Require significant but less extreme mitigation than C1."
        ),
        "color": "#f4a261",
    },
    "C5": {
        "label": "2.5°C-compatible range (C5)",
        "tooltip": (
            "C5 scenarios limit warming to ~2.5°C with >50% probability by 2100. "
            "Current policy trajectories exceed this range."
        ),
        "color": "#e63946",
    },
    "C7": {
        "label": "~3°C range (C7)",
        "tooltip": (
            "C7 scenarios limit warming to 3°C with >67% probability by 2100. "
            "Close to the trajectory under current implemented policies."
        ),
        "color": "#6c757d",
    },
    "C8": {
        "label": ">3°C (C8)",
        "tooltip": (
            "C8 scenarios exceed 3°C warming by 2100. "
            "Represents a 'business-as-usual' high-emissions future."
        ),
        "color": "#495057",
    },
}


# ---------------------------------------------------------------------------
# Step 1: Extract scenario pathway envelopes from IIASA AR6 data
# ---------------------------------------------------------------------------

def build_scenarios_df() -> pd.DataFrame:
    """
    Read the IIASA AR6 Scenario Database (1 GB zipped CSV) using chunked reading.
    Extract net CO2 emissions for vetted C1/C3/C5/C7/C8 scenarios.
    Compute category-level percentile envelopes.
    """
    zip_path = RAW_DIR / "1668008030411-AR6_Scenarios_Database_World_ALL_CLIMATE_v1.1.csv.zip"
    meta_path = RAW_DIR / "AR6_Scenarios_Database_metadata_indicators_v1.1.xlsx"

    if not zip_path.exists() or not meta_path.exists():
        print("  [WARN] AR6 data files not found. Generating placeholder data.")
        return _build_placeholder_scenarios()

    # Load metadata: Model/Scenario -> Category mapping
    print("  Loading AR6 metadata...")
    meta = pd.read_excel(meta_path, sheet_name="meta_Ch3vetted_withclimate")
    cats_of_interest = list(CATEGORY_META.keys())
    meta_filt = meta[meta["Category"].isin(cats_of_interest)][
        ["Model", "Scenario", "Category"]
    ].copy()
    meta_filt["key"] = meta_filt["Model"] + "|" + meta_filt["Scenario"]
    lookup = dict(zip(meta_filt["key"], meta_filt["Category"]))
    for cat in cats_of_interest:
        count = sum(1 for v in lookup.values() if v == cat)
        print(f"    {cat}: {count} scenarios")

    # Read the big CSV in chunks, filtering for "Emissions|CO2" variable only
    print("  Reading AR6 scenario database (chunked)...")
    target_var = "Emissions|CO2"
    results = []

    with zipfile.ZipFile(zip_path) as z:
        csv_name = [n for n in z.namelist() if n.endswith(".csv")][0]
        with z.open(csv_name) as f:
            reader = pd.read_csv(f, chunksize=50_000, low_memory=False)
            for chunk in reader:
                mask = chunk["Variable"] == target_var
                filtered = chunk[mask].copy()
                if filtered.empty:
                    continue
                filtered["key"] = filtered["Model"] + "|" + filtered["Scenario"]
                filtered = filtered[filtered["key"].isin(lookup)]
                if not filtered.empty:
                    filtered["Category"] = filtered["key"].map(lookup)
                    results.append(filtered)

    if not results:
        print("  [WARN] No matching rows found in AR6 CSV. Using placeholder.")
        return _build_placeholder_scenarios()

    df = pd.concat(results, ignore_index=True)
    print(f"  Matched {len(df)} scenario rows across {df['Category'].nunique()} categories.")

    # Melt year columns to long format
    year_cols = [c for c in df.columns if c.isdigit() and 1995 <= int(c) <= 2100]
    id_cols = ["Model", "Scenario", "Category", "Variable", "Unit"]
    df_long = df.melt(
        id_vars=id_cols, value_vars=year_cols, var_name="year", value_name="value"
    )
    df_long["year"] = df_long["year"].astype(int)
    df_long["value"] = pd.to_numeric(df_long["value"], errors="coerce")
    df_long = df_long.dropna(subset=["value"])

    # Convert Mt CO2/yr to Gt CO2/yr
    if (df_long["Unit"] == "Mt CO2/yr").any():
        df_long["value"] = df_long["value"] / 1000.0

    # Compute percentiles by Category and Year
    print("  Computing percentile envelopes...")

    def _percentiles(group):
        vals = group["value"]
        return pd.Series({
            "p5": np.percentile(vals, 5),
            "p10": np.percentile(vals, 10),
            "p25": np.percentile(vals, 25),
            "p50": np.percentile(vals, 50),
            "p75": np.percentile(vals, 75),
            "p90": np.percentile(vals, 90),
            "p95": np.percentile(vals, 95),
            "count": len(vals),
        })

    pcts = (
        df_long.groupby(["Category", "year"])
        .apply(_percentiles, include_groups=False)
        .reset_index()
    )

    # Build output DataFrame in the expected schema
    rows = []
    for _, row in pcts.iterrows():
        cat = row["Category"]
        meta_info = CATEGORY_META.get(cat, {})
        rows.append({
            "category": cat,
            "label": meta_info.get("label", cat),
            "variable": "Emissions|CO2|Net",
            "year": int(row["year"]),
            "p5": row["p5"],
            "p10": row["p10"],
            "p25": row["p25"],
            "p50": row["p50"],
            "p75": row["p75"],
            "p90": row["p90"],
            "p95": row["p95"],
            "n_scenarios": int(row["count"]),
            "placeholder": False,
        })

    return pd.DataFrame(rows)


def _build_placeholder_scenarios() -> pd.DataFrame:
    """Fallback placeholder if raw data is not available."""
    # Minimal placeholder — same as the old script but marked clearly
    YEARS = [2010, 2015, 2020, 2025, 2030, 2035, 2040, 2045, 2050,
             2060, 2070, 2080, 2090, 2100]
    C1_p50 = [35.5, 37.0, 37.0, 30, 19, 11, 4, -1, -5, -9, -12, -14, -15, -16]
    rows = []
    for i, yr in enumerate(YEARS):
        rows.append({
            "category": "C1", "label": "1.5°C-compatible range (C1)",
            "variable": "Emissions|CO2|Net", "year": yr,
            "p5": C1_p50[i] - 3, "p10": C1_p50[i] - 2.5,
            "p25": C1_p50[i] - 1.5, "p50": C1_p50[i],
            "p75": C1_p50[i] + 2, "p90": C1_p50[i] + 4,
            "p95": C1_p50[i] + 5, "n_scenarios": 0, "placeholder": True,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Step 2: IEA NZE milestones (unchanged — these are published milestones)
# ---------------------------------------------------------------------------

NZE_MILESTONES = [
    (2020, 2829, 1841, 8500, "Actual (IEA 2020)"),
    (2022, 3372, 2290, 9800, "Actual (IEA 2022)"),
    (2030, 11000, 8500, 22000, "NZE 2030 milestone"),
    (2040, 18000, 14000, 40000, "NZE 2040 milestone"),
    (2050, 27000, 21000, 61000, "NZE 2050 milestone"),
]


def build_nze_df() -> pd.DataFrame:
    """Build NZE milestones DataFrame."""
    rows = []
    for year, total_gw, solar_wind_gw, total_twh, description in NZE_MILESTONES:
        rows.append({
            "year": year,
            "total_renewable_gw": total_gw,
            "solar_wind_gw": solar_wind_gw,
            "total_renewable_twh": total_twh,
            "description": description,
            "source": "IEA NZE 2050 (approximate milestones from published reports)",
            "placeholder": True,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Step 3: Burke et al. GDP climate damage projections
# ---------------------------------------------------------------------------

def build_damages_df() -> pd.DataFrame:
    """
    Process Burke, Hsiang & Miguel (2015) GDP/capita projections.

    Computes % GDP loss per country at 2050 and 2080 under RCP8.5/SSP5.
    The damage is the gap between GDP projections WITH vs WITHOUT climate change.

    This data is powerful for the EJ narrative: hot (tropical/developing) countries
    face devastating GDP losses while cold (wealthy) countries may gain.
    """
    cc_path = RAW_DIR / "GDPcap_ClimateChange_RCP85_SSP5.csv"
    no_cc_path = RAW_DIR / "GDPcap_NOClimateChange_RCP85_SSP5.csv"

    if not cc_path.exists() or not no_cc_path.exists():
        print("  [WARN] Burke et al. GDP files not found. Skipping damages.")
        return pd.DataFrame()

    print("  Processing Burke et al. GDP damage projections...")
    gdp_cc = pd.read_csv(cc_path)
    gdp_no = pd.read_csv(no_cc_path)

    rows = []
    for idx in range(len(gdp_cc)):
        iso3 = gdp_cc.iloc[idx]["ISO3"]
        name = gdp_cc.iloc[idx]["name"]
        mean_temp = gdp_cc.iloc[idx].get("meantemp", None)

        row = {"iso3": iso3, "country_name": name, "mean_temp_c": mean_temp}

        # Compute % GDP loss at key horizons
        for yr_str, col_name in [("2050", "pct_gdp_loss_2050"),
                                  ("2080", "pct_gdp_loss_2080")]:
            if yr_str in gdp_cc.columns and yr_str in gdp_no.columns:
                cc_val = pd.to_numeric(gdp_cc.iloc[idx][yr_str], errors="coerce")
                no_val = pd.to_numeric(gdp_no.iloc[idx][yr_str], errors="coerce")
                if pd.notna(cc_val) and pd.notna(no_val) and no_val > 0:
                    pct_loss = (no_val - cc_val) / no_val * 100
                    row[col_name] = round(pct_loss, 1)
                else:
                    row[col_name] = None
            else:
                row[col_name] = None

        rows.append(row)

    df = pd.DataFrame(rows)
    # Drop rows with all nulls
    df = df.dropna(subset=["pct_gdp_loss_2050", "pct_gdp_loss_2080"], how="all")

    print(f"  GDP damage projections: {len(df)} countries")
    print(f"    2050 — mean loss: {df['pct_gdp_loss_2050'].mean():.1f}%, "
          f"median: {df['pct_gdp_loss_2050'].median():.1f}%")
    print(f"    2080 — mean loss: {df['pct_gdp_loss_2080'].mean():.1f}%, "
          f"median: {df['pct_gdp_loss_2080'].median():.1f}%")

    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"\n{'='*60}")
    print("Energy Transition Dashboard — Scenario & Damage Processor")
    print(f"{'='*60}\n")

    # IPCC scenarios (real IIASA data)
    scenarios_df = build_scenarios_df()
    out_path = PROCESSED_DIR / "scenarios.parquet"
    scenarios_df.to_parquet(out_path, index=False)
    is_real = not scenarios_df["placeholder"].all() if "placeholder" in scenarios_df.columns else False
    source_label = "IIASA AR6 database" if is_real else "placeholder"
    cats = scenarios_df["category"].unique() if not scenarios_df.empty else []
    print(f"  [OK] scenarios.parquet  → {len(scenarios_df)} rows ({source_label})")
    print(f"       Categories: {', '.join(sorted(cats))}")
    if is_real and "n_scenarios" in scenarios_df.columns:
        for cat in sorted(cats):
            n = scenarios_df[scenarios_df["category"] == cat]["n_scenarios"].iloc[0]
            print(f"         {cat}: {n} scenarios")

    # NZE milestones (unchanged)
    nze_df = build_nze_df()
    nze_path = PROCESSED_DIR / "nze_milestones.parquet"
    nze_df.to_parquet(nze_path, index=False)
    print(f"  [OK] nze_milestones.parquet → {len(nze_df)} milestone rows")

    # GDP damage projections
    damages_df = build_damages_df()
    if not damages_df.empty:
        damages_path = PROCESSED_DIR / "damages.parquet"
        damages_df.to_parquet(damages_path, index=False)
        print(f"  [OK] damages.parquet → {len(damages_df)} countries")
    else:
        print("  [--] damages.parquet not generated (raw data missing)")

    print(f"\n{'='*60}")
    print("Scenario processing complete.")
    print("  ✓  scenarios.parquet")
    print("  ✓  nze_milestones.parquet")
    if not damages_df.empty:
        print("  ✓  damages.parquet")
    print(f"{'='*60}\n")

    if is_real:
        print("Data sources:")
        print("  Scenarios: IIASA AR6 Scenario Explorer v1.1")
        print("    Byers et al. (2022). doi:10.5281/zenodo.5886911")
        print("    https://data.ece.iiasa.ac.at/ar6/")
        print("  NZE: IEA Net Zero by 2050 (2021, updated 2023)")
        print("    https://www.iea.org/reports/net-zero-by-2050")
        if not damages_df.empty:
            print("  GDP damages: Burke, Hsiang & Miguel (2015)")
            print("    Nature 527, 235–239. doi:10.1038/nature15725")
        print()


if __name__ == "__main__":
    main()
