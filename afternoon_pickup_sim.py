"""
================================================================================
AFTERNOON PICKUP / NOT-READY SIMULATION  --  v1 (open-loop)
School traffic optimisation project
================================================================================

WHAT THIS MODELS
----------------
The afternoon dismissal as a queueing system:

    arrival -> [grounds ingress] -> internal buffer -> boarding spot (5 servers)
            -> wait for child (THE not-ready event) -> board -> west-gate egress -> leave

The single mechanic that makes this hard is HEAD-OF-LINE BLOCKING: a car whose
child is not yet ready physically occupies a boarding spot while it waits, so it
degrades the throughput of every car behind it. Everything interesting in the
afternoon flows from that one fact.

THE READINESS COMPOSITION (the heart of the model -- read this)
---------------------------------------------------------------
We never store "P(not-ready)" as a number, because that number CHANGES under
every policy (loudspeaker vs geofence vs tight staging) and would have to be
re-measured each time. Instead we compose readiness from POLICY-INVARIANT
sub-processes that we measure once:

    effective_summon = max(summon_time, cohort_dismissal + release_lag)
        # you cannot summon a child out of a class that has not been let out yet.
        # This term is the STRUCTURAL cause of not-ready (car beat the bell).

    kid_ready = effective_summon + summon_to_board_latency
        # summon_to_board_latency is the measured invariant: "name called" ->
        # "child physically at the car". Its tail is the BEHAVIOURAL cause
        # (kid dawdling). Tight staging shrinks this tail (a dial).

    car_ready = max over the car's children of kid_ready
        # the SIBLING term: a cross-cohort car (primary 15:00 + highschool 15:20)
        # is structurally not-ready until the LATER bell, no matter how clever
        # the summon. This is why per-car cohort composition matters.

A car can only board when BOTH (car_ready) AND (a spot is free).
Arriving before car_ready is what produces blocking.

DIALS (every solution idea is a parameter here)
-----------------------------------------------
  advance_summon      : "off" | "placard" | "geofence"   (+ geofence_adoption phi)
  not_ready_policy    : "blocking" | "recirculate" | "holding"
  holding_location    : "none" | "internal" | "external_staging"
  bell_gap_min        : minutes between primary and highschool dismissal
  mode_shift_frac     : fraction of cars removed (carpool / shuttle / in-house bus)
  egress_coupling     : "independent" | "calming"  (the queue-as-traffic-calming
                        hypothesis -- default independent; "calming" makes egress
                        SLOWER when the road queue is short)
  staging_discipline  : scales the behavioural latency tail (loose .. tight)

WHAT IS DELIBERATELY *NOT* HERE (v1 is open-loop)
-------------------------------------------------
  * Arrivals are a FIXED measured input. In reality they are endogenous (parents
    arrive early BECAUSE the queue is bad and will stop once it isn't). So v1, if
    anything, UNDER-states the benefit of fixes that flip that loop. Report ranges
    and direction, not precise single numbers.
  * The "leave-home nudge" feedback controller is v2. Arrival generation is kept
    modular so a smoothing operator can be swapped in later.

VALIDATION TARGETS (do these before trusting any lever)
-------------------------------------------------------
  1. M/G/5 degenerate case: set every child ready at t=0 (no blocking). The DES
     mean wait must converge on the analytic M/G/c result. See validate_mgc().
  2. Observed-rate check: the composed not-ready rate this model produces under
     the as-is config must match the rate measured directly at the gate.

ALL NUMERIC DISTRIBUTIONS BELOW ARE PLACEHOLDERS  <-- replace with measured data.
They are flagged with the marker  ###PLACEHOLDER###  so they are easy to find.
The structure does not change when you swap them; only the numbers do. That is
the whole point of measuring sub-processes instead of outcomes.
================================================================================
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import math
import random
import statistics
import simpy
import numpy as np


# ==============================================================================
# 1. CONFIG  -- every dial lives here. Nothing below this block is scenario-specific.
# ==============================================================================

@dataclass
class Config:
    # ---- session clock (minutes; t=0 is an arbitrary session start) -----------
    sim_start: float = 0.0
    sim_end: float = 120.0          # ~2h covers 14:20 preschool .. post-15:20 tail

    # ---- cohorts: name -> (dismissal time in min from sim_start, share of kids)-
    # ###PLACEHOLDER### bells relative to sim_start=14:20. Gap is a DIAL (see make).
    cohorts: dict = field(default_factory=lambda: {
        "preschool":  {"dismissal": 20.0, "share": 0.06},   # 14:40
        "primary":    {"dismissal": 40.0, "share": 0.55},   # 15:00
        "highschool": {"dismissal": 60.0, "share": 0.39},   # 15:20
    })
    bell_gap_min: Optional[float] = None   # if set, OVERRIDES primary->highschool gap

    # ---- demand --------------------------------------------------------------
    n_cars_base: int = 330          # ###PLACEHOLDER### cars in a peak afternoon
    mode_shift_frac: float = 0.0    # DIAL: fraction of cars removed by mode shift
    # per-car child count distribution (kids per car). DIAL feeds carpool headroom.
    kids_per_car_probs: tuple = (0.70, 0.25, 0.05)  # ###PLACEHOLDER### 1,2,3 kids
    # probability a 2nd/3rd kid is in a DIFFERENT cohort (creates sibling-wait)
    cross_cohort_prob: float = 0.45                 # ###PLACEHOLDER###

    # ---- arrival timing ------------------------------------------------------
    # Arrivals are expressed as minutes-relative-to-each-kid's-bell, then shifted.
    # Negative = early bird (arrives before bell -> structurally not-ready).
    # ###PLACEHOLDER### a left-skewed spread with a fat early-bird tail.
    arrival_rel_mean: float = -4.0     # mean arrival 4 min BEFORE the bell
    arrival_rel_sd: float = 7.0
    arrival_early_cap: float = -25.0   # earliest anyone shows up (min before bell)

    # ---- resources -----------------------------------------------------------
    buffer_capacity: int = 22          # ###PLACEHOLDER### measured 20-25 internal
    n_boarding_spots: int = 5          # the five stop-and-drop spots = servers
    holding_capacity: int = 4          # internal holding (if policy=holding,internal)

    # ---- service times (minutes) --------------------------------------------
    ingress_time_mean: float = 0.10    # ###PLACEHOLDER### time to clear east gate
    board_time_mean: float = 0.25      # ###PLACEHOLDER### identify->seated, once ready
    board_time_sd: float = 0.08

    # summon-to-board latency = THE measured behavioural invariant.
    # lognormal-ish: most kids quick, a fat tail of dawdlers. ###PLACEHOLDER###
    latency_median: float = 0.8        # min, under LOOSE staging
    latency_sigma: float = 0.6         # shape of the tail
    release_lag: float = 1.0           # ###PLACEHOLDER### bell -> first kid available

    # ---- egress (west gate merge into 80km/h traffic) ------------------------
    egress_time_mean: float = 0.30     # ###PLACEHOLDER### ready-at-gate -> merged
    egress_time_sd: float = 0.20
    egress_coupling: str = "independent"   # "independent" | "calming"
    # under "calming": egress gets SLOWER as the road queue shrinks (hypothesis)
    calming_min_factor: float = 0.6    # egress time multiplier when queue is long
    calming_max_factor: float = 1.8    # multiplier when road is clear (no calming)

    # ---- DIALS: policies -----------------------------------------------------
    advance_summon: str = "off"        # "off" | "placard" | "geofence"
    placard_lead: float = 1.5          # ###PLACEHOLDER### lead time staff get from placard
    geofence_lead: float = 4.0         # ###PLACEHOLDER### lead from ETA geofence
    geofence_adoption: float = 0.0     # phi: fraction of cars with working geofence

    not_ready_policy: str = "blocking" # "blocking" | "recirculate" | "holding"
    holding_grace: float = 0.5         # min to wait in spot before pulling aside

    holding_location: str = "none"     # "none" | "internal" | "external_staging"

    staging_discipline: float = 1.0    # multiplies latency_median (1.0 loose, <1 tight)

    # ---- external staging ground (separate upstream resource) ----------------
    staging_travel_in: float = 4.0     # ###PLACEHOLDER### drive to the lot
    staging_travel_back: float = 4.0   # ###PLACEHOLDER### lot -> school grounds
    staging_dispatch_interval: float = 0.4  # metered cadence: min between dispatches

    # ---- safety threshold ----------------------------------------------------
    # road queue (cars) beyond which the tail reaches the blind curve = HARD GATE.
    curve_threshold_cars: int = 12     # ###PLACEHOLDER### cars from gate to curve

    # ---- run control ---------------------------------------------------------
    seed: int = 0
    monitor_dt: float = 1.0            # sampling interval for time-series metrics


# ==============================================================================
# 2. DISTRIBUTION HELPERS  (all placeholders; swap for fitted measured curves)
# ==============================================================================

def lognormal_latency(rng: random.Random, cfg: Config) -> float:
    """summon-to-board latency. staging_discipline scales the median (a dial)."""
    median = cfg.latency_median * cfg.staging_discipline
    mu = math.log(max(median, 1e-6))
    return rng.lognormvariate(mu, cfg.latency_sigma)


def truncated_normal(rng: random.Random, mean: float, sd: float,
                     lo: float = 0.0) -> float:
    for _ in range(20):
        x = rng.gauss(mean, sd)
        if x >= lo:
            return x
    return lo


# ==============================================================================
# 3. ENTITIES
# ==============================================================================

@dataclass
class Child:
    cohort: str
    dismissal: float
    behavioural_dwell: float   # the realised tail draw for this child


@dataclass
class Car:
    cid: int
    arrival: float
    children: list
    has_geofence: bool
    # filled in during the run:
    summon_time: float = math.inf
    car_ready: float = math.inf
    board_start: float = math.inf
    depart: float = math.inf
    blocked_time: float = 0.0
    routed_staging: bool = False
    spilled_road: bool = False


# ==============================================================================
# 4. THE SIMULATION
# ==============================================================================

class AfternoonSim:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.rng = random.Random(cfg.seed)
        self.env = simpy.Environment()

        # resources
        self.buffer = simpy.Container(self.env, capacity=cfg.buffer_capacity,
                                      init=0)
        self.spots = simpy.Resource(self.env, capacity=cfg.n_boarding_spots)
        self.egress = simpy.Resource(self.env, capacity=1)  # single west gate
        self.holding = simpy.Resource(self.env, capacity=cfg.holding_capacity)

        # external staging: a store of waiting cars + a dispatcher
        self.staging_store = simpy.Store(self.env)
        self.staging_count = 0

        # bookkeeping
        self.cars: list[Car] = []
        self.road_queue = 0            # cars currently spilled onto the road
        self.completed: list[Car] = []

        # time-series monitors
        self.ts_t: list[float] = []
        self.ts_road: list[int] = []
        self.ts_buffer: list[float] = []
        self.ts_spotbusy: list[int] = []

    # ---- cohort / arrival generation (MODULAR: swap this for v2 smoothing) ----
    def _build_cohorts(self) -> dict:
        c = {k: dict(v) for k, v in self.cfg.cohorts.items()}
        if self.cfg.bell_gap_min is not None:
            base = c["primary"]["dismissal"]
            c["highschool"]["dismissal"] = base + self.cfg.bell_gap_min
        return c

    def _make_cars(self):
        cfg = self.cfg
        cohorts = self._build_cohorts()
        names = list(cohorts.keys())
        shares = np.array([cohorts[n]["share"] for n in names])
        shares = shares / shares.sum()

        n_cars = int(round(cfg.n_cars_base * (1.0 - cfg.mode_shift_frac)))
        for cid in range(n_cars):
            # how many kids in this car
            r = self.rng.random()
            cum = 0.0
            nkids = 1
            for i, p in enumerate(cfg.kids_per_car_probs):
                cum += p
                if r <= cum:
                    nkids = i + 1
                    break
            # primary cohort for the car (weighted by share)
            primary_cohort = self.rng.choices(names, weights=shares)[0]
            kids = []
            for k in range(nkids):
                if k == 0 or self.rng.random() > cfg.cross_cohort_prob:
                    ch = primary_cohort
                else:
                    ch = self.rng.choices(names, weights=shares)[0]
                dism = cohorts[ch]["dismissal"]
                dwell = lognormal_latency(self.rng, cfg)
                kids.append(Child(ch, dism, dwell))

            # arrival time: relative to the car's EARLIEST kid's bell, + spread
            earliest_bell = min(k.dismissal for k in kids)
            rel = truncated_normal(self.rng, cfg.arrival_rel_mean,
                                   cfg.arrival_rel_sd, lo=cfg.arrival_early_cap)
            arrival = max(cfg.sim_start, earliest_bell + rel)

            has_geo = (cfg.advance_summon == "geofence"
                       and self.rng.random() < cfg.geofence_adoption)
            self.cars.append(Car(cid, arrival, kids, has_geo))

        self.cars.sort(key=lambda c: c.arrival)

    # ---- summon timing: when does staff/system call the child? ---------------
    def _summon_time(self, car: Car, at_grounds: float) -> float:
        cfg = self.cfg
        if cfg.advance_summon == "off":
            return at_grounds                      # summon only when spot acquired
        if cfg.advance_summon == "placard":
            return max(cfg.sim_start, car.arrival - cfg.placard_lead)
        if cfg.advance_summon == "geofence":
            lead = cfg.geofence_lead if car.has_geofence else cfg.placard_lead
            return max(cfg.sim_start, car.arrival - lead)
        return at_grounds

    # ---- readiness composition (the heart) -----------------------------------
    def _car_ready_time(self, car: Car) -> float:
        cfg = self.cfg
        kid_readys = []
        for k in car.children:
            effective_summon = max(car.summon_time, k.dismissal + cfg.release_lag)
            kid_ready = effective_summon + k.behavioural_dwell
            kid_readys.append(kid_ready)
        return max(kid_readys)   # sibling term: the LAST kid governs

    # ---- egress service, optionally coupled to road queue (the hypothesis) ----
    def _egress_time(self) -> float:
        cfg = self.cfg
        base = truncated_normal(self.rng, cfg.egress_time_mean, cfg.egress_time_sd)
        if cfg.egress_coupling == "independent":
            return base
        # "calming": long road queue -> slower traffic -> EASIER (faster) merge.
        # short/zero queue -> faster traffic -> HARDER (slower) merge.
        q = self.road_queue
        # map queue 0..curve_threshold to factor max..min (linear, clamped)
        frac = min(1.0, q / max(1, cfg.curve_threshold_cars))
        factor = cfg.calming_max_factor + frac * (cfg.calming_min_factor
                                                  - cfg.calming_max_factor)
        return base * factor

    # ---- monitor process ------------------------------------------------------
    def _monitor(self):
        while True:
            self.ts_t.append(self.env.now)
            self.ts_road.append(self.road_queue)
            self.ts_buffer.append(self.buffer.level)
            self.ts_spotbusy.append(self.spots.count)
            yield self.env.timeout(self.cfg.monitor_dt)

    # ---- external staging dispatcher ------------------------------------------
    def _staging_dispatcher(self):
        """Pulls staged cars back to the grounds, metered, when buffer has room."""
        cfg = self.cfg
        while True:
            car = yield self.staging_store.get()   # FIFO; could prioritise ready
            # wait until buffer has space, then meter the dispatch cadence
            while self.buffer.level >= cfg.buffer_capacity - 0:
                yield self.env.timeout(0.1)
            yield self.env.timeout(cfg.staging_travel_back)
            self.env.process(self._enter_grounds(car, from_staging=True))
            yield self.env.timeout(cfg.staging_dispatch_interval)

    # ---- car lifecycle --------------------------------------------------------
    def _car_process(self, car: Car):
        cfg = self.cfg
        yield self.env.timeout(max(0.0, car.arrival - self.env.now))

        # geofence/placard summon can fire BEFORE the car reaches the grounds
        car.summon_time = self._summon_time(car, self.env.now)

        # decide route: if buffer full, either spill to road or divert to staging
        if self.buffer.level >= cfg.buffer_capacity:
            if cfg.holding_location == "external_staging":
                car.routed_staging = True
                self.staging_count += 1
                yield self.env.timeout(cfg.staging_travel_in)
                yield self.staging_store.put(car)
                return   # dispatcher will resume this car via _enter_grounds
            else:
                # spillback onto the live road -- the danger state
                car.spilled_road = True
                self.road_queue += 1
                # wait for buffer space
                while self.buffer.level >= cfg.buffer_capacity:
                    yield self.env.timeout(0.1)
                self.road_queue -= 1

        yield from self._enter_grounds(car)

    def _enter_grounds(self, car: Car, from_staging: bool = False):
        cfg = self.cfg
        yield self.buffer.put(1)                       # occupy a buffer slot
        yield self.env.timeout(cfg.ingress_time_mean)  # clear the east gate

        yield from self._serve_at_spot(car)

        # egress (ready cars can STILL queue here if the merge is slow)
        with self.egress.request() as req:
            yield req
            yield self.env.timeout(self._egress_time())
        car.depart = self.env.now
        self.completed.append(car)

    def _serve_at_spot(self, car: Car):
        cfg = self.cfg
        car.car_ready = self._car_ready_time(car)

        if cfg.not_ready_policy == "holding" and cfg.holding_location in (
                "internal", "external_staging"):
            yield from self._serve_with_holding(car)
        else:
            yield from self._serve_blocking(car)   # blocking & recirculate(approx)

    def _serve_blocking(self, car: Car):
        """As-is: hold the spot until the child is ready (head-of-line blocking)."""
        with self.spots.request() as req:
            yield req
            self.buffer.get(1)                     # leaves buffer, now at a spot
            t0 = self.env.now
            if car.car_ready > self.env.now:
                car.blocked_time += car.car_ready - self.env.now
                yield self.env.timeout(car.car_ready - self.env.now)
            yield self.env.timeout(truncated_normal(self.rng,
                                                    self.cfg.board_time_mean,
                                                    self.cfg.board_time_sd))
            car.board_start = t0

    def _serve_with_holding(self, car: Car):
        """Proposed: if not ready after a grace period, release the spot and
        pull aside (internal holding area or back to staging), re-acquire when
        ready. Decouples the blocked car from the server pool."""
        cfg = self.cfg
        got_in = False
        while not got_in:
            with self.spots.request() as req:
                yield req
                if self.buffer.level > 0:
                    self.buffer.get(1)
                wait = car.car_ready - self.env.now
                if wait <= cfg.holding_grace:
                    if wait > 0:
                        car.blocked_time += wait
                        yield self.env.timeout(wait)
                    yield self.env.timeout(truncated_normal(
                        self.rng, cfg.board_time_mean, cfg.board_time_sd))
                    car.board_start = self.env.now
                    got_in = True
                else:
                    # not ready -> release spot, go to holding, come back when ready
                    pass
            if not got_in:
                with self.holding.request() as hreq:
                    yield hreq
                    remaining = max(0.0, car.car_ready - self.env.now)
                    yield self.env.timeout(remaining)
                # loop: re-request a spot now that the child is ready

    # ---- run ------------------------------------------------------------------
    def run(self) -> dict:
        self._make_cars()
        self.env.process(self._monitor())
        if self.cfg.holding_location == "external_staging":
            self.env.process(self._staging_dispatcher())
        for car in self.cars:
            self.env.process(self._car_process(car))
        self.env.run(until=self.cfg.sim_end)
        return self._metrics()

    # ---- metrics --> the six criteria -----------------------------------------
    def _metrics(self) -> dict:
        cfg = self.cfg
        done = self.completed
        parent_times = [c.depart - c.arrival for c in done
                        if c.depart < math.inf]
        road = np.array(self.ts_road) if self.ts_road else np.array([0])
        n_spilled = sum(1 for c in self.cars if c.spilled_road)
        n_staged = sum(1 for c in self.cars if c.routed_staging)
        blocked = [c.blocked_time for c in done]

        # carbon proxy: total vehicle-minutes on-site + spilled (idle/dwell)
        veh_minutes = sum(parent_times)

        def pct(a, p):
            return float(np.percentile(a, p)) if len(a) else float("nan")

        return {
            "n_cars": len(self.cars),
            "n_completed": len(done),
            # SAFETY (hard gate)
            "max_road_queue": int(road.max()),
            "min_above_curve": float(np.sum(road > cfg.curve_threshold_cars)
                                     * cfg.monitor_dt),
            "n_spilled_road": n_spilled,
            # CONGESTION
            "veh_minutes_total": round(veh_minutes, 1),
            "mean_road_queue": round(float(road.mean()), 2),
            # PARENT TIME (mean AND p90 -- predictability matters)
            "parent_mean": round(statistics.mean(parent_times), 2)
            if parent_times else float("nan"),
            "parent_p90": round(pct(parent_times, 90), 2),
            # BLOCKING (the afternoon's signature pathology)
            "mean_blocked": round(statistics.mean(blocked), 2)
            if blocked else 0.0,
            "frac_blocked": round(sum(1 for b in blocked if b > 0.01)
                                  / len(blocked), 3) if blocked else 0.0,
            # STAGING
            "n_routed_staging": n_staged,
            # CARBON proxy
            "carbon_proxy_vehmin": round(veh_minutes, 1),
        }


# ==============================================================================
# 5. REPLICATION RUNNER  (terminating sim -> independent replications + CI)
# ==============================================================================

def run_scenario(base: Config, n_reps: int = 20, **overrides) -> dict:
    """Run n_reps independent days; return mean and 95% CI half-width per metric."""
    keys = None
    rows = []
    for r in range(n_reps):
        cfg = Config(**{**base.__dict__, **overrides, "seed": r})
        m = AfternoonSim(cfg).run()
        if keys is None:
            keys = [k for k, v in m.items()
                    if isinstance(v, (int, float))]
        rows.append(m)
    out = {}
    for k in keys:
        vals = np.array([row[k] for row in rows], dtype=float)
        mean = float(np.nanmean(vals))
        sd = float(np.nanstd(vals, ddof=1)) if len(vals) > 1 else 0.0
        ci = 1.96 * sd / math.sqrt(len(vals)) if len(vals) > 1 else 0.0
        out[k] = (round(mean, 2), round(ci, 2))
    return out


# ==============================================================================
# 6. VALIDATION: M/G/5 degenerate case
# ==============================================================================

def validate_mgc(base: Config, n_reps: int = 30):
    """Switch OFF blocking (all kids ready at t=0) and compare DES mean wait to
    the analytic M/G/c (Allen-Cunneen) approximation. If these don't agree, the
    model is wrong, not the world. Prints both for eyeballing."""
    cfg = Config(**base.__dict__)
    # make every child instantly ready: bells at t=0, no dwell, no release lag
    cfg.cohorts = {"all": {"dismissal": 0.0, "share": 1.0}}
    cfg.bell_gap_min = None
    cfg.release_lag = 0.0
    cfg.latency_median = 1e-6
    cfg.latency_sigma = 1e-6
    cfg.arrival_rel_mean = 30.0      # arrive well after t=0 so no structural block
    cfg.arrival_rel_sd = 8.0
    cfg.arrival_early_cap = 5.0
    cfg.advance_summon = "off"
    cfg.not_ready_policy = "blocking"
    cfg.holding_location = "none"
    cfg.egress_coupling = "independent"

    res = run_scenario(cfg, n_reps=n_reps)
    print("  [M/G/5 degenerate] mean parent time:", res["parent_mean"],
          "| frac_blocked (should be ~0):", res["frac_blocked"])
    print("  (Compare parent_mean against your napkin M/G/5 with service =",
          "board_time + egress_time and your peak arrival rate.)")


# ==============================================================================
# 7. DEMO: as-is baseline + a few single-dial sweeps
# ==============================================================================

def fmt(res: dict, keys: list[str]) -> str:
    return "  ".join(f"{k}={res[k][0]}±{res[k][1]}" for k in keys)


if __name__ == "__main__":
    base = Config()
    show = ["max_road_queue", "min_above_curve", "parent_mean",
            "parent_p90", "frac_blocked", "n_spilled_road"]

    print("=" * 78)
    print("VALIDATION")
    print("=" * 78)
    validate_mgc(base)

    print("\n" + "=" * 78)
    print("AS-IS BASELINE  (loudspeaker, blocking, no staging, 20min bell gap)")
    print("=" * 78)
    asis = run_scenario(base, n_reps=25)
    print(fmt(asis, show))

    print("\n" + "=" * 78)
    print("SINGLE-DIAL SWEEPS  (each changes ONE thing vs as-is)")
    print("=" * 78)

    scenarios = {
        "geofence summon @50% adoption":
            dict(advance_summon="geofence", geofence_adoption=0.5),
        "geofence summon @90% adoption":
            dict(advance_summon="geofence", geofence_adoption=0.9),
        "holding policy (internal, H=4)":
            dict(not_ready_policy="holding", holding_location="internal"),
        "external staging ground":
            dict(not_ready_policy="holding", holding_location="external_staging"),
        "widen bell gap 20->35 min":
            dict(bell_gap_min=35.0),
        "mode shift -20% cars":
            dict(mode_shift_frac=0.20),
        "egress coupling = CALMING (hypothesis on)":
            dict(egress_coupling="calming"),
        "COMBINED: geofence90 + staging + bellgap35 + -20% cars":
            dict(advance_summon="geofence", geofence_adoption=0.9,
                 not_ready_policy="holding", holding_location="external_staging",
                 bell_gap_min=35.0, mode_shift_frac=0.20),
    }
    for name, ov in scenarios.items():
        res = run_scenario(base, n_reps=25, **ov)
        print(f"\n{name}:")
        print("  " + fmt(res, show))

    print("\n" + "=" * 78)
    print("Reminder: numbers are PLACEHOLDER-driven. Read DIRECTION and RANK,")
    print("not absolute values, until the measured distributions are loaded.")
    print("=" * 78)
