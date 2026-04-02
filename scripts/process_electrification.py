"""
process_electrification.py — Process IEA Global EV Data Explorer into
dashboard-ready parquet files for the Electrification section.

Inputs:
  - data/raw/EV Data Explorer 2025.xlsx  (IEA GEVO 2025, CC BY 4.0)

Outputs:
  - data/processed/ev_sales_share.parquet   (EV sales share % by region, cars)
  - data/processed/ev_sales.parquet         (EV sales absolute by region, cars + trucks)
  - data/processed/electrification_kpis.json (headline numbers for hero bar)
"""

import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

EV_FILE = RAW_DIR / "EV Data Explorer 2025.xlsx"


def process_ev_data():
    """Process EV data from IEA xlsx into clean parquet files."""
    if not EV_FILE.exists():
        print(f"[process_electrification] WARNING: {EV_FILE} not found. Skipping.")
        return

    print(f"[process_electrification] Reading {EV_FILE}...")
    df = pd.read_excel(EV_FILE)

    # -----------------------------------------------------------------------
    # 1. EV Sales Share (%) for Cars — main S-curve data
    # -----------------------------------------------------------------------
    share = df[
        (df["parameter"] == "EV sales share")
        & (df["mode"] == "Cars")
        & (df["powertrain"] == "EV")       # BEV + PHEV combined
        & (df["category"] == "Historical")  # exclude projections
    ][["region_country", "year", "value"]].copy()
    share = share.rename(columns={"region_country": "region", "value": "ev_share_pct"})
    share = share.dropna(subset=["ev_share_pct"])
    share = share.sort_values(["region", "year"])

    # Key regions for the S-curve chart
    key_regions = [
        "World", "China", "EU27", "USA", "Norway", "India",
        "Germany", "France", "United Kingdom", "Japan", "Korea",
        "Brazil", "Thailand", "Indonesia", "Viet Nam",
    ]
    share["is_key_region"] = share["region"].isin(key_regions)

    share.to_parquet(PROCESSED_DIR / "ev_sales_share.parquet", index=False)
    print(f"  -> ev_sales_share.parquet: {len(share)} rows, {share['region'].nunique()} regions")

    # -----------------------------------------------------------------------
    # 2. EV Sales (absolute) for Cars and Trucks
    # -----------------------------------------------------------------------
    # EV sales: sum BEV + PHEV (no "EV" aggregate for absolute sales)
    sales = df[
        (df["parameter"] == "EV sales")
        & (df["powertrain"].isin(["BEV", "PHEV"]))
        & (df["category"] == "Historical")
        & (df["mode"].isin(["Cars", "Trucks", "Buses", "Vans"]))
    ][["region_country", "mode", "year", "value"]].copy()
    sales = sales.rename(columns={"region_country": "region", "value": "ev_sales"})
    sales = sales.dropna(subset=["ev_sales"])
    # Sum BEV + PHEV per region/mode/year
    sales = sales.groupby(["region", "mode", "year"], as_index=False)["ev_sales"].sum()
    sales = sales.sort_values(["region", "mode", "year"])

    sales.to_parquet(PROCESSED_DIR / "ev_sales.parquet", index=False)
    print(f"  -> ev_sales.parquet: {len(sales)} rows")

    # -----------------------------------------------------------------------
    # 3. EV Stock for global context
    # -----------------------------------------------------------------------
    # EV stock: sum BEV + PHEV
    stock = df[
        (df["parameter"] == "EV stock")
        & (df["powertrain"].isin(["BEV", "PHEV"]))
        & (df["category"] == "Historical")
        & (df["mode"] == "Cars")
    ][["region_country", "year", "value"]].copy()
    stock = stock.rename(columns={"region_country": "region", "value": "ev_stock"})
    stock = stock.dropna(subset=["ev_stock"])
    stock = stock.groupby(["region", "year"], as_index=False)["ev_stock"].sum()

    stock.to_parquet(PROCESSED_DIR / "ev_stock.parquet", index=False)
    print(f"  -> ev_stock.parquet: {len(stock)} rows")

    # -----------------------------------------------------------------------
    # 4. Headline KPIs for the Electrification hero bar
    # -----------------------------------------------------------------------
    kpis = {}

    # Global EV share of new car sales (latest year)
    world_share = share[share["region"] == "World"].sort_values("year")
    if not world_share.empty:
        latest = world_share.iloc[-1]
        kpis["ev_share_global"] = {
            "value": round(float(latest["ev_share_pct"]), 1),
            "year": int(latest["year"]),
            "unit": "%",
            "label": "Global EV share of new car sales",
            "source": "IEA Global EV Outlook 2025",
        }

    # China EV share
    china_share = share[share["region"] == "China"].sort_values("year")
    if not china_share.empty:
        latest_cn = china_share.iloc[-1]
        kpis["ev_share_china"] = {
            "value": round(float(latest_cn["ev_share_pct"]), 1),
            "year": int(latest_cn["year"]),
            "unit": "%",
            "label": "China EV share of new car sales",
            "source": "IEA Global EV Outlook 2025",
        }

    # Global EV stock
    world_stock = stock[stock["region"] == "World"].sort_values("year")
    if not world_stock.empty:
        latest_stock = world_stock.iloc[-1]
        stock_m = float(latest_stock["ev_stock"]) / 1e6
        kpis["ev_stock_global"] = {
            "value": round(stock_m, 0),
            "year": int(latest_stock["year"]),
            "unit": "M",
            "label": "Global EV fleet",
            "source": "IEA Global EV Outlook 2025",
        }

    # S-curve tipping point analysis: which regions have crossed 5% and 10%
    tipping = {}
    for region in key_regions:
        rs = share[share["region"] == region].sort_values("year")
        crossed_5 = rs[rs["ev_share_pct"] >= 5.0]
        crossed_10 = rs[rs["ev_share_pct"] >= 10.0]
        if not crossed_5.empty:
            tipping[region] = {
                "crossed_5pct_year": int(crossed_5.iloc[0]["year"]),
                "crossed_10pct_year": int(crossed_10.iloc[0]["year"]) if not crossed_10.empty else None,
                "latest_share": round(float(rs.iloc[-1]["ev_share_pct"]), 1),
            }
    kpis["tipping_points"] = tipping

    # Count how many key regions crossed 5% tipping point
    n_tipped = len(tipping)
    kpis["n_regions_past_tipping"] = {
        "value": n_tipped,
        "total": len(key_regions),
        "label": "Key markets past 5% EV tipping point",
        "source": "IEA Global EV Outlook 2025",
    }

    # Electric truck sales global (latest year)
    truck_sales = sales[(sales["mode"] == "Trucks") & (sales["region"] == "World")]
    truck_sales = truck_sales.sort_values("year")
    if not truck_sales.empty:
        latest_truck = truck_sales.iloc[-1]
        kpis["truck_ev_sales_global"] = {
            "value": int(latest_truck["ev_sales"]),
            "year": int(latest_truck["year"]),
            "label": "Global electric truck sales",
            "source": "IEA Global EV Outlook 2025",
        }

    kpi_path = PROCESSED_DIR / "electrification_kpis.json"
    with open(kpi_path, "w") as f:
        json.dump(kpis, f, indent=2)
    print(f"  -> electrification_kpis.json: {len(kpis)} KPIs")


if __name__ == "__main__":
    process_ev_data()
    print("[process_electrification] Done.")
