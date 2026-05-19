"""
various pping integration tests
"""

import os
import getpass
import threading
import time
from shutil import which
from subprocess import PIPE, STDOUT, Popen, TimeoutExpired

import pytest

from nav.models.manage import Netbox, NetboxProfile
from nav.models.event import EventQueue
from nav.config import find_config_file


#
# These helpers need to be defined first because they are used in test skip rules
#
def can_be_root():
    try:
        get_root_method()
        return True
    except (OSError, AssertionError):
        return False


def get_root_method():
    if os.geteuid() == 0:
        return []
    elif os.system("sudo -nv") == 0:
        return ["sudo", "-E"]
    elif os.system("gosu root true") == 0:
        return ["gosu", "root"]
    else:
        assert False, "cannot become root"


class PpingProcess:
    """Runs pping as a background subprocess with output capture."""

    def __init__(self):
        self._process = None
        self._output_lines = []
        self._reader_thread = None

    def __enter__(self):
        pping = which("pping")
        assert pping, "Cannot find pping in PATH"
        cmd = get_root_method() + [pping, "-f"]
        self._process = Popen(cmd, stdout=PIPE, stderr=STDOUT)
        self._reader_thread = threading.Thread(target=self._read_output, daemon=True)
        self._reader_thread.start()
        return self

    def __exit__(self, *exc_info):
        self._process.terminate()
        try:
            self._process.wait(timeout=5)
        except TimeoutExpired:
            self._process.kill()
            self._process.wait()
        self._reader_thread.join(timeout=5)
        print(self.get_output())

    def _read_output(self):
        for line in self._process.stdout:
            self._output_lines.append(line.decode("utf-8", errors="replace"))

    def get_output(self):
        return "".join(self._output_lines)

    def wait_for_condition(self, condition, timeout=30, interval=0.5):
        """Poll *condition()* until it returns True or *timeout* is reached."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._process.poll() is not None:
                break
            if condition():
                return True
            time.sleep(interval)
        return False


#
# Actual tests begin here
#
@pytest.mark.timeout(60)
@pytest.mark.skipif(
    not can_be_root(), reason="pping can only be tested with root privileges"
)
def test_pping_localhost_should_work(localhost, pping_test_config):
    with PpingProcess() as pping:
        pping.wait_for_condition(lambda: "hosts checked" in pping.get_output())
    output = pping.get_output()
    assert "hosts checked" in output
    assert f"{localhost.sysname} ({localhost.ip}) marked as down" not in output


@pytest.mark.timeout(60)
@pytest.mark.skipif(
    not can_be_root(), reason="pping can only be tested with root privileges"
)
def test_pping_nonavailable_host_should_fail(
    host_expected_to_be_down, pping_test_config
):
    expected = (
        f"{host_expected_to_be_down.sysname}"
        f" ({host_expected_to_be_down.ip}) marked as down"
    )
    with PpingProcess() as pping:
        pping.wait_for_condition(lambda: expected in pping.get_output())
    assert expected in pping.get_output()


@pytest.mark.timeout(60)
@pytest.mark.skipif(
    not can_be_root(), reason="pping can only be tested with root privileges"
)
def test_pping_should_post_event_when_host_is_unreachable(
    host_expected_to_be_down, pping_test_config
):
    with PpingProcess() as pping:
        pping.wait_for_condition(
            lambda: EventQueue.objects.filter(
                netbox=host_expected_to_be_down,
                event_type_id='boxState',
                state=EventQueue.STATE_START,
            ).exists()
        )
    assert EventQueue.objects.filter(
        netbox=host_expected_to_be_down,
        event_type_id='boxState',
        state=EventQueue.STATE_START,
    ), "The expected boxState start event was not found on the event queue"


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
""".format(user=getpass.getuser())
        )
    yield configfile
    print("restoring ping config")
    os.remove(configfile)
    os.rename(tmpfile, configfile)
