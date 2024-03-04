from nav.web.auth import logout
from nav.web.auth.utils import ACCOUNT_ID_VAR, set_account, ensure_account


def test_account_should_be_set_if_request_does_not_already_have_an_account(
    session_request,
):
    assert not hasattr(session_request, "account")
    ensure_account(session_request)
    assert ACCOUNT_ID_VAR in session_request.session, 'Account id is not in the session'
    assert hasattr(session_request, 'account'), 'Account not set'
    assert (
        session_request.account.id == session_request.session[ACCOUNT_ID_VAR]
    ), 'Correct user not set'


def test_account_should_be_switched_to_default_if_locked(
    session_request, locked_account, default_account
):
    set_account(session_request, locked_account)
    ensure_account(session_request)
    assert session_request.session[ACCOUNT_ID_VAR] == default_account.id
    assert session_request.account == default_account, 'Correct user not set'


def test_account_should_be_unchanged_if_ok(session_request, account):
    set_account(session_request, account)
    ensure_account(session_request)
    assert session_request.account == account
    assert session_request.session[ACCOUNT_ID_VAR] == account.id


def test_session_id_should_be_changed_if_going_from_locked_to_default_account(
    session_request, locked_account, default_account
):
    set_account(session_request, locked_account)
    pre_session_id = session_request.session.session_key
    ensure_account(session_request)
    assert session_request.account == default_account
    post_session_id = session_request.session.session_key
    assert post_session_id != pre_session_id
