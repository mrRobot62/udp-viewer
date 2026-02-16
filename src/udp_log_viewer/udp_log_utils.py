from __future__ import annotations

import json
import re
from collections import deque
from typing import Deque, List, Pattern, Union, Any, Dict


def drain_queue(q: Deque[str], max_items: int) -> List[str]:
    out: List[str] = []
    for _ in range(max_items):
        if not q:
            break
        out.append(q.popleft())
    return out


# ---------- Filter helpers ----------

def _parse_tokens(text: str) -> List[str]:
    return [t.strip() for t in text.split(";") if t.strip()]


def compile_patterns(text: str, mode: str) -> List[Pattern[str] | str]:
    tokens = _parse_tokens(text)
    if not tokens:
        return []

    if mode == "Regex":
        out: List[Pattern[str]] = []
        for t in tokens:
            try:
                out.append(re.compile(t))
            except re.error:
                pass
        return out
    else:
        return tokens


def match_include(line: str, patterns: List[Pattern[str] | str]) -> bool:
    # AND logic
    if not patterns:
        return True

    for p in patterns:
        if isinstance(p, str):
            if p not in line:
                return False
        else:
            if not p.search(line):
                return False
    return True


def match_exclude(line: str, patterns: List[Pattern[str] | str]) -> bool:
    # OR logic
    if not patterns:
        return False

    for p in patterns:
        if isinstance(p, str):
            if p in line:
                return True
        else:
            if p.search(line):
                return True
    return False


# ---------- Highlight rule persistence helpers ----------

def rules_to_json(rules: List[dict]) -> str:
    try:
        return json.dumps(rules, ensure_ascii=False)
    except Exception:
        return "[]"


def rules_from_json(text: str) -> List[dict]:
    try:
        data = json.loads(text or "[]")
        if isinstance(data, list):
            out: List[dict] = []
            for item in data:
                if isinstance(item, dict):
                    out.append(item)
            return out
    except Exception:
        pass
    return []