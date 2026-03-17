class VisualizerWindow:
    def __init__(self, config):
        self.config = config
        self.samples = []
        self.auto_refresh_enabled = True
        self.freeze_sample_index = None

    def append_sample(self, sample):
        self.samples.append(sample)

        if self.auto_refresh_enabled:
            self.refresh_plot()

    def set_auto_refresh(self, enabled: bool):
        self.auto_refresh_enabled = enabled

        if enabled:
            self.freeze_sample_index = None
            self.rebuild_plot()
        else:
            self.freeze_sample_index = len(self.samples)

    def refresh_plot(self):
        # placeholder for matplotlib refresh
        pass

    def rebuild_plot(self):
        # placeholder for full redraw
        pass
