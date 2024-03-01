from nav.web.auth import logout
from nav.web.auth.utils import ACCOUNT_ID_VAR, set_account
from nav.web.auth.sudo import sudo


def test_non_sudo_logout_removes_session_data(db, session_request, admin_account):
    # login with admin acount
    set_account(session_request, admin_account)
    logout(session_request)
    assert not hasattr(session_request, 'account')
    assert ACCOUNT_ID_VAR not in session_request.session


def test_non_sudo_logout_returns_path_to_index(db, session_request, admin_account):
    # login with admin acount
    set_account(session_request, admin_account)
    result = logout(session_request)
    assert result == '/'


def test_sudo_logout_sets_session_to_original_user(
    db, session_request, admin_account, other_account
):
    # login with admin acount
    set_account(session_request, admin_account)
    sudo(session_request, other_account)
    assert session_request.account is other_account
    result = logout(session_request, sudo=True)
    assert result == '/'
    assert session_request.account == admin_account
