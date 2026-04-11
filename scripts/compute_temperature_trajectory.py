"""
compute_temperature_trajectory.py — Bottom-up temperature projection from S-curve adoption.

Instead of using top-down policy assumptions (UNEP's 3.1°C), this model:
1. Takes fitted S-curve adoption rates for each clean technology
2. Maps adoption to sector-by-sector fossil fuel displacement
3. Projects an emissions trajectory
4. Converts cumulative emissions to temperature via TCRE

Output: data/processed/temperature_trajectory.json

Sources:
  - TCRE: IPCC AR6 WG1, 0.45°C per 1000 GtCO2 (likely range 0.27–0.63)
  - Sector baselines: IPCC AR6 WG3 Ch. 2, 2024 values
  - Current warming: 1.3°C above 1850-1900 (IPCC AR6)
  - Current policies: 3.1°C (UNEP Emissions Gap Report 2024)
"""

import json
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


# ---------------------------------------------------------------------------
# Logistic S-curve
# ---------------------------------------------------------------------------

def logistic(t, K, r, t0):
    """S(t) = K / (1 + exp(-r * (t - t0)))"""
    return K / (1.0 + np.exp(-r * (t - t0)))


# ---------------------------------------------------------------------------
# Sector emissions baselines (2024, GtCO2e/yr)
# Source: IPCC AR6 WG3, updated with 2024 estimates
# ---------------------------------------------------------------------------

SECTORS = {
    "electricity": {
        "baseline_gtco2e": 13.6,
        "share_of_total": 0.25,
        "description": "Electricity & heat generation",
    },
    "road_transport": {
        "baseline_gtco2e": 6.5,
        "share_of_total": 0.12,
        "description": "Road transport (cars, trucks, buses)",
    },
    "aviation": {
        "baseline_gtco2e": 1.4,
        "share_of_total": 0.025,
        "description": "Aviation",
    },
    "shipping": {
        "baseline_gtco2e": 0.8,
        "share_of_total": 0.015,
        "description": "Shipping",
    },
    "industry": {
        "baseline_gtco2e": 11.4,
        "share_of_total": 0.21,
        "description": "Industry (steel, cement, chemicals)",
    },
    "buildings": {
        "baseline_gtco2e": 3.3,
        "share_of_total": 0.06,
        "description": "Buildings (direct heating, cooking)",
    },
    "agriculture": {
        "baseline_gtco2e": 12.0,
        "share_of_total": 0.22,
        "description": "Agriculture, forestry & land use",
    },
    "other": {
        "baseline_gtco2e": 5.4,
        "share_of_total": 0.10,
        "description": "Waste, fugitive emissions, other",
    },
}

TOTAL_BASELINE = 54.4  # GtCO2e, 2024

# Climate constants
TCRE = 0.45  # °C per 1000 GtCO2 (IPCC AR6 best estimate)
TCRE_LOW = 0.27  # likely range lower bound
TCRE_HIGH = 0.63  # likely range upper bound
CURRENT_WARMING = 1.3  # °C above pre-industrial (2024)
CO2_FRACTION_OF_CO2E = 0.75  # ~75% of CO2e is actual CO2

# Fleet turnover: EV sales share → fleet share lag
FLEET_TURNOVER_YEARS = 12


def compute_sector_emissions(years, scurve_params, rate_multiplier=1.0):
    """
    Compute year-by-year emissions for each sector based on S-curve displacement.

    Parameters
    ----------
    years : array of int
    scurve_params : dict from scurve_params.json
    rate_multiplier : float, multiplies all r values (1.0=central, 1.3=fast, 0.7=slow)

    Returns dict of {sector: array of emissions by year}
    """
    n = len(years)
    results = {}

    # --- Electricity: renewable share displaces fossil ---
    ren = scurve_params.get("renewable_share_global", {})
    K_ren = ren.get("K", 100)
    r_ren = ren.get("r", 0.04) * rate_multiplier
    t0_ren = ren.get("t0", 2044)

    # Demand growth: 1.5% declining to 0% by 2074
    demand_factor = np.array([
        1.0 + 0.015 * max(0, 1.0 - (y - 2024) / 50) for y in years
    ])
    cumulative_demand = np.cumprod(demand_factor)
    # Normalize so 2024 = 1.0
    cumulative_demand = cumulative_demand / cumulative_demand[0]

    ren_share = logistic(years, K_ren, r_ren, t0_ren) / 100.0
    fossil_frac = 1.0 - ren_share
    electricity = SECTORS["electricity"]["baseline_gtco2e"] * fossil_frac * cumulative_demand
    results["electricity"] = electricity

    # --- Road transport: EV fleet share (lagged from sales share) ---
    ev = scurve_params.get("ev_share_World", {})
    K_ev = ev.get("K", 80)
    r_ev = ev.get("r", 0.41) * rate_multiplier
    t0_ev = ev.get("t0", 2026)

    # Sales share for extended range (need history for fleet averaging)
    extended_years = np.arange(years[0] - FLEET_TURNOVER_YEARS, years[-1] + 1)
    ev_sales = logistic(extended_years, K_ev, r_ev, t0_ev)

    # Fleet share = rolling average of past FLEET_TURNOVER_YEARS sales shares
    ev_fleet = np.zeros(n)
    for i, y in enumerate(years):
        idx_start = int(y - FLEET_TURNOVER_YEARS - (years[0] - FLEET_TURNOVER_YEARS))
        idx_end = int(y - (years[0] - FLEET_TURNOVER_YEARS)) + 1
        ev_fleet[i] = np.mean(ev_sales[idx_start:idx_end])

    road_fossil = 1.0 - ev_fleet / 100.0
    road = SECTORS["road_transport"]["baseline_gtco2e"] * road_fossil * cumulative_demand
    results["road_transport"] = road

    # --- Aviation: SAF adoption (EV-like S-curve, lagged ~15 years) ---
    K_av, r_av, t0_av = 80, 0.20 * rate_multiplier, 2042
    saf_share = logistic(years, K_av, r_av, t0_av) / 100.0
    # SAF reduces ~80% of lifecycle emissions per unit
    aviation = SECTORS["aviation"]["baseline_gtco2e"] * (1.0 - saf_share * 0.80)
    # Aviation demand grows ~3% per year, declining
    av_growth = np.array([1.0 + 0.03 * max(0, 1.0 - (y - 2024) / 40) for y in years])
    av_cumulative = np.cumprod(av_growth) / av_growth[0]
    aviation = aviation * av_cumulative
    results["aviation"] = aviation

    # --- Shipping: alt fuel adoption ---
    K_sh, r_sh, t0_sh = 70, 0.18 * rate_multiplier, 2044
    ship_clean = logistic(years, K_sh, r_sh, t0_sh) / 100.0
    shipping = SECTORS["shipping"]["baseline_gtco2e"] * (1.0 - ship_clean * 0.70)
    results["shipping"] = shipping

    # --- Industry: green H2 + EAF + electrification (slower) ---
    K_ind, r_ind, t0_ind = 60, 0.07 * rate_multiplier, 2048
    ind_clean = logistic(years, K_ind, r_ind, t0_ind) / 100.0
    industry = SECTORS["industry"]["baseline_gtco2e"] * (1.0 - ind_clean)
    results["industry"] = industry

    # --- Buildings: heat pumps + induction ---
    K_bld, r_bld, t0_bld = 80, 0.15 * rate_multiplier, 2035
    bld_clean = logistic(years, K_bld, r_bld, t0_bld) / 100.0
    buildings = SECTORS["buildings"]["baseline_gtco2e"] * (1.0 - bld_clean)
    results["buildings"] = buildings

    # --- Agriculture: slow reduction (0.5%/yr baseline) ---
    ag_rate = 0.005 * rate_multiplier
    agriculture = SECTORS["agriculture"]["baseline_gtco2e"] * (
        (1.0 - ag_rate) ** (years - 2024)
    )
    results["agriculture"] = agriculture

    # --- Other: follows average trend ---
    # Reduce at half the rate of the overall displacement
    avg_displacement = 1.0 - (electricity + road + industry) / (
        SECTORS["electricity"]["baseline_gtco2e"]
        + SECTORS["road_transport"]["baseline_gtco2e"]
        + SECTORS["industry"]["baseline_gtco2e"]
    )
    other = SECTORS["other"]["baseline_gtco2e"] * (1.0 - avg_displacement * 0.5)
    results["other"] = other

    return results


def emissions_to_temperature(years, total_emissions_gtco2e, tcre=TCRE):
    """
    Convert annual emissions trajectory to temperature trajectory using TCRE.

    Parameters
    ----------
    years : array
    total_emissions_gtco2e : array of annual GtCO2e
    tcre : float, °C per 1000 GtCO2

    Returns array of temperature anomaly (°C above pre-industrial)
    """
    # Convert CO2e to CO2 (roughly 75% of CO2e is actual CO2)
    annual_co2 = total_emissions_gtco2e * CO2_FRACTION_OF_CO2E

    # Cumulative CO2 from 2024 onward
    cumulative = np.cumsum(annual_co2)

    # Temperature from CO2 forcing
    delta_t_co2 = cumulative * tcre / 1000.0

    # Non-CO2 forcing (methane, N2O): adds ~0.5°C, slowly declining
    # as methane lifetime is short and clean energy reduces fugitive emissions
    non_co2 = 0.5 * np.array([
        max(0.1, 1.0 - 0.4 * (y - 2024) / 76) for y in years
    ])

    temperature = CURRENT_WARMING + delta_t_co2 + non_co2
    return temperature


def main():
    print("=" * 60)
    print("Computing temperature trajectory from S-curve adoption")
    print("=" * 60)

    # Load S-curve parameters
    params_path = PROCESSED_DIR / "scurve_params.json"
    if not params_path.exists():
        print("ERROR: scurve_params.json not found. Run scripts/fit_scurves.py first.")
        return

    with open(params_path) as f:
        scurve_params = json.load(f)

    years = np.arange(2024, 2101)

    scenarios = {}
    for scenario_name, rate_mult in [("fast", 1.3), ("central", 1.0), ("slow", 0.7)]:
        print(f"\n--- Scenario: {scenario_name} (rate x{rate_mult}) ---")

        sector_emissions = compute_sector_emissions(years, scurve_params, rate_mult)

        # Total emissions
        total = sum(sector_emissions.values())

        # Temperature
        temp = emissions_to_temperature(years, total)

        # Find peak
        peak_idx = np.argmax(temp)
        peak_temp = float(temp[peak_idx])
        peak_year = int(years[peak_idx])

        # Key milestones
        temp_2050 = float(temp[years == 2050][0]) if 2050 in years else None
        temp_2100 = float(temp[-1])
        emissions_2050 = float(total[years == 2050][0]) if 2050 in years else None

        # Net zero year (if reached)
        net_zero_idx = np.where(total <= 0)[0]
        net_zero_year = int(years[net_zero_idx[0]]) if len(net_zero_idx) > 0 else None

        print(f"  Peak: {peak_temp:.2f}°C in {peak_year}")
        print(f"  2050: {temp_2050:.2f}°C, {emissions_2050:.1f} GtCO2e/yr")
        print(f"  2100: {temp_2100:.2f}°C")
        if net_zero_year:
            print(f"  Net zero: ~{net_zero_year}")

        trajectory = []
        for i, y in enumerate(years):
            entry = {
                "year": int(y),
                "emissions_gtco2e": round(float(total[i]), 2),
                "temp_c": round(float(temp[i]), 3),
            }
            trajectory.append(entry)

        # Sector breakdown (every 5 years for compactness)
        sector_traj = {}
        for sector, emissions in sector_emissions.items():
            sector_traj[sector] = [
                {"year": int(y), "emissions_gtco2e": round(float(emissions[i]), 2)}
                for i, y in enumerate(years) if y % 5 == 0
            ]

        scenarios[f"scurve_{scenario_name}"] = {
            "peak_temp_c": round(peak_temp, 2),
            "peak_year": peak_year,
            "temp_2050": round(temp_2050, 2) if temp_2050 else None,
            "temp_2100": round(temp_2100, 2),
            "emissions_2050": round(emissions_2050, 1) if emissions_2050 else None,
            "net_zero_year": net_zero_year,
            "trajectory": trajectory,
            "sector_breakdown": sector_traj,
        }

    # Add current policies reference
    scenarios["current_policies"] = {
        "description": "UNEP 2024 Emissions Gap Report — assumes current implemented policies continue",
        "temp_2100": 3.1,
        "source": "UNEP Emissions Gap Report 2024",
    }

    output = {
        "methodology": "Bottom-up S-curve displacement model. Maps technology adoption curves "
                       "to sector-by-sector fossil fuel displacement, converts cumulative "
                       "emissions to temperature via TCRE (IPCC AR6). This is a simplified "
                       "thought experiment, not a full integrated assessment model.",
        "baseline_year": 2024,
        "baseline_emissions_gtco2e": TOTAL_BASELINE,
        "current_warming_c": CURRENT_WARMING,
        "tcre_c_per_1000gtco2": TCRE,
        "tcre_range": {"low": TCRE_LOW, "high": TCRE_HIGH},
        "assumptions": {
            "fleet_turnover_years": FLEET_TURNOVER_YEARS,
            "co2_fraction_of_co2e": CO2_FRACTION_OF_CO2E,
            "demand_growth": "1.5% declining to 0% over 50 years",
            "non_co2_forcing": "0.5°C baseline, declining 40% by 2100 as methane reduces",
            "aviation_demand_growth": "3% declining to 0% over 40 years",
            "saf_lifecycle_reduction": "80% per unit substituted",
            "agriculture_reduction_rate": "0.5% per year (slow, policy-dependent)",
        },
        "sector_baselines": {
            name: {
                "baseline_gtco2e": sec["baseline_gtco2e"],
                "share_of_total": sec["share_of_total"],
                "description": sec["description"],
            }
            for name, sec in SECTORS.items()
        },
        "scurve_parameters_used": {
            "electricity": "renewable_share_global from scurve_params.json",
            "road_transport": "ev_share_World from scurve_params.json (with 12yr fleet lag)",
            "aviation": "Assumed logistic K=80, r=0.20, t0=2042 (SAF adoption analogy)",
            "shipping": "Assumed logistic K=70, r=0.18, t0=2044 (alt fuel adoption)",
            "industry": "Assumed logistic K=60, r=0.07, t0=2048 (green H2 + EAF)",
            "buildings": "Assumed logistic K=80, r=0.15, t0=2035 (heat pumps)",
        },
        "scenarios": scenarios,
        "sources": [
            "IPCC AR6 WG1 Ch. 5 (TCRE)",
            "IPCC AR6 WG3 Ch. 2 (sector emissions)",
            "UNEP Emissions Gap Report 2024 (current policies)",
            "IEA World Energy Outlook 2025",
            "S-curve parameters fitted from OWID/IEA data",
        ],
    }

    output_path = PROCESSED_DIR / "temperature_trajectory.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"Wrote temperature trajectory to {output_path}")
    print(f"\nKey finding:")
    central = scenarios["scurve_central"]
    print(f"  S-curve central: peak {central['peak_temp_c']}°C in {central['peak_year']}")
    print(f"  vs. current policies: 3.1°C")
    print(f"  Difference: {3.1 - central['peak_temp_c']:.1f}°C less warming")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
