import os

import pytest
import pytest_twisted

from mock import patch

from nav.models.manage import NetboxProfile
from nav.config import find_configfile
from nav.ipdevpoll import config, jobs, plugins
from nav.ipdevpoll.pool import InlinePool, WorkerPool


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_reschedule(localhost, ipdevpoll_test_config, pool):
    with pytest.raises(jobs.SuggestedReschedule):
        yield pool.execute_job('noop', localhost.pk, ['snmpcheck', ], 0)


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_success(localhost, ipdevpoll_test_config, pool):
    res = yield pool.execute_job('noop', localhost.pk, ['noop', ], 0)
    assert res is True


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_fail(localhost, ipdevpoll_test_config, pool):
    res = yield pool.execute_job('noop', localhost.pk, ['fail', ], 0)
    assert res is True  # TODO: Check job status in database


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_not_done(localhost, ipdevpoll_test_config, pool):
    NetboxProfile.objects.filter(netbox=localhost).delete()
    res = yield pool.execute_job('noop', localhost.pk, ['snmpcheck', ], 0)
    assert res is False


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_crash(localhost, ipdevpoll_test_config, pool):
    with pytest.raises(jobs.AbortedJobError):
        yield pool.execute_job('noop', localhost.pk, ['crash', ], 0)


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_cancel(localhost, ipdevpoll_test_config, pool):
    with pytest.raises(jobs.AbortedJobError):
        defered = pool.execute_job('noop', localhost.pk, ['sleep', ], 0)
        pool.cancel(defered)
        yield defered


@pytest.fixture(params=["WorkerPool", "InlinePool"])
def pool(request):
    with patch('nav.ipdevpoll.control.get_process_command') as gpc:

        gpc.return_value = 'ipdevpolld'
        if request.param == "WorkerPool":
            yield WorkerPool(1, 1)
        elif request.param == "InlinePool":
            yield InlinePool()


@pytest.fixture(scope="module")
def ipdevpoll_test_config():
    print("placing temporary ipdevpoll config")
    configfile = find_configfile("ipdevpoll.conf")
    tmpfile = configfile + '.bak'
    os.rename(configfile, tmpfile)
    with open(configfile, "w") as config_handle:
        config_handle.write("""
[plugins]
snmpcheck=
crash=nav.ipdevpoll.plugins.debugging.Crash
error=nav.ipdevpoll.plugins.debugging.Error
fail=nav.ipdevpoll.plugins.debugging.Fail
sleep=nav.ipdevpoll.plugins.debugging.Sleep
noop=nav.ipdevpoll.plugins.debugging.Noop
""")
    config.ipdevpoll_conf.read_all()
    plugins.import_plugins()
    yield configfile
    print("restoring ipdevpoll config")
    os.remove(configfile)
    os.rename(tmpfile, configfile)
