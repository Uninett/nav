import pytest

from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware


@pytest.fixture()
def session_request(db):
    """Request object with a real session"""
    r = RequestFactory()
    session_request = r.post('/anyurl')

    # use middleware to make session for session_request
    middleware = SessionMiddleware(lambda request: None)
    middleware.process_request(session_request)
    session_request.session.save()
    return session_request


@pytest.fixture()
def other_account(db):
    from nav.models.profiles import Account

    account = Account(login="other_user")
    account.set_password("password")
    account.save()
    yield account
    account.delete()
