from .visualizer_config import VisualizerConfig
from .visualizer_sample import VisualizerSample


class CsvLogParser:
    def parse_line(
        self,
        line: str,
        config: VisualizerConfig,
        sample_index: int,
    ) -> VisualizerSample | None:
        parts = [part.strip() for part in line.strip().split(";")]
        if len(parts) < 2:
            return None

        timestamp = parts[0]
        filter_value = parts[1]

        if not timestamp or filter_value != config.filter_string:
            return None

        data_fields = parts[2:]
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

    @staticmethod
    def _parse_numeric_value(raw_value: str, scale: int) -> float | None:
        try:
            numeric_value = float(raw_value)
        except ValueError:
            return None

        normalized_scale = scale if scale > 0 else 1
        return numeric_value / normalized_scale
