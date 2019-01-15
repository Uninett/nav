# Copyright (C) 2017 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
import mock
import pytest

from nav.statemon.RunQueue import _RunQueue, TerminateException


@mock.patch('nav.statemon.RunQueue.config')
class TestRunQueue(object):
    """Tests for nav.statemon.RunQueue._RunQueue class"""

    def test_deq_should_wait_if_queue_is_empty(self, config):
        rq = _RunQueue()
        rq.await_work.wait = mock.Mock(side_effect=RuntimeError)
        with pytest.raises(RuntimeError):
            rq.deq()
        rq.await_work.wait.assert_called_once_with()

    @mock.patch('time.time')
    def test_queue_is_read_in_correct_order(self, mocktime, config):
        rq = _RunQueue()
        t = [100]
        mocktime.side_effect = lambda: t[0]

        def advance_time(x):
            t[0] += x

        rq.await_work.wait = mock.Mock(side_effect=advance_time)
        rq._start_worker_if_needed = mock.Mock()
        rq.enq(2)
        rq.enq((t[0] + 100, 3))
        rq.enq((t[0] - 100, 1))
        assert rq.deq() == 1
        assert rq.deq() == 2
        rq.await_work.wait.assert_not_called()
        assert rq.deq() == 3
        rq.await_work.wait.assert_called_once_with(100)

    def test_deq_raises_when_stopped(self, config):
        rq = _RunQueue()
        rq.await_work.wait = mock.Mock()
        rq._start_worker_if_needed = mock.Mock()
        rq.stop = True
        with pytest.raises(TerminateException):
            rq.deq()
        rq.enq(1)
        with pytest.raises(TerminateException):
            rq.deq()
