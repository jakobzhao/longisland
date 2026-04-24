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
# # Nassau County — Facility Data Collection
#
# Produces `data/raw/nassau_facilities.geojson` in the schema expected by
# `01_access_need_mismatch.py`:
# `facility_id, name, type, capacity, source, address, geometry(Point)`
#
# Sources merged:
# 1. **OSM** via Overpass — fully automated (this file)
# 2. **Long Island Cares** partner locator — web scrape, may change; stub here
# 3. **Island Harvest** partner locations — same
# 4. **NY OTDA** emergency shelter list — PDF/HTML, stub
# 5. **Nassau County DSS** — FOIL request; manual CSV drop
#
# Dedup: point within 50 m + fuzzy name match ≥ 0.8 → collapse, prefer source with
# the most complete fields.

# %%
from __future__ import annotations

import hashlib
import json
import time
from difflib import SequenceMatcher
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import Point

# %% [markdown]
# ## 0. Config

# %%
ROOT = Path(__file__).resolve().parent.parent if "__file__" in dir() else Path("..").resolve()
DATA_RAW = ROOT / "data" / "raw"
DATA_RAW.mkdir(parents=True, exist_ok=True)

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",  # fallback
]

METRIC_CRS = 32618      # UTM 18N, meters, for dedup distance
DEDUP_DIST_M = 50
DEDUP_NAME_SIM = 0.80

# %% [markdown]
# ## 1. OSM via Overpass
#
# Pulls anything likely to be a homelessness-adjacent service:
# `amenity=social_facility`, `amenity=food_bank`, `amenity=social_centre`,
# `amenity=community_centre` (when tagged with `social_facility:for`),
# plus legacy `social_facility=shelter|food_bank|soup_kitchen|outreach`.

# %%
# Nassau County NY = OSM relation 2552442 (FIPS 36059). Other "Nassau County"
# relations exist (Florida's FIPS 12089); using the numeric id avoids ambiguity.
NASSAU_NY_AREA_ID = 3602552442
USER_AGENT = "nassau-homeless-research/0.1 (jakobzhao@gmail.com)"

OVERPASS_QL = f"""
[out:json][timeout:90];
area(id:{NASSAU_NY_AREA_ID})->.nassau;
(
  nwr["amenity"="social_facility"](area.nassau);
  nwr["amenity"="food_bank"](area.nassau);
  nwr["amenity"="social_centre"](area.nassau);
  nwr["social_facility"~"shelter|food_bank|soup_kitchen|outreach"](area.nassau);
  nwr["social_facility:for"~"homeless|poor|unemployed|migrant"](area.nassau);
  nwr["office"="charity"](area.nassau);
);
out center tags;
"""


def fetch_osm_facilities() -> gpd.GeoDataFrame:
    """Query Overpass; fall back across endpoints; return GeoDataFrame."""
    headers = {"User-Agent": USER_AGENT}
    last_err = None
    for url in OVERPASS_ENDPOINTS:
        try:
            r = requests.post(url, data={"data": OVERPASS_QL},
                              headers=headers, timeout=180)
            r.raise_for_status()
            elements = r.json().get("elements", [])
            break
        except Exception as e:
            last_err = e
            print(f"[overpass] {url} failed: {e}")
            time.sleep(2)
    else:
        raise RuntimeError(f"all overpass endpoints failed: {last_err}")

    rows = []
    for el in elements:
        if el["type"] == "node":
            lon, lat = el["lon"], el["lat"]
        elif "center" in el:
            lon, lat = el["center"]["lon"], el["center"]["lat"]
        else:
            continue
        tags = el.get("tags", {})
        rows.append({
            "facility_id": f"osm:{el['type'][0]}{el['id']}",
            "name": tags.get("name") or tags.get("operator") or "(unnamed)",
            "type": _osm_type(tags),
            "is_homelessness_service": _osm_is_homelessness_service(tags),
            "capacity": _osm_capacity(tags),
            "source": "osm",
            "address": _osm_address(tags),
            "osm_tags": tags,
            "geometry": Point(lon, lat),
        })
    gdf = gpd.GeoDataFrame(rows, crs=4326)
    print(f"[osm] fetched {len(gdf)} raw features "
          f"({int(gdf['is_homelessness_service'].sum())} flagged homelessness-relevant)")
    return gdf


# --- OSM tag -> our type vocabulary ---
#
# Key distinction: OSM `social_facility=group_home` and `=nursing_home` are
# elder-care / disability facilities, NOT homeless shelter. Do not classify as
# shelter. Require an explicit shelter tag or `for=homeless`.
def _osm_type(tags: dict) -> str:
    sf = tags.get("social_facility") or ""
    sf_for = tags.get("social_facility:for") or ""
    amenity = tags.get("amenity") or ""
    if sf == "shelter" or "homeless" in sf_for:
        return "shelter"
    if sf == "food_bank" or amenity == "food_bank":
        return "food_bank"
    if sf == "soup_kitchen":
        return "soup_kitchen"
    if sf == "outreach":
        return "outreach"
    if sf in ("group_home", "nursing_home", "assisted_living"):
        return "elder_or_disability_care"      # excluded from homelessness analysis
    if amenity == "social_facility":
        return "social_facility_other"
    if amenity == "social_centre":
        return "social_centre"                  # mostly VFW/Legion posts in Nassau
    if tags.get("office") == "charity":
        return "charity_office"
    return "other"


# Homelessness-service whitelist. These are the types that should feed into
# access-need mismatch. Everything else is kept in the file (for transparency
# and possible context layers) but flagged False.
_HOMELESSNESS_TYPES = {"shelter", "food_bank", "soup_kitchen", "food_pantry", "outreach"}


def _osm_is_homelessness_service(tags: dict) -> bool:
    if _osm_type(tags) in _HOMELESSNESS_TYPES:
        return True
    # charity offices occasionally run pantries; keep as candidate if name hints
    name = (tags.get("name") or "").lower()
    if any(k in name for k in ("pantry", "food bank", "shelter", "soup kitchen",
                               "homeless", "rescue mission")):
        return True
    return False


def _osm_capacity(tags: dict) -> float:
    """OSM rarely has capacity; return NaN and let pipeline default to 1."""
    for k in ("capacity", "capacity:persons", "beds"):
        v = tags.get(k)
        if v and v.isdigit():
            return float(v)
    return float("nan")


def _osm_address(tags: dict) -> str:
    parts = [tags.get("addr:housenumber"), tags.get("addr:street"),
             tags.get("addr:city"), tags.get("addr:state"),
             tags.get("addr:postcode")]
    return " ".join(p for p in parts if p).strip() or ""

# %% [markdown]
# ## 2. Stub loaders — non-OSM sources
#
# These require manual data gathering because the sites don't expose APIs.
# Workflow for each:
# 1. Visit the site, extract the list (usually a `/locations` or `/find-food` page)
# 2. Save as CSV to `data/raw/<source>_raw.csv` with columns: `name, address`
# 3. Run the matching loader to geocode and normalize

# %%
def _load_manual_csv(path: Path, source_tag: str, facility_type: str) -> gpd.GeoDataFrame:
    """Expected CSV columns: name, address, [city, state, zip, phone, capacity, lon, lat].

    If lon/lat already present (e.g., from a source API that returned coordinates),
    geocoding is skipped. Otherwise the address column is passed to the Census
    Geocoder."""
    if not path.exists():
        print(f"[{source_tag}] skip — no file at {path}")
        return gpd.GeoDataFrame(columns=["facility_id", "name", "type", "capacity",
                                         "source", "address", "geometry"], crs=4326)
    df = pd.read_csv(path)
    df["capacity"] = df.get("capacity", float("nan"))

    has_coords = "lon" in df.columns and "lat" in df.columns \
                 and df[["lon", "lat"]].notna().all(axis=1).any()
    if not has_coords:
        # Build full address for better geocoder hit rate
        full = df.apply(lambda r: ", ".join(
            str(r[c]) for c in ("address", "city", "state", "zip")
            if c in df.columns and pd.notna(r[c]) and str(r[c]).strip()), axis=1)
        coords = census_geocode(full.tolist())
        df = df.join(coords)

    before = len(df)
    df = df.dropna(subset=["lon", "lat"]).reset_index(drop=True)
    print(f"[{source_tag}] kept {len(df)}/{before} "
          f"({'coords pre-supplied' if has_coords else 'geocoded via Census'})")

    df["facility_id"] = df["name"].apply(
        lambda n: f"{source_tag}:" + hashlib.md5(str(n).encode()).hexdigest()[:10])
    df["source"] = source_tag
    df["type"] = facility_type
    gdf = gpd.GeoDataFrame(
        df[["facility_id", "name", "type", "capacity", "source", "address"]],
        geometry=[Point(lon, lat) for lon, lat in zip(df["lon"], df["lat"])],
        crs=4326,
    )
    return gdf


def load_li_cares() -> gpd.GeoDataFrame:
    """Long Island Cares partner pantries.
    Manual step: find-food page -> scrape to data/raw/li_cares_raw.csv"""
    return _load_manual_csv(DATA_RAW / "li_cares_raw.csv", "licares", "food_pantry")


def load_island_harvest() -> gpd.GeoDataFrame:
    """Island Harvest partner agencies.
    Manual step: food-assistance locator -> data/raw/island_harvest_raw.csv"""
    return _load_manual_csv(DATA_RAW / "island_harvest_raw.csv", "iharvest", "food_pantry")


def load_otda_shelters() -> gpd.GeoDataFrame:
    """NY OTDA emergency shelters in Nassau.
    Manual step: OTDA shelter directory PDF -> data/raw/otda_shelters_raw.csv"""
    return _load_manual_csv(DATA_RAW / "otda_shelters_raw.csv", "otda", "shelter")


def load_dss_shelters() -> gpd.GeoDataFrame:
    """Nassau County DSS placements — requires FOIL request.
    Drop CSV at data/raw/dss_shelters_raw.csv when obtained."""
    return _load_manual_csv(DATA_RAW / "dss_shelters_raw.csv", "dss", "shelter")


def load_rhy() -> gpd.GeoDataFrame:
    """Runaway & Homeless Youth agencies (NY OCFS via data.ny.gov). Comes
    pre-geocoded (georeference field)."""
    return _load_manual_csv(DATA_RAW / "otda_rhy_raw.csv", "rhy", "shelter")

# %% [markdown]
# ## 3. Geocoder — US Census (free, no key, US-only, high quality)

# %%
CENSUS_GEOCODER = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"


def census_geocode(addresses: list[str]) -> pd.DataFrame:
    """One-off geocoding via Census. Returns DataFrame with columns lon, lat."""
    out = []
    for addr in addresses:
        if not isinstance(addr, str) or not addr.strip():
            out.append({"lon": None, "lat": None})
            continue
        try:
            r = requests.get(CENSUS_GEOCODER, params={
                "address": addr, "benchmark": "Public_AR_Current", "format": "json",
            }, timeout=20)
            r.raise_for_status()
            matches = r.json().get("result", {}).get("addressMatches", [])
            if matches:
                c = matches[0]["coordinates"]
                out.append({"lon": c["x"], "lat": c["y"]})
            else:
                out.append({"lon": None, "lat": None})
        except Exception as e:
            print(f"[geocode] {addr!r} failed: {e}")
            out.append({"lon": None, "lat": None})
        time.sleep(0.1)  # polite
    return pd.DataFrame(out)

# %% [markdown]
# ## 4. Deduplication
#
# Two records are duplicates if:
# - they are within `DEDUP_DIST_M` meters, AND
# - their name similarity ≥ `DEDUP_NAME_SIM`
#
# When collapsing, prefer the record with the most non-null fields; keep OSM's
# tag dict as a tie-breaker. Source provenance is kept in `source`.

# %%
def _name_sim(a: str, b: str) -> float:
    a, b = (a or "").lower(), (b or "").lower()
    return SequenceMatcher(None, a, b).ratio()


def _completeness(row: pd.Series) -> int:
    cols = ["name", "type", "capacity", "address"]
    return sum(1 for c in cols if pd.notna(row.get(c)) and str(row.get(c)).strip()
               and row.get(c) != "(unnamed)")


def dedup_facilities(gdfs: list[gpd.GeoDataFrame]) -> gpd.GeoDataFrame:
    non_empty = [g for g in gdfs if len(g) > 0]
    if not non_empty:
        return gpd.GeoDataFrame(
            columns=["facility_id", "name", "type", "capacity",
                     "source", "address", "geometry"], crs=4326)
    merged = pd.concat(non_empty, ignore_index=True)
    merged = gpd.GeoDataFrame(merged, geometry="geometry", crs=4326)

    proj = merged.to_crs(METRIC_CRS)
    keep = [True] * len(merged)
    # O(n^2) — fine for <2000 facilities
    for i in range(len(merged)):
        if not keep[i]:
            continue
        for j in range(i + 1, len(merged)):
            if not keep[j]:
                continue
            d = proj.geometry.iloc[i].distance(proj.geometry.iloc[j])
            if d > DEDUP_DIST_M:
                continue
            if _name_sim(merged["name"].iloc[i], merged["name"].iloc[j]) < DEDUP_NAME_SIM:
                continue
            # keep the more complete row
            if _completeness(merged.iloc[i]) >= _completeness(merged.iloc[j]):
                keep[j] = False
            else:
                keep[i] = False
                break
    dedup = merged[keep].reset_index(drop=True)
    print(f"[dedup] {len(merged)} -> {len(dedup)} ({len(merged) - len(dedup)} merged)")
    return dedup

# %% [markdown]
# ## 5. Assemble and write

# %%
def collect_all() -> gpd.GeoDataFrame:
    sources = [
        fetch_osm_facilities(),
        load_li_cares(),
        load_island_harvest(),
        load_otda_shelters(),
        load_dss_shelters(),
        load_rhy(),
    ]
    gdf = dedup_facilities(sources)

    # Drop OSM categories that are not homelessness-related at all
    # (elder_or_disability_care, charity_office, social_centre — the VFW posts etc.)
    if "is_homelessness_service" in gdf.columns:
        before = len(gdf)
        gdf = gdf[gdf["is_homelessness_service"].fillna(True)].reset_index(drop=True)
        print(f"[filter] kept {len(gdf)}/{before} homelessness-relevant")

    # strip OSM tag dict before writing (not JSON-clean for shapefile, ugly for GeoJSON)
    if "osm_tags" in gdf.columns:
        gdf = gdf.drop(columns=["osm_tags"])

    # Write into processed/ so the static site's publicDir only needs to include one folder.
    # Raw source CSVs stay under raw/ for provenance.
    DATA_PROCESSED = DATA_RAW.parent / "processed"
    DATA_PROCESSED.mkdir(exist_ok=True)
    out = DATA_PROCESSED / "nassau_facilities.geojson"
    gdf.to_file(out, driver="GeoJSON")

    print(f"\n[done] {len(gdf)} facilities -> {out}")
    print("\nType counts:")
    print(gdf["type"].value_counts().to_string())
    print("\nSource counts:")
    print(gdf["source"].value_counts().to_string())
    return gdf

# %% [markdown]
# ## 6. Run
#
# Uncomment when ready. OSM portion runs standalone; others silently skip if the
# manual CSVs don't exist.

# %%
# collect_all()

# %% [markdown]
# ## 7. TODO: eviction data (separate notebook)
#
# `03_collect_evictions.py` will pull, in order of preference:
# 1. **Princeton Eviction Lab** tract-level CSV for Nassau (coverage may be partial post-2016)
# 2. **NY OCA bulk data** via FOIL — raw housing court dockets, geocode to tract
# 3. Fallback: county-level totals only, do rate analysis at municipality not tract
