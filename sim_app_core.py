"""
sim_app_core.py
================================================================================
Orchestration / compute layer that sits between the SimPy engine
(afternoon_pickup_sim.py) and the Streamlit UI (streamlit_app.py).

WHY THIS IS A SEPARATE FILE
---------------------------
The engine answers "what happens in one afternoon". This layer answers the
questions the UI actually asks: "run N independent days, give me means with
confidence intervals, give me the average time-series with an uncertainty band,
and tell me which REGIME we're in (egress-saturated or not)." None of that needs
Streamlit, so it lives here where it can be unit-tested headlessly. The Streamlit
file only does widgets and charts.
================================================================================
"""

from __future__ import annotations
from dataclasses import replace
import math
import statistics
import numpy as np

from afternoon_pickup_sim import Config, AfternoonSim


# ------------------------------------------------------------------ run N days
def run_reps(cfg: Config, n_reps: int = 15) -> dict:
    """Run n_reps independent replications. Returns aggregated metrics (mean+CI),
    the mean time-series with std bands, pooled parent-time samples, and a regime
    diagnosis. Each rep uses a distinct seed so replications are independent."""
    metric_rows = []
    road_series, buf_series, spot_series = [], [], []
    parent_times: list[float] = []
    t_axis = None

    for r in range(n_reps):
        c = replace(cfg, seed=r)
        sim = AfternoonSim(c)
        m = sim.run()
        metric_rows.append(m)
        road_series.append(sim.ts_road)
        buf_series.append(sim.ts_buffer)
        spot_series.append(sim.ts_spotbusy)
        t_axis = sim.ts_t
        parent_times.extend(
            car.depart - car.arrival for car in sim.completed
            if car.depart < math.inf
        )

    # ---- align time-series to the shortest rep, then average across reps -----
    L = min(min(len(s) for s in road_series), len(t_axis))
    t = np.array(t_axis[:L], dtype=float)
    road = np.array([s[:L] for s in road_series], dtype=float)
    buf = np.array([s[:L] for s in buf_series], dtype=float)
    spot = np.array([s[:L] for s in spot_series], dtype=float)

    timeseries = {
        "t": t,
        "road_mean": road.mean(axis=0),
        "road_std": road.std(axis=0, ddof=1) if n_reps > 1 else np.zeros(L),
        "buffer_mean": buf.mean(axis=0),
        "spot_mean": spot.mean(axis=0),
    }

    # ---- aggregate scalar metrics: mean + 95% CI half-width ------------------
    keys = [k for k, v in metric_rows[0].items() if isinstance(v, (int, float))]
    agg = {}
    for k in keys:
        vals = np.array([row[k] for row in metric_rows], dtype=float)
        mean = float(np.nanmean(vals))
        sd = float(np.nanstd(vals, ddof=1)) if n_reps > 1 else 0.0
        ci = 1.96 * sd / math.sqrt(n_reps) if n_reps > 1 else 0.0
        agg[k] = {"mean": mean, "ci": ci}

    # ---- regime diagnosis ----------------------------------------------------
    completion_frac = (agg["n_completed"]["mean"]
                       / max(1e-9, agg["n_cars"]["mean"]))
    spot_util = float(timeseries["spot_mean"].mean()) / max(1, cfg.n_boarding_spots)
    saturated = (completion_frac < 0.90) or (spot_util > 0.92)
    regime = {
        "saturated": bool(saturated),
        "completion_frac": completion_frac,
        "spot_util": spot_util,
    }

    # ---- safety gate ---------------------------------------------------------
    safety = {
        "max_road_queue": agg["max_road_queue"]["mean"],
        "threshold": cfg.curve_threshold_cars,
        "minutes_above_curve": agg["min_above_curve"]["mean"],
        "passes": agg["max_road_queue"]["mean"] <= cfg.curve_threshold_cars,
    }

    return {
        "metrics": agg,
        "timeseries": timeseries,
        "parent_times": parent_times,
        "regime": regime,
        "safety": safety,
        "n_reps": n_reps,
    }


# ------------------------------------------------------------ helper utilities
def parent_time_stats(parent_times: list[float]) -> dict:
    if not parent_times:
        return {"mean": float("nan"), "p50": float("nan"), "p90": float("nan")}
    a = np.array(parent_times)
    return {
        "mean": float(a.mean()),
        "p50": float(np.percentile(a, 50)),
        "p90": float(np.percentile(a, 90)),
    }


def make_config(**overrides) -> Config:
    """Build a Config from UI values. Only the exposed dials are passed; the rest
    keep their (placeholder) defaults from the engine."""
    return Config(**overrides)
