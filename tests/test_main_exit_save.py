from __future__ import annotations

from types import SimpleNamespace

from udp_log_viewer.main import MainWindow


class _DummyMessageBox:
    Question = object()
    YesRole = object()
    NoRole = object()
    RejectRole = object()
    clicked = None
    instances: list["_DummyMessageBox"] = []

    def __init__(self, parent) -> None:
        self.parent = parent
        self.buttons: list[tuple[str, object]] = []
        self._clicked = None
        _DummyMessageBox.instances.append(self)

    def setWindowTitle(self, value: str) -> None:
        self.window_title = value

    def setIcon(self, value) -> None:
        self.icon = value

    def setText(self, value: str) -> None:
        self.text = value

    def setInformativeText(self, value: str) -> None:
        self.info = value

    def addButton(self, label: str, role):
        button = SimpleNamespace(label=label, role=role)
        self.buttons.append((label, role))
        if label == _DummyMessageBox.clicked:
            self._clicked = button
        return button

    def setDefaultButton(self, button) -> None:
        self.default = button

    def exec_(self) -> None:
        return None

    def clickedButton(self):
        return self._clicked


class _DummyExitWindow:
    def __init__(self, *, connected: bool, rx_lines: int, save_result="saved") -> None:
        self._listener = object() if connected else None
        self._connection_state = SimpleNamespace(rx_lines=rx_lines)
        self.save_calls = 0
        self.save_result = save_result

    def on_save_clicked(self):
        self.save_calls += 1
        return self.save_result


def test_exit_save_prompt_is_skipped_without_connection() -> None:
    window = _DummyExitWindow(connected=False, rx_lines=10)

    allowed = MainWindow._confirm_save_logs_before_exit(window)

    assert allowed is True
    assert window.save_calls == 0


def test_exit_save_prompt_is_skipped_without_received_data() -> None:
    window = _DummyExitWindow(connected=True, rx_lines=0)

    allowed = MainWindow._confirm_save_logs_before_exit(window)

    assert allowed is True
    assert window.save_calls == 0


def test_exit_cancel_blocks_exit(monkeypatch) -> None:
    _DummyMessageBox.instances.clear()
    _DummyMessageBox.clicked = "Cancel"
    monkeypatch.setattr("udp_log_viewer.main.QMessageBox", _DummyMessageBox)
    window = _DummyExitWindow(connected=True, rx_lines=5)

    allowed = MainWindow._confirm_save_logs_before_exit(window)

    assert allowed is False
    assert window.save_calls == 0


def test_exit_yes_with_successful_save_allows_exit(monkeypatch) -> None:
    _DummyMessageBox.instances.clear()
    _DummyMessageBox.clicked = "Save…"
    monkeypatch.setattr("udp_log_viewer.main.QMessageBox", _DummyMessageBox)
    window = _DummyExitWindow(connected=True, rx_lines=5, save_result="/tmp/out.txt")

    allowed = MainWindow._confirm_save_logs_before_exit(window)

    assert allowed is True
    assert window.save_calls == 1


def test_exit_yes_with_aborted_save_blocks_exit(monkeypatch) -> None:
    _DummyMessageBox.instances.clear()
    _DummyMessageBox.clicked = "Save…"
    monkeypatch.setattr("udp_log_viewer.main.QMessageBox", _DummyMessageBox)
    window = _DummyExitWindow(connected=True, rx_lines=5, save_result=None)

    allowed = MainWindow._confirm_save_logs_before_exit(window)

    assert allowed is False
    assert window.save_calls == 1


def test_exit_no_allows_exit_without_save(monkeypatch) -> None:
    _DummyMessageBox.instances.clear()
    _DummyMessageBox.clicked = "No"
    monkeypatch.setattr("udp_log_viewer.main.QMessageBox", _DummyMessageBox)
    window = _DummyExitWindow(connected=True, rx_lines=5)

    allowed = MainWindow._confirm_save_logs_before_exit(window)

    assert allowed is True
    assert window.save_calls == 0

