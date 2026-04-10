from __future__ import annotations

import re

_LEGACY_STATS_PATTERN = re.compile(r"(\s*[-;|]?\s*)?\{stats\}(\s*[-;|]?\s*)?", re.IGNORECASE)


def normalize_footer_status_format(value: str | None) -> str:
    fmt = (value or "").strip()
    if not fmt:
        return ""
    fmt = _LEGACY_STATS_PATTERN.sub(" ", fmt)
    fmt = re.sub(r"[ \t]{2,}", " ", fmt)
    fmt = re.sub(r" *\\n *", r"\\n", fmt)
    fmt = re.sub(r" *\n *", "\n", fmt)
    return fmt.strip(" -;|")
