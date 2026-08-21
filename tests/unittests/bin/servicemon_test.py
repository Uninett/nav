import itertools
from unittest.mock import MagicMock, patch

from nav.bin.servicemon import Controller


class TestControllerMainSleep:
    """Tests for Controller.main()'s post-enqueue sleep computation."""

    def test_when_enqueue_overruns_then_main_should_sleep_zero(self):
        controller = _make_controller(looptime=60)
        # Three calls of interest in main(): loop start, first-overrun check,
        # second-overrun check. Logging incidentally also calls time.time(),
        # so keep yielding the last value afterwards.
        # 24179 is chosen so that the buggy `wait %= looptime` would compute
        # 1.0 (since -24119 % 60 == 1) and not coincidentally agree with the
        # clamp-to-zero fix.
        fake_clock = itertools.chain([0.0, 10.0, 24179.0], itertools.repeat(24179.0))
        with (
            patch("nav.bin.servicemon.sleep") as mock_sleep,
            patch("nav.bin.servicemon.time.time", side_effect=fake_clock) as mock_time,
        ):
            mock_sleep.side_effect = lambda *_: setattr(controller, "_isrunning", 0)
            controller.main()
        mock_sleep.assert_called_once_with(0.0)
        # Guard against a future refactor silently changing the time.time()
        # call ordering: we expect at least the three calls listed above.
        assert mock_time.call_count >= 3

    def test_when_enqueue_finishes_quickly_then_main_should_sleep_remaining_time(self):
        controller = _make_controller(looptime=60)
        # Loop start at t=0, first-overrun check at t=5 (wait=55, positive),
        # second-overrun check at t=10 (wait=50, positive) -> sleep(50).
        fake_clock = itertools.chain([0.0, 5.0, 10.0], itertools.repeat(10.0))
        with (
            patch("nav.bin.servicemon.sleep") as mock_sleep,
            patch("nav.bin.servicemon.time.time", side_effect=fake_clock) as mock_time,
        ):
            mock_sleep.side_effect = lambda *_: setattr(controller, "_isrunning", 0)
            controller.main()
        mock_sleep.assert_called_once_with(50.0)
        assert mock_time.call_count >= 3


def _make_controller(looptime):
    """Build a Controller with just enough attributes to run main() for one
    iteration. Skips the real __init__ by going through __new__ so we don't
    open a DB, parse config, or install signal handlers.
    """
    controller = Controller.__new__(Controller)
    controller._isrunning = 1
    controller._looptime = looptime
    controller._checkers = []
    controller.db = MagicMock()
    controller._runqueue = MagicMock()
    controller.get_checkers = MagicMock()
    return controller
