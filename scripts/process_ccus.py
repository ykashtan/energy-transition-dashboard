"""
process_ccus.py — Process IEA CCUS Projects Database for the predictions page.

Extracts real-world CCS/CCUS project data to strengthen the predictions page's
analysis of CCS overestimation. Key outputs:
  - Operational capacity by year (to compare against IEA projections)
  - Project status breakdown (how many planned vs operational vs cancelled)
  - Pipeline analysis (announced capacity by status)

Source: IEA CCUS Projects Database 2026
  https://www.iea.org/data-and-statistics/data-product/ccus-projects-database

Output: data/processed/ccus_projects.parquet

Schema:
  year              : int   — year (for time series rows)
  metric            : str   — "operational_capacity", "cumulative_projects", "status_summary", "pipeline"
  category          : str   — project status or type qualifier
  value             : float — MtCO2/yr or count
  unit              : str   — "MtCO2/yr" or "projects"
  n_projects        : int   — number of projects (for capacity rows)
"""

from pathlib import Path
import pandas as pd
import numpy as np

RAW_PATH = Path(__file__).parent.parent / "data" / "raw" / "IEA CCUS Projects Database 2026.xlsx"
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "processed" / "ccus_projects.parquet"


def process_ccus() -> pd.DataFrame:
    """Process IEA CCUS database into dashboard-ready format."""

    # Read the main data sheet
    df = pd.read_excel(RAW_PATH, sheet_name="DRAFT CCUS Projects Database")

    # Standardize casing inconsistencies noted in exploration
    df["Project type"] = df["Project type"].str.strip().str.title()
    df["Fate of carbon"] = df["Fate of carbon"].str.strip().str.title()
    df["Project status"] = df["Project status"].str.strip()

    # Use IEA's estimated capacity (clean numeric) over announced (has ranges)
    df["capacity_mt"] = pd.to_numeric(df["Estimated capacity by IEA (Mt CO2/yr)"], errors="coerce")

    rows = []

    # -----------------------------------------------------------------------
    # 1. Operational capacity time series — what's actually capturing CO2?
    #    Only count Full Chain, Capture, and CCU projects (per IEA methodology)
    # -----------------------------------------------------------------------
    capture_types = ["Full Chain", "Capture", "Ccu"]
    capture_df = df[df["Project type"].isin(capture_types)].copy()

    # Operational projects with known operation year
    operational = capture_df[
        (capture_df["Project status"] == "Operational") &
        (capture_df["Operation"].notna())
    ].copy()
    operational["op_year"] = operational["Operation"].astype(int)

    # Build cumulative operational capacity by year
    if not operational.empty:
        for year in range(operational["op_year"].min(), 2026):
            active = operational[
                (operational["op_year"] <= year) &
                # Exclude if decommissioned/suspended before this year
                ~(
                    (operational["Suspension/decommissioning/cancellation"].notna()) &
                    (operational["Suspension/decommissioning/cancellation"] <= year)
                )
            ]
            cum_cap = active["capacity_mt"].sum()
            n_proj = len(active)
            rows.append({
                "year": year,
                "metric": "operational_capacity",
                "category": "operational",
                "value": round(cum_cap, 1),
                "unit": "MtCO2/yr",
                "n_projects": n_proj,
            })

    # -----------------------------------------------------------------------
    # 2. Pipeline snapshot — what's announced/planned vs operational
    #    This shows the massive gap between plans and reality
    # -----------------------------------------------------------------------
    for status in ["Operational", "Under construction", "Planned", "Cancelled"]:
        status_df = capture_df[capture_df["Project status"] == status]
        cap = status_df["capacity_mt"].sum()
        n = len(status_df)
        rows.append({
            "year": 2026,
            "metric": "pipeline",
            "category": status.lower().replace(" ", "_"),
            "value": round(cap, 1),
            "unit": "MtCO2/yr",
            "n_projects": n,
        })

    # -----------------------------------------------------------------------
    # 3. Sector breakdown of operational projects
    # -----------------------------------------------------------------------
    if not operational.empty:
        for sector, grp in operational.groupby("Sector"):
            cap = grp["capacity_mt"].sum()
            rows.append({
                "year": 2026,
                "metric": "operational_by_sector",
                "category": sector,
                "value": round(cap, 1),
                "unit": "MtCO2/yr",
                "n_projects": len(grp),
            })

    # -----------------------------------------------------------------------
    # 4. Under construction — what's coming next
    # -----------------------------------------------------------------------
    under_construction = capture_df[capture_df["Project status"] == "Under construction"]
    if not under_construction.empty:
        uc_cap = under_construction["capacity_mt"].sum()
        rows.append({
            "year": 2026,
            "metric": "under_construction_total",
            "category": "under_construction",
            "value": round(uc_cap, 1),
            "unit": "MtCO2/yr",
            "n_projects": len(under_construction),
        })

    result = pd.DataFrame(rows)
    return result


if __name__ == "__main__":
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df = process_ccus()
    df.to_parquet(OUTPUT_PATH, index=False)
    print(f"[process_ccus] Wrote {len(df)} rows → {OUTPUT_PATH}")

    # Summary
    pipeline = df[df["metric"] == "pipeline"]
    for _, row in pipeline.iterrows():
        print(f"  {row['category']}: {row['value']} MtCO2/yr ({row['n_projects']} projects)")

    op_ts = df[df["metric"] == "operational_capacity"]
    if not op_ts.empty:
        latest = op_ts.iloc[-1]
        print(f"  Latest operational: {latest['value']} MtCO2/yr ({latest['n_projects']} projects) in {latest['year']}")
