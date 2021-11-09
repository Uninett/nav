"""Black-box integration tests for the apparent proper processing of boxState events"""
import os

try:
    from subprocess32 import STDOUT, check_output, TimeoutExpired, CalledProcessError
except ImportError:
    from subprocess import STDOUT, check_output, TimeoutExpired, CalledProcessError

import pytest

from nav.config import find_config_file
from nav.models.manage import Netbox
from nav.models.event import EventQueue as Event


def test_eventengine_should_declare_box_down(host_going_down, eventengine_test_config):
    post_fake_boxdown(host_going_down)
    get_eventengine_output(6)
    states = host_going_down.get_unresolved_alerts("boxState")
    assert states.count() > 0, "netbox has not been marked as down"


########################
#                      #
# fixtures and helpers #
#                      #
########################
def post_fake_boxdown(netbox):
    event = Event(
        source_id="pping",
        target_id="eventEngine",
        event_type_id="boxState",
        netbox=netbox,
        state=Event.STATE_START,
    )
    event.save()


def get_eventengine_output(timeout=10):
    """
    Runs eventengine in foreground mode, kills it after timeout seconds and
    returns the combined stdout+stderr output from the process.

    Also asserts that pping shouldn't unexpectedly exit with a zero exitcode.
    """
    cmd = ["eventengine", "-f"]
    try:
        output = check_output(cmd, stderr=STDOUT, timeout=timeout)
    except TimeoutExpired as error:
        # this is the normal case, since we need to kill eventengine after the timeout
        print(error.output.decode("utf-8"))
        return error.output.decode("utf-8")
    except CalledProcessError as error:
        print(error.output.decode("utf-8"))
        raise
    else:
        print(output)
        assert False, "eventengine exited with non-zero status"


@pytest.fixture()
def host_going_down():
    box = Netbox(
        ip="10.254.254.254",
        sysname="downhost.example.org",
        organization_id="myorg",
        room_id="myroom",
        category_id="SRV",
    )
    box.save()
    yield box
    print("teardown test device")
    box.delete()


@pytest.fixture(scope="module")
def eventengine_test_config():
    print("placing temporary eventengine config")
    configfile = find_config_file("eventengine.conf")
    tmpfile = configfile + ".bak"
    os.rename(configfile, tmpfile)
    with open(configfile, "w") as config:
        config.write(
            """
[timeouts]
boxDown.warning = 1s
boxDown.alert = 2s
"""
        )
    yield configfile
    print("restoring eventengine config")
    os.remove(configfile)
    os.rename(tmpfile, configfile)
