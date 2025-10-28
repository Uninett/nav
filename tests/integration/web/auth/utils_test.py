from django.core.cache import cache
from django.test import RequestFactory
from django.urls import reverse

from nav.web.auth.sudo import SUDOER_ID_VAR
from nav.web.auth.utils import (
    default_account,
    get_account,
    set_account,
    clear_session,
    ACCOUNT_ID_VAR,
    ensure_account,
    get_number_of_accounts_with_password_issues,
    PASSWORD_ISSUES_CACHE_KEY,
)


class TestGetAccount:
    class Account:
        id = 3465

    def test_return_account_if_request_account_set(self):
        r = RequestFactory()
        request = r.get('/')
        user = self.Account()
        request.account = user
        result = get_account(request)
        assert result == user

    def test_return_account_if_request_user_set_and_request_account_not_set(self):
        r = RequestFactory()
        request = r.get('/')
        user = self.Account()
        request.user = user
        result = get_account(request)
        assert result == user

    # Needs to be an integration test due to default_account()
    def test_return_default_account_if_neither_request_user_nor_request_account_is_set(
        self,
        db,
    ):
        r = RequestFactory()
        request = r.get('/')
        result = get_account(request)
        assert result == default_account()


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
        assert ACCOUNT_ID_VAR in session_request.session, (
            'Account id is not in the session'
        )
        assert hasattr(session_request, 'account'), 'Account not set'
        assert session_request.account.id == session_request.session[ACCOUNT_ID_VAR], (
            'Correct user not set'
        )

    def test_account_should_be_switched_to_default_if_locked(
        self, db, session_request, locked_account, default_account
    ):
        set_account(session_request, locked_account)
        ensure_account(session_request)
        assert session_request.session[ACCOUNT_ID_VAR] == default_account.id
        assert session_request.account == default_account, 'Correct user not set'

    def test_account_should_be_unchanged_if_ok(
        self, db, session_request, non_admin_account
    ):
        set_account(session_request, non_admin_account)
        ensure_account(session_request)
        assert session_request.account == non_admin_account
        assert session_request.session[ACCOUNT_ID_VAR] == non_admin_account.id

    def test_session_should_not_be_flushed_if_account_is_default(
        self, db, session_request, default_account, admin_account
    ):
        session_request.session[SUDOER_ID_VAR] = admin_account.id

        set_account(session_request, default_account)
        ensure_account(session_request)
        assert session_request.account == default_account
        assert session_request.session.get(SUDOER_ID_VAR) == admin_account.id

    def test_session_id_should_be_changed_if_going_from_locked_to_default_account(
        self, db, session_request, locked_account, default_account
    ):
        set_account(session_request, locked_account)
        pre_session_id = session_request.session.session_key
        ensure_account(session_request)
        assert session_request.account == default_account
        post_session_id = session_request.session.session_key
        assert post_session_id != pre_session_id


class TestGetNumberOfAccountsWithPasswordIssues:
    def test_returns_correct_number_of_accounts_with_password_issues(self, db):
        cache.delete(PASSWORD_ISSUES_CACHE_KEY)

        # Admin user in tests has deprecated password hash method
        assert get_number_of_accounts_with_password_issues() == 1

    def test_ignores_default_account(self, db, default_account):
        cache.delete(PASSWORD_ISSUES_CACHE_KEY)

        # Admin user in tests has deprecated password hash method
        assert get_number_of_accounts_with_password_issues() == 1

    def test_sets_cache_on_function_call(self, db):
        cache.delete(PASSWORD_ISSUES_CACHE_KEY)

        get_number_of_accounts_with_password_issues()

        assert cache.get(PASSWORD_ISSUES_CACHE_KEY) is not None

    def test_cache_entry_gets_deleted_on_password_change(self, db, non_admin_account):
        get_number_of_accounts_with_password_issues()

        non_admin_account.set_password("new_password")
        non_admin_account.save()

        assert cache.get(PASSWORD_ISSUES_CACHE_KEY) is None

    def test_cache_entry_gets_deleted_on_user_deletion(
        self, db, client, non_admin_account
    ):
        get_number_of_accounts_with_password_issues()

        url = reverse('useradmin-account_delete', args=(non_admin_account.id,))

        client.post(url, follow=True)

        assert cache.get(PASSWORD_ISSUES_CACHE_KEY) is None
