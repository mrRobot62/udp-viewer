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
-   Debugging embedded systems without USB connection (important if your are working **in 230V environments!**)
-   Real-time log analysis during hardware testing
-   Field diagnostics and remote troubleshooting

------------------------------------------------------------------------

## Screenshot
### Main screen (no highlighting)
<img width="1100" height="785" alt="image" src="https://github.com/user-attachments/assets/1d86de14-ef78-48fb-9b06-0868c29e1b72" />

### Highlighting
<img width="1100" height="785" alt="image" src="https://github.com/user-attachments/assets/6423b809-f52e-462a-8957-b17a9840f6af" />

### Filter ajustment
<img width="232" height="387" alt="image" src="https://github.com/user-attachments/assets/56fb3ab1-fdb6-46e6-98d6-4c1e933cd127" />

### Saving/Loading logfiles
<img width="963" height="213" alt="image" src="https://github.com/user-attachments/assets/1dd140b2-8a6a-467e-9dd3-c9728ab3d86c" />

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

Bernd Klein (aka LunaX)
