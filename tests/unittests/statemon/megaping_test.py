import socket
from unittest.mock import MagicMock, Mock, patch

from nav.statemon.megaping import Host, MegaPing


class TestMegaPingResults:
    """Tests for MegaPing.results()"""

    def test_when_host_reply_is_none_then_results_should_return_minus_one(self):
        megaping = _megaping_with_host_reply(None)
        assert megaping.results() == [("127.0.0.1", -1)]

    def test_when_host_reply_is_zero_then_results_should_return_zero(self):
        megaping = _megaping_with_host_reply(0.0)
        assert megaping.results() == [("127.0.0.1", 0.0)]

    def test_when_host_reply_is_positive_then_results_should_return_that_value(self):
        megaping = _megaping_with_host_reply(0.001)
        assert megaping.results() == [("127.0.0.1", 0.001)]


class TestMegaPingHeaderStripping:
    """Verifies that MegaPing records the right IPv4 header offset.

    With SOCK_RAW the kernel hands us the 20-byte IP header before the ICMP
    datagram. With SOCK_DGRAM/IPPROTO_ICMP the kernel strips it for us. The
    receive loop slices ``raw_pong`` by this offset before parsing.
    """

    def test_when_v4_socket_is_raw_then_header_len_should_be_20(self):
        mp = _make_megaping(v4_kind=socket.SOCK_RAW)
        assert mp._sock4_header_len == 20

    def test_when_v4_socket_is_dgram_then_header_len_should_be_0(self):
        mp = _make_megaping(v4_kind=socket.SOCK_DGRAM)
        assert mp._sock4_header_len == 0


def _megaping_with_host_reply(reply):
    sockets = (MagicMock(), MagicMock())
    megaping = MegaPing(sockets=sockets, conf={})
    host = Host("127.0.0.1")
    host.reply = reply
    megaping._hosts = {host.ip: host}
    return megaping


def _make_megaping(v4_kind):
    sockets = [_make_socket_mock(socket.SOCK_RAW), _make_socket_mock(v4_kind)]
    with patch("nav.statemon.megaping.config.pingconf", return_value={}):
        return MegaPing(sockets=sockets)


def _make_socket_mock(kind):
    sock = Mock(spec=socket.socket)
    sock.type = kind
    return sock
