from __future__ import annotations

from datetime import datetime
import re

from ..footer_format import normalize_footer_status_format
from .visualizer_sample import VisualizerSample

_PLACEHOLDER_PATTERN = re.compile(r"\{([^{}]+)\}")


def parse_footer_timestamp(timestamp_raw: str) -> datetime | None:
    value = (timestamp_raw or "").strip()
    if not value:
        return None
    try:
        return datetime.strptime(value.split(" ")[0], "%Y%m%d-%H:%M:%S.%f")
    except ValueError:
        return None


def format_footer_time(value: datetime | None) -> str:
    if value is None:
        return "--:--:--"
    return value.strftime("%H:%M:%S")


def format_footer_duration(start_time: datetime | None, end_time: datetime | None) -> str:
    if start_time is None or end_time is None:
        return "--:--:--"
    total_seconds = max(0, int((end_time - start_time).total_seconds()))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def format_footer_template(template: str, resolver) -> str:
    raw_template = (template or "").strip()
    if not raw_template:
        return ""
    normalized_template = raw_template.replace("\\n", "\n")

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        replacement = resolver(key)
        return replacement if replacement is not None else match.group(0)

    return _PLACEHOLDER_PATTERN.sub(_replace, normalized_template)


def build_footer_context(samples: list[VisualizerSample]) -> dict[str, str]:
    first_time = parse_footer_timestamp(samples[0].timestamp_raw) if samples else None
    last_time = parse_footer_timestamp(samples[-1].timestamp_raw) if samples else None
    return {
        "start": format_footer_time(first_time),
        "end": format_footer_time(last_time),
        "duration": format_footer_duration(first_time, last_time),
        "samples": str(len(samples)),
    }
