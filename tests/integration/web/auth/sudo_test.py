import pytest

from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware

from nav.web.auth.utils import set_account
from nav.web.auth.sudo import sudo, desudo
from nav.models.profiles import Account


def test_sudo_should_change_session_id(
    db, session_request, admin_account, other_account
):
    # login with admin acount
    set_account(session_request, admin_account)

    pre_sudo_session_id = session_request.session.session_key
    sudo(session_request, other_account)
    post_sudo_session_id = session_request.session.session_key

    assert pre_sudo_session_id != post_sudo_session_id


def test_desudo_should_change_session_id(
    db, session_request, admin_account, other_account
):
    # login with admin acount
    set_account(session_request, admin_account)

    sudo(session_request, other_account)

    pre_desudo_session_id = session_request.session.session_key
    desudo(session_request)
    post_desudo_session_id = session_request.session.session_key

    assert pre_desudo_session_id != post_desudo_session_id


@pytest.fixture()
def other_account(db):
    account = Account(login="other_user")
    account.save()
    yield account
    account.delete()
