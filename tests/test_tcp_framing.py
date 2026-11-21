"""Exercise stream boundaries independently of sockets and Qt scheduling."""

import pytest

from udp_log_viewer.tcp_listener import TcpLineBuffer


def test_fragmented_utf8_and_crlf() -> None:
    """Keep multibyte characters and CRLF intact across reads."""
    buffer = TcpLineBuffer()
    assert list(buffer.feed(b"Gr\xc3")) == []
    assert list(buffer.feed(b"\xbc\xc3\x9fe\r")) == []
    assert list(buffer.feed(b"\nnext\nlast")) == ["Grüße", "next"]
    assert list(buffer.feed(b" line\n")) == ["last line"]


def test_blank_lines_and_invalid_utf8() -> None:
    """Ignore blank messages and replace malformed UTF-8."""
    buffer = TcpLineBuffer()
    assert list(buffer.feed(b"\n \t\r\nvalid\xff\n")) == ["valid�"]


@pytest.mark.parametrize("ending", [b"\n", b"\r\n"])
def test_message_limit_excludes_delimiter(ending: bytes) -> None:
    """Accept payloads exactly at the limit with either delimiter."""
    buffer = TcpLineBuffer(4)
    assert list(buffer.feed(b"1234" + ending)) == ["1234"]


def test_split_crlf_at_limit() -> None:
    """Allow one pending CR at the maximum payload length."""
    buffer = TcpLineBuffer(4)
    assert list(buffer.feed(b"1234\r")) == []
    assert list(buffer.feed(b"\n")) == ["1234"]


@pytest.mark.parametrize("data", [b"12345", b"12345\n", b"12345\r\n"])
def test_oversized_message_clears_buffer(data: bytes) -> None:
    """Reject oversized terminated and unterminated messages."""
    buffer = TcpLineBuffer(4)
    with pytest.raises(ValueError, match="exceeds"):
        list(buffer.feed(data))
    assert buffer.clear() == 0
    assert list(buffer.feed(b"ok\n")) == ["ok"]


def test_pending_cr_is_payload_when_not_followed_by_lf() -> None:
    """Do not let a CR bypass the size limit for subsequent payload."""
    buffer = TcpLineBuffer(4)
    list(buffer.feed(b"1234\r"))
    with pytest.raises(ValueError, match="exceeds"):
        list(buffer.feed(b"x"))


def test_complete_lines_precede_oversize_error() -> None:
    """Deliver valid preceding messages even if a later one is too large."""
    buffer = TcpLineBuffer(4)
    lines = buffer.feed(b"ok\n12345\n")
    assert next(lines) == "ok"
    with pytest.raises(ValueError, match="exceeds"):
        next(lines)


def test_clear_discards_partial_message_before_reconnect() -> None:
    """Never concatenate partial messages from different senders."""
    buffer = TcpLineBuffer()
    assert list(buffer.feed(b"old\xc3")) == []
    assert buffer.clear() == 4
    assert list(buffer.feed(b"new\n")) == ["new"]


def test_limit_applies_per_message_not_per_read() -> None:
    """Accept a read containing many individually bounded messages."""
    assert list(TcpLineBuffer(2).feed(b"ab\n" * 100)) == ["ab"] * 100
