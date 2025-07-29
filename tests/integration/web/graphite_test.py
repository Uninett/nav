#
# Copyright (C) 2024 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
import http.server
import socketserver
import threading
import time

import nav.web.graphite.views
import pytest
import requests


def test_graphite_proxy_should_not_log_503_error_from_graphite_web(
    client, mock_graphite_config, fake_graphite_web_server, capsys, monkeypatch
):
    from django.conf import settings

    url = (
        "/graphite/render/?width=815&height=364&_salt=1400078618.531&from=-1hours"
        "&target=alias%28sumSeries%28group%28carbon.agents.%2A.metricsReceived%29%29%2C%"
        "22Metrics+received%22%29&target=alias%28sumSeries%28group%28carbon.agents.%2A."
        "committedPoints%29%29%2C%22Committed+points%22%29&target=alias%28secondYAxis"
        "%28sumSeries%28group%28carbon.agents.%2A.cache.size%29%29%29%2C%22Cache+size"
        "%22%29"
    )
    monkeypatch.setattr(
        settings, "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
    )
    monkeypatch.setattr(settings, "DEBUG", False)
    client.get(url)
    captured = capsys.readouterr()
    assert "[Django] ERROR" not in captured.out
    assert "Service Unavailable" not in captured.out


def test_graphite_proxy_should_respond_with_graphite_web_status_code(
    client, mock_graphite_config, fake_graphite_web_server
):
    url = (
        "/graphite/render/?width=815&height=364&_salt=1400078618.531&from=-1hours"
        "&target=alias%28sumSeries%28group%28carbon.agents.%2A.metricsReceived"
        "%29%29%2C%22Metrics+received%22%29&target=alias%28sumSeries%28group%28"
        "carbon.agents.%2A.committedPoints%29%29%2C%22Committed+points%22%29"
        "&target=alias%28secondYAxis%28sumSeries%28group%28carbon.agents.%2A.cache."
        "size%29%29%29%2C%22Cache+size%22%29"
    )
    response = client.get(url)
    assert response.status_code == 503


def test_fake_graphite_server_should_respond_with_503_error(fake_graphite_web_server):
    response = requests.get(f"http://localhost:{fake_graphite_web_server}")
    assert response.status_code == 503


#
# Helpers and fixtures
#


@pytest.fixture(scope="module")
def fake_graphite_web_server():
    """A fixture that starts a fake graphite web server that always responds with a
    503 status code.  The fixture returns the localhost port number the server
    listens to.
    """
    port = 54321
    response_code = 503  # Example response code

    handler = lambda *args, **kwargs: SingleStatusHandler(
        *args, response_code=response_code, **kwargs
    )
    httpd = socketserver.TCPServer(("", port), handler)

    thread = threading.Thread(target=httpd.serve_forever)
    thread.daemon = True
    thread.start()
    time.sleep(1)  # Give the server a second to ensure it starts

    yield port

    httpd.shutdown()
    thread.join()


@pytest.fixture
def mock_graphite_config(fake_graphite_web_server, monkeypatch):
    def mock_getter(*args, **kwargs):
        return f"http://localhost:{fake_graphite_web_server}/"

    monkeypatch.setattr(nav.web.graphite.views.CONFIG, "get", mock_getter)
    yield monkeypatch


class SingleStatusHandler(http.server.SimpleHTTPRequestHandler):
    """A request handler that responds to all requests with the same response code
    and dummy content (for testing response code handling)
    """

    def __init__(self, *args, **kwargs):
        self.response_code = kwargs.pop("response_code", 200)
        super().__init__(*args, **kwargs)

    def do_GET(self):
        self.send_response(self.response_code)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Test server response")

    def do_POST(self):
        self.send_response(self.response_code)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Test server response")


def main():
    """Main function for manual test usage of the fake server"""
    port = 54321
    handler = lambda *args, **kwargs: SingleStatusHandler(
        *args, response_code=503, **kwargs
    )
    httpd = socketserver.TCPServer(("", port), handler)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
