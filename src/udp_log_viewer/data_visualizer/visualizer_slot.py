from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


VisualizerGraphType = Literal["plot", "logic"]
SLOT_COUNT = 5


@dataclass(frozen=True, slots=True)
class VisualizerSlotId:
    graph_type: VisualizerGraphType
    slot_index: int

    @property
    def slot_number(self) -> int:
        return self.slot_index + 1


def iter_slot_ids(graph_type: VisualizerGraphType) -> list[VisualizerSlotId]:
    return [VisualizerSlotId(graph_type=graph_type, slot_index=index) for index in range(SLOT_COUNT)]
