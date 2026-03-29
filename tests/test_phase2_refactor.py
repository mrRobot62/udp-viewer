from __future__ import annotations

from collections import deque

from udp_log_viewer.replay_simulation import (
    TextSimulationState,
    build_temperature_replay_sample,
    build_text_replay_sample,
    drain_replay_batch,
    next_client_logic_simulation_line,
    next_text_simulation_line,
)
from udp_log_viewer.rule_slots import (
    PatternSlot,
    build_highlight_rules,
    compile_slot_patterns,
    find_first_free_slot,
    match_exclude_slots,
    match_include_slots,
    slots_from_json,
    slots_to_json,
)


def test_rule_slot_json_roundtrip_and_matching() -> None:
    slots = [
        PatternSlot(pattern="[OVEN/INFO];[T11]", mode="Substring", color="Red"),
        PatternSlot(pattern="ERROR", mode="Substring", color="None"),
    ]

    raw = slots_to_json(slots)
    loaded = slots_from_json(raw, 5)
    compiled = compile_slot_patterns(loaded[:1])

    assert loaded[0].pattern == "[OVEN/INFO];[T11]"
    assert match_include_slots("[OVEN/INFO] [T11] ready", compiled) is True
    assert find_first_free_slot(loaded) == 2

    exclude_compiled = compile_slot_patterns([PatternSlot(pattern="ERROR")])
    assert match_exclude_slots("[HOST/ERROR] fail", exclude_compiled) is True
    assert build_highlight_rules(loaded)[0].color_name == "Red"


def test_replay_batch_drains_expected_queue() -> None:
    lines = deque(["a", "b", "c"])

    batch = drain_replay_batch(lines, 2)

    assert batch == ["a", "b"]
    assert list(lines) == ["c"]


def test_replay_samples_are_non_empty() -> None:
    assert build_text_replay_sample()
    assert build_temperature_replay_sample()


def test_simulation_helpers_emit_expected_prefixes() -> None:
    text_line = next_text_simulation_line(TextSimulationState())
    logic_line = next_client_logic_simulation_line([0] * 8)

    assert text_line.startswith("[")
    assert logic_line.startswith("[CSV_LOGIC];")
