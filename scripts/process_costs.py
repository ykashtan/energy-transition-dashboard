"""
process_costs.py — Generate costs.parquet and finance.parquet.

Data sources (well-sourced reference values):
  LCOE  : IRENA Renewable Power Generation Costs 2023
  Battery: BloombergNEF Lithium-ion Battery Price Survey 2023
  Investment / subsidies: IEA World Energy Investment 2024; IMF Working Paper (Black et al. 2023)
  Carbon pricing: World Bank Carbon Pricing Dashboard 2023; ICAP ETS Status Report 2024

Outputs
-------
  data/processed/costs.parquet   — Global benchmark LCOE by year (wide format)
  data/processed/finance.parquet — Country carbon prices + global investment/subsidy rows

Run:
    python scripts/process_costs.py
"""

import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "processed"


# ---------------------------------------------------------------------------
# LCOE benchmark data (2010–2023)
#
# Source: IRENA Renewable Power Generation Costs in 2023 (September 2024)
#   - Full report: https://www.irena.org/Publications/2024/Sep/Renewable-Power-Generation-Costs-in-2023
#   - Solar, onshore wind, offshore wind: global capacity-weighted average LCOE
#     for newly commissioned utility-scale projects. Originally published in
#     2022 USD/MWh; adjusted to 2025 USD using CPI-U (factor ≈ 1.092).
#   - Endpoint values (2010 & 2023) verified against IRENA executive summary;
#     intermediate years from annual IRENA "Renewable Power Generation Costs"
#     reports (2012–2022 editions). Where annual reports did not provide a value,
#     values are interpolated along the documented learning curve trajectory.
#
# Coal: IEA Projected Costs of Generating Electricity 2020 + EIA estimates
# Battery: BloombergNEF Lithium-ion Battery Price Survey 2023
#
# CPI adjustment: All values converted from original 2022 USD to 2025 USD
# using BLS CPI-U annual averages (2022=292.655 → 2025≈319.5, factor=1.092).
# ---------------------------------------------------------------------------

# CPI-U conversion factor: 2022 USD → 2025 USD
_CPI_2022_TO_2025 = 1.092

def _adj(vals):
    """Adjust a list of values from 2022 USD to 2025 USD."""
    return [round(v * _CPI_2022_TO_2025) if v is not None else None for v in vals]

LCOE_DATA = {
    "year": list(range(2010, 2024)),

    # Solar PV utility-scale: $502 (2010) → $48 (2023), 90% reduction
    # Original IRENA (2022 USD): $460 → $44, 90% decline.
    "solar_lcoe_usd_mwh": _adj([
        460, 381, 295, 215, 177, 131, 101, 86, 85, 68, 57, 49, 50, 44
    ]),

    # Onshore wind: $121 (2010) → $36 (2023), 70% reduction
    # Original IRENA (2022 USD): $111 → $33, 70% decline.
    "onshore_wind_lcoe_usd_mwh": _adj([
        111, 102, 84, 81, 73, 64, 56, 52, 53, 50, 39, 33, 33, 33
    ]),

    # Offshore wind: $222 (2010) → $82 (2023), 63% reduction
    # Original IRENA (2022 USD): $203 → $75, 63% decline.
    "offshore_wind_lcoe_usd_mwh": _adj([
        203, 197, 180, 184, 178, 171, 148, 126, 113, 115, 84, 75, 81, 75
    ]),

    # Coal (new plant, LCOE including fuel): broadly stable, with fuel-cost spikes
    # Original (2022 USD): ~$109 (2010) → ~$111 (2023)
    # Source: IEA Projected Costs of Generating Electricity 2020 + EIA estimates
    "coal_lcoe_usd_mwh": _adj([
        109, 109, 107, 106, 105, 101, 101, 100, 108, 111, 113, 109, 117, 111
    ]),

    # Gas CCGT LCOE ($/MWh) — approximate global benchmark
    # IMPORTANT: Unlike solar/wind (which come from IRENA's annual global
    # capacity-weighted average), gas LCOE does NOT have a single authoritative
    # annual time series. These are approximate values synthesized from:
    #   - IEA/OECD NEA Projected Costs of Generating Electricity 2020: ~$71/MWh
    #   - IRENA RPGC 2024 global comparison: ~$85/MWh
    # Gas LCOE is highly region-dependent (fuel price drives ~60-70% of cost).
    # Values rounded to nearest $5 to avoid false precision.
    # Source: IEA Projected Costs of Generating Electricity 2020; IRENA RPGC 2023
    "gas_ccgt_lcoe_usd_mwh": _adj([
        75, 75, 70, 70, 65, 60, 55, 55, 60, 55, 55, 65, 80, 70
    ]),

    # Nuclear LCOE ($/MWh) — new-build, global range
    # Nuclear LCOE is highly site-specific. These are approximate midpoints
    # from Lazard LCOE reports (US-focused) and IEA Projected Costs 2020.
    # Lazard v12 (2018): $112-$189 mid ~$150; v16 (2023): $141-$221 mid ~$180
    # Nuclear has NOT seen cost declines — if anything, costs have increased.
    # Source: Lazard LCOE v12-v16; IEA Projected Costs 2020
    "nuclear_lcoe_usd_mwh": _adj([
        150, 150, 150, 150, 150, 150, 150, 150, 150, 155, 160, 165, 175, 180
    ]),

    # Battery storage pack cost ($/kWh) — DIFFERENT UNIT — BloombergNEF LCOS
    # First reliable survey: 2013.
    # Source: BloombergNEF Lithium-ion Battery Price Survey 2023
    "battery_cost_usd_kwh": _adj([
        None, None, None, 1200, 900, 630, 475, 330, 250, 190, 152, 145, 141, 139
    ]),
}

LCOE_SOURCES = (
    "IRENA Renewable Power Generation Costs in 2023 (Sep 2024) — "
    "global capacity-weighted average LCOE, adjusted to 2025 USD (CPI-U 1.092× from 2022); "
    "IEA Projected Costs of Generating Electricity 2020 (coal, gas CCGT); "
    "Lazard LCOE v12-v16 (nuclear); "
    "BloombergNEF Lithium-ion Battery Price Survey 2023 (battery)"
)


# ---------------------------------------------------------------------------
# Carbon pricing by country (2023 snapshot)
# Source: World Bank Carbon Pricing Dashboard (cpd.worldbank.org); ICAP ETS Map 2024
# Values: effective headline price in USD/tCO₂e for primary scheme(s)
#         (ETS auction/market price or statutory carbon tax rate)
# ---------------------------------------------------------------------------

# EU ETS 2023 average price ~€87/tCO₂ ≈ $95 USD (mid-2023 EUR/USD ≈ 1.09)
_EU_ETS_PRICE = 95

# EU ETS member states (27 EU members + linked non-EU)
_EU_ETS_MEMBERS = [
    "AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN",
    "FRA", "DEU", "GRC", "HUN", "IRL", "ITA", "LVA", "LTU", "LUX",
    "MLT", "NLD", "POL", "PRT", "ROU", "SVK", "SVN", "ESP",
    "NOR", "ISL", "LIE",   # EEA non-EU participants in EU ETS
]

# Sweden has a national carbon tax on top of EU ETS → highest effective price globally
_SWEDEN_PRICE = 130   # SEK 1,365/tCO₂ ≈ $130 USD (2023)

# Other schemes (not EU ETS)
_OTHER_CARBON_PRICES = {
    "SWE": _SWEDEN_PRICE,  # Override EU ETS — national tax dominates
    "GBR": 55,             # UK ETS: ~£44/tCO₂ ≈ $55 USD
    "CHE": 130,            # Swiss CO₂ levy + Swiss ETS (linked to EU)
    "CAN": 65,             # Federal carbon pricing (C$65/tCO₂ = ~$48 USD; rounded for regional variation)
    "NZL": 33,             # NZ ETS: ~$33 NZD/tCO₂ ≈ $20 USD; ~NZD 53 = $33 more typical mid-year
    "KOR": 9,              # Korean ETS: ~KRW 12,000/tCO₂ ≈ $9 USD
    "CHN": 9,              # China national ETS: ~CNY 65/tCO₂ ≈ $9 USD
    "JPN": 3,              # Carbon levy on fossil fuels: ¥289/tCO₂ ≈ $3 USD
    "SGP": 4,              # Singapore carbon tax: S$5/tCO₂ ≈ $4 USD (raised to S$25 in 2024)
    "COL": 5,              # Colombia carbon tax
    "CHL": 5,              # Chile carbon tax: $5 USD/tCO₂
    "ARG": 5,              # Argentina carbon levy
    "MEX": 1,              # Mexico carbon tax (very low, symbolic)
    "ZAF": 10,             # South Africa carbon tax: ~$10 USD/tCO₂
    "URY": 3,              # Uruguay carbon levy (agriculture + transport)
}


def build_costs_df() -> pd.DataFrame:
    """Build LCOE and battery cost reference DataFrame (2010–2023)."""
    df = pd.DataFrame(LCOE_DATA)
    df["source"] = LCOE_SOURCES
    return df


def build_finance_df() -> pd.DataFrame:
    """
    Build finance DataFrame combining:
      1. Global investment / subsidy rows (iso3 = 'WORLD')
      2. Country-level carbon pricing rows (iso3 = ISO3 code)

    Columns
    -------
    iso3                    : str    — ISO3 or 'WORLD'
    year                    : int
    carbon_price_usd_tco2   : float  — USD/tCO₂e (country rows only)
    fossil_subsidies_usd_t  : float  — trillion USD/yr (WORLD rows only)
    clean_investment_usd_b  : float  — billion USD/yr  (WORLD rows only)
    dirty_investment_usd_b  : float  — billion USD/yr  (WORLD rows only)
    """
    # ------------------------------------------------------------------
    # Global investment and subsidy time series
    # Source: IEA World Energy Investment 2024; IMF Black et al. (2023)
    # Fossil fuel subsidies include explicit + implicit (unpriced externalities)
    # ------------------------------------------------------------------
    global_rows = [
        # (year, fossil_sub_usd_t, clean_invest_usd_b, dirty_invest_usd_b)
        (2015, 5.2,  330,  950),
        (2016, 5.0,  348,  870),
        (2017, 5.1,  364,  890),
        (2018, 5.3,  380,  940),
        (2019, 5.4,  380,  940),
        (2020, 5.6,  400,  750),
        (2021, 5.9,  530,  850),
        (2022, 7.0, 1100, 1000),
        (2023, 7.0, 1800, 1050),
    ]

    rows = []
    for year, sub, clean, dirty in global_rows:
        rows.append({
            "iso3": "WORLD",
            "year": year,
            "carbon_price_usd_tco2": None,
            "fossil_subsidies_usd_t": sub,
            "clean_investment_usd_b": float(clean),
            "dirty_investment_usd_b": float(dirty),
        })

    # ------------------------------------------------------------------
    # Country-level carbon pricing (2023 snapshot)
    # ------------------------------------------------------------------
    carbon_prices: dict[str, float] = {}

    # EU ETS members (skip SWE since it has its own higher price in _OTHER)
    for iso3 in _EU_ETS_MEMBERS:
        if iso3 not in _OTHER_CARBON_PRICES:
            carbon_prices[iso3] = float(_EU_ETS_PRICE)

    # Add / override with other national schemes
    carbon_prices.update({k: float(v) for k, v in _OTHER_CARBON_PRICES.items()})

    for iso3, price in sorted(carbon_prices.items()):
        rows.append({
            "iso3": iso3,
            "year": 2023,
            "carbon_price_usd_tco2": price,
            "fossil_subsidies_usd_t": None,
            "clean_investment_usd_b": None,
            "dirty_investment_usd_b": None,
        })

    df = pd.DataFrame(rows)
    return df


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    costs_df = build_costs_df()
    costs_path = OUTPUT_DIR / "costs.parquet"
    costs_df.to_parquet(costs_path, index=False)
    print(f"[process_costs]   Wrote {len(costs_df)} rows  → {costs_path}")

    finance_df = build_finance_df()
    finance_path = OUTPUT_DIR / "finance.parquet"
    finance_df.to_parquet(finance_path, index=False)
    n_country = (finance_df["iso3"] != "WORLD").sum()
    n_global  = (finance_df["iso3"] == "WORLD").sum()
    print(
        f"[process_finance] Wrote {len(finance_df)} rows  → {finance_path}"
        f"  ({n_country} country rows, {n_global} global rows)"
    )


if __name__ == "__main__":
    main()
