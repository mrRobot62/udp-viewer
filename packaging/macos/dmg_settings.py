# packaging/macos/dmg_settings.py
# Settings for dmgbuild. Run your app build first (cx_Freeze), then:
#   dmgbuild -s packaging/macos/dmg_settings.py "UDPLogViewer" dist/UDPLogViewer.dmg
# Optionally pass the .app path:
#   dmgbuild -D APP_PATH="build/UDPLogViewer.app" -s packaging/macos/dmg_settings.py "UDPLogViewer" dist/UDPLogViewer.dmg

import os

volume_name = "UDPLogViewer"
format = "UDZO"

window_rect = ((200, 200), (540, 380))
default_view = "icon-view"
icon_size = 128
text_size = 12

# Optional background image (PNG)
# background = "packaging/macos/dmg_background.png"

symlinks = {"Applications": "/Applications"}

APP_PATH = globals().get("APP_PATH")


def _find_app_under_build() -> str:
    # 1) bdist_mac variant: build/<Something>.app
    if os.path.isdir("build"):
        for entry in os.listdir("build"):
            if entry.endswith(".app"):
                return os.path.join("build", entry)

    # 2) classic build structure: build/exe.macosx-*/<Name>.app
    if os.path.isdir("build"):
        for root, dirs, _files in os.walk("build"):
            for d in dirs:
                if d.endswith(".app"):
                    return os.path.join(root, d)

    raise FileNotFoundError(
        "No .app found under 'build/'. Build first with:\n"
        "  python freeze_setup.py bdist_mac\n"
        "or\n"
        "  python freeze_setup.py build"
    )


if not APP_PATH:
    APP_PATH = _find_app_under_build()

APP_NAME = os.path.basename(APP_PATH)

files = [(APP_PATH, APP_NAME)]

icon_locations = {
    APP_NAME: (140, 200),
    "Applications": (400, 200),
}
