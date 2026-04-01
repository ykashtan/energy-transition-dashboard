"""
Canonical metric definitions for the Energy Transition Dashboard.

All other modules must import from here. Column names, display labels, tooltips,
and baselines are defined once and used everywhere. Do not hardcode any of these
values elsewhere — changes here propagate to all consumers.

Scientific reviewers: these definitions reflect IPCC AR6 conventions and
recommendations from PSE's environmental science review (2026-03-30).
"""

# ---------------------------------------------------------------------------
# Emissions: CO2 vs GHG vs CO2e
# ---------------------------------------------------------------------------
# GCB provides fossil CO2 only (~37 GtCO2/yr in 2023). EDGAR provides all
# GHGs as CO2e. These are VERY different numbers from different sources.
# Never use plain "CO2" or "emissions" without one of these qualifiers.

EMISSIONS_DEFINITIONS = {
    "co2_fossil_mt": {
        "label": "Fossil CO₂",
        "unit": "GtCO₂/yr",
        "source": "Global Carbon Budget",
        "note": "Fossil fuel combustion only. Does not include land-use change.",
    },
    "co2_land_mt": {
        "label": "Land-use CO₂",
        "unit": "GtCO₂/yr",
        "source": "Global Carbon Budget",
        "note": "CO₂ from deforestation and land-use change. High uncertainty for some countries.",
    },
    "co2_total_mt": {
        "label": "Total CO₂ (fossil + land use)",
        "unit": "GtCO₂/yr",
        "source": "Global Carbon Budget",
        "note": "Sum of fossil and land-use CO₂. CO₂ only — does not include CH₄, N₂O, or F-gases.",
    },
    "ghg_total_mtco2e": {
        "label": "Total GHG Emissions",
        "unit": "GtCO₂e/yr",
        "source": "EDGAR + PRIMAP-hist",
        "note": "All greenhouse gases (CO₂, CH₄, N₂O, F-gases) expressed as CO₂-equivalent using AR6 GWP100.",
    },
    "co2_consumption_mt": {
        "label": "Consumption-based CO₂",
        "unit": "GtCO₂/yr",
        "source": "Our World in Data (OWID)",
        "note": (
            "Emissions attributed to consumption rather than production. "
            "Wealthy importing nations appear higher than under territorial accounting."
        ),
    },
}

# ---------------------------------------------------------------------------
# Renewable share: denominator must always be explicit
# ---------------------------------------------------------------------------
# ~30% for electricity generation, ~13% for final energy — radically different.
# Never display "renewable share" without one of these labels.

RENEWABLE_SHARE_DEFINITIONS = {
    "renewable_share_electricity_pct": {
        "label": "Renewable share of electricity generation",
        "unit": "%",
        "denominator": "Total electricity generation",
        "note": "~30% globally (2023). Primary displayed metric on this dashboard.",
    },
    "renewable_share_final_energy_pct": {
        "label": "Renewable share of final energy consumption",
        "unit": "%",
        "denominator": "Total final energy consumption",
        "note": "~13% globally (2023). Includes electricity, heat, and transport.",
    },
}

# ---------------------------------------------------------------------------
# Temperature anomaly baseline
# ---------------------------------------------------------------------------
# IPCC AR6 standard is 1850-1900. NASA uses 1951-1980; NOAA uses 1901-2000.
# These differ by ~0.1-0.2°C — material at the 1.5°C threshold.

TEMPERATURE_BASELINE = "1850-1900"
TEMPERATURE_LABEL = f"Temperature anomaly vs {TEMPERATURE_BASELINE} baseline (IPCC AR6)"
TEMPERATURE_NOTE = (
    f"Pre-industrial baseline: {TEMPERATURE_BASELINE} (IPCC AR6 standard). "
    "NASA uses 1951-1980; NOAA uses 1901-2000. Values differ by ~0.1-0.2°C."
)

# ---------------------------------------------------------------------------
# IPCC scenario labels
# ---------------------------------------------------------------------------
# C1 scenarios limit warming to 1.5°C with >50% probability by 2100, OFTEN
# via overshoot followed by drawdown using negative emissions. They are NOT
# "scenarios where we stay below 1.5°C". Label and tooltip required everywhere.

SCENARIO_LABELS = {
    "C1": "1.5°C-compatible range (C1)",
    "C3": "2°C-compatible range (C3)",
    "C5": "2.5°C-compatible range (C5)",
}

SCENARIO_TOOLTIPS = {
    "C1": (
        "C1 scenarios limit warming to 1.5°C with >50% probability by 2100. "
        "Most involve temperature overshoot before returning to 1.5°C via "
        "large-scale carbon dioxide removal (CDR). "
        "All C1 scenarios require ~8-10 GtCO₂/yr of CDR by 2050; "
        "current CDR is ~2 GtCO₂/yr."
    ),
    "C3": (
        "C3 scenarios limit warming to 2°C with >67% probability by 2100."
    ),
    "C5": (
        "C5 scenarios limit warming to 2.5°C with >50% probability by 2100."
    ),
}

# CDR callout — appears alongside every 1.5°C scenario presentation
CDR_CALLOUT = (
    "⚠️ CDR gap: All 1.5°C-compatible scenarios require ~8-10 GtCO₂/yr of "
    "carbon dioxide removal by 2050. Current CDR is ~2 GtCO₂/yr."
)

# ---------------------------------------------------------------------------
# Health mortality categories
# ---------------------------------------------------------------------------
# CRITICAL: These two categories must never be summed when contextualizing
# energy transition impacts. Ambient PM2.5 is reducible by decarbonizing
# electricity; household air pollution requires clean cooking access programs.

HEALTH_MORTALITY_DEFINITIONS = {
    "deaths_ambient_pm25": {
        "label": "Deaths from ambient (outdoor) PM2.5",
        "unit": "millions/yr",
        "source": "GBD/IHME",
        "policy_lever": "Electricity decarbonization, industrial emissions",
        "note": "Directly reducible by decarbonizing electricity and industry.",
    },
    "deaths_household_air": {
        "label": "Deaths from household air pollution",
        "unit": "millions/yr",
        "source": "GBD/IHME",
        "policy_lever": "Clean cooking access programs",
        "note": (
            "Caused by solid-fuel cooking in South Asia and Sub-Saharan Africa. "
            "NOT directly addressed by electricity-sector energy transition. "
            "Requires clean cooking access programs."
        ),
    },
}

# Label for combined display only (context must be explicit when used)
HEALTH_COMBINED_LABEL = "Total air pollution mortality (ambient PM2.5 + household, all sources)"

# ---------------------------------------------------------------------------
# Deaths per TWh: comparative only, not precision mortality
# ---------------------------------------------------------------------------

DEATHS_PER_TWH_TOOLTIP = (
    "Deaths per TWh derived from lifecycle analysis studies with heterogeneous "
    "methodologies (Sovacool 2008, Markandya & Wilkinson 2007, updated GBD). "
    "Coal estimates dominated by older Chinese plants; modern gas rates lower. "
    "Nuclear numbers contested across studies by orders of magnitude. "
    "Intended as comparative orders of magnitude only — not precision mortality rates. "
    "See OWID methodology page for details."
)

DEATHS_PER_TWH_FRAMING = (
    "Coal causes roughly 1000× more deaths per unit of energy than wind or solar."
)

# ---------------------------------------------------------------------------
# Carbon budget
# ---------------------------------------------------------------------------
# Defined in CO2-only terms (not CO2e). Source: GCB annual update. Always cite year.

CARBON_BUDGET_NOTE = (
    "Remaining carbon budget is defined in CO₂-only terms (not CO₂e). "
    "Source: Global Carbon Budget (cite year of estimate). "
    "Budget is revised with each annual GCB update."
)

# ---------------------------------------------------------------------------
# Avoided deaths methodology
# ---------------------------------------------------------------------------
# Do NOT calculate as (deaths/TWh for coal) × (renewable TWh added).
# This ignores displacement mix, additive demand, and curtailment.

AVOIDED_DEATHS_METHODOLOGY = """
Avoided deaths methodology:
- US estimates: use EPA COBRA/AVERT pipeline (PSE toolkit). Most defensible.
- Non-US estimates: present "current health burden of fossil electricity"
  rather than speculative avoided-deaths. Equally compelling, more defensible.
- NEVER calculate as: (deaths/TWh for coal) × (renewable TWh added).
  This overestimates substantially.
- PSE health team review required before publishing any avoided-deaths figures.
"""

# ---------------------------------------------------------------------------
# Emissions data quality tiers
# ---------------------------------------------------------------------------

DATA_QUALITY_TIERS = {
    "annex_i": {
        "label": "Annex I",
        "note": "Mandatory MRV reporting. High confidence.",
    },
    "non_annex_i": {
        "label": "Non-Annex I",
        "note": (
            "Voluntary reporting. Larger uncertainties. "
            "China coal emissions have been substantially revised. "
            "Brazil/Indonesia LULUCF estimates vary ~2× across datasets."
        ),
    },
}

# ---------------------------------------------------------------------------
# Methane GWP
# ---------------------------------------------------------------------------

METHANE_GWP20 = 80   # CO2-equivalent over 20 years (AR6)
METHANE_GWP100 = 27.9  # CO2-equivalent over 100 years (AR6 GWP100; fossil CH4 = 29.8 incl. CO2 from oxidation)
METHANE_NOTE = (
    "Methane's GWP is ~80× CO₂ over 20 years — its short-term climate forcing "
    "is disproportionate. Methane is also a tropospheric ozone precursor, "
    "linking oil/gas/coal sector emissions to respiratory mortality."
)
