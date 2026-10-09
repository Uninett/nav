"""Unit tests for nav/bin/update_ouis.py proxy configuration"""

from unittest.mock import patch

from nav.bin import update_ouis
from nav.bin.update_ouis import OuiConfig


def test_given_configured_proxy_then_get_proxy_returns_it():
    conf = OuiConfig()
    conf.set("oui", "proxy", "http://proxy.example.org:3128")
    assert conf.get_proxy() == "http://proxy.example.org:3128"


def test_given_whitespace_proxy_then_get_proxy_strips_it():
    conf = OuiConfig()
    conf.set("oui", "proxy", "  http://proxy.example.org:3128  ")
    assert conf.get_proxy() == "http://proxy.example.org:3128"


def test_given_no_proxy_then_get_proxy_returns_empty_string():
    conf = OuiConfig()
    conf.set("oui", "proxy", "")
    assert conf.get_proxy() == ""


def test_when_proxy_configured_then_download_passes_proxies():
    proxy = "http://proxy.example.org:3128"
    with patch.object(OuiConfig, "get_proxy", return_value=proxy):
        with patch.object(update_ouis, "requests") as mock_requests:
            update_ouis._download_oui_file(update_ouis.FILE_URL)
    _, kwargs = mock_requests.get.call_args
    assert kwargs["proxies"] == {"http": proxy, "https": proxy}


def test_when_no_proxy_configured_then_download_passes_no_proxies():
    with patch.object(OuiConfig, "get_proxy", return_value=""):
        with patch.object(update_ouis, "requests") as mock_requests:
            update_ouis._download_oui_file(update_ouis.FILE_URL)
    _, kwargs = mock_requests.get.call_args
    assert kwargs["proxies"] is None
