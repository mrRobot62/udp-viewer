from __future__ import annotations

import errno
import select
import socket
import threading
from typing import List, Optional

from PyQt5.QtCore import QThread, pyqtSignal


class UdpListenerThread(QThread):
    """
    Background UDP listener (non-blocking, thread-based).

    Important:
    - stop() closes the socket to unblock select()/recvfrom().
    - Those operations may raise EBADF (Errno 9) during shutdown.
      This must NOT be treated as an error.
    """

    line_received = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    error = pyqtSignal(str)
    rx_stats = pyqtSignal(int, int)  # packets, lines

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
        # Closing the socket will unblock select()/recvfrom().
        if self._sock is not None:
            try:
                self._sock.close()
            except Exception:
                pass

    @staticmethod
    def _split_lines(text: str) -> List[str]:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        parts = text.split("\n")
        return [p for p in parts if p.strip() != ""]

    @staticmethod
    def _is_ebadf(e: BaseException) -> bool:
        if isinstance(e, OSError):
            return getattr(e, "errno", None) == errno.EBADF
        return False

    def run(self) -> None:
        sock: Optional[socket.socket] = None
        try:
            self.status_changed.emit(f"Binding UDP {self._bind_ip}:{self._port} ...")

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock = sock

            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self._bind_ip, self._port))
            sock.setblocking(False)

            self.status_changed.emit(f"Listening UDP {self._bind_ip}:{self._port}")

            while not self._stop_evt.is_set():
                try:
                    rlist, _, _ = select.select([sock], [], [], 0.10)
                except (OSError, ValueError) as e:
                    # During shutdown the socket may be closed -> EBADF/ValueError.
                    if self._stop_evt.is_set() or self._is_ebadf(e):
                        break
                    self.error.emit(f"select failed: {e}")
                    break

                if not rlist:
                    continue

                try:
                    data, _addr = sock.recvfrom(65535)
                except OSError as e:
                    # During shutdown: EBADF or similar -> exit silently
                    if self._stop_evt.is_set() or getattr(e, "errno", None) in (errno.EBADF, errno.EINVAL):
                        break
                    self.error.emit(f"recvfrom failed: {e}")
                    continue
                except Exception as e:
                    if self._stop_evt.is_set():
                        break
                    self.error.emit(f"recvfrom failed: {e}")
                    continue

                self._packets += 1

                try:
                    text = data.decode("utf-8", errors="replace")
                except Exception:
                    text = repr(data)

                lines = self._split_lines(text)
                self._lines += len(lines)

                for line in lines:
                    self.line_received.emit(line)

                self.rx_stats.emit(self._packets, self._lines)

        except Exception as e:
            # If stop was requested, do not report shutdown noise as error
            if not self._stop_evt.is_set():
                self.error.emit(f"UDP listener error: {e}")
        finally:
            try:
                if sock is not None:
                    sock.close()
            except Exception:
                pass
            self._sock = None
            self.status_changed.emit("Listener stopped")