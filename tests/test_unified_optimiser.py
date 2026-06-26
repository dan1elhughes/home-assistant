"""
Tests for the unified battery optimiser PURE function
``compute_unified_schedule``.

These tests exercise the DP core, the saving-bonus prioritisation, the
reserve bound, the allow_discharge gate, free-session zero pricing, and
basic arbitrage — all at epoch level so no ISO formatter is needed.
"""

from tests._assemble_unified import UNIFIED

compute_unified_schedule = UNIFIED.compute_unified_schedule

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE = 1_700_000_000  # arbitrary epoch — all scenario times use offsets


def m(mins):
    """Return epoch of *mins* minutes after BASE."""
    return BASE + mins * 60


def assert_events_equal(actual, expected):
    """Check events match on intent, start, end (prices ignored unless
    present in expected).  Uses plain asserts (pytest style)."""
    assert len(actual) == len(expected), (
        f"Event count mismatch: got {len(actual)}, expected {len(expected)}\n"
        f"  actual:   {actual}\n"
        f"  expected: {expected}"
    )
    for i, exp in enumerate(expected):
        act = actual[i]
        assert act["intent"] == exp["intent"], (
            f"Event[{i}] intent: {act['intent']} != {exp['intent']}"
        )
        assert act["start"] == exp["start"], (
            f"Event[{i}] start: {act['start']} != {exp['start']}"
        )
        assert act["end"] == exp["end"], (
            f"Event[{i}] end: {act['end']} != {exp['end']}"
        )


# ===================================================================
# Tests
# ===================================================================


def test_empty_inputs_returns_empty():
    """No rates, no sessions, no available energy → no events."""
    events = compute_unified_schedule(
        now_epoch=BASE,
        horizon_end_epoch=BASE + 86400,
        import_rates=[],
        export_rates=[],
        free_sessions=[],
        saving_window=None,
        saving_bonus_events=[],
        available_kwh=0,
        capacity_kwh=10,
        reserve_kwh=0,
        power_rate_kw=9.6,
        efficiency=0.9,
        allow_discharge=True,
        minimum_slot_length=5,
        step_minutes=5,
    )
    assert events == [], f"Expected [], got {events}"


def test_saving_bonus_prioritised_over_higher_export():
    """
    With 30 kWh available and a saving session that bumps a low export
    price (5p) to 77p/kWh, the DP must fill the saving window rather
    than a standalone 30p export window elsewhere.
    """
    # Two export windows: one high-priced (0.30) at m(300)-m(330),
    # one low-priced (0.05) at m(420)-m(450) with a 0.72 saving bonus
    # (in £/kWh — the HA wrapper converts octopoints before calling).
    # The saving window makes m(420)-m(450) worth 0.05+0.72=0.77/kWh,
    # which beats 0.30.
    events = compute_unified_schedule(
        now_epoch=BASE,
        horizon_end_epoch=BASE + 86400,
        import_rates=[],
        export_rates=[
            {"start": m(300), "end": m(330), "price": 0.30},
            {"start": m(420), "end": m(450), "price": 0.05},
        ],
        free_sessions=[],
        saving_window={"start": m(420), "end": m(450)},
        # bonus_pence is already in £/kWh (the HA wrapper converts
        # octopoints / 8 / 100 before calling).  Here 0.72 = £0.72/kWh.
        saving_bonus_events=[
            {"start": m(420), "end": m(450), "bonus_pence": 0.72},
        ],
        available_kwh=30,
        capacity_kwh=1000,
        reserve_kwh=0,
        power_rate_kw=60,  # step_kwh = 60 * 5/60 = 5.0
        efficiency=0.9,
        allow_discharge=True,
        minimum_slot_length=5,
        step_minutes=5,
    )

    assert_events_equal(events, [
        {"intent": "Discharge", "start": m(420), "end": m(450)},
    ])


def test_reserve_bounds_discharge_tail_end_first():
    """
    With available_kwh=30, reserve_kwh=15, only 15 kWh (3 steps at
    5 kWh/step) are usable.  The DP must fill the saving window
    tail-end-first so only the LAST 15 minutes are dispatched.
    """
    events = compute_unified_schedule(
        now_epoch=BASE,
        horizon_end_epoch=BASE + 86400,
        import_rates=[],
        export_rates=[
            {"start": m(420), "end": m(450), "price": 0.05},
        ],
        free_sessions=[],
        saving_window={"start": m(420), "end": m(450)},
        saving_bonus_events=[
            {"start": m(420), "end": m(450), "bonus_pence": 0.72},
        ],
        available_kwh=30,
        capacity_kwh=1000,
        reserve_kwh=15,  # usable = 30 - 15 = 15 kWh => 3 steps
        power_rate_kw=60,  # step_kwh = 5.0
        efficiency=0.9,
        allow_discharge=True,
        minimum_slot_length=5,
        step_minutes=5,
    )

    # Tail-end-first: last 15 min of the 30-min window
    assert_events_equal(events, [
        {"intent": "Discharge", "start": m(435), "end": m(450)},
    ])


def test_allow_discharge_false_blocks_discharge():
    """
    Identical scenario to test_saving_bonus_prioritised_over_higher_export
    but with allow_discharge=False → no discharge events at all.
    """
    events = compute_unified_schedule(
        now_epoch=BASE,
        horizon_end_epoch=BASE + 86400,
        import_rates=[],
        export_rates=[
            {"start": m(300), "end": m(330), "price": 0.30},
            {"start": m(420), "end": m(450), "price": 0.05},
        ],
        free_sessions=[],
        saving_window={"start": m(420), "end": m(450)},
        saving_bonus_events=[
            {"start": m(420), "end": m(450), "bonus_pence": 0.72},
        ],
        available_kwh=30,
        capacity_kwh=1000,
        reserve_kwh=0,
        power_rate_kw=60,
        efficiency=0.9,
        allow_discharge=False,  # <-- key difference
        minimum_slot_length=5,
        step_minutes=5,
    )

    assert events == [], f"Expected [], got {events}"


def test_arbitrage_charges_then_discharges_with_buffer():
    """
    Profitable round trip: cheap import (1p) early, valuable export (100p)
    later, with a natural gap in between.  The DP should charge during the
    cheap window and discharge during the export window, and the
    charge/discharge events must not overlap or be adjacent (the gap
    provides the inverter mode-switch buffer).

    step_kwh = 60 * 5/60 = 5.0,  n_levels = 30/5 = 6,  start_level = 0.
    """
    events = compute_unified_schedule(
        now_epoch=BASE,
        horizon_end_epoch=BASE + 86400,
        import_rates=[
            {"start": m(0), "end": m(60), "price": 0.01},
        ],
        export_rates=[
            {"start": m(120), "end": m(180), "price": 1.00},
        ],
        free_sessions=[],
        saving_window=None,
        saving_bonus_events=[],
        available_kwh=0,
        capacity_kwh=30,
        reserve_kwh=0,
        power_rate_kw=60,  # step_kwh = 5.0
        efficiency=0.9,
        allow_discharge=True,
        minimum_slot_length=5,
        step_minutes=5,
    )

    assert len(events) >= 2, (
        f"Expected at least 2 events, got {len(events)}: {events}"
    )

    # Find charge and discharge events
    charge_events = [e for e in events if e["intent"] == "Charge"]
    discharge_events = [e for e in events if e["intent"] == "Discharge"]

    assert len(charge_events) >= 1, f"No Charge event found: {events}"
    assert len(discharge_events) >= 1, f"No Discharge event found: {events}"

    for e in charge_events:
        assert m(0) <= e["start"] < m(60), (
            f"Charge.start {e['start']} not within [m(0), m(60))"
        )
        assert e["start"] < e["end"] <= m(60), (
            f"Charge block [{e['start']}, {e['end']}) not within [m(0), m(60)]"
        )

    for e in discharge_events:
        assert m(120) <= e["start"] < m(180), (
            f"Discharge.start {e['start']} not within [m(120), m(180))"
        )
        assert e["start"] < e["end"] <= m(180), (
            f"Discharge block [{e['start']}, {e['end']}) not within "
            f"[m(120), m(180)]"
        )

    # All charge blocks end before any discharge block starts
    last_charge_end = max(e["end"] for e in charge_events)
    first_discharge_start = min(e["start"] for e in discharge_events)
    assert last_charge_end <= first_discharge_start, (
        f"Charge ends at {last_charge_end} but discharge starts at "
        f"{first_discharge_start} (overlap or adjacency)"
    )


def test_free_session_charges_at_zero_price():
    """
    A free session (no-cost import) overrides an otherwise expensive
    import rate.  The resulting Charge event must carry import_price=0.0.
    """
    events = compute_unified_schedule(
        now_epoch=BASE,
        horizon_end_epoch=BASE + 86400,
        import_rates=[
            {"start": m(0), "end": m(60), "price": 0.50},  # expensive
        ],
        export_rates=[
            {"start": m(120), "end": m(180), "price": 1.00},
        ],
        free_sessions=[
            {"start": m(0), "end": m(60)},  # free overrides the 0.50
        ],
        saving_window=None,
        saving_bonus_events=[],
        available_kwh=0,
        capacity_kwh=30,
        reserve_kwh=0,
        power_rate_kw=60,  # step_kwh = 5.0
        efficiency=0.9,
        allow_discharge=True,
        minimum_slot_length=5,
        step_minutes=5,
    )

    # Find a Charge event within the free window with import_price 0.0
    charge_events = [e for e in events if e["intent"] == "Charge"]
    assert len(charge_events) >= 1, f"No Charge event found: {events}"

    free_charge = None
    for e in charge_events:
        # The charge block must be within or at least overlap the free window
        if e["start"] >= m(0) and e["end"] <= m(60):
            free_charge = e
            break

    assert free_charge is not None, (
        f"No Charge event fully within free window [m(0), m(60)]: "
        f"{charge_events}"
    )
    assert free_charge.get("import_price") == 0.0, (
        f"Expected import_price 0.0 for free-session charge, "
        f"got {free_charge.get('import_price')}"
    )

    # Also verify a discharge event exists
    discharge_events = [e for e in events if e["intent"] == "Discharge"]
    assert len(discharge_events) >= 1, f"No Discharge event found: {events}"


def test_min_slot_via_step_size():
    """
    Verify that every emitted event spans at least step_minutes.
    Uses the scenario from test_saving_bonus_prioritised_over_higher_export.
    """
    events = compute_unified_schedule(
        now_epoch=BASE,
        horizon_end_epoch=BASE + 86400,
        import_rates=[],
        export_rates=[
            {"start": m(300), "end": m(330), "price": 0.30},
            {"start": m(420), "end": m(450), "price": 0.05},
        ],
        free_sessions=[],
        saving_window={"start": m(420), "end": m(450)},
        saving_bonus_events=[
            {"start": m(420), "end": m(450), "bonus_pence": 0.72},
        ],
        available_kwh=30,
        capacity_kwh=1000,
        reserve_kwh=0,
        power_rate_kw=60,
        efficiency=0.9,
        allow_discharge=True,
        minimum_slot_length=5,
        step_minutes=5,
    )

    for e in events:
        duration = e["end"] - e["start"]
        assert duration >= 5 * 60, (
            f"Event {e['intent']} [{e['start']}, {e['end']}) "
            f"is only {duration}s (< {5*60}s = 5 min)"
        )


def test_charge_front_first_discharge_tail_end():
    """
    Charge fills from start of cheap window; discharge from end of export.

    Free session (40 min = 8 steps at 5 min) is longer than the 6 charge
    steps needed to fill the battery.  With front-first tie-breaking the
    charge block should occupy the first 30 min (m(0) → m(30)).

    Export window (40 min = 8 steps) is longer than the 6 discharge steps
    needed.  With tail-end-first tie-breaking the discharge block should
    occupy the last 30 min (m(90) → m(120)).

    step_kwh = 60 * 5/60 = 5.0,  capacity = 30 → n_levels = 6, start = 0.
    """
    events = compute_unified_schedule(
        now_epoch=BASE,
        horizon_end_epoch=BASE + 86400,
        import_rates=[],
        export_rates=[
            {"start": m(80), "end": m(120), "price": 0.50},
        ],
        free_sessions=[
            {"start": m(0), "end": m(40)},
        ],
        saving_window=None,
        saving_bonus_events=[],
        available_kwh=0,
        capacity_kwh=30,
        reserve_kwh=0,
        power_rate_kw=60,   # step_kwh = 5.0
        efficiency=0.9,
        allow_discharge=True,
        minimum_slot_length=0,
        step_minutes=5,
    )

    charge_blocks = [e for e in events if e["intent"] == "Charge"]
    discharge_blocks = [e for e in events if e["intent"] == "Discharge"]

    assert len(charge_blocks) >= 1, f"No Charge events: {events}"
    assert len(discharge_blocks) >= 1, f"No Discharge events: {events}"

    # Charge starts at the start of the free-session window
    first = charge_blocks[0]
    assert first["start"] == m(0), (
        f"Expected charge to start at m(0), got {first['start']}"
    )

    # Discharge ends at the end of the export window
    last = discharge_blocks[-1]
    assert last["end"] == m(120), (
        f"Expected discharge to end at m(120), got {last['end']}"
    )

    # Discharge also starts at m(90) (last 30 min of a 40 min export window)
    assert last["start"] == m(90), (
        f"Expected discharge to start at m(90), got {last['start']}"
    )


def test_price_threshold_extends_charge_block():
    """
    When charge_price_threshold is set and a charge block starts during
    a below-threshold price window, the block is extended to the end of
    the continuous cheap window.  This prevents step-by-step re-evaluation
    oscillation at near-100% SoC.

    Scenario: cheap import (0.05, below 0.10 threshold) for 60 min, then
    expensive (0.30, above threshold).  Battery empty → DP would charge 6
    steps (30 kWh) which fits in the cheap window.  The charge block must
    cover the FULL cheap window [m(0), m(60)], not stop after step 1.
    """
    import_rates = [
        {"start": m(0),  "end": m(60),  "price": 0.05},   # below threshold
        {"start": m(60), "end": m(120), "price": 0.30},  # above threshold
    ]
    events = compute_unified_schedule(
        now_epoch=BASE,
        horizon_end_epoch=BASE + 86400,
        import_rates=import_rates,
        export_rates=[],
        free_sessions=[],
        saving_window=None,
        saving_bonus_events=[],
        available_kwh=0,
        capacity_kwh=30,
        reserve_kwh=0,
        power_rate_kw=60,
        efficiency=0.9,
        allow_discharge=True,
        minimum_slot_length=5,
        step_minutes=5,
        charge_price_threshold=0.10,
    )

    charge_events = [e for e in events if e["intent"] == "Charge"]
    assert len(charge_events) >= 1, f"No Charge event found: {events}"

    # The charge block should span the entire cheap window [m(0), m(60)],
    # not stop at the first DP step.
    cheap_blocks = [
        e for e in charge_events
        if e["start"] == m(0) and e["end"] == m(60)
    ]
    assert len(cheap_blocks) >= 1, (
        f"No Charge event exactly covering cheap window [m(0), m(60)]: "
        f"{charge_events}"
    )


def test_no_extension_when_price_above_threshold():
    """
    When the import price is above charge_price_threshold throughout,
    no charge events are scheduled at all (charge_value returns None).
    """
    import_rates = [
        {"start": m(0),  "end": m(60),  "price": 0.30},  # above threshold
        {"start": m(60), "end": m(120), "price": 0.30},
    ]
    events = compute_unified_schedule(
        now_epoch=BASE,
        horizon_end_epoch=BASE + 86400,
        import_rates=import_rates,
        export_rates=[],
        free_sessions=[],
        saving_window=None,
        saving_bonus_events=[],
        available_kwh=0,
        capacity_kwh=30,
        reserve_kwh=0,
        power_rate_kw=60,
        efficiency=0.9,
        allow_discharge=True,
        minimum_slot_length=5,
        step_minutes=5,
        charge_price_threshold=0.10,
    )

    charge_events = [e for e in events if e["intent"] == "Charge"]
    # With price above threshold throughout, no charge should be scheduled.
    assert charge_events == [], f"Expected no charge events above threshold: {events}"
