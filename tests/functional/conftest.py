import os
import subprocess

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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


def pytest_configure(config):
    subprocess.check_call([SCRIPT_CREATE_DB])


############
#          #
# Fixtures #
#          #
############


@pytest.fixture
def selenium(selenium, base_url, admin_username, admin_password):
    """Fixture to initialize the selenium web driver with a NAV session logged
    in as the admin user.

    """
    selenium.implicitly_wait(10)
    wait = WebDriverWait(selenium, 10)

    # visit the login page and submit the login form
    selenium.get(f"{base_url}/index/login")
    wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "label"), "Username"))

    username = selenium.find_element(By.ID, "id_username")
    password = selenium.find_element(By.ID, "id_password")
    username.send_keys(admin_username)
    password.send_keys(admin_password)
    selenium.find_element(By.NAME, "submit").click()
    wait.until(EC.url_to_be(f"{base_url}/"))

    # Yield logged-in session to the test
    yield selenium


class _session_cookie_is_present(object):
    """Selenium expectation for verifying that a session cookie is set"""

    def __init__(self, session_cookie):
        self.session_cookie = session_cookie

    def __call__(self, driver):
        for cookie in driver.get_cookies():
            if cookie['name'] == self.session_cookie['name']:
                return cookie['value'] == self.session_cookie['value']


@pytest.fixture(scope="session")
def base_url(gunicorn):
    """Used as shorthand for the base URL of the test web server, but really just
    invokes the gunicorn fixture.
    """
    yield gunicorn


@pytest.fixture
def chrome_options(chrome_options):
    # All options stolen from https://stackoverflow.com/questions/48450594/selenium-timed-out-receiving-message-from-renderer
    # AGGRESSIVE: options.setPageLoadStrategy(PageLoadStrategy.NONE)  # https://www.skptricks.com/2018/08/timed-out-receiving-message-from-renderer-selenium.html
    chrome_options.add_argument(
        "start-maximized"
    )  # https://stackoverflow.com/a/26283818/1689770
    chrome_options.add_argument(
        "enable-automation"
    )  # https://stackoverflow.com/a/43840128/1689770
    chrome_options.add_argument(
        "--headless"
    )  # only if you are ACTUALLY running headless
    chrome_options.add_argument(
        "--no-sandbox"
    )  # https://stackoverflow.com/a/50725918/1689770
    chrome_options.add_argument(
        "--disable-infobars"
    )  # https://stackoverflow.com/a/43840128/1689770
    chrome_options.add_argument(
        "--disable-dev-shm-usage"
    )  # https://stackoverflow.com/a/50725918/1689770
    chrome_options.add_argument(
        "--disable-browser-side-navigation"
    )  # https://stackoverflow.com/a/49123152/1689770
    chrome_options.add_argument(
        "--disable-gpu"
    )  # https://stackoverflow.com/questions/51959986/how-to-solve-selenium-chromedriver-timed-out-receiving-message-from-renderer-exc
    return chrome_options
