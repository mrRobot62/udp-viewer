"""Check that TCP status advertises usable local endpoints, not wildcard IPs."""

from types import SimpleNamespace

from PyQt5.QtNetwork import QHostAddress, QNetworkInterface

from udp_log_viewer.tcp_listener import tcp_listening_status


def interface(*addresses, active=True):
    """Provide a deterministic interface snapshot without real network access."""
    flags = QNetworkInterface.IsUp | QNetworkInterface.IsRunning if active else 0
    return SimpleNamespace(
        flags=lambda: flags,
        addressEntries=lambda: [SimpleNamespace(ip=lambda value=value: QHostAddress(value)) for value in addresses],
    )


def test_wildcard_lists_active_ipv4_destinations(monkeypatch):
    """List all active IPv4 addresses once and exclude inactive/IPv6 addresses."""
    monkeypatch.setattr(QNetworkInterface, "allInterfaces", lambda: [
        interface("192.168.1.50", "fe80::1"),
        interface("10.0.0.5", "192.168.1.50", "127.0.0.1"),
        interface("172.16.1.2", active=False),
    ])
    status = tcp_listening_status("0.0.0.0", 10514)
    assert "192.168.1.50:10514" in status
    assert "10.0.0.5:10514" in status
    assert status.count("192.168.1.50") == 1
    assert all(address not in status for address in ("0.0.0.0", "fe80", "172.16", "127.0.0.1"))


def test_explicit_bind_advertises_only_that_address():
    """A socket bound to one interface must not advertise other interfaces."""
    assert "connect sender to: 192.168.1.50:10514" in tcp_listening_status("192.168.1.50", 10514)


def test_loopback_is_labelled_local_only():
    """Make loopback scope explicit to users configuring remote senders."""
    assert "127.0.0.1:10514 (this computer only)" in tcp_listening_status("127.0.0.1", 10514)


def test_no_lan_address_does_not_invent_a_remote_destination(monkeypatch):
    """Provide a clearly labelled local endpoint when no LAN address exists."""
    monkeypatch.setattr(QNetworkInterface, "allInterfaces", lambda: [])
    status = tcp_listening_status("0.0.0.0", 10514)
    assert "127.0.0.1:10514" in status
    assert "no active LAN IPv4 address" in status
    assert "0.0.0.0" not in status
