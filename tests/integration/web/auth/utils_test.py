from nav.web.auth.utils import set_account, clear_session


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
