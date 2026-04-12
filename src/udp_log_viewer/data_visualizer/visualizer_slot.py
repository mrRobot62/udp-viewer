from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


VisualizerGraphType = Literal["plot", "logic"]
SLOT_COUNT = 5


@dataclass(frozen=True, slots=True)
class VisualizerSlotId:
    """Typed identifier for a visualizer slot."""
    graph_type: VisualizerGraphType
    slot_index: int

    @property
    def slot_number(self) -> int:
        """Handle slot number."""
        return self.slot_index + 1


def iter_slot_ids(graph_type: VisualizerGraphType) -> list[VisualizerSlotId]:
    """Return slot ids."""
    return [VisualizerSlotId(graph_type=graph_type, slot_index=index) for index in range(SLOT_COUNT)]
