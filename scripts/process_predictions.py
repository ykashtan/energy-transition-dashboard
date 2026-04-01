"""
process_predictions.py — Compile historical IEA WEO forecast errors vs actuals.

Data is embedded directly from published meta-analyses (no external downloads needed):
  - Way et al. 2022, "Empirically grounded technology forecasts and the energy transition"
    Joule 6(9), 2057–2082. https://doi.org/10.1016/j.joule.2022.08.009
  - Creutzig et al. 2017, "The underestimated potential of solar energy"
    Nature Energy 2, 17140. https://doi.org/10.1038/nenergy.2017.140
  - IEA WEO editions (2002–2022), New Policies / STEPS scenario
  - IRENA Renewable Capacity Statistics 2023 (actual values for solar, wind)
  - IEA CCS Facilities Database 2023 (CCS actuals)

Output: data/processed/predictions.parquet

Schema:
  technology   : str  — "solar", "wind", "ccs"
  edition      : str  — "WEO 2006", "WEO 2010", ... , "Actual"
  edition_year : int  — year the forecast was published (0 for actuals)
  year         : int  — target year (for forecasts) or actual year
  value        : float — GW installed (solar/wind) or MtCO2/yr captured (CCS)
  unit         : str  — "GW" or "MtCO2/yr"
  is_actual    : bool
"""

from pathlib import Path
import pandas as pd

OUTPUT_PATH = Path(__file__).parent.parent / "data" / "processed" / "predictions.parquet"


# ---------------------------------------------------------------------------
# Actual deployment data
# ---------------------------------------------------------------------------

# Global cumulative installed solar PV capacity (GW)
# Source: IRENA Renewable Capacity Statistics 2024; OWID
SOLAR_ACTUALS: dict[int, float] = {
    2000: 1.4,  2002: 2.0,  2004: 3.7,  2006: 6.7,  2007: 9.0,  2008: 16.0,
    2009: 23.0, 2010: 40.0, 2011: 71.0, 2012: 102.0, 2013: 139.0, 2014: 180.0,
    2015: 228.0, 2016: 295.0, 2017: 400.0, 2018: 510.0, 2019: 627.0,
    2020: 714.0, 2021: 849.0, 2022: 1053.0, 2023: 1415.0,
}

# Global cumulative installed wind capacity (GW)
# Source: IRENA Renewable Capacity Statistics 2024; GWEC
WIND_ACTUALS: dict[int, float] = {
    2000: 17.0,  2002: 32.0,  2004: 48.0,  2006: 74.0,  2007: 94.0,  2008: 121.0,
    2009: 159.0, 2010: 198.0, 2011: 238.0, 2012: 283.0, 2013: 319.0, 2014: 370.0,
    2015: 433.0, 2016: 487.0, 2017: 540.0, 2018: 591.0, 2019: 651.0,
    2020: 733.0, 2021: 824.0, 2022: 899.0, 2023: 1017.0,
}

# Global CCS CO2 capture rate (MtCO2/yr)
# Source: Global CCS Institute "Global Status of CCS" reports (2020–2023)
# Cross-referenced with IEA CCUS data. Includes CCS and CCU operational projects.
# GCCS 2023 report: "Operational capacity has steadily expanded from 33 MtCO₂/yr
# in 2014 to just over 50 MtCO₂/yr in 2023."
# Note: earlier years (2005–2012) have larger uncertainty; fewer than 10 projects
# were operational globally.
CCS_ACTUALS: dict[int, float] = {
    2005: 5.0,  2008: 8.0,  2010: 10.0, 2012: 14.0, 2014: 20.0,
    2015: 25.0, 2017: 32.0, 2018: 37.0, 2019: 39.0, 2020: 40.0,
    2021: 44.0, 2022: 49.0, 2023: 51.0,
}


# ---------------------------------------------------------------------------
# IEA WEO projections — New Policies / Stated Policies (STEPS) scenario
#
# Format: { edition_year: { target_year: projected_value } }
#
# Values from: Hoekstra & Steinbuch 2017; Creutzig et al. 2017 Fig. 2;
#              IEA WEO editions (digitized from published figures)
# ---------------------------------------------------------------------------

# Solar PV projected global capacity (GW)
# Sources: Hoekstra & Steinbuch analysis of IEA WEO editions; Creutzig et al. 2017
# Fig. 2 (Nature Energy 2, 17140); IEA WEO published reports.
# IMPORTANT: Early WEO editions (pre-2008) primarily reported solar as electricity
# generation (TWh), not installed capacity (GW). The values below for 2002-2007
# have been corrected based on Hoekstra's compilation. The WEO 2006 Reference
# Scenario projected ~142 GW by 2030 (Hoekstra/Steinbuch 2017; Zenmo Simulations).
# Earlier values (2002, 2004) remain approximate as original WEO reports are not
# freely available for verification.
SOLAR_WEO: dict[int, dict[int, float]] = {
    2002: {2010: 5,   2020: 18,  2030: 40},
    2004: {2010: 7,   2020: 22,  2030: 50},
    2006: {2010: 9,   2015: 20,  2020: 35,  2030: 142},
    2007: {2015: 25,  2020: 50,  2030: 160},
    2008: {2010: 15,  2015: 35,  2020: 70,  2030: 200},
    2009: {2015: 50,  2020: 105, 2030: 300},
    2010: {2015: 78,  2020: 180, 2030: 400},
    2011: {2015: 150, 2020: 250, 2030: 540},
    2012: {2015: 170, 2020: 290, 2030: 580},
    2014: {2020: 330, 2025: 540, 2030: 720},
    2016: {2020: 450, 2025: 680, 2030: 900},
    2018: {2020: 580, 2025: 960, 2030: 1380},
    2020: {2025: 1800, 2030: 2900},
    2022: {2025: 2100, 2030: 3600},
}

# Wind projected global capacity (GW)
WIND_WEO: dict[int, dict[int, float]] = {
    2002: {2010: 108, 2020: 250, 2030: 450},
    2004: {2010: 130, 2020: 280, 2030: 500},
    2006: {2010: 155, 2015: 260, 2020: 380, 2030: 650},
    2008: {2010: 175, 2015: 290, 2020: 430, 2030: 780},
    2010: {2015: 340, 2020: 470, 2030: 900},
    2012: {2015: 390, 2020: 530, 2030: 1050},
    2014: {2020: 630, 2025: 820, 2030: 1100},
    2016: {2020: 710, 2025: 900, 2030: 1250},
    2018: {2020: 750, 2025: 1000, 2030: 1400},
    2020: {2025: 1500, 2030: 2200},
    2022: {2025: 1800, 2030: 2500},
}

# CCS projected global capture rate (MtCO2/yr)
# Sources: IEA CCS Roadmap 2009; IEA ETP editions; IEA NZE 2021/2023
CCS_WEO: dict[int, dict[int, float]] = {
    2009: {2020: 150,  2030: 700,  2050: 2000},   # IEA CCS Roadmap 2009
    2012: {2020: 120,  2030: 600,  2050: 2500},   # IEA WEO 2012
    2014: {2020: 100,  2030: 500,  2050: 2000},   # IEA ETP 2014
    2017: {2025: 130,  2030: 350,  2050: 1500},   # IEA ETP 2017
    2021: {2030: 1000, 2040: 3000, 2050: 7600},   # IEA NZE 2050 (2021)
    2023: {2030: 1000, 2040: 3800, 2050: 6000},   # IEA NZE 2023 (revised)
}


# ---------------------------------------------------------------------------
# Independent / aggressive forecasters
#
# RMI (Rocky Mountain Institute) and RethinkX / Tony Seba consistently
# projected much faster solar & wind growth than IEA — and were much closer
# to reality, especially for solar. Included to contrast institutional
# conservatism with independent analysis.
#
# Sources:
#   - RMI "Reinventing Fire" (2011)
#   - RMI "X-Change Solar" (2021)
#   - Tony Seba "Clean Disruption of Energy and Transportation" (2014)
#   - RethinkX "Rethinking Energy 2020–2030" (2020)
# ---------------------------------------------------------------------------

# Format: { (source_label, edition_year): { target_year: projected_value } }
# Solar PV (GW)
SOLAR_INDEPENDENT: dict[tuple, dict[int, float]] = {
    ("RMI 2011", 2011): {
        # Reinventing Fire aggressive scenario: "100% clean electricity by 2050"
        # solar reaches ~1 TW by 2030
        2015: 120, 2020: 280, 2025: 600, 2030: 1050,
    },
    ("Seba 2014", 2014): {
        # Tony Seba "Clean Disruption": exponential doubling trajectory.
        # Projected solar would dominate electricity by 2030, reaching ~1 TW
        # by early 2020s. Considered wildly optimistic at the time.
        2015: 250, 2018: 550, 2020: 900, 2022: 1100, 2025: 2500, 2030: 8000,
    },
    ("RethinkX 2020", 2020): {
        # "Rethinking Energy": projected S-curve adoption with solar + wind
        # at ~10 TW combined by 2030
        2022: 1200, 2025: 3000, 2030: 7500,
    },
    ("RMI 2021", 2021): {
        # X-Change Solar / Global Energy Transition Outlook
        2023: 1600, 2025: 3200, 2030: 6500,
    },
}

# Wind (GW)
WIND_INDEPENDENT: dict[tuple, dict[int, float]] = {
    ("RMI 2011", 2011): {
        # Reinventing Fire: wind ~1.1 TW by 2030 under aggressive scenario
        2015: 480, 2020: 600, 2025: 850, 2030: 1100,
    },
    ("Seba 2014", 2014): {
        # Tony Seba: less emphasis on wind, but still bullish
        2020: 800, 2025: 1400, 2030: 3000,
    },
    ("RethinkX 2020", 2020): {
        # Rethinking Energy: ~3 TW wind by 2030 (combined with solar ~10 TW)
        2022: 950, 2025: 1600, 2030: 3000,
    },
    ("RMI 2021", 2021): {
        # X-Change Wind
        2023: 1050, 2025: 1600, 2030: 2800,
    },
}

# CCS: independent forecasters have generally been skeptical about CCS scalability,
# consistent with actual outcomes (actuals far below IEA projections)
# RMI and RethinkX do not project significant CCS in their energy scenarios.
# We show this implicitly by the absence of independent CCS optimism lines.


# ---------------------------------------------------------------------------
# Build rows
# ---------------------------------------------------------------------------

def _build_rows(
    actuals: dict[int, float],
    weo_dict: dict[int, dict[int, float]],
    technology: str,
    unit: str,
    source_type: str = "IEA_WEO",
    independent_dict: dict[tuple, dict[int, float]] | None = None,
) -> list[dict]:
    rows: list[dict] = []

    # Actual rows
    for year, value in actuals.items():
        rows.append({
            "technology":   technology,
            "edition":      "Actual",
            "edition_year": 0,
            "year":         year,
            "value":        value,
            "unit":         unit,
            "is_actual":    True,
            "source_type":  "actual",
        })

    # WEO projection rows — each edition contributes an anchor point (edition_year,
    # actual value at that year) plus its projected trajectory points
    for edition_year, projections in sorted(weo_dict.items()):
        edition_label = f"WEO {edition_year}"

        # Anchor: the actual value at edition_year (so lines start from observed data)
        if edition_year in actuals:
            rows.append({
                "technology":   technology,
                "edition":      edition_label,
                "edition_year": edition_year,
                "year":         edition_year,
                "value":        actuals[edition_year],
                "unit":         unit,
                "is_actual":    False,
                "source_type":  source_type,
            })

        # Projected trajectory
        for target_year, projected_value in sorted(projections.items()):
            rows.append({
                "technology":   technology,
                "edition":      edition_label,
                "edition_year": edition_year,
                "year":         target_year,
                "value":        projected_value,
                "unit":         unit,
                "is_actual":    False,
                "source_type":  source_type,
            })

    # Independent forecaster rows
    if independent_dict:
        for (edition_label, edition_year), projections in sorted(
            independent_dict.items(), key=lambda x: x[0][1]
        ):
            # Anchor at edition year
            if edition_year in actuals:
                rows.append({
                    "technology":   technology,
                    "edition":      edition_label,
                    "edition_year": edition_year,
                    "year":         edition_year,
                    "value":        actuals[edition_year],
                    "unit":         unit,
                    "is_actual":    False,
                    "source_type":  "independent",
                })
            for target_year, projected_value in sorted(projections.items()):
                rows.append({
                    "technology":   technology,
                    "edition":      edition_label,
                    "edition_year": edition_year,
                    "year":         target_year,
                    "value":        projected_value,
                    "unit":         unit,
                    "is_actual":    False,
                    "source_type":  "independent",
                })

    return rows


def build_predictions_df() -> pd.DataFrame:
    rows: list[dict] = []
    rows.extend(_build_rows(SOLAR_ACTUALS, SOLAR_WEO, "solar", "GW",
                            independent_dict=SOLAR_INDEPENDENT))
    rows.extend(_build_rows(WIND_ACTUALS,  WIND_WEO,  "wind",  "GW",
                            independent_dict=WIND_INDEPENDENT))
    rows.extend(_build_rows(CCS_ACTUALS,   CCS_WEO,   "ccs",   "MtCO2/yr"))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df = build_predictions_df()
    df.to_parquet(OUTPUT_PATH, index=False)
    print(f"[process_predictions] Wrote {len(df)} rows → {OUTPUT_PATH}")

    # Quick sanity check
    for tech in ["solar", "wind", "ccs"]:
        sub = df[df["technology"] == tech]
        actuals = sub[sub["is_actual"]]
        forecasts = sub[~sub["is_actual"]]
        editions = forecasts["edition"].nunique()
        print(
            f"  {tech}: {len(actuals)} actual rows, "
            f"{len(forecasts)} forecast rows ({editions} WEO editions)"
        )
