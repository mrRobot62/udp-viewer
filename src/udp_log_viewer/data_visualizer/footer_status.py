from __future__ import annotations

from datetime import datetime
import re
from typing import Any

from ..footer_format import normalize_footer_status_format
from .visualizer_sample import VisualizerSample

_PLACEHOLDER_PATTERN = re.compile(r"\{([^{}]+)\}")


def split_footer_placeholder(value: str) -> tuple[str, str]:
    name, separator, format_spec = value.strip().partition(":")
    if not separator:
        return name.strip(), ""
    return name.strip(), format_spec.strip()


def format_footer_value(value: Any, format_spec: str = "", unit: str = "") -> str:
    if value is None:
        return "--"
    if format_spec:
        try:
            formatted = format(value, format_spec)
        except (TypeError, ValueError):
            formatted = str(value)
    else:
        formatted = str(value)
    unit_text = (unit or "").strip()
    if unit_text:
        return f"{formatted} {unit_text}"
    return formatted


def resolve_footer_context_placeholder(key: str, context: dict[str, Any]) -> str | None:
    name, format_spec = split_footer_placeholder(key)
    value = context.get(name.lower())
    if value is None:
        return None
    return format_footer_value(value, format_spec)


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


def build_footer_context(samples: list[VisualizerSample]) -> dict[str, Any]:
    first_time = parse_footer_timestamp(samples[0].timestamp_raw) if samples else None
    last_time = parse_footer_timestamp(samples[-1].timestamp_raw) if samples else None
    return {
        "start": format_footer_time(first_time),
        "end": format_footer_time(last_time),
        "duration": format_footer_duration(first_time, last_time),
        "samples": len(samples),
    }
