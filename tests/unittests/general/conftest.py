import pytest


class FakeSession(dict):
    def set_expiry(self, *_):
        pass

    def save(self, *_):
        pass

    def cycle_key(self, *_):
        pass

    def flush(self):
        pass


@pytest.fixture
def fake_session():
    return FakeSession()
