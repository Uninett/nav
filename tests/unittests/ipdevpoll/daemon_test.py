from unittest.mock import Mock, patch

from nav.ipdevpoll.daemon import IPDevPollProcess


def make_process():
    return IPDevPollProcess(Mock())


class TestShutdownWatchdog:
    def test_when_sigterm_received_then_shutdown_watchdog_is_armed(self):
        process = make_process()
        with patch("nav.ipdevpoll.daemon.threading.Timer") as timer:
            process._arm_shutdown_watchdog()
        timer.assert_called_once()
        timer.return_value.start.assert_called_once()
        assert timer.return_value.daemon is True

    def test_it_should_not_arm_the_watchdog_more_than_once(self):
        process = make_process()
        with patch("nav.ipdevpoll.daemon.threading.Timer") as timer:
            process._arm_shutdown_watchdog()
            process._arm_shutdown_watchdog()
        timer.assert_called_once()

    def test_when_shutdown_completes_then_watchdog_is_cancelled(self):
        process = make_process()
        with patch("nav.ipdevpoll.daemon.threading.Timer") as timer:
            process._arm_shutdown_watchdog()
            process._cancel_shutdown_watchdog()
        timer.return_value.cancel.assert_called_once()
        assert process._shutdown_watchdog is None

    def test_it_should_force_exit_when_watchdog_fires(self):
        process = make_process()
        with patch("nav.ipdevpoll.daemon.threading.Timer") as timer:
            process._arm_shutdown_watchdog()
        # The function handed to the Timer must forcibly terminate the process
        force_exit = timer.call_args.args[1]
        with patch("nav.ipdevpoll.daemon.os._exit") as os_exit:
            force_exit()
        os_exit.assert_called_once_with(1)
