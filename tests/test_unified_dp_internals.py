"""
Tests for the unified battery-optimiser internals.

Ports the inline ``__main__`` self-tests from the old monolithic
``unified_battery_schedule.py`` into real pytest functions.

All scenarios call the assembled module via the test assembler
(``tests._assemble_unified``), which concatenates the four pure
fragments (10_helpers, 20_dp, 30_events, 40_api) at import time.
"""

from tests._assemble_unified import UNIFIED

# ===================================================================
# Helper function self-tests
# (ported from Slice 2 self-tests in the old __main__ block)
# ===================================================================


def testrate_at():
    """rate_at returns correct price or None outside range."""
    rates = [{"start": 0, "end": 600, "price": 10.0}]
    assert UNIFIED.rate_at(rates, 0) == 10.0
    assert UNIFIED.rate_at(rates, 600) is None


def testin_window():
    """in_window returns True for inclusive start, False at exclusive end."""
    assert UNIFIED.in_window({"start": 0, "end": 300}, 0) is True
    assert UNIFIED.in_window({"start": 0, "end": 300}, 300) is False


def testbonus_at():
    """bonus_at returns bonus inside window, 0.0 outside."""
    events = [{"start": 0, "end": 300, "bonus_pence": 4.0}]
    assert UNIFIED.bonus_at(events, 0) == 4.0
    assert UNIFIED.bonus_at(events, 300) == 0.0


def test_charge_value():
    """charge_value: negative cost, zero in free session, None when unavailable."""
    import_rates = [{"start": 0, "end": 600, "price": 10.0}]
    free_sessions = [{"start": 600, "end": 1200}]
    efficiency = 0.9
    step_kwh = 0.1

    cv0 = UNIFIED.charge_value(0, import_rates, free_sessions, efficiency, step_kwh)
    expected = -(10.0 * (0.1 / 0.9))
    assert abs(cv0 - expected) < 1e-9, (
        f"charge_value at 0: {cv0} != {expected}"
    )

    cv_free = UNIFIED.charge_value(
        600, import_rates, free_sessions, efficiency, step_kwh
    )
    assert cv_free == 0.0, (
        f"charge_value at 600 (free): {cv_free} != 0.0"
    )

    cv_none = UNIFIED.charge_value(
        5000, import_rates, free_sessions, efficiency, step_kwh
    )
    assert cv_none is None, (
        f"charge_value at 5000: {cv_none} is not None"
    )


def test_discharge_value():
    """discharge_value: revenue incl bonus, None when disallowed or no export."""
    import_rates = []
    export_rates = [{"start": 0, "end": 600, "price": 20.0}]
    saving_bonus_events = [{"start": 0, "end": 300, "bonus_pence": 4.0}]
    efficiency = 0.9
    step_kwh = 0.1

    dv0 = UNIFIED.discharge_value(
        0, import_rates, export_rates, saving_bonus_events, efficiency, step_kwh, True
    )
    expected = (20.0 + 4.0) * 0.1
    assert abs(dv0 - expected) < 1e-9, (
        f"discharge_value at 0: {dv0} != {expected}"
    )

    dv300 = UNIFIED.discharge_value(
        300, import_rates, export_rates, saving_bonus_events, efficiency, step_kwh, True
    )
    expected_dv300 = 20.0 * 0.1
    assert abs(dv300 - expected_dv300) < 1e-9, (
        f"discharge_value at 300: {dv300} != {expected_dv300}"
    )

    dv_disallowed = UNIFIED.discharge_value(
        0, import_rates, export_rates, saving_bonus_events, efficiency, step_kwh, False
    )
    assert dv_disallowed is None, (
        f"discharge_value with allow_discharge=False: "
        f"{dv_disallowed} is not None"
    )

    dv_no_export = UNIFIED.discharge_value(
        5000, import_rates, export_rates, saving_bonus_events, efficiency, step_kwh, True
    )
    # With missing export rates we now conservatively return 0.0 (no profit)
    # instead of None so the DP can still evaluate charging decisions.
    assert dv_no_export == 0.0, (
        f"discharge_value at 5000: {dv_no_export} is not 0.0"
    )


def test_charge_value_threshold():
    """charge_value respects charge_price_threshold: blocks when price too high."""
    import_rates = [{"start": 0, "end": 600, "price": 10.0}]
    free_sessions = []
    efficiency = 0.9
    step_kwh = 0.1

    # Below threshold (5.0) — should charge
    cv = UNIFIED.charge_value(
        0, import_rates, free_sessions, efficiency, step_kwh,
        charge_price_threshold=15.0,
    )
    assert cv is not None, "charge_value should allow charge below threshold"

    # Above threshold (5.0) — should NOT charge
    cv_blocked = UNIFIED.charge_value(
        0, import_rates, free_sessions, efficiency, step_kwh,
        charge_price_threshold=5.0,
    )
    assert cv_blocked is None, (
        f"charge_value should block charge above threshold, got {cv_blocked}"
    )


def test_discharge_value_threshold():
    """discharge_value respects discharge_price_threshold: blocks when price too low."""
    import_rates = []
    export_rates = [{"start": 0, "end": 600, "price": 20.0}]
    saving_bonus_events = []
    efficiency = 0.9
    step_kwh = 0.1

    # Above threshold (15.0) — should discharge
    dv = UNIFIED.discharge_value(
        0, import_rates, export_rates, saving_bonus_events, efficiency, step_kwh, True,
        discharge_price_threshold=15.0,
    )
    assert dv is not None, "discharge_value should allow discharge above threshold"

    # Below threshold (25.0) — should NOT discharge
    dv_blocked = UNIFIED.discharge_value(
        0, import_rates, export_rates, saving_bonus_events, efficiency, step_kwh, True,
        discharge_price_threshold=25.0,
    )
    assert dv_blocked is None, (
        f"discharge_value should block discharge below threshold, got {dv_blocked}"
    )


# ===================================================================
# DP scenario tests — 1-minute step resolution
# (ported from Slice 3 self-tests in the old __main__ block)
# ===================================================================


def test_dp_scenario_a_tail_end_first():
    """Tail-end-first discharge within an equal-priced window (1-min steps).

    Old label: Scenario A
    step_kwh=60*(1/60)=1.0, total_steps=30, n_levels=100, start_level=15.
    """
    actions = UNIFIED.solve_dp(
        now_epoch=0,
        total_steps=30,
        n_levels=100,
        start_level=15,
        step_kwh=1.0,
        efficiency=0.9,
        import_rates=[],
        export_rates=[{"start": 0, "end": 1800, "price": 20.0}],
        free_sessions=[],
        saving_bonus_events=[],
        allow_discharge=True,
        step_minutes=1,
    )
    assert actions[:15] == ["idle"] * 15, (
        f"A: first 15 not all idle: {actions[:15]}"
    )
    assert actions[15:] == ["discharge"] * 15, (
        f"A: last 15 not all discharge: {actions[15:]}"
    )


def test_dp_scenario_b_no_discharge():
    """No discharge when disallowed (1-min steps).

    Old label: Scenario B
    """
    actions = UNIFIED.solve_dp(
        now_epoch=0,
        total_steps=30,
        n_levels=100,
        start_level=15,
        step_kwh=1.0,
        efficiency=0.9,
        import_rates=[],
        export_rates=[{"start": 0, "end": 1800, "price": 20.0}],
        free_sessions=[],
        saving_bonus_events=[],
        allow_discharge=False,
        step_minutes=1,
    )
    assert actions == ["idle"] * 30, f"B: not all idle: {actions}"


def test_dp_scenario_c_no_export():
    """Cheap import but no export opportunity -> optimal is idle.

    Old label: Scenario C
    step_kwh=1.0, total_steps=60, n_levels=10, start_level=0
    """
    actions = UNIFIED.solve_dp(
        now_epoch=0,
        total_steps=60,
        n_levels=10,
        start_level=0,
        step_kwh=1.0,
        efficiency=0.9,
        import_rates=[{"start": 0, "end": 1800, "price": 1.0}],
        export_rates=[],
        free_sessions=[],
        saving_bonus_events=[],
        allow_discharge=True,
        step_minutes=1,
    )
    assert actions == ["idle"] * 60, f"C: not all idle: {actions[:10]}..."


def test_dp_scenario_d_arbitrage():
    """Profitable arbitrage round trip (1-min steps).

    Old label: Scenario D
    step_kwh=1.0, total_steps=60, n_levels=10, start_level=0
    """
    actions = UNIFIED.solve_dp(
        now_epoch=0,
        total_steps=60,
        n_levels=10,
        start_level=0,
        step_kwh=1.0,
        efficiency=0.9,
        import_rates=[{"start": 0, "end": 1800, "price": 1.0}],
        export_rates=[{"start": 1800, "end": 3600, "price": 100.0}],
        free_sessions=[],
        saving_bonus_events=[],
        allow_discharge=True,
        step_minutes=1,
    )
    assert actions.count("charge") == 10, (
        f"D: charge count {actions.count('charge')} != 10"
    )
    assert actions.count("discharge") == 10, (
        f"D: discharge count {actions.count('discharge')} != 10"
    )
    assert actions.count("idle") == 40, (
        f"D: idle count {actions.count('idle')} != 40"
    )
    for i, a in enumerate(actions):
        if a == "charge":
            assert i < 30, f"D: charge at index {i} >= 30"
        if a == "discharge":
            assert i >= 30, f"D: discharge at index {i} < 30"
    assert UNIFIED.no_opposite_adjacency(actions), (
        "D has opposite adjacency!"
    )


# ===================================================================
# Equivalence / invariant tests
# (ported from Slice 3b self-tests in the old __main__ block)
# ===================================================================


def _check_consistent(actions, total_minutes, start_level, n_levels, label):
    """Verify action list length, bounds, and SoC invariance."""
    assert len(actions) == total_minutes, (
        f"{label}: action length {len(actions)} != {total_minutes}"
    )
    level = start_level
    for i, a in enumerate(actions):
        if a == "charge":
            level += 1
        elif a == "discharge":
            level -= 1
        assert 0 <= level <= n_levels, (
            f"{label}: level {level} out of bounds [0, {n_levels}] "
            f"at index {i}"
        )


def test_dp_scenario_e_arbitrage_invariant():
    """Arbitrage with different price ratio (invariant checks).

    Old label: Scenario E
    step_kwh=1.0, total_steps=60, n_levels=10, start_level=0
    """
    actions = UNIFIED.solve_dp(
        now_epoch=0,
        total_steps=60,
        n_levels=10,
        start_level=0,
        step_kwh=1.0,
        efficiency=0.9,
        import_rates=[{"start": 0, "end": 1800, "price": 1.0}],
        export_rates=[{"start": 1800, "end": 3600, "price": 50.0}],
        free_sessions=[],
        saving_bonus_events=[],
        allow_discharge=True,
        step_minutes=1,
    )
    _check_consistent(actions, 60, 0, 10, "E arbitrage")
    assert actions.count("charge") == 10, (
        f"E charge count {actions.count('charge')} != 10"
    )
    assert actions.count("discharge") == 10, (
        f"E discharge count {actions.count('discharge')} != 10"
    )
    assert UNIFIED.no_opposite_adjacency(actions), (
        "E has opposite adjacency!"
    )


def test_dp_scenario_f_partial_discharge():
    """Partial start, discharge only, no import available.

    Old label: Scenario F
    step_kwh=1.0, total_steps=20, n_levels=10, start_level=5
    """
    actions = UNIFIED.solve_dp(
        now_epoch=0,
        total_steps=20,
        n_levels=10,
        start_level=5,
        step_kwh=1.0,
        efficiency=0.9,
        import_rates=[],
        export_rates=[{"start": 0, "end": 1200, "price": 10.0}],
        free_sessions=[],
        saving_bonus_events=[],
        allow_discharge=True,
        step_minutes=1,
    )
    _check_consistent(actions, 20, 5, 10, "F partial discharge")
    assert actions.count("discharge") <= 5, (
        f"F discharge count {actions.count('discharge')} > 5"
    )
    assert actions.count("charge") == 0, (
        f"F charge count {actions.count('charge')} != 0"
    )


def test_dp_scenario_g_free_session_only():
    """Free session only (no import/export rates) — all idle.

    Old label: Scenario G
    step_kwh=1.0, total_steps=15, n_levels=5, start_level=0
    """
    actions = UNIFIED.solve_dp(
        now_epoch=0,
        total_steps=15,
        n_levels=5,
        start_level=0,
        step_kwh=1.0,
        efficiency=0.9,
        import_rates=[],
        export_rates=[],
        free_sessions=[{"start": 0, "end": 900}],
        saving_bonus_events=[],
        allow_discharge=False,
        step_minutes=1,
    )
    _check_consistent(actions, 15, 0, 5, "G free only")
    assert actions == ["idle"] * 15, f"G not all idle: {actions}"


def test_dp_scenario_h_saving_bonus():
    """Saving bonus with partial SoC (consistency check).

    Old label: Scenario H
    step_kwh=1.0, total_steps=25, n_levels=10, start_level=3
    """
    actions = UNIFIED.solve_dp(
        now_epoch=0,
        total_steps=25,
        n_levels=10,
        start_level=3,
        step_kwh=1.0,
        efficiency=0.9,
        import_rates=[],
        export_rates=[{"start": 0, "end": 1500, "price": 5.0}],
        free_sessions=[],
        saving_bonus_events=[{"start": 600, "end": 1200, "bonus_pence": 10.0}],
        allow_discharge=True,
        step_minutes=1,
    )
    _check_consistent(actions, 25, 3, 10, "H saving bonus")


def test_dp_scenario_i_reserve():
    """Reserve prevents full discharge.

    Old label: Scenario I
    step_kwh=1.0, total_steps=60, n_levels=8, start_level=6
    """
    actions = UNIFIED.solve_dp(
        now_epoch=0,
        total_steps=60,
        n_levels=8,
        start_level=6,
        step_kwh=1.0,
        efficiency=0.9,
        import_rates=[],
        export_rates=[{"start": 0, "end": 3600, "price": 10.0}],
        free_sessions=[],
        saving_bonus_events=[],
        allow_discharge=True,
        step_minutes=1,
    )
    _check_consistent(actions, 60, 6, 8, "I reserve")
    assert actions.count("discharge") <= 6, (
        f"I discharge count {actions.count('discharge')} > 6"
    )


def test_dp_floor_does_not_block_charging():
    """Reserve floor must constrain discharge only, never block charging.

    Regression guard: an active per-step floor (min_level_per_step) used
    to forbid charging while the floor was active, which wrongly skipped
    free-session top-ups during the reserve window.  With the floor at
    level 8 for the whole horizon and the battery starting exactly at the
    floor, a free charging session must still trigger charging (and a
    later profitable discharge), while the floor itself is never breached.

    step_kwh = 3.0 * 5/60 = 0.25; total_steps=40, n_levels=12, start=8.
    Free session at steps 10..15 (10 <= t < 16) makes import cost ~zero;
    import is expensive (0.40) elsewhere; export is a flat 0.15.
    """
    step = 5
    total_steps = 40
    n_levels = 12
    step_kwh = 3.0 * step / 60.0

    import_rates = []
    for t in range(total_steps):
        s = t * step * 60
        e = s + step * 60
        price = 0.0001 if 10 <= t < 16 else 0.40
        import_rates.append({"start": s, "end": e, "price": price})
    free_sessions = [{"start": 10 * step * 60, "end": 16 * step * 60}]
    export_rates = [{"start": 0, "end": total_steps * step * 60, "price": 0.15}]

    actions = UNIFIED.solve_dp(
        now_epoch=0,
        total_steps=total_steps,
        n_levels=n_levels,
        start_level=8,
        step_kwh=step_kwh,
        efficiency=0.9,
        import_rates=import_rates,
        export_rates=export_rates,
        free_sessions=free_sessions,
        saving_bonus_events=[],
        allow_discharge=True,
        step_minutes=step,
        min_level_per_step=[8] * total_steps,
    )

    # The free session must be used to charge (this is the regression:
    # previously zero charges happened because the floor blocked charging).
    assert actions.count("charge") > 0, (
        f"floor wrongly blocked charging: {actions}"
    )
    # Every charge must fall inside the free session window (steps 10..15).
    for i, a in enumerate(actions):
        if a == "charge":
            assert 10 <= i < 16, f"charge at step {i} outside free session"
    # The floor must never be breached: starting at level 8 (== floor),
    # the level must stay >= 8 throughout.
    level = 8
    for a in actions:
        if a == "charge":
            level += 1
        elif a == "discharge":
            level -= 1
        assert level >= 8, f"floor breached: level {level} < 8"
    # No illegal opposite-intent adjacency.
    assert UNIFIED.no_opposite_adjacency(actions), (
        f"opposite adjacency present: {actions}"
    )


# ===================================================================
# 5-minute step resolution tests
# (ported from Slice 3c self-tests in the old __main__ block)
# ===================================================================


def test_dp_scenario_s1_tail_end_first_5min():
    """Discharge at 5-min resolution, tail-end-first.

    Old label: Scenario S1
    6 steps, step_kwh=60*(5/60)=5.0, n_levels=20, start_level=3
    """
    actions = UNIFIED.solve_dp(
        now_epoch=0,
        total_steps=6,
        n_levels=20,
        start_level=3,
        step_kwh=5.0,
        efficiency=0.9,
        import_rates=[],
        export_rates=[{"start": 0, "end": 1800, "price": 20.0}],
        free_sessions=[],
        saving_bonus_events=[],
        allow_discharge=True,
        step_minutes=5,
    )
    assert actions[:3] == ["idle", "idle", "idle"], (
        f"S1: first 3 not all idle: {actions[:3]}"
    )
    assert actions[3:] == ["discharge", "discharge", "discharge"], (
        f"S1: last 3 not all discharge: {actions[3:]}"
    )
    assert UNIFIED.no_opposite_adjacency(actions), (
        "S1 has opposite adjacency!"
    )


def test_dp_scenario_s2_arbitrage_5min():
    """Arbitrage at 5-min resolution, buffer-aware.

    Old label: Scenario S2
    12 steps (60 min / 5 min), step_kwh=5.0, n_levels=10, start_level=0
    """
    actions = UNIFIED.solve_dp(
        now_epoch=0,
        total_steps=12,
        n_levels=10,
        start_level=0,
        step_kwh=5.0,
        efficiency=0.9,
        import_rates=[{"start": 0, "end": 1800, "price": 1.0}],
        export_rates=[{"start": 1800, "end": 3600, "price": 100.0}],
        free_sessions=[],
        saving_bonus_events=[],
        allow_discharge=True,
        step_minutes=5,
    )
    assert actions.count("charge") == 5, (
        f"S2: charge count {actions.count('charge')} != 5"
    )
    assert actions.count("discharge") == 5, (
        f"S2: discharge count {actions.count('discharge')} != 5"
    )
    assert actions.count("idle") == 2, (
        f"S2: idle count {actions.count('idle')} != 2"
    )
    for i, a in enumerate(actions):
        if a == "charge":
            assert i < 6, f"S2: charge at index {i} >= 6"
        if a == "discharge":
            assert i >= 6, f"S2: discharge at index {i} < 6"
    assert UNIFIED.no_opposite_adjacency(actions), (
        "S2 has opposite adjacency!"
    )


# ===================================================================
# Buffer self-tests
# (ported from Slice 3d self-tests in the old __main__ block)
# ===================================================================


def test_buffer_b1_natural_gap():
    """Forced buffer between charge and discharge (natural gap).

    Old label: Scenario B1
    3 steps, step_kwh=5.0, n_levels=20, start_level=0
    """
    actions = UNIFIED.solve_dp(
        now_epoch=0,
        total_steps=3,
        n_levels=20,
        start_level=0,
        step_kwh=5.0,
        efficiency=0.9,
        import_rates=[{"start": 0, "end": 300, "price": 1.0}],
        export_rates=[{"start": 600, "end": 900, "price": 100.0}],
        free_sessions=[],
        saving_bonus_events=[],
        allow_discharge=True,
        step_minutes=5,
    )
    assert actions == ["charge", "idle", "discharge"], (
        f"B1: unexpected actions {actions}"
    )
    assert UNIFIED.no_opposite_adjacency(actions), (
        "B1 has opposite adjacency!"
    )


def test_buffer_b2_blocked_adjacency():
    """Adjacency blocked: charge and discharge available simultaneously.

    Old label: Scenario B2
    2 steps, step_kwh=5.0, n_levels=20, start_level=1
    """
    actions = UNIFIED.solve_dp(
        now_epoch=0,
        total_steps=2,
        n_levels=20,
        start_level=1,
        step_kwh=5.0,
        efficiency=0.9,
        import_rates=[{"start": 0, "end": 300, "price": 1.0}],
        export_rates=[{"start": 0, "end": 600, "price": 100.0}],
        free_sessions=[],
        saving_bonus_events=[],
        allow_discharge=True,
        step_minutes=5,
    )
    assert UNIFIED.no_opposite_adjacency(actions), (
        f"B2 has opposite adjacency: {actions}"
    )


# ===================================================================
# Event-conversion tests
# (ported from Slice 4 self-tests in the old __main__ block)
# ===================================================================


def test_events_o1_single_discharge_block():
    """Single discharge block with price + saving bonus, via end-to-end API.

    Old label: Scenario O1
    Calls compute_unified_schedule with epoch_to_iso=None (default).
    """
    events = UNIFIED.compute_unified_schedule(
        now_epoch=0,
        horizon_end_epoch=1800,
        import_rates=[],
        export_rates=[{"start": 0, "end": 1800, "price": 20.0}],
        free_sessions=[],
        saving_window=None,
        saving_bonus_events=[{"start": 0, "end": 1800, "bonus_pence": 4.0}],
        available_kwh=15.0,
        capacity_kwh=100.0,
        reserve_kwh=0.0,
        power_rate_kw=60.0,
        efficiency=0.9,
        allow_discharge=True,
        minimum_slot_length=0,
        step_minutes=5,
        add_minutes=None,
    )
    # Tail-end-first: start_level=3 => steps 0-2 idle, steps 3-5 discharge
    # block start epoch = 0 + 3*300 = 900, block end = 0 + 6*300 = 1800
    assert len(events) == 1, f"O1: expected 1 event, got {len(events)}"
    e = events[0]
    assert e["intent"] == "Discharge", (
        f"O1: intent {e['intent']} != 'Discharge'"
    )
    assert e["start"] == 900, f"O1: start {e['start']} != 900"
    assert e["end"] == 1800, f"O1: end {e['end']} != 1800"
    assert e.get("export_price") == round(20.0 + 4.0, 4), (
        f"O1: export_price {e.get('export_price')} != {round(20.0 + 4.0, 4)}"
    )
    assert "import_price" not in e, (
        "O1: import_price should not be present"
    )


def test_events_o2_charge_with_free_session():
    """Charge block with free session zeroing price, via actions_to_events.

    Old label: Scenario O2
    Uses actions_to_events directly with a hand-crafted actions list.
    """
    actions = ["charge", "charge", "charge", "charge", "idle", "idle"]
    events = UNIFIED.actions_to_events(
        actions,
        now_epoch=0,
        step_minutes=5,
        import_rates=[{"start": 0, "end": 1800, "price": 10.0}],
        export_rates=[],
        free_sessions=[{"start": 600, "end": 1200}],
        saving_bonus_events=[],
        epoch_to_iso=lambda e: "ISO(" + str(e) + ")",
    )
    assert len(events) == 1, f"O2: expected 1 event, got {len(events)}"
    e2 = events[0]
    assert e2["intent"] == "Charge", (
        f"O2: intent {e2['intent']} != 'Charge'"
    )
    assert e2["start"] == "ISO(0)", (
        f"O2: start {e2['start']} != 'ISO(0)'"
    )
    assert e2["end"] == "ISO(1200)", (
        f"O2: end {e2['end']} != 'ISO(1200)'"
    )
    # Steps 0,1 at 10.0; steps 2,3 free=0.0 => avg = (10+10+0+0)/4 = 5.0
    assert e2.get("import_price") == 5.0, (
        f"O2: import_price {e2.get('import_price')} != 5.0"
    )
    assert "export_price" not in e2, (
        "O2: export_price should not be present"
    )


def test_events_o3_idle_gap_splits_blocks():
    """Idle gap splits two discharge blocks, via actions_to_events.

    Old label: Scenario O3
    """
    actions = ["discharge", "idle", "discharge"]
    events = UNIFIED.actions_to_events(
        actions,
        now_epoch=0,
        step_minutes=5,
        import_rates=[],
        export_rates=[{"start": 0, "end": 900, "price": 7.0}],
        free_sessions=[],
        saving_bonus_events=[],
        epoch_to_iso=None,
    )
    assert len(events) == 2, f"O3: expected 2 events, got {len(events)}"
    e3a, e3b = events
    assert e3a["intent"] == "Discharge", (
        f"O3: first intent {e3a['intent']}"
    )
    assert e3a["start"] == 0, f"O3: first start {e3a['start']} != 0"
    assert e3a["end"] == 300, f"O3: first end {e3a['end']} != 300"
    assert e3a.get("export_price") == 7.0, (
        f"O3: first price {e3a.get('export_price')}"
    )
    assert e3b["intent"] == "Discharge", (
        f"O3: second intent {e3b['intent']}"
    )
    assert e3b["start"] == 600, f"O3: second start {e3b['start']} != 600"
    assert e3b["end"] == 900, f"O3: second end {e3b['end']} != 900"
    assert e3b.get("export_price") == 7.0, (
        f"O3: second price {e3b.get('export_price')}"
    )


# ===================================================================
# Smoke test (not in old __main__, ensures full pipeline works at size)
# ===================================================================


def test_compute_unified_schedule_smoke():
    """2-day realistic horizon via end-to-end API: assert returns a list."""
    now = 0
    horizon = 2 * 86400
    total_minutes = int((horizon - now) // 60)
    import_rates = []
    export_rates = []
    for i in range(total_minutes // 30):
        start = i * 30 * 60
        end = start + 30 * 60
        import_rates.append({
            "start": start, "end": end,
            "price": 1.0 if i % 2 == 0 else 30.0,
        })
        export_rates.append({
            "start": start, "end": end,
            "price": 5.0 if i % 2 == 0 else 25.0,
        })

    events = UNIFIED.compute_unified_schedule(
        now_epoch=now,
        horizon_end_epoch=horizon,
        import_rates=import_rates,
        export_rates=export_rates,
        free_sessions=[],
        saving_window=None,
        saving_bonus_events=[],
        available_kwh=6.75,
        capacity_kwh=13.5,
        reserve_kwh=0.0,
        power_rate_kw=9.6,
        efficiency=0.9,
        allow_discharge=True,
        minimum_slot_length=0,
        step_minutes=5,
    )
    assert isinstance(events, list), (
        f"Expected list, got {type(events)}"
    )


def test_compute_load_floor_tapers():
    """Tapering floor: reserves only the remaining hours of load per step.

    Regression: compute_load_floor used to produce a flat floor
    (same reserve for the entire pre-charge window).  It now tapers
    so the floor is highest at the start and drops to 0 at the charge
    step, letting the battery discharge more surplus near the charge
    while still protecting house load.
    """
    step = 5
    total_steps = 24
    next_charge_step = 12
    n_levels = 20
    idle_power_kw = 1.0
    lower_discharge_limit_kwh = 0.5
    step_kwh = 3.0 * step / 60.0  # 0.25

    floor = UNIFIED.compute_load_floor(
        total_steps,
        next_charge_step,
        n_levels,
        step,
        idle_power_kw,
        lower_discharge_limit_kwh,
        step_kwh,
        now_epoch=0,
        import_rates=[],
        export_rates=[],
        saving_bonus_events=[],
        efficiency=1.0,
    )

    # Step 0: must survive full 12 steps = 60 min = 1.0 h
    # required = 1.0 * 1.0 + 0.5 = 1.5 kWh -> 1.5 / 0.25 = 6 levels
    assert floor[0] == 6, f"floor[0] {floor[0]} != 6"
    # Step 11: must survive 1 step = 5 min = 1/12 h
    # required = 1.0 * (1/12) + 0.5 = 0.5833 kWh -> ceil(0.5833 / 0.25) = 3
    assert floor[11] == 3, f"floor[11] {floor[11]} != 3"
    # From step 12 onward: no reserve (charge replenishes)
    assert floor[12] == 0, f"floor[12] {floor[12]} != 0"
    assert floor[23] == 0, f"floor[23] {floor[23]} != 0"

    # Non-increasing across the pre-charge window
    for i in range(1, next_charge_step):
        assert floor[i] <= floor[i - 1], (
            f"floor increases at {i}: {floor[i]} > {floor[i - 1]}"
        )

    # All entries in [0, n_levels]
    for i, f in enumerate(floor):
        assert 0 <= f <= n_levels, (
            f"floor[{i}] {f} out of bounds [0, {n_levels}]"
        )

    # Full expected list
    expected = [6, 6, 6, 5, 5, 5, 4, 4, 4, 3, 3, 3] + [0] * 12
    assert floor == expected, f"floor {floor} != expected {expected}"


def test_compute_load_floor_reduces_when_export_beats_import():
    """When export + bonus > breakeven, floor drops to soft buffer only."""
    step = 5
    total_steps = 12
    next_charge_step = 6
    n_levels = 20
    idle_power_kw = 0.75
    lower_discharge_limit_kwh = 0.5
    step_kwh = 0.25
    now_epoch = 0
    efficiency = 0.9

    import_rates = [
        {"start": 0, "end": 1800, "price": 0.292},
        {"start": 1800, "end": 3600, "price": 0.04},
    ]
    export_rates = [
        {"start": 0, "end": 1800, "price": 0.24},
        {"start": 1800, "end": 3600, "price": 0.161},
    ]
    saving_bonus_events = [
        {"start": 0, "end": 1800, "bonus_pence": 0.135},
    ]

    floor = UNIFIED.compute_load_floor(
        total_steps,
        next_charge_step,
        n_levels,
        step,
        idle_power_kw,
        lower_discharge_limit_kwh,
        step_kwh,
        now_epoch=now_epoch,
        import_rates=import_rates,
        export_rates=export_rates,
        saving_bonus_events=saving_bonus_events,
        efficiency=efficiency,
    )

    # Steps 0-5: effective_export = 0.24 + 0.135 = 0.375,
    #   max_import = 0.292 (all steps in [0, 1800)),
    #   charge_price = 0.04, breakeven = 0.292 + 0.04/0.9 = 0.3364...
    #   Since 0.375 > 0.3364, floor should be soft buffer only
    #   = ceil(0.5 / 0.25) = 2 levels.
    expected_soft_buffer = 2
    for t in range(6):
        assert floor[t] == expected_soft_buffer, (
            f"floor[{t}] {floor[t]} != {expected_soft_buffer}"
        )

    # Steps 6-11: after charge, floor = 0.
    for t in range(6, 12):
        assert floor[t] == 0, f"floor[{t}] {floor[t]} != 0"

    # All entries in [0, n_levels]
    for i, f in enumerate(floor):
        assert 0 <= f <= n_levels, (
            f"floor[{i}] {f} out of bounds [0, {n_levels}]"
        )

    expected = [2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0]
    assert floor == expected, f"floor {floor} != expected {expected}"


def test_compute_load_floor_keeps_when_export_below_breakeven():
    """When export < breakeven, floor uses original tapering logic."""
    step = 5
    total_steps = 12
    next_charge_step = 6
    n_levels = 20
    idle_power_kw = 0.75
    lower_discharge_limit_kwh = 0.5
    step_kwh = 0.25
    now_epoch = 0
    efficiency = 0.9

    import_rates = [
        {"start": 0, "end": 1800, "price": 0.292},
        {"start": 1800, "end": 3600, "price": 0.04},
    ]
    # No bonus this time — export = 0.24 < breakeven = 0.3364...
    export_rates = [
        {"start": 0, "end": 1800, "price": 0.24},
        {"start": 1800, "end": 3600, "price": 0.161},
    ]
    saving_bonus_events = []

    floor = UNIFIED.compute_load_floor(
        total_steps,
        next_charge_step,
        n_levels,
        step,
        idle_power_kw,
        lower_discharge_limit_kwh,
        step_kwh,
        now_epoch=now_epoch,
        import_rates=import_rates,
        export_rates=export_rates,
        saving_bonus_events=saving_bonus_events,
        efficiency=efficiency,
    )

    # Original tapering with idle_power_kw=0.75, step_kwh=0.25:
    # Step 0: remaining 6 steps = 30 min = 0.5 h
    #   required = 0.75 * 0.5 + 0.5 = 0.875 -> ceil(0.875/0.25)=4
    assert floor[0] == 4, f"floor[0] {floor[0]} != 4"
    # Step 1: remaining 5 steps = 25 min = 25/60 h
    #   required = 0.75*25/60 + 0.5 = 0.8125 -> ceil(0.8125/0.25)=4
    assert floor[1] == 4, f"floor[1] {floor[1]} != 4"
    # Step 2: remaining 4 steps = 20 min = 20/60 h
    #   required = 0.75*20/60 + 0.5 = 0.75 -> ceil(0.75/0.25)=3
    assert floor[2] == 3, f"floor[2] {floor[2]} != 3"
    # Step 3: remaining 3 steps = 15 min = 15/60 h
    #   required = 0.75*15/60 + 0.5 = 0.6875 -> ceil(0.6875/0.25)=3
    assert floor[3] == 3, f"floor[3] {floor[3]} != 3"
    # Step 4: remaining 2 steps = 10 min = 10/60 h
    #   required = 0.75*10/60 + 0.5 = 0.625 -> ceil(0.625/0.25)=3
    assert floor[4] == 3, f"floor[4] {floor[4]} != 3"
    # Step 5: remaining 1 step = 5 min = 5/60 h
    #   required = 0.75*5/60 + 0.5 = 0.5625 -> ceil(0.5625/0.25)=3
    assert floor[5] == 3, f"floor[5] {floor[5]} != 3"
    # Steps 6-11: after charge, floor = 0
    for t in range(6, 12):
        assert floor[t] == 0, f"floor[{t}] {floor[t]} != 0"

    # All entries in [0, n_levels]
    for i, f in enumerate(floor):
        assert 0 <= f <= n_levels, (
            f"floor[{i}] {f} out of bounds [0, {n_levels}]"
        )

    expected = [4, 4, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0]
    assert floor == expected, f"floor {floor} != expected {expected}"
