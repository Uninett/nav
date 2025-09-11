from nav.web.auth import logout
from nav.web.auth.utils import ACCOUNT_ID_VAR, set_account
from nav.web.auth.sudo import sudo


class TestLogout:
    def test_non_sudo_logout_should_remove_session_data(
        self, db, session_request, admin_account
    ):
        # login with admin acount
        set_account(session_request, admin_account)
        logout(session_request)
        assert not hasattr(session_request, 'account')
        assert ACCOUNT_ID_VAR not in session_request.session

    def test_non_sudo_logout_should_return_path_to_index(
        self, db, session_request, admin_account
    ):
        # login with admin acount
        set_account(session_request, admin_account)
        result = logout(session_request)
        assert result == '/'

    def test_sudo_logout_should_set_session_to_original_user(
        self, db, session_request, admin_account, non_admin_account
    ):
        # login with admin acount
        set_account(session_request, admin_account)
        sudo(session_request, non_admin_account)
        assert session_request.account is non_admin_account
        result = logout(session_request, sudo=True)
        assert result == '/'
        assert session_request.account == admin_account

    def test_non_sudo_logout_should_change_session_id(
        self, db, session_request, admin_account
    ):
        # login with admin acount
        set_account(session_request, admin_account)
        pre_session_id = session_request.session.session_key
        logout(session_request)
        post_session_id = session_request.session.session_key
        assert post_session_id != pre_session_id

    def test_sudo_logout_should_change_session_id(
        self, db, session_request, admin_account, non_admin_account
    ):
        # login with admin acount
        set_account(session_request, admin_account)
        sudo(session_request, non_admin_account)
        pre_session_id = session_request.session.session_key
        logout(session_request, sudo=True)
        post_session_id = session_request.session.session_key
        assert post_session_id != pre_session_id
