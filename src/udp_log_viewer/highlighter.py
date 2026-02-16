from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Pattern, Union

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QSyntaxHighlighter, QTextCharFormat


PatternOrStr = Union[Pattern[str], str]


def _parse_tokens(text: str) -> List[str]:
    return [t.strip() for t in text.split(";") if t.strip()]


def _compile_tokens(tokens: List[str], mode: str) -> List[PatternOrStr]:
    if not tokens:
        return []

    if mode == "Regex":
        out: List[PatternOrStr] = []
        for t in tokens:
            try:
                out.append(re.compile(t))
            except re.error:
                # invalid regex token -> ignore token (rule may become ineffective)
                pass
        return out

    # Substring mode
    return tokens


def _rule_matches(line: str, compiled: List[PatternOrStr]) -> bool:
    # AND logic
    if not compiled:
        return False

    for p in compiled:
        if isinstance(p, str):
            if p not in line:
                return False
        else:
            if not p.search(line):
                return False
    return True


def _color_from_name(name: str) -> Optional[QColor]:
    name = (name or "").strip().lower()
    if name in ("", "none"):
        return None

    # Minimal palette
    mapping = {
        "red": QColor("#e74c3c"),
        "green": QColor("#2ecc71"),
        "blue": QColor("#3498db"),
        "orange": QColor("#f39c12"),
        "purple": QColor("#9b59b6"),
        "gray": QColor("#95a5a6"),
    }
    return mapping.get(name)


@dataclass(frozen=True)
class HighlightRule:
    pattern_text: str         # user text, may contain ';'
    mode: str                 # "Substring" | "Regex"
    color_name: str           # "Red" | ...
    compiled: List[PatternOrStr]

    @staticmethod
    def create(pattern_text: str, mode: str, color_name: str) -> "HighlightRule":
        tokens = _parse_tokens(pattern_text)
        compiled = _compile_tokens(tokens, mode)
        return HighlightRule(pattern_text=pattern_text, mode=mode, color_name=color_name, compiled=compiled)

    def matches(self, line: str) -> bool:
        return _rule_matches(line, self.compiled)

    def color(self) -> Optional[QColor]:
        return _color_from_name(self.color_name)


class LogHighlighter(QSyntaxHighlighter):
    """
    Minimal highlighter for QPlainTextEdit (QTextDocument).

    - Iterates all rules
    - First match wins
    - Applies a foreground color (minimal, readable)
    """

    def __init__(self, parent_document) -> None:
        super().__init__(parent_document)
        self._rules: List[HighlightRule] = []
        self._default_format = QTextCharFormat()

    def set_rules(self, rules: List[HighlightRule]) -> None:
        self._rules = list(rules)
        self.rehighlight()

    def highlightBlock(self, text: str) -> None:
        if not self._rules or not text:
            return

        for r in self._rules:
            col = r.color()
            if col is None:
                continue
            if r.matches(text):
                fmt = QTextCharFormat(self._default_format)
                fmt.setForeground(col)
                self.setFormat(0, len(text), fmt)
                return