"""Driver: collect facilities -> build access-need index -> run spatial diagnostics.

Runs the three notebooks in order. Notebooks are loaded via importlib since
their filenames start with digits (not valid module names).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NB = ROOT / "notebooks"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main():
    print("\n========== 00: collect facilities ==========")
    collect = load("nb_collect", NB / "00_collect_facilities.py")
    facilities = collect.collect_all()
    print(f"facilities: {len(facilities)}")
    print(facilities["type"].value_counts().to_string())

    print("\n========== 01: build access-need index ==========")
    pipe = load("nb_pipeline", NB / "01_access_need_mismatch.py")

    tracts_base = pipe.fetch_tract_geoms(pipe.ACS_YEAR, pipe.NASSAU_STATE, pipe.NASSAU_COUNTY)
    print(f"tracts: {len(tracts_base)}")

    acs_df = pipe.fetch_acs_tract(pipe.ACS_YEAR, pipe.NASSAU_STATE, pipe.NASSAU_COUNTY, pipe.ACS_VARS)
    print(f"acs rows: {len(acs_df)}")
    tracts_base = tracts_base.merge(acs_df, on="GEOID", how="left")

    evictions = pipe.load_evictions(pipe.DATA_RAW / "nassau_evictions_2022.csv")
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

    print("\n========== DONE ==========")
    print(f"outputs -> {pipe.DATA_PROCESSED}/")


if __name__ == "__main__":
    main()
