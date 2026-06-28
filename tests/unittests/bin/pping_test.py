from unittest.mock import MagicMock, patch

from nav.bin.pping import Pinger


class TestPingerMainOverrun:
    """Tests for Pinger.main()'s post-iteration sleep computation."""

    def test_when_check_overruns_then_main_should_sleep_zero(self):
        pinger = _make_pinger(looptime=20, elapsedtime=24179.267)
        with patch("nav.bin.pping.sleep") as mock_sleep:
            pinger.main()
        mock_sleep.assert_called_once_with(0.0)

    def test_when_check_finishes_quickly_then_main_should_sleep_remaining_time(self):
        pinger = _make_pinger(looptime=20, elapsedtime=5.0)
        with patch("nav.bin.pping.sleep") as mock_sleep:
            pinger.main()
        mock_sleep.assert_called_once_with(15.0)


def _make_pinger(looptime, elapsedtime):
    """Build a Pinger with just enough attributes to run main() for one
    iteration. Skips the real __init__ (which opens a DB, parses config and
    installs signal handlers) by going through __new__.
    """
    pinger = Pinger.__new__(Pinger)
    pinger._isrunning = 1
    pinger._looptime = looptime
    pinger.netboxmap = {}
    pinger.down = []
    pinger.db = MagicMock()
    pinger.update_host_list = MagicMock()
    pinger.generate_events = MagicMock()

    def fake_ping():
        pinger._isrunning = 0
        return elapsedtime

    pinger.pinger = MagicMock()
    pinger.pinger.ping.side_effect = fake_ping
    return pinger
