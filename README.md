# nyc-street-vendor-enforcement-

# NYC Street Vendor Enforcement Analysis

One or two sentences: what this project does and why it matters
(e.g. spatial analysis of OATH violation enforcement patterns across NYC boroughs/council districts)

## Overview
- Brief context: what question you're answering
- Who this is for / research context (e.g. RA work with Dr. Farah)
- Key finding or headline visual (this is a great place for your borough enforcement figure)

![Enforcement violations by borough](outputs/violations_by_borough.png)

## Data Sources
- NYC OATH violations (~108k records) DIFFERENCE BETWEEN CIVIL AND CRIMINAL SUMMONS
- NYC 311 complaints (Socrata)
- PLUTO
- Legistar (legislative vote records, 1998–2025)
- ACS (Census API, NYC counties)
- Council district shapefiles (2013/2023 redistricting)

## Repository Structure

## Methodology
- Geocoding approach (Pelias/NYC GeoSearch API, spatial accuracy tiers)
- Projection standard (EPSG:2263)
- Spatial joins (census tracts, BID overlays, council districts)
- Modeling approach (negative binomial regression, elastic net, Moran's I/LISA, multilevel models)
- Key predictors identified (e.g. pct_in_bid_z, 311_requests_z)

## Key Results
- 2-4 bullet points or a short paragraph summarizing main findings
- Link to relevant notebook(s) for full detail

## Setup / Installation
```bash
git clone https://github.com/AmelieDall/nyc-street-vendor-enforcement.git
cd nyc-street-vendor-enforcement
pip install -r requirements.txt
cp .env.example .env  # add your API keys
```

## Usage
Brief instructions on running notebooks in order, or pointing to specific ones for specific analyses

## Acknowledgments
- Dr. Irene Farah Rivadeneyra / research context
- Any data providers worth crediting

## License
Reference to LICENSE file