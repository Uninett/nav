from mock import patch

from nav.web.auth.middleware import AuthenticationMiddleware


def test_when_remote_user_logs_in_it_should_change_the_session_id(
    db, session_request, non_admin_account
):
    pre_login_session_id = session_request.session.session_key
    with patch(
        'nav.web.auth.remote_user.get_username', return_value=non_admin_account.login
    ):
        middleware = AuthenticationMiddleware(lambda request: None)
        middleware.process_request(session_request)
    assert session_request.account == non_admin_account
    post_login_session_id = session_request.session.session_key
    assert pre_login_session_id != post_login_session_id
