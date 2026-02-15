from __future__ import annotations

import select
import socket
import threading
from typing import List, Optional, Tuple

from PyQt5.QtCore import QThread, pyqtSignal


class UdpListenerThread(QThread):
    """
    Background UDP listener (non-blocking, thread-based).

    - Binds to (bind_ip, port)
    - Receives UDP datagrams
    - Decodes UTF-8 (with replacement)
    - Splits into lines
    - Emits one signal per line

    Notes:
    - QThread is used so UI stays responsive.
    - We use select() with a short timeout so stop requests are handled quickly.
    """

    line_received = pyqtSignal(str)
    status_changed = pyqtSignal(str)      # human-readable status
    error = pyqtSignal(str)               # human-readable error
    rx_stats = pyqtSignal(int, int)       # packets, lines

    def __init__(self, bind_ip: str, port: int, *, parent=None) -> None:
        super().__init__(parent)
        self._bind_ip = bind_ip
        self._port = port

        self._stop_evt = threading.Event()
        self._sock: Optional[socket.socket] = None

        self._packets = 0
        self._lines = 0

    def stop(self) -> None:
        self._stop_evt.set()
        # Closing the socket will also break select()/recv
        if self._sock is not None:
            try:
                self._sock.close()
            except Exception:
                pass

    @staticmethod
    def _split_lines(text: str) -> List[str]:
        # Normalize CRLF/CR -> LF, then split
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        parts = text.split("\n")
        # Keep non-empty lines only (UDP payloads often end with '\n')
        return [p for p in parts if p.strip() != ""]

    def run(self) -> None:
        try:
            self.status_changed.emit(f"Binding UDP {self._bind_ip}:{self._port} ...")

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock = sock

            # Allow quick re-bind after restart
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind
            sock.bind((self._bind_ip, self._port))

            # Non-blocking mode
            sock.setblocking(False)

            self.status_changed.emit(f"Listening UDP {self._bind_ip}:{self._port}")

            while not self._stop_evt.is_set():
                # select timeout: short so stop() reacts quickly
                rlist, _, _ = select.select([sock], [], [], 0.10)
                if not rlist:
                    continue

                try:
                    data, addr = sock.recvfrom(65535)
                except OSError:
                    # likely closed during stop()
                    break
                except Exception as e:
                    self.error.emit(f"recvfrom failed: {e}")
                    continue

                self._packets += 1

                try:
                    text = data.decode("utf-8", errors="replace")
                except Exception:
                    text = repr(data)

                lines = self._split_lines(text)
                self._lines += len(lines)

                # Emit per line (UI will batch via queue)
                for line in lines:
                    self.line_received.emit(line)

                self.rx_stats.emit(self._packets, self._lines)

        except Exception as e:
            self.error.emit(f"UDP listener error: {e}")
        finally:
            try:
                if self._sock is not None:
                    self._sock.close()
            except Exception:
                pass
            self._sock = None
            self.status_changed.emit("Listener stopped")