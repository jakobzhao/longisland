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
# # Long Island — Facility and Support Resource Collection
#
# Produces `data/processed/longisland_facilities.geojson`.
#
# The accessibility model should not treat every support office as the same kind
# of service. Food, shelter/intake, and outreach records feed the E2SFCA access
# score (`is_access_resource = True`). Legal aid, housing counseling, behavioral
# health, public benefits, and clinics stay in the public map as context layers.

# %%
from __future__ import annotations

import hashlib
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parent.parent if "__file__" in dir() else Path("..").resolve()
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
DATA_RAW.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

ACCESS_TYPES = {"food_pantry", "food_bank", "shelter", "shelter_intake", "outreach"}


def _stable_id(prefix: str, value: str) -> str:
    return f"{prefix}:{hashlib.md5(str(value).encode()).hexdigest()[:10]}"


def _clean_capacity(value) -> float:
    if pd.isna(value):
        return float("nan")
    text = str(value).strip()
    if not text or text.lower() in {"n/a", "na", "not publicly listed"}:
        return float("nan")
    return pd.to_numeric(text, errors="coerce")


def _resource_group(resource_type: str) -> str:
    rt = (resource_type or "").lower()
    if "food" in rt or "pantry" in rt:
        return "food"
    if "shelter" in rt or "homeless overnight" in rt or "emergency housing" in rt:
        return "shelter"
    if "outreach" in rt or "coalition for the homeless" in rt:
        return "outreach"
    if "legal" in rt or "eviction" in rt:
        return "legal"
    if "housing counseling" in rt or "tenant" in rt or "affordable housing" in rt:
        return "housing_support"
    if "behavioral" in rt or "mental health" in rt or "substance" in rt or "crisis" in rt:
        return "behavioral_health"
    if "public assistance" in rt or "benefits" in rt or "employment" in rt:
        return "public_benefits"
    if "clinic" in rt or "fqhc" in rt:
        return "health"
    return "other"


def _type_from_group(resource_type: str, group: str) -> str:
    rt = (resource_type or "").lower()
    if group == "food":
        return "food_pantry"
    if "intake" in rt or "access point" in rt:
        return "shelter_intake"
    if group == "shelter":
        return "shelter"
    if group == "outreach":
        return "outreach"
    return group


def _finalize(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf.to_crs(4326).copy()
    if "capacity" not in gdf.columns:
        gdf["capacity"] = float("nan")
    gdf["capacity"] = gdf["capacity"].map(_clean_capacity)
    gdf["is_access_resource"] = gdf["type"].isin(ACCESS_TYPES)
    keep = [
        "facility_id", "name", "type", "resource_group", "is_access_resource",
        "capacity", "county", "source", "address", "opening_time",
        "short_description", "coordinate_note", "verification_status",
        "source_url", "geometry",
    ]
    for col in keep:
        if col not in gdf.columns:
            gdf[col] = ""
    return gdf[keep]


def load_nassau_facilities() -> gpd.GeoDataFrame:
    """Load the previously consolidated Nassau facility layer."""
    path = DATA_RAW / "nassau_facilities.geojson"
    if not path.exists():
        path = DATA_PROCESSED / "nassau_facilities.geojson"
    if not path.exists():
        print("[nassau] skip — no consolidated Nassau facility GeoJSON found")
        return gpd.GeoDataFrame(columns=["geometry"], geometry="geometry", crs=4326)

    gdf = gpd.read_file(path).to_crs(4326)
    gdf["county"] = "Nassau"
    gdf["resource_group"] = gdf["type"].map({
        "food_pantry": "food",
        "food_bank": "food",
        "shelter": "shelter",
        "outreach": "outreach",
        "soup_kitchen": "food",
    }).fillna("other")
    gdf["opening_time"] = ""
    gdf["short_description"] = ""
    gdf["coordinate_note"] = "Existing Nassau geocoded facility layer"
    gdf["verification_status"] = "Carried forward from Nassau consolidated dataset"
    gdf["source_url"] = ""
    if "facility_id" not in gdf.columns:
        gdf["facility_id"] = gdf["name"].map(lambda name: _stable_id("nassau", name))
    print(f"[nassau] loaded {len(gdf)} facilities")
    return _finalize(gdf)


def load_suffolk_resources() -> gpd.GeoDataFrame:
    """Load the manually verified Suffolk resource CSV."""
    path = DATA_RAW / "suffolk_homelessness_resources.csv"
    if not path.exists():
        print(f"[suffolk] skip — no file at {path}")
        return gpd.GeoDataFrame(columns=["geometry"], geometry="geometry", crs=4326)

    df = pd.read_csv(path)
    df["resource_group"] = df["resource_type"].map(_resource_group)
    df["type"] = [
        _type_from_group(rt, group)
        for rt, group in zip(df["resource_type"], df["resource_group"])
    ]
    df["facility_id"] = df.apply(
        lambda r: _stable_id("suffolk", f"{r['name']}|{r['address']}"),
        axis=1,
    )
    df["county"] = "Suffolk"
    df["source"] = "suffolk_manual"
    df["capacity"] = df["capacity"].map(_clean_capacity)
    gdf = gpd.GeoDataFrame(
        df,
        geometry=[Point(lon, lat) for lon, lat in zip(df["longitude"], df["latitude"])],
        crs=4326,
    )
    print(f"[suffolk] loaded {len(gdf)} resources")
    return _finalize(gdf)


def collect_all() -> gpd.GeoDataFrame:
    gdfs = [load_nassau_facilities(), load_suffolk_resources()]
    gdfs = [g for g in gdfs if len(g) > 0]
    if not gdfs:
        raise RuntimeError("No facility/resource inputs were found.")

    gdf = pd.concat(gdfs, ignore_index=True)
    gdf = gpd.GeoDataFrame(gdf, geometry="geometry", crs=4326)

    out = DATA_PROCESSED / "longisland_facilities.geojson"
    gdf.to_file(out, driver="GeoJSON")

    print(f"\n[done] {len(gdf)} Long Island resources -> {out}")
    print("\nCounty counts:")
    print(gdf["county"].value_counts().to_string())
    print("\nType counts:")
    print(gdf["type"].value_counts().to_string())
    print("\nAccess-resource counts:")
    print(gdf["is_access_resource"].value_counts().to_string())
    return gdf


# %%
# collect_all()
