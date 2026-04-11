"""
fit_scurves.py -- Fit logistic S-curves to historical adoption data and output parameters.

Reads ev_sales_share.parquet and energy_mix.parquet, fits the logistic function
    S(t) = K / (1 + exp(-r * (t - t0)))
to each key time series, and writes fitted parameters to data/processed/scurve_params.json.

Usage:
    python scripts/fit_scurves.py
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

PROJECT_ROOT = Path(__file__).parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


# ---------------------------------------------------------------------------
# Logistic (S-curve) function
# ---------------------------------------------------------------------------

def logistic(t, K, r, t0):
    """Standard logistic function: S(t) = K / (1 + exp(-r * (t - t0)))"""
    return K / (1.0 + np.exp(-r * (t - t0)))


def fit_logistic(years, values, label="", K_min=None):
    """
    Fit a logistic curve to the given (years, values) data.

    Parameters
    ----------
    K_min : float, optional
        Minimum saturation level. For technologies still in early growth
        (e.g., EVs at 20% globally), the optimizer will find a low K that
        fits historical data well but produces unrealistic projections.
        Set K_min to enforce a higher floor (e.g., 80 for EVs, 50 for solar).

    Returns a dict with K, r, t0, r_squared, n_points, year_start, year_end,
    or None if the fit fails.
    """
    years = np.asarray(years, dtype=float)
    values = np.asarray(values, dtype=float)

    # Filter out NaN / zero-only
    mask = np.isfinite(values) & (values > 0)
    years = years[mask]
    values = values[mask]

    if len(years) < 4:
        print(f"  [SKIP] {label}: only {len(years)} valid points (need >= 4)")
        return None

    # Bounds: K in [K_lower, 100], r in [0.01, 3.0], t0 in [year_range]
    K_upper = 100.0  # percentages capped at 100
    K_lower = max(values) * 0.8
    if K_min is not None:
        K_lower = max(K_lower, K_min)
    if K_lower > K_upper:
        K_upper = K_lower * 1.5

    # Initial guesses (clamped within bounds)
    K_guess = min(max(K_lower * 1.1, max(values) * 1.5), K_upper * 0.95)
    K_guess = max(K_guess, K_lower * 1.05)
    if K_guess < 1.0:
        K_guess = 50.0  # for very small shares
    r_guess = 0.3
    t0_guess = years[len(years) // 2]  # midpoint year

    bounds_lower = [K_lower, 0.01, years.min() - 10]
    bounds_upper = [K_upper, 3.0, years.max() + 30]

    try:
        popt, pcov = curve_fit(
            logistic, years, values,
            p0=[K_guess, r_guess, t0_guess],
            bounds=(bounds_lower, bounds_upper),
            maxfev=10000,
        )
    except (RuntimeError, ValueError) as e:
        print(f"  [FAIL] {label}: curve_fit failed — {e}")
        return None

    K_fit, r_fit, t0_fit = popt

    # Compute R-squared
    predicted = logistic(years, *popt)
    ss_res = np.sum((values - predicted) ** 2)
    ss_tot = np.sum((values - np.mean(values)) ** 2)
    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    result = {
        "K": round(float(K_fit), 2),
        "r": round(float(r_fit), 4),
        "t0": round(float(t0_fit), 1),
        "r_squared": round(float(r_squared), 4),
        "n_points": int(len(years)),
        "year_start": int(years.min()),
        "year_end": int(years.max()),
    }
    print(f"  [OK]   {label}: K={result['K']}, r={result['r']}, t0={result['t0']}, R²={result['r_squared']}")
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Fitting S-curves to adoption data")
    print("=" * 60)

    results = {}

    # ----- EV sales share by region -----
    ev_path = PROCESSED_DIR / "ev_sales_share.parquet"
    if not ev_path.exists():
        print(f"ERROR: {ev_path} not found. Run scripts/process_electrification.py first.")
        sys.exit(1)

    ev_df = pd.read_parquet(ev_path)
    print(f"\nLoaded ev_sales_share.parquet: {len(ev_df)} rows")

    # Regions to fit
    ev_regions = ["Norway", "China", "World", "USA", "India", "Viet Nam",
                  "Germany", "Sweden", "France", "United Kingdom"]

    # K_min per region: mature markets (Norway) can self-calibrate;
    # early-growth markets need a floor so the curve doesn't plateau at 20%.
    ev_K_min = {
        "Norway": None,    # already at ~90%, let it find its own K
        "Sweden": 70,      # at ~58%, heading higher
        "China": 80,       # at ~48%, strong momentum
        "World": 80,       # at ~22%, definitely going higher
        "USA": 80,         # at ~10%, early growth
        "India": 80,       # at ~2%, very early but massive market
        "Viet Nam": 80,    # at ~17%, rapid growth with VinFast
        "Germany": 70,     # at ~25%, subsidy-cut dip is temporary
        "France": 70,      # at ~25%, EU mandate drives higher
        "United Kingdom": 70,  # at ~27%, ZEV mandate to 2035
    }

    print("\n--- EV sales share S-curves ---")
    for region in ev_regions:
        sub = ev_df[ev_df["region"] == region].sort_values("year")
        if sub.empty:
            print(f"  [SKIP] {region}: no data")
            continue

        # Use a safe key name (no spaces)
        key = f"ev_share_{region.replace(' ', '_')}"
        result = fit_logistic(
            sub["year"].values, sub["ev_share_pct"].values,
            label=key, K_min=ev_K_min.get(region),
        )
        if result is not None:
            results[key] = result

    # ----- Global solar, wind, renewable share -----
    mix_path = PROCESSED_DIR / "energy_mix.parquet"
    if not mix_path.exists():
        print(f"\nWARNING: {mix_path} not found. Skipping energy mix S-curves.")
    else:
        mix_df = pd.read_parquet(mix_path)
        print(f"\nLoaded energy_mix.parquet: {len(mix_df)} rows")

        # Compute global aggregates (sum across all countries per year)
        # Exclude years with suspiciously incomplete data (e.g. 2025 partial)
        global_agg = mix_df.groupby("year").agg({
            "electricity_twh_solar": "sum",
            "electricity_twh_wind": "sum",
            "total_electricity_twh": "sum",
        }).reset_index()

        # Also sum all renewable sources for renewable share
        ren_cols = [
            "electricity_twh_solar", "electricity_twh_wind",
            "electricity_twh_hydro", "electricity_twh_biomass",
            "electricity_twh_other_renewable",
        ]
        # Some columns may not exist; use those that do
        available_ren = [c for c in ren_cols if c in mix_df.columns]
        global_agg["total_renewable_twh"] = mix_df.groupby("year")[available_ren].sum().sum(axis=1).values

        # Compute shares
        global_agg["solar_share_pct"] = (
            global_agg["electricity_twh_solar"] / global_agg["total_electricity_twh"] * 100
        )
        global_agg["wind_share_pct"] = (
            global_agg["electricity_twh_wind"] / global_agg["total_electricity_twh"] * 100
        )
        global_agg["renewable_share_pct"] = (
            global_agg["total_renewable_twh"] / global_agg["total_electricity_twh"] * 100
        )

        # Filter to reasonable years (exclude 2025 if data looks incomplete)
        # Check: if 2025 total is < 50% of 2024 total, drop it
        if 2025 in global_agg["year"].values and 2024 in global_agg["year"].values:
            total_2024 = global_agg.loc[global_agg["year"] == 2024, "total_electricity_twh"].iloc[0]
            total_2025 = global_agg.loc[global_agg["year"] == 2025, "total_electricity_twh"].iloc[0]
            if total_2025 < total_2024 * 0.5:
                print("  Dropping 2025 energy_mix data (appears incomplete)")
                global_agg = global_agg[global_agg["year"] <= 2024]

        # Fit solar share (use data from 2000 onward where solar is measurable)
        print("\n--- Energy mix S-curves (global) ---")

        # Solar, wind, renewable share: use RESEARCHED K_min values.
        #
        # Historical-only fits produce unrealistically low K because these
        # technologies are still in early exponential growth. K_min values
        # are set based on the convergence of major energy forecasts:
        #
        # SOLAR K_min=40%:
        #   IEA NZE 2050: 43%, DNV best-estimate 2050: 40%, BNEF base: 22% (floor)
        #   Solar cost advantage is accelerating; storage makes it dispatchable.
        #
        # WIND K_min=30%:
        #   IEA NZE 2050: 31%, DNV best-estimate 2050: 29%, IRENA 1.5C: 35%
        #   Wind growth (~8%/yr) is slower than solar (~29%/yr); siting constraints.
        #
        # RENEWABLE K_min=80%:
        #   IEA NZE 2050: ~90%, DNV 2050: 69%+. Hydro/nuclear/other fill remainder.
        #
        # Sources: IEA WEO 2025, DNV ETO 2025, IRENA WETO 2024, BNEF NEO 2025

        solar_data = global_agg[global_agg["year"] >= 2000].copy()
        result = fit_logistic(
            solar_data["year"].values,
            solar_data["solar_share_pct"].values,
            label="solar_share_global",
            K_min=40,
        )
        if result is not None:
            results["solar_share_global"] = result

        wind_data = global_agg[global_agg["year"] >= 2000].copy()
        result = fit_logistic(
            wind_data["year"].values,
            wind_data["wind_share_pct"].values,
            label="wind_share_global",
            K_min=30,
        )
        if result is not None:
            results["wind_share_global"] = result

        ren_data = global_agg[global_agg["year"] >= 2000].copy()
        result = fit_logistic(
            ren_data["year"].values,
            ren_data["renewable_share_pct"].values,
            label="renewable_share_global",
            K_min=80,
        )
        if result is not None:
            results["renewable_share_global"] = result

    # ----- Electric truck share (computed from ev_sales / total truck sales) -----
    ev_sales_path = PROCESSED_DIR / "ev_sales.parquet"
    if ev_sales_path.exists():
        ev_sales_df = pd.read_parquet(ev_sales_path)
        trucks = ev_sales_df[
            (ev_sales_df["mode"] == "Trucks") & (ev_sales_df["region"] == "World")
        ].sort_values("year")
        if not trucks.empty:
            # Global truck sales ~3.5M/yr (OICA); compute share
            GLOBAL_TRUCK_SALES = 3_500_000
            trucks = trucks.copy()
            trucks["share_pct"] = trucks["ev_sales"] / GLOBAL_TRUCK_SALES * 100
            print("\n--- Electric truck share S-curve ---")
            result = fit_logistic(
                trucks["year"].values, trucks["share_pct"].values,
                label="electric_trucks_global", K_min=80,
            )
            if result is not None:
                results["electric_trucks_global"] = result

    # ----- Heat pumps global share (synthetic from known data points) -----
    # Sources: IEA Heat Pumps Report, EHPA
    # Known: ~3% in 2015, ~5% in 2019, ~10% in 2024 (global heating equipment sales)
    print("\n--- Synthetic S-curves (heat pumps, induction cooking) ---")
    hp_years = np.array([2010, 2012, 2015, 2017, 2019, 2020, 2021, 2022, 2023, 2024])
    hp_share = np.array([1.5,  2.0,  3.0,  4.0,  5.0,  6.0,  7.5,  8.5,  9.0,  10.0])
    result = fit_logistic(hp_years, hp_share, label="heat_pumps_global", K_min=60)
    if result is not None:
        results["heat_pumps_global"] = result
        results["heat_pumps_global"]["synthetic"] = True
        results["heat_pumps_global"]["source"] = "IEA Heat Pump Market Report 2025, EHPA"

    # ----- Induction cooking global share (synthetic) -----
    # Known: ~1% in 2015, ~3% in 2020, ~5% in 2024 (global cooking appliance sales)
    # Already dominant in parts of Asia (China, Japan, Korea)
    ic_years = np.array([2010, 2013, 2015, 2017, 2019, 2020, 2021, 2022, 2023, 2024])
    ic_share = np.array([0.5,  0.8,  1.0,  1.5,  2.5,  3.0,  3.5,  4.0,  4.5,  5.0])
    result = fit_logistic(ic_years, ic_share, label="induction_cooking_global", K_min=50)
    if result is not None:
        results["induction_cooking_global"] = result
        results["induction_cooking_global"]["synthetic"] = True
        results["induction_cooking_global"]["source"] = "IEA Energy Efficiency 2025 (estimated)"

    # ----- Write results -----
    output_path = PROCESSED_DIR / "scurve_params.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"Wrote {len(results)} S-curve fits to {output_path}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
