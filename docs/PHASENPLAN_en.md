# UDP Log Viewer Phase Plan

This document acts as a fixed development reference for the next larger
project phases.

Important:

Before moving into a new phase, that phase should be briefly revisited
and re-confirmed. Only after that reflection should the actual code
changes begin.

## Rule for Phase Transitions

Whenever moving into the next phase:

1. briefly confirm the phase goal
2. name the affected files and risks
3. check whether priorities changed since the previous phase
4. only then start implementation, refactoring, or tests

## Phase 1: Stabilization

Goal:

Make the codebase reproducibly testable and internally consistent again.

Content:

- make `pytest` runnable directly from repository root
- wire the `src` layout cleanly into tests
- ensure `scripts/dev_test.sh` really runs tests
- centralize the version source
- remove version drift between package, GUI, and freeze scripts
- clean up obvious replay and simulation inconsistencies
- build a small but reliable automated test core

Status:

Completed

## Phase 2: Maintainability

Goal:

Move core runtime logic out of the large main module and make it more
testable.

Content:

- split [main.py](../src/udp_log_viewer/main.py) incrementally
- separate responsibilities for connection, replay, rules, settings,
  and visualizer integration
- separate UI-adjacent logic from domain logic
- convert smoke-style scripts into automated tests
- extend test coverage for parser, rules, persistence, and replay
- clarify configuration ownership between `QSettings` and `config.ini`

Status:

Open

## Phase 3: Product Readiness

Goal:

Move the application toward a clearly documented, releasable, and
extensible product base.

Content:

- formalize CSV contracts for plot and logic traffic
- verify build and packaging paths for macOS and Windows in practice
- structure technical documentation further
- decouple internal event and data flow further
- prepare the base for later exports and additional visualizers

Status:

Open
