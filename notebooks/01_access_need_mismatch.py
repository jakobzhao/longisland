# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Nassau County — Access-Need Mismatch Index
#
# Pipeline:
# 1. Pull ACS 5-year tract data (rent burden, poverty, renter share, demographics) with margins of error
# 2. Pull Nassau tract geometries (TIGER)
# 3. Load eviction filings (external source — stub here)
# 4. Load facility locations (shelters, food banks, pantries — stub here)
# 5. Build **need** composite with MOE propagation
# 6. Compute **access** via Enhanced 2SFCA (walk + drive)
# 7. Mismatch = z(need) - z(access)
# 8. Write GeoJSON + parquet for the frontend
#
# Notes:
# - Everything spatial is computed here and dumped as static artifacts. Frontend never computes W, 2SFCA, etc.
# - MOE values from ACS are 90% margins; convert to SE by dividing by 1.645.
# - Catchment defaults: 15 min walk, 15 min drive. Run the pipeline twice, once per mode.

# %%
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import requests
from scipy import stats

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env" if "__file__" in dir()
                else Path("../.env"))
except ImportError:
    pass  # python-dotenv not installed; fall back to shell env

# %% [markdown]
# ## 0. Config

# %%
NASSAU_STATE = "36"
NASSAU_COUNTY = "059"
NASSAU_FIPS = NASSAU_STATE + NASSAU_COUNTY

ACS_YEAR = 2022                        # latest 5-year endpoint at time of writing
ACS_DATASET = "acs5"

WALK_CATCHMENT_MIN = 15
DRIVE_CATCHMENT_MIN = 15

# MOE -> SE conversion (ACS publishes 90% MOE; z_{0.95} = 1.645)
MOE_Z = 1.645

# Paths (notebook runs from /notebooks)
ROOT = Path(__file__).resolve().parent.parent if "__file__" in dir() else Path("..").resolve()
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
DATA_RAW.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

CENSUS_API_KEY = os.environ.get("CENSUS_API_KEY")  # get free key at api.census.gov/data/key_signup.html

# OSRM endpoint for travel-time matrix. Options:
#   1. Self-host: docker run -t -i -p 5000:5000 osrm/osrm-backend osrm-routed /data/us-northeast.osrm
#   2. Public demo: "https://router.project-osrm.org" (rate-limited; fine for Nassau scale)
OSRM_DRIVE = os.environ.get("OSRM_DRIVE", "https://router.project-osrm.org")
OSRM_WALK = os.environ.get("OSRM_WALK", "")  # public demo only supports car; self-host for walking

# %% [markdown]
# ## 1. ACS variable definitions
#
# Tables we pull (estimate + MOE each):
# - **B25070**: Gross Rent as % of Household Income (rent burden). Burdened = 30%+ of income on rent.
# - **B17001**: Poverty status.
# - **B25003**: Tenure (renter vs owner occupied).
# - **B03002**: Race / Hispanic origin (for disparity analysis).
# - **B19013**: Median household income.

# %%
ACS_VARS = {
    # rent burdened renters = B25070_007..010 (30-34.9, 35-39.9, 40-49.9, 50+)
    "rent_30_34":     ("B25070_007E", "B25070_007M"),
    "rent_35_39":     ("B25070_008E", "B25070_008M"),
    "rent_40_49":     ("B25070_009E", "B25070_009M"),
    "rent_50_plus":   ("B25070_010E", "B25070_010M"),
    "rent_total":     ("B25070_001E", "B25070_001M"),  # total renter households paying cash rent

    "pov_below":      ("B17001_002E", "B17001_002M"),
    "pov_universe":   ("B17001_001E", "B17001_001M"),

    "renter_occ":     ("B25003_003E", "B25003_003M"),
    "tenure_total":   ("B25003_001E", "B25003_001M"),

    "race_total":     ("B03002_001E", "B03002_001M"),
    "race_nhw":       ("B03002_003E", "B03002_003M"),  # non-Hispanic white
    "race_nhb":       ("B03002_004E", "B03002_004M"),  # non-Hispanic Black
    "race_hisp":      ("B03002_012E", "B03002_012M"),  # Hispanic/Latino any race

    "median_hh_inc":  ("B19013_001E", "B19013_001M"),
}

# %% [markdown]
# ## 2. Fetch ACS + tract geometries

# %%
def fetch_acs_tract(year: int, state: str, county: str, vars_map: dict) -> pd.DataFrame:
    """Pull all requested ACS variables for all tracts in the county."""
    if not CENSUS_API_KEY:
        raise RuntimeError("Set CENSUS_API_KEY env var. Free key: https://api.census.gov/data/key_signup.html")
    var_codes = [v for pair in vars_map.values() for v in pair]
    get = ",".join(["GEO_ID", "NAME"] + var_codes)
    url = (
        f"https://api.census.gov/data/{year}/acs/acs5"
        f"?get={get}&for=tract:*&in=state:{state}+county:{county}&key={CENSUS_API_KEY}"
    )
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    rows = r.json()
    df = pd.DataFrame(rows[1:], columns=rows[0])
    # GEOID for joins: 11-char string state(2)+county(3)+tract(6)
    df["GEOID"] = df["state"] + df["county"] + df["tract"]
    for code in var_codes:
        df[code] = pd.to_numeric(df[code], errors="coerce")
    return df


def fetch_tract_geoms(year: int, state: str, county: str) -> gpd.GeoDataFrame:
    """Download TIGER/Line tract shapefile, filter to county."""
    url = f"https://www2.census.gov/geo/tiger/TIGER{year}/TRACT/tl_{year}_{state}_tract.zip"
    local = DATA_RAW / f"tl_{year}_{state}_tract.zip"
    if not local.exists():
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        local.write_bytes(r.content)
    gdf = gpd.read_file(f"zip://{local}")
    gdf = gdf[gdf["COUNTYFP"] == county].copy()
    gdf = gdf.to_crs(4326)
    # project to meters for centroid / area work
    return gdf[["GEOID", "NAMELSAD", "ALAND", "AWATER", "geometry"]]


# %%
# Uncomment to run:
# acs_df = fetch_acs_tract(ACS_YEAR, NASSAU_STATE, NASSAU_COUNTY, ACS_VARS)
# tracts = fetch_tract_geoms(ACS_YEAR, NASSAU_STATE, NASSAU_COUNTY)
# tracts = tracts.merge(acs_df, on="GEOID", how="left")

# %% [markdown]
# ## 3. MOE propagation utilities
#
# ACS MOEs are 90% margins. For derived quantities, use the Census Bureau's formulas
# (ACS Handbook, Appendix 3):
#
# - **Sum**:      MOE(X+Y) = sqrt(MOE_X^2 + MOE_Y^2)
# - **Difference**: same as sum
# - **Proportion** (p = x / y, x is subset of y):
#   - MOE(p) = (1/y) * sqrt( MOE_x^2 - p^2 * MOE_y^2 )
#   - If the radicand is negative, fall back to the **ratio** formula (x not subset of y):
#   - MOE(p) = (1/y) * sqrt( MOE_x^2 + p^2 * MOE_y^2 )
# - **Product** (a * X where a is constant): a * MOE_X

# %%
def moe_sum(moes: np.ndarray) -> np.ndarray:
    """MOE for a sum of independent ACS estimates. moes shape: (n, k) -> (n,)."""
    return np.sqrt(np.sum(moes ** 2, axis=-1))


def moe_proportion(x: np.ndarray, y: np.ndarray, moe_x: np.ndarray, moe_y: np.ndarray) -> np.ndarray:
    """MOE for p = x / y.  Tries subset formula, falls back to ratio if radicand negative."""
    p = np.divide(x, y, out=np.zeros_like(x, dtype=float), where=y != 0)
    rad_subset = moe_x ** 2 - (p ** 2) * (moe_y ** 2)
    rad_ratio  = moe_x ** 2 + (p ** 2) * (moe_y ** 2)
    rad = np.where(rad_subset >= 0, rad_subset, rad_ratio)
    return np.divide(np.sqrt(rad), y, out=np.zeros_like(x, dtype=float), where=y != 0)


def moe_to_se(moe: np.ndarray) -> np.ndarray:
    return moe / MOE_Z

# %% [markdown]
# ## 4. Derive need indicators with MOE
#
# Four components (all z-scored, averaged with optional user weights):
# 1. **rent_burden_rate** = (rent_30+ categories) / rent_total
# 2. **poverty_rate**     = pov_below / pov_universe
# 3. **renter_share**     = renter_occ / tenure_total
# 4. **eviction_filing_rate** = filings / renter_occ   (from external data; see §5)

# %%
def build_acs_rates(tracts: gpd.GeoDataFrame) -> pd.DataFrame:
    """Return one row per tract with rate + MOE for each ACS-derived indicator."""
    t = tracts.copy()

    # --- rent burden (30%+) ---
    burden_cols = ["B25070_007E", "B25070_008E", "B25070_009E", "B25070_010E"]
    burden_moes = ["B25070_007M", "B25070_008M", "B25070_009M", "B25070_010M"]
    burdened_x = t[burden_cols].sum(axis=1).values
    burdened_moe = moe_sum(t[burden_moes].values)
    total_x, total_moe = t["B25070_001E"].values, t["B25070_001M"].values
    t["rent_burden_rate"] = np.divide(burdened_x, total_x,
                                      out=np.zeros_like(burdened_x, dtype=float),
                                      where=total_x != 0)
    t["rent_burden_moe"]  = moe_proportion(burdened_x, total_x, burdened_moe, total_moe)

    # --- poverty rate ---
    t["poverty_rate"] = np.divide(t["B17001_002E"], t["B17001_001E"],
                                  out=np.zeros(len(t)), where=t["B17001_001E"] != 0)
    t["poverty_moe"]  = moe_proportion(t["B17001_002E"].values, t["B17001_001E"].values,
                                       t["B17001_002M"].values, t["B17001_001M"].values)

    # --- renter share ---
    t["renter_share"] = np.divide(t["B25003_003E"], t["B25003_001E"],
                                  out=np.zeros(len(t)), where=t["B25003_001E"] != 0)
    t["renter_moe"]   = moe_proportion(t["B25003_003E"].values, t["B25003_001E"].values,
                                       t["B25003_003M"].values, t["B25003_001M"].values)

    keep = ["GEOID", "rent_burden_rate", "rent_burden_moe",
            "poverty_rate", "poverty_moe",
            "renter_share", "renter_moe",
            "B25003_003E",  # renter_occ — needed later for eviction rate
            "B03002_001E", "B03002_003E", "B03002_004E", "B03002_012E",
            "B19013_001E"]
    return t[keep].rename(columns={"B25003_003E": "renter_occ",
                                   "B03002_001E": "pop_total",
                                   "B03002_003E": "pop_nhw",
                                   "B03002_004E": "pop_nhb",
                                   "B03002_012E": "pop_hisp",
                                   "B19013_001E": "median_hh_inc"})


# %% [markdown]
# ## 5. Eviction filings — external source
#
# Options, in order of preference:
# 1. **NY OCA bulk data** (best granularity, requires FOIL request): https://www.nycourts.gov/
# 2. **Princeton Eviction Lab county-level**: https://data-downloads.evictionlab.org/
#    - Nassau has data but NY tract-level is sparse post-2016
# 3. **Housing Data Coalition / Right to Counsel NYC** for 5-borough only (Nassau not covered)
#
# Expected schema for our pipeline: `GEOID`, `filings_year`, `filings_count`.

# %%
def load_evictions(path: Path | None = None) -> pd.DataFrame:
    """TODO: replace with real loader. Returns tract-level filing counts for Nassau."""
    if path and path.exists():
        return pd.read_csv(path, dtype={"GEOID": str})
    # Stub: zero filings so the pipeline runs end-to-end.
    return pd.DataFrame(columns=["GEOID", "filings_count"])


def add_eviction_rate(need_df: pd.DataFrame, evictions: pd.DataFrame) -> pd.DataFrame:
    df = need_df.merge(evictions, on="GEOID", how="left")
    df["filings_count"] = df["filings_count"].fillna(0)
    df["eviction_filing_rate"] = np.divide(df["filings_count"], df["renter_occ"],
                                           out=np.zeros(len(df)), where=df["renter_occ"] > 0)
    # Empirical-Bayes shrinkage for small-N tracts
    df["eviction_filing_rate_eb"] = _empirical_bayes_rate(df["filings_count"].values,
                                                          df["renter_occ"].values)
    return df


def _empirical_bayes_rate(events: np.ndarray, exposure: np.ndarray) -> np.ndarray:
    """Shrink small-N tract rates toward county mean (Poisson-Gamma conjugate).
    Returns raw 0 rates when the county has no events (nothing to shrink toward)."""
    exposure = np.where(exposure <= 0, np.nan, exposure)
    tot_events = np.nansum(events)
    tot_exposure = np.nansum(exposure)
    if tot_events <= 0 or tot_exposure <= 0:
        # no events at all → rate is 0 everywhere; skip EB to avoid div-by-zero
        out = np.zeros_like(events, dtype=float)
        return out
    raw = events / exposure
    mu = tot_events / tot_exposure
    var = np.nanvar(raw)
    alpha = max(mu ** 2 / (var - mu / np.nanmean(exposure) + 1e-12), 1e-3)
    beta = alpha / mu
    return (events + alpha) / (exposure + beta)

# %% [markdown]
# ## 6. Need composite
#
# z-score each component, then weighted sum. Default weights = equal.
# Export the component z-scores so the frontend can let users change weights interactively.

# %%
NEED_COMPONENTS = ["rent_burden_rate", "poverty_rate", "renter_share", "eviction_filing_rate_eb"]


def zscore(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    m = np.nanmean(x)
    s = np.nanstd(x, ddof=0)
    return (x - m) / s if s > 0 else np.zeros_like(x)


def build_need(df: pd.DataFrame, weights: dict | None = None) -> pd.DataFrame:
    weights = weights or {c: 1 / len(NEED_COMPONENTS) for c in NEED_COMPONENTS}
    z_cols = {}
    for c in NEED_COMPONENTS:
        z_cols[f"z_{c}"] = zscore(df[c].values)
    z_df = pd.DataFrame(z_cols)
    df = pd.concat([df.reset_index(drop=True), z_df], axis=1)
    df["need_score"] = sum(weights[c] * df[f"z_{c}"] for c in NEED_COMPONENTS)
    return df

# %% [markdown]
# ## 7. Facility data
#
# Expected schema: `facility_id`, `type` (shelter/food_bank/pantry/etc.), `capacity`, `geometry` (Point).
# If capacity unknown, default to 1 (i.e., count facilities equally).
#
# Sources to wire in:
# - **Long Island Cares** partner locator
# - **Island Harvest** partner locations
# - **Nassau County DSS** shelter directory (FOIL may be needed)
# - **NY OTDA** emergency shelter list
# - **OSM** amenity=social_facility, amenity=food_bank for backfill

# %%
def load_facilities(path: Path | None = None) -> gpd.GeoDataFrame:
    """TODO: replace with real loader."""
    if path and path.exists():
        return gpd.read_file(path).to_crs(4326)
    # Stub — empty with correct schema
    return gpd.GeoDataFrame(
        {"facility_id": [], "type": [], "capacity": []},
        geometry=gpd.GeoSeries([], crs=4326),
    )

# %% [markdown]
# ## 8. Travel-time matrix
#
# Uses OSRM `/table` service. Returns (n_tracts, n_facilities) matrix in **minutes**.
# Falls back to haversine / assumed speed if OSRM unreachable — useful for quick
# iteration, but rerun with real routing before publishing.

# %%
def _osrm_table(sources: list[tuple[float, float]],
                destinations: list[tuple[float, float]],
                base_url: str) -> np.ndarray:
    """OSRM /table returns durations in seconds. coords are (lon, lat)."""
    coords = sources + destinations
    coords_str = ";".join(f"{lon:.6f},{lat:.6f}" for lon, lat in coords)
    src_idx = ";".join(str(i) for i in range(len(sources)))
    dst_idx = ";".join(str(i + len(sources)) for i in range(len(destinations)))
    url = f"{base_url}/table/v1/driving/{coords_str}?sources={src_idx}&destinations={dst_idx}&annotations=duration"
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    durations = np.array(r.json()["durations"])  # seconds
    return durations / 60.0


def _haversine_minutes(sources: list[tuple[float, float]],
                       destinations: list[tuple[float, float]],
                       speed_kmh: float) -> np.ndarray:
    """Fallback: straight-line distance / assumed speed."""
    R = 6371.0
    s = np.radians(np.array(sources))[:, None, :]     # (n_src, 1, 2) lon,lat
    d = np.radians(np.array(destinations))[None, :, :]  # (1, n_dst, 2)
    dlon = d[..., 0] - s[..., 0]
    dlat = d[..., 1] - s[..., 1]
    a = np.sin(dlat / 2) ** 2 + np.cos(s[..., 1]) * np.cos(d[..., 1]) * np.sin(dlon / 2) ** 2
    km = 2 * R * np.arcsin(np.sqrt(a))
    return km / speed_kmh * 60.0


def travel_time_matrix(tracts: gpd.GeoDataFrame, facilities: gpd.GeoDataFrame,
                       mode: str) -> np.ndarray:
    """mode in {'drive', 'walk'}. Returns (n_tracts, n_facilities) in minutes."""
    src = [(pt.x, pt.y) for pt in tracts.geometry.representative_point()]
    dst = [(pt.x, pt.y) for pt in facilities.geometry]
    base = OSRM_DRIVE if mode == "drive" else OSRM_WALK
    if base:
        try:
            return _osrm_table(src, dst, base)
        except Exception as e:
            print(f"[travel_time_matrix] OSRM failed ({e}); falling back to haversine.")
    speed = 40.0 if mode == "drive" else 4.8   # km/h
    return _haversine_minutes(src, dst, speed)

# %% [markdown]
# ## 9. Enhanced 2SFCA
#
# Luo & Qi (2009) gaussian decay, normalized so f(0)=1 and f(t0)=0.
#
# Step 1. For each facility j:  R_j = S_j / Σ_k ( P_k · W(t_kj) )
# Step 2. For each demand tract i:  A_i = Σ_j ( R_j · W(t_ij) )
#
# Where S_j = facility capacity, P_k = tract population (or renter households), t = travel time.

# %%
def luo_qi_decay(t: np.ndarray, t0: float) -> np.ndarray:
    """Gaussian decay; f(0)=1, f(t0)=0, 0 beyond t0."""
    t = np.asarray(t, dtype=float)
    inside = t <= t0
    out = np.zeros_like(t)
    numer = np.exp(-0.5 * (t / t0) ** 2) - np.exp(-0.5)
    denom = 1 - np.exp(-0.5)
    out = np.where(inside, numer / denom, 0.0)
    return out


def e2sfca(time_matrix: np.ndarray,
           demand: np.ndarray,
           supply: np.ndarray,
           catchment_min: float) -> np.ndarray:
    """E2SFCA accessibility score for each demand tract."""
    W = luo_qi_decay(time_matrix, catchment_min)            # (n_demand, n_supply)
    weighted_demand = (W * demand[:, None]).sum(axis=0)     # (n_supply,)
    R = np.divide(supply, weighted_demand,
                  out=np.zeros_like(supply, dtype=float),
                  where=weighted_demand > 0)
    A = (W * R[None, :]).sum(axis=1)                        # (n_demand,)
    return A

# %% [markdown]
# ## 10. Assemble the mismatch index

# %%
@dataclass
class PipelineConfig:
    catchment_min: float = 15.0
    mode: str = "drive"           # or 'walk'
    demand_col: str = "renter_occ"   # use renter households as the "at-risk" demand base
    need_weights: dict | None = None


def run_pipeline(tracts_base: gpd.GeoDataFrame,
                 facilities: gpd.GeoDataFrame,
                 evictions: pd.DataFrame,
                 cfg: PipelineConfig) -> gpd.GeoDataFrame:
    # --- need ---
    rates = build_acs_rates(tracts_base)
    rates = add_eviction_rate(rates, evictions)
    rates = build_need(rates, cfg.need_weights)

    # --- access ---
    if len(facilities) == 0:
        rates["access_score"] = 0.0
    else:
        demand = rates[cfg.demand_col].fillna(0).values.astype(float)
        supply = facilities["capacity"].fillna(1).values.astype(float)
        tt = travel_time_matrix(tracts_base, facilities, cfg.mode)
        rates["access_score"] = e2sfca(tt, demand, supply, cfg.catchment_min)

    rates["z_access"] = zscore(rates["access_score"].values)
    rates["mismatch_index"] = rates["need_score"] - rates["z_access"]
    # percentile rank (0–100) for easier UI
    rates["mismatch_pct"] = stats.rankdata(rates["mismatch_index"], method="average") \
                            / len(rates) * 100

    merged = tracts_base[["GEOID", "geometry"]].merge(rates, on="GEOID", how="left")
    return merged

# %% [markdown]
# ## 11. Write outputs

# %%
def write_outputs(gdf: gpd.GeoDataFrame, tag: str) -> None:
    # GeoJSON for Mapbox/MapLibre (keep small: round coords, drop heavy cols)
    slim = gdf.copy()
    for c in slim.columns:
        if pd.api.types.is_float_dtype(slim[c]):
            slim[c] = slim[c].round(4)
    slim.to_file(DATA_PROCESSED / f"tracts_{tag}.geojson", driver="GeoJSON")
    # Parquet for DuckDB-WASM in the browser (no geometry here — lighter)
    slim.drop(columns="geometry").to_parquet(DATA_PROCESSED / f"metrics_{tag}.parquet",
                                             index=False)
    print(f"wrote tracts_{tag}.geojson and metrics_{tag}.parquet")

# %% [markdown]
# ## 12. Glue it together
#
# Uncomment these to run end-to-end once the external data loaders are wired up.

# %%
# tracts_base = fetch_tract_geoms(ACS_YEAR, NASSAU_STATE, NASSAU_COUNTY)
# acs_df      = fetch_acs_tract(ACS_YEAR, NASSAU_STATE, NASSAU_COUNTY, ACS_VARS)
# tracts_base = tracts_base.merge(acs_df, on="GEOID", how="left")
#
# evictions   = load_evictions(DATA_RAW / "nassau_evictions_2022.csv")
# facilities  = load_facilities(DATA_RAW / "nassau_facilities.geojson")
#
# for mode, catch in [("drive", DRIVE_CATCHMENT_MIN), ("walk", WALK_CATCHMENT_MIN)]:
#     cfg = PipelineConfig(catchment_min=catch, mode=mode)
#     out = run_pipeline(tracts_base, facilities, evictions, cfg)
#     write_outputs(out, tag=mode)

# %% [markdown]
# ## 13. Sanity checks to add next
#
# - [ ] Moran's I on `mismatch_index` (expect positive spatial autocorrelation if index is real)
# - [ ] Bivariate Moran's I: `need_score` vs `access_score` (this is the core product claim)
# - [ ] Correlation of `mismatch_index` with independent validators (311 homeless-related calls, DSS intake counts by origin ZIP)
# - [ ] Leave-one-facility-out sensitivity: how much does removing one big facility shift the ranking?
# - [ ] Compare `eviction_filing_rate` vs `eviction_filing_rate_eb` — EB should smooth noise in low-renter tracts
