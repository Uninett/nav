"""
smsd integration tests
"""
import os
try:
    from subprocess32 import (STDOUT, check_output, TimeoutExpired,
                              CalledProcessError)
except ImportError:
    from subprocess import (STDOUT, check_output, TimeoutExpired,
                            CalledProcessError)

import pytest
from mock import Mock, patch

from nav.config import find_configfile, find_config_dir


def test_smsd_test_message_with_uninettmaildispatcher_should_work(
    smsd_test_config,
    django_settings_email_backend_file,
):
    output = get_smsd_test_output('99999999')
    print(output)
    assert 'SMS sent' in output


########################
#                      #
# fixtures and helpers #
#                      #
########################

@pytest.fixture(scope="module")
def smsd_test_config():
    print("placing temporary smsd config")
    configfile = find_configfile("smsd.conf")
    tmpfile = configfile + '.bak'
    os.rename(configfile, tmpfile)
    with open(configfile, "w") as config:
        config.write("""
[main]
mailwarnlevel: CRITICAL

[dispatcher]
dispatcher1: UninettMailDispatcher

[UninettMailDispatcher]
mailaddr: root@localhost
""")
    yield configfile
    print("restoring smsd config")
    os.remove(configfile)
    os.rename(tmpfile, configfile)


@pytest.fixture(scope="module")
def django_settings_email_backend_file():
    """Fixture to ensure any NAV Django process does not attempt to contact an
    actual SMTP server when using the Django e-mail framework - since we
    probably don't have one in the test container.

    """
    print("placing temporary local_settings config")
    pythondir = os.path.join(find_config_dir(), 'python')
    if not os.path.exists(pythondir):
        os.mkdir(pythondir, 0o755)

    configfile = os.path.join(pythondir, 'local_settings.py')
    with open(configfile, "w") as config:
        config.write("""
LOCAL_SETTINGS = True
from nav.django.settings import *

EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/tmp/app-messages'
""")
    yield configfile
    print("restoring temporary local_settings config")
    os.remove(configfile)


def get_smsd_test_output(phone_no, timeout=5):
    """
    Runs smsd in foreground mode, kills it after timeout seconds and
    returns the combined stdout+stderr output from the process.

    """
    cmd = ['smsd.py', '-t', phone_no]
    try:
        # remove environment var that may interfere with our test - this mimicks
        # a production environment
        env = os.environ.copy()
        if 'DJANGO_SETTINGS_MODULE' in env:
            del env['DJANGO_SETTINGS_MODULE']
        output = check_output(cmd, stderr=STDOUT, timeout=timeout, env=env)
    except TimeoutExpired as error:
        print(error.output.decode('utf-8'))
        return error.output.decode('utf-8')
    except CalledProcessError as error:
        print(error.output.decode('utf-8'))
        raise
    else:
        print(output)
        return output.decode('utf-8')
