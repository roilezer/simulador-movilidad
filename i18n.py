"""
i18n.py
================================================================================
All user-facing strings for the Streamlit app, in English and Colombian Spanish.
Kept separate from the app so a native speaker can proofread/extend without
touching code, and so adding a third language is just another column.

Strings with {placeholders} are .format()-ed in the app with live values.
Option labels (OPT) are DISPLAY ONLY — the underlying selectbox values stay as
the engine's keys (off/placard/geofence/...), so language never affects the model.
================================================================================
"""

LANGS = {"Español": "es", "English": "en"}

STR = {
    # ---- chrome --------------------------------------------------------------
    "lang_label":        {"en": "Language / Idioma", "es": "Language / Idioma"},
    "page_title":        {"en": "Afternoon Pickup Simulator",
                          "es": "Simulador de Recogida de la Tarde"},
    "main_title":        {"en": "Afternoon Pickup Simulator",
                          "es": "Simulador de Recogida de la Tarde"},
    "main_caption":      {"en": "Placeholder distributions — read direction and rank, "
                                "not absolute values. Safety is a hard gate, not a score.",
                          "es": "Distribuciones de marcador de posición — lea la dirección y "
                                "el orden, no los valores absolutos. La seguridad es un "
                                "umbral inquebrantable, no un puntaje."},
    "sidebar_title":     {"en": "Dials", "es": "Controles"},
    "sidebar_caption":   {"en": "Each control is a lever in the model. Hover the ⓘ for what it does.",
                          "es": "Cada control es una palanca del modelo. Pase el cursor sobre la ⓘ para ver qué hace."},

    # ---- sidebar: demand & resources ----------------------------------------
    "exp_demand":        {"en": "Demand & resources", "es": "Demanda y recursos"},
    "n_cars":            {"en": "Cars in a peak afternoon", "es": "Autos en una tarde pico"},
    "n_cars_help":       {"en": "Total private-vehicle pickups. Mode-shift removes a fraction of these.",
                          "es": "Total de recogidas en vehículo particular. El cambio de modo elimina una fracción de estos."},
    "mode_shift":        {"en": "Mode shift — fraction of cars removed",
                          "es": "Cambio de modo — fracción de autos eliminados"},
    "mode_shift_help":   {"en": "Carpool / shuttle / in-house bus. Attacks the root cause: car count.",
                          "es": "Carpool / shuttle / bus propio. Ataca la causa raíz: la cantidad de autos."},
    "buffer":            {"en": "Internal buffer (cars on grounds)",
                          "es": "Capacidad interna (autos dentro del colegio)"},
    "buffer_help":       {"en": "Measured 20–25. When full, cars spill onto the road (or divert to staging).",
                          "es": "Medida en 20–25. Cuando se llena, los autos se desbordan a la vía (o se desvían al parqueadero de espera)."},
    "spots":             {"en": "Boarding spots (servers)", "es": "Puntos de abordaje (servidores)"},
    "spots_help":        {"en": "The five stop-and-drop spots in the roundabout.",
                          "es": "Los cinco puntos de recogida en la rotonda."},

    # ---- sidebar: schedule ---------------------------------------------------
    "exp_schedule":      {"en": "Schedule", "es": "Horario"},
    "bell_gap":          {"en": "Primary → high-school bell gap (min)",
                          "es": "Brecha entre salidas: primaria → bachillerato (min)"},
    "bell_gap_help":     {"en": "Currently ~20 min. Widening it desynchronises the two largest cohorts.",
                          "es": "Actualmente ~20 min. Ampliarla desincroniza las dos cohortes más grandes."},

    # ---- sidebar: summon -----------------------------------------------------
    "exp_summon":        {"en": "Advance summon", "es": "Llamado anticipado"},
    "summon_mech":       {"en": "Summon mechanism", "es": "Mecanismo de llamado"},
    "summon_help":       {"en": "off = loudspeaker at the spot. placard = visor card read on entry. geofence = parent-app ETA.",
                          "es": "apagado = altavoz en el punto. tarjeta = leída al ingresar. geocerca = ETA por app de los padres."},
    "geo_adopt":         {"en": "Geofence adoption φ", "es": "Adopción de geocerca φ"},
    "geo_adopt_help":    {"en": "Fraction of cars with a working app + location permission. Non-adopters fall back to placard.",
                          "es": "Fracción de autos con app y permiso de ubicación activos. Los demás usan la tarjeta como respaldo."},

    # ---- sidebar: not-ready --------------------------------------------------
    "exp_policy":        {"en": "Not-ready policy", "es": "Política de niño no listo"},
    "policy_sel":        {"en": "Policy when the child isn't ready",
                          "es": "Qué hacer cuando el niño no está listo"},
    "policy_help":       {"en": "blocking = car holds the spot (as-is). holding = pull aside, free the server, return when ready.",
                          "es": "bloqueo = el auto retiene el punto (actual). apartar = se hace a un lado, libera el servidor y regresa cuando está listo."},
    "holding_loc":       {"en": "Where not-ready cars wait",
                          "es": "Dónde esperan los autos sin niño listo"},
    "holding_loc_help":  {"en": "external_staging = a remote consolidation lot off the carriageway. Needs 'holding' policy to take effect.",
                          "es": "parqueadero externo = lote remoto de consolidación, fuera de la vía. Requiere la política 'apartar' para tener efecto."},
    "holding_cap":       {"en": "Internal holding capacity",
                          "es": "Capacidad de la zona de espera interna"},
    "discipline":        {"en": "Staging discipline (latency multiplier)",
                          "es": "Disciplina de organización (multiplicador de latencia)"},
    "discipline_help":   {"en": "<1 = tighter staging shrinks the dawdle tail. 1.0 = today's loose staging.",
                          "es": "<1 = mejor organización reduce la cola de demoras. 1.0 = organización actual (laxa)."},

    # ---- sidebar: egress -----------------------------------------------------
    "exp_egress":        {"en": "Egress (the ceiling)", "es": "Salida (el techo)"},
    "egress_time":       {"en": "Mean merge time at west gate (min)",
                          "es": "Tiempo medio de incorporación en la portería occidental (min)"},
    "egress_time_help":  {"en": "Ready-at-gate → merged into 80 km/h traffic. THIS is usually the binding constraint.",
                          "es": "Listo-en-portería → incorporado al tráfico de 80 km/h. ESTE suele ser el cuello de botella."},
    "coupling":          {"en": "Egress coupling", "es": "Acoplamiento de la salida"},
    "coupling_help":     {"en": "calming = the queue-as-traffic-calming hypothesis: merge gets HARDER when the road queue is short.",
                          "es": "calmante = hipótesis de la cola como calmante de tráfico: incorporarse se vuelve MÁS difícil cuando la cola en la vía es corta."},

    # ---- sidebar: safety & run ----------------------------------------------
    "exp_safety":        {"en": "Safety & run settings", "es": "Seguridad y configuración"},
    "curve_thr":         {"en": "Cars from gate to curve (safety gate)",
                          "es": "Autos desde la portería hasta la curva (umbral de seguridad)"},
    "curve_thr_help":    {"en": "Road queue beyond this reaches the blind curve. Any scenario that exceeds it FAILS the safety gate.",
                          "es": "Una cola mayor a esto alcanza la curva ciega. Cualquier escenario que la supere REPRUEBA el umbral de seguridad."},
    "n_reps":            {"en": "Replications (simulated days)", "es": "Réplicas (días simulados)"},
    "n_reps_help":       {"en": "More reps = tighter confidence intervals, slower runs.",
                          "es": "Más réplicas = intervalos de confianza más estrechos, corridas más lentas."},

    # ---- banners -------------------------------------------------------------
    "safety_pass":       {"en": "**SAFETY GATE: PASS** — peak road queue ≈ {q:.0f} cars, below the "
                                "curve threshold of {thr}. Queue stays off the blind curve.",
                          "es": "**UMBRAL DE SEGURIDAD: APROBADO** — cola pico en la vía ≈ {q:.0f} autos, "
                                "por debajo del umbral de curva de {thr}. La cola no llega a la curva ciega."},
    "safety_fail":       {"en": "**SAFETY GATE: FAIL** — peak road queue ≈ {q:.0f} cars vs curve threshold "
                                "{thr}. The queue reaches the blind curve for ≈ {mins:.0f} min/session. "
                                "This scenario is discarded regardless of its other scores.",
                          "es": "**UMBRAL DE SEGURIDAD: REPROBADO** — cola pico en la vía ≈ {q:.0f} autos frente "
                                "al umbral de curva {thr}. La cola alcanza la curva ciega durante ≈ {mins:.0f} "
                                "min/sesión. Este escenario se descarta sin importar sus otros resultados."},
    "regime_sat":        {"en": "**Egress-saturated regime** (completion {c:.0f}%, spot utilisation {u:.0f}%). "
                                "The merge is the binding constraint — readiness dials (summon, staging) will "
                                "look almost INERT here. Relieve egress / cut volume first.",
                          "es": "**Régimen saturado en la salida** (completadas {c:.0f}%, utilización de puntos "
                                "{u:.0f}%). La incorporación es el cuello de botella — los controles de llamado "
                                "(llamado, parqueadero) se verán casi INERTES aquí. Primero alivie la salida / "
                                "reduzca el volumen."},
    "regime_unsat":      {"en": "**Unsaturated regime** (completion {c:.0f}%, spot utilisation {u:.0f}%). "
                                "Egress is keeping up — readiness dials now bite.",
                          "es": "**Régimen no saturado** (completadas {c:.0f}%, utilización de puntos {u:.0f}%). "
                                "La salida da abasto — los controles de llamado ahora sí influyen."},

    # ---- metrics -------------------------------------------------------------
    "six_criteria":      {"en": "The six criteria", "es": "Los seis criterios"},
    "m_peak_queue":      {"en": "Peak road queue (safety)", "es": "Cola pico en la vía (seguridad)"},
    "m_min_curve":       {"en": "Minutes queue past curve", "es": "Minutos de cola pasando la curva"},
    "m_spilled":         {"en": "Cars spilled to road", "es": "Autos desbordados a la vía"},
    "m_parent_mean":     {"en": "Parent time — mean", "es": "Tiempo de los padres — media"},
    "m_parent_p90":      {"en": "Parent time — p90", "es": "Tiempo de los padres — p90"},
    "m_carbon":          {"en": "Carbon proxy (veh-min idle)", "es": "Proxy de carbono (veh-min en ralentí)"},
    "m_blocked":         {"en": "Cars blocked at a spot", "es": "Autos bloqueados en un punto"},
    "m_staging":         {"en": "Cars routed to staging", "es": "Autos enviados al parqueadero"},
    "m_staging_help":    {"en": "Only non-zero when 'where not-ready cars wait' = external staging.",
                          "es": "Distinto de cero solo cuando 'dónde esperan' = parqueadero externo."},
    "vs_asis":           {"en": "vs as-is", "es": "vs actual"},

    # ---- charts --------------------------------------------------------------
    "overlay":           {"en": "Overlay as-is baseline on charts",
                          "es": "Superponer la línea base actual en las gráficas"},
    "chart_road":        {"en": "Road queue over time — the safety chart",
                          "es": "Cola en la vía en el tiempo — la gráfica de seguridad"},
    "ax_minutes":        {"en": "minutes from session start (t=0 ≈ 14:20)",
                          "es": "minutos desde el inicio de la sesión (t=0 ≈ 14:20)"},
    "ax_cars_road":      {"en": "cars queued on the road", "es": "autos en cola en la vía"},
    "lbl_curve_thr":     {"en": "curve threshold", "es": "umbral de curva"},
    "cap_road":          {"en": "Blue = this scenario (band = ±1 SD across days). Grey dashed = as-is. "
                                "Anything above the red line is on the blind curve.",
                          "es": "Azul = este escenario (banda = ±1 DE entre días). Gris punteado = actual. "
                                "Todo lo que esté sobre la línea roja está en la curva ciega."},
    "chart_inside":      {"en": "Inside the grounds", "es": "Dentro del colegio"},
    "ax_cars":           {"en": "cars", "es": "autos"},
    "ser_buffer":        {"en": "buffer occupancy", "es": "ocupación interna"},
    "ser_spots":         {"en": "spots busy", "es": "puntos ocupados"},
    "cap_inside":        {"en": "When buffer occupancy pins at capacity, the overflow is what becomes the "
                                "road queue (or goes to staging).",
                          "es": "Cuando la ocupación interna se topa con la capacidad, el excedente es lo que "
                                "se convierte en cola en la vía (o va al parqueadero)."},
    "chart_parent":      {"en": "Parent time distribution", "es": "Distribución del tiempo de los padres"},
    "ax_arr_dep":        {"en": "minutes from arrival to departure",
                          "es": "minutos desde la llegada hasta la salida"},
    "cap_parent":        {"en": "Black = mean ({mean:.0f} min). Red dashed = p90 ({p90:.0f} min) — "
                                "predictability matters as much as the average for satisfaction.",
                          "es": "Negro = media ({mean:.0f} min). Rojo punteado = p90 ({p90:.0f} min) — "
                                "la previsibilidad importa tanto como el promedio para la satisfacción."},

    # ---- validation ----------------------------------------------------------
    "val_title":         {"en": "Model validation (run before trusting any lever)",
                          "es": "Validación del modelo (ejecútela antes de confiar en cualquier palanca)"},
    "val_body":          {"en": "**M/G/5 degenerate case** — switch off blocking (every child ready at t=0). "
                                "The mean parent time should converge on the analytic M/G/5 result, and "
                                "`frac_blocked` should be ≈ 0. If not, the model is wrong, not the world.",
                          "es": "**Caso degenerado M/G/5** — desactive el bloqueo (todos los niños listos en t=0). "
                                "El tiempo medio de los padres debería converger al resultado analítico M/G/5, y "
                                "`frac_blocked` debería ser ≈ 0. Si no, el modelo está mal, no el mundo."},
    "val_btn":           {"en": "Run degenerate check", "es": "Ejecutar verificación degenerada"},
    "val_result":        {"en": "Mean parent time: **{mean:.1f} min** · frac_blocked: **{fb:.3f}** "
                                "(should be ≈ 0). Compare the mean against your napkin M/G/5.",
                          "es": "Tiempo medio de los padres: **{mean:.1f} min** · frac_blocked: **{fb:.3f}** "
                                "(debería ser ≈ 0). Compare la media con su M/G/5 de servilleta."},

    # ---- footer --------------------------------------------------------------
    "footer":            {"en": "Engine: afternoon_pickup_sim.py · Compute: sim_app_core.py · "
                                "All distributions are placeholders pending the Phase-1 measurement week.",
                          "es": "Motor: afternoon_pickup_sim.py · Cómputo: sim_app_core.py · Todas las "
                                "distribuciones son marcadores de posición pendientes de la semana de medición de la Fase 1."},

    # ---- units (with leading space) -----------------------------------------
    "u_cars":            {"en": " cars", "es": " autos"},
    "u_min":             {"en": " min", "es": " min"},
    "u_pct":             {"en": " %", "es": " %"},
}

# ---- selectbox option DISPLAY labels (values stay as engine keys) -----------
OPT = {
    "summon": {
        "en": {"off": "off (loudspeaker)", "placard": "placard (visor card)",
               "geofence": "geofence (app)"},
        "es": {"off": "apagado (altavoz)", "placard": "tarjeta (parasol)",
               "geofence": "geocerca (app)"},
    },
    "policy": {
        "en": {"blocking": "blocking (as-is)", "recirculate": "recirculate",
               "holding": "holding (pull aside)"},
        "es": {"blocking": "bloqueo (actual)", "recirculate": "recircular",
               "holding": "apartar (holding)"},
    },
    "holding": {
        "en": {"none": "none", "internal": "internal", "external_staging": "external staging"},
        "es": {"none": "ninguno", "internal": "interno", "external_staging": "parqueadero externo"},
    },
    "coupling": {
        "en": {"independent": "independent", "calming": "calming (hypothesis)"},
        "es": {"independent": "independiente", "calming": "calmante (hipótesis)"},
    },
}


def t(key: str, lang: str) -> str:
    return STR[key][lang]


def opt(group: str, value: str, lang: str) -> str:
    return OPT[group][lang][value]
