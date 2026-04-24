# Nassau County Homelessness & Social Safety Net

A spatial-statistical analysis of the homelessness service network in Nassau County, NY
(FIPS 36059), with the intent of publishing findings as a static web application on
GitHub Pages.

---

## 1. Project goal

Explore the spatial relationship between:

- **Need**: where are the populations at risk of housing instability and food insecurity?
- **Access**: where are the services (shelters, food pantries, food banks, outreach)?
- **Mismatch**: where does need exceed access, and is that gap systematic or local?

Eventually also:

- Correlation with **eviction filings**, **eviction appeals** (pending data).
- Correlation with **socioeconomic context** (income, rent burden, race/ethnicity, vehicle
  ownership).

All analysis is pre-computed in Python notebooks; the static site reads the artifacts.

---

## 2. Research questions

1. **Does service provision follow need in Nassau?**
   Operationalised as a bivariate Moran's I between a `need_score` composite and a
   `access_score` from Enhanced 2SFCA. This is the **validation gate** for the product
   thesis — if services already track need, the "mismatch" narrative has no legs
   globally (see §4 for the first answer).

2. **Where are the local hotspots of unmet need?**
   LISA (Local Moran's I) on the composite mismatch index. Even when the global answer
   is "no mismatch", local HH clusters still identify actionable tracts.

3. **Does modality matter?** Walking vs driving reachability differ dramatically in
   car-dependent suburbs. Nassau's answer appears to be yes (§4).

4. **Is the system fragile?** Leave-one-facility-out sensitivity (TODO): how much does
   the mismatch surface shift when a single large facility is removed?

5. **Does eviction pressure predict the mismatch?** Pending eviction data.

---

## 3. Repository structure

```
nassau/
├── README.md                            this file
├── .env                                 CENSUS_API_KEY (gitignored)
├── requirements.txt                     Python deps
├── run_pipeline.py                      driver: collect → build → diagnose
│
├── notebooks/
│   ├── 00_collect_facilities.py         OSM, LI Cares, Island Harvest, RHY, dedup
│   ├── 01_access_need_mismatch.py       ACS, MOE propagation, E2SFCA, mismatch index
│   └── 02_spatial_diagnostics.py        Moran's I, LISA, Gi*, validation gate
│
├── data/
│   ├── raw/                             gitignored; populated by notebooks 00 + external
│   │   ├── island_harvest_raw.csv       89 pantries (Nassau, geocoded)
│   │   ├── li_cares_raw.csv             3 First Stop centers (Nassau, geocoded)
│   │   ├── otda_rhy_raw.csv             2 youth agencies (Nassau, geocoded)
│   │   ├── osm_raw.json                 70 raw OSM features
│   │   ├── nassau_facilities_osm.geojson  cleaned OSM subset
│   │   ├── nassau_facilities.geojson    consolidated 98-facility output
│   │   ├── hud_hic_ny603_2024.pdf       HUD HIC official report (CoC level)
│   │   ├── hud_hic_ny603_2024.csv       parsed table, all 209 programs
│   │   └── hud_hic_nassau_shelters.csv  14 Nassau-named shelter entries (no addresses)
│   └── processed/                       pipeline outputs
│       ├── tracts_{drive,walk}.geojson          286 tracts w/ need + access + mismatch
│       ├── metrics_{drive,walk}.parquet         same minus geometry, for DuckDB-WASM
│       ├── tracts_{drive,walk}_diagnostics.geojson   + LISA labels + Gi* scores
│       └── diagnostics_{drive,walk}.json        Moran's I table, validation verdict
│
└── site/                                frontend (not yet built)
```

---

## 4. 初步发现（第一次端到端运行）

### 4.1 Validation gate（验证命题是否站得住）

| 模式 | Bivariate Moran's I(need, access) | p-sim | 判定 |
| --- | ---: | ---: | --- |
| Drive（15 min 驾车） | **+0.274** | 0.001 | `mismatch-story-weak` —— 服务已经集中在高需求地区 |
| Walk（15 min 步行） | +0.033 | 0.163 | `inconclusive` —— 没有显著空间关系 |

**解读**：在 15 分钟驾车的 catchment 里，Nassau 的食物网络**已经跟着 need 走了**。这其实
是成熟的 emergency-food infrastructure 的预期行为——Island Harvest 和 Long Island Cares
本来就主动把合作网点布在高需求 municipality。

这意味着"全局 mismatch"叙事**撑不起整个产品**——三条可行的 pivot 见 §5。

### 4.2 Global Moran's I（queen contiguity, drive 模式）

| 变量 | I | p-sim | 对 W 选择是否稳健 |
| --- | ---: | ---: | --- |
| need_score | 0.32 | 0.001 | 否（I_std 0.11） |
| poverty_rate | 0.27 | 0.001 | 否（I_std 0.09） |
| mismatch_index | 0.09 | 0.008 | **是**（I_std 0.03） |
| access_score | 0.04 | 0.027 | **是** |
| rent_burden_rate | 0.07 | 0.014 | 否 |
| eviction_filing_rate_eb | n/a | — | 无数据 |

值得注意的是：`need_score` 和 `poverty_rate` 虽然 I 值高，但跨三种 W（queen / knn=5 /
3-mile band）波动大；`mismatch_index` 虽然 I 值不大，但**跨 W 稳健**——这才是产品可以
放心引用的指标。

### 4.3 LISA 聚类（drive 模式，mismatch_index）

```
HH  高 mismatch + 邻居也高   ─  70 tracts  ← 可执行的热点
LL  低 mismatch + 邻居也低   ─  66 tracts
HL  异常点                    ─   2 tracts
ns  不显著                    ─ 148 tracts
─────────────────────────────────────────
合计                             286 tracts
```

全局信号虽弱，局部仍然锁定了 **70 个 HH cluster tract**——足够支撑一条"局部失配"的产品
叙事（见 §5 方向 A）。

---

## 5. Three narrative options for the product

### Option A — Local pockets (recommended; data already supports)

Global need-access correlation is positive, but 70 tracts still cluster as HH on the
mismatch index. Product focus: **what is happening in these 70 tracts, and what is
different about them from the LL cluster tracts?**

UI: map centred on the LISA surface; drawer with tract-level deep-dive (demographics,
nearest facilities, capacity).

Strength: findings survive the validation gate. Data already in hand.

### Option B — Shortage, not mismatch

Food coverage exists; **shelter coverage is essentially absent in our dataset** (2 youth
agencies). Nassau's emergency-shelter system is dominated by DSS **motel vouchers**
(938 beds across `Other Motel` + `Voucher Motel`), which cannot be point-mapped — they
are a distributed-purchase inventory, not a facility inventory.

Product focus: **Nassau's shelter infrastructure is a centralised-DSS-dispersed-motel
model**, not a concentrated shelter model (contrast NYC). This is a genuine
methodological story about suburban homelessness.

Strength: actually interesting, novel.
Blocker: requires Nassau DSS FOIL to locate actual shelter facilities beyond voucher programs.

### Option C — Transport-mediated access

Drive and walk diagnostics diverge: drive finds mature coverage, walk finds no
significant relationship. Nassau is car-dependent — access is conditional on having
a vehicle.

Product focus: **households without a vehicle face a different map**. Overlay ACS
B25044 (tenure by vehicles available), LIRR stations, NICE bus routes.

Strength: adds a dimension the public can relate to ("what if you don't have a car?").
New data lift: ACS vehicle table only, small.

---

## 6. Methodology (what the pipeline does)

### 6.1 Need composite

Four components, each z-scored then averaged (weights adjustable at display time):

| component | ACS source | MOE-propagated? |
|---|---|---|
| `rent_burden_rate` | B25070 007..010 / 001 (paying ≥30% of income on rent) | yes |
| `poverty_rate` | B17001 002 / 001 | yes |
| `renter_share` | B25003 003 / 001 | yes |
| `eviction_filing_rate_eb` | external + empirical-Bayes shrinkage | n/a (not a Census quantity) |

All ACS rates propagate 90 % MOEs using the Census Bureau Appendix-3 formulas
(`proportion` form with `ratio` fallback when the radicand is negative).

Small-N Poisson rates (eviction, potentially shelter admissions) are shrunk toward the
county mean using a Poisson-Gamma empirical-Bayes estimator with method-of-moments
prior. Skipped when total events in the county are zero.

### 6.2 Access score

**Enhanced 2SFCA** with Luo-Qi (2009) gaussian distance decay normalised to f(0)=1,
f(t₀)=0, zero beyond t₀.

Demand base is **renter-occupied households** (`B25003_003`), not total population —
housing instability risk acts on renters. Supply defaults to 1 per facility when
capacity is unknown.

Catchments: **15 min drive** (primary) and **15 min walk** (alternate). Run separately.

Travel-time matrix via OSRM `/table` (public demo, falls back to haversine with mode-
specific assumed speed). OSRM public endpoint blocked this machine during the first
run → haversine fallback is optimistic about real travel times.

### 6.3 Mismatch index

```
mismatch_index = z(need_score) - z(access_score)
mismatch_pct   = percentile rank (0–100)
```

Everything exposed per tract for UI re-weighting.

### 6.4 Spatial diagnostics (notebook 02)

- Global Moran's I on 6 variables × 3 weights (queen / knn=5 / 3-mile band)
  — robustness flag = I_std < 0.05 and all p < 0.05
- Bivariate Moran's I(need, access) → validation gate verdict
- Local Moran's I (LISA) on `mismatch_index` and `need_score` → HH/LL/HL/LH/ns labels
- Getis-Ord Gi* on `mismatch_index` → z-score + p-value per tract

---

## 7. Data sources and status

### 7.1 Facilities (98 geocoded, after dedup)

| source | count | note |
|---|---:|---|
| Island Harvest (StoreRocket API) | 89 | partner pantries, Nassau subset of 218 LI-wide |
| Long Island Cares First Stop hubs | 3 | from archive.org snapshot + Census Geocoder |
| OSM Overpass | 4 | after relevance filter (OSM tags unreliable for homelessness) |
| NY Runaway & Homeless Youth | 2 | data.ny.gov `q88j-j2mi`, pre-geocoded |

### 7.2 Facility data we can't currently point-map

| source | status | workaround |
|---|---|---|
| **LI Cares partner pantries** | Cloudflare-blocked (live + archive) | manual browser copy, or give up (Island Harvest overlaps ~70 %) |
| **HUD HIC NY-603 shelters** (14 Nassau-named entries) | no addresses in public HIC (HUD policy, partly to protect DV shelters) | FOIL Nassau DSS |
| **Nassau DSS motel-voucher beds** (938 total) | fundamentally not point-mappable | represent as county-level layer, or as DSS intake-office gravity |
| **Other OTDA/NY 211 shelters** | not yet probed | try `https://www.211longisland.org` listings |

### 7.3 Tract boundaries and ACS

- TIGER/Line tracts for state 36, county 059, year 2022 (286 tracts)
- ACS 2022 5-year estimates via `api.census.gov`, variables B25070, B17001, B25003,
  B03002, B19013 with MOEs

### 7.4 What is missing for the full thesis

| need | status |
|---|---|
| Eviction filings (tract-level) | not pulled — Princeton Eviction Lab + NY OCA FOIL are the paths |
| Eviction appeals | not pulled — smaller dataset, probably OCA only |
| Actual shelter facility coordinates | FOIL required |
| Vehicle ownership (for Option C) | ACS B25044, not yet pulled |

---

## 8. Critical caveats (must appear in the methods page of the site)

1. **Eviction layer is absent** in the first run. The need composite was computed with
   3/4 components (rent burden + poverty + renter share). Mean of 3 z-scores is a
   valid but incomplete operationalisation of "need".

2. **Shelter layer is effectively absent**. 98 facilities ≈ 93 food + 3 LI Cares hubs
   + 2 youth agencies. The access surface is a **food-network** surface, not a
   homelessness-services surface. This affects what the mismatch index measures.

3. **Nassau's shelter system does not look like NYC's**. Of ~1,100 HIC-reported
   emergency beds in the Nassau-named subset, ~938 are DSS motel vouchers — a
   distributed-purchase inventory that fundamentally cannot be point-mapped. Any
   Nassau-centred homelessness product must either acknowledge this or switch to
   municipality-level aggregation for shelter access.

4. **Travel-time matrix used haversine fallback**, not road-network routing. Real
   drive times will be 10–30 % longer; real walk times much longer in areas without
   sidewalks. Rerun with a local OSRM instance before publishing findings.

5. **CoC NY-603 = Nassau + Suffolk Counties combined**. HIC PIT/HIC data for Nassau
   cannot be cleanly separated from Suffolk at the official level. Summary headlines
   should be CoC-level; tract-level analysis remains Nassau-only.

6. **MOE propagation is implemented for ACS indicators** (§6.1) but **not yet into
   spatial statistics** (Moran's I, LISA). Bootstrap over MOE-implied distributions
   is the correct fix and is in the §10 TODO.

7. **Spatial weights choice matters**. Global I differs 2–3× across queen / knn5 /
   distance-band for some indicators. Only `mismatch_index` and `access_score` are
   robust across all three.

8. **"Accessibility" here means physical reach under a travel-time catchment**, not
   eligibility, operating hours, cultural fit, language capacity, stigma, or any of
   the other barriers that matter in practice.

---

## 9. How to run

```bash
# one-time
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # or create .env with CENSUS_API_KEY=...

# end-to-end
python3 run_pipeline.py
# writes data/processed/tracts_{drive,walk}.geojson
#        data/processed/metrics_{drive,walk}.parquet
#        data/processed/tracts_{drive,walk}_diagnostics.geojson
#        data/processed/diagnostics_{drive,walk}.json
```

Notebook files use [jupytext percent format](https://jupytext.readthedocs.io/) — open in
Jupyter via `jupytext --to notebook notebooks/*.py` or run as scripts through
`run_pipeline.py`.

---

## 10. TODO

### Data
- [ ] Eviction filings CSV (`data/raw/nassau_evictions_2022.csv`)
- [ ] Nassau DSS shelter addresses (FOIL)
- [ ] NY 211 Long Island shelter listings (scrape attempt)
- [ ] ACS vehicle ownership B25044 for Option C
- [ ] Real OSRM instance for road-network travel times

### Analysis
- [ ] Leave-one-facility-out sensitivity (identifies critical facilities)
- [ ] GWR: regress `eviction_filing_rate_eb` on `rent_burden_rate + poverty_rate + access_score`
- [ ] MOE propagation into Moran's I via bootstrap
- [ ] Compare `eviction_filing_rate_eb` vs raw rate (validate shrinkage)
- [ ] Bivariate LISA(need, access) — local counterpart to the global gate
- [ ] Independent validator: 311 homeless-related calls / DSS intake by origin ZIP

### Frontend (`site/`)
- [ ] MapLibre GL + deck.gl base
- [ ] Layers: facilities / ACS choropleth / LISA / Gi* / mismatch composite
- [ ] Interactive need-weight sliders (DuckDB-WASM + arquero for in-browser recompute)
- [ ] Methods page (paste §6, §8 content + live-read `diagnostics_*.json`)

---

## 11. Data-collection notes (tactical)

Things that took non-trivial digging and are worth remembering:

- **OSM is nearly useless for Nassau homelessness services.** 70 raw OSM features; only
  4 are homelessness-relevant after filtering. Most `social_facility` tags in Nassau
  are nursing homes and group homes (elder/disability care), not homeless shelters.
  `social_facility=group_home` ≠ homeless shelter; require `=shelter` or
  `social_facility:for=homeless`.

- **Nassau County NY = OSM relation 2552442.** There is a Florida Nassau County
  (relation 1210720) — pin by numeric id, not by `name="Nassau County"`.

- **Island Harvest uses the StoreRocket widget** (`storerocket-id=n0pjnLgp6V`). Public
  unauthenticated endpoint: `https://storerocket.io/api/user/<id>/locations` returns
  full geocoded location list. This is the single most useful API we found.

- **Long Island Cares is behind Cloudflare Turnstile.** curl/WebFetch get 403. Only the
  home page is cached on archive.org — the `ouragencies` partner list is not archived.

- **data.ny.gov uses Socrata.** Catalog search:
  `https://api.us.socrata.com/api/catalog/v1?q=<term>&domains=data.ny.gov`.
  Data endpoint: `https://data.ny.gov/resource/<id>.json`.

- **HUD HIC PDFs are fragile to parse.** The column alignment uses pdfplumber word
  coordinates, not extractable tables. Section headers repeat on every page top.

- **HIC does not include facility addresses.** This is policy, partly to protect
  domestic-violence shelter locations.

---

## 12. References

- HUD Continuum of Care NY-603 Housing Inventory Count 2024:
  `https://files.hudexchange.info/reports/published/CoC_HIC_CoC_NY-603-2024_NY_2024.pdf`
- Luo, W., & Qi, Y. (2009). An enhanced two-step floating catchment area (E2SFCA)
  method for measuring spatial accessibility to primary care physicians.
  *Health & Place*, 15(4), 1100–1107.
- US Census Bureau, *A Compass for Understanding and Using American Community Survey
  Data* (Appendix 3 on MOE calculations for derived estimates).
- Anselin, L. (1995). Local Indicators of Spatial Association — LISA.
  *Geographical Analysis*, 27(2), 93–115.
