import signal
from unittest.mock import patch, Mock

import pytest
import pytest_twisted
import twisted.internet.defer

from nav.ipdevpoll.pool import Worker


class TestWorker:
    @pytest.mark.twisted
    @pytest_twisted.inlineCallbacks
    def test_mock_process_should_not_respond_to_ping(self):
        worker = Worker(pool=None, threadpoolsize=0, max_jobs=5)
        worker.process = Mock()
        ping_response = yield worker.responds_to_ping()
        assert not ping_response  # Mock process cannot respond

    @pytest.mark.twisted
    @pytest_twisted.inlineCallbacks
    def test_unresponsive_worker_should_be_euthanized(self):
        worker = Worker(pool=None, threadpoolsize=0, max_jobs=5)
        worker._pid = 666
        with patch.object(worker, 'responds_to_ping') as ping:
            ping.side_effect = twisted.internet.defer.TimeoutError("Mock timeout")
            with patch('os.kill') as mock_kill:
                yield worker._euthanize_unresponsive_worker()

                mock_kill.assert_called_with(worker.pid, signal.SIGTERM)
