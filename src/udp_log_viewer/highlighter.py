from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Pattern, Union

from PyQt5.QtGui import QColor, QSyntaxHighlighter, QTextCharFormat

PatternOrStr = Union[Pattern[str], str]


def _compile(pattern_text: str, mode: str) -> Optional[PatternOrStr]:
    pattern_text = (pattern_text or "").strip()
    if not pattern_text:
        return None

    if mode == "Regex":
        try:
            return re.compile(pattern_text)
        except re.error:
            return None

    # Substring mode
    return pattern_text


def _matches(line: str, compiled: PatternOrStr) -> bool:
    if isinstance(compiled, str):
        return compiled in line
    return compiled.search(line) is not None


def _color_from_name(name: str) -> Optional[QColor]:
    name = (name or "").strip().lower()
    if name in ("", "none"):
        return None

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
    """
    Single-pattern rule (no AND/semicolon logic).
    """
    pattern_text: str
    mode: str               # "Substring" | "Regex"
    color_name: str         # "Red" | ...
    compiled: PatternOrStr

    @staticmethod
    def create(pattern_text: str, mode: str, color_name: str) -> Optional["HighlightRule"]:
        mode = (mode or "Substring").strip()
        if mode not in ("Substring", "Regex"):
            mode = "Substring"

        compiled = _compile(pattern_text, mode)
        if compiled is None:
            return None

        return HighlightRule(
            pattern_text=pattern_text.strip(),
            mode=mode,
            color_name=(color_name or "None").strip(),
            compiled=compiled,
        )

    def matches(self, line: str) -> bool:
        return _matches(line, self.compiled)

    def color(self) -> Optional[QColor]:
        return _color_from_name(self.color_name)


class LogHighlighter(QSyntaxHighlighter):
    """
    Minimal highlighter for QPlainTextEdit (QTextDocument).

    - Iterates rules in order
    - First match wins
    - Applies foreground color only (minimal design)
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
