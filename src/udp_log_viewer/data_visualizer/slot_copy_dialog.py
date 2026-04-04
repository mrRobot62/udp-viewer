from __future__ import annotations

from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QSpinBox, QVBoxLayout, QWidget

from .visualizer_slot import SLOT_COUNT


class SlotCopyDialog(QDialog):
    def __init__(self, current_slot: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Copy from SLOT to SLOT")
        self.setModal(True)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._from_slot = QSpinBox()
        self._from_slot.setRange(1, SLOT_COUNT)
        self._from_slot.setValue(current_slot + 1)
        self._from_slot.setToolTip("Source slot whose configuration should be copied.")
        form.addRow("From Slot", self._from_slot)

        self._to_slot = QSpinBox()
        self._to_slot.setRange(1, SLOT_COUNT)
        self._to_slot.setValue(current_slot + 1)
        self._to_slot.setToolTip("Target slot that will receive the copied configuration.")
        form.addRow("To Slot", self._to_slot)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self)
        buttons.button(QDialogButtonBox.Ok).setText("COPY")
        buttons.button(QDialogButtonBox.Ok).setToolTip("Copy the selected slot configuration to the target slot.")
        buttons.button(QDialogButtonBox.Cancel).setToolTip("Close the dialog without copying a slot configuration.")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def source_slot(self) -> int:
        return self._from_slot.value() - 1

    def target_slot(self) -> int:
        return self._to_slot.value() - 1
