# Fragment 90_glue — HA python_script glue (LAST fragment, only one referencing
# hass/data/logger/output/dt_util).  Concatenated at build; do not add imports.
"""
HA python_script glue footer — APPENDED to pure core by build.sh.

This file is NOT standalone; it relies on names defined above (the inlined
pure core).  The HA sandbox injects the globals ``hass``, ``data``, ``logger``,
``output``, ``datetime``, ``dt_util``, and builtins.

Sandbox constraint: NO ``import`` statements allowed.
"""

# ======================================================================
# Expected ``data`` keys (populated by the automation calling this script)
# ======================================================================
#
# now_epoch           (int)       — current time, epoch seconds
# horizon_end_epoch   (int)       — plan horizon, epoch seconds
# import_rates        (list[dict]) — [{"start": int, "end": int, "price": float}]
# export_rates        (list[dict]) — same shape as import_rates
# free_sessions       (list[dict]) — [{"start": int, "end": int}]
# saving_window       (dict|None)  — {"start": int, "end": int} or None
# saving_bonus_events (list[dict]) — [{"start": int, "end": int,
#                                      "bonus_pence": float}]  # value IN POUNDS/kWh
# available_kwh       (float|None) — current usable battery energy (None = unavailable)
# capacity_kwh        (float|None) — usable battery capacity
# reserve_kwh         (float|None) — reserve floor
# power_rate_kw       (float|None) — max charge/discharge power
# efficiency          (float|None) — round-trip efficiency (0..1)
# allow_discharge     (bool|None)  — whether discharge is permitted
# minimum_slot_length    (int|None)   — minimum emitted slot length
# step_minutes        (int)        — DP step resolution (default 5)
# idle_power_kw       (float|None) — house idle draw in kW (0 = no load-aware reserve)
# hard_lower_limit_kwh      (float|None) — absolute SoC floor in kWh (None = use reserve_kwh)
# lower_discharge_limit_kwh     (float)      — extra reserve buffer above hard floor (default 0)
#
# All times are epoch ints.  All prices are in pounds/kWh (bonus already
# converted to pounds upstream).
# ======================================================================


# ------------------------------------------------------------------
# Epoch-to-ISO formatter using injected sandbox helpers.
#
# ``dt_util.utc_from_timestamp`` gives an aware UTC datetime;
# ``dt_util.as_local`` converts to HA's timezone; ``.isoformat()``
# appends the correct offset string (e.g. "+00:00" or "+01:00").
#
# Avoids ``datetime.timezone`` (not in the sandbox's allowed-attribute
# list for ``datetime``).
# ------------------------------------------------------------------


def epoch_to_iso(e):
    """Convert epoch seconds *e* to an ISO-8601 string with local offset."""
    return dt_util.as_local(dt_util.utc_from_timestamp(e)).isoformat()


# ------------------------------------------------------------------
# Main glue
# ------------------------------------------------------------------


def main():
    """Run the optimiser and write the result to sensor.energy_intents_py.

    This function is called once per script invocation.  All data is
    expected in the ``data`` dict provided by the HA automation.
    Results are returned via the ``output`` dict (response_variable)
    and also published as a sensor state for template-based consumers.
    """
    d = data  # injected by HA sandbox

    # --- Guard: battery unavailable? ---
    available_kwh = d.get("available_kwh")
    capacity_kwh = d.get("capacity_kwh")

    if available_kwh is None or capacity_kwh is None or capacity_kwh <= 0:
        logger.warning(
            "unified_battery_schedule: battery unavailable "
            "(available_kwh=%s, capacity_kwh=%s) — emitting empty schedule",
            available_kwh, capacity_kwh,
        )
        output["events"] = []
        output["count"] = 0
        hass.states.set(
            "sensor.energy_intents_py",
            "on",
            {
                "events": [],
                "unavailable": True,
                "friendly_name": "Energy intents (Python)",
                "icon": "mdi:calendar",
            },
        )
        return

    # --- Extract all data with defaults ---
    now_epoch = d["now_epoch"]
    horizon_end_epoch = d["horizon_end_epoch"]
    import_rates = d.get("import_rates", [])
    export_rates = d.get("export_rates", [])
    free_sessions = d.get("free_sessions", [])
    saving_window = d.get("saving_window")
    saving_bonus_events = d.get("saving_bonus_events", [])
    reserve_kwh = d.get("reserve_kwh", 0.0)
    power_rate_kw = d.get("power_rate_kw", 0.0)
    efficiency = d.get("efficiency", 0.9)
    allow_discharge = d.get("allow_discharge", False)
    minimum_slot_length = d.get("minimum_slot_length", 0)
    step_minutes = d.get("step_minutes", 5)
    idle_power_kw = d.get("idle_power_kw", 0.0)
    hard_lower_limit_kwh = d.get("hard_lower_limit_kwh")
    lower_discharge_limit_kwh = d.get("lower_discharge_limit_kwh", 0.0)
    charge_price_threshold = d.get("charge_price_threshold")
    discharge_price_threshold = d.get("discharge_price_threshold")

    # --- Fill export-rate gaps ---
    # When Octopus hasn't published next-day export rates yet, the DP
    # still needs to evaluate charging decisions.  The discharge_value
    # function now defaults to 0 when no export rate is found, so the
    # DP can still charge into cheap import windows even without
    # known export prices.  No gap-fill needed here.

    # --- Guard: native-type rendering fail-safe ---
    def is_bad(v):
        """True if *v* is a str — indicates native rendering failed."""
        # Avoid type() and isinstance() — the sandbox may restrict them.
        # For strings, str(v) == v; for numbers/lists/dicts it does not.
        return v == str(v)

    bad_keys = []
    # All fields must be native types (not strings).  A string means the
    # Jinja template rendered with surrounding whitespace and HA fell back
    # to treating it as a plain string.
    for key in ("import_rates", "export_rates", "free_sessions",
                "saving_bonus_events", "saving_window",
                "now_epoch", "horizon_end_epoch", "step_minutes",
                "power_rate_kw", "efficiency", "reserve_kwh", "idle_power_kw",
                "lower_discharge_limit_kwh", "hard_lower_limit_kwh",
                "charge_price_threshold", "discharge_price_threshold",
                "allow_discharge", "available_kwh", "capacity_kwh"):
        val = d.get(key)
        if is_bad(val):
            bad_keys.append(key)

    if bad_keys:
        logger.error(
            "unified_battery_schedule: received non-native data (template rendering "
            "failed?). Offending keys: %s",
            bad_keys,
        )
        for k in bad_keys:
            logger.error("  %s = %r", k, d.get(k))
        output["events"] = []
        output["count"] = 0
        output["error"] = "non-native data"
        hass.states.set(
            "sensor.energy_intents_py",
            "on",
            {
                "events": [],
                "error": "non-native data",
                "friendly_name": "Energy intents (Python)",
                "icon": "mdi:calendar",
            },
        )
        return

    # Injected callables (sandbox-safe — no imports)
    add_minutes = lambda e, n: e + n * 60

    

    # --- Log inputs for debugging ---
    logger.info(
        "unified_battery_schedule: inputs now=%s available=%.3fkWh capacity=%.3fkWh "
        "hard_floor=%s soft_buffer=%.3fkWh idle=%.3fkW power=%.3fkW eff=%.3f "
        "allow_discharge=%s charge_threshold=%s discharge_threshold=%s "
        "import_rates=%d export_rates=%d free_sessions=%d bonus_events=%d",
        now_epoch, available_kwh, capacity_kwh,
        hard_lower_limit_kwh, lower_discharge_limit_kwh, idle_power_kw, power_rate_kw, efficiency,
        allow_discharge, charge_price_threshold, discharge_price_threshold,
        len(import_rates), len(export_rates), len(free_sessions), len(saving_bonus_events),
    )

    try:
        events = compute_unified_schedule(
            now_epoch=now_epoch,
            horizon_end_epoch=horizon_end_epoch,
            import_rates=import_rates,
            export_rates=export_rates,
            free_sessions=free_sessions,
            saving_window=saving_window,
            saving_bonus_events=saving_bonus_events,
            available_kwh=available_kwh,
            capacity_kwh=capacity_kwh,
            reserve_kwh=reserve_kwh,
            power_rate_kw=power_rate_kw,
            efficiency=efficiency,
            allow_discharge=allow_discharge,
            minimum_slot_length=minimum_slot_length,
            step_minutes=step_minutes,
            add_minutes=add_minutes,
            epoch_to_iso=epoch_to_iso,
            idle_power_kw=idle_power_kw,
            hard_lower_limit_kwh=hard_lower_limit_kwh,
            lower_discharge_limit_kwh=lower_discharge_limit_kwh,
            charge_price_threshold=charge_price_threshold,
            discharge_price_threshold=discharge_price_threshold,
        )
        logger.info(
            "unified_battery_schedule: computed %d events",
            len(events),
        )
        for ev in events:
            if ev.get("intent") == "Charge":
                logger.info(
                    "unified_battery_schedule: event Charge %s -> %s import=%.4f",
                    ev.get("start"), ev.get("end"), ev.get("import_price"),
                )
            else:
                logger.info(
                    "unified_battery_schedule: event Discharge %s -> %s export=%.4f",
                    ev.get("start"), ev.get("end"), ev.get("export_price"),
                )
    except Exception as exc:
        logger.error(
            "unified_battery_schedule: compute_unified_schedule failed: %s", exc,
        )
        output["events"] = []
        output["count"] = 0
        output["error"] = str(exc)
        hass.states.set(
            "sensor.energy_intents_py",
            "on",
            {
                "events": [],
                "error": str(exc),
                "friendly_name": "Energy intents (Python)",
                "icon": "mdi:calendar",
            },
        )
        return

    output["events"] = events
    output["count"] = len(events)

    hass.states.set(
        "sensor.energy_intents_py",
        "on",
        {
            "events": events,
            "friendly_name": "Energy intents (Python)",
            "icon": "mdi:calendar",
        },
    )


main()
