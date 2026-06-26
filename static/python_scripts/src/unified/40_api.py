# Fragment 40_api — public API: compute_unified_schedule (concatenated at build; do not add imports)


def ceil_div(a, b):
    """Ceiling division for positive integers: ceil(a / b).

    Pure-python helper, no imports required.  Works for a >= 0, b > 0.
    """
    return -(-a // b)


def compute_unified_schedule(
    now_epoch,
    horizon_end_epoch,
    import_rates,
    export_rates,
    free_sessions,
    saving_window,
    saving_bonus_events,
    available_kwh,
    capacity_kwh,
    reserve_kwh,
    power_rate_kw,
    efficiency,
    allow_discharge,
    minimum_slot_length,
    step_minutes=5,
    add_minutes=None,
    epoch_to_iso=None,
    # ------------------------------------------------------------------
    # Load-aware reserve parameters (two-pass DP).
    #
    # These replace the old approach of reading a separate
    # ``optimal_charge_slots`` sensor.  Instead the DP's OWN plan
    # (first pass) determines the next charge window, and a per-step
    # SoC floor is computed to protect house load until that charge.
    # A second DP pass then plans around that floor.
    #
    # All parameters have safe defaults so existing callers (including
    # all current tests) see exactly the same behaviour as before.
    # ------------------------------------------------------------------
    idle_power_kw=0.0,
    lower_discharge_limit_kwh=0.0,
    hard_lower_limit_kwh=None,
    charge_price_threshold=None,
    discharge_price_threshold=None,
    max_passes=2,
):
    """
    Compute a unified battery charge/discharge schedule.

    A dynamic-programming optimiser over (minute, state-of-charge level).
    SoC is discretised into steps of size ``power_rate_kw * (1/60) kWh``
    — the energy moved in one minute at full power.  At each minute the
    action is one of:

      - **charge one step** — import energy, increase SoC
      - **discharge one step** — export energy, decrease SoC
      - **idle** — no change

    The DP maximises net value:

      net = export_revenue + saving_bonus - import_cost

    where import_cost is adjusted for round-trip efficiency.  SoC is
    constrained to stay within ``[lower_bound_kwh, capacity_kwh]``.
    Power limits are enforced by the step size (one step per minute at
    full power).

    **Load-aware reserve** (two-pass DP)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    When ``idle_power_kw > 0`` the function runs up to *max_passes*
    DP solves.  The first pass finds the optimal next-charge window
    (ignoring house load).  A per-step SoC floor is then computed that
    reserves enough energy to power the house (idle draw) until that
    charge, plus a *lower_discharge_limit_kwh* margin.  The second pass solves
    with this floor, preventing the battery from discharging below the
    load-survival level.  If *max_passes >= 3* and the next-charge
    window shifts, additional passes are run until it stabilises.

    The output (implemented in later slices) is a merged list of events:

      ``{"start": epoch, "end": epoch, "intent": "charge"|"discharge"|"idle",
        "price": float}``

    Parameters
    ----------
    now_epoch : int
        Current time, in epoch seconds, already truncated to the minute.
    horizon_end_epoch : int
        Plan no further than this epoch (e.g. end of tomorrow's rates).
    import_rates : list[dict]
        Each dict has keys ``start`` (epoch), ``end`` (epoch), and
        ``price`` (float in £/kWh or pence — caller-consistent; treat
        as a number).
    export_rates : list[dict]
        Each dict has keys ``start`` (epoch), ``end`` (epoch), and
        ``price`` (float, same unit convention as import_rates).
    free_sessions : list[dict]
        Each dict has keys ``start``, ``end`` (epoch).  Import is
        treated as zero cost inside these windows.
    saving_window : dict or None
        A single dict ``{"start": epoch, "end": epoch}`` representing
        the current or next saving session window, or ``None``.
    saving_bonus_events : list[dict]
        Each dict has keys ``start``, ``end`` (epoch) and
        ``bonus_pence`` (float, export bonus in pence/kWh inside the
        window).
    step_minutes : int, optional
        DP / inverter time resolution in minutes.  Default 5 because
        the inverter cannot switch modes faster than 5 minutes.  All
        rate periods, free sessions and saving windows are ASSUMED to
        start and end on the step grid (Octopus data is half-hourly, so
        5-minute steps divide it exactly).  A step is classified by its
        START epoch via ``_rate_at`` / ``_in_*``.
    available_kwh : float
        Current usable battery energy in kWh.
    capacity_kwh : float
        Usable battery capacity in kWh (upper SoC bound).
    reserve_kwh : float
        Legacy reserve floor in kWh (lower SoC bound) when
        *hard_lower_limit_kwh* is not provided.  Never discharge below
        this level.
    power_rate_kw : float
        Maximum charge/discharge power in kW.
    efficiency : float
        Round-trip efficiency (0..1), e.g. 0.9.
    allow_discharge : bool
        If False, no discharge actions are permitted.
    minimum_slot_length : int
        Minimum emitted slot length in minutes (0 = no minimum).
    add_minutes : callable
        ``add_minutes(epoch_seconds, n) -> epoch_seconds``.  Injected
        helper; accepted for API stability (equivalent to
        ``epoch + n * 60`` since all times are raw ints).
    epoch_to_iso : callable
        ``epoch_to_iso(epoch_seconds) -> str``.  Injected ISO
        formatter; used in later slices for output serialisation.
    idle_power_kw : float, optional
        House idle draw in kW.  When > 0, enables the two-pass DP so
        the battery reserves energy for house load until the next
        charge.  Default 0.0 (single-pass, back-compat).
    lower_discharge_limit_kwh : float, optional
        Extra energy margin (kWh) above the hard floor to buffer
        against load uncertainty.  Default 0.0.
    hard_lower_limit_kwh : float or None, optional
        Absolute SoC floor in kWh.  If None (default), *reserve_kwh*
        is used as the lower bound, maintaining backward compatibility.
    max_passes : int, optional
        Maximum number of DP passes for the load-aware floor.
        Default 2 (first pass finds next charge, second pass plans
        with floor).  Must be >= 1.  Ignored when *idle_power_kw <= 0*
        (single pass).

    Returns
    -------
    list[dict]
        Empty list in this slice; merged schedule events in later
        slices.
    """
    # ------------------------------------------------------------------
    # 1.  Derived quantities
    # ------------------------------------------------------------------

    # TIME STEP: the DP runs at step_minutes resolution (default 5 min
    # = inverter's minimum mode-switch interval).  All rate periods,
    # free sessions and saving windows are ASSUMED to start/end on the
    # step grid (Octopus data is half-hourly, so 5-min steps divide it
    # exactly).  A step is classified by its START epoch via
    # _rate_at/_in_*.

    # Energy moved in one step at full power (kWh)
    step_kwh = power_rate_kw * (step_minutes / 60.0)

    # Total number of steps in the planning horizon
    total_steps = int((horizon_end_epoch - now_epoch) // (step_minutes * 60))
    if total_steps < 0:
        total_steps = 0

    # Lower bound of the SoC grid.  When hard_lower_limit_kwh is provided use
    # it as the absolute floor; otherwise fall back to reserve_kwh for
    # backward compatibility.
    lower_bound_kwh = hard_lower_limit_kwh if hard_lower_limit_kwh is not None else reserve_kwh

    # Number of discrete SoC levels spanning [lower_bound_kwh, capacity_kwh]
    if step_kwh > 0:
        n_levels = int(round((capacity_kwh - lower_bound_kwh) / step_kwh))
    else:
        n_levels = 0
    if n_levels < 0:
        n_levels = 0

    # Current SoC expressed as a level index above lower_bound_kwh
    if step_kwh > 0:
        start_level = int(round((available_kwh - lower_bound_kwh) / step_kwh))
    else:
        start_level = 0
    start_level = max(0, min(start_level, n_levels))

    # ------------------------------------------------------------------
    # 2.  Defensive guards
    # ------------------------------------------------------------------

    # Guard: zero or negative horizon — nothing to schedule
    if total_steps <= 0:
        return []

    # Guard: zero power rate yields degenerate step size
    if step_kwh <= 0:
        return []

    # Guard: zero SoC levels means no actionable state range
    if n_levels <= 0:
        return []

    # ------------------------------------------------------------------
    # ALGORITHM: Dynamic programming + (optional) two-pass load-aware
    # reserve floor.
    #
    # The DP table is a (total_steps + 1) × (n_levels + 1) grid.
    # Each cell stores the maximum net value achievable at step `t`
    # ending at level `l`.  Transitions:
    #
    #   charge one step   : level l ← l-1  (if l >= 1)
    #   discharge one step: level l ← l+1  (if l < n_levels
    #                                        and allow_discharge)
    #   idle              : level l ← l
    #
    # The value of each transition depends on the import/export rate at
    # minute t, efficiency, free_sessions, saving_bonus_events, and
    # saving_window.
    #
    # After the DP forward pass, backtrack to recover the optimal action
    # per minute, then merge contiguous same-intent blocks into the
    # output event list.
    #
    # Addressed parameters:
    #   - minimum_slot_length: merge passes drop slots shorter than this
    #   - epoch_to_iso    : serialise epochs to ISO strings in output
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # 2a.  Two-pass DP for load-aware reserve floor
    #
    # When idle_power_kw > 0 we replace the old external-sensor-driven
    # reserve calculation with an iterative two-pass method that uses
    # the DP's OWN plan to determine the next charge window:
    #
    #   PASS 1: solve with flat floor (None) → find next charge step.
    #   PASS 2: compute per-step floor to protect house load until that
    #           charge, then solve again.
    #
    # If max_passes >= 3 and the next-charge window shifts between
    # passes, iterate until it stabilises (capped at max_passes).
    #
    # When idle_power_kw <= 0 (default), skip the two-pass logic and
    # run a single DP pass with the flat floor, producing byte-identical
    # output to the old code.
    # ------------------------------------------------------------------

    # Determine if we need load-aware reserve
    if idle_power_kw > 0.0 or lower_discharge_limit_kwh > 0.0:
        use_two_pass = True
    else:
        use_two_pass = False

    if not use_two_pass:
        # ----- Single pass (backward compatible) -----
        actions = solve_dp(
            now_epoch,
            total_steps,
            n_levels,
            start_level,
            step_kwh,
            efficiency,
            import_rates,
            export_rates,
            free_sessions,
            saving_bonus_events,
            allow_discharge,
            step_minutes,
            charge_price_threshold=charge_price_threshold,
            discharge_price_threshold=discharge_price_threshold,
        )
    else:
        # ----- Two-pass (or more) load-aware reserve -----
        max_passes = max(max_passes, 1)
        actions = None
        prev_next_charge = -1  # sentinel

        for pass_idx in range(max_passes):
            if pass_idx == 0:
                # Pass 1: flat floor
                floor_per_step = None
            else:
                # Subsequent passes: use the floor computed from the
                # previous pass's next-charge step.
                floor_per_step = floor_per_step

            actions = solve_dp(
                now_epoch,
                total_steps,
                n_levels,
                start_level,
                step_kwh,
                efficiency,
                import_rates,
                export_rates,
                free_sessions,
                saving_bonus_events,
                allow_discharge,
                step_minutes,
                min_level_per_step=floor_per_step,
                charge_price_threshold=charge_price_threshold,
                discharge_price_threshold=discharge_price_threshold,
            )

            # Find the first charge step in the plan.
            next_charge_step = total_steps  # default: no charge in horizon
            for t, a in enumerate(actions):
                if a == "charge":
                    next_charge_step = t
                    break

            # Check for stability (early exit if next-charge window
            # stabilised).
            if pass_idx >= 1 and next_charge_step == prev_next_charge:
                break
            prev_next_charge = next_charge_step

            # Compute per-step floor for the next pass (only needed
            # if we'll do another pass).
            if pass_idx + 1 < max_passes:
                floor_per_step = compute_load_floor(
                    total_steps,
                    next_charge_step,
                    n_levels,
                    step_minutes,
                    idle_power_kw,
                    lower_discharge_limit_kwh,
                    step_kwh,
                    now_epoch=now_epoch,
                    import_rates=import_rates,
                    export_rates=export_rates,
                    saving_bonus_events=saving_bonus_events,
                    efficiency=efficiency,
                )

    # SLICE 4: convert DP per-step actions into merged event dicts
    events = actions_to_events(
        actions,
        now_epoch,
        step_minutes,
        import_rates,
        export_rates,
        free_sessions,
        saving_bonus_events,
        epoch_to_iso,
        charge_price_threshold=charge_price_threshold,
    )
    return events


def compute_load_floor(
    total_steps,
    next_charge_step,
    n_levels,
    step_minutes,
    idle_power_kw,
    lower_discharge_limit_kwh,
    step_kwh,
    now_epoch=0,
    import_rates=None,
    export_rates=None,
    saving_bonus_events=None,
    efficiency=1.0,
):
    """Build per-step minimum level array for load-aware reserve.

    For steps *before* the next charge the floor reserves enough energy
    to keep the house running until that charge (idle draw + buffer).
    From the charge step onward the floor drops to zero (the charge
    replenishes the battery).

    When the current effective export price (export + saving bonus)
    exceeds the breakeven price (max import from now until charge +
    replacement cost at the charge step), the floor for that step is
    reduced to the soft buffer alone, because draining and buying back
    yields a net profit.

    Parameters
    ----------
    total_steps : int
    next_charge_step : int
        Step index of the first charge action (or *total_steps* if no
        charge is planned in the horizon).
    n_levels : int
        Maximum level index (number of steps above the hard floor).
    step_minutes : int
        Duration of one DP step in minutes.
    idle_power_kw : float
        House idle draw in kW.
    lower_discharge_limit_kwh : float
        Extra energy buffer in kWh above the hard floor.
    step_kwh : float
        Energy per level step in kWh.
    now_epoch : int
        Current time in epoch seconds (for looking up rates).
    import_rates : list[dict] or None
        Each dict has keys ``start``, ``end``, ``price`` (same format as
        the top-level parameter).
    export_rates : list[dict] or None
        Each dict has keys ``start``, ``end``, ``price``.
    saving_bonus_events : list[dict] or None
        Each dict has keys ``start``, ``end``, ``bonus_pence``.
    efficiency : float
        Round-trip efficiency (0..1).

    Returns
    -------
    list[int]
        Per-step minimum level array of length *total_steps*, each
        entry in [0, n_levels].
    """
    floor_level = [0] * total_steps
    if idle_power_kw <= 0.0 and lower_discharge_limit_kwh <= 0.0:
        return floor_level

    # Soft buffer in discrete levels (shared between branches)
    soft_buffer_levels = 0
    if step_kwh > 0:
        soft_buffer_levels = ceil_div(
            int(round(lower_discharge_limit_kwh * 1e6)),
            int(round(step_kwh * 1e6)),
        )

    # Precompute import prices and suffix-max for the breakeven check.
    # Only meaningful when there is a charge in the horizon.
    no_charge_in_horizon = next_charge_step >= total_steps
    if not no_charge_in_horizon and import_rates is not None:
        import_price_at = [0.0] * total_steps
        for t in range(total_steps):
            epoch = now_epoch + t * step_minutes * 60
            p = rate_at(import_rates, epoch)
            import_price_at[t] = p if p is not None else 0.0

        # Suffix max: highest import price from t to next_charge_step - 1
        max_import_from = [0.0] * total_steps
        running_max = 0.0
        for t in range(next_charge_step - 1, -1, -1):
            running_max = max(import_price_at[t], running_max)
            max_import_from[t] = running_max

        charge_price = import_price_at[next_charge_step]
    else:
        # Sentinel: no breakeven check when charge_price is 0
        # (the effective_export > breakeven comparison will be False)
        charge_price = 0.0

    for t in range(total_steps):
        if t >= next_charge_step:
            # At or after the charge step: no extra reserve needed;
            # the charge itself replenishes SoC.
            floor_level[t] = 0
        else:
            # Determine whether the effective export price is high
            # enough that draining the battery (selling now) and
            # buying back later yields a net profit.
            use_soft_buffer_only = False
            if charge_price != 0.0:
                epoch = now_epoch + t * step_minutes * 60
                export_price = rate_at(export_rates, epoch)
                if export_price is None:
                    export_price = 0.0
                bonus = bonus_at(saving_bonus_events, epoch) if saving_bonus_events else 0.0
                effective_export = export_price + bonus
                max_import = max_import_from[t]
                breakeven = max_import + (charge_price / efficiency) if efficiency > 0 else float('inf')

                if effective_export > breakeven:
                    use_soft_buffer_only = True

            if use_soft_buffer_only:
                floor_level[t] = min(n_levels, soft_buffer_levels)
            else:
                # Original tapering logic: reserve enough to cover
                # remaining hours of house load plus soft buffer.
                remaining_hours = (next_charge_step - t) * step_minutes / 60.0
                required_kwh = idle_power_kw * remaining_hours + lower_discharge_limit_kwh
                if step_kwh > 0:
                    floor_level[t] = min(
                        n_levels,
                        ceil_div(
                            int(round(required_kwh * 1e6)),
                            int(round(step_kwh * 1e6)),
                        ),
                    )
                else:
                    floor_level[t] = 0

            # Cap the floor at the soft buffer when there is no charge in the
            # horizon so the battery is not blocked from discharging entirely.
            if no_charge_in_horizon:
                if floor_level[t] > soft_buffer_levels:
                    floor_level[t] = soft_buffer_levels

    return floor_level
