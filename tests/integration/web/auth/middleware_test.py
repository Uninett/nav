import pytest
from mock import patch

from nav.web.auth.middleware import AuthenticationMiddleware
from nav.models.profiles import Account


def test_when_remote_user_logs_in_it_should_change_the_session_id(
    db, session_request, remote_account
):
    pre_login_session_id = session_request.session.session_key
    with patch(
        'nav.web.auth.remote_user.get_username', return_value=remote_account.login
    ):
        middleware = AuthenticationMiddleware()
        middleware.process_request(session_request)
    assert session_request.account == remote_account
    post_login_session_id = session_request.session.session_key
    assert pre_login_session_id != post_login_session_id


@pytest.fixture()
def remote_account(db):
    account = Account(login="remote")
    account.set_password("supersecret")
    account.save()
    yield account
    account.delete()
