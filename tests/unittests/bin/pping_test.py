from unittest.mock import MagicMock, patch

from nav.bin.pping import Pinger
from nav.statemon.event import Event


class TestPingerMainOverrun:
    """Tests for Pinger.main()'s post-iteration sleep computation."""

    def test_when_check_overruns_then_main_should_sleep_zero(self):
        pinger = _make_main_pinger(looptime=20, elapsedtime=24179.267)
        with patch("nav.bin.pping.sleep") as mock_sleep:
            pinger.main()
        mock_sleep.assert_called_once_with(0.0)

    def test_when_check_finishes_quickly_then_main_should_sleep_remaining_time(self):
        pinger = _make_main_pinger(looptime=20, elapsedtime=5.0)
        with patch("nav.bin.pping.sleep") as mock_sleep:
            pinger.main()
        mock_sleep.assert_called_once_with(15.0)


class TestPingerReconcileWithDatabase:
    """Tests for syncing pping's internal state with netbox.up"""

    def test_when_db_says_down_but_box_answers_then_generate_events_should_post_up(  # noqa: E501
        self,
    ):
        pinger = _make_pinger()
        _run_cycle(pinger, db_up="y", rtt=0.01)
        _run_cycle(pinger, db_up="n", rtt=0.01)
        assert _posted_states(pinger) == [Event.UP]

    def test_when_db_says_shadow_but_box_answers_then_generate_events_should_post_up(  # noqa: E501
        self,
    ):
        pinger = _make_pinger()
        _run_cycle(pinger, db_up="y", rtt=0.01)
        _run_cycle(pinger, db_up="s", rtt=0.01)
        assert _posted_states(pinger) == [Event.UP]

    def test_when_db_stays_down_and_box_answers_then_generate_events_should_post_up_until_db_agrees(  # noqa: E501
        self,
    ):
        pinger = _make_pinger()
        _run_cycle(pinger, db_up="y", rtt=0.01)
        _run_cycle(pinger, db_up="n", rtt=0.01)
        _run_cycle(pinger, db_up="n", rtt=0.01)
        _run_cycle(pinger, db_up="y", rtt=0.01)
        assert _posted_states(pinger) == [Event.UP, Event.UP]

    def test_when_db_says_down_and_box_is_silent_then_generate_events_should_post_nothing(  # noqa: E501
        self,
    ):
        pinger = _make_pinger()
        _run_cycle(pinger, db_up="y", rtt=0.01)
        _run_cycle(pinger, db_up="n", rtt=-1)
        assert _posted_states(pinger) == []

    def test_when_db_says_up_but_box_is_down_then_generate_events_should_post_nothing(  # noqa: E501
        self,
    ):
        pinger = _make_pinger()
        _run_cycle(pinger, db_up="n", rtt=-1)
        _run_cycle(pinger, db_up="y", rtt=-1)
        assert _posted_states(pinger) == []

    def test_when_new_box_is_down_in_db_and_silent_then_generate_events_should_post_nothing(  # noqa: E501
        self,
    ):
        pinger = _make_pinger()
        _run_cycle(pinger, db_up="n", rtt=-1)
        assert _posted_states(pinger) == []

    def test_when_box_stays_down_in_db_then_update_host_list_should_not_duplicate_it_in_down(  # noqa: E501
        self,
    ):
        pinger = _make_pinger()
        _run_cycle(pinger, db_up="n", rtt=-1)
        _run_cycle(pinger, db_up="n", rtt=-1)
        pinger.update_host_list()
        assert pinger.down.count(1) == 1


def _make_pinger(nrping=3):
    """
    Build a bare Pinger. Skips the real __init__ (which opens a DB, parses
    config and installs signal handlers) by going through __new__.
    """
    pinger = Pinger.__new__(Pinger)
    pinger.config = {}
    pinger._nrping = nrping
    pinger.netboxmap = {}
    pinger.down = []
    pinger.replies = {}
    pinger.ip_to_netboxid = {}
    pinger.db = MagicMock()
    pinger.pinger = MagicMock()
    return pinger


def _make_main_pinger(looptime, elapsedtime):
    """
    Build a Pinger with just enough attributes to run main() for one iteration.
    """
    pinger = _make_pinger()
    pinger._isrunning = 1
    pinger._looptime = looptime
    pinger.update_host_list = MagicMock()
    pinger.generate_events = MagicMock()

    def fake_ping():
        pinger._isrunning = 0
        return elapsedtime

    pinger.pinger.ping.side_effect = fake_ping
    return pinger


def _run_cycle(pinger, db_up, rtt, netboxid=1, ip="10.0.0.1"):
    """
    Run one pping cycle with the box's netbox.up set to db_up and its ping
    reply set to rtt (-1 means no reply).
    """
    pinger.db.hosts_to_ping.return_value = [(netboxid, "box", ip, db_up)]
    pinger.pinger.results.return_value = [(ip, rtt)]
    with patch("nav.bin.pping.statistics"):
        pinger.update_host_list()
        pinger.generate_events()


def _posted_states(pinger):
    return [call.args[0].status for call in pinger.db.new_event.call_args_list]
