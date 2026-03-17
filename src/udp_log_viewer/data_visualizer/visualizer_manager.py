from .csv_log_parser import CsvLogParser
from .config_store import ConfigStore

class VisualizerManager:

    def __init__(self):
        self.parser = CsvLogParser()
        self.config_store = ConfigStore()
        self.visualizers = []
        self.sample_counter = 0

    def load_configs(self):
        self.visualizers = self.config_store.load_visualizer_configs()

    def save_configs(self):
        self.config_store.save_visualizer_configs(self.visualizers)

    def process_log_line(self, line: str):
        for config in self.visualizers:
            sample = self.parser.parse_line(line, config, self.sample_counter)
            if sample:
                self.sample_counter += 1
                # routing to window will be added later
