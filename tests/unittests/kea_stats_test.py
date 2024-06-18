import pytest
from nav.kea_stats import KeaQuery, KeaResponse
import requests

def custom_post_response(func):
    """
    Replace the content of the response from any call to requests.post()
    with the content of func().encode("utf8")
    """
    def new_post(url, *args, **kwargs):
        response = requests.Response()
        response._content = func().encode("utf8")
        response.encoding = "utf8"
        response.status_code = 400
        response.reason = "OK"
        response.headers = kwargs.get("headers", {})
        response.cookies = kwargs.get("cookies", {})
        response.url = url
        response.close = lambda: True
        return response

    def new_post_method(self, url, *args, **kwargs):
        return new_post(url, *args, **kwargs)

    def replace_post(monkeypatch):
        monkeypatch.setattr(requests, 'post', new_post)
        monkeypatch.setattr(requests.Session, 'post', new_post_method) # Not sure this works?

    return replace_post

@pytest.fixture
@custom_post_response
def simple_response():
    return '[{"result": 0, "text": "b", "arguments": {"arg1": "val1"}, "service": "d"}]'

@pytest.fixture
@custom_post_response
def lackluster_response():
    return '[{"result": "a"}]'

@pytest.fixture
@custom_post_response
def large_response():
    return '''

    '''

