# Long Island Social Responsibility & Resource Access

Static spatial-analysis app for evaluating whether basic-needs and homelessness-related resources across suburban Long Island are visible, reachable, and aligned with high-need communities.

The study area is Nassau County and Suffolk County. Kings and Queens are excluded because they are part of New York City's distinct shelter, transit, density, and governance system.

## Research Frame

The project asks whether resource presence is enough to count as social responsibility. A county may list food pantries, shelter intake offices, outreach providers, legal aid, housing counseling, clinics, and public-benefits offices, but a resource map alone does not prove that vulnerable households can actually reach or use those resources.

The analysis therefore separates three questions:

1. Where are housing-instability and basic-needs risks concentrated?
2. Do visible resources align with those high-need tracts?
3. Does the answer change when accessibility is measured by walking rather than driving?

## Current Data

- Tracts: 665 Long Island census tracts from TIGER/Line 2022, excluding water-only tracts
- ACS: 2022 5-year tract indicators
- Resources: 184 Nassau + Suffolk resource points
- Access-score resources: 161 food, shelter/intake, and outreach points
- Context-only resources: 23 legal, housing-support, behavioral-health, public-benefits, clinic, and other support points
- Homeless-student layer: 113 NYSED McKinney-Vento school-district polygons, 2018-19 to 2020-21 three-year average, clipped to land with TIGER AREAWATER removed

## Methods

Need is a tract-level composite of:

- rent burden rate,
- poverty rate,
- renter share,
- eviction filing rate placeholder.

Eviction data is currently a stub because tract-level Long Island eviction data has not yet been added. The code skips the constant eviction placeholder in spatial diagnostics.

Access is calculated with Enhanced Two-Step Floating Catchment Area (E2SFCA), using renter households as the demand base and a 15-minute catchment. The pipeline produces separate outputs for:

- 15-minute drive access,
- 15-minute walk access.

The raw `access_score` is retained for diagnostics and mismatch calculations. The map displays `access_index`, a 0-100 Long Island percentile rank of raw access, so readers can compare relative accessibility without interpreting tiny E2SFCA supply-demand ratios.

Spatial diagnostics include:

- Global Moran's I,
- bivariate Moran's I between need and access,
- LISA clusters on mismatch,
- Getis-Ord Gi* hotspot scores,
- robustness checks across queen, KNN-5, and 3-mile distance-band weights.

## Latest Findings

For the Long Island-wide run:

- Drive: bivariate Moran's I between need and access is `+0.097`, `p = 0.001`. Resources weakly but significantly follow need, so the project should lead with local mismatch rather than a blanket claim that resources ignore high-need areas.
- Walk: bivariate Moran's I is `-0.025`, `p = 0.141`. There is no clear spatial relationship, supporting the argument that car dependence changes the meaning of access.
- Homeless-student data shows substantial suburban need beyond New York City. The 3-year average Long Island total is about 7,657 K-12 students identified as homeless, with high concentrations in Hempstead, William Floyd, Brentwood, Longwood, Riverhead, Central Islip, Amityville, Sachem, Copiague, Farmingdale, Wyandanch, and other districts.

## Repository Structure

```text
longisland/
├── README.md
├── STORY.md
├── run_pipeline.py
├── requirements.txt
├── notebooks/
│   ├── 00_collect_facilities.py
│   ├── 01_access_need_mismatch.py
│   ├── 02_spatial_diagnostics.py
│   └── 03_homeless_students.py
├── data/
│   ├── raw/
│   │   ├── nassau_facilities.geojson
│   │   └── suffolk_homelessness_resources.csv
│   └── processed/
│       ├── longisland_facilities.geojson
│       ├── tracts_{drive,walk}.geojson
│       ├── tracts_{drive,walk}_diagnostics.geojson
│       ├── diagnostics_{drive,walk}.json
│       └── homeless_students_districts.{geojson,csv}
├── docs/
│   └── static GitHub Pages app
└── site/
    └── Vite development app
```

## Run

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run_pipeline.py
```

Frontend development:

```bash
cd site
npm install
npm run dev
```

Production build:

```bash
cd site
npm run build
```

## Caveats

- The drive and walk travel-time matrices currently use haversine fallback unless an OSRM endpoint is configured.
- Suffolk resource coordinates are manually verified but mostly marked for re-geocoding before final publication.
- Homeless-student counts are school-district indicators, not tract-level counts.
- McKinney-Vento data includes doubled-up students and may count students in multiple LEAs if they move during a school year.
- Shelter systems using motel vouchers, protected addresses, and dispersed placements remain difficult to map as facility points.
