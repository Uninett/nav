import re

from django.core.cache import cache
from django.test import Client, RequestFactory, override_settings
from django.urls import reverse
from django.utils.encoding import smart_str
from mock import Mock

from nav.models.profiles import Account

from nav.web.auth.utils import PASSWORD_ISSUES_CACHE_KEY
from nav.web.webfront.utils import tool_list
from nav.web.webfront.views import index


def test_tools_should_be_readable():
    admin = Mock()
    tools = tool_list(admin)
    assert len(tools) > 0


def test_when_logging_in_it_should_change_the_session_id(
    db, client, admin_username, admin_password, log_in
):
    logout_url = reverse('webfront-logout')
    # log out first to compare before and after being logged in
    client.post(logout_url)
    assert client.session.session_key, "the initial session lacks an ID"
    session_id_pre_login = client.session.session_key
    log_in(client, admin_username, admin_password)
    session_id_post_login = client.session.session_key
    assert session_id_post_login != session_id_pre_login


def test_non_expired_session_id_should_not_be_changed_on_request_unrelated_to_login(
    db, client
):
    """Client should be fresh and guaranteed to not be expired"""
    index_url = reverse('webfront-index')
    assert client.session.session_key, "the initial session lacks an ID"
    session_id_pre_login = client.session.session_key
    client.get(index_url)
    session_id_post_login = client.session.session_key
    assert session_id_post_login == session_id_pre_login


class TestBannerWarnings:
    def test_given_own_password_issues_then_show_password_issue_banner(
        self, db, client
    ):
        """
        The admin user has a password with an outdated password hashing method, so a
        banner indicating a problem with the password should be shown
        """
        index_url = reverse('webfront-index')
        response = client.get(index_url)

        assert (
            "Your account has an insecure or old password. It should be reset."
            in smart_str(response.content)
        )

    def test_when_password_is_empty_then_navbar_should_not_show_password_issue_banner(
        self, db
    ):
        """
        Remote user login sets the password to empty which led to showing the password
        issues banner, even though there are no issues
        """

        factory = RequestFactory()

        request = factory.get(reverse('webfront-index'))
        request.user = Account.objects.create(login="emptypassword", password="")

        response = index(request)

        assert (
            "Your account has an insecure or old password. It should be reset."
            not in smart_str(response.content)
        )

    def test_given_own_and_other_accounts_password_issues_then_show_two_banners_to_admin_account(  # noqa: E501
        self, db, client
    ):
        """
        If other users have insecure or old passwords a banner should be shown to admins
        """
        cache.delete(PASSWORD_ISSUES_CACHE_KEY)

        account = Account.objects.create(
            login="plaintext_pw_user", password="plaintext_pw"
        )

        assert account.has_password_issues(), 'Test account SHOULD have password issues'

        index_url = reverse('webfront-index')
        response = client.get(index_url)
        assert (
            "There are 2 accounts that have insecure or old passwords."
        ) in smart_str(response.content)
        assert (
            "Your account has an insecure or old password. It should be reset."
        ) in smart_str(response.content)
        # The test setup uses the default secret key, so a warning banner for that is
        # additionally shown
        assert (
            len(re.findall(r'<div class="info-bar">', smart_str(response.content))) == 3
        )

    def test_given_other_accounts_password_issues_then_show_only_other_issues_banner(
        self, db, admin_account, log_in
    ):
        """
        If admin doesn't have password issues, but other users do a banner should be
        shown to admin
        """

        # Admin account has a password with outdated password hashing method
        # This needs to be fixed, otherwise the "Your password is insecure..." banner
        # will be shown

        new_password = 'new_password'
        admin_account.set_password(new_password)
        admin_account.save()
        assert not admin_account.has_password_issues(), (
            'Admin account should not have password issues'
        )

        account = Account.objects.create(
            login="plaintext_pw_user", password="plaintext_pw"
        )

        assert account.has_password_issues(), 'Test account SHOULD have password issues'

        # login with a password only used for this test
        client_ = Client()
        log_in(client_, admin_account.login, new_password)

        # test
        index_url = reverse('webfront-index')
        response = client_.get(index_url)

        assert (
            "Your account has an insecure or old password. It should be reset."
        ) not in smart_str(response.content)
        assert (
            "There are 1 accounts that have insecure or old passwords."
        ) in smart_str(response.content)
        # The test setup uses the default secret key, so a warning banner for that is
        # additionally shown
        assert (
            len(re.findall(r'<div class="info-bar">', smart_str(response.content))) == 2
        )

    @override_settings(SECRET_KEY='YouShouldReallyChangeThis')
    def test_when_secret_key_is_default_then_show_settings_issue_banner_warning(
        self, db, client
    ):
        index_url = reverse('webfront-index')
        response = client.get(index_url)
        assert (
            "The SECRET_KEY of this NAV installation is still the default value. Set a "
            "random SECRET_KEY in nav.conf and restart NAV."
        ) in smart_str(response.content)


def test_show_qr_code_returns_fragment_with_qr_code(client):
    """
    Tests that calling the qr_code view will return a fragment with a generated QR
    code
    """
    url = reverse("webfront-qr-code")
    header = {'HTTP_REFERER': 'www.example.com'}
    response = client.get(url, follow=True, **header)

    assert response.status_code == 200
    assert "qr-code" in smart_str(response.content)
    assert "img" in smart_str(response.content)
    assert "QR Code linking to current page" in smart_str(response.content)


def test_should_render_about_logging_modal(client):
    """
    Tests that calling the about_audit_logging_modal view will return a modal with
    information about audit logging
    """
    url = reverse("webfront-audit-logging-modal")
    response = client.get(url)

    assert response.status_code == 200
    assert 'id="about-audit-logging"' in smart_str(response.content)
