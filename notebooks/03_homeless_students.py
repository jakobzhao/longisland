# %% [markdown]
# # 03 — NYSED McKinney-Vento homeless students (Long Island school districts)
#
# Joins NYSED 3-year SIRS data on student homelessness (2018-19 → 2020-21)
# to TIGER 2023 school district boundaries (UNSD + ELSD + SCSD) clipped to
# Nassau and Suffolk, producing `docs/homeless_students_districts.geojson`.
#
# Output polygons are non-overlapping as much as possible: unified (K-12)
# districts keep their own counts, and elementary districts are dissolved into
# containing secondary districts with summed K-12 totals.
#
# Caveats reported in UI:
# - Total includes unaccompanied youth (no public district-level split;
#   ~10-12% nationally per CSPR).
# - "Experienced homelessness at any point" definition (McKinney-Vento):
#   includes doubled-up due to economic hardship.
# - Duplicated across LEAs when a student moved mid-year.

# %%
import re
from pathlib import Path
from time import sleep

import openpyxl
import pandas as pd
import geopandas as gpd
import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
DOCS = ROOT / "docs"
DATA_RAW.mkdir(parents=True, exist_ok=True)

NYSED_XLSX_URL = (
    "https://www.nysteachs.org/_files/ugd/10c789_"
    "aa90519997814d7ab0f4602ebf23fb29.xlsx"
)
TIGER_YEAR = 2023
TIGER_STATE = "36"  # NY
LONG_ISLAND_COUNTIES = {"NASSAU", "SUFFOLK"}
LONG_ISLAND_COUNTYFPS = {"059", "103"}

# %% [markdown]
# ## 1. Download NYSED 3-year SIRS homelessness summary

# %%
def download_nysed():
    out = DATA_RAW / "nysed_homeless_3yr.xlsx"
    if not out.exists():
        r = requests.get(NYSED_XLSX_URL, timeout=60)
        r.raise_for_status()
        out.write_bytes(r.content)
    return out

def parse_nysed(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb["DUP_Data_3Years"]
    rows = list(ws.iter_rows(values_only=True))
    hdr_idx = next(i for i, r in enumerate(rows) if r[0] == "Bedscode")
    headers = rows[hdr_idx]
    recs = [dict(zip(headers, r)) for r in rows[hdr_idx + 1:] if r[0]]
    df = pd.DataFrame(recs)
    df = df[df["COUNTY NAME"].str.upper().str.strip().isin(LONG_ISLAND_COUNTIES)].copy()
    # coerce 's' (suppressed 1–4) to NaN, else numeric
    for c in ["2018-19 Dup Total", "2019-20 Dup Total",
              "2020-21 Dup Total", "3-Year Average"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

# %% [markdown]
# ## 2. Download TIGER school district boundaries

# %%
def download_tiger(kind):
    url = (
        f"https://www2.census.gov/geo/tiger/TIGER{TIGER_YEAR}/"
        f"{kind.upper()}/tl_{TIGER_YEAR}_{TIGER_STATE}_{kind}.zip"
    )
    out_zip = DATA_RAW / f"tl_{TIGER_YEAR}_{TIGER_STATE}_{kind}.zip"
    if not out_zip.exists():
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        out_zip.write_bytes(r.content)
    return gpd.read_file(f"zip://{out_zip}")


def download_binary(url, out_path, timeout=180, attempts=3):
    tmp_path = out_path.with_suffix(out_path.suffix + ".part")
    for attempt in range(1, attempts + 1):
        try:
            with requests.get(url, timeout=timeout, stream=True) as r:
                r.raise_for_status()
                with tmp_path.open("wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
            tmp_path.replace(out_path)
            return out_path
        except requests.RequestException:
            tmp_path.unlink(missing_ok=True)
            if attempt == attempts:
                raise
            sleep(2 * attempt)
    return out_path


def long_island_county_geom_2263():
    """Use full county tract coverage to identify Nassau + Suffolk."""
    tract_zip = DATA_RAW / "tl_2022_36_tract.zip"
    if not tract_zip.exists():
        url = "https://www2.census.gov/geo/tiger/TIGER2022/TRACT/tl_2022_36_tract.zip"
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        tract_zip.write_bytes(r.content)
    tracts = gpd.read_file(f"zip://{tract_zip}")
    tracts = tracts[tracts["COUNTYFP"].isin(LONG_ISLAND_COUNTYFPS)].copy()
    return tracts.to_crs(2263).union_all()


def long_island_land_geom_2263():
    """Land-only clipping mask for K-12 districts.

    TIGER school-district polygons often extend into bays, the Sound, and the
    Atlantic. Subtracting TIGER AREAWATER keeps the school layer readable while
    preserving coastal districts on land.
    """
    county_geom = long_island_county_geom_2263()
    water_parts = []
    for county_fp in sorted(LONG_ISLAND_COUNTYFPS):
        county_geoid = f"{TIGER_STATE}{county_fp}"
        water_zip = DATA_RAW / f"tl_{TIGER_YEAR}_{county_geoid}_areawater.zip"
        url = (
            f"https://www2.census.gov/geo/tiger/TIGER{TIGER_YEAR}/"
            f"AREAWATER/tl_{TIGER_YEAR}_{county_geoid}_areawater.zip"
        )
        if not water_zip.exists():
            download_binary(url, water_zip)
        water_parts.append(gpd.read_file(f"zip://{water_zip}"))

    water = pd.concat(water_parts, ignore_index=True)
    water = gpd.GeoDataFrame(water, geometry="geometry", crs=water_parts[0].crs)
    water = water.to_crs(2263)
    water = water[water.intersects(county_geom)].copy()
    water_geom = water.union_all()
    return county_geom.difference(water_geom).buffer(0)


def long_island_county_lookup_2263():
    tract_zip = DATA_RAW / "tl_2022_36_tract.zip"
    if not tract_zip.exists():
        long_island_county_geom_2263()
    tracts = gpd.read_file(f"zip://{tract_zip}")
    tracts = tracts[tracts["COUNTYFP"].isin(LONG_ISLAND_COUNTYFPS)].copy()
    tracts["county_name"] = tracts["COUNTYFP"].map({"059": "NASSAU", "103": "SUFFOLK"})
    return tracts.to_crs(2263).dissolve(by="county_name").reset_index()[["county_name", "geometry"]]


def select_long_island(gdf, selection_geom_2263):
    g = gdf.to_crs(2263)
    mask = g.geometry.centroid.within(selection_geom_2263.buffer(100))
    return gdf.loc[mask].copy()

# %% [markdown]
# ## 3. Name normalisation and join

# %%
def norm_name(s):
    s = (s or "").upper()
    s = re.sub(r"\bUNION FREE SCHOOL DISTRICT\b|\bUFSD\b", "", s)
    s = re.sub(r"\bCENTRAL HIGH SCHOOL DISTRICT\b|\bCENTRAL HS DISTRICT\b", " HS", s)
    s = re.sub(r"\bCENTRAL SCHOOL DISTRICT\b|\bCSD\b", "", s)
    s = re.sub(r"\bCITY SD\b|\bCITY SCHOOL DISTRICT\b", "", s)
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

# %% [markdown]
# ## 4. Build

# %%
def build():
    long_island_geom = long_island_county_geom_2263()
    long_island_land_geom = long_island_land_geom_2263()

    unsd = select_long_island(download_tiger("unsd"), long_island_geom)
    elsd = select_long_island(download_tiger("elsd"), long_island_geom)
    scsd = select_long_island(download_tiger("scsd"), long_island_geom)
    unsd["LEVEL"] = "UNSD"
    elsd["LEVEL"] = "ELSD"
    scsd["LEVEL"] = "SCSD"

    districts = pd.concat([unsd, elsd, scsd], ignore_index=True)
    districts["key"] = districts["NAME"].map(norm_name)

    nysed = parse_nysed(download_nysed())
    nysed["key"] = nysed["LEA NAME"].map(norm_name)

    # Attach counts to each TIGER district
    count_by_key = (
        nysed[nysed["ORG TYPE"] == "SCHOOL DISTRICT"]
        .set_index("key")["3-Year Average"].to_dict()
    )
    count_2020_by_key = (
        nysed[nysed["ORG TYPE"] == "SCHOOL DISTRICT"]
        .set_index("key")["2020-21 Dup Total"].to_dict()
    )
    beds_by_key = (
        nysed[nysed["ORG TYPE"] == "SCHOOL DISTRICT"]
        .set_index("key")["Bedscode"].to_dict()
    )
    county_by_key = (
        nysed[nysed["ORG TYPE"] == "SCHOOL DISTRICT"]
        .set_index("key")["COUNTY NAME"].to_dict()
    )

    districts["homeless_avg_3yr"] = districts["key"].map(count_by_key)
    districts["homeless_2020_21"] = districts["key"].map(count_2020_by_key)
    districts["bedscode"] = districts["key"].map(beds_by_key)
    districts["county_name"] = districts["key"].map(county_by_key)

    # Dissolve ELSD into containing SCSD so we have one K-12 count per
    # non-unified region.
    scsd_only = districts[districts["LEVEL"] == "SCSD"].copy()
    elsd_only = districts[districts["LEVEL"] == "ELSD"].copy()
    unsd_only = districts[districts["LEVEL"] == "UNSD"].copy()

    # Spatial containment of ELSD centroid within SCSD polygons.
    scsd_only_2263 = scsd_only.to_crs(2263)
    elsd_only_2263 = elsd_only.to_crs(2263)
    elsd_only_2263["pt"] = elsd_only_2263.geometry.centroid
    els_with_scsd = gpd.sjoin(
        elsd_only_2263.set_geometry("pt"),
        scsd_only_2263[["GEOID", "NAME", "geometry"]].rename(
            columns={"GEOID": "scsd_geoid", "NAME": "scsd_name"}
        ),
        how="left", predicate="within",
    )

    # Sum ELSD counts inside each SCSD
    elsd_sum = (
        els_with_scsd.groupby("scsd_geoid")
        .agg(elsd_total=("homeless_avg_3yr", "sum"),
             elsd_2020=("homeless_2020_21", "sum"),
             elsd_children=("NAME", list))
        .reset_index()
    )

    scsd_merged = scsd_only.merge(
        elsd_sum, left_on="GEOID", right_on="scsd_geoid", how="left"
    )
    scsd_merged["homeless_k12_avg"] = (
        scsd_merged["homeless_avg_3yr"].fillna(0)
        + scsd_merged["elsd_total"].fillna(0)
    )
    scsd_merged["homeless_k12_2020"] = (
        scsd_merged["homeless_2020_21"].fillna(0)
        + scsd_merged["elsd_2020"].fillna(0)
    )
    scsd_merged["display_name"] = scsd_merged["NAME"] + " (elem + high)"
    scsd_merged["composition"] = scsd_merged["elsd_children"].apply(
        lambda xs: xs if isinstance(xs, list) else []
    )

    unsd_only["homeless_k12_avg"] = unsd_only["homeless_avg_3yr"].fillna(0)
    unsd_only["homeless_k12_2020"] = unsd_only["homeless_2020_21"].fillna(0)
    unsd_only["display_name"] = unsd_only["NAME"]
    unsd_only["composition"] = [[] for _ in range(len(unsd_only))]

    final = pd.concat(
        [unsd_only, scsd_merged[unsd_only.columns]],
        ignore_index=True,
    )
    final = gpd.GeoDataFrame(final, geometry="geometry", crs=unsd_only.crs)

    county_lookup = long_island_county_lookup_2263()
    final_2263 = final.to_crs(2263).copy()
    final_2263["district_pt"] = final_2263.geometry.representative_point()
    county_join = gpd.sjoin(
        final_2263.set_geometry("district_pt"),
        county_lookup,
        how="left",
        predicate="within",
    )[["GEOID", "county_name_right"]]
    final = final.merge(county_join, on="GEOID", how="left")
    final["county_name"] = final["county_name"].fillna(final["county_name_right"])
    final = final.drop(columns=["county_name_right"], errors="ignore")

    final_crs = final.crs
    final_2263 = final.to_crs(2263).copy()
    final_2263["geometry"] = final_2263.geometry.intersection(long_island_land_geom)
    final_2263 = final_2263[~final_2263.geometry.is_empty].copy()
    final = final_2263.to_crs(final_crs)

    # Enrollment-based rate would be better, but NYSED 3-year file doesn't
    # include enrollment. Leave count-only and let the UI decide styling.
    out_cols = [
        "GEOID", "display_name", "LEVEL",
        "homeless_k12_avg", "homeless_k12_2020",
        "bedscode", "county_name", "composition", "geometry",
    ]
    final = final[out_cols]
    final.to_file(DOCS / "homeless_students_districts.geojson", driver="GeoJSON")
    final.to_file(DATA_PROCESSED / "homeless_students_districts.geojson", driver="GeoJSON")
    final.drop(columns="geometry").to_csv(
        DATA_PROCESSED / "homeless_students_districts.csv", index=False
    )

    print(f"wrote {len(final)} district polygons")
    print(
        final[["display_name", "homeless_k12_avg", "homeless_k12_2020"]]
        .sort_values("homeless_k12_avg", ascending=False)
        .head(15)
        .to_string(index=False)
    )
    print(f"\ncounty total (3-yr avg): {final['homeless_k12_avg'].sum():.0f}")

# %%
if __name__ == "__main__":
    build()
