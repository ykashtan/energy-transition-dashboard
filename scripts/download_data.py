"""
download_data.py — Downloads all Tier 1 raw data files for the Energy Transition Dashboard.

Run this script to populate data/raw/ before running any process_*.py scripts.
All downloads are idempotent: files already present are skipped unless --force is passed.

Usage:
    python scripts/download_data.py
    python scripts/download_data.py --force   # re-download everything

Sources downloaded here:
  - OWID energy data (energy consumption, electricity mix, capacity)
  - OWID CO2 data (fossil CO2, all GHGs, consumption-based, cumulative)
  - Ember Yearly Electricity Data (generation by source, 215 countries)
  - Global Carbon Budget (fossil CO2, land-use CO2, carbon budget)
  - NOAA global mean CO2 (atmospheric CO2 concentration — global mean, not Mauna Loa alone)
  - EDGAR GHG emissions (country-level GHG by sector, IPCC AR6 reference dataset)

Sources NOT automated here (require manual steps — see comments):
  - IRENA IRENASTAT: PxWeb API, complex query; OWID energy already includes IRENA capacity
  - IEA data: free account required; download links noted in comments
  - PRIMAP-hist: Zenodo DOI noted; version pinned
  - GBD/IHME: free account required; download from ihmeresults tool
  - IEA Global Methane Tracker: noted in comments
"""

import argparse
import sys
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# Resolve paths relative to project root, regardless of where script is run from
PROJECT_ROOT = Path(__file__).parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Download sources
# ---------------------------------------------------------------------------

SOURCES = {
    # OWID energy data: ~129 variables, energy consumption + electricity mix + capacity
    "owid_energy.csv": {
        "url": "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv",
        "description": "OWID energy data (~129 vars, all countries, all years)",
    },
    # OWID CO2 data: fossil CO2, all GHGs, consumption-based, cumulative, per-capita
    "owid_co2.csv": {
        "url": "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv",
        "description": "OWID CO2 + GHG data (fossil CO2, GHGs, consumption-based, per-capita)",
    },
    # Ember Yearly Electricity Data: generation by source, 215 countries, CC-BY-4.0
    "ember_yearly_electricity.csv": {
        "url": "https://ember-energy.org/app/uploads/2024/05/yearly_full_release_long_format.csv",
        "description": "Ember yearly electricity data (generation by source, 215 countries)",
    },
    # NOAA global mean atmospheric CO2 (global mean surface product, not Mauna Loa alone)
    # Using the globally averaged marine surface annual mean
    "noaa_co2_global_mean.csv": {
        "url": "https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_annmean_gl.txt",
        "description": "NOAA global mean atmospheric CO2 (globally averaged, annual mean)",
    },
    # OWID deaths per TWh (coal vs renewables comparison, orders of magnitude)
    # Source: Our World in Data safety-by-energy-source dataset
    "owid_deaths_per_twh.csv": {
        "url": "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv",
        "description": "Deaths per TWh embedded in OWID energy data (use owid_energy.csv as source)",
        "note": "deaths_per_twh columns are in owid_energy.csv; this entry is a reminder only.",
    },
}

# ---------------------------------------------------------------------------
# Sources requiring manual download (instructions printed to stdout)
# ---------------------------------------------------------------------------

MANUAL_SOURCES = {
    "gcb_2024.xlsx": {
        "description": "Global Carbon Budget 2024 (fossil CO2, land-use CO2, carbon budget)",
        "url": "https://www.globalcarbonbudget.org/data/",
        "instructions": (
            "Visit https://www.globalcarbonbudget.org/data/ → "
            "download 'Global Carbon Budget 2024' Excel file → "
            "save as data/raw/gcb_2024.xlsx"
        ),
    },
    "edgar_ghg_2023.csv": {
        "description": "EDGAR GHG emissions v8 (all GHGs, all countries, 1970-2022)",
        "url": "https://edgar.jrc.ec.europa.eu/dataset_ghg80",
        "instructions": (
            "Visit https://edgar.jrc.ec.europa.eu/dataset_ghg80 → "
            "download the 'EDGAR_2024_GHG_booklet_2024.xlsx' or country totals CSV → "
            "save as data/raw/edgar_ghg_2023.csv (or .xlsx)"
        ),
    },
    "primap_hist.csv": {
        "description": "PRIMAP-hist v2.5 (non-CO2 GHGs for non-Annex I countries)",
        "url": "https://zenodo.org/doi/10.5281/zenodo.3638137",
        "instructions": (
            "Visit https://zenodo.org/doi/10.5281/zenodo.3638137 → "
            "download the latest PRIMAP-hist CSV → "
            "save as data/raw/primap_hist.csv"
        ),
    },
    "iea_methane_tracker.csv": {
        "description": "IEA Global Methane Tracker (country-level oil/gas/coal methane)",
        "url": "https://www.iea.org/data-and-statistics/data-product/methane-tracker-database",
        "instructions": (
            "Visit IEA Global Methane Tracker → "
            "download country-level data CSV → "
            "save as data/raw/iea_methane_tracker.csv"
        ),
    },
    "irena_capacity.csv": {
        "description": "IRENA renewable capacity by technology (2000-present)",
        "url": "https://pxweb.irena.org/pxweb/en/IRENASTAT/",
        "instructions": (
            "OWID energy data includes IRENA capacity — use owid_energy.csv as fallback. "
            "For direct IRENA data: https://pxweb.irena.org/pxweb/en/IRENASTAT/ → "
            "Capacity and Generation → Renewable capacity → download CSV → "
            "save as data/raw/irena_capacity.csv"
        ),
    },
}


# ---------------------------------------------------------------------------
# Download helper
# ---------------------------------------------------------------------------

def download_file(url: str, dest: Path, description: str, force: bool = False) -> bool:
    """Download a file from url to dest. Returns True if downloaded, False if skipped."""
    if dest.exists() and not force:
        print(f"  [SKIP] {dest.name} already exists (use --force to re-download)")
        return False

    print(f"  [DOWNLOAD] {dest.name} ...")
    print(f"             {description}")

    try:
        response = requests.get(url, timeout=120, stream=True)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"  [ERROR] HTTP {e.response.status_code} for {url}")
        print(f"          {e}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"  [ERROR] Connection error for {url}: {e}")
        return False
    except requests.exceptions.Timeout:
        print(f"  [ERROR] Timeout downloading {url}")
        return False

    with open(dest, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    size_kb = dest.stat().st_size / 1024
    print(f"  [OK]     {dest.name} ({size_kb:.0f} KB)")
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Download raw data files for the Energy Transition Dashboard."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download files even if they already exist.",
    )
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print("Energy Transition Dashboard — Data Downloader")
    print(f"Saving to: {RAW_DIR}")
    print(f"{'='*60}\n")

    # --- Automated downloads ---
    print("AUTOMATED DOWNLOADS:")
    print("-" * 40)
    success_count = 0
    fail_count = 0

    for filename, info in SOURCES.items():
        dest = RAW_DIR / filename
        ok = download_file(
            url=info["url"],
            dest=dest,
            description=info["description"],
            force=args.force,
        )
        if ok is False and not dest.exists():
            fail_count += 1
        else:
            success_count += 1

    # --- Manual download instructions ---
    print(f"\nMANUAL DOWNLOADS REQUIRED:")
    print("-" * 40)
    print("The following sources require manual download steps:")
    for filename, info in MANUAL_SOURCES.items():
        dest = RAW_DIR / filename
        status = "[PRESENT]" if dest.exists() else "[MISSING]"
        print(f"\n  {status} {filename}")
        print(f"  {info['description']}")
        print(f"  Instructions: {info['instructions']}")

    # --- Summary ---
    print(f"\n{'='*60}")
    missing_manual = [
        f for f in MANUAL_SOURCES if not (RAW_DIR / f).exists()
    ]
    if missing_manual:
        print(f"⚠️  {len(missing_manual)} manual downloads still needed:")
        for f in missing_manual:
            print(f"   - {f}")
        print("   process_core.py will skip these and note gaps in output.")
    else:
        print("✓ All manual downloads present.")
    print(f"{'='*60}\n")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
