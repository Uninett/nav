import errno
import signal

from unittest.mock import Mock, patch

import pytest

from nav.startstop import DaemonService


class FakeClock:
    """A deterministic replacement for time.monotonic/time.sleep so that the
    stop() grace loops can be exercised without real waiting."""

    def __init__(self):
        self.now = 1000.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


@pytest.fixture
def clock(monkeypatch):
    fake = FakeClock()
    monkeypatch.setattr("nav.startstop.time.monotonic", fake.monotonic)
    monkeypatch.setattr("nav.startstop.time.sleep", fake.sleep)
    return fake


def make_service():
    service = DaemonService(
        "ipdevpoll", {"command": "ipdevpolld", "description": "test"}
    )
    service.get_pid = Mock(return_value=1234)
    return service


class TestDaemonServiceStop:
    def test_returns_false_when_not_running(self):
        service = make_service()
        service.is_up = Mock(return_value=False)
        assert service.stop() is False

    def test_when_process_exits_on_sigterm_then_does_not_escalate_to_sigkill(
        self, clock
    ):
        service = make_service()
        # up on the initial check, gone right after SIGTERM
        service.is_up = Mock(side_effect=[True, False])
        with (
            patch("nav.startstop.os.getpgid", return_value=1234),
            patch("nav.startstop.os.killpg") as killpg,
        ):
            assert service.stop() is True

        signals_sent = [call.args[1] for call in killpg.call_args_list]
        assert signals_sent == [signal.SIGTERM]

    def test_escalates_to_sigkill_when_sigterm_ignored(self, clock):
        service = make_service()
        sent = []

        def fake_killpg(_pgid, sig):
            sent.append(sig)

        def fake_is_up(pid=None, silent=False):
            # Stays up until SIGKILL is delivered
            return signal.SIGKILL not in sent

        service.is_up = fake_is_up
        with (
            patch("nav.startstop.os.getpgid", return_value=1234),
            patch("nav.startstop.os.killpg", side_effect=fake_killpg),
        ):
            assert service.stop() is True

        assert signal.SIGTERM in sent
        assert signal.SIGKILL in sent
        assert sent.index(signal.SIGTERM) < sent.index(signal.SIGKILL)


class TestSignalProcessGroup:
    def test_returns_false_when_process_already_gone(self):
        with patch("nav.startstop.os.getpgid", side_effect=ProcessLookupError):
            assert DaemonService._signal_process_group(1234, signal.SIGTERM) is False

    def test_it_should_signal_whole_process_group(self):
        with (
            patch("nav.startstop.os.getpgid", return_value=4321),
            patch("nav.startstop.os.killpg") as killpg,
        ):
            assert DaemonService._signal_process_group(1234, signal.SIGKILL) is True
        killpg.assert_called_once_with(4321, signal.SIGKILL)

    def test_falls_back_to_single_process_when_not_group_leader(self):
        with (
            patch("nav.startstop.os.getpgid", return_value=1234),
            patch("nav.startstop.os.killpg", side_effect=OSError(errno.EPERM, "nope")),
            patch("nav.startstop.os.kill") as kill,
        ):
            assert DaemonService._signal_process_group(1234, signal.SIGTERM) is True
        kill.assert_called_once_with(1234, signal.SIGTERM)
