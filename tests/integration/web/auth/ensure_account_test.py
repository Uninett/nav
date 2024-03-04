from nav.web.auth import logout, Account
from nav.web.auth.utils import ACCOUNT_ID_VAR, set_account, ensure_account
from nav.web.auth.sudo import sudo


def test_account_is_set_if_missing(session_request):
    assert not hasattr(session_request, "account")
    ensure_account(session_request)
    assert ACCOUNT_ID_VAR in session_request.session, 'Account id is not in the session'
    assert hasattr(session_request, 'account'), 'Account not set'
    assert (
        session_request.account.id == session_request.session[ACCOUNT_ID_VAR]
    ), 'Correct user not set'


def test_account_is_switched_to_default_if_locked(session_request, locked_account):
    set_account(session_request, locked_account)
    ensure_account(session_request)
    default_account = Account.objects.get(id=Account.DEFAULT_ACCOUNT)
    assert session_request.session[ACCOUNT_ID_VAR] == default_account.id
    assert session_request.account == default_account, 'Correct user not set'


def test_account_is_left_alone_if_ok(session_request, account):
    set_account(session_request, account)
    ensure_account(session_request)
    assert session_request.account == account
    assert session_request.session[ACCOUNT_ID_VAR] == account.id
