"""Driver: collect resources -> build access-need index -> run spatial diagnostics.

Runs the three notebooks in order. Notebooks are loaded via importlib since
their filenames start with digits (not valid module names).
"""
from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NB = ROOT / "notebooks"
DOCS = ROOT / "docs"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def sync_docs_outputs(data_processed: Path) -> None:
    DOCS.mkdir(exist_ok=True)
    for name in [
        "longisland_facilities.geojson",
        "tracts_drive.geojson",
        "tracts_walk.geojson",
        "tracts_drive_diagnostics.geojson",
        "tracts_walk_diagnostics.geojson",
        "diagnostics_drive.json",
        "diagnostics_walk.json",
        "homeless_students_districts.geojson",
    ]:
        src = data_processed / name
        if src.exists():
            shutil.copy2(src, DOCS / name)
    old = DOCS / "nassau_facilities.geojson"
    if old.exists():
        old.unlink()


def main():
    print("\n========== 00: collect Long Island resources ==========")
    collect = load("nb_collect", NB / "00_collect_facilities.py")
    facilities = collect.collect_all()
    print(f"resources: {len(facilities)}")
    print(facilities["type"].value_counts().to_string())
    if "is_access_resource" in facilities.columns:
        print("\naccess resources:")
        print(facilities["is_access_resource"].value_counts().to_string())

    print("\n========== 01: build access-need index ==========")
    pipe = load("nb_pipeline", NB / "01_access_need_mismatch.py")

    tracts_base = pipe.fetch_long_island_tract_geoms(pipe.ACS_YEAR)
    print(f"tracts: {len(tracts_base)}")
    print(tracts_base["county_name"].value_counts().to_string())

    acs_df = pipe.fetch_acs_long_island(pipe.ACS_YEAR, pipe.ACS_VARS)
    print(f"acs rows: {len(acs_df)}")
    acs_df = acs_df.drop(columns=["county_name"], errors="ignore")
    tracts_base = tracts_base.merge(acs_df, on="GEOID", how="left")

    evictions = pipe.load_evictions(pipe.DATA_RAW / "longisland_evictions_2022.csv")
    print(f"eviction rows: {len(evictions)} "
          f"{'(STUB — access layer only; need composite missing eviction component)' if len(evictions) == 0 else ''}")

    for mode, catch in [("drive", pipe.DRIVE_CATCHMENT_MIN),
                        ("walk", pipe.WALK_CATCHMENT_MIN)]:
        print(f"\n-- run {mode} --")
        cfg = pipe.PipelineConfig(catchment_min=catch, mode=mode)
        out = pipe.run_pipeline(tracts_base, facilities, evictions, cfg)
        pipe.write_outputs(out, tag=mode)

    print("\n========== 02: spatial diagnostics ==========")
    diag = load("nb_diag", NB / "02_spatial_diagnostics.py")
    for mode in ["drive", "walk"]:
        print(f"\n-- diagnostics {mode} --")
        try:
            diag.run_diagnostics(mode)
        except FileNotFoundError as e:
            print(f"[skip] {e}")

    print("\n========== 03: homeless student district layer ==========")
    students = load("nb_students", NB / "03_homeless_students.py")
    students.build()

    print("\n========== sync docs outputs ==========")
    sync_docs_outputs(pipe.DATA_PROCESSED)

    print("\n========== DONE ==========")
    print(f"outputs -> {pipe.DATA_PROCESSED}/ and {DOCS}/")


if __name__ == "__main__":
    main()
