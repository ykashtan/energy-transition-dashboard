"""
process_ndgain.py — Process ND-GAIN Country Index data for climate vulnerability mapping.

The ND-GAIN index combines vulnerability (exposure, sensitivity, adaptive capacity)
with readiness (economic, governance, social) to show which countries are most at
risk from climate change and least prepared to adapt.

This supports the environmental justice angle: the most vulnerable countries are
often the least responsible for emissions.

Source: Notre Dame Global Adaptation Initiative (ND-GAIN)
  https://gain.nd.edu/our-work/country-index/

Output: data/processed/vulnerability.parquet

Schema:
  iso3              : str   — ISO 3166-1 alpha-3 country code
  year              : int   — year (1995–2023)
  gain_score        : float — ND-GAIN overall score (0–100, higher = less vulnerable)
  vulnerability     : float — vulnerability score (0–1, higher = more vulnerable)
  readiness         : float — readiness score (0–1, higher = more ready)
  exposure          : float — exposure sub-score
  sensitivity       : float — sensitivity sub-score
  adaptive_capacity : float — adaptive capacity sub-score
"""

from pathlib import Path
import zipfile
import pandas as pd
import numpy as np

RAW_PATH = Path(__file__).parent.parent / "data" / "raw" / "ndgain_countryindex_2026.zip"
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "processed" / "vulnerability.parquet"


def _read_wide_csv(zf: zipfile.ZipFile, inner_path: str) -> pd.DataFrame:
    """Read a wide-format ND-GAIN CSV (ISO3, Name, year columns) from zip."""
    with zf.open(inner_path) as f:
        df = pd.read_csv(f)
    # Melt from wide to long: year columns are the numeric ones
    id_cols = [c for c in df.columns if not c.isdigit()]
    year_cols = [c for c in df.columns if c.isdigit()]
    melted = df.melt(id_vars=id_cols, value_vars=year_cols,
                     var_name="year", value_name="value")
    melted["year"] = melted["year"].astype(int)
    return melted


def process_ndgain() -> pd.DataFrame:
    """Process ND-GAIN zip into dashboard-ready vulnerability data."""

    with zipfile.ZipFile(RAW_PATH) as zf:
        # List available files
        names = zf.namelist()

        # Read the key indices
        indices = {}
        file_map = {
            "gain_score": "resources/gain/gain.csv",
            "vulnerability": "resources/vulnerability/vulnerability.csv",
            "readiness": "resources/readiness/readiness.csv",
            "exposure": "resources/vulnerability/exposure.csv",
            "sensitivity": "resources/vulnerability/sensitivity.csv",
            "adaptive_capacity": "resources/vulnerability/capacity.csv",
        }

        for key, path in file_map.items():
            if path in names:
                df = _read_wide_csv(zf, path)
                # Rename columns
                iso_col = [c for c in df.columns if c.upper() in ("ISO3", "ISO")]
                name_col = [c for c in df.columns if c.lower() == "name"]

                if iso_col:
                    df = df.rename(columns={iso_col[0]: "iso3"})
                if name_col:
                    df = df.rename(columns={name_col[0]: "country_name"})

                indices[key] = df[["iso3", "year", "value"]].rename(
                    columns={"value": key}
                )

    # Merge all indices on iso3 + year
    result = None
    for key, df in indices.items():
        if result is None:
            result = df
        else:
            result = result.merge(df, on=["iso3", "year"], how="outer")

    if result is None:
        return pd.DataFrame()

    # Drop rows where all scores are missing
    score_cols = list(file_map.keys())
    result = result.dropna(subset=score_cols, how="all")

    # Sort
    result = result.sort_values(["iso3", "year"]).reset_index(drop=True)

    return result


if __name__ == "__main__":
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df = process_ndgain()
    df.to_parquet(OUTPUT_PATH, index=False)
    print(f"[process_ndgain] Wrote {len(df)} rows → {OUTPUT_PATH}")
    print(f"  Countries: {df['iso3'].nunique()}")
    print(f"  Years: {df['year'].min()}–{df['year'].max()}")

    # Latest year stats
    latest = df[df["year"] == df["year"].max()]
    for col in ["gain_score", "vulnerability", "readiness"]:
        if col in latest.columns:
            vals = latest[col].dropna()
            print(f"  {col} ({len(vals)} countries): "
                  f"mean={vals.mean():.2f}, min={vals.min():.2f}, max={vals.max():.2f}")
