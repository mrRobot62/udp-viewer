from __future__ import annotations

import re

from .visualizer_config import VisualizerConfig
from .visualizer_sample import VisualizerSample


class CsvLogParser:
    _FILTER_IN_FIRST_FIELD_RE = re.compile(
        r"^(?P<timestamp>.*?)\s*(?P<filter>\[CSV_[^\]]+\])\s*$"
    )

    def parse_line(
        self,
        line: str,
        config: VisualizerConfig,
        sample_index: int,
    ) -> VisualizerSample | None:
        timestamp, filter_value, data_fields = self._extract_parts(line)
        if filter_value is None:
            return None

        if filter_value != config.filter_string:
            return None

        if len(data_fields) != len(config.fields):
            return None

        values: dict[str, float | None] = {}

        for raw_value, field_cfg in zip(data_fields, config.fields, strict=True):
            if not field_cfg.field_name:
                continue

            if raw_value == "":
                values[field_cfg.field_name] = None
                continue

            if not field_cfg.numeric:
                values[field_cfg.field_name] = None
                continue

            parsed_value = self._parse_numeric_value(raw_value, field_cfg.scale)
            values[field_cfg.field_name] = parsed_value

        return VisualizerSample(
            timestamp_raw=timestamp,
            filter_string=filter_value,
            sample_index=sample_index,
            values_by_name=values,
        )

    def _extract_parts(self, line: str) -> tuple[str, str | None, list[str]]:
        # Spaces before/after ';' are tolerated and ignored.
        parts = [part.strip() for part in line.strip().split(";")]
        if not parts:
            return "", None, []

        # Variant A:
        #   <timestamp> ; [CSV_TEMP] ; ...
        # Variant B:
        #   <timestamp>;[CSV_TEMP];...
        if len(parts) >= 2 and parts[1].startswith("[CSV_"):
            timestamp = parts[0]
            filter_value = parts[1]
            data_fields = parts[2:]
            return timestamp, filter_value, data_fields

        # Variant C:
        #   <timestamp> [CSV_TEMP] ; ...
        first = parts[0]
        match = self._FILTER_IN_FIRST_FIELD_RE.match(first)
        if match is not None:
            timestamp = match.group("timestamp").strip()
            filter_value = match.group("filter").strip()
            data_fields = parts[1:]
            return timestamp, filter_value, data_fields

        # Variant D:
        #   [CSV_TEMP] ; ...
        if parts[0].startswith("[CSV_"):
            timestamp = ""
            filter_value = parts[0]
            data_fields = parts[1:]
            return timestamp, filter_value, data_fields

        return "", None, []

    @staticmethod
    def _parse_numeric_value(raw_value: str, scale: int) -> float | None:
        try:
            numeric_value = float(raw_value)
        except ValueError:
            return None

        normalized_scale = scale if scale > 0 else 1
        return numeric_value / normalized_scale
