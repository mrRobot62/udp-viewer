from .visualizer_sample import VisualizerSample
from .visualizer_config import VisualizerConfig

class CsvLogParser:
    def parse_line(self, line: str, config: VisualizerConfig, sample_index: int) -> VisualizerSample | None:
        parts = line.strip().split(";")
        if len(parts) < 2:
            return None

        timestamp = parts[0]
        filter_value = parts[1]

        if filter_value != config.filter_string:
            return None

        data_fields = parts[2:]
        if len(data_fields) != len(config.fields):
            return None

        values = {}

        for i, field_cfg in enumerate(config.fields):
            raw = data_fields[i].strip()

            if raw == "":
                values[field_cfg.field_name] = None
                continue

            if field_cfg.numeric:
                try:
                    val = float(raw)
                    scale = field_cfg.scale if field_cfg.scale > 0 else 1
                    values[field_cfg.field_name] = val / scale
                except ValueError:
                    values[field_cfg.field_name] = None
            else:
                values[field_cfg.field_name] = None

        return VisualizerSample(
            timestamp_raw=timestamp,
            filter_string=filter_value,
            sample_index=sample_index,
            values_by_name=values
        )
