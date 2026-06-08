"""
streamlit_app.py
================================================================================
Interactive, BILINGUAL (EN/ES) front-end for the afternoon pickup / not-ready
simulation.

RUN IT:
    pip install -r requirements.txt
    streamlit run streamlit_app.py

Requires in the same folder:
    afternoon_pickup_sim.py   (the SimPy engine)
    sim_app_core.py           (the replication / aggregation layer)
    i18n.py                   (EN/ES strings)

Language only affects DISPLAY. Selectbox values stay as the engine's keys, so
switching language never changes the model. All numbers are PLACEHOLDER-driven:
read direction and rank, not absolute values. The safety gate is a hard discard.
================================================================================
"""

import altair as alt
import pandas as pd
import numpy as np
import streamlit as st

from sim_app_core import run_reps, make_config, parent_time_stats
from i18n import LANGS, t as _t, opt as _opt

st.set_page_config(page_title="Afternoon Pickup Simulator",
                   layout="wide", initial_sidebar_state="expanded")


# ============================================================ cached simulation
@st.cache_data(show_spinner=False)
def simulate(params: tuple, n_reps: int):
    cfg = make_config(**dict(params))
    return run_reps(cfg, n_reps=n_reps)


def run_with(overrides: dict, n_reps: int):
    return simulate(tuple(sorted(overrides.items())), n_reps)


# ============================================================ language selector
lang_choice = st.sidebar.radio("Language / Idioma", list(LANGS.keys()),
                               horizontal=True)
lang = LANGS[lang_choice]

def T(key):                       # localized string
    return _t(key, lang)

def O(group):                     # format_func for a selectbox group
    return lambda v: _opt(group, v, lang)


# ================================================================== sidebar dials
st.sidebar.title(T("sidebar_title"))
st.sidebar.caption(T("sidebar_caption"))

with st.sidebar.expander(T("exp_demand"), expanded=True):
    n_cars_base = st.slider(T("n_cars"), 100, 450, 330, 10, help=T("n_cars_help"))
    mode_shift_frac = st.slider(T("mode_shift"), 0.0, 0.5, 0.0, 0.05, help=T("mode_shift_help"))
    buffer_capacity = st.slider(T("buffer"), 10, 30, 22, 1, help=T("buffer_help"))
    n_boarding_spots = st.slider(T("spots"), 3, 8, 5, 1, help=T("spots_help"))

with st.sidebar.expander(T("exp_schedule"), expanded=False):
    bell_gap_min = st.slider(T("bell_gap"), 10, 45, 20, 1, help=T("bell_gap_help"))

with st.sidebar.expander(T("exp_summon"), expanded=True):
    advance_summon = st.selectbox(T("summon_mech"), ["off", "placard", "geofence"],
                                  format_func=O("summon"), help=T("summon_help"))
    geofence_adoption = st.slider(T("geo_adopt"), 0.0, 1.0, 0.0, 0.05,
                                  disabled=(advance_summon != "geofence"),
                                  help=T("geo_adopt_help"))

with st.sidebar.expander(T("exp_policy"), expanded=True):
    not_ready_policy = st.selectbox(T("policy_sel"), ["blocking", "recirculate", "holding"],
                                    format_func=O("policy"), help=T("policy_help"))
    holding_location = st.selectbox(T("holding_loc"), ["none", "internal", "external_staging"],
                                    format_func=O("holding"), help=T("holding_loc_help"))
    holding_capacity = st.slider(T("holding_cap"), 1, 10, 4, 1,
                                 disabled=(holding_location != "internal"))
    staging_discipline = st.slider(T("discipline"), 0.4, 1.2, 1.0, 0.05, help=T("discipline_help"))

with st.sidebar.expander(T("exp_egress"), expanded=True):
    egress_time_mean = st.slider(T("egress_time"), 0.10, 0.50, 0.30, 0.02, help=T("egress_time_help"))
    # egress_coupling = st.selectbox(T("coupling"), ["independent", "calming"],
    #                                format_func=O("coupling"), help=T("coupling_help"))
    egress_coupling = "independent"   # LOCKED for the pre-meeting link — protects Wednesday's reveal

with st.sidebar.expander(T("exp_safety"), expanded=False):
    curve_threshold_cars = st.slider(T("curve_thr"), 5, 25, 12, 1, help=T("curve_thr_help"))
    n_reps = st.slider(T("n_reps"), 5, 40, 20, 5, help=T("n_reps_help"))

overrides = dict(
    n_cars_base=n_cars_base, mode_shift_frac=mode_shift_frac,
    buffer_capacity=buffer_capacity, n_boarding_spots=n_boarding_spots,
    bell_gap_min=float(bell_gap_min), advance_summon=advance_summon,
    geofence_adoption=geofence_adoption, not_ready_policy=not_ready_policy,
    holding_location=holding_location, holding_capacity=holding_capacity,
    staging_discipline=staging_discipline, egress_time_mean=egress_time_mean,
    egress_coupling=egress_coupling, curve_threshold_cars=curve_threshold_cars,
)

# ===================================================================== run sims
res = run_with(overrides, n_reps)
baseline = run_with({}, n_reps)
m = res["metrics"]
bm = baseline["metrics"]

# ===================================================================== header
st.title(T("main_title"))
st.caption(T("main_caption"))

saf = res["safety"]
if saf["passes"]:
    st.success(T("safety_pass").format(q=saf["max_road_queue"], thr=saf["threshold"]))
else:
    st.error(T("safety_fail").format(q=saf["max_road_queue"], thr=saf["threshold"],
                                     mins=saf["minutes_above_curve"]))

rg = res["regime"]
if rg["saturated"]:
    st.warning(T("regime_sat").format(c=rg["completion_frac"]*100, u=rg["spot_util"]*100))
else:
    st.info(T("regime_unsat").format(c=rg["completion_frac"]*100, u=rg["spot_util"]*100))

# ===================================================================== metrics
def card(col, label, key, unit="", inverse=True, scale=1.0):
    val = m[key]["mean"] * scale
    delta = (m[key]["mean"] - bm[key]["mean"]) * scale
    col.metric(label, f"{val:.1f}{unit}",
               delta=f"{delta:+.1f}{unit} {T('vs_asis')}",
               delta_color="inverse" if inverse else "normal")

U_CARS, U_MIN, U_PCT = T("u_cars"), T("u_min"), T("u_pct")

st.subheader(T("six_criteria"))
c1, c2, c3 = st.columns(3)
card(c1, T("m_peak_queue"), "max_road_queue", U_CARS)
card(c2, T("m_min_curve"), "min_above_curve", U_MIN)
card(c3, T("m_spilled"), "n_spilled_road", "")
c4, c5, c6 = st.columns(3)
card(c4, T("m_parent_mean"), "parent_mean", U_MIN)
card(c5, T("m_parent_p90"), "parent_p90", U_MIN)
card(c6, T("m_carbon"), "carbon_proxy_vehmin", "")
c7, c8, _ = st.columns(3)
card(c7, T("m_blocked"), "frac_blocked", U_PCT, scale=100.0)
c8.metric(T("m_staging"), f"{m['n_routed_staging']['mean']:.0f}", help=T("m_staging_help"))

# ===================================================================== charts
ts = res["timeseries"]
bts = baseline["timeseries"]
show_baseline = st.checkbox(T("overlay"), value=True)

st.subheader(T("chart_road"))
df_road = pd.DataFrame({"minute": ts["t"], "queue": ts["road_mean"],
                        "lo": np.maximum(0, ts["road_mean"] - ts["road_std"]),
                        "hi": ts["road_mean"] + ts["road_std"]})
band = alt.Chart(df_road).mark_area(opacity=0.18, color="#1f77b4").encode(
    x=alt.X("minute:Q", title=T("ax_minutes")),
    y=alt.Y("lo:Q", title=T("ax_cars_road")), y2="hi:Q")
line = alt.Chart(df_road).mark_line(color="#1f77b4", strokeWidth=2.5).encode(
    x="minute:Q", y="queue:Q")
thr = alt.Chart(pd.DataFrame({"y": [curve_threshold_cars]})).mark_rule(
    color="red", strokeDash=[6, 4]).encode(y="y:Q")
thr_text = alt.Chart(pd.DataFrame({"y": [curve_threshold_cars],
                                   "label": [T("lbl_curve_thr")]})).mark_text(
    align="left", dx=5, dy=-6, color="red").encode(
    y="y:Q", text="label:N", x=alt.value(5))
layers = [band, line, thr, thr_text]
if show_baseline:
    df_b = pd.DataFrame({"minute": bts["t"], "queue": bts["road_mean"]})
    layers.append(alt.Chart(df_b).mark_line(
        color="#999", strokeDash=[3, 3]).encode(x="minute:Q", y="queue:Q"))
st.altair_chart(alt.layer(*layers).properties(height=300), width='stretch')
st.caption(T("cap_road"))

col_a, col_b = st.columns(2)
with col_a:
    st.subheader(T("chart_inside"))
    df_in = pd.DataFrame({
        "minute": np.concatenate([ts["t"], ts["t"]]),
        "value": np.concatenate([ts["buffer_mean"], ts["spot_mean"]]),
        "series": ([T("ser_buffer")] * len(ts["t"]) + [T("ser_spots")] * len(ts["t"])),
    })
    chart_in = alt.Chart(df_in).mark_line().encode(
        x=alt.X("minute:Q", title=T("ax_minutes")),
        y=alt.Y("value:Q", title=T("ax_cars")),
        color=alt.Color("series:N", title="")).properties(height=260)
    st.altair_chart(chart_in, width='stretch')
    st.caption(T("cap_inside"))

with col_b:
    st.subheader(T("chart_parent"))
    pt = res["parent_times"]
    stats = parent_time_stats(pt)
    df_pt = pd.DataFrame({"parent_time": pt})
    hist = alt.Chart(df_pt).mark_bar(opacity=0.8, color="#1f77b4").encode(
        x=alt.X("parent_time:Q", bin=alt.Bin(maxbins=30), title=T("ax_arr_dep")),
        y=alt.Y("count():Q", title=T("ax_cars")))
    rule_mean = alt.Chart(pd.DataFrame({"x": [stats["mean"]]})).mark_rule(
        color="black").encode(x="x:Q")
    rule_p90 = alt.Chart(pd.DataFrame({"x": [stats["p90"]]})).mark_rule(
        color="red", strokeDash=[5, 3]).encode(x="x:Q")
    st.altair_chart((hist + rule_mean + rule_p90).properties(height=260), width='stretch')
    st.caption(T("cap_parent").format(mean=stats["mean"], p90=stats["p90"]))

# ===================================================================== validation
with st.expander(T("val_title")):
    st.markdown(T("val_body"))
    if st.button(T("val_btn")):
        deg = make_config(
            n_cars_base=n_cars_base, egress_time_mean=egress_time_mean,
            release_lag=0.0, latency_median=1e-6, latency_sigma=1e-6,
            arrival_rel_mean=30.0, arrival_rel_sd=8.0, arrival_early_cap=5.0,
            advance_summon="off", not_ready_policy="blocking",
            holding_location="none", egress_coupling="independent",
            cohorts={"all": {"dismissal": 0.0, "share": 1.0}})
        dres = run_reps(deg, n_reps=n_reps)
        st.write(T("val_result").format(
            mean=dres["metrics"]["parent_mean"]["mean"],
            fb=dres["metrics"]["frac_blocked"]["mean"]))

st.divider()
st.caption(T("footer"))
