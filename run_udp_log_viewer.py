#!/usr/bin/env python3
"""Entry point used for frozen builds.

We import the package module so relative imports inside udp_log_viewer.main work
(cx_Freeze executes this file as __main__).
"""

from udp_log_viewer.main import main

if __name__ == "__main__":
    raise SystemExit(main())
