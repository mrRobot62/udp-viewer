"""Verify AND/OR slot semantics while retaining legacy matching behavior."""

import pytest

from udp_log_viewer.rule_slots import (
    PatternSlot, compile_slot_patterns, match_include_slots, match_exclude_slots,
)


@pytest.mark.parametrize("operator, expected", [("AND", [False, False, True, False]), ("OR", [True, True, True, False])])
def test_include_combinations(operator, expected):
    """Allow either message family or require both active slot patterns."""
    patterns = compile_slot_patterns([PatternSlot("ADC"), PatternSlot(), PatternSlot("PCF")])
    assert [match_include_slots(line, patterns, operator) for line in ("ADC ready", "PCF ready", "ADC PCF", "other")] == expected


@pytest.mark.parametrize("operator, expected", [("AND", [False, False, True, False]), ("OR", [True, True, True, False])])
def test_exclude_combinations(operator, expected):
    """Exclude one targeted subtype with AND or whole families with OR."""
    patterns = compile_slot_patterns([PatternSlot("CL57TE"), PatternSlot("scope")])
    assert [match_exclude_slots(line, patterns, operator) for line in ("CL57TE init", "other scope", "CL57TE scope", "ADC")] == expected


@pytest.mark.parametrize("operator", ["AND", "OR"])
def test_empty_and_single_groups(operator):
    """Empty groups never suppress output; one slot is operator-independent."""
    empty = compile_slot_patterns([PatternSlot(), PatternSlot(" ")])
    assert match_include_slots("anything", empty, operator)
    assert not match_exclude_slots("anything", empty, operator)
    single = compile_slot_patterns([PatternSlot("ADC")])
    for match in (match_include_slots, match_exclude_slots):
        assert match("ADC ready", single, operator)
        assert not match("PCF ready", single, operator)


def test_defaults_and_invalid_selection_preserve_legacy_behavior():
    """Missing or invalid operators keep include-AND and exclude-OR semantics."""
    patterns = compile_slot_patterns([PatternSlot("ADC"), PatternSlot("PCF")])
    assert not match_include_slots("ADC", patterns)
    assert match_exclude_slots("ADC", patterns)
    assert not match_include_slots("ADC", patterns, "invalid")
    assert match_exclude_slots("ADC", patterns, "invalid")


def test_or_between_slots_does_not_change_and_within_slot():
    """Preserve multiple terms in one slot and regular expression matching."""
    patterns = compile_slot_patterns([PatternSlot("CL57TE;bench"), PatternSlot(r"ADC\s+timeout", "Regex")])
    assert match_include_slots("CL57TE bench", patterns, "OR")
    assert match_include_slots("ADC timeout", patterns, "OR")
    assert not match_include_slots("CL57TE init", patterns, "OR")
    assert not match_include_slots("ADC ready", patterns, "OR")
