import os
import subprocess

import pytest

USERNAME = 'admin'
gunicorn = None

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


def pytest_configure(config):
    subprocess.check_call([SCRIPT_CREATE_DB])
    os.environ['TARGETURL'] = "http://localhost:8000/"
    start_gunicorn()


def pytest_unconfigure(config):
    stop_gunicorn()


def start_gunicorn():
    global gunicorn
    gunicorn_log = open("reports/gunicorn.log", "ab")
    gunicorn = subprocess.Popen(['gunicorn', 'navtest_wsgi:application'],
                                stdout=gunicorn_log,
                                stderr=subprocess.STDOUT)


def stop_gunicorn():
    if gunicorn:
        gunicorn.terminate()


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
    print("Adding session cookie for {}: {!r}".format(USERNAME, cookie))
    # visit a non-existent URL just to set the site context for cookies
    selenium.get('{}/400'.format(base_url))
    selenium.add_cookie(cookie)
    selenium.refresh()
    yield selenium
    print("Cookies after test: {!r}".format(selenium.get_cookies()))


@pytest.fixture(scope="session")
def base_url():
    return os.environ.get('TARGETURL', 'http://localhost:8000')


@pytest.fixture
def chrome_options(chrome_options):
    chrome_options.add_argument('--no-sandbox')
    return chrome_options
