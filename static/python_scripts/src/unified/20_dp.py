# Fragment 20_dp — dynamic-programming solver (concatenated at build; do not add imports)

# --- Slice 3: dynamic-programming core ---


def solve_dp(
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
    min_level_per_step=None,
    charge_price_threshold=None,
    discharge_price_threshold=None,
):
    """Backward value-to-go DP over (step, SoC level, last_mode).

    The DP state includes ``last_mode`` in {0=idle, 1=discharge, 2=charge}
    to enforce the inverter's minimum mode-switch buffer (``step_minutes``):

        - idle is always legal.
        - charge is legal UNLESS the previous action was discharge.
        - discharge is legal UNLESS the previous action was charge.

    At the first step (t=0) the battery is not mid-action, so the initial
    previous-mode is treated as idle (unconstrained first action).

    Parameters
    ----------
    min_level_per_step : list[int] or None, optional
        Per-step minimum SoC level (above the fixed lower bound).  If
        provided, must be a list of length *total_steps*.  The constraint
        is enforced at transition boundaries:

            An action at step t is only legal if the resulting level at
            step t+1 is >= min_level_per_step[t+1].  There is no floor
            constraint on the terminal level (step total_steps).

        If the battery starts below a floor (start_level <
        min_level_per_step[0]), the floor cannot be retroactively
        satisfied — the DP simply does not permit further discharge below
        it.  This provides graceful degradation: the optimiser never
        returns an infeasible / empty schedule due to a floor mismatch.

        When *None* (default), behaviour is identical to a flat floor at
        level 0 — production callers that do not supply this argument see
        zero change in output.

    Returns a list ``actions`` of length *total_steps*, each element one of
    ``"charge"``, ``"discharge"``, ``"idle"`` — the optimal action for that
    step (starting from *start_level* and following the optimal policy).
    """
    # 1. Precompute per-step action values
    cv = [None] * total_steps
    dv = [None] * total_steps
    for t in range(total_steps):
        epoch_t = now_epoch + t * step_minutes * 60
        cv[t] = charge_value(
            epoch_t, import_rates, free_sessions, efficiency, step_kwh,
            charge_price_threshold=charge_price_threshold,
        )
        dv[t] = discharge_value(
            epoch_t, import_rates, export_rates, saving_bonus_events,
            efficiency, step_kwh, allow_discharge,
            discharge_price_threshold=discharge_price_threshold,
        )

    # 2. Rolling value-to-go arrays and action table.
    #
    # State is (level, last_mode) where last_mode in {0=idle, 1=discharge,
    # 2=charge}.  We keep nxt = V[t+1] and cur = V[t], each a 2-D list
    # of shape (n_levels+1) x 3.
    # The action table act[t][l * 3 + m] stores the chosen action for
    # state (t, l, m) as a small int (0=idle, 1=discharge, 2=charge).
    #
    # Terminal row: V[total_steps][l][m] = 0.0 for all l, m.
    EPS = 1e-9
    nxt = [[0.0, 0.0, 0.0] for _ in range(n_levels + 1)]
    act = [[0] * ((n_levels + 1) * 3) for _ in range(total_steps)]

    # 3. Backward fill — compute cur = V[t] from nxt = V[t+1]
    #
    # FLOOR CONSTRAINT (when min_level_per_step is provided):
    #
    #   The floor is a HARD lower bound on the SoC level.  For each step
    #   *k* (0-indexed), floor[k] = min_level_per_step[k].  The terminal
    #   level (step total_steps) is unconstrained (floor = 0).
    #
    #   Convention (constraint on transitions, NOT infeasible-marking):
    #
    #     * discharge at step t is legal ONLY IF both
    #         (l_t - 1) >= floor[t+1]   AND   l_t > floor[t]
    #       The second clause (l_t > floor[t]) prevents the battery from
    #       discharging when it is already at or below the current step's
    #       floor.
    #
    #     * charge at step t is legal as long as the resulting level
    #         (l+1) >= floor[t+1].
    #       The floor constrains DISCHARGE only — charging is never
    #       blocked by the current floor.  Profitable arbitrage cycling
    #       (charge then discharge) is permitted intentionally: it earns
    #       real money, and the 5-minute opposite-intent buffer still
    #       applies between consecutive actions.
    #
    #     * idle keeps its existing rule (it does not reduce the level
    #       so it never breaches a lower floor).
    #
    #   Graceful degradation: if the battery starts below a floor the DP
    #   never marks any state infeasible — it simply forbids further
    #   discharge below the floor.  Idle and charge remain available so
    #   the battery can recover.
    #
    for t in range(total_steps - 1, -1, -1):
        cur = [[0.0, 0.0, 0.0] for _ in range(n_levels + 1)]
        # Minimum level at the CURRENT step t (origin).
        if min_level_per_step is not None and t < total_steps:
            floor_cur = min_level_per_step[t]
        else:
            floor_cur = 0
        # Minimum level at the DESTINATION (step t+1).
        # There is no step total_steps, so the terminal transition is
        # unconstrained (floor = 0).
        if min_level_per_step is not None and t + 1 < total_steps:
            floor_next = min_level_per_step[t + 1]
        else:
            floor_next = 0
        for l in range(n_levels + 1):
            for m in range(3):
                # idle — always available; new mode = 0
                idle_total = nxt[l][0]

                # charge — legal unless last mode was discharge (m == 1).
                # The floor constrains DISCHARGE only; charging is never
                # blocked by the floor (even if the battery is currently below
                # it, the DP can still charge to recover).  Profitable
                # charge-discharge cycling is intentionally allowed (it earns
                # real money, and the mode buffer still prevents rapid
                # oscillation).
                charge_total = None
                if cv[t] is not None and l < n_levels and m != 1:
                    charge_total = cv[t] + nxt[l + 1][2]

                # discharge — legal unless last mode was charge (m == 2),
                # AND the resulting level (l-1) must satisfy the floor at
                # the next step, AND the current level must be strictly
                # above the current step's floor (prevents discharging
                # when already at/below the floor).
                discharge_total = None
                if dv[t] is not None and l > 0 and m != 2:
                    if l - 1 >= floor_next and l > floor_cur:
                        discharge_total = dv[t] + nxt[l - 1][1]

                best = idle_total
                if charge_total is not None and charge_total > best:
                    best = charge_total
                if discharge_total is not None and discharge_total > best:
                    best = discharge_total

                cur[l][m] = best

                # Tie-breaking for equal-value actions.
                #
                # Discharge vs idle: prefer idle → defers discharge to later
                # steps, yielding tail-end-first discharge within an
                # equal-priced window.
                #
                # Charge vs idle: prefer charge when there is ANY future
                # value downstream (nxt[l][0] > 0), which signals a
                # profitable discharge opportunity — charge early (front-
                # first) within the charge window.  When nxt[l][0] == 0
                # there is no profitable use for stored energy downstream,
                # so prefer idle to avoid unnecessary cycling.
                #
                # This uses the idle-mode value of the CURRENT level
                # (no mode-buffer noise) as a simple "is there anything
                # valuable ahead?" check.
                #
                # Charge vs discharge: prefer discharge (arbitrary stable
                # choice since both cannot simultaneously be optimal at the
                # same (t, l) under normal conditions).
                if charge_total is not None and abs(charge_total - best) < EPS:
                    if nxt[l][0] > EPS:
                        a = 2  # Front-first within charge window
                    elif abs(idle_total - best) < EPS:
                        a = 0  # No future value → idle
                    else:
                        a = 2  # charge > discharge (discharge not tied)
                elif abs(idle_total - best) < EPS:
                    a = 0  # idle > discharge
                elif discharge_total is not None and abs(discharge_total - best) < EPS:
                    a = 1
                else:
                    a = 2
                act[t][l * 3 + m] = a

        nxt = cur

    # 4. Forward reconstruction using stored actions.
    #    Initial previous mode is idle (0) — no prior action to constrain.
    actions = []
    level = start_level
    mode = 0

    for t in range(total_steps):
        a = act[t][level * 3 + mode]
        if a == 0:
            actions.append("idle")
        elif a == 1:
            actions.append("discharge")
            level -= 1
        else:  # a == 2
            actions.append("charge")
            level += 1
        mode = a

    return actions
