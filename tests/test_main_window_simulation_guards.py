from __future__ import annotations

from udp_log_viewer.main import MainWindow


class _DummyAction:
    def __init__(self, checked: bool = True) -> None:
        self.checked = checked
        self.enabled = True
        self.block_calls: list[bool] = []

    def blockSignals(self, value: bool) -> None:
        self.block_calls.append(value)

    def setChecked(self, value: bool) -> None:
        self.checked = value

    def isChecked(self) -> bool:
        return self.checked

    def setEnabled(self, value: bool) -> None:
        self.enabled = value


class _DummyTimer:
    def __init__(self) -> None:
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True


class _DummyStatusBar:
    def __init__(self) -> None:
        self.messages: list[tuple[str, int]] = []

    def showMessage(self, message: str, timeout: int) -> None:
        self.messages.append((message, timeout))


class _DummyWindow:
    def __init__(self) -> None:
        self._listener = None
        self._status_bar = _DummyStatusBar()
        self.act_simulate = _DummyAction(True)
        self.act_simulate_temperature = _DummyAction(True)
        self.act_simulate_logic = _DummyAction(True)
        self._sim_logic_enabled = False
        self._sim_logic_timer = _DummyTimer()
        self._ingested: list[str] = []
        self._replay_started = False
        self._replay_lines = []
        self._replay_active = False
        self._replay_requires_connection = False
        self._replay_timer = _DummyTimer()

    def statusBar(self) -> _DummyStatusBar:
        return self._status_bar

    def _is_connected(self) -> bool:
        return self._listener is not None

    def _set_action_checked_without_signal(self, action, checked: bool) -> None:
        MainWindow._set_action_checked_without_signal(self, action, checked)

    def _require_connected_for_generated_data(self, action=None) -> bool:
        return MainWindow._require_connected_for_generated_data(self, action)

    def _set_generated_data_actions_enabled(self, enabled: bool) -> None:
        MainWindow._set_generated_data_actions_enabled(self, enabled)

    def on_stop_replay_clicked(self) -> None:
        self._replay_started = False
        self._replay_lines = []
        self._replay_active = False
        self._replay_requires_connection = False

    def _ingest_line(self, line: str) -> None:
        self._ingested.append(line)


def test_require_connected_for_generated_data_unchecks_action_and_reports_status() -> None:
    window = _DummyWindow()
    action = _DummyAction(True)

    allowed = MainWindow._require_connected_for_generated_data(window, action)

    assert allowed is False
    assert action.checked is False
    assert action.block_calls == [True, False]
    assert window.statusBar().messages[-1] == ("Simulation requires CONNECTED (start listener first).", 2500)


def test_logic_simulation_is_blocked_without_connection() -> None:
    window = _DummyWindow()

    MainWindow.on_simulate_logic_toggled(window, True)

    assert window._sim_logic_enabled is False
    assert window._sim_logic_timer.started is False
    assert window.act_simulate_logic.checked is False
    assert window.statusBar().messages[-1] == ("Simulation requires CONNECTED (start listener first).", 2500)


def test_replay_sample_is_blocked_without_connection(monkeypatch) -> None:
    window = _DummyWindow()

    monkeypatch.setattr("udp_log_viewer.main.build_text_replay_sample", lambda: ["sample"])

    MainWindow.on_replay_sample_clicked(window)

    assert window._replay_started is False
    assert window._replay_lines == []
    assert window._replay_active is False
    assert window._replay_requires_connection is False
    assert window.statusBar().messages[-1] == ("Simulation requires CONNECTED (start listener first).", 2500)


def test_generated_data_actions_follow_connection_state() -> None:
    window = _DummyWindow()

    MainWindow._set_generated_data_actions_enabled(window, False)

    assert window.act_simulate.enabled is False
    assert window.act_simulate_temperature.enabled is False
    assert window.act_simulate_logic.enabled is False

    MainWindow._set_generated_data_actions_enabled(window, True)

    assert window.act_simulate.enabled is True
    assert window.act_simulate_temperature.enabled is True
    assert window.act_simulate_logic.enabled is True
