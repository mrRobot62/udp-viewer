Step 10.x — Fix frozen entrypoint (macOS/Windows)

Problem
- Frozen binary crashed with:
  ImportError: attempted relative import with no known parent package

Cause
- cx_Freeze executed udp_log_viewer/main.py as __main__.
- main.py uses relative imports (from .highlighter import ...), which require package context.

Fix
1) Add repo-root wrapper `run_udp_log_viewer.py`:
   - imports `udp_log_viewer.main` as a package module and calls main()
2) Update `freeze_setup.py` to freeze the wrapper script, not udp_log_viewer/main.py.
3) Exclude QtQml/Quick modules to avoid the `QmlImportsPath` hook error.

How to use
- Copy both files into your repo root:
  - run_udp_log_viewer.py
  - freeze_setup.py (replace existing)
- Build:
  python freeze_setup.py build

Test
- Run:
  ./build/exe.macosx-*/UDPLogViewer
