"""
tipping_points.py — Tipping Points page.

Tracks clean energy tipping points: a curated checklist of whether key thresholds
have been crossed, an S-curve momentum tracker, countdown to milestones, and a
composite optimism meter. Based on research from RMI, RethinkX, Lenton et al.
(Exeter), and the broader tipping-points literature.

Expanded in April 2025 to cover ~28 tipping points across 11 sectors, with
emissions-weighted optimism scoring and accordion-based sector grouping.
"""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from collections import OrderedDict

from utils.data_loader import get_kpis, get_investment, get_energy_mix, get_capacity
from utils.chart_styles import (
    GREEN, YELLOW, RED, BLUE, GRAY, PRIMARY,
    GRAPH_CONFIG, CHART_FONT, PAPER_BG, PLOT_BG,
)

dash.register_page(
    __name__,
    path="/tipping-points",
    title="Tipping Points — Energy Transition Dashboard",
)


# ---------------------------------------------------------------------------
# Color palette additions
# ---------------------------------------------------------------------------
LIGHT_BG = "#f8f9fa"  # Card backgrounds


# ---------------------------------------------------------------------------
# Sector definitions with display names and emissions weights
# ---------------------------------------------------------------------------
# climate_weight = approximate share of global GHG emissions that the sector
# represents, used to weight tipping points in the optimism score.

SECTOR_META = OrderedDict([
    ("electricity", {
        "name": "Electricity & Heat",
        "icon": "bi-lightning-charge-fill",
        "climate_weight": 0.25,
    }),
    ("transport_road", {
        "name": "Transport \u2014 Road",
        "icon": "bi-car-front-fill",
        "climate_weight": 0.10,
    }),
    ("transport_aviation", {
        "name": "Transport \u2014 Aviation",
        "icon": "bi-airplane-fill",
        "climate_weight": 0.03,
    }),
    ("transport_shipping", {
        "name": "Transport \u2014 Shipping",
        "icon": "bi-ship",
        "climate_weight": 0.03,
    }),
    ("buildings", {
        "name": "Buildings",
        "icon": "bi-house-door-fill",
        "climate_weight": 0.06,
    }),
    ("industry", {
        "name": "Industry",
        "icon": "bi-gear-fill",
        "climate_weight": 0.21,
    }),
    ("grid_storage", {
        "name": "Grid & Storage",
        "icon": "bi-battery-charging",
        "climate_weight": 0.04,
    }),
    ("nuclear", {
        "name": "Nuclear",
        "icon": "bi-radioactive",
        "climate_weight": 0.03,
    }),
    ("carbon_removal", {
        "name": "Carbon Removal",
        "icon": "bi-cloud-minus-fill",
        "climate_weight": 0.05,
    }),
    ("supply_chains", {
        "name": "Supply Chains",
        "icon": "bi-link-45deg",
        "climate_weight": 0.05,
    }),
    ("fossil_fuels", {
        "name": "Fossil Fuels",
        "icon": "bi-fuel-pump-fill",
        "climate_weight": 0.15,
    }),
])


# ---------------------------------------------------------------------------
# Section 1: Tipping Points Checklist (~28 items across 11 sectors)
# ---------------------------------------------------------------------------
# Status values: "crossed", "approaching", "contested", "not_yet"

CHECKLIST_ITEMS = [
    # ---- ELECTRICITY (7 items) ----
    {
        "label": "Solar LCOE below new coal globally",
        "status": "crossed",
        "year": "2020\u20132023",
        "sector": "electricity",
        "climate_weight": 0.25,
        "detail": (
            "Utility-scale solar LCOE fell to $0.043/kWh (2024), 87% below 2010. "
            "91% of new renewable projects are cheaper than fossil alternatives."
        ),
        "sources": "IRENA Renewable Power Generation Costs 2024; Way et al. 2022 (Joule)",
    },
    {
        "label": "Clean energy investment > fossil fuel investment",
        "status": "crossed",
        "year": "2023",
        "sector": "electricity",
        "climate_weight": 0.25,
        "detail": (
            "Clean energy investment reached $2.15T in 2025 vs ~$1.1T for fossil "
            "fuels \u2014 nearly a 2:1 ratio. Renewables-to-fossil electricity "
            "investment ratio is ~10:1."
        ),
        "sources": "IEA World Energy Investment 2025; BloombergNEF",
    },
    {
        "label": "Renewables >50% of new power capacity globally",
        "status": "crossed",
        "year": "2015+",
        "sector": "electricity",
        "climate_weight": 0.25,
        "detail": (
            "Solar alone represented 70% of all new generating capacity worldwide "
            "in 2024. Renewables have dominated new capacity for over a decade."
        ),
        "sources": "IRENA 2025; Ember Global Electricity Review 2025",
    },
    {
        "label": "1 TW of solar installed globally",
        "status": "crossed",
        "year": "2023",
        "sector": "electricity",
        "climate_weight": 0.25,
        "detail": (
            "Global solar capacity reached 1,865 GW by end 2024. "
            "First TW took ~15 years; next TW is expected in ~4 years."
        ),
        "sources": "IRENA Renewable Energy Statistics 2025",
    },
    {
        "label": "Renewables overtake coal in global generation",
        "status": "crossed",
        "year": "H1 2025",
        "sector": "electricity",
        "climate_weight": 0.25,
        "detail": (
            "Ember's Global Electricity Review shows renewables surpassing coal "
            "as a share of global electricity generation for the first time in "
            "H1 2025, driven primarily by solar and wind additions."
        ),
        "sources": "Ember Global Electricity Review 2025",
    },
    {
        "label": "Solar + wind >15% of global electricity",
        "status": "crossed",
        "year": "2024",
        "sector": "electricity",
        "climate_weight": 0.25,
        "detail": (
            "Combined solar and wind generation reached ~16% of global "
            "electricity in 2024, up from ~12% in 2022. Variable renewables "
            "at >15% begin requiring grid flexibility investments."
        ),
        "sources": "Ember Global Electricity Review 2025",
    },
    {
        "label": "Second TW of solar capacity",
        "status": "approaching",
        "year": "~2026",
        "sector": "electricity",
        "climate_weight": 0.25,
        "detail": (
            "Current capacity: 1,865 GW. With annual additions >400 GW, the "
            "second TW milestone is expected around mid-2026, demonstrating "
            "continued exponential scaling."
        ),
        "sources": "IRENA 2025; BloombergNEF Solar Outlook",
    },

    # ---- TRANSPORT -- ROAD (5 items) ----
    {
        "label": "EVs past 5% of new car sales globally",
        "status": "crossed",
        "year": "2021",
        "sector": "transport_road",
        "climate_weight": 0.10,
        "detail": (
            "Global EV share reached ~22% in 2024 (17M vehicles sold). "
            "Past the 5\u201310% S-curve inflection point identified by RMI and "
            "Nature Communications (2025) as triggering adoption takeoff."
        ),
        "sources": "IEA Global EV Outlook 2025; RMI X-Change: Cars",
    },
    {
        "label": "EVs past 5% in 15+ national markets",
        "status": "crossed",
        "year": "2023",
        "sector": "transport_road",
        "climate_weight": 0.10,
        "detail": (
            "Norway (88\u201397%), China (50%), Sweden (58%), Denmark (56%), "
            "Netherlands (48%), UK (~30%), EU avg (~21%), US (~10%), and "
            "many others have crossed the 5% threshold."
        ),
        "sources": "IEA Global EV Outlook 2025; BloombergNEF",
    },
    {
        "label": "EV price parity with ICE without subsidies",
        "status": "approaching",
        "year": "2025\u20132028",
        "sector": "transport_road",
        "climate_weight": 0.10,
        "detail": (
            "Battery pack prices fell below $100/kWh in China in 2024. "
            "A 2025 Nature Communications study projects unsubsidized purchase "
            "price parity for medium-sized EVs in most major markets by 2025\u20132028."
        ),
        "sources": "Nature Communications 2025; BloombergNEF Battery Price Survey",
    },
    {
        "label": "Cascading global EV tipping point \u2014 31 countries past 5%",
        "status": "approaching",
        "year": "Ongoing",
        "sector": "transport_road",
        "climate_weight": 0.10,
        "detail": (
            "BloombergNEF data shows 31 countries past the 5% EV sales threshold "
            "as of 2024. Network effects in manufacturing scale, charging "
            "infrastructure, and policy support create cascading acceleration."
        ),
        "sources": "BloombergNEF EVO 2025",
    },
    {
        "label": "Electric trucks past 5% of new sales",
        "status": "not_yet",
        "year": "Current: <1%",
        "sector": "transport_road",
        "climate_weight": 0.10,
        "detail": (
            "Battery-electric truck sales remain below 1% globally. "
            "Battery cost declines cascading from passenger EVs are expected "
            "to make electric trucks cost-competitive for short/medium haul "
            "by 2027\u20132030."
        ),
        "sources": "IEA Global EV Outlook 2025; ICCT",
    },

    # ---- TRANSPORT -- AVIATION (3 items) ----
    {
        "label": "SAF reaches 2% of jet fuel",
        "status": "not_yet",
        "year": "Current: ~0.3%",
        "sector": "transport_aviation",
        "climate_weight": 0.03,
        "detail": (
            "Sustainable aviation fuel currently constitutes roughly 0.3% of "
            "global jet fuel. EU ReFuelEU mandate requires 2% SAF by 2025 "
            "and 6% by 2030. Production capacity is scaling but remains "
            "far below targets."
        ),
        "sources": "IATA SAF Dashboard; EU ReFuelEU Aviation regulation",
    },
    {
        "label": "eVTOL aircraft certified for commercial service",
        "status": "not_yet",
        "year": "~2026\u20132027",
        "sector": "transport_aviation",
        "climate_weight": 0.03,
        "detail": (
            "Multiple eVTOL companies (Joby, Archer, Lilium) are in advanced "
            "certification stages. First commercial service expected 2026\u20132027, "
            "initially for urban air mobility."
        ),
        "sources": "FAA certification timelines; company filings",
    },
    {
        "label": "Electric regional aircraft certified (<100 passengers)",
        "status": "not_yet",
        "year": "Post-2030",
        "sector": "transport_aviation",
        "climate_weight": 0.03,
        "detail": (
            "Electric aircraft for regional routes remain in development. "
            "Battery energy density (~250 Wh/kg current vs ~800 Wh/kg needed) "
            "constrains range. Hybrid-electric approaches may come sooner."
        ),
        "sources": "ICAO LTAG report; Heart Aerospace, Wright Electric filings",
    },

    # ---- TRANSPORT -- SHIPPING (2 items) ----
    {
        "label": "Alternative fuels reach 5% of shipping fuel",
        "status": "not_yet",
        "year": "IMO target: 5\u201310% by 2030",
        "sector": "transport_shipping",
        "climate_weight": 0.03,
        "detail": (
            "Alternative fuels (methanol, ammonia, LNG as transition) currently "
            "represent a small fraction of total shipping fuel. IMO 2023 GHG "
            "Strategy targets 5\u201310% zero/near-zero GHG fuels by 2030."
        ),
        "sources": "IMO GHG Strategy 2023; DNV Maritime Forecast",
    },
    {
        "label": "300+ methanol-capable vessels on order",
        "status": "approaching",
        "year": "2024\u20132025",
        "sector": "transport_shipping",
        "climate_weight": 0.03,
        "detail": (
            "Over 300 methanol-capable vessels are on order globally. "
            "Maersk alone has ordered 25 methanol-powered container ships. "
            "Methanol is emerging as the leading transition fuel for shipping."
        ),
        "sources": "Global Maritime Forum; DNV Alternative Fuels Insight",
    },

    # ---- BUILDINGS (2 items) ----
    {
        "label": "Heat pumps outselling gas boilers in leading markets",
        "status": "crossed",
        "year": "2022\u20132024",
        "sector": "buildings",
        "climate_weight": 0.06,
        "detail": (
            "In the Nordics: 90\u201397% heat pump market share. European average: "
            "28% (past inflection). In the US, heat pumps outsold gas furnaces "
            "by 30% in 2024. UK still in early adoption (19 per 1,000 households)."
        ),
        "sources": "EHPA 2025; IEA Heat Pumps Tracking",
    },
    {
        "label": "Induction cooking reaches 10% of global cooking",
        "status": "not_yet",
        "year": "Current: ~5%",
        "sector": "buildings",
        "climate_weight": 0.06,
        "detail": (
            "Induction cooking has reached high penetration in some Asian markets "
            "(Japan, South Korea) but remains below 10% globally. Growth is "
            "accelerating in Europe and parts of the US."
        ),
        "sources": "IEA Buildings Tracking; industry estimates",
    },

    # ---- INDUSTRY (3 items) ----
    {
        "label": "Green steel (EAF) reaches 40% of global production",
        "status": "not_yet",
        "year": "Current: ~28% EAF share",
        "sector": "industry",
        "climate_weight": 0.21,
        "detail": (
            "Electric arc furnace steelmaking currently represents ~28% of "
            "global production. Reaching 40% would mark a significant shift. "
            "Green H2-based DRI-EAF projects are in pilot stage (HYBRIT, "
            "H2 Green Steel)."
        ),
        "sources": "World Steel Association; IEA Iron and Steel Tracking",
    },
    {
        "label": "Industrial heat pumps reaching 200\u00b0C",
        "status": "approaching",
        "year": "2024\u20132026",
        "sector": "industry",
        "climate_weight": 0.21,
        "detail": (
            "High-temperature industrial heat pumps capable of 150\u2013200\u00b0C "
            "are entering commercial deployment, enabling electrification of "
            "low-to-medium temperature industrial process heat."
        ),
        "sources": "IEA Industrial Heat Pumps report; Vattenfall pilot projects",
    },
    {
        "label": "Green hydrogen below $2/kg unsubsidized",
        "status": "not_yet",
        "year": "Current: ~$4\u20136/kg",
        "sector": "industry",
        "climate_weight": 0.21,
        "detail": (
            "Green hydrogen from electrolysis currently costs $4\u20136/kg. "
            "The ~$2/kg target is needed for competitiveness with grey hydrogen. "
            "Electrolyzer cost reductions and cheap renewables could reach this "
            "target by 2030 in optimal locations."
        ),
        "sources": "IEA Global Hydrogen Review 2024; IRENA Green Hydrogen Cost Reduction",
    },

    # ---- GRID & STORAGE (2 items) ----
    {
        "label": "Grid-scale battery storage doubling year-over-year",
        "status": "crossed",
        "year": "2023\u20132024",
        "sector": "grid_storage",
        "climate_weight": 0.04,
        "detail": (
            "Global battery storage additions roughly doubled in 2023 and 2024, "
            "with cumulative capacity reaching ~120 GWh. Growth rate comparable "
            "to solar PV around 2010."
        ),
        "sources": "BloombergNEF Energy Storage Outlook; IEA Grid-Scale Storage Tracking",
    },
    {
        "label": "Long-duration storage (>8hr) commercially viable",
        "status": "approaching",
        "year": "2025\u20132028",
        "sector": "grid_storage",
        "climate_weight": 0.04,
        "detail": (
            "Multiple LDES technologies (iron-air, compressed air, flow batteries, "
            "gravity storage) are in demo or early commercial stages. Form Energy's "
            "iron-air battery is targeting commercial deployment."
        ),
        "sources": "LDES Council; Form Energy, ESS Inc. filings",
    },

    # ---- NUCLEAR (1 item) ----
    {
        "label": "First SMR connected to grid",
        "status": "approaching",
        "year": "~2026",
        "sector": "nuclear",
        "climate_weight": 0.03,
        "detail": (
            "China's Linglong One (ACP100) SMR at Hainan is under construction "
            "with grid connection expected ~2026. NuScale canceled its first US "
            "project but other designs continue. Russia's floating SMR has "
            "operated since 2020."
        ),
        "sources": "IAEA SMR booklet; World Nuclear Association; China National Nuclear Corp.",
    },

    # ---- CARBON REMOVAL (2 items) ----
    {
        "label": "Direct air capture below $200/tonne",
        "status": "not_yet",
        "year": "Current: ~$400\u2013600/t",
        "sector": "carbon_removal",
        "climate_weight": 0.05,
        "detail": (
            "Current DAC costs are $400\u2013600/tonne for leading technologies "
            "(Climeworks, Carbon Engineering/Occidental). DOE Carbon Negative "
            "Shot targets $100/tonne. $200/tonne would likely trigger significant "
            "scale-up."
        ),
        "sources": "DOE Carbon Negative Shot; Climeworks/Occidental public cost estimates",
    },
    {
        "label": "Carbon removal reaches 1 GtCO\u2082/yr",
        "status": "not_yet",
        "year": "Current: ~0.04 Mt DAC",
        "sector": "carbon_removal",
        "climate_weight": 0.05,
        "detail": (
            "Total engineered carbon removal (DAC + BECCS) is in the tens of "
            "kilotonnes/yr. IPCC scenarios for 1.5\u00b0C require 5\u201316 GtCO\u2082/yr "
            "by 2050 \u2014 a gap of ~five orders of magnitude."
        ),
        "sources": "IPCC AR6 WGIII; CDR.fyi tracker",
    },

    # ---- SUPPLY CHAINS (1 item) ----
    {
        "label": "Critical mineral supply diversified (no country >50%)",
        "status": "not_yet",
        "year": "Significant concentration remains",
        "sector": "supply_chains",
        "climate_weight": 0.05,
        "detail": (
            "China dominates processing of many critical minerals: ~70% lithium "
            "refining, ~77% cobalt refining, ~97% gallium, ~60% graphite. "
            "Diversification is essential for energy security."
        ),
        "sources": "IEA Critical Minerals Report 2024; USGS; EU Critical Raw Materials Act",
    },

    # ---- FOSSIL FUELS (1 item) ----
    {
        "label": "Peak fossil fuel demand reached",
        "status": "contested",
        "year": "~2025?",
        "sector": "fossil_fuels",
        "climate_weight": 0.15,
        "detail": (
            "IEA projects fossil fuel demand peaks by ~2030 under current policies. "
            "DNV estimates emissions peaked in 2025. Coal demand may have already "
            "peaked. Oil demand peak depends heavily on EV adoption speed and "
            "petrochemical feedstock growth. Contested because some analysts "
            "project continued growth through the 2030s."
        ),
        "sources": "IEA WEO 2025 (STEPS); DNV ETO 2025; RMI 2025",
    },
]


# ---------------------------------------------------------------------------
# Section 1b: Climate System Tipping Points (negative / danger side)
# ---------------------------------------------------------------------------
# Status values: "crossed" (already tipping), "imminent" (within threshold
# range with early warnings), "approaching" (possible this century),
# "distant" (unlikely this century).

CLIMATE_TIPPING_POINTS = [
    {
        "label": "Coral Reef Die-off",
        "status": "crossed",
        "detail": (
            "The fourth global mass bleaching event (2023-2025) affected "
            "77% of reef areas worldwide. 84% of reefs surveyed showed "
            "bleaching. Warm-water coral ecosystems provide food security "
            "and livelihoods for hundreds of millions of people."
        ),
        "sources": "NOAA 4th Global Bleaching Event 2023-2025; ICRI",
        "threshold_c": "1.0-2.0",
        "urgency_weight": 1.0,
        "cascade_multiplier": 1.0,
        "impact_scale": "500M+ people (food), 84% bleached",
    },
    {
        "label": "Arctic Summer Sea Ice Loss",
        "status": "imminent",
        "detail": (
            "Arctic summer sea ice extent has declined ~13% per decade "
            "since 1979. Ice-free Arctic summers (< 1M km2) are projected "
            "by the 2030s-2040s. Loss of reflective ice drives albedo "
            "feedback that accelerates global warming."
        ),
        "sources": "CU Boulder 2024; IPCC AR6",
        "threshold_c": "~2.0",
        "urgency_weight": 0.9,
        "cascade_multiplier": 1.2,
        "impact_scale": "Ice-free summers by 2030s-2040s",
    },
    {
        "label": "Greenland Ice Sheet Collapse",
        "status": "imminent",
        "detail": (
            "Greenland has lost ~5,300 Gt of ice since 1992, contributing "
            "~15 mm to sea level rise. Full collapse would raise sea levels "
            "by up to 7.4m over millennia. Mass loss is accelerating and "
            "may trigger AMOC weakening."
        ),
        "sources": "Armstrong McKay et al. 2022, Science",
        "threshold_c": "0.8-3.0",
        "urgency_weight": 0.3,
        "cascade_multiplier": 1.3,
        "impact_scale": "Up to 7.4m SLR",
    },
    {
        "label": "West Antarctic Ice Sheet (WAIS) Collapse",
        "status": "imminent",
        "detail": (
            "Warm ocean water is destabilizing the Thwaites and Pine Island "
            "glaciers from below. Full WAIS collapse would raise sea levels "
            "by ~3.3m, putting ~480M people at risk. Process may already be "
            "irreversible for some glaciers."
        ),
        "sources": "Armstrong McKay et al. 2022; The Cryosphere 2025",
        "threshold_c": "1.0-3.0",
        "urgency_weight": 0.4,
        "cascade_multiplier": 1.1,
        "impact_scale": "3.3m SLR, 480M people at risk",
    },
    {
        "label": "AMOC Slowdown/Collapse",
        "status": "approaching",
        "detail": (
            "The Atlantic Meridional Overturning Circulation has weakened "
            "by ~15% since the mid-20th century. Full collapse would cause "
            "major cooling in Europe (-4 to -10C), disrupt monsoons, and "
            "destabilize the West Antarctic Ice Sheet."
        ),
        "sources": "RAPID array data 2004-2023; Nature 2024",
        "threshold_c": "1.4-8.0",
        "urgency_weight": 0.7,
        "cascade_multiplier": 1.4,
        "impact_scale": "Europe cooling -4 to -10C; monsoon disruption",
    },
    {
        "label": "Amazon Rainforest Dieback",
        "status": "approaching",
        "detail": (
            "Deforestation and warming are pushing portions of the Amazon "
            "toward a savanna tipping point. 2023-2024 drought and fires "
            "were the worst on record. Dieback would release massive stored "
            "carbon and cause biodiversity catastrophe."
        ),
        "sources": "Nature 2023; PBS 2024 fire data",
        "threshold_c": "2.0-6.0",
        "urgency_weight": 0.7,
        "cascade_multiplier": 1.2,
        "impact_scale": "$1-3.5T damages; massive biodiversity loss",
    },
    {
        "label": "Permafrost Thaw",
        "status": "approaching",
        "detail": (
            "Permafrost contains ~1,035 GtC -- roughly twice the carbon "
            "currently in the atmosphere. Thawing releases methane and CO2, "
            "creating a self-reinforcing feedback loop. Infrastructure "
            "damage already exceeds $20B."
        ),
        "sources": "Max Planck Institute 2025",
        "threshold_c": "1.0-6.0",
        "urgency_weight": 0.5,
        "cascade_multiplier": 1.2,
        "impact_scale": "1,035 GtC stored; >$20B infrastructure damage",
    },
    {
        "label": "Mountain Glacier Loss",
        "status": "crossed",
        "detail": (
            "Mountain glaciers outside Greenland and Antarctica have lost "
            "mass every year since 1989. Many small glaciers are past the "
            "point of recovery. Glacier-fed rivers provide water supply "
            "for nearly 2 billion people."
        ),
        "sources": "IPCC AR6; WGMS",
        "threshold_c": "1.5-3.0",
        "urgency_weight": 0.7,
        "cascade_multiplier": 1.0,
        "impact_scale": "Water supply for 2B people",
    },
    {
        "label": "Boreal Forest Dieback",
        "status": "approaching",
        "detail": (
            "Boreal forests, the largest terrestrial carbon sink, face "
            "increasing wildfire, insect outbreaks, and heat stress. "
            "Canada's 2024 wildfire season burned 13.5M hectares. "
            "Conversion to grassland would release massive carbon stores."
        ),
        "sources": "WRI 2024 fire data",
        "threshold_c": "1.4-5.0",
        "urgency_weight": 0.6,
        "cascade_multiplier": 1.1,
        "impact_scale": "Carbon sink loss; 13.5M ha burned in 2024",
    },
    {
        "label": "Monsoon System Disruption",
        "status": "distant",
        "detail": (
            "Major monsoon systems (South Asian, West African, East Asian) "
            "could be disrupted by warming or AMOC collapse. The South "
            "Asian monsoon alone supports food and water security for "
            "~1.7 billion people."
        ),
        "sources": "IPCC AR6 WG2; linked to AMOC",
        "threshold_c": "2.0-4.0",
        "urgency_weight": 0.8,
        "cascade_multiplier": 1.0,
        "impact_scale": "1.7B people food/water security",
    },
]


# ---------------------------------------------------------------------------
# Status colors (extended for climate tipping points)
# ---------------------------------------------------------------------------
CLIMATE_STATUS_COLORS = {
    "crossed": RED,
    "imminent": "#e67e22",  # orange
    "approaching": YELLOW,
    "distant": GRAY,
}

CLIMATE_STATUS_LABELS = {
    "crossed": "Already Tipping",
    "imminent": "Imminent",
    "approaching": "Approaching",
    "distant": "Distant",
}


# ---------------------------------------------------------------------------
# Status helpers
# ---------------------------------------------------------------------------

def _checklist_icon(status: str) -> html.Span:
    """Return a colored icon for checklist status."""
    icon_map = {
        "crossed": ("bi bi-check-circle-fill", GREEN),
        "approaching": ("bi bi-arrow-right-circle-fill", BLUE),
        "contested": ("bi bi-question-circle-fill", YELLOW),
        "not_yet": ("bi bi-x-circle-fill", RED),
    }
    icon_class, color = icon_map.get(status, ("bi bi-circle", GRAY))
    return html.I(
        className=f"{icon_class} me-2",
        style={"color": color, "fontSize": "1.3rem"},
    )


def _checklist_badge(status: str, year: str) -> dbc.Badge:
    """Return a badge with the year and status color."""
    color_map = {
        "crossed": "success",
        "approaching": "primary",
        "contested": "warning",
        "not_yet": "danger",
    }
    label_map = {
        "crossed": f"Crossed {year}",
        "approaching": f"Approaching \u2014 {year}",
        "contested": f"Contested \u2014 {year}",
        "not_yet": "Not yet",
    }
    return dbc.Badge(
        label_map.get(status, ""),
        color=color_map.get(status, "secondary"),
        className="ms-2",
        pill=True,
    )


# ---------------------------------------------------------------------------
# Section 1: Checklist grouped by sector via Accordion
# ---------------------------------------------------------------------------

def _build_checklist_section() -> dbc.Card:
    """Build the tipping-points checklist section grouped by sector accordion."""
    # Group items by sector
    sector_items = OrderedDict()
    for item in CHECKLIST_ITEMS:
        sector = item["sector"]
        if sector not in sector_items:
            sector_items[sector] = []
        sector_items[sector].append(item)

    # Count totals for header
    total = len(CHECKLIST_ITEMS)
    crossed = sum(1 for i in CHECKLIST_ITEMS if i["status"] == "crossed")
    approaching = sum(1 for i in CHECKLIST_ITEMS if i["status"] == "approaching")
    contested = sum(1 for i in CHECKLIST_ITEMS if i["status"] == "contested")
    not_yet = sum(1 for i in CHECKLIST_ITEMS if i["status"] == "not_yet")

    # Build accordion items for each sector
    accordion_items = []
    for sector_key, items in sector_items.items():
        meta = SECTOR_META.get(sector_key, {"name": sector_key, "icon": "bi-circle"})
        sector_crossed = sum(1 for i in items if i["status"] == "crossed")
        sector_approaching = sum(1 for i in items if i["status"] == "approaching")
        sector_total = len(items)

        # Build list items for this sector
        list_items = []
        for item in items:
            list_items.append(
                dbc.ListGroupItem([
                    html.Div([
                        html.Div([
                            _checklist_icon(item["status"]),
                            html.Span(item["label"], className="fw-bold"),
                            _checklist_badge(item["status"], item["year"]),
                        ], className="d-flex align-items-center flex-wrap"),
                        html.P(
                            item["detail"],
                            className="mb-1 mt-2 small text-muted",
                        ),
                        html.P(
                            [html.Em("Sources: "), item["sources"]],
                            className="mb-0 small text-muted",
                            style={"fontSize": "0.8rem"},
                        ),
                    ]),
                ])
            )

        # Sector progress summary for the accordion header
        progress_parts = []
        if sector_crossed > 0:
            progress_parts.append(f"{sector_crossed} crossed")
        if sector_approaching > 0:
            progress_parts.append(f"{sector_approaching} approaching")
        remaining = sector_total - sector_crossed - sector_approaching
        if remaining > 0:
            progress_parts.append(f"{remaining} remaining")
        progress_text = " | ".join(progress_parts)

        accordion_items.append(
            dbc.AccordionItem(
                dbc.ListGroup(list_items, flush=True),
                title=html.Span([
                    html.I(className=f"{meta['icon']} me-2"),
                    f"{meta['name']}: ",
                    html.Small(progress_text, className="text-muted"),
                ]),
                item_id=sector_key,
            )
        )

    return dbc.Card([
        dbc.CardHeader([
            html.H4([
                html.I(className="bi bi-check2-square me-2"),
                "Clean Energy Tipping Points Checklist",
            ], className="mb-0 fw-bold"),
        ]),
        dbc.CardBody([
            html.P([
                html.Span(f"{crossed}", className="fw-bold", style={"color": GREEN}),
                f" of {total} tipping points crossed",
                html.Span(" | ", className="text-muted mx-1"),
                html.Span(f"{approaching} approaching", style={"color": BLUE}),
                html.Span(" | ", className="text-muted mx-1"),
                html.Span(
                    f"{contested} contested",
                    style={"color": YELLOW},
                ) if contested else "",
                html.Span(" | ", className="text-muted mx-1") if contested else "",
                html.Span(f"{not_yet} not yet", style={"color": RED}),
            ], className="lead mb-3"),
            html.P(
                "Based on the framework from RMI, Lenton et al. (Exeter), "
                "and Carbon Tracker: technologies reach a catalytic tipping point "
                "at ~5\u201310% market share, after which adoption accelerates rapidly. "
                "Each item below tracks whether a key clean energy threshold has "
                "been crossed. Items are grouped by sector and weighted by each "
                "sector's share of global emissions.",
                className="text-muted small mb-3",
            ),
            dbc.Accordion(
                accordion_items,
                start_collapsed=True,
                always_open=True,
                flush=True,
            ),
        ]),
    ], className="mb-4 shadow-sm")


# ---------------------------------------------------------------------------
# Section 2: S-Curve Momentum Tracker
# ---------------------------------------------------------------------------

S_CURVE_STAGES = [
    {
        "stage": "Innovation (<1%)",
        "color": GRAY,
        "icon": "bi-lightbulb",
        "technologies": [
            ("DAC (direct air capture)", "~0.5% of removal needed; costs $400\u2013600/t"),
            ("E-fuels (synthetic fuels)", "Pilot scale; niche aviation/shipping use"),
            ("SAF (sustainable aviation fuel)", "~0.3% of jet fuel; scaling slowly"),
            ("Shipping alt-fuels", "~1% of shipping fuel; methanol orders growing"),
            ("Electric trucks", "~1% of new sales; battery costs cascading from EVs"),
        ],
    },
    {
        "stage": "Early Adoption (1\u20135%)",
        "color": BLUE,
        "icon": "bi-graph-up",
        "technologies": [
            ("Green H\u2082 electrolyzers", "~3% of H2 production; $4\u20136/kg cost"),
            ("Offshore wind (global)", "~8% of total wind; rapid growth in UK, EU, China"),
            ("Induction cooking (global)", "~5% of cooking; strong in Asia"),
        ],
    },
    {
        "stage": "Rapid Growth (10\u201350%)",
        "color": "#27ae60",
        "icon": "bi-rocket-takeoff",
        "technologies": [
            ("EVs (22% globally)", "Past the 5\u201310% inflection; 50%+ in China, Norway"),
            ("Solar PV (~10% of electricity)", "Largest source of new electricity for 3 consecutive years"),
            ("Wind power (~8% of electricity)", "Mature in Denmark (58%), Germany (23%), US (~11%)"),
            ("Grid storage (~14% growth rate)", "Doubling YoY; entering steep S-curve like solar ~2010"),
            ("Heat pumps global (~10%)", "28% in Europe; US outselling gas furnaces"),
        ],
    },
    {
        "stage": "Mainstream (>50%)",
        "color": GREEN,
        "icon": "bi-check2-all",
        "technologies": [
            ("Renewables in new capacity (>80%)", "Dominant source of new power globally since ~2015"),
            ("EVs in Norway (88\u201397%)", "Near-saturation; essentially completed S-curve"),
            ("Heat pumps in Nordics (90%+)", "Finland, Sweden, Norway \u2014 near-complete adoption"),
            ("LED lighting (~65% globally)", "Rapid transition from 4% (2015) to 65% (2025)"),
        ],
    },
]


_SCURVE_CACHE = None

def _build_scurve_figure() -> go.Figure:
    """Build an idealized S-curve with stage annotations. Cached at module level."""
    global _SCURVE_CACHE
    if _SCURVE_CACHE is not None:
        return _SCURVE_CACHE
    import numpy as np
    x = np.linspace(-6, 6, 200)
    y = 100 / (1 + np.exp(-x))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode="lines",
        line={"color": PRIMARY, "width": 3},
        hoverinfo="skip",
        showlegend=False,
    ))

    # Stage regions (approximate x positions on the S-curve)
    stages = [
        ("Innovation\n<1%", -5, 2, GRAY),
        ("Early\nAdoption\n1\u20135%", -2.5, 8, BLUE),
        ("Rapid\nGrowth\n10\u201350%", 0.5, 55, "#27ae60"),
        ("Main-\nstream\n>50%", 3.5, 92, GREEN),
    ]
    for label, x_pos, y_pos, color in stages:
        fig.add_annotation(
            x=x_pos, y=y_pos,
            text=label,
            showarrow=False,
            font={"size": 11, "color": color, "family": "Arial"},
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor=color,
            borderwidth=1,
            borderpad=4,
        )

    # Mark specific technologies on the curve (expanded list)
    tech_markers = [
        ("DAC", -5.0, 0.7),
        ("SAF", -4.5, 1.1),
        ("Ship\nalt-fuels", -4.0, 1.8),
        ("E-trucks", -3.8, 2.2),
        ("Green H\u2082", -3.0, 4.7),
        ("Grid\nstorage", -1.5, 18),
        ("Heat pumps\nglobal", -0.8, 31),
        ("EVs\n(global)", 0.8, 22),
        ("Solar PV", 1.2, 30),
        ("RE in new\ncapacity", 3.0, 83),
        ("EVs\n(Norway)", 4.2, 96),
    ]
    for label, x_pos, y_pos in tech_markers:
        fig.add_trace(go.Scatter(
            x=[x_pos], y=[y_pos],
            mode="markers+text",
            marker={"size": 10, "color": PRIMARY, "symbol": "diamond"},
            text=[label],
            textposition="top center",
            textfont={"size": 9},
            hoverinfo="text",
            hovertext=label.replace("\n", " "),
            showlegend=False,
        ))

    fig.update_layout(
        xaxis={"visible": False},
        yaxis={"title": "Market Share (%)", "range": [-2, 105]},
        margin={"l": 50, "r": 20, "t": 30, "b": 20},
        height=380,
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=CHART_FONT,
    )
    _SCURVE_CACHE = fig
    return fig


def _build_scurve_section() -> dbc.Card:
    """Build the S-curve momentum tracker section."""
    # Technology cards for each stage
    stage_rows = []
    for stage_info in S_CURVE_STAGES:
        tech_items = []
        for name, detail in stage_info["technologies"]:
            tech_items.append(
                html.Li([
                    html.Strong(name, style={"color": stage_info["color"]}),
                    html.Span(f" \u2014 {detail}", className="text-muted small"),
                ], className="mb-1")
            )
        stage_rows.append(
            dbc.Col([
                html.Div([
                    html.H6([
                        html.I(className=f"{stage_info['icon']} me-1"),
                        stage_info["stage"],
                    ], style={"color": stage_info["color"]}, className="fw-bold mb-2"),
                    html.Ul(tech_items, className="ps-3", style={"listStyleType": "none"}),
                ], className="p-2", style={
                    "borderLeft": f"3px solid {stage_info['color']}",
                    "backgroundColor": LIGHT_BG,
                    "borderRadius": "4px",
                }),
            ], md=6, lg=3, className="mb-3")
        )

    return dbc.Card([
        dbc.CardHeader([
            html.H4([
                html.I(className="bi bi-graph-up-arrow me-2"),
                "S-Curve Momentum Tracker",
            ], className="mb-0 fw-bold"),
        ]),
        dbc.CardBody([
            html.P(
                "Technology adoption follows S-curves: slow start, explosive middle, "
                "gradual saturation. The critical insight from RMI and Carbon Tracker: "
                "technologies reaching ~5\u201310% market share typically accelerate rapidly "
                "toward 50%+. The same time it takes to go from 0% to 5% often equals "
                "the time from 5% to 50%.",
                className="text-muted small mb-3",
            ),
            dcc.Graph(
                figure=_build_scurve_figure(),
                config=GRAPH_CONFIG,
                className="mb-3",
            ),
            dbc.Row(stage_rows),
            html.P([
                html.Em("Sources: "),
                "RMI (Bond & Butler-Sloss 2022, ",
                html.Em("Peaking: A Theory of Rapid Transition"),
                "); RethinkX; Rogers (1962), ",
                html.Em("Diffusion of Innovations"),
                "; Way et al. 2022 (",
                html.Em("Joule"),
                "); Carbon Tracker S-Curve analysis.",
            ], className="text-muted small mt-2", style={"fontSize": "0.8rem"}),
        ]),
    ], className="mb-4 shadow-sm")


# ---------------------------------------------------------------------------
# Section 3: Countdown to Key Milestones
# ---------------------------------------------------------------------------

def _build_countdown_section() -> dbc.Card:
    """Build progress bars / gauges toward key milestones using real data."""
    kpis = get_kpis()

    # Temperature
    temp_val = kpis.get("temperature_anomaly_c", {}).get("value", 1.55)
    temp_pct = min((temp_val / 2.0) * 100, 100)  # Scale to 2C as "full bar"

    # Renewable electricity share
    re_share = kpis.get("renewable_share_electricity_pct", {}).get("value", 31.7)

    # Clean energy investment
    clean_inv = kpis.get("clean_energy_investment_t", {}).get("value", 2.15)
    inv_target = 4.5  # IEA NZE requires ~$4.5T/yr by 2030
    inv_pct = min((clean_inv / inv_target) * 100, 100)

    # Net-zero pledges coverage (editorial)
    nz_pct_gdp = 88

    # Coal phase-out commitments
    coal_committed = 58
    coal_dependent = 80
    coal_pct = min((coal_committed / coal_dependent) * 100, 100)

    # NEW: Second TW of solar
    solar_current_gw = 1865
    solar_target_gw = 2000
    solar_pct = min((solar_current_gw / solar_target_gw) * 100, 100)

    # NEW: Global EV fleet
    ev_fleet_current_m = 58
    ev_fleet_target_m = 230  # IEA NZE 2030 target
    ev_fleet_pct = min((ev_fleet_current_m / ev_fleet_target_m) * 100, 100)

    # NEW: Green hydrogen cost
    h2_current = 5.0  # $/kg
    h2_target = 2.0   # $/kg
    # Invert: lower cost = more progress. Progress = (start - current) / (start - target)
    h2_start = 12.0   # ~$12/kg a decade ago
    h2_pct = min(max(0, (h2_start - h2_current) / (h2_start - h2_target) * 100), 100)

    milestones = [
        {
            "label": "Global Temperature",
            "current": f"{temp_val}\u00b0C",
            "target": "1.5\u00b0C Paris target",
            "pct": temp_pct,
            "color": RED if temp_val >= 1.5 else YELLOW,
            "note": (
                f"Already at {temp_val}\u00b0C above pre-industrial baseline. "
                "Carbon budget for 50% chance of staying below 1.5\u00b0C is "
                "~250 GtCO\u2082 (~6 years at current rates)."
            ),
            "source": "HadCRUT5 (Met Office/UEA); IPCC AR6",
        },
        {
            "label": "Renewable Electricity Share",
            "current": f"{re_share}%",
            "target": "100% target",
            "pct": re_share,
            "color": GREEN if re_share > 30 else YELLOW,
            "note": (
                f"Renewables generate {re_share}% of global electricity (2024). "
                "IEA Net Zero scenario requires ~90% by 2050."
            ),
            "source": "OWID (Ember/IRENA)",
        },
        {
            "label": "Clean Energy Investment",
            "current": f"${clean_inv}T/yr",
            "target": f"${inv_target}T/yr needed (IEA NZE 2030)",
            "pct": inv_pct,
            "color": GREEN if inv_pct > 40 else YELLOW,
            "note": (
                f"Clean energy investment reached ${clean_inv}T in 2025 \u2014 "
                "nearly 2x fossil fuel investment. IEA NZE pathway requires "
                f"~${inv_target}T/yr by 2030."
            ),
            "source": "IEA World Energy Investment 2025",
        },
        {
            "label": "Second TW of Solar Capacity",
            "current": f"{solar_current_gw:,} GW",
            "target": f"{solar_target_gw:,} GW",
            "pct": solar_pct,
            "color": GREEN,
            "note": (
                f"Solar capacity at {solar_current_gw:,} GW. With >400 GW/yr "
                "additions, the second TW milestone is expected mid-2026. "
                "First TW took ~15 years; second TW in ~4 years."
            ),
            "source": "IRENA 2025; BloombergNEF",
        },
        {
            "label": "Global EV Fleet",
            "current": f"~{ev_fleet_current_m}M vehicles",
            "target": f"{ev_fleet_target_m}M by 2030 (IEA NZE)",
            "pct": ev_fleet_pct,
            "color": YELLOW,
            "note": (
                f"~{ev_fleet_current_m}M EVs on the road globally. IEA NZE "
                f"scenario requires ~{ev_fleet_target_m}M by 2030. Annual sales "
                "of 17M in 2024 need to roughly double."
            ),
            "source": "IEA Global EV Outlook 2025",
        },
        {
            "label": "Green Hydrogen Cost",
            "current": f"~${h2_current}/kg",
            "target": f"${h2_target}/kg target",
            "pct": h2_pct,
            "color": YELLOW,
            "note": (
                f"Green H\u2082 at ~${h2_current}/kg, down from ~$12/kg a decade "
                f"ago. Target: ${h2_target}/kg for competitiveness with grey H\u2082. "
                "Electrolyzer costs and cheap renewables are key drivers."
            ),
            "source": "IEA Global Hydrogen Review 2024; IRENA",
        },
        {
            "label": "Net-Zero Pledges (% of global GDP)",
            "current": f"{nz_pct_gdp}%",
            "target": "100% of global GDP",
            "pct": nz_pct_gdp,
            "color": GREEN,
            "note": (
                "~88% of global GDP covered by net-zero pledges. However, the "
                "implementation gap remains large \u2014 current policies deliver "
                "~3.1\u00b0C, not the ~1.5\u00b0C these pledges imply."
            ),
            "source": "Energy & Climate Intelligence Unit (ECIU); UNEP EGR 2024",
        },
        {
            "label": "Coal Phase-Out Commitments",
            "current": f"{coal_committed} countries",
            "target": f"~{coal_dependent} coal-using countries",
            "pct": coal_pct,
            "color": YELLOW,
            "note": (
                f"{coal_committed} countries have committed to coal phase-out or "
                "joined the Powering Past Coal Alliance. Major gaps: China, India, "
                "Indonesia, US."
            ),
            "source": "Powering Past Coal Alliance; Global Energy Monitor",
        },
    ]

    rows = []
    for m in milestones:
        rows.append(
            dbc.Col([
                html.Div([
                    html.Div([
                        html.Strong(m["label"]),
                        html.Span(
                            f"  {m['current']} / {m['target']}",
                            className="text-muted small ms-2",
                        ),
                    ], className="mb-1"),
                    dbc.Progress(
                        value=m["pct"],
                        color=(
                            "danger" if m["color"] == RED
                            else "warning" if m["color"] == YELLOW
                            else "success"
                        ),
                        striped=True,
                        animated=True,
                        className="mb-1",
                        style={"height": "22px"},
                    ),
                    html.P(m["note"], className="text-muted small mb-1",
                           style={"fontSize": "0.8rem"}),
                    html.P(
                        [html.Em("Source: "), m["source"]],
                        className="text-muted mb-0",
                        style={"fontSize": "0.75rem"},
                    ),
                ], className="p-3", style={
                    "backgroundColor": LIGHT_BG,
                    "borderRadius": "6px",
                }),
            ], md=6, className="mb-3")
        )

    return dbc.Card([
        dbc.CardHeader([
            html.H4([
                html.I(className="bi bi-hourglass-split me-2"),
                "Countdown to Key Milestones",
            ], className="mb-0 fw-bold"),
        ]),
        dbc.CardBody([
            html.P(
                "Progress toward critical energy transition thresholds. "
                "These milestones combine observed data with pathway targets from "
                "the IEA Net Zero scenario, IPCC AR6, and international agreements.",
                className="text-muted small mb-3",
            ),
            dbc.Row(rows),
        ]),
    ], className="mb-4 shadow-sm")


# ---------------------------------------------------------------------------
# Section 4: Optimism Meter (Dual-score: Progress vs. Climate Risk)
# ---------------------------------------------------------------------------
# The meter now weighs positive clean energy tipping points AGAINST negative
# climate system tipping points, producing a net score with a visual
# breakdown of both components.

def _compute_progress_score() -> tuple:
    """
    Compute the progress score (0-100) from clean energy tipping points.

    Keeps the existing emissions-weighted checklist methodology but combines
    checklist, momentum, and gap sub-scores into a single 0-100 value.

    Returns (progress_score, progress_breakdown).
    """
    kpis = get_kpis()

    # ---------------------------------------------------------------
    # 1. Checklist sub-score (40 points max) -- emissions-weighted
    # ---------------------------------------------------------------
    proximity_multiplier = {
        "crossed": 1.0,
        "approaching": 1.5,
        "contested": 0.75,
        "not_yet": 0.5,
    }

    sector_scores = {}
    sector_max = {}
    for item in CHECKLIST_ITEMS:
        sector = item["sector"]
        weight = item["climate_weight"]
        mult = proximity_multiplier.get(item["status"], 0.5)
        sc = weight * mult

        if sector not in sector_scores:
            sector_scores[sector] = 0
            sector_max[sector] = 0
        sector_scores[sector] += sc
        sector_max[sector] += weight * 1.5  # max multiplier

    total_weighted = sum(sector_scores.values())
    total_max = sum(sector_max.values())
    checklist_raw = total_weighted / total_max if total_max > 0 else 0
    checklist_score = checklist_raw * 40

    # ---------------------------------------------------------------
    # 2. Momentum sub-score (30 points max)
    # ---------------------------------------------------------------
    re_share = kpis.get("renewable_share_electricity_pct", {}).get("value", 31.7)
    re_score = min(re_share / 100 * 8, 8)

    clean_inv = kpis.get("clean_energy_investment_t", {}).get("value", 2.15)
    inv_ratio = clean_inv / 1.1
    inv_score = min(inv_ratio / 3 * 7, 7)

    solar_growth = kpis.get("capacity_solar_gw", {}).get("pct_change", 32)
    growth_score = min(solar_growth / 30 * 8, 8)

    ev_share = 22.0
    ev_score = min(ev_share / 50 * 7, 7)

    momentum_score = re_score + inv_score + growth_score + ev_score

    # ---------------------------------------------------------------
    # 3. Gap sub-score (30 points max, inverted)
    # ---------------------------------------------------------------
    temp = kpis.get("temperature_anomaly_c", {}).get("value", 1.55)
    temp_score = max(0, (2.0 - temp) / 0.5 * 10)

    proj_warming = kpis.get("current_policies_warming_c", {}).get("value", 3.1)
    proj_score = max(0, (4.0 - proj_warming) / 2.0 * 10)

    emissions_growth = kpis.get("co2_fossil_gt", {}).get("pct_change", 1.1)
    emissions_score = max(0, min(10, (5 - emissions_growth) / 5 * 10))

    gap_score = temp_score + proj_score + emissions_score

    # ---------------------------------------------------------------
    # Combined progress score (0 - 100)
    # ---------------------------------------------------------------
    progress_score = checklist_score + momentum_score + gap_score

    # Status counts for display
    crossed_count = sum(1 for i in CHECKLIST_ITEMS if i["status"] == "crossed")
    approaching_count = sum(1 for i in CHECKLIST_ITEMS if i["status"] == "approaching")
    contested_count = sum(1 for i in CHECKLIST_ITEMS if i["status"] == "contested")
    not_yet_count = sum(1 for i in CHECKLIST_ITEMS if i["status"] == "not_yet")
    total_count = len(CHECKLIST_ITEMS)

    breakdown = {
        "checklist": round(checklist_score, 1),
        "momentum": round(momentum_score, 1),
        "gap": round(gap_score, 1),
        "sub": {
            "Tipping points": (
                f"{crossed_count} crossed, {approaching_count} approaching, "
                f"{contested_count} contested, {not_yet_count} not yet "
                f"(of {total_count})"
            ),
            "Checklist weighting": (
                f"Emissions-weighted: {checklist_raw:.2f} raw "
                f"-> {checklist_score:.1f}/40"
            ),
            "Renewable electricity": f"{re_share}% -> {re_score:.1f}/8",
            "Investment ratio": f"{inv_ratio:.1f}:1 clean/fossil -> {inv_score:.1f}/7",
            "Solar growth": f"{solar_growth}% YoY -> {growth_score:.1f}/8",
            "EV share trajectory": f"{ev_share}% global -> {ev_score:.1f}/7",
            "Temperature buffer": f"{temp}C of 2C -> {temp_score:.1f}/10",
            "Policy trajectory": f"{proj_warming}C projected -> {proj_score:.1f}/10",
            "Emissions growth": f"{emissions_growth}% -> {emissions_score:.1f}/10",
        },
    }
    return round(progress_score, 1), breakdown


def _compute_danger_score() -> tuple:
    """
    Compute the climate risk score (0-100) from the S-curve temperature
    trajectory model.

    Instead of scoring individual climate tipping points, this uses the
    bottom-up temperature projection: how much warming does the S-curve
    model predict, and how does that compare to safe thresholds?

    Scoring:
    - 1.5°C or below = 0 (Paris target met)
    - 2.0°C = 50 (guardrail breached)
    - 3.1°C = 100 (current policies, worst case)

    Linear interpolation between these anchors.

    Returns (danger_score, danger_breakdown).
    """
    from utils.data_loader import get_temperature_trajectory

    traj = get_temperature_trajectory()
    scenarios = traj.get("scenarios", {}) if traj else {}

    central = scenarios.get("scurve_central", {})
    fast = scenarios.get("scurve_fast", {})
    slow = scenarios.get("scurve_slow", {})

    peak_temp = central.get("peak_temp_c", 2.5)
    peak_year = central.get("peak_year", 2100)
    temp_2050 = central.get("temp_2050", 2.0)
    temp_2100 = central.get("temp_2100", 2.5)
    fast_peak = fast.get("peak_temp_c", peak_temp - 0.1)
    slow_peak = slow.get("peak_temp_c", peak_temp + 0.1)

    # Score: linear mapping from temperature to danger
    # 1.5°C → 0, 2.0°C → 50, 3.1°C → 100
    def temp_to_score(t):
        if t <= 1.5:
            return 0.0
        elif t <= 2.0:
            return (t - 1.5) / (2.0 - 1.5) * 50.0
        else:
            return 50.0 + (t - 2.0) / (3.1 - 2.0) * 50.0

    danger_score = round(min(100, temp_to_score(peak_temp)), 1)

    # Sub-scores for each temperature milestone
    overshoot_15 = round(max(0, peak_temp - 1.5), 2)
    overshoot_20 = round(max(0, peak_temp - 2.0), 2)
    gap_from_policies = round(3.1 - peak_temp, 2)

    breakdown = {
        "method": "S-curve temperature projection",
        "peak_temp_c": peak_temp,
        "peak_year": peak_year,
        "temp_2050_c": temp_2050,
        "temp_2100_c": temp_2100,
        "fast_scenario_peak": fast_peak,
        "slow_scenario_peak": slow_peak,
        "overshoot_above_15": overshoot_15,
        "overshoot_above_20": overshoot_20,
        "improvement_vs_policies": gap_from_policies,
        "status_summary": (
            f"S-curve peak: {peak_temp}°C in {peak_year} "
            f"(range: {fast_peak}–{slow_peak}°C) — "
            f"{overshoot_15}°C above 1.5°C target, "
            f"{gap_from_policies}°C below current policies"
        ),
        "scoring_rule": "1.5°C=0, 2.0°C=50, 3.1°C=100 (linear interpolation)",
    }

    return danger_score, breakdown


def _compute_optimism_score() -> tuple:
    """
    Compute the dual-score optimism meter.

    Net score = progress_score - (danger_score x 0.5)

    The 0.5 factor means a danger score of 100 can at most cancel half
    the progress -- acknowledging that the dangers are real but the
    dashboard's purpose is tracking whether we're responding fast enough.
    The net score can go negative.

    Returns (net_score, progress_score, danger_score, full_breakdown).
    """
    progress_score, progress_breakdown = _compute_progress_score()
    danger_score, danger_breakdown = _compute_danger_score()

    net_score = round(progress_score - (danger_score * 0.5), 1)

    # Sensitivity analysis
    optimistic_net = round(net_score + 5, 1)
    conservative_net = round(net_score - 8, 1)

    full_breakdown = {
        "progress": progress_breakdown,
        "danger": danger_breakdown,
        "progress_score": progress_score,
        "danger_score": danger_score,
        "net_score": net_score,
        "scenarios": {
            "optimistic": optimistic_net,
            "central": net_score,
            "conservative": conservative_net,
        },
        "progress_weights_table": _build_weights_table_data(),
    }

    return net_score, progress_score, danger_score, full_breakdown


def _build_weights_table_data() -> list:
    """Build the data for the progress weighting transparency table."""
    proximity_labels = {
        "crossed": "1.0",
        "approaching": "1.5",
        "contested": "0.75",
        "not_yet": "0.5",
    }
    rows = []
    for item in CHECKLIST_ITEMS:
        meta = SECTOR_META.get(item["sector"], {})
        rows.append({
            "sector": meta.get("name", item["sector"]),
            "item": item["label"],
            "status": item["status"],
            "climate_weight": item["climate_weight"],
            "proximity_mult": proximity_labels.get(item["status"], "0.5"),
        })
    return rows


def _build_optimism_section() -> dbc.Card:
    """
    Build the optimism meter section with dual-bar visualization showing
    Progress vs. Climate Risk, a net score, and collapsible breakdown tables.
    """
    net_score, progress_score, danger_score, breakdown = _compute_optimism_score()
    scenarios = breakdown.get("scenarios", {})
    progress_bd = breakdown.get("progress", {})
    danger_bd = breakdown.get("danger", {})

    # ---------------------------------------------------------------
    # Net score display: color and sign
    # ---------------------------------------------------------------
    if net_score > 0:
        net_color = GREEN
        net_prefix = "+"
    elif net_score < 0:
        net_color = RED
        net_prefix = ""  # negative sign comes from the number
    else:
        net_color = YELLOW
        net_prefix = ""

    # ---------------------------------------------------------------
    # Dual-bar visualization
    # ---------------------------------------------------------------
    # Progress bar (green, left)
    progress_bar = html.Div([
        html.Div([
            html.I(className="bi bi-lightning-charge-fill me-1"),
            html.Span("Clean Energy Progress", className="fw-bold"),
        ], className="mb-1 small"),
        html.Div([
            html.Div(
                style={
                    "width": f"{min(progress_score, 100)}%",
                    "backgroundColor": GREEN,
                    "height": "28px",
                    "borderRadius": "4px",
                    "transition": "width 0.5s ease",
                    "minWidth": "2px",
                },
            ),
        ], style={
            "backgroundColor": "#e8f8f5",
            "borderRadius": "4px",
            "overflow": "hidden",
        }),
        html.Div([
            html.Span(
                f"{progress_score}/100",
                className="fw-bold",
                style={"color": GREEN},
            ),
            html.Span(
                f"  (Checklist {progress_bd.get('checklist', 0)}/40 + "
                f"Momentum {progress_bd.get('momentum', 0)}/30 + "
                f"Gap {progress_bd.get('gap', 0)}/30)",
                className="text-muted",
                style={"fontSize": "0.75rem"},
            ),
        ], className="mt-1 small"),
    ], className="mb-3")

    # Danger bar (red, right)
    danger_bar = html.Div([
        html.Div([
            html.I(className="bi bi-exclamation-triangle-fill me-1"),
            html.Span("Climate System Risk", className="fw-bold"),
        ], className="mb-1 small"),
        html.Div([
            html.Div(
                style={
                    "width": f"{min(danger_score, 100)}%",
                    "backgroundColor": RED,
                    "height": "28px",
                    "borderRadius": "4px",
                    "transition": "width 0.5s ease",
                    "minWidth": "2px",
                },
            ),
        ], style={
            "backgroundColor": "#fadbd8",
            "borderRadius": "4px",
            "overflow": "hidden",
        }),
        html.Div([
            html.Span(
                f"{danger_score}/100",
                className="fw-bold",
                style={"color": RED},
            ),
            html.Span(
                f"  ({danger_bd.get('status_summary', '')})",
                className="text-muted",
                style={"fontSize": "0.75rem"},
            ),
        ], className="mt-1 small"),
    ], className="mb-3")

    # Net score display (center)
    net_display = html.Div([
        html.Div([
            html.Span(
                "Net Score",
                className="text-muted small d-block text-center mb-1",
            ),
            html.Div(
                f"{net_prefix}{net_score}",
                className="text-center fw-bold",
                style={
                    "fontSize": "2.8rem",
                    "color": net_color,
                    "lineHeight": "1.1",
                },
            ),
            html.Div(
                f"= {progress_score} - ({danger_score} x 0.5)",
                className="text-center text-muted",
                style={"fontSize": "0.75rem"},
            ),
        ], style={
            "border": f"2px solid {net_color}",
            "borderRadius": "12px",
            "padding": "12px 20px",
            "backgroundColor": "white",
        }),
    ], className="d-flex justify-content-center mb-3")

    # Scenario badges
    scenario_badges = html.Div([
        html.Span("Sensitivity: ", className="small fw-bold me-2"),
        dbc.Badge(
            f"Conservative: {scenarios.get('conservative', 0)}",
            color="danger",
            className="me-1",
            pill=True,
        ),
        dbc.Badge(
            f"Central: {scenarios.get('central', 0)}",
            color="primary",
            className="me-1",
            pill=True,
        ),
        dbc.Badge(
            f"Optimistic: {scenarios.get('optimistic', 0)}",
            color="success",
            pill=True,
        ),
    ], className="mb-3 text-center")

    # ---------------------------------------------------------------
    # Collapsible breakdown: Progress Drivers
    # ---------------------------------------------------------------
    # Build progress sub-table
    progress_sub_rows = []
    for label, value in progress_bd.get("sub", {}).items():
        progress_sub_rows.append(html.Tr([
            html.Td(label, className="small text-muted"),
            html.Td(value, className="small text-muted text-end"),
        ]))

    # Build progress weights table
    weights_data = breakdown.get("progress_weights_table", [])
    progress_status_colors = {
        "crossed": GREEN,
        "approaching": BLUE,
        "contested": YELLOW,
        "not_yet": RED,
    }
    progress_weights_rows = []
    for row in weights_data:
        s_color = progress_status_colors.get(row["status"], GRAY)
        progress_weights_rows.append(html.Tr([
            html.Td(row["sector"], className="small"),
            html.Td(row["item"], className="small"),
            html.Td(
                html.Span(
                    row["status"].replace("_", " ").title(),
                    style={"color": s_color, "fontWeight": "600"},
                ),
                className="small",
            ),
            html.Td(f"{row['climate_weight']:.2f}", className="small text-end"),
            html.Td(row["proximity_mult"], className="small text-end"),
        ]))

    progress_collapse = html.Details([
        html.Summary(
            "Progress Drivers -- full breakdown (click to expand)",
            className="small text-primary mb-2",
            style={"cursor": "pointer"},
        ),
        html.Div([
            html.H6("Score Components", className="fw-bold mb-2 small"),
            dbc.Table([
                html.Tbody([
                    html.Tr([
                        html.Td("Checklist (40 pts)", className="small"),
                        html.Td(
                            html.Strong(f"{progress_bd.get('checklist', 0)}"),
                            className="small text-end",
                        ),
                    ]),
                    html.Tr([
                        html.Td("Momentum (30 pts)", className="small"),
                        html.Td(
                            html.Strong(f"{progress_bd.get('momentum', 0)}"),
                            className="small text-end",
                        ),
                    ]),
                    html.Tr([
                        html.Td("Gap to targets (30 pts)", className="small"),
                        html.Td(
                            html.Strong(f"{progress_bd.get('gap', 0)}"),
                            className="small text-end",
                        ),
                    ]),
                ] + progress_sub_rows),
            ], bordered=False, size="sm", className="mb-3"),

            html.H6("Tipping Point Weights", className="fw-bold mb-2 small"),
            dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Sector", className="small"),
                    html.Th("Tipping Point", className="small"),
                    html.Th("Status", className="small"),
                    html.Th("Climate Wt", className="small text-end"),
                    html.Th("Prox. Mult", className="small text-end"),
                ])),
                html.Tbody(progress_weights_rows),
            ], bordered=True, hover=True, size="sm",
               style={"fontSize": "0.8rem"}),
        ]),
    ])

    # ---------------------------------------------------------------
    # Collapsible breakdown: Climate Risk (Temperature Projection)
    # ---------------------------------------------------------------
    danger_collapse = html.Details([
        html.Summary(
            "Climate Risk -- temperature projection breakdown (click to expand)",
            className="small text-primary mb-2",
            style={"cursor": "pointer"},
        ),
        html.Div([
            html.P([
                html.Strong("Method: "),
                "S-curve temperature projection. Maps technology adoption curves to "
                "sector-by-sector fossil fuel displacement, then converts cumulative "
                "emissions to temperature via TCRE (IPCC AR6).",
            ], className="small mb-2"),
            dbc.Table([
                html.Tbody([
                    html.Tr([
                        html.Td("S-curve peak temperature", className="small"),
                        html.Td(
                            html.Strong(f"{danger_bd.get('peak_temp_c', '?')}°C in {danger_bd.get('peak_year', '?')}"),
                            className="small text-end",
                        ),
                    ]),
                    html.Tr([
                        html.Td("Scenario range", className="small"),
                        html.Td(
                            f"{danger_bd.get('fast_scenario_peak', '?')}–{danger_bd.get('slow_scenario_peak', '?')}°C",
                            className="small text-end",
                        ),
                    ]),
                    html.Tr([
                        html.Td("Temperature in 2050", className="small"),
                        html.Td(f"{danger_bd.get('temp_2050_c', '?')}°C", className="small text-end"),
                    ]),
                    html.Tr([
                        html.Td("Overshoot above 1.5°C target", className="small"),
                        html.Td(
                            html.Strong(
                                f"+{danger_bd.get('overshoot_above_15', '?')}°C",
                                style={"color": RED},
                            ),
                            className="small text-end",
                        ),
                    ]),
                    html.Tr([
                        html.Td("Overshoot above 2.0°C guardrail", className="small"),
                        html.Td(
                            html.Strong(
                                f"+{danger_bd.get('overshoot_above_20', '?')}°C",
                                style={"color": YELLOW if danger_bd.get('overshoot_above_20', 0) > 0 else GREEN},
                            ),
                            className="small text-end",
                        ),
                    ]),
                    html.Tr([
                        html.Td("Improvement vs current policies (3.1°C)", className="small"),
                        html.Td(
                            html.Strong(
                                f"-{danger_bd.get('improvement_vs_policies', '?')}°C",
                                style={"color": GREEN},
                            ),
                            className="small text-end",
                        ),
                    ]),
                ]),
            ], bordered=False, size="sm", className="mb-2"),
            html.P([
                html.Strong("Scoring rule: "),
                danger_bd.get("scoring_rule", ""),
            ], className="small text-muted"),
        ]),
    ])

    # ---------------------------------------------------------------
    # Methodology note
    # ---------------------------------------------------------------
    methodology_note = dbc.Alert([
        html.I(className="bi bi-info-circle me-2"),
        html.Strong("Methodology note: "),
        html.Div([
            html.P([
                "This meter uses a ",
                html.Strong("dual-scoring approach"),
                " that weighs clean energy progress against climate risk. "
                "The ",
                html.Strong("Progress Score"),
                " (0-100) combines emissions-weighted tipping points crossed (40 pts), "
                "technology and investment momentum (30 pts), and the gap to climate "
                "targets (30 pts).",
            ], className="mb-2"),
            html.P([
                "The ",
                html.Strong("Climate Risk Score"),
                " (0-100) is derived from the ",
                dcc.Link("S-curve temperature projection", href="/trajectories"),
                ": a bottom-up model that maps technology adoption curves to sector-by-sector "
                "fossil fuel displacement, then converts cumulative emissions to temperature "
                "via TCRE (IPCC AR6). The scoring rule: 1.5\u00b0C = 0 (Paris met), "
                "2.0\u00b0C = 50, 3.1\u00b0C = 100 (current policies).",
            ], className="mb-2"),
            html.P([
                "The ",
                html.Strong("Net Score = Progress - (Risk \u00d7 0.5)"),
                ". The 0.5 factor means maximum risk reduces but does not eliminate "
                "progress \u2014 reflecting that the dashboard tracks whether our "
                "clean energy response is fast enough, not providing a final judgment.",
            ], className="mb-2"),
            html.P([
                html.Em(
                    "This score is thought-provoking, not definitive. "
                    "All inputs and weights are transparent in the breakdowns above. "
                ),
                "See the ",
                dcc.Link("Methodology page", href="/methodology"),
                " for full data source documentation.",
            ], className="mb-0"),
        ]),
    ], color="info", className="mt-3 small")

    # ---------------------------------------------------------------
    # Assemble the card
    # ---------------------------------------------------------------
    return dbc.Card([
        dbc.CardHeader([
            html.H4([
                html.I(className="bi bi-speedometer2 me-2"),
                "Optimism Meter",
            ], className="mb-0 fw-bold"),
        ]),
        dbc.CardBody([
            # Dual bars + net score
            dbc.Row([
                dbc.Col([
                    progress_bar,
                    danger_bar,
                ], md=7, lg=8),
                dbc.Col([
                    net_display,
                    scenario_badges,
                ], md=5, lg=4),
            ]),

            html.Hr(className="my-3"),

            # Collapsible breakdowns
            progress_collapse,
            html.Div(className="mb-2"),
            danger_collapse,

            # Methodology note
            methodology_note,
        ]),
    ], className="mb-4 shadow-sm")


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

def layout(**kwargs):
    return html.Div([
        dbc.Container([

            # Header
            dbc.Row([
                dbc.Col([
                    html.H1(
                        "Tipping Points",
                        className="display-5 fw-bold mt-4 mb-1",
                    ),
                    html.P(
                        "Tracking the clean energy thresholds that, once crossed, "
                        "trigger self-reinforcing adoption cascades. Based on research "
                        "from RMI, RethinkX, Lenton et al. (Exeter), and the broader "
                        "S-curve and technology disruption literature.",
                        className="lead text-muted mb-1",
                    ),
                    html.P([
                        "Key insight: technologies reaching ",
                        html.Strong("5\u201310% market share"),
                        " typically accelerate rapidly toward 50%+. Many clean energy "
                        "technologies have already crossed this threshold.",
                    ], className="text-muted mb-3"),
                ], md=10, lg=9),
            ]),

            html.Hr(),

            # Section 1: Checklist (Accordion by sector)
            _build_checklist_section(),

            # Section 2: S-Curve Tracker
            _build_scurve_section(),

            # Section 3: Countdown
            _build_countdown_section(),

            # Section 4: Optimism Meter
            _build_optimism_section(),

            # Footer note
            dbc.Row([
                dbc.Col([
                    html.Hr(),
                    html.P([
                        html.Strong("A note on framing: "),
                        "Research from the Yale Program on Climate Change Communication "
                        "finds that ",
                        html.Em("constructive hope"),
                        " (seeing real progress and others acting) increases engagement "
                        "and policy support, while ",
                        html.Em("false hope"),
                        " (believing technology alone will save us) decreases it. "
                        "This page aims to pair progress with honest assessment of "
                        "what still needs to happen. The energy transition is real and "
                        "accelerating \u2014 and it is not yet fast enough.",
                    ], className="text-muted small mb-4"),
                ], md=10, lg=9),
            ]),

        ], fluid=True, className="px-3 px-md-4"),
    ])
