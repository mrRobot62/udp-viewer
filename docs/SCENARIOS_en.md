# UDP Viewer Scenarios

This document extends the user guide with practical scenarios. Each one
uses the same structure so you can quickly decide whether it matches
your current task and how to approach it with UDP Viewer.

Related documents:

- [User Guide](USER_GUIDE_en.md)
- [Scenario Figures](SCENARIO_IMAGES_en.md)
- [Supported CSV Input Formats](SUPPORTED_CSV_INPUT_FORMATS_en.md)
- [Simulation Reference](SIMULATION_REFERENCE_en.md)

## Contents

- [Scenario 1 Checking Drift on an ESP32 Sensor Node](#scenario-1-checking-drift-on-an-esp32-sensor-node)
- [Scenario 2 Checking an Arduino Firmware Change](#scenario-2-checking-an-arduino-firmware-change)
- [Scenario 3 Assessing Control Behavior in an ESP-IDF Project](#scenario-3-assessing-control-behavior-in-an-esp-idf-project)
- [Scenario 4 Checking ESP32 Digital Timing](#scenario-4-checking-esp32-digital-timing)
- [Scenario 5 Evaluating a Battery-Powered IoT Node Over Time](#scenario-5-evaluating-a-battery-powered-iot-node-over-time)
- [Scenario 6 Analyzing a Device Boot Sequence](#scenario-6-analyzing-a-device-boot-sequence)
- [Scenario 7 Narrowing Down a Noisy UDP Stream](#scenario-7-narrowing-down-a-noisy-udp-stream)
- [Scenario 8 Comparing a Normal Run with a Faulty Run](#scenario-8-comparing-a-normal-run-with-a-faulty-run)
- [Scenario 9 Detecting a Protocol Regression After a Firmware Update](#scenario-9-detecting-a-protocol-regression-after-a-firmware-update)
- [Scenario 10 Reviewing a Delivered Recording in a Reproducible Way](#scenario-10-reviewing-a-delivered-recording-in-a-reproducible-way)

## Scenario 1 Checking Drift on an ESP32 Sensor Node

### Goal

Find out whether a sensor node is really drifting or whether you are
only seeing occasional noisy readings.

### Initial Situation

You have an ESP32 that periodically sends UDP text logs and CSV values
for temperature, humidity, and supply voltage. After some time, the
temperature starts to look too high even though nothing obvious changed
around the device.

### Typical Symptoms

- the temperature rises slowly instead of jumping abruptly
- single values still look believable, but the overall trend does not
- the text log does not immediately tell you whether the cause is the
  sensor, the firmware, or the transport path

### Why UDP Viewer Helps Here

You can keep the text log and the CSV plot visible at the same time.
That makes it much easier to judge whether the trend is real or only the
result of occasional outliers.

### Procedure

1. Create a new project for the run and note what you want to verify.
2. Connect to the UDP stream of the ESP32.
3. Add a filter for sensor-related messages if the log is noisy.
4. Open the plot visualizer for temperature and supply voltage.
5. Watch the trend over several minutes.
6. Measure the distance between two points in time.
7. Save the log and screenshots once the behavior is clear.

### Expected Findings

- whether the value really drifts or only fluctuates now and then
- whether the trend changes together with the supply voltage
- whether reconnects, warnings, or calibration hints appear at the same
  time

### Relevant UDP Viewer Functions

- `PROJECT`
- `CONNECT`
- `Filter`
- Plot visualizer
- Plot measurement
- `SAVE`
- Screenshot export

### Figures

- [Figure 1 Main Window Overview](SCENARIO_IMAGES_en.md#figure-1-main-window-overview)
- [Figure 4 Plot Visualizer Configuration](SCENARIO_IMAGES_en.md#figure-4-plot-visualizer-configuration)
- [Figure 6 Plot Visualizer Tooltip](SCENARIO_IMAGES_en.md#figure-6-plot-visualizer-tooltip)

### Notes / Limits

UDP Viewer makes the pattern easy to see. You still need to confirm in
the actual system whether the root cause is the sensor, the calibration,
or the firmware.

## Scenario 2 Checking an Arduino Firmware Change

### Goal

Verify that an updated Arduino firmware still produces the expected logs
and CSV output.

### Initial Situation

You changed something in the firmware, for example added new status
messages or modified a CSV field. Now you want to make sure the output
still matches your existing workflow.

### Typical Symptoms

- field names or field order changed without being noticed
- text messages look fine, but the plot stays empty
- an older preset suddenly no longer works cleanly

### Why UDP Viewer Helps Here

You can validate runtime behavior and data structure in one place. That
lets you spot the case where the firmware still sends data, but no
longer matches the visualizer setup you already depend on.

### Procedure

1. Create a fresh project for the firmware check.
2. Connect the viewer before rebooting or flashing the device.
3. Watch the boot and initialization messages in the main window.
4. Open the plot visualizer with the existing configuration.
5. Check whether the expected CSV fields still arrive correctly.
6. Replay the saved run later if you need to re-check it.

### Expected Findings

- whether the format still matches your previous configuration
- whether fields were added, removed, or moved
- whether only the preset needs an update or the firmware itself

### Relevant UDP Viewer Functions

- `PROJECT`
- `CONNECT`
- `SAVE`
- Replay from `Open Log…`
- Plot visualizer

### Figures

- [Figure 1 Main Window Overview](SCENARIO_IMAGES_en.md#figure-1-main-window-overview)
- [Figure 3 Project Dialog](SCENARIO_IMAGES_en.md#figure-3-project-dialog)
- [Figure 4 Plot Visualizer Configuration](SCENARIO_IMAGES_en.md#figure-4-plot-visualizer-configuration)

### Notes / Limits

CSV-based checks are often where a small protocol change first becomes
visible, even when the plain-text log still looks normal.

## Scenario 3 Assessing Control Behavior in an ESP-IDF Project

### Goal

Assess whether a control loop behaves stably or shows overshoot and slow
settling.

### Initial Situation

Your ESP32 running ESP-IDF sends CSV values for target, measured value,
and actuator output. At first glance everything works, but the curve
looks slower or more restless than expected.

### Typical Symptoms

- the measured value overshoots after a change
- the actuator output oscillates while the target stays constant
- there is no clear error message in the text log

### Why UDP Viewer Helps Here

The plot visualizer turns raw telemetry into something you can evaluate
directly. That saves you from exporting data into another tool or
reading raw CSV rows by hand.

### Procedure

1. Connect to the running controller.
2. Open the plot visualizer for target, actual value, and actuator
   output.
3. Keep the main window visible for contextual log messages.
4. Mark two points to estimate settling time.
5. Save the result in the project with screenshots.

### Expected Findings

- whether the loop overshoots too much
- whether the system settles quickly enough
- whether warnings or debug messages line up with the visible behavior

### Relevant UDP Viewer Functions

- Plot visualizer
- Plot measurement
- Highlight rules
- Screenshot export

### Figures

- [Figure 4 Plot Visualizer Configuration](SCENARIO_IMAGES_en.md#figure-4-plot-visualizer-configuration)
- [Figure 5 Plot Visualizer Detail](SCENARIO_IMAGES_en.md#figure-5-plot-visualizer-detail)
- [Figure 6 Plot Visualizer Tooltip](SCENARIO_IMAGES_en.md#figure-6-plot-visualizer-tooltip)

### Notes / Limits

This makes the behavior much easier to judge, but the actual control
design still has to be evaluated within the project itself.

## Scenario 4 Checking ESP32 Digital Timing

### Goal

Verify that digital states appear in the right order and with the right
timing.

### Initial Situation

Your device sends states such as `ready`, `relay_on`, or `door_open` as
CSV logic channels. You suspect that one state changes too early or too
late.

### Typical Symptoms

- two states appear in the wrong order
- one signal stays active longer than expected
- a timeout appears in the log only after the timing problem already
  started

### Why UDP Viewer Helps Here

The logic visualizer shows the timing directly and lets you measure
intervals without exporting or preprocessing the data first.

### Procedure

1. Connect to the CSV logic stream.
2. Open the logic visualizer and check the active channels.
3. Start a measurement at the first relevant edge.
4. Set the second marker at the matching edge.
5. Use `Space` and `Esc` to switch quickly between measurement and live
   viewing.

### Expected Findings

- whether the state order matches the implementation
- whether the timeout is the cause or only a follow-up symptom
- whether the issue happens reliably or only occasionally

### Relevant UDP Viewer Functions

- Logic visualizer
- Logic measurement
- Screenshot export
- Replay

### Figures

- [Figure 7 Logic Visualizer Configuration](SCENARIO_IMAGES_en.md#figure-7-logic-visualizer-configuration)
- [Figure 8 Logic Visualizer Measurement](SCENARIO_IMAGES_en.md#figure-8-logic-visualizer-measurement)

### Notes / Limits

This is especially useful when you do not measure real GPIO lines
directly and only see their reported states in the stream.

## Scenario 5 Evaluating a Battery-Powered IoT Node Over Time

### Goal

Check whether a battery-powered device keeps sending stably over a
longer run.

### Initial Situation

You have a mobile node that sends status data every few seconds. During
a longer run, you want to understand whether falling battery voltage
makes the send intervals unstable or causes values to drop out.

### Typical Symptoms

- the time between packets becomes irregular
- supply warnings appear only late in the run
- after a longer run it is hard to reconstruct when the problem started

### Why UDP Viewer Helps Here

With a project, saved log, and plot view, you can preserve a long run in
a clean and reusable form instead of ending up with scattered files and
single screenshots.

### Procedure

1. Create a project before the run starts.
2. Add a short note about the test context.
3. Watch text messages and CSV fields in parallel.
4. Save screenshots when voltage or cadence starts to look suspicious.
5. Save the complete run for later review.

### Expected Findings

- whether the send interval changes over time
- whether low voltage lines up with gaps in the data stream
- whether you can later review the run through replay

### Relevant UDP Viewer Functions

- `PROJECT`
- `SAVE`
- Plot visualizer
- Screenshot export
- Replay

### Figures

- [Figure 3 Project Dialog](SCENARIO_IMAGES_en.md#figure-3-project-dialog)
- [Figure 6 Plot Visualizer Tooltip](SCENARIO_IMAGES_en.md#figure-6-plot-visualizer-tooltip)

### Notes / Limits

This is especially useful when you cannot watch a long run permanently
but still want a reviewable record afterwards.

## Scenario 6 Analyzing a Device Boot Sequence

### Goal

Check whether a device passes through the expected startup steps in the
right order.

### Initial Situation

After power-on, the device sends logs for network initialization,
service startup, and readiness. Sometimes startup completes cleanly,
sometimes the device looks alive but is not really ready.

### Typical Symptoms

- expected startup messages are missing
- the device responds partially but not completely
- a good and a bad startup differ only by a few lines

### Why UDP Viewer Helps Here

You can capture the whole startup flow live and later compare it with a
known-good run. That is especially useful when startup problems are
sporadic.

### Procedure

1. Connect before restarting the device.
2. Watch the startup messages in the main window.
3. Highlight the important phases.
4. Save the run and compare it with a known-good startup.

### Expected Findings

- whether startup messages are complete
- where the failing startup diverges
- whether the problem begins before or after network readiness

### Relevant UDP Viewer Functions

- `CONNECT`
- Highlight rules
- `SAVE`
- Replay

### Figures

- [Figure 1 Main Window Overview](SCENARIO_IMAGES_en.md#figure-1-main-window-overview)
- [Figure 2 Rule Configuration](SCENARIO_IMAGES_en.md#figure-2-rule-configuration)

### Notes / Limits

This helps with message order and timing. You still need specialized
tools for low-level network analysis.

## Scenario 7 Narrowing Down a Noisy UDP Stream

### Goal

Reduce a large stream until the actual problem is still visible during a
live run.

### Initial Situation

Several parts of your system send at the same time. During a test, you
only care about the warnings and state changes from one specific area,
but you do not want to lose all broader context.

### Typical Symptoms

- the stream scrolls too fast
- warnings disappear immediately from view
- cause and effect are hard to connect in real time

### Why UDP Viewer Helps Here

With `Filter`, `Exclude`, and `Highlight`, you can condense the stream
enough to keep working live without losing the overall picture.

### Procedure

1. Connect to the full stream first.
2. Add filter rules for the relevant area.
3. Exclude known repetitive noise patterns.
4. Highlight warnings and state changes.
5. Save the focused session for later comparison.

### Expected Findings

- a much smaller and easier-to-read stream
- clearer relations between warnings and state changes
- reusable rules for similar tests later on

### Relevant UDP Viewer Functions

- `Filter`
- `Exclude`
- `Highlight`
- `SAVE`

### Figures

- [Figure 1 Main Window Overview](SCENARIO_IMAGES_en.md#figure-1-main-window-overview)
- [Figure 2 Rule Configuration](SCENARIO_IMAGES_en.md#figure-2-rule-configuration)

### Notes / Limits

Whether a large stream is still usable live often depends directly on
good rule setup.

## Scenario 8 Comparing a Normal Run with a Faulty Run

### Goal

Understand where a faulty run starts to differ from a normal one.

### Initial Situation

You have two recordings: one clean run and one with a visible fault.
The defect cannot currently be reproduced on demand, but you still want
to compare both runs in a structured way.

### Typical Symptoms

- the surrounding conditions look the same, but the result does not
- the issue is only available as a recording now
- the analysis happens well after the run finished

### Why UDP Viewer Helps Here

Replay lets you review both runs in the same workflow and jump straight
to the phases where the behavior starts to differ.

### Procedure

1. Open the known-good recording first.
2. Find the relevant phase and note the key points.
3. Open the faulty recording and replay the same interval.
4. Compare message order, warnings, and telemetry.
5. Save screenshots or notes in separate projects.

### Expected Findings

- the exact moment where the two runs diverge
- whether the fault appears first in logs, telemetry, or both
- a better basis for root-cause analysis

### Relevant UDP Viewer Functions

- `Open Log…`
- Replay
- Plot visualizer
- Logic visualizer

### Figures

- [Figure 6 Plot Visualizer Tooltip](SCENARIO_IMAGES_en.md#figure-6-plot-visualizer-tooltip)
- [Figure 8 Logic Visualizer Measurement](SCENARIO_IMAGES_en.md#figure-8-logic-visualizer-measurement)

### Notes / Limits

Replay does not reproduce the original network environment. In practice,
it is often still enough to reproduce the visible symptoms.

## Scenario 9 Detecting a Protocol Regression After a Firmware Update

### Goal

Detect whether a firmware change modified the effective UDP protocol in
a way that breaks existing evaluation.

### Initial Situation

After an update, the device still sends data. Even so, your evaluation
now shows gaps, empty plots, or implausible values.

### Typical Symptoms

- text messages still look normal
- some CSV fields stay empty or disappear
- names, order, or scaling changed silently

### Why UDP Viewer Helps Here

You can immediately see whether the problem is only in the
visualization or whether the firmware output itself no longer matches
the expected structure.

### Procedure

1. Connect to the updated firmware or open a recording from it.
2. Check the text log for protocol or version hints.
3. Open the matching visualizer configuration.
4. Confirm whether all expected fields still populate correctly.
5. Document the deviation in the project.

### Expected Findings

- whether the regression is textual, structural, or numeric
- whether only the preset needs an update
- whether the firmware output itself is no longer compatible

### Relevant UDP Viewer Functions

- `CONNECT`
- Replay
- Plot visualizer
- `PROJECT`

### Figures

- [Figure 4 Plot Visualizer Configuration](SCENARIO_IMAGES_en.md#figure-4-plot-visualizer-configuration)
- [Figure 5 Plot Visualizer Detail](SCENARIO_IMAGES_en.md#figure-5-plot-visualizer-detail)

### Notes / Limits

This is especially useful when protocol changes were not documented
completely.

## Scenario 10 Reviewing a Delivered Recording in a Reproducible Way

### Goal

Turn one saved log file into a traceable analysis case.

### Initial Situation

You receive a recording and a short problem description. The original
situation is not directly available anymore, but you still want to
review the case cleanly and hand it over if needed.

### Typical Symptoms

- the written description is short and incomplete
- the original hardware is not currently available
- several people need to understand the same case

### Why UDP Viewer Helps Here

With projects, replay, screenshots, and visualizers, one saved file
becomes a structured case again instead of remaining just an isolated
log.

### Procedure

1. Create a new project with a suitable name.
2. Copy the short summary into the project description.
3. Open the recording and replay it.
4. Activate filters and visualizers for the suspected cause.
5. Save screenshots and keep the project folder as the case package.

### Expected Findings

- a repeatable internal analysis flow
- better handover between the people involved
- a traceable package instead of a single loose log file

### Relevant UDP Viewer Functions

- `PROJECT`
- `Open Log…`
- Replay
- Screenshots
- `SAVE`

### Figures

- [Figure 3 Project Dialog](SCENARIO_IMAGES_en.md#figure-3-project-dialog)
- [Figure 1 Main Window Overview](SCENARIO_IMAGES_en.md#figure-1-main-window-overview)

### Notes / Limits

This is often the cleanest way to pass on a case that only exists as a
saved recording.
