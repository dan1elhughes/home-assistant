# Fragment 30_events — action-to-event conversion (concatenated at build; do not add imports)

# --- Slice 4: convert actions to events ---


def actions_to_events(
    actions,
    now_epoch,
    step_minutes,
    import_rates,
    export_rates,
    free_sessions,
    saving_bonus_events,
    epoch_to_iso,
):
    """Convert DP per-step action strings into merged event dicts.

    Groups maximal runs of the same non-idle intent into blocks, computes
    time-weighted average prices for each block, and serialises times.

    Parameters
    ----------
    epoch_to_iso : callable or None
        If None (self-test mode), emit raw epoch integers instead of ISO
        strings so the function is testable without a formatter.

    Returns
    -------
    list[dict]
        Each dict: {"start": ..., "end": ..., "intent": "Charge"|"Discharge",
                     "import_price"? ..., "export_price"? ...}
    """
    step_seconds = step_minutes * 60
    raw_events = []  # (numeric_start_epoch, event_dict) for defensive sort
    i = 0
    n = len(actions)

    while i < n:
        if actions[i] == "idle":
            i += 1
            continue

        # Start of a maximal block of the same non-idle intent
        intent = actions[i]
        block_start = i
        while i < n and actions[i] == intent:
            i += 1
        block_end = i

        block_start_epoch = now_epoch + block_start * step_seconds
        block_end_epoch = now_epoch + block_end * step_seconds

        # Compute time-weighted average representative price
        prices = []
        for t in range(block_start, block_end):
            step_epoch = now_epoch + t * step_seconds
            if intent == "charge":
                if in_any_window(free_sessions, step_epoch):
                    step_price = 0.0
                else:
                    step_price = rate_at(import_rates, step_epoch)
            else:  # discharge
                export_price = rate_at(export_rates, step_epoch)
                if export_price is None:
                    step_price = None
                else:
                    step_price = export_price + bonus_at(
                        saving_bonus_events, step_epoch
                    )

            if step_price is not None:
                prices.append(step_price)

        if prices:
            price = round(sum(prices) / len(prices), 4)
        else:
            price = None

        # Serialise times
        if epoch_to_iso is not None:
            start = epoch_to_iso(block_start_epoch)
            end = epoch_to_iso(block_end_epoch)
        else:
            # Self-test mode: emit raw epochs for testability without a formatter
            start = block_start_epoch
            end = block_end_epoch

        # Map intent string to output vocabulary
        mapped_intent = "Charge" if intent == "charge" else "Discharge"

        event = {"start": start, "end": end, "intent": mapped_intent}
        if price is not None:
            if intent == "charge":
                event["import_price"] = price
            else:
                event["export_price"] = price

        raw_events.append((block_start_epoch, event))

    # Defensive sort by block start epoch (internal numeric value)
    raw_events.sort(key=lambda x: x[0])
    return [e for _, e in raw_events]
