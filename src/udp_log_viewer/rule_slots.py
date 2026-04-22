from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List, Optional

from .highlighter import HighlightRule
from .udp_log_utils import compile_patterns


@dataclass
class PatternSlot:
    """Single filter, exclude, or highlight slot definition."""
    pattern: str = ""
    mode: str = "Substring"
    color: str = "None"


def slots_from_json(raw: str, slot_count: int) -> List[PatternSlot]:
    """Handle slots from json."""
    if not raw:
        return [PatternSlot() for _ in range(slot_count)]
    try:
        items = json.loads(raw)
        if not isinstance(items, list):
            return [PatternSlot() for _ in range(slot_count)]
        out: List[PatternSlot] = [PatternSlot() for _ in range(slot_count)]
        for index in range(min(slot_count, len(items))):
            item = items[index]
            if not isinstance(item, dict):
                continue
            out[index] = PatternSlot(
                pattern=str(item.get("pattern", "")).strip(),
                mode=str(item.get("mode", "Substring")).strip() or "Substring",
                color=str(item.get("color", "None")).strip() or "None",
            )
        return out
    except Exception:
        return [PatternSlot() for _ in range(slot_count)]


def slots_to_json(slots: List[PatternSlot]) -> str:
    """Handle slots to json."""
    items = [{"pattern": s.pattern, "mode": s.mode, "color": s.color} for s in slots]
    return json.dumps(items, ensure_ascii=False)


def strip_slot_colors(slots: List[PatternSlot]) -> List[PatternSlot]:
    """Handle strip slot colors."""
    return [PatternSlot(pattern=slot.pattern, mode=slot.mode, color="None") for slot in slots]


def compile_slot_patterns(slots: List[PatternSlot]) -> List[List[object]]:
    """Compile slot patterns."""
    compiled: List[List[object]] = []
    for slot in slots:
        if not slot.pattern.strip():
            continue
        patterns = compile_patterns(slot.pattern, slot.mode)
        if patterns:
            compiled.append(patterns)
    return compiled


def match_all_patterns(line: str, patterns: List[object]) -> bool:
    """Return whether all patterns."""
    for pattern in patterns:
        try:
            if hasattr(pattern, "search"):
                if pattern.search(line) is None:
                    return False
            elif callable(pattern):
                if not bool(pattern(line)):
                    return False
            else:
                if str(pattern) not in line:
                    return False
        except Exception:
            return False
    return True


def match_include_slots(line: str, compiled_patterns: List[List[object]]) -> bool:
    """Return whether include slots."""
    if not compiled_patterns:
        return True
    for patterns in compiled_patterns:
        if not match_all_patterns(line, patterns):
            return False
    return True


def match_exclude_slots(line: str, compiled_patterns: List[List[object]]) -> bool:
    """Return whether exclude slots."""
    for patterns in compiled_patterns:
        if match_all_patterns(line, patterns):
            return True
    return False


def build_highlight_rules(slots: List[PatternSlot]) -> List[HighlightRule]:
    """Build and return highlight rules."""
    rules: List[HighlightRule] = []
    for slot in slots:
        if not slot.pattern.strip():
            continue
        if slot.color.strip().lower() == "none":
            continue
        rule = HighlightRule.create(slot.pattern, slot.mode, slot.color)
        if rule is not None:
            rules.append(rule)
    return rules


def find_first_free_slot(slots: List[PatternSlot]) -> Optional[int]:
    """Find first free slot."""
    for index, slot in enumerate(slots):
        if not slot.pattern.strip():
            return index
    return None
