from nav.web.auth.utils import set_account
from nav.web.auth.sudo import sudo, desudo


def test_sudo_should_change_session_id(db, session_request, admin_account, account):
    # login with admin acount
    set_account(session_request, admin_account)

    pre_sudo_session_id = session_request.session.session_key
    sudo(session_request, account)
    post_sudo_session_id = session_request.session.session_key

    assert pre_sudo_session_id != post_sudo_session_id


def test_desudo_should_change_session_id(db, session_request, admin_account, account):
    # login with admin acount
    set_account(session_request, admin_account)

    sudo(session_request, account)

    pre_desudo_session_id = session_request.session.session_key
    desudo(session_request)
    post_desudo_session_id = session_request.session.session_key

    assert pre_desudo_session_id != post_desudo_session_id
