from nav.web.auth.utils import (
    set_account,
    clear_session,
    ACCOUNT_ID_VAR,
    ensure_account,
)


class TestClearSession:
    def test_should_create_new_session_id(self, db, session_request):
        pre_session_id = session_request.session.session_key
        clear_session(session_request)
        post_session_id = session_request.session.session_key
        assert pre_session_id != post_session_id

    def test_should_remove_account_from_request(
        self, db, session_request, admin_account
    ):
        # login with admin acount
        set_account(session_request, admin_account)
        assert session_request.account
        clear_session(session_request)
        assert not hasattr(session_request, "account")

    def test_should_clear_session_dict(self, db, session_request, admin_account):
        set_account(session_request, admin_account)
        # Make sure there is something to be deleted
        assert session_request.session.keys()
        clear_session(session_request)
        assert not session_request.session.keys()


class TestEnsureAccount:
    def test_account_should_be_set_if_request_does_not_already_have_an_account(
        self, db, session_request
    ):
        assert not hasattr(session_request, "account")
        ensure_account(session_request)
        assert (
            ACCOUNT_ID_VAR in session_request.session
        ), 'Account id is not in the session'
        assert hasattr(session_request, 'account'), 'Account not set'
        assert (
            session_request.account.id == session_request.session[ACCOUNT_ID_VAR]
        ), 'Correct user not set'

    def test_account_should_be_switched_to_default_if_locked(
        self, db, session_request, locked_account, default_account
    ):
        set_account(session_request, locked_account)
        ensure_account(session_request)
        assert session_request.session[ACCOUNT_ID_VAR] == default_account.id
        assert session_request.account == default_account, 'Correct user not set'

    def test_account_should_be_unchanged_if_ok(self, db, session_request, account):
        set_account(session_request, account)
        ensure_account(session_request)
        assert session_request.account == account
        assert session_request.session[ACCOUNT_ID_VAR] == account.id

    def test_session_id_should_be_changed_if_going_from_locked_to_default_account(
        self, db, session_request, locked_account, default_account
    ):
        set_account(session_request, locked_account)
        pre_session_id = session_request.session.session_key
        ensure_account(session_request)
        assert session_request.account == default_account
        post_session_id = session_request.session.session_key
        assert post_session_id != pre_session_id
