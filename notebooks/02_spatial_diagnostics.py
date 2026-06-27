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
# # Long Island — Spatial Diagnostics
#
# Runs after `01_access_need_mismatch.py`. Inputs = `data/processed/tracts_{mode}.geojson`
# produced there; outputs = enriched GeoJSON (LISA labels, Gi* scores) + a
# `diagnostics_summary.json` that lives next to the frontend as a "methodology" panel.
#
# What this notebook answers:
# 1. Is each indicator **spatially clustered** at all? (Global Moran's I)
# 2. **Does service follow need?** Bivariate Moran's I(need, access) — this is the
#    product's validation gate. Strong positive = services already track need, no
#    "mismatch" story to tell. Near-zero or negative = mismatch index has signal.
# 3. **Where** are the clusters? (Local Moran's I / LISA) — per-tract HH/LL/HL/LH labels.
# 4. **Where are the hotspots** of unmet need? (Getis-Ord Gi*)
# 5. **How sensitive are these findings to W?** Re-run across queen / knn=5 / 3-mi band.

# %%
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd

from libpysal.weights import Queen, KNN, DistanceBand, W as Weights
from esda.moran import Moran, Moran_BV, Moran_Local
from esda.getisord import G_Local

# %% [markdown]
# ## 0. Config

# %%
ROOT = Path(__file__).resolve().parent.parent if "__file__" in dir() else Path("..").resolve()
DATA_PROCESSED = ROOT / "data" / "processed"

MODES = ["drive", "walk"]
DEFAULT_MODE = "drive"

PERMUTATIONS = 999
P_THRESHOLD = 0.05

# Projection for distance-based weights (UTM 18N covers Nassau cleanly, meters)
METRIC_CRS = 32618
DISTANCE_BAND_M = 4828  # ~3 miles

# Variables we run global Moran's I on
GLOBAL_VARS = [
    "need_score",
    "access_score",
    "mismatch_index",
    "rent_burden_rate",
    "poverty_rate",
    "eviction_filing_rate_eb",
]

# %% [markdown]
# ## 1. Load the pipeline output
#
# If this fails, run `01_access_need_mismatch.py` first.

# %%
def load_tracts(mode: str) -> gpd.GeoDataFrame:
    path = DATA_PROCESSED / f"tracts_{mode}.geojson"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run 01_access_need_mismatch.py first to produce it."
        )
    gdf = gpd.read_file(path).to_crs(METRIC_CRS).reset_index(drop=True)
    # PySAL uses positional index; keep GEOID as a plain column for joins
    return gdf

# %% [markdown]
# ## 2. Weight matrices
#
# Three choices, all row-standardized:
# - **Queen contiguity**: classic for polygon data; captures shared-edge neighbors
# - **KNN (k=5)**: forces every tract to have exactly 5 neighbors (avoids islands)
# - **Distance band (3 mi)**: captures service-area logic better for sparse suburban tracts
#
# We report results under all three. If they agree → robust finding. If they diverge →
# say so in the methods page.

# %%
def build_weights(gdf: gpd.GeoDataFrame) -> dict[str, Weights]:
    out = {}

    w_queen = Queen.from_dataframe(gdf, use_index=False)
    w_queen.transform = "r"
    out["queen"] = w_queen

    w_knn = KNN.from_dataframe(gdf, k=5)
    w_knn.transform = "r"
    out["knn5"] = w_knn

    w_dist = DistanceBand.from_dataframe(gdf, threshold=DISTANCE_BAND_M,
                                         binary=True, silence_warnings=True)
    w_dist.transform = "r"
    out["dist3mi"] = w_dist

    # Warn about islands (tracts with no neighbors)
    for name, w in out.items():
        islands = getattr(w, "islands", [])
        if islands:
            print(f"[weights:{name}] {len(islands)} island(s): GEOIDs = "
                  f"{[gdf.loc[i, 'GEOID'] for i in islands[:5]]}")
    return out

# %% [markdown]
# ## 3. Global Moran's I across variables × weights
#
# Report I, expected I under null, permutation p-value.

# %%
def global_moran_table(gdf: gpd.GeoDataFrame, weights: dict,
                       variables: list[str]) -> pd.DataFrame:
    rows = []
    for var in variables:
        if var not in gdf.columns:
            print(f"[global_moran] skipping missing column: {var}")
            continue
        y = gdf[var].fillna(gdf[var].mean()).values
        if np.nanstd(y) == 0:
            print(f"[global_moran] skipping constant column: {var}")
            continue
        for wname, w in weights.items():
            mi = Moran(y, w, permutations=PERMUTATIONS)
            rows.append({
                "variable": var,
                "weights": wname,
                "I": round(float(mi.I), 4),
                "EI": round(float(mi.EI), 4),
                "z_sim": round(float(mi.z_sim), 3),
                "p_sim": round(float(mi.p_sim), 4),
            })
    return pd.DataFrame(rows)

# %% [markdown]
# ## 4. Bivariate Moran's I — the product validation gate
#
# `Moran_BV(x, y, w)` measures whether the **spatial lag of y** correlates with `x`.
# We want: x = need_score, y = access_score.
# - Strongly positive + significant → services already follow need; "mismatch" story
#   is weak. Pivot to: shortage-across-the-board narrative, or demographic disparity
#   within high-need clusters.
# - Near zero or negative → mismatch index genuinely reveals something the eye misses.
#   Product thesis survives.

# %%
@dataclass
class ValidationGate:
    bivariate_I: float
    p_sim: float
    interpretation: str      # human-readable
    verdict: str             # "mismatch-story-strong" | "mismatch-story-weak" | "inconclusive"


def run_validation_gate(gdf: gpd.GeoDataFrame, w: Weights) -> ValidationGate:
    need = gdf["need_score"].fillna(0).values
    access = gdf["access_score"].fillna(0).values
    mb = Moran_BV(need, access, w, permutations=PERMUTATIONS)
    I = float(mb.I)
    p = float(mb.p_sim)
    if p >= P_THRESHOLD:
        interp = f"I={I:+.3f}, p={p:.3f} — not significant; no clear spatial relation."
        verdict = "inconclusive"
    elif I > 0.15:
        interp = (f"I={I:+.3f}, p={p:.3f} — services concentrate where need is high. "
                  "Mismatch narrative will underperform; consider shortage / disparity angle.")
        verdict = "mismatch-story-weak"
    elif I < -0.05:
        interp = (f"I={I:+.3f}, p={p:.3f} — services systematically avoid high-need areas. "
                  "Mismatch index has strong signal; proceed with product.")
        verdict = "mismatch-story-strong"
    else:
        interp = (f"I={I:+.3f}, p={p:.3f} — weak relationship. Mismatch index can still "
                  "surface local pockets; proceed but lead with LISA rather than the global claim.")
        verdict = "mismatch-story-strong"
    return ValidationGate(bivariate_I=round(I, 4), p_sim=round(p, 4),
                          interpretation=interp, verdict=verdict)

# %% [markdown]
# ## 5. Local Moran's I (LISA)
#
# Per-tract cluster label:
# - **HH**: high value, surrounded by high → core of a hot cluster
# - **LL**: low value, surrounded by low → core of a cold cluster
# - **HL / LH**: outlier — different from neighbors
# - **ns**: not significant at p < 0.05 (default)

# %%
_LISA_LABELS = {0: "ns", 1: "HH", 2: "LH", 3: "LL", 4: "HL"}


def lisa_labels(gdf: gpd.GeoDataFrame, w: Weights, var: str,
                p_thresh: float = P_THRESHOLD) -> tuple[np.ndarray, np.ndarray]:
    y = gdf[var].fillna(gdf[var].mean()).values
    lm = Moran_Local(y, w, permutations=PERMUTATIONS)
    sig = lm.p_sim < p_thresh
    quad = np.where(sig, lm.q, 0)
    labels = np.array([_LISA_LABELS[int(q)] for q in quad])
    return labels, lm.p_sim

# %% [markdown]
# ## 6. Getis-Ord Gi*
#
# z-score per tract indicating hot/cold spot intensity. Positive = hotspot.
# Useful complement to LISA because Gi* includes the tract itself (star=True),
# LISA does not.

# %%
def gi_star(gdf: gpd.GeoDataFrame, w: Weights, var: str) -> tuple[np.ndarray, np.ndarray]:
    y = gdf[var].fillna(gdf[var].mean()).values
    g = G_Local(y, w, star=True, permutations=PERMUTATIONS)
    return g.Zs, g.p_sim

# %% [markdown]
# ## 7. Robustness across W choices
#
# For each variable, compute std-dev of Moran's I across the three weight matrices.
# Large std → finding depends on W choice; flag it in the methods page.

# %%
def robustness_summary(global_tbl: pd.DataFrame) -> pd.DataFrame:
    agg = (global_tbl
           .groupby("variable")
           .agg(I_mean=("I", "mean"),
                I_std=("I", "std"),
                p_max=("p_sim", "max"))
           .round(4)
           .reset_index())
    agg["robust"] = (agg["I_std"] < 0.05) & (agg["p_max"] < P_THRESHOLD)
    return agg

# %% [markdown]
# ## 8. Assemble outputs

# %%
def run_diagnostics(mode: str = DEFAULT_MODE) -> dict:
    gdf = load_tracts(mode)
    weights = build_weights(gdf)
    w_primary = weights["queen"]

    # --- global ---
    global_tbl = global_moran_table(gdf, weights, GLOBAL_VARS)
    print("\n== Global Moran's I ==")
    print(global_tbl.to_string(index=False))

    robust_tbl = robustness_summary(global_tbl)
    print("\n== Robustness across W ==")
    print(robust_tbl.to_string(index=False))

    # --- validation gate ---
    gate = run_validation_gate(gdf, w_primary)
    print(f"\n== Validation gate ({mode}) ==\n  verdict: {gate.verdict}\n  {gate.interpretation}")

    # --- local: LISA + Gi* on mismatch_index and need_score ---
    for var in ["mismatch_index", "need_score"]:
        labels, p = lisa_labels(gdf, w_primary, var)
        gdf[f"lisa_{var}_label"] = labels
        gdf[f"lisa_{var}_p"] = np.round(p, 4)

    z, p = gi_star(gdf, w_primary, "mismatch_index")
    gdf["gi_mismatch_z"] = np.round(z, 3)
    gdf["gi_mismatch_p"] = np.round(p, 4)

    # --- write outputs ---
    out_geojson = DATA_PROCESSED / f"tracts_{mode}_diagnostics.geojson"
    gdf.to_crs(4326).to_file(out_geojson, driver="GeoJSON")

    summary = {
        "mode": mode,
        "permutations": PERMUTATIONS,
        "p_threshold": P_THRESHOLD,
        "primary_weights": "queen",
        "global_moran": global_tbl.to_dict(orient="records"),
        "robustness": robust_tbl.to_dict(orient="records"),
        "validation_gate": asdict(gate),
        "lisa_counts": {
            var: pd.Series(gdf[f"lisa_{var}_label"]).value_counts().to_dict()
            for var in ["mismatch_index", "need_score"]
        },
    }
    out_json = DATA_PROCESSED / f"diagnostics_{mode}.json"
    def _no_nan(o):
        if isinstance(o, float) and o != o: return None
        if isinstance(o, dict): return {k: _no_nan(v) for k, v in o.items()}
        if isinstance(o, list): return [_no_nan(v) for v in o]
        return o
    out_json.write_text(json.dumps(_no_nan(summary), indent=2, default=str))
    print(f"\nwrote {out_geojson.name} and {out_json.name}")
    return summary

# %% [markdown]
# ## 9. Run
#
# Uncomment to execute once `01_access_need_mismatch.py` has produced its outputs.

# %%
# for mode in MODES:
#     try:
#         run_diagnostics(mode)
#     except FileNotFoundError as e:
#         print(f"[skip] {e}")

# %% [markdown]
# ## 10. Next diagnostics (TODO)
#
# - [ ] **Leave-one-facility-out sensitivity**: loop `run_pipeline` in notebook 01 with
#       each facility dropped; track which tracts' `mismatch_pct` shifts most. Output:
#       `data/processed/facility_criticality.parquet`. Lives in 01 because it needs
#       `run_pipeline`, not diagnostics on its output.
# - [ ] **Raw vs EB eviction rate scatter**: how much did shrinkage change the ranking?
# - [ ] **GWR (Geographically Weighted Regression)**: regress `eviction_filing_rate_eb`
#       on `rent_burden_rate + poverty_rate + access_score`; map local R² and
#       coefficient surfaces. Use `mgwr` package. Heavy; run separately.
# - [ ] **ACS MOE propagation into Moran's I**: bootstrap over MOE-implied distributions.
#       Graduate-thesis territory; defer unless reviewers push back.
