import pytest

from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware


@pytest.fixture()
def session_request(db):
    """Request object with a real session"""
    r = RequestFactory()
    session_request = r.post('/anyurl')

    # use middleware to make session for session_request
    middleware = SessionMiddleware()
    middleware.process_request(session_request)
    session_request.session.save()
    return session_request
