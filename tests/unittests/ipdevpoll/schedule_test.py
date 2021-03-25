from mock import Mock

import pytest
from twisted.internet import defer, task

from nav.ipdevpoll import schedule


@pytest.fixture
def netbox_job_scheduler():
    job = Mock()
    job.name = 'myjob'
    job.interval = 10
    job.plugins = []
    job.intensity = 0
    netbox = Mock()
    netbox.id = 1
    pool = Mock()
    return schedule.NetboxJobScheduler(job, netbox, pool)


def test_netbox_job_scheduler_reschedule_on_success(netbox_job_scheduler):
    pool = netbox_job_scheduler.pool
    pool.execute_job.return_value = defer.succeed(True)
    clock = task.Clock()
    netbox_job_scheduler.callLater = clock.callLater
    netbox_job_scheduler.start()
    clock.advance(1)
    pool.execute_job.assert_called_once_with('myjob', 1, plugins=[], interval=10)
    clock.advance(10)
    assert pool.execute_job.call_count == 2
    pool.execute_job.assert_called_with('myjob', 1, plugins=[], interval=10)
