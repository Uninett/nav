from unittest.mock import MagicMock

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


def _megaping_with_host_reply(reply):
    sockets = (MagicMock(), MagicMock())
    megaping = MegaPing(sockets=sockets, conf={})
    host = Host("127.0.0.1")
    host.reply = reply
    megaping._hosts = {host.ip: host}
    return megaping
