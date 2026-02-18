# UDP Log Viewer

Lightweight, real-time UDP log viewer designed for embedded systems such
as ESP32 devices.

This tool provides a fast, reliable, and distraction-free interface for
receiving, viewing, filtering, and analyzing plain-text UDP log
messages.

------------------------------------------------------------------------

## Overview

UDP Log Viewer is a cross-platform desktop application built with Python
and PyQt5.\
It is optimized for real-time monitoring of embedded firmware logs
transmitted over WiFi.

Typical use cases:

-   Monitoring ESP32 firmware logs over UDP
-   Debugging embedded systems without USB connection
-   Real-time log analysis during hardware testing
-   Field diagnostics and remote troubleshooting

------------------------------------------------------------------------

## Screenshot

```{=html}
<!-- Replace with actual screenshots -->
```
![Main Window](docs/screenshots/main_window.png)

![Filter and Highlight](docs/screenshots/filter_highlight.png)

------------------------------------------------------------------------

## Features

-   Real-time UDP log reception
-   Lightweight and fast UI
-   Highlight, filter, and exclude rules
-   Timestamp support
-   Log saving to file
-   Pause and resume functionality
-   Simulation and replay support
-   Cross-platform (macOS, Windows, Linux)

------------------------------------------------------------------------

## Installation

Prebuilt binaries will be available via GitHub Releases.

Alternatively, run from source:

``` bash
python -m venv venv
source venv/bin/activate
pip install -e .
udp-log-viewer
```

------------------------------------------------------------------------

## Quick Start (User Manual)

### Step 1 -- Start the Application

Launch the application:

``` bash
udp-log-viewer
```

------------------------------------------------------------------------

### Step 2 -- Configure Log Source

Ensure your device sends UDP log messages to the computer's IP address
and configured port.

Example ESP32:

``` c
sendto(sock, log_line, len, 0, &dest_addr, sizeof(dest_addr));
```

------------------------------------------------------------------------

### Step 3 -- View Logs

Incoming log messages appear in real time in the main window.

You can:

-   Scroll through logs
-   Pause/resume logging
-   Save logs to file

------------------------------------------------------------------------

### Step 4 -- Use Filters and Highlights

Create rules to:

-   Highlight important messages
-   Filter specific components
-   Exclude unwanted log noise

------------------------------------------------------------------------

## Project Structure

    src/udp_log_viewer/
    scripts/
    packaging/
    data/
    doc/

------------------------------------------------------------------------

## Development

Bootstrap developer environment:

``` bash
./scripts/bootstrap_macos_linux.sh
```

Run:

``` bash
./scripts/dev_run.sh
```

Test:

``` bash
./scripts/dev_test.sh
```

------------------------------------------------------------------------

## Roadmap

Planned future improvements:

-   Advanced filtering engine
-   Plugin system
-   Extended export formats
-   Improved UI customization

------------------------------------------------------------------------

## License

License to be defined.

------------------------------------------------------------------------

## Author

Bernhard Klein
