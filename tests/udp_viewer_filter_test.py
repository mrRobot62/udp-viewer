#!/usr/bin/env python3
"""Send reproducible manual UDP Log Viewer filter tests using Python's stdlib.

Examples:
  python3 udp_viewer_filter_test.py
  python3 udp_viewer_filter_test.py --filter ADC PCF --filter-op OR
  python3 udp_viewer_filter_test.py --filter CL57TE bench --filter-op AND
  python3 udp_viewer_filter_test.py --exclude CL57TE scope --exclude-op AND
  python3 udp_viewer_filter_test.py --protocol tcp --tcp-mode fragmented
  python3 udp_viewer_filter_test.py --protocol tcp --tcp-mode batch
  python3 udp_viewer_filter_test.py --list
  python3 udp_viewer_filter_test.py --self-test

Each --filter/--exclude term represents a separate Substring slot in the viewer.
These arguments predict results only: ALL generated messages are always sent.
Use exactly the same spelling/case in the viewer. Regex and multiple terms
inside one slot are intentionally outside this prediction model.

Default matrix: all 512 subsets of nine terms, each exactly once, plus 12
readable examples. No ESP32, third-party packages or administrator rights needed.
"""

from __future__ import annotations

import argparse
import itertools
import math
import socket
import sys
import time
from datetime import datetime


TERMS = ("ADC", "PCF", "CL57TE", "bench", "scope", "DEBUG", "Heartbeat", "ERROR", "WARN")
EXAMPLES = (
    "Ready",
    "ADC value=1234",
    "PCF state=1",
    "ADC PCF value=1234 state=1",
    "CL57TE init axis=X",
    "CL57TE bench axis=X",
    "CL57TE scope axis=X",
    "CL57TE bench scope axis=X",
    "ADC DEBUG value=1234",
    "PCF Heartbeat state=1",
    "ADC ERROR timeout",
    "PCF WARN text=Temperatur_überhöht_°C_✓",
)


def make_messages(suite: str, terms: list[str] | tuple[str, ...], run_id: str) -> list[str]:
    """Build labelled examples and every subset, including no matching terms."""
    payloads = []
    if suite in ("examples", "all"):
        payloads.extend(EXAMPLES)
    if suite in ("matrix", "all"):
        for bits in itertools.product((False, True), repeat=len(terms)):
            selected = [term for term, present in zip(terms, bits) if present]
            payloads.append(" ".join(selected) if selected else "neutral")
    return [f"[MANUAL] run={run_id} id={index:04d} {payload}" for index, payload in enumerate(payloads, 1)]


def matches(line: str, terms: list[str], operator: str, empty: bool) -> bool:
    """Evaluate separate literal substring slots with explicit empty semantics."""
    if not terms:
        return empty
    hits = (term in line for term in terms)
    return all(hits) if operator == "AND" else any(hits)


def accepted(line: str, args: argparse.Namespace) -> bool:
    """Predict inclusion followed by exclusion; exclusions take precedence."""
    return matches(line, args.filter, args.filter_op, True) and not matches(
        line, args.exclude, args.exclude_op, False
    )


def positive_port(value: str) -> int:
    """Validate an ordinary UDP/TCP destination port."""
    port = int(value)
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("Port muss zwischen 1 und 65535 liegen.")
    return port


def self_test() -> None:
    """Verify generation and the AND/OR prediction without network access."""
    messages = make_messages("matrix", TERMS, "check")
    assert len(messages) == 512
    assert sum(matches(line, ["ADC", "PCF"], "OR", True) for line in messages) == 384
    assert sum(matches(line, ["ADC", "PCF"], "AND", True) for line in messages) == 128
    assert sum(not matches(line, ["DEBUG", "Heartbeat"], "OR", False) for line in messages) == 128
    assert sum(not matches(line, ["DEBUG", "Heartbeat"], "AND", False) for line in messages) == 384
    for mode in ("AND", "OR"):
        assert matches("neutral", [], mode, True)
        assert not matches("neutral", [], mode, False)
    print("Selbsttest erfolgreich; keine Daten versendet.")


def main() -> int:
    """Send the complete suite and print expected filter counts."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", default="127.0.0.1", help="Viewer-IP; Standard: 127.0.0.1")
    parser.add_argument("--port", type=positive_port, default=10514)
    parser.add_argument("--protocol", choices=("udp", "tcp"), default="udp")
    parser.add_argument("--broadcast", action="store_true", help="UDP an 255.255.255.255 senden")
    parser.add_argument("--suite", choices=("examples", "matrix", "all"), default="all")
    parser.add_argument("--terms", nargs="+", default=list(TERMS), help="Begriffe der Kombinationsmatrix (maximal 10)")
    parser.add_argument("--interval", type=float, default=0.05, help="Pause zwischen Sendungen in Sekunden")
    parser.add_argument("--repeat", type=int, default=1, help="Anzahl Durchläufe innerhalb derselben Verbindung")
    parser.add_argument("--tcp-mode", choices=("lines", "fragmented", "batch"), default="lines")
    parser.add_argument("--line-ending", choices=("lf", "crlf", "none"), default="lf", help="none ist nur für UDP erlaubt")
    parser.add_argument("--filter", nargs="*", default=[], help="Include-Slots zur Vorhersage, kein Sendefilter")
    parser.add_argument("--filter-op", choices=("AND", "OR"), default="AND")
    parser.add_argument("--exclude", nargs="*", default=[], help="Exclude-Slots zur Vorhersage, kein Sendefilter")
    parser.add_argument("--exclude-op", choices=("AND", "OR"), default="OR")
    parser.add_argument("--list", action="store_true", help="Testzeilen und Vorhersage anzeigen; nichts versenden")
    parser.add_argument("--self-test", action="store_true", help="Lokale Generierungsprüfung ohne Netzwerk")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not math.isfinite(args.interval) or args.interval < 0 or args.repeat < 1:
        parser.error("interval muss endlich und >= 0 sein; repeat muss >= 1 sein.")
    if len(args.terms) > 10 or len(set(args.terms)) != len(args.terms) or any(not term.strip() for term in args.terms):
        parser.error("Bitte maximal 10 verschiedene, nichtleere Matrix-Begriffe angeben.")
    if args.protocol == "tcp" and (args.broadcast or args.line_ending == "none"):
        parser.error("TCP benötigt eine konkrete Zieladresse und LF/CRLF.")
    if args.host == "0.0.0.0":
        parser.error("0.0.0.0 ist eine Bind-Adresse, keine Zieladresse. Nutze 127.0.0.1 oder die Viewer-IP.")
    run_id = datetime.now().strftime("%H%M%S")
    messages = make_messages(args.suite, args.terms, run_id)
    count = sum(accepted(line, args) for line in messages)
    target = "255.255.255.255" if args.broadcast else args.host
    print(f"Ziel: {args.protocol.upper()} {target}:{args.port}; Lauf: {run_id}", flush=True)
    print(f"Pro Durchlauf: {len(messages)} Nachrichten; erwartete Filtertreffer: {count}", flush=True)
    print(f"Gesamt: {len(messages) * args.repeat} Nachrichten; erwartete Filtertreffer: {count * args.repeat}", flush=True)
    print("Vorhersage gilt nur bei identischen Substring-Slots im Viewer; alle Nachrichten werden gesendet.", flush=True)
    if args.list:
        for line in messages:
            print(f"{'ANZEIGEN' if accepted(line, args) else 'AUSBLENDEN'} {line}")
        return 0
    ending = {"lf": "\n", "crlf": "\r\n", "none": ""}[args.line_ending]
    payloads = [(line + ending).encode("utf-8") for line in messages]
    if any(len(payload) > 65507 for payload in payloads):
        parser.error("Eine Testnachricht ist zu groß; kürzere Matrix-Begriffe verwenden.")
    sent = 0
    try:
        kind = socket.SOCK_DGRAM if args.protocol == "udp" else socket.SOCK_STREAM
        with socket.socket(socket.AF_INET, kind) as sock:
            sock.settimeout(5)
            if args.protocol == "tcp":
                sock.connect((target, args.port))
            elif args.broadcast:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            for cycle in range(args.repeat):
                if args.protocol == "tcp" and args.tcp_mode == "batch":
                    sock.sendall(b"".join(payloads))
                    sent += len(payloads)
                    time.sleep(args.interval)
                else:
                    for payload in payloads:
                        if args.protocol == "udp":
                            sock.sendto(payload, (target, args.port))
                        elif args.tcp_mode == "fragmented":
                            # Split a multibyte UTF-8 character when available.
                            cut = next((i + 1 for i, byte in enumerate(payload) if byte >= 0xC0), max(1, len(payload) // 2))
                            sock.sendall(payload[:cut])
                            time.sleep(0.01)
                            sock.sendall(payload[cut:])
                        else:
                            sock.sendall(payload)
                        sent += 1
                        time.sleep(args.interval)
                print(f"Durchlauf {cycle + 1}/{args.repeat} abgeschlossen.", flush=True)
    except (OSError, KeyboardInterrupt) as error:
        print(f"Abgebrochen nach {sent} vollständig versendeten Nachrichten: {error}", file=sys.stderr)
        return 1
    print(f"Fertig: {sent} Nachrichten an das Betriebssystem übergeben. Empfang im Viewer prüfen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
