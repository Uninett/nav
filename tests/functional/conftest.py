import os
import subprocess

import pytest

USERNAME = 'admin'

########################################################################
#                                                                      #
# Set up the required components for an integration test. Components   #
# such as PostgreSQL and Apache are assumed to already be installed on #
# the system. The system is assumed to be Debian. See                  #
# tests/docker/Dockerfile.                                             #
#                                                                      #
########################################################################

if os.environ.get('WORKSPACE'):
    SCRIPT_PATH = os.path.join(os.environ['WORKSPACE'], 'tests/docker/scripts')
else:
    SCRIPT_PATH = '/'
SCRIPT_CREATE_DB = os.path.join(SCRIPT_PATH, 'create-db.sh')
SCRIPT_START_SERVICES = os.path.join(SCRIPT_PATH, 'start-services.sh')
SCRIPT_STOP_SERVICES = os.path.join(SCRIPT_PATH, 'stop-services.sh')


def pytest_configure(config):
    subprocess.check_call([SCRIPT_CREATE_DB])
    os.environ['TARGETURL'] = "http://localhost:8000/"
    subprocess.check_call([SCRIPT_START_SERVICES])

def pytest_unconfigure(config):
    subprocess.check_call([SCRIPT_STOP_SERVICES])

############
#          #
# Fixtures #
#          #
############

@pytest.fixture
def selenium(selenium, base_url):
    from nav.django.auth import create_session_cookie

    selenium.implicitly_wait(10)
    cookie = create_session_cookie(USERNAME)
    selenium.get('{}/400'.format(base_url))
    selenium.add_cookie(cookie)
    selenium.refresh()
    return selenium


@pytest.fixture(scope="session")
def base_url():
    return os.environ.get('TARGETURL', 'http://localhost:8000')

@pytest.fixture
def chrome_options(chrome_options):
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    return chrome_options
