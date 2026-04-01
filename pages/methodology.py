"""
methodology.py — Methodology & Data Sources page.

Explains data sources, processing steps, definitions, limitations,
and citations for every metric shown in the dashboard.
"""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/methodology", title="Methodology — Energy Transition Dashboard")


def _source_row(name: str, description: str, url: str, license_: str = "") -> html.Tr:
    """Build a table row for a data source."""
    return html.Tr([
        html.Td(html.Strong(name), className="align-top"),
        html.Td(description, className="small"),
        html.Td(
            html.A(url.replace("https://", "").split("/")[0], href=url, target="_blank")
            if url else "—",
            className="small",
        ),
        html.Td(html.Small(license_), className="small text-muted") if license_ else html.Td("—"),
    ])


def layout(**kwargs):
    return html.Div([
        dbc.Container([

            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("Methodology & Data Sources",
                            className="display-5 fw-bold mt-4 mb-1"),
                    html.P(
                        "This page documents every data source, processing step, "
                        "definition, and limitation behind the Energy Transition Dashboard. "
                        "Transparency about what we know — and don't know — is essential.",
                        className="lead text-muted mb-3",
                    ),
                ], md=10, lg=9),
            ]),

            html.Hr(),

            # ================================================================
            # Section 1: Data Sources
            # ================================================================
            html.H2("Data Sources", className="fw-bold mt-3 mb-3"),

            html.H5("Emissions & Climate", className="fw-bold mt-3 mb-2 text-primary",
                     id="source-emissions-climate"),
            dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Source", style={"width": "18%"}),
                    html.Th("What We Use"),
                    html.Th("URL", style={"width": "15%"}),
                    html.Th("License", style={"width": "10%"}),
                ])),
                html.Tbody([
                    _source_row(
                        "Our World in Data (OWID) — Energy",
                        "Energy consumption, electricity mix, capacity by source, per country/year. "
                        "~129 variables covering 200+ countries.",
                        "https://github.com/owid/energy-data",
                        "CC-BY-4.0",
                    ),
                    _source_row(
                        "OWID — CO₂ and GHG",
                        "CO₂ by fuel type, all GHGs (CH₄, N₂O, F-gases), consumption-based, "
                        "cumulative, per-capita. ~80 variables. Primary backbone for emissions data.",
                        "https://github.com/owid/co2-data",
                        "CC-BY-4.0",
                    ),
                    _source_row(
                        "EDGAR (JRC)",
                        "IPCC AR6 reference dataset for territorial GHG emissions by country and sector "
                        "(CO₂, CH₄, N₂O, F-gases). Used for country-level sectoral breakdown.",
                        "https://edgar.jrc.ec.europa.eu",
                        "Free",
                    ),
                    _source_row(
                        "Global Carbon Budget",
                        "Fossil CO₂ (~37.4 GtCO₂/yr in 2024) and land-use CO₂. "
                        "Carbon budget remaining (CO₂-only, not CO₂e).",
                        "https://globalcarbonbudget.org",
                        "CC-BY-4.0",
                    ),
                    _source_row(
                        "NOAA Global Mean CO₂",
                        "Atmospheric CO₂ concentration — global mean surface product "
                        "(preferred over single-station Mauna Loa).",
                        "https://gml.noaa.gov/ccgg/trends/gl_trend.html",
                        "Public domain",
                    ),
                    _source_row(
                        "UNEP Emissions Gap Report 2024",
                        "Gap between pledges and required reductions. "
                        "Current policies → ~3.1°C warming projection.",
                        "https://www.unep.org/resources/emissions-gap-report-2024",
                        "Free",
                    ),
                ]),
            ], bordered=True, hover=True, responsive=True, size="sm",
                className="mb-4"),

            html.H5("Clean Energy & Capacity", className="fw-bold mt-3 mb-2 text-primary",
                     id="source-clean-energy"),
            dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Source", style={"width": "18%"}),
                    html.Th("What We Use"),
                    html.Th("URL", style={"width": "15%"}),
                    html.Th("License", style={"width": "10%"}),
                ])),
                html.Tbody([
                    _source_row(
                        "Ember Yearly Electricity",
                        "Generation by source, capacity, emissions intensity. "
                        "215 countries, annual updates.",
                        "https://ember-energy.org/data/yearly-electricity-data/",
                        "CC-BY-4.0",
                    ),
                    _source_row(
                        "IRENA Renewable Energy Statistics",
                        "Installed electricity capacity (MW) by technology and country, "
                        "2000–2024. Primary source for the deployment tracker and capacity KPIs. "
                        "224 countries, 21 technologies including solar PV, onshore/offshore wind, "
                        "hydropower, geothermal, and biomass.",
                        "https://pxweb.irena.org/pxweb/en/IRENASTAT/",
                        "Free",
                    ),
                    _source_row(
                        "IEA Net Zero by 2050",
                        "NZE 2050 renewable capacity milestones used as targets in the "
                        "deployment tracker chart.",
                        "https://www.iea.org/reports/net-zero-by-2050",
                        "Free report",
                    ),
                ]),
            ], bordered=True, hover=True, responsive=True, size="sm",
                className="mb-4"),

            html.H5("Costs & Finance", className="fw-bold mt-3 mb-2 text-primary",
                     id="source-costs-finance"),
            dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Source", style={"width": "18%"}),
                    html.Th("What We Use"),
                    html.Th("URL", style={"width": "15%"}),
                    html.Th("License", style={"width": "10%"}),
                ])),
                html.Tbody([
                    _source_row(
                        "IRENA Power Generation Costs",
                        "Global LCOE by technology (solar PV, onshore/offshore wind). "
                        "Used for the cost revolution chart.",
                        "https://www.irena.org/publications/2024/Sep/Renewable-Power-Generation-Costs-in-2023",
                        "Free",
                    ),
                    _source_row(
                        "BloombergNEF",
                        "Battery pack cost data ($/kWh) for the cost revolution chart.",
                        "https://about.bnef.com/",
                        "Referenced values",
                    ),
                    _source_row(
                        "World Bank Carbon Pricing Dashboard",
                        "ETS and carbon tax data by country. Used for the cost map and "
                        "country-level carbon pricing cards.",
                        "https://carbonpricingdashboard.worldbank.org/",
                        "Free",
                    ),
                    _source_row(
                        "IMF Fossil Fuel Subsidies",
                        "Explicit + implicit subsidies (including health externality component). "
                        "170+ countries. $7T/yr estimate (2022) includes unpaid externalities.",
                        "https://www.imf.org/en/Topics/climate-change/energy-subsidies",
                        "Free",
                    ),
                    _source_row(
                        "IEA World Energy Investment 2025",
                        "Clean vs fossil fuel investment flows by region (2015-2025). "
                        "Used for investment section on homepage and country pages.",
                        "https://www.iea.org/reports/world-energy-investment-2025",
                        "Free data file",
                    ),
                    _source_row(
                        "IEA Fossil Fuel Subsidies Database",
                        "Explicit fossil fuel subsidies by country and product (2010-2024). "
                        "48 countries covered. Used for subsidies charts and country profiles.",
                        "https://www.iea.org/data-and-statistics/data-product/fossil-fuel-subsidies-database",
                        "Free data file",
                    ),
                ]),
            ], bordered=True, hover=True, responsive=True, size="sm",
                className="mb-4"),

            html.H5("Health & Environmental Justice", className="fw-bold mt-3 mb-2 text-primary",
                     id="source-health-ej"),
            dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Source", style={"width": "18%"}),
                    html.Th("What We Use"),
                    html.Th("URL", style={"width": "15%"}),
                    html.Th("License", style={"width": "10%"}),
                ])),
                html.Tbody([
                    _source_row(
                        "World Bank WDI",
                        "PM2.5 annual mean exposure (EN.ATM.PM25.MC.M3), "
                        "electricity access (EG.ELC.ACCS.ZS), "
                        "clean cooking access (EG.CFT.ACCS.ZS). Country-level time series.",
                        "https://data.worldbank.org/",
                        "CC-BY-4.0",
                    ),
                    _source_row(
                        "Lelieveld et al. 2023 (BMJ)",
                        "Global fossil fuel air pollution mortality: ~5.13M excess deaths/yr "
                        "(out of 8.34M total from PM2.5 + O₃). Uses atmospheric chemistry model "
                        "with satellite-derived PM2.5 observations. Most recent authoritative estimate.",
                        "https://doi.org/10.1136/bmj-2023-077784",
                        "Open Access",
                    ),
                    _source_row(
                        "Vohra et al. 2021 (Env. Research)",
                        "Global mortality from fossil fuel PM2.5: ~8.7M deaths/yr (2018). "
                        "Uses GEOS-Chem model with updated concentration-response functions. "
                        "Upper bound of current estimates.",
                        "https://doi.org/10.1016/j.envres.2021.110754",
                        "Open Access",
                    ),
                    _source_row(
                        "GBD 2023 / IHME",
                        "Global Burden of Disease Study 2023 — country-level deaths "
                        "attributable to ambient PM2.5 and household air pollution (solid fuels), "
                        "separately, 1990–2023. Downloaded from the GBD Results Tool. "
                        "Citation: GBD 2023 Collaborative Network, IHME, 2024.",
                        "https://vizhub.healthdata.org/gbd-results/",
                        "Free (registration)",
                    ),
                    _source_row(
                        "OWID — Deaths per TWh",
                        "Comparative safety of energy sources. Derived from lifecycle studies "
                        "(Markandya & Wilkinson 2007; Sovacool 2008).",
                        "https://ourworldindata.org/safest-sources-of-energy",
                        "CC-BY-4.0",
                    ),
                    _source_row(
                        "Lancet Countdown 2025",
                        "Indicator 1.1.1: Heatwave days attributable to climate change "
                        "(country-level, 2020–2024). Indicator 1.1.5: Heat-related mortality "
                        "(global, ~600K deaths/yr average 2019–2021). Separate from air pollution.",
                        "https://lancetcountdown.org/2025-report/",
                        "Open access",
                    ),
                ]),
            ], bordered=True, hover=True, responsive=True, size="sm",
                className="mb-4"),

            html.H5("Climate Impacts & Vulnerability", className="fw-bold mt-3 mb-2 text-primary",
                     id="source-climate-impacts"),
            dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Source", style={"width": "18%"}),
                    html.Th("What We Use"),
                    html.Th("URL", style={"width": "15%"}),
                    html.Th("License", style={"width": "10%"}),
                ])),
                html.Tbody([
                    _source_row(
                        "EM-DAT (CRED / UCLouvain)",
                        "Climate-related disaster data (floods, storms, droughts, extreme "
                        "temperatures, wildfires) aggregated by country-year since 2000. "
                        "Used for the Damages map layer showing cumulative deaths and "
                        "economic losses from climate disasters.",
                        "https://www.emdat.be/",
                        "Non-commercial",
                    ),
                    _source_row(
                        "ND-GAIN Country Index",
                        "Climate vulnerability and readiness scores by country (1995-2023). "
                        "Vulnerability combines exposure, sensitivity, and adaptive capacity "
                        "across food, water, health, infrastructure, habitat, and ecosystems. "
                        "Used for the Vulnerability map layer.",
                        "https://gain.nd.edu/our-work/country-index/",
                        "CC-BY-4.0",
                    ),
                    _source_row(
                        "IEA CCUS Projects Database 2026",
                        "1,110 CCS/CCUS projects globally (announcements as of Feb 2026). "
                        "Project-level data on capacity, status, sector, and timeline. "
                        "Used on the Predictions page to show actual CCS pipeline vs projections.",
                        "https://www.iea.org/data-and-statistics/data-product/ccus-projects-database",
                        "Free IEA account",
                    ),
                ]),
            ], bordered=True, hover=True, responsive=True, size="sm",
                className="mb-4"),

            html.H5("Scenarios & Predictions", className="fw-bold mt-3 mb-2 text-primary",
                     id="source-scenarios-predictions"),
            dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Source", style={"width": "18%"}),
                    html.Th("What We Use"),
                    html.Th("URL", style={"width": "15%"}),
                    html.Th("License", style={"width": "10%"}),
                ])),
                html.Tbody([
                    _source_row(
                        "IIASA AR6 Scenario Explorer v1.1",
                        "IPCC AR6 scenario database. Percentile envelopes (p10/p25/p50/p75/p90) "
                        "computed from Ch.3-vetted scenarios: C1 (97), C3 (311), C5 (212), "
                        "C7 (164), C8 (29). Variable: Emissions|CO2 (Mt CO2/yr → Gt). "
                        "Citation: Byers et al. (2022), doi:10.5281/zenodo.5886911.",
                        "https://data.ece.iiasa.ac.at/ar6/",
                        "CC-BY 4.0",
                    ),
                    _source_row(
                        "Burke, Hsiang & Miguel (2015)",
                        "Country-level GDP per capita projections under RCP8.5/SSP5 with and "
                        "without climate change. Used for climate damages map (% GDP loss at "
                        "2050 and 2080). Shows disproportionate impacts on tropical/developing "
                        "nations — central to the EJ narrative.",
                        "https://doi.org/10.1038/nature15725",
                        "Published",
                    ),
                    _source_row(
                        "Way et al. 2022, Joule",
                        "Empirically grounded technology cost forecasts and the energy transition. "
                        "Used for LCOE projection context. Capacity projections compiled from "
                        "Hoekstra & Steinbuch 2017 and IEA WEO editions directly.",
                        "https://doi.org/10.1016/j.joule.2022.08.009",
                        "Published",
                    ),
                    _source_row(
                        "IEA WEO Editions (2002–2022)",
                        "New Policies / STEPS scenario capacity projections. "
                        "Used for the fan chart of historical forecast errors.",
                        "https://www.iea.org/reports/world-energy-outlook-2023",
                        "Free IEA account",
                    ),
                ]),
            ], bordered=True, hover=True, responsive=True, size="sm",
                className="mb-4"),

            html.Hr(),

            # ================================================================
            # Section 2: Key Definitions
            # ================================================================
            html.H2("Key Definitions", className="fw-bold mt-3 mb-3"),

            dbc.Accordion([
                dbc.AccordionItem([
                    html.P([
                        "Total GHG emissions include CO₂ (from fossil fuels and land use), "
                        "methane (CH₄), nitrous oxide (N₂O), and fluorinated gases (F-gases), "
                        "expressed as CO₂ equivalents (CO₂e) using ", html.Strong("AR6 GWP100"),
                        " values.",
                    ], className="small"),
                    html.P([
                        html.Strong("GWP100 conversion factors (AR6): "),
                        "CO₂ = 1, CH₄ = 27.9 (fossil: 29.8 including CO₂ oxidation), "
                        "N₂O = 273. F-gases vary (HFC-134a = 1,526).",
                    ], className="small"),
                    html.P(
                        "When we report 'fossil CO₂', this is combustion and industrial "
                        "process emissions only — not land-use change.",
                        className="small text-muted",
                    ),
                ], title="GHG Emissions & CO₂e"),

                dbc.AccordionItem([
                    html.P([
                        "We always specify whether a percentage refers to share of ",
                        html.Strong("electricity generation"),
                        " (~30% globally from renewables) or share of ",
                        html.Strong("total final energy consumption"),
                        " (~13% globally). These are very different metrics.",
                    ], className="small"),
                    html.P(
                        "Electricity is roughly 20% of total final energy consumption. "
                        "Transport, industrial heat, and buildings account for the rest.",
                        className="small text-muted",
                    ),
                ], title="Renewable Share: Electricity vs Total Energy"),

                dbc.AccordionItem([
                    html.P([
                        "Levelized Cost of Energy (LCOE) is the average net present cost of "
                        "electricity generation for a new plant over its lifetime. Values shown "
                        "are ", html.Strong("global capacity-weighted averages"), " for new "
                        "installations, adjusted to 2025 USD (from IRENA's native 2022 USD "
                        "using CPI-U, factor \u22481.09).",
                    ], className="small"),
                    html.P([
                        html.Strong("Important limitations: "),
                        "LCOE does not capture system integration costs (grid upgrades, "
                        "backup capacity, storage), financing conditions by country, or "
                        "value deflation from variable generation profiles.",
                    ], className="small text-muted"),
                ], title="LCOE (Levelized Cost of Energy)"),

                dbc.AccordionItem([
                    html.P([
                        "This dashboard reports ", html.Strong("fossil fuel PM2.5 deaths"),
                        " as a range (1.3\u20138.7M/yr) reflecting three peer-reviewed methodologies:"
                    ], className="small"),
                    html.Ul([
                        html.Li([
                            html.Strong("McDuffie et al. 2021 (~1.3M): "),
                            "GBD sector attribution approach. Assigns ~33% of GBD\u2019s "
                            "~4.9M total ambient PM2.5 deaths to fossil fuel combustion. "
                            "This is a single cross-sectional estimate (2017 data). The time series "
                            "in the chart applies the 33% fraction to GBD\u2019s annual totals "
                            "\u2014 an approximation, as the true fraction may vary year-to-year.",
                        ], className="small"),
                        html.Li([
                            html.Strong("Lelieveld et al. 2023 (~5.1M): "),
                            "Atmospheric chemistry model (EMAC) with satellite-derived PM2.5. "
                            "Counts all PM2.5 + ozone deaths from fossil sources. Published in BMJ.",
                        ], className="small"),
                        html.Li([
                            html.Strong("Vohra et al. 2021 (~8.7M): "),
                            "Uses GEOS-Chem model with updated concentration-response functions "
                            "(GEMM). Upper bound of current estimates.",
                        ], className="small"),
                    ]),
                    html.P([
                        "The wide range is due to different concentration-response functions "
                        "and source attribution methods \u2014 not sampling uncertainty within a "
                        "single study. GBD\u2019s ~4.9M total ambient PM2.5 (all sources) is a ",
                        html.Strong("separate metric"),
                        " from the fossil-fuel-specific estimates above.",
                    ], className="small text-muted"),
                ], title="Health: Fossil Fuel PM2.5 Deaths"),

                dbc.AccordionItem([
                    html.P([
                        "IPCC scenario categories classify mitigation pathways by end-of-century "
                        "temperature outcome. We show three:",
                    ], className="small"),
                    html.Ul([
                        html.Li([
                            html.Strong("C1 (1.5°C-compatible): "),
                            "Limits warming to 1.5°C with >50% probability by 2100. "
                            "Most C1 scenarios involve temperature ", html.Em("overshoot"),
                            " before returning to 1.5°C via large-scale CDR (8–10 GtCO₂/yr "
                            "by 2050). Current CDR capacity: ~2 GtCO₂/yr.",
                        ], className="small"),
                        html.Li([
                            html.Strong("C3 (2°C-compatible): "),
                            "Limits warming to 2°C with >67% probability.",
                        ], className="small"),
                        html.Li([
                            html.Strong("C5 (2.5°C-compatible): "),
                            "Limits warming to ~2.5°C. Current policies (~3.1°C) exceed this.",
                        ], className="small"),
                    ]),
                    dbc.Alert([
                        html.Strong("Data source: "),
                        "Scenario envelopes computed from the full IIASA AR6 Scenario Explorer "
                        "v1.1 database (Byers et al. 2022, ",
                        html.A("doi:10.5281/zenodo.5886911",
                               href="https://doi.org/10.5281/zenodo.5886911",
                               target="_blank"),
                        "). Percentiles (p10/p25/p50/p75/p90) calculated from Ch.3-vetted "
                        "scenarios only. Variable: net CO₂ emissions (Emissions|CO2).",
                    ], color="info", className="small py-2"),
                ], title="IPCC Scenario Categories (C1, C3, C5, C7, C8)"),

                dbc.AccordionItem([
                    html.P([
                        "Deaths per TWh estimates are derived from lifecycle analysis studies "
                        "with heterogeneous methodologies (Markandya & Wilkinson 2007; "
                        "Sovacool 2008; GBD-based OWID estimates). Key values: "
                        "Coal ~24.6, Oil ~18.4, Gas ~2.8, Biomass ~4.5, "
                        "Nuclear ~0.07, Wind ~0.04, Solar ~0.02, Hydro ~0.02 deaths per TWh.",
                    ], className="small"),
                    html.P([
                        html.Strong("These are comparative orders of magnitude only — "),
                        "not precision mortality rates. Uncertainty spans an order of magnitude "
                        "for some sources. Coal estimate dominated by older Asian plants; "
                        "modern coal rates are lower.",
                    ], className="small text-muted"),
                ], title="Deaths per TWh (Energy Source Safety)"),

                dbc.AccordionItem([
                    html.P([
                        "Carbon prices shown use the headline effective rate for each country's "
                        "primary pricing scheme — either the ETS market price or statutory "
                        "carbon tax rate, whichever is higher. ",
                        html.Strong("Gray countries on the map have no national carbon price."),
                    ], className="small"),
                    html.P(
                        "Data source: World Bank Carbon Pricing Dashboard 2023. "
                        "Sub-national or sectoral schemes (e.g., RGGI in the US, "
                        "Tokyo ETS in Japan) are not captured in the national figure.",
                        className="small text-muted",
                    ),
                ], title="Carbon Pricing"),
            ], start_collapsed=True, className="mb-4"),

            html.Hr(),

            # ================================================================
            # Section 3: Processing Pipeline
            # ================================================================
            html.H2("Data Processing Pipeline", className="fw-bold mt-3 mb-3"),

            html.P(
                "All data goes through a standardized pipeline before display:",
                className="mb-2",
            ),

            html.Ol([
                html.Li([
                    html.Strong("Download: "),
                    "Raw data is fetched from source APIs and CSV files "
                    "(scripts/download_data.py).",
                ], className="small mb-2"),
                html.Li([
                    html.Strong("Process: "),
                    "Country-level time series are standardized to ISO 3166-1 alpha-3 codes, "
                    "unit conversions applied (Mt → Gt, etc.), and missing values handled. "
                    "Each domain has a dedicated script (process_core.py, process_costs.py, "
                    "process_health.py, process_scenarios.py, process_predictions.py).",
                ], className="small mb-2"),
                html.Li([
                    html.Strong("Compute KPIs: "),
                    "Global headline statistics are computed from the processed Parquet files "
                    "and saved to kpis.json (scripts/compute_kpis.py). The homepage reads "
                    "kpis.json directly — no database queries at request time.",
                ], className="small mb-2"),
                html.Li([
                    html.Strong("Display: "),
                    "All Parquet files are pre-loaded into memory at app startup. "
                    "Charts are built with Plotly; interactivity uses Dash clientside "
                    "callbacks where possible to avoid server round-trips.",
                ], className="small mb-2"),
            ], className="mb-3"),

            dbc.Alert([
                html.Strong("Reproducibility: "),
                "All processing scripts are in the scripts/ directory. "
                "Running them in order regenerates every data file and KPI from "
                "raw downloads. The dashboard never modifies source data.",
            ], color="info", className="small py-2 mb-4"),

            html.Hr(),

            # ================================================================
            # Section 4: Known Limitations
            # ================================================================
            html.H2("Known Limitations & Caveats", className="fw-bold mt-3 mb-3"),

            html.Ul([
                html.Li([
                    html.Strong("Scenario data from IIASA AR6 database: "),
                    "IPCC scenario envelopes are computed from the full Ch.3-vetted IIASA "
                    "AR6 Scenario Explorer v1.1 (Byers et al. 2022). C1: 97 scenarios, "
                    "C3: 311, C5: 212, C7: 164, C8: 29. Not all scenarios report values "
                    "for all years, so sample sizes vary by time period.",
                ], className="small mb-2"),
                html.Li([
                    html.Strong("GDP damage projections are model-dependent: "),
                    "Climate damage estimates from Burke et al. (2015) use a single "
                    "empirical model relating temperature to GDP growth. Results under "
                    "RCP8.5/SSP5 represent a high-emissions scenario. Actual damages "
                    "depend on adaptation, policy, and model assumptions.",
                ], className="small mb-2"),
                html.Li([
                    html.Strong("IEA NZE milestones are approximate: "),
                    "Renewable capacity milestones for the deployment tracker are based on "
                    "published IEA Net Zero by 2050 report figures, not the full downloadable "
                    "dataset (which requires a free IEA account).",
                ], className="small mb-2"),
                html.Li([
                    html.Strong("GBD mortality data requires registration: "),
                    "Country-level air pollution mortality (deaths attributable to ambient "
                    "PM2.5 and household air pollution) requires a specific GBD query for "
                    "risk factor 'Ambient particulate matter pollution'. The bulk GBD 2023 "
                    "download contains disease outcomes, not risk factor attributions. "
                    "Global reference values (~4M and ~3.2M/yr) are from GBD 2019.",
                ], className="small mb-2"),
                html.Li([
                    html.Strong("Investment data is regional, not country-level: "),
                    "Clean energy investment data from the IEA WEI 2025 data file is available "
                    "at the global and regional level (11 regions) but not per country. "
                    "Country pages show their region's investment trend for context.",
                ], className="small mb-2"),
                html.Li([
                    html.Strong("Carbon price reflects national schemes only: "),
                    "Sub-national carbon pricing (e.g., California cap-and-trade, RGGI) "
                    "is not captured in the national figure.",
                ], className="small mb-2"),
                html.Li([
                    html.Strong("Capacity data coverage: "),
                    "Renewable capacity data comes directly from IRENA (224 countries, "
                    "2000–2024). Some smaller territories may have gaps in early years.",
                ], className="small mb-2"),
                html.Li([
                    html.Strong("No avoided-deaths calculations: "),
                    "This dashboard does not calculate avoided deaths from renewables "
                    "deployment. Such calculations require the EPA COBRA/AVERT pipeline (US) "
                    "or careful per-country methodology. We present the current health burden "
                    "as context instead.",
                ], className="small mb-2"),
            ], className="mb-4"),

            html.Hr(),

            # ================================================================
            # Section 5: Citation
            # ================================================================
            html.H2("How to Cite", className="fw-bold mt-3 mb-3"),

            dbc.Card([
                dbc.CardBody([
                    html.P(
                        "Energy Transition Dashboard. 2024–2025. "
                        "Data sources listed on this page.",
                        className="small mb-0 fst-italic",
                    ),
                ]),
            ], className="mb-4 border-primary"),

        ], fluid=False),
    ])
