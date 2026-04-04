from __future__ import annotations

from pathlib import Path

from udp_log_viewer.project_dialog import ProjectDialog


class _DummyLineEdit:
    def __init__(self, value: str = "") -> None:
        self.value = value

    def clear(self) -> None:
        self.value = ""

    def setText(self, value: str) -> None:
        self.value = value


def test_reset_to_defaults_clears_name_and_restores_default_root() -> None:
    dialog = ProjectDialog.__new__(ProjectDialog)
    dialog._name = _DummyLineEdit("Demo")
    dialog._root_dir = _DummyLineEdit("/tmp/custom")
    dialog._default_root_dir = Path("/tmp/default-project-root")
    captured: list[str] = []
    preview_calls: list[bool] = []

    dialog._set_default_notes_text = lambda project_name: captured.append(project_name)
    dialog._update_preview = lambda: preview_calls.append(True)

    ProjectDialog._reset_to_defaults(dialog)

    assert dialog._name.value == ""
    assert dialog._root_dir.value == "/tmp/default-project-root"
    assert captured == ["project"]
    assert preview_calls == [True]
