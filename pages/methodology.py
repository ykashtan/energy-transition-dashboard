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
            # Section 2: How the Numbers Are Calculated
            # ================================================================
            html.H2("How the Numbers Are Calculated", className="fw-bold mt-3 mb-3"),

            html.P(
                "This section documents the specific calculations, unit conversions, "
                "aggregation methods, and judgement calls behind every metric in the "
                "dashboard. Where methodological choices could materially affect "
                "interpretation, we flag them explicitly.",
                className="text-muted mb-4",
            ),

            # --- 2a: Emissions & Climate ---
            html.H4("Emissions & Climate", className="fw-bold mt-4 mb-2 text-primary"),

            html.H6("CO\u2082 vs GHG: two different metrics", className="fw-bold mt-3"),
            html.P([
                "We report two distinct emissions metrics, and they are ",
                html.Strong("never conflated"), ":",
            ], className="small"),
            html.Ul([
                html.Li([
                    html.Strong("Fossil CO\u2082 (GtCO\u2082/yr): "),
                    "Combustion and industrial process emissions only. Does not include "
                    "land-use change. Source: Global Carbon Budget via Our World in Data.",
                ], className="small"),
                html.Li([
                    html.Strong("Total GHG (GtCO\u2082e/yr): "),
                    "All greenhouse gases (CO\u2082, CH\u2084, N\u2082O, F-gases) converted to "
                    "CO\u2082 equivalents using AR6 GWP100 values. "
                    "Source: EDGAR + PRIMAP-hist via Our World in Data.",
                ], className="small"),
            ]),
            html.P([
                html.Strong("GWP100 conversion factors (IPCC AR6): "),
                "CO\u2082 = 1, CH\u2084 = 27.9 (fossil methane = 29.8 including CO\u2082 from "
                "oxidation), N\u2082O = 273. F-gases vary widely (e.g., HFC-134a = 1,526).",
            ], className="small"),
            dbc.Alert([
                html.Strong("Judgement call \u2014 GWP100 vs GWP20: "),
                "We use GWP100 (the IPCC standard), which weights methane at 27.9\u00d7 CO\u2082. "
                "GWP20 weights methane at 80\u00d7, better reflecting its short-term warming "
                "potency. The choice of metric materially affects how 'important' methane "
                "appears relative to CO\u2082. We follow the IPCC convention but note that "
                "short-lived climate pollutant strategies may warrant GWP20 framing.",
            ], color="warning", className="small py-2"),

            html.H6("Country aggregation", className="fw-bold mt-3"),
            html.P(
                "Global totals are computed by summing across all countries with valid "
                "3-letter ISO codes. OWID aggregate rows (e.g., 'World', 'EU-27', "
                "'High-income countries') are excluded to prevent double-counting. "
                "A year is only considered valid if >100 countries report data.",
                className="small",
            ),

            html.H6("Data quality tiers", className="fw-bold mt-3"),
            html.P([
                html.Strong("Annex I countries "), "(\u223c42 nations) have mandatory MRV "
                "(monitoring, reporting, verification) under the UNFCCC, yielding high-confidence "
                "data. ",
                html.Strong("Non-Annex I countries "), "report voluntarily; China\u2019s coal "
                "statistics have been substantially revised in past years, and Brazil/Indonesia "
                "LULUCF estimates can vary 2\u00d7 across datasets.",
            ], className="small"),

            html.H6("Temperature anomaly", className="fw-bold mt-3"),
            html.P([
                "Global mean temperature uses HadCRUT5, rebased from its native 1961\u20131990 "
                "baseline to the IPCC standard ", html.Strong("1850\u20131900 baseline"),
                " (offset: approximately +0.36\u00b0C). ",
                "NASA GISTEMP uses 1951\u20131980; NOAA uses 1901\u20132000. The choice of "
                "baseline shifts absolute values by 0.1\u20130.2\u00b0C, which matters at the "
                "1.5\u00b0C threshold.",
            ], className="small"),

            html.H6("Atmospheric CO\u2082 concentration", className="fw-bold mt-3"),
            html.P(
                "We use the NOAA global mean surface CO\u2082 product, not the single-station "
                "Mauna Loa record. The global mean is slightly lower than Mauna Loa "
                "(\u223c1\u20132 ppm) because it averages across the hemisphere.",
                className="small",
            ),

            # --- 2b: Clean Energy & Capacity ---
            html.H4("Clean Energy & Capacity", className="fw-bold mt-4 mb-2 text-primary"),

            html.H6("Renewable share: two denominators", className="fw-bold mt-3"),
            html.P([
                "This is the single most important labelling choice on the dashboard. "
                "We always specify whether a percentage refers to share of ",
                html.Strong("electricity generation"), " (\u223c30% globally from renewables) "
                "or share of ", html.Strong("total final energy consumption"),
                " (\u223c13% globally). These differ by a factor of \u223c2.3\u00d7 because "
                "electricity is only \u223c20% of total final energy; the rest is transport fuel, "
                "industrial heat, and building heating.",
            ], className="small"),
            dbc.Alert([
                html.Strong("Why this matters: "),
                "A headline like \u201c30% renewable\u201d (electricity) vs \u201c13% renewable\u201d "
                "(total energy) describes the same world but gives very different impressions "
                "of progress. We label every instance explicitly.",
            ], color="warning", className="small py-2"),

            html.H6("Installed capacity (GW)", className="fw-bold mt-3"),
            html.P([
                "Primary source: ", html.Strong("IRENA Renewable Energy Statistics"),
                " (224 countries, 21 technologies, 2000\u20132024). We extract "
                "\u201cElectricity Installed Capacity (MW)\u201d rows with \u201cAll\u201d "
                "grid connection type, then convert MW \u2192 GW (\u00f71000). "
                "Solar = PV + thermal. Wind = onshore + offshore. "
                "Country names are mapped to ISO3 codes via the country_converter library.",
            ], className="small"),

            html.H6("Deployment tracker: on-track logic", className="fw-bold mt-3"),
            html.P([
                "The deployment tracker compares actual renewable capacity growth against "
                "IEA Net Zero by 2050 milestones. We compute a 4-year rolling average "
                "compound annual growth rate (CAGR) from actual data and compare it to "
                "the CAGR required to reach the next NZE milestone.",
            ], className="small"),
            dbc.Alert([
                html.Strong("Judgement call \u2014 on-track threshold: "),
                "We classify deployment as \u201con track\u201d if the current CAGR is "
                "\u226580% of the required rate. This 80% threshold is a pragmatic choice; "
                "there is no standard definition of \u201con track.\u201d IEA NZE milestones "
                "are approximate figures from published reports, not the full downloadable "
                "dataset.",
            ], color="warning", className="small py-2"),

            html.H6("Electricity generation by source", className="fw-bold mt-3"),
            html.P(
                "Generation data (TWh/yr) comes from Our World in Data, which synthesizes "
                "Ember Yearly Electricity (primary for recent years) and BP/EI Statistical "
                "Review (historical). Year-over-year percent changes are computed as "
                "(current \u2212 previous) / |previous| \u00d7 100.",
                className="small",
            ),

            # --- 2c: Costs & Finance ---
            html.H4("Costs & Finance", className="fw-bold mt-4 mb-2 text-primary"),

            html.H6("LCOE (Levelized Cost of Energy)", className="fw-bold mt-3"),
            html.P([
                "Values shown are ", html.Strong("global capacity-weighted averages"),
                " for newly commissioned utility-scale projects. Primary source: "
                "IRENA Renewable Power Generation Costs 2023 (solar, onshore/offshore wind). "
                "Coal and gas CCGT from IEA Projected Costs of Generating Electricity 2020. "
                "Battery costs from BloombergNEF Lithium-ion Battery Price Survey 2023.",
            ], className="small"),
            html.P([
                html.Strong("Currency adjustment: "),
                "All values converted from source dollar-years to 2025 USD using "
                "CPI-U adjustment factor of \u22481.092 (from IRENA\u2019s native 2022 USD). "
                "This is a fixed factor, not a forecast.",
            ], className="small"),
            dbc.Alert([
                html.Strong("Uncertainty \u2014 gas LCOE: "),
                "There is no single authoritative annual global gas CCGT LCOE series. "
                "Fuel costs represent 60\u201370% of gas LCOE and vary dramatically by region "
                "(US Henry Hub vs European TTF vs Asian LNG spot). Our values are approximate "
                "global benchmarks from IEA and IRENA, not precision estimates. Nuclear LCOE "
                "is similarly contested across studies (Lazard vs IEA vs national estimates).",
            ], color="warning", className="small py-2"),

            html.H6("Investment data", className="fw-bold mt-3"),
            html.P([
                "Source: IEA World Energy Investment 2025. ",
                html.Strong("Clean energy"), " includes: renewables, nuclear, energy efficiency, "
                "electricity networks, battery storage, and EVs. ",
                html.Strong("Fossil fuel"), " includes: oil & gas upstream, refining, coal mine "
                "development, and fossil fuel power generation. "
                "All values in 2024 real USD (market exchange rates). "
                "Data is available at the global and regional level (11 regions) "
                "but not per country.",
            ], className="small"),

            html.H6("Carbon pricing", className="fw-bold mt-3"),
            html.P(
                "Carbon prices are a 2023 snapshot from the World Bank Carbon Pricing Dashboard "
                "and ICAP ETS Status Report. We use the headline effective rate for each "
                "country\u2019s primary scheme (ETS market price or statutory tax rate, "
                "whichever is higher). Sub-national or sectoral schemes "
                "(e.g., California cap-and-trade, Tokyo ETS, RGGI) are not captured.",
                className="small",
            ),

            # --- 2d: Fossil Fuel Subsidies ---
            html.H4("Fossil Fuel Subsidies", className="fw-bold mt-4 mb-2 text-primary"),

            html.H6("IMF methodology (per-country chart)", className="fw-bold mt-3"),
            html.P([
                "The per-country subsidies chart uses the ",
                html.Strong("IMF CPAT (Climate Policy Assessment Tool) database"),
                " (2025 update), covering ", html.Strong("186 countries"), ". "
                "This dataset reports both ",
                html.Strong("explicit subsidies"), " (direct price support \u2014 when "
                "consumers pay below the cost of supply) and ",
                html.Strong("implicit subsidies"), " (underpricing of externalities).",
            ], className="small"),
            html.P([
                "Implicit subsidies include four components: ",
                "(1) local air pollution costs (premature mortality from PM2.5/SO\u2082/NO\u2082), "
                "(2) global warming damages (social cost of carbon), "
                "(3) other local externalities (traffic congestion, road damage, accidents), and "
                "(4) forgone consumption tax revenue (below-normal VAT rates on fossil fuels). "
                "All values adjusted to 2025 USD (from IMF\u2019s native 2021 USD "
                "using CPI-U factor \u22481.18).",
            ], className="small"),
            dbc.Alert([
                html.Strong("Why the numbers are so large: "),
                "The IMF\u2019s \u223c$8.7 trillion global estimate (2024, in 2025 USD) is dominated by implicit "
                "subsidies (\u223c85% of the total). These are not cash transfers \u2014 they "
                "represent the economic cost of failing to price externalities. Explicit "
                "subsidies alone total \u223c$750 billion. Whether underpriced "
                "externalities should be called \u201csubsidies\u201d is debated, but the IMF "
                "framework is widely used in policy analysis.",
            ], color="warning", className="small py-2"),

            html.H6("IEA methodology (time series, explicit only)", className="fw-bold mt-3"),
            html.P(
                "The global subsidies time series uses the IEA Fossil Fuel Subsidies Database "
                "(48 countries, 2010\u20132024), which measures only explicit consumption "
                "subsidies via the price-gap method (comparing what consumers pay vs. the "
                "full cost of supply). This methodology does not cover the USA or most OECD "
                "nations, whose fossil fuel support comes through production-side tax measures.",
                className="small",
            ),

            dbc.Alert([
                html.Strong("Cross-reference \u2014 shared data with Health and Damages sections: "),
                "The IMF\u2019s implicit subsidies are built from two components that also appear "
                "elsewhere on this dashboard: (1) ", html.Strong("Air pollution mortality"),
                " \u2014 the IMF uses GBD-based country-specific fossil fuel death counts "
                "(\u223c2.6M/yr globally), which are also used on the Health map. These are "
                "higher than McDuffie\u2019s \u223c1.3M because the IMF includes household fossil "
                "fuel pollution and ozone, not just ambient PM2.5. (2) ",
                html.Strong("Climate damages"), " \u2014 the IMF values CO\u2082 at "
                "\u223c$78/tCO\u2082 (2025 USD), applied uniformly globally. "
                "The Damages map instead uses Burke et al.\u2019s country-specific empirical "
                "damage function, which shows much larger losses for tropical countries. "
                "These are complementary approaches, not conflicting ones.",
            ], color="info", className="small py-2"),

            # --- 2e: Health & Environmental Justice ---
            html.H4("Health & Environmental Justice",
                     className="fw-bold mt-4 mb-2 text-primary"),

            html.H6("Fossil fuel PM2.5 mortality", className="fw-bold mt-3"),
            html.P(
                "The headline health metric is premature deaths attributable to "
                "fossil fuel combustion PM2.5. We present this as a range "
                "(1.3\u20138.7 million/yr) from three peer-reviewed studies using "
                "different methodologies:",
                className="small",
            ),
            html.Ul([
                html.Li([
                    html.Strong("McDuffie et al. 2021 (\u223c1.3M): "),
                    "Attributes \u223c33% of GBD\u2019s total ambient PM2.5 deaths to fossil "
                    "fuel combustion sectors. Single cross-section (2017). Our time series "
                    "applies this 33% fraction to GBD\u2019s annual totals \u2014 an approximation, "
                    "as the true fraction likely varies year to year.",
                ], className="small"),
                html.Li([
                    html.Strong("Lelieveld et al. 2023 (\u223c5.1M): "),
                    "Atmospheric chemistry model (EMAC) with satellite-derived PM2.5. "
                    "Counts all PM2.5 + ozone deaths from fossil sources. Published in BMJ.",
                ], className="small"),
                html.Li([
                    html.Strong("Vohra et al. 2021 (\u223c8.7M): "),
                    "GEOS-Chem model with updated concentration-response functions (GEMM). "
                    "Upper bound of current estimates.",
                ], className="small"),
            ]),
            dbc.Alert([
                html.Strong("Uncertainty: "),
                "The 7\u00d7 range across studies is due to different concentration-response "
                "functions and source attribution methods, not sampling error within a single "
                "study. GBD\u2019s \u223c4.9M total ambient PM2.5 deaths (all sources, not just "
                "fossil) is a separate metric. We display it alongside the fossil-specific "
                "estimates but never conflate them.",
            ], color="warning", className="small py-2"),

            html.H6("Health map: IMF country-specific death counts", className="fw-bold mt-3"),
            html.P([
                "The world map\u2019s Health layer uses ",
                html.Strong("IMF CPAT country-specific fossil fuel death counts"),
                " (\u223c2.6M/yr globally, 177 countries) rather than McDuffie\u2019s uniform "
                "33% fraction. The IMF estimates are higher because they include household "
                "fossil fuel pollution and ozone mortality in addition to ambient PM2.5. "
                "Both use GBD-based concentration-response functions but with different "
                "source attribution methods. The same IMF death counts underlie the air "
                "pollution component of the IMF fossil fuel subsidy estimates shown in the "
                "Investment & Subsidies section.",
            ], className="small"),

            html.H6("Ambient vs household air pollution", className="fw-bold mt-3"),
            html.P([
                "We report ", html.Strong("ambient PM2.5 deaths"), " (\u223c4M/yr globally, "
                "GBD 2023) and ", html.Strong("household air pollution deaths"),
                " (\u223c3.2M/yr, from solid fuel cooking) as ",
                html.Strong("separate columns that are never summed"), ". "
                "Ambient PM2.5 is directly reduced by electricity decarbonization. "
                "Household air pollution is reduced by clean cooking programs \u2014 a related "
                "but distinct intervention.",
            ], className="small"),
            dbc.Alert([
                html.Strong("Why we keep them separate: "),
                "Summing would overstate the deaths addressable by energy transition alone. "
                "A country that decarbonizes its grid but doesn\u2019t address clean cooking "
                "access would not reduce household air pollution deaths. These require "
                "different policy interventions.",
            ], color="warning", className="small py-2"),

            html.H6("Deaths per TWh by energy source", className="fw-bold mt-3"),
            html.P([
                "Reference values: Coal \u223c24.6, Oil \u223c18.4, Gas \u223c2.8, "
                "Biomass \u223c4.5, Nuclear \u223c0.07, Wind \u223c0.04, Solar \u223c0.02, "
                "Hydro \u223c0.02 deaths per TWh. Source: OWID, based on lifecycle analysis "
                "studies (Markandya & Wilkinson 2007; Sovacool 2008; GBD-derived estimates).",
            ], className="small"),
            dbc.Alert([
                html.Strong("Comparative only \u2014 not precision mortality: "),
                "These rates are derived from heterogeneous methodologies across different "
                "time periods and geographies. Coal estimates are dominated by older Asian "
                "plants; modern coal plants have lower rates. Nuclear estimates are contested "
                "across studies by orders of magnitude. The key insight is the \u223c1000\u00d7 "
                "difference between coal and solar/wind, not the precise values. "
                "We do not use these rates to calculate avoided deaths from specific "
                "deployment scenarios.",
            ], color="warning", className="small py-2"),

            html.H6("Health map metric", className="fw-bold mt-3"),
            html.P([
                "The map\u2019s \u201cHealth\u201d layer shows fossil fuel PM2.5 deaths as a "
                "percentage of all deaths in each country. Calculation: ",
                html.Code(
                    "fossil_fuel_deaths / (population \u00d7 crude_death_rate) \u00d7 100"
                ), ". ",
                "We use a global crude death rate of 8.1 per 1,000/year (WHO 2020 estimate) "
                "as a uniform denominator.",
            ], className="small"),
            dbc.Alert([
                html.Strong("Judgement call \u2014 crude death rate: "),
                "Actual crude death rates range from \u223c2/1000 (young populations, e.g., "
                "UAE) to \u223c15/1000 (aging populations, e.g., Bulgaria). Using a single "
                "global average introduces error at the country level, but avoids the "
                "circularity of using country-specific rates that themselves depend on "
                "pollution exposure.",
            ], color="warning", className="small py-2"),

            html.H6("Heat mortality", className="fw-bold mt-3"),
            html.P(
                "Climate-attributable heat deaths come from the Lancet Countdown 2025 "
                "(Indicator 1.1.5). These are deaths attributable to climate change "
                "(above a counterfactual without warming), distinct from total heat deaths "
                "and from air pollution deaths. Reported separately in the health section.",
                className="small",
            ),

            # --- 2f: Climate Impacts ---
            html.H4("Climate Impacts & Vulnerability",
                     className="fw-bold mt-4 mb-2 text-primary"),

            html.H6("GDP damage projections", className="fw-bold mt-3"),
            html.P([
                "Climate damage estimates use the empirical temperature\u2013GDP relationship "
                "from ", html.Strong("Burke, Hsiang & Miguel (2015, Nature)"),
                ", applied to RCP8.5/SSP5 GDP projections. "
                "The calculation: ",
                html.Code(
                    "pct_gdp_loss = (GDP_no_climate_change \u2212 GDP_with_climate_change) "
                    "/ GDP_no_climate_change \u00d7 100"
                ), ".",
            ], className="small"),
            dbc.Alert([
                html.Strong("Model dependency: "),
                "This is a single empirical model; other damage functions "
                "(Nordhaus, Howard & Sterner, Kalkuhl & Wenz) give different magnitudes. "
                "RCP8.5/SSP5 represents a high-emissions scenario. Results show that "
                "tropical/developing countries face severe losses while some cold/wealthy "
                "countries may see modest gains \u2014 a pattern robust across damage models "
                "but with uncertain magnitudes.",
            ], color="warning", className="small py-2"),
            dbc.Alert([
                html.Strong("Cross-reference \u2014 IMF social cost of carbon: "),
                "The IMF\u2019s fossil fuel subsidy estimates use a social cost of carbon of "
                "\u223c$78/tCO\u2082 (2025 USD, starting at $60/t in 2020 + $1.50/yr), applied "
                "uniformly to all countries. This is a fundamentally different approach from "
                "Burke et al.\u2019s empirical damage function, which finds country-specific "
                "impacts (e.g., India loses \u223c37% of GDP by 2050 under RCP8.5, while some "
                "cold countries gain). The IMF\u2019s SCC is also well below current academic "
                "estimates (\u223c$185\u2013190/tCO\u2082; Rennert et al. 2022, US EPA 2023), "
                "meaning the climate component of IMF subsidies is likely a substantial "
                "underestimate.",
            ], color="info", className="small py-2"),

            html.H6("Climate disasters (EM-DAT)", className="fw-bold mt-3"),
            html.P([
                "Disaster data from the EM-DAT international disaster database (CRED/UCLouvain). "
                "We include only climate-related natural disasters: ",
                html.Strong("floods, storms, droughts, extreme temperature events, wildfires, "
                            "and wet mass movements"),
                ". Earthquakes, volcanoes, and technological disasters are excluded.",
            ], className="small"),
            dbc.Alert([
                html.Strong("Judgement call \u2014 zero damage values: "),
                "When EM-DAT records zero economic damage for a disaster event, we interpret "
                "this as \u201cnot reported\u201d rather than \u201cno damage occurred.\u201d "
                "These values are replaced with NaN. This is standard practice for EM-DAT data "
                "but means our damage totals are conservative (underestimates).",
            ], color="warning", className="small py-2"),

            html.H6("Vulnerability index (ND-GAIN)", className="fw-bold mt-3"),
            html.P([
                "The ND-GAIN Country Index combines ", html.Strong("vulnerability"),
                " (exposure + sensitivity \u2212 adaptive capacity) and ",
                html.Strong("readiness"), " (economic + governance + social readiness) "
                "across six sectors: food, water, health, infrastructure, habitat, and "
                "ecosystems. Score range 0\u20131, where higher = more vulnerable. "
                "The map uses a color scale from 0.2 to 0.65 to show meaningful variation.",
            ], className="small"),

            # --- 2g: IPCC Scenarios ---
            html.H4("IPCC Scenarios & Pathways",
                     className="fw-bold mt-4 mb-2 text-primary"),

            html.H6("Scenario envelope computation", className="fw-bold mt-3"),
            html.P([
                "Scenario bands are computed from the full ",
                html.Strong("IIASA AR6 Scenario Explorer v1.1"),
                " database (Byers et al. 2022). We extract the variable ",
                html.Code("Emissions|CO2"), " (net CO\u2082), match each Model|Scenario pair "
                "to its IPCC category (C1, C3, C5, C7, C8) via the Ch.3-vetted metadata, "
                "then compute percentiles (p10, p25, p50, p75, p90, p95) for each "
                "category\u2013year combination. Darker bands show the interquartile range "
                "(p25\u2013p75); lighter bands show p10\u2013p90.",
            ], className="small"),
            html.P([
                html.Strong("Sample sizes: "),
                "C1: 97 scenarios, C3: 311, C5: 212, C7: 164, C8: 29. "
                "Not all scenarios report values for all years, so effective sample sizes "
                "vary by time period. C8 has the fewest scenarios.",
            ], className="small"),
            dbc.Alert([
                html.Strong("Critical caveat \u2014 C1 and overshoot: "),
                "C1 scenarios limit warming to 1.5\u00b0C with >50% probability by 2100, "
                "but most involve temperature ", html.Em("overshoot"),
                " (temporarily exceeding 1.5\u00b0C before returning via large-scale carbon "
                "dioxide removal). Required CDR: 8\u201310 GtCO\u2082/yr by 2050. Current "
                "global CDR capacity: \u223c2 GtCO\u2082/yr. These are NOT scenarios where "
                "we stay below 1.5\u00b0C at all times.",
            ], color="warning", className="small py-2"),

            html.H6("NZE milestones", className="fw-bold mt-3"),
            html.P(
                "IEA Net Zero by 2050 milestones used in the deployment tracker are "
                "approximate values from published reports (e.g., 11,000 GW total "
                "renewable capacity by 2030; 27,000 GW by 2050). These are hardcoded "
                "reference points, not dynamically updated from IEA data.",
                className="small",
            ),

            # --- 2h: Predictions vs Reality ---
            html.H4("Predictions vs Reality",
                     className="fw-bold mt-4 mb-2 text-primary"),

            html.H6("Forecast tracking methodology", className="fw-bold mt-3"),
            html.P([
                "We compare historical forecasts from ", html.Strong("IEA World Energy "
                "Outlook editions (2002\u20132022)"), " against actual deployment data for "
                "solar PV (GW), wind (GW), and CCS (MtCO\u2082/yr). Each forecast line "
                "is anchored at the actual value in its publication year (so lines start "
                "from observed data, not from prior predictions).",
            ], className="small"),
            html.P([
                html.Strong("Key findings: "),
                "IEA systematically underestimated solar deployment by 5\u201310\u00d7 in early "
                "editions (WEO 2006 projected 142 GW solar by 2030; actual 2023: 1,415 GW). "
                "Wind was underestimated by 2\u20133\u00d7. CCS was consistently overestimated "
                "(IEA NZE 2021 projected 1,000 MtCO\u2082/yr by 2030; actual 2023: 51 MtCO\u2082/yr "
                "\u2014 a 20\u00d7 shortfall).",
            ], className="small"),
            html.P([
                "We also show forecasts from independent analysts (RMI, Tony Seba/RethinkX) "
                "that used exponential growth models and came closer to actual solar/wind "
                "deployment than institutional forecasts.",
            ], className="small"),

            # --- 2i: World Map Metrics ---
            html.H4("World Map Metrics",
                     className="fw-bold mt-4 mb-2 text-primary"),

            html.H6("Available metrics and derivations", className="fw-bold mt-3"),
            html.P(
                "The interactive map offers seven thematic views. Each metric is derived "
                "from the latest available year of country-level data:",
                className="small",
            ),
            dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Theme"), html.Th("Metric"), html.Th("Unit"),
                    html.Th("Source"),
                ])),
                html.Tbody([
                    html.Tr([
                        html.Td("Emissions"), html.Td("Total GHG per capita"),
                        html.Td("tCO\u2082e/yr"), html.Td("EDGAR + PRIMAP-hist via OWID"),
                    ]),
                    html.Tr([
                        html.Td("Electricity Mix"),
                        html.Td("Grid carbon intensity"),
                        html.Td("gCO\u2082/kWh"), html.Td("OWID / Ember"),
                    ]),
                    html.Tr([
                        html.Td("Total Energy Mix"),
                        html.Td("Renewable share of final energy"),
                        html.Td("%"), html.Td("OWID / Ember"),
                    ]),
                    html.Tr([
                        html.Td("Carbon Pricing"),
                        html.Td("National ETS or carbon tax rate"),
                        html.Td("$/tCO\u2082"), html.Td("World Bank / ICAP"),
                    ]),
                    html.Tr([
                        html.Td("Health"),
                        html.Td("Fossil fuel PM2.5 + climate disaster deaths as % of all deaths"),
                        html.Td("% of deaths"), html.Td("McDuffie / EM-DAT / WHO"),
                    ]),
                    html.Tr([
                        html.Td("Damages"),
                        html.Td("Projected GDP loss/gain from warming"),
                        html.Td("% GDP/yr"), html.Td("Burke et al. 2015"),
                    ]),
                    html.Tr([
                        html.Td("Vulnerability"),
                        html.Td("ND-GAIN climate vulnerability score"),
                        html.Td("0\u20131 index"), html.Td("ND-GAIN / Notre Dame"),
                    ]),
                ]),
            ], bordered=True, hover=True, responsive=True, size="sm",
                className="small mb-3"),
            html.P([
                html.Strong("Missing data: "),
                "Countries without data for the selected metric appear in gray. "
                "The map uses the Natural Earth projection and clips Antarctica "
                "(latitude range \u221260\u00b0 to 85\u00b0) to save vertical space.",
            ], className="small"),

            # --- 2j: Homepage KPIs ---
            html.H4("Homepage KPIs",
                     className="fw-bold mt-4 mb-2 text-primary"),

            html.H6("Aggregation methods", className="fw-bold mt-3"),
            html.P(
                "The five headline statistics on the homepage are pre-computed at build time "
                "and stored in kpis.json (no database queries at page load). "
                "Different KPIs use different aggregation methods:",
                className="small",
            ),
            html.Ul([
                html.Li([
                    html.Strong("Sum across countries: "),
                    "Emissions (CO\u2082, GHG), capacity (solar GW, wind GW), "
                    "PM2.5 deaths. Only countries with 3-letter ISO codes are included "
                    "(OWID aggregates excluded).",
                ], className="small"),
                html.Li([
                    html.Strong("Population-weighted average: "),
                    "Electricity access (%), clean cooking access (%). Formula: "
                    "\u03a3(access_pct \u00d7 population) / \u03a3(population). "
                    "This is the standard World Bank methodology. "
                    "Unweighted averages would understate global access because many small "
                    "low-access countries pull the average down.",
                ], className="small"),
                html.Li([
                    html.Strong("Generation-weighted average: "),
                    "Renewable share of electricity. Formula: "
                    "\u03a3(renewable_share \u00d7 total_generation) / \u03a3(total_generation). "
                    "Ensures large producers count proportionally.",
                ], className="small"),
                html.Li([
                    html.Strong("Direct observation: "),
                    "CO\u2082 concentration (NOAA), temperature anomaly (HadCRUT5), "
                    "clean energy investment (IEA).",
                ], className="small"),
            ]),
            html.P([
                html.Strong("Year selection: "),
                "KPIs use the most recent year with data from >100 countries. "
                "Year-over-year percent change is computed as: ",
                html.Code("(current \u2212 previous) / |previous| \u00d7 100"),
                ". A change within \u00b10.5% is classified as \u201cstable\u201d (\u2192).",
            ], className="small"),

            # --- 2k: S-Curve Technology Trajectories ---
            html.H4("S-Curve Technology Trajectories",
                     className="fw-bold mt-4 mb-2 text-primary",
                     id="source-scurve-model"),

            html.H6("S-Curve logistic model", className="fw-bold mt-3"),
            html.P([
                "Technology adoption trajectories are modelled as logistic S-curves: ",
                html.Code("S(t) = K / (1 + exp(-r \u00d7 (t \u2212 t\u2080)))"),
                ". Parameters (K, r, t\u2080) are fitted using ",
                html.Code("scipy.optimize.curve_fit"),
                " with constrained bounds.",
            ], className="small"),
            html.Ul([
                html.Li([
                    html.Strong("EV data: "),
                    "IEA Global EV Outlook 2025 via Global EV Data Explorer.",
                ], className="small"),
                html.Li([
                    html.Strong("Solar/wind share: "),
                    "Our World in Data (from Ember Global Electricity Review).",
                ], className="small"),
                html.Li([
                    html.Strong("K (saturation) values: "),
                    "Set using convergence of major energy forecasts rather than "
                    "pure historical fitting for early-growth technologies.",
                ], className="small"),
            ]),

            html.H6("Saturation levels (K)", className="fw-bold mt-3"),
            html.Ul([
                html.Li([
                    html.Strong("EV sales share: "),
                    "K\u2098\u1d62\u2099 = 70\u201380% based on ICE phase-out mandates "
                    "(EU 2035, UK 2035, China targets).",
                ], className="small"),
                html.Li([
                    html.Strong("Solar: "),
                    "K = 40% (IEA NZE 2050: 43%, DNV 2050: 40%, BNEF base: 22%).",
                ], className="small"),
                html.Li([
                    html.Strong("Wind: "),
                    "K = 30% (IEA NZE 2050: 31%, DNV 2050: 29%, IRENA 1.5\u00b0C: 35%).",
                ], className="small"),
                html.Li([
                    html.Strong("Renewables overall: "),
                    "K\u2098\u1d62\u2099 = 80% (IEA NZE 2050: ~90%, DNV: 69%+).",
                ], className="small"),
            ]),

            html.H6("Nascent technology data", className="fw-bold mt-3"),
            html.Ul([
                html.Li(
                    "Editorially curated from IEA, IATA, Global Maritime Forum, "
                    "World Steel Association.",
                    className="small",
                ),
                html.Li([
                    html.Strong("Threshold framework: "),
                    "Rogers Diffusion of Innovations milestones "
                    "(5% inflection, 16% early majority, 50% majority).",
                ], className="small"),
                html.Li(
                    "Each entry includes source URL, assessment date, and "
                    "confidence level.",
                    className="small",
                ),
            ]),

            # --- 2l: Temperature Trajectory Model ---
            html.H4("Temperature Trajectory Model",
                     className="fw-bold mt-4 mb-2 text-primary",
                     id="source-temperature-model"),

            html.H6("Bottom-up temperature projection", className="fw-bold mt-3"),
            html.P(
                "Maps S-curve adoption rates to sector-by-sector fossil fuel "
                "displacement, then converts cumulative CO\u2082 to temperature.",
                className="small",
            ),
            html.Ul([
                html.Li([
                    html.Strong("8 sectors (% of global emissions): "),
                    "electricity (25%), road transport (12%), aviation (2.5%), "
                    "shipping (1.5%), industry (21%), buildings (6%), "
                    "agriculture (22%), other (10%).",
                ], className="small"),
                html.Li([
                    html.Strong("TCRE: "),
                    "0.45\u00b0C per 1000 GtCO\u2082 (IPCC AR6 WG1 best estimate, "
                    "likely range 0.27\u20130.63).",
                ], className="small"),
                html.Li([
                    html.Strong("Fleet turnover lag: "),
                    "12 years for road transport (EV sales share \u2192 fleet share).",
                ], className="small"),
                html.Li([
                    html.Strong("Demand growth: "),
                    "1.5% declining to 0% over 50 years.",
                ], className="small"),
                html.Li([
                    html.Strong("Non-CO\u2082 forcing: "),
                    "0.5\u00b0C baseline, declining as methane reduces.",
                ], className="small"),
                html.Li([
                    html.Strong("Three scenarios: "),
                    "fast (r \u00d7 1.3), central (r \u00d7 1.0), slow (r \u00d7 0.7).",
                ], className="small"),
            ]),
            dbc.Alert([
                html.Strong("Intentionally simplified: "),
                "This is a thought experiment, not a full integrated assessment "
                "model (IAM). Key difference from UNEP 3.1\u00b0C: UNEP assumes "
                "current policies; this model assumes current technology trajectories.",
            ], color="warning", className="small py-2"),

            # --- 2m: Optimism Meter ---
            html.H4("Optimism Meter Methodology",
                     className="fw-bold mt-4 mb-2 text-primary",
                     id="source-optimism-meter"),

            html.H6("Dual-score approach", className="fw-bold mt-3"),
            html.Ul([
                html.Li([
                    html.Strong("Progress Score (0\u2013100): "),
                    "emissions-weighted clean energy tipping points crossed (40 pts), "
                    "technology/investment momentum (30 pts), "
                    "gap to climate targets (30 pts).",
                ], className="small"),
                html.Li([
                    html.Strong("Climate Risk Score (0\u2013100): "),
                    "derived from S-curve temperature projection. "
                    "Scoring: 1.5\u00b0C = 0, 2.0\u00b0C = 50, 3.1\u00b0C = 100.",
                ], className="small"),
                html.Li([
                    html.Strong("Net Score: "),
                    html.Code("Progress \u2212 (Risk \u00d7 0.5)"),
                    ". The 0.5 factor means maximum risk reduces but does not "
                    "eliminate progress.",
                ], className="small"),
            ]),

            # --- 2n: Country Comparison Tool ---
            html.H4("Country Comparison Tool",
                     className="fw-bold mt-4 mb-2 text-primary",
                     id="source-country-comparison"),

            html.Ul([
                html.Li([
                    html.Strong("7 comparison metrics: "),
                    "CO\u2082 trajectory, renewable share, energy mix, "
                    "CO\u2082/capita, PM2.5 deaths, investment, "
                    "vulnerability (ND-GAIN).",
                ], className="small"),
                html.Li(
                    "Data sources are the same as the country detail pages.",
                    className="small",
                ),
                html.Li(
                    "Missing data is shown as a placeholder chart, not an "
                    "empty panel.",
                    className="small",
                ),
            ]),

            # --- 2o: Country Spotlight Selection ---
            html.H4("Country Spotlight Selection",
                     className="fw-bold mt-4 mb-2 text-primary",
                     id="source-country-spotlights"),

            html.Ul([
                html.Li(
                    "18 countries in 6 analytically defensible categories.",
                    className="small",
                ),
                html.Li([
                    html.Strong("Framework: "),
                    "WEF Energy Transition Index, Carnegie \u201celectrostate\u201d "
                    "concept, crisis-driven vs policy-led transition literature.",
                ], className="small"),
                html.Li([
                    html.Strong("Selection criteria: "),
                    "narratively distinctive, data-rich, globally representative.",
                ], className="small"),
                html.Li([
                    html.Strong("Notable exclusions: "),
                    "Morocco (pre-deployment projects), UK (overlaps Denmark), "
                    "Bangladesh (limited data coverage).",
                ], className="small"),
            ]),

            html.Hr(),

            # ================================================================
            # Section 3: Key Definitions
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

                dbc.AccordionItem([
                    html.P([
                        "Per-country subsidy data uses the ",
                        html.Strong("IMF CPAT database (2025 update)"),
                        ", covering 186 countries. The IMF defines subsidies as the gap between "
                        "what consumers pay and the ", html.Em("efficient price"),
                        " (supply cost + externalities + forgone tax revenue).",
                    ], className="small"),
                    html.P([
                        html.Strong("Explicit subsidies: "),
                        "Consumer price below supply cost (\u223c$750B globally, in 2025 USD). ",
                        html.Strong("Implicit subsidies: "),
                        "Supply cost covered, but externalities unpriced (\u223c$8.0T globally). "
                        "Total: \u223c$8.7T/yr (2024, in 2025 USD). Implicit costs include air pollution "
                        "mortality, climate damages, traffic externalities, and forgone "
                        "consumption tax revenue.",
                    ], className="small"),
                    html.P([
                        "The separate IEA time series (price-gap method, 48 countries, "
                        "explicit only) is used for the global trend chart. The two datasets "
                        "are complementary, not interchangeable.",
                    ], className="small text-muted"),
                ], title="Fossil Fuel Subsidies (IMF vs IEA)"),
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
                    html.Strong("IMF subsidy estimates include modelled externalities: "),
                    "The IMF's implicit subsidies are not cash transfers but estimated costs "
                    "of underpriced pollution, climate damages, and forgone tax revenue. "
                    "These estimates depend on modelling assumptions (social cost of carbon, "
                    "concentration-response functions for mortality). The explicit subsidy "
                    "component (\u223c$750B in 2025 USD) is more directly observable.",
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
