"""
various pping integration tests
"""
import os
import getpass
from shutil import which

try:
    from subprocess32 import STDOUT, check_output, TimeoutExpired, CalledProcessError
except ImportError:
    from subprocess import STDOUT, check_output, TimeoutExpired, CalledProcessError

import pytest

from nav.models.manage import Netbox, NetboxProfile
from nav.models.event import EventQueue
from nav.config import find_config_file


def can_be_root():
    try:
        get_root_method()
        return True
    except Exception:
        return False


@pytest.mark.timeout(20)
@pytest.mark.skipif(
    can_be_root(), reason="pping can only be tested with root privileges"
)
def test_pping_localhost_should_work(localhost, pping_test_config):
    output = get_pping_output()
    assert "0 hosts currently marked as down" in output


@pytest.mark.timeout(20)
@pytest.mark.skipif(
    can_be_root(), reason="pping can only be tested with root privileges"
)
def test_pping_nonavailable_host_should_fail(
    host_expected_to_be_down, pping_test_config
):
    expected = "{sysname} ({ip}) marked as down".format(
        sysname=host_expected_to_be_down.sysname, ip=host_expected_to_be_down.ip
    )
    output = get_pping_output()
    assert expected in output


@pytest.mark.timeout(20)
@pytest.mark.skipif(
    can_be_root(), reason="pping can only be tested with root privileges"
)
def test_pping_should_post_event_when_host_is_unreachable(
    host_expected_to_be_down, pping_test_config
):
    get_pping_output()
    assert EventQueue.objects.filter(
        netbox=host_expected_to_be_down,
        event_type_id='boxState',
        state=EventQueue.STATE_START,
    ), "The expected boxState start event was not found on the event queue"


########################
#                      #
# fixtures and helpers #
#                      #
########################
def get_root_method():
    if os.geteuid() == 0:
        return []
    elif os.system("sudo true") == 0:
        return ["sudo", "-E"]
    elif os.system("gosu root true") == 0:
        return ["gosu", "root"]
    else:
        assert False, "cannot become root"


def get_pping_output(timeout=5):
    """
    Runs pping in foreground mode, kills it after timeout seconds and
    returns the combined stdout+stderr output from the process.

    Also asserts that pping shouldn't unexpectedly exit with a zero exitcode.
    """
    pping = which('pping.py')
    assert pping, "Cannot find pping.py on path"
    cmd = get_root_method() + ["/usr/bin/timeout", str(timeout), pping, "-f"]
    try:
        output = check_output(cmd, stderr=STDOUT)
    except CalledProcessError as error:
        if error.returncode == 124:  # timeout
            # this is the normal case, since we need to kill pping after the timeout
            print(error.output.decode('utf-8'))
            return error.output.decode('utf-8')
        print(error.output.decode('utf-8'))
        raise
    else:
        print(output)
        assert False, "pping exited unexpectedly"


@pytest.fixture()
def host_expected_to_be_down(management_profile):
    box = Netbox(
        ip='10.254.254.254',
        sysname='downhost.example.org',
        organization_id='myorg',
        room_id='myroom',
        category_id='SRV',
    )
    box.save()
    NetboxProfile(netbox=box, profile=management_profile).save()
    yield box
    print("teardown test device")
    box.delete()


@pytest.fixture(scope="module")
def pping_test_config():
    print("placing temporary pping config")
    configfile = find_config_file("pping.conf")
    tmpfile = configfile + '.bak'
    os.rename(configfile, tmpfile)
    with open(configfile, "w") as config:
        config.write(
            """
user = {user}
checkinterval = 2
packetsize = 64
timeout = 1
nrping = 2
delay = 2
""".format(
                user=getpass.getuser()
            )
        )
    yield configfile
    print("restoring ping config")
    os.remove(configfile)
    os.rename(tmpfile, configfile)
