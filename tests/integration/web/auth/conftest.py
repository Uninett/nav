from contextlib import contextmanager
from unittest.mock import patch

import pytest

from django.test import Client, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware


@pytest.fixture()
def anonymous_client():
    """Provides a logged-out Django test client.

    Deliberately not named ``client``: the project-wide fixture of that name in
    ``tests/integration/conftest.py`` is already logged in as admin, and naming
    this one the same would shadow it for every test in this directory.
    """
    return Client()


@pytest.fixture()
def remote_user_auth():
    """Provides a context manager for configuring REMOTE_USER authentication.

    Both flags patched here are re-read on every request, so the patches must
    stay active while the request is being made, not merely while the test is
    set up. `varname` is deliberately not among them: the middleware reads that
    one only once, when the middleware chain is built.
    """

    @contextmanager
    def _remote_user_auth(enabled=True, autocreate=False):
        with (
            patch(
                "nav.web.auth.remote_user.CONFIG.is_remote_user_enabled",
                return_value=enabled,
            ),
            patch(
                "nav.web.auth.remote_user.CONFIG.will_autocreate_user",
                return_value=autocreate,
            ),
        ):
            yield

    return _remote_user_auth


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
def locked_account(db):
    from nav.models.profiles import Account

    account = Account(login="locked_user", is_active=False)
    account.save()
    yield account
    account.delete()
