import json
from io import BytesIO

import pytest
from django.urls import reverse
from django.utils.encoding import smart_str
from mock import Mock, patch

from nav.models.profiles import (
    Account,
    AccountDashboard,
    AccountDashboardSubscription,
)
from nav.web.webfront.utils import tool_list


def test_tools_should_be_readable():
    admin = Mock()
    tools = tool_list(admin)
    assert len(tools) > 0


def test_set_default_dashboard_should_succeed(db, client, admin_account):
    """Tests that a default dashboard can be set"""
    dashboard = AccountDashboard.objects.create(
        name="new_default",
        is_default=False,
        account=admin_account,
    )
    url = reverse("set-default-dashboard", args=(dashboard.pk,))
    response = client.post(url, follow=True)

    dashboard.refresh_from_db()

    assert response.status_code == 200
    assert f"Default dashboard set to «{dashboard.name}»" in smart_str(response.content)
    assert dashboard.is_default
    assert (
        AccountDashboard.objects.filter(account=admin_account, is_default=True).count()
        == 1
    )


def test_set_default_dashboard_with_multiple_previous_defaults_should_succeed(
    db, client, admin_account
):
    """
    Tests that a default dashboard can be set if multiple default dashboards
    exist currently
    """
    # By default there already exists one default dashboard for the admin user
    # which is why we only have to create a second default one
    default_dashboard = AccountDashboard.objects.create(
        name="default_dashboard",
        is_default=True,
        account=admin_account,
    )
    dashboard = AccountDashboard.objects.create(
        name="new_default",
        is_default=False,
        account=admin_account,
    )
    url = reverse("set-default-dashboard", args=(dashboard.pk,))
    response = client.post(url, follow=True)

    default_dashboard.refresh_from_db()
    dashboard.refresh_from_db()

    assert response.status_code == 200
    assert f"Default dashboard set to «{dashboard.name}»" in smart_str(response.content)
    assert dashboard.is_default
    assert not default_dashboard.is_default
    assert (
        AccountDashboard.objects.filter(account=admin_account, is_default=True).count()
        == 1
    )


def test_delete_last_dashboard_should_fail(db, client, admin_account):
    """Tests that the last dashboard cannot be deleted"""
    dashboard = AccountDashboard.objects.get(
        is_default=True,
        account=admin_account,
    )
    url = reverse("delete-dashboard", args=(dashboard.pk,))
    response = client.post(url, follow=True)

    assert response.status_code == 400
    assert "Cannot delete last dashboard" in smart_str(response.content)
    assert AccountDashboard.objects.filter(id=dashboard.id).exists()


def test_delete_default_dashboard_should_fail(db, client, admin_account):
    """Tests that the default dashboard cannot be deleted"""
    # Creating another dashboard, so that default is not the last one
    AccountDashboard.objects.create(
        name="non_default",
        is_default=False,
        account=admin_account,
    )

    default_dashboard = AccountDashboard.objects.get(
        is_default=True,
        account=admin_account,
    )
    url = reverse("delete-dashboard", args=(default_dashboard.pk,))
    response = client.post(url, follow=True)

    assert response.status_code == 400
    assert "Cannot delete default dashboard" in smart_str(response.content)
    assert AccountDashboard.objects.filter(id=default_dashboard.id).exists()


def test_when_logging_in_it_should_change_the_session_id(
    db, client, admin_username, admin_password
):
    login_url = reverse('webfront-login')
    logout_url = reverse('webfront-logout')
    # log out first to compare before and after being logged in
    client.post(logout_url)
    assert client.session.session_key, "the initial session lacks an ID"
    session_id_pre_login = client.session.session_key
    client.post(login_url, {'username': admin_username, 'password': admin_password})
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


def test_shows_password_issue_banner_on_own_password_issues(db, client):
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


def test_shows_password_issue_banner_to_admins_on_other_users_password_issues(
    db, client, admin_account
):
    """
    If other users have insecure or old passwords a banner should be shown to admins
    """

    # Admin account has a password with outdated password hashing method
    # This needs to be fixed, otherwise the "Your password is insecure..." banner will
    # be shown
    admin_account.set_password("new_password")
    admin_account.save()

    Account.objects.create(login="plaintext_pw_user", password="plaintext_pw")

    index_url = reverse('webfront-index')
    response = client.get(index_url)

    assert "There are 1 accounts that have insecure or old passwords." in smart_str(
        response.content
    )


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


class TestToggleDashboardSharingView:
    def test_given_unshared_dashboard_then_share(self, db, client, admin_account):
        """Tests that a dashboard can be shared"""
        dashboard = create_dashboard(admin_account, is_shared=False)
        self._post_toggle_shared(client, dashboard.id, True)

        dashboard.refresh_from_db()
        assert dashboard.is_shared is True

    def test_given_shared_dashboard_then_unshare(self, db, client, admin_account):
        """Tests that a dashboard can be unshared"""
        dashboard = create_dashboard(admin_account, is_shared=True)
        self._post_toggle_shared(client, dashboard.id, False)

        dashboard.refresh_from_db()
        assert dashboard.is_shared is False

    def test_given_dashboard_when_is_shared_is_unchanged_then_do_nothing(
        self, db, client, admin_account
    ):
        """Tests that nothing changes when the sharing status is unchanged"""
        for is_shared in (False, True):
            dashboard = create_dashboard(admin_account, is_shared=is_shared)
            self._post_toggle_shared(client, dashboard.id, is_shared)

            dashboard.refresh_from_db()
            assert dashboard.is_shared is is_shared

    def test_given_shared_dashboard_with_subscriptions_then_remove_subscriptions(
        self, db, client, admin_account, non_admin_account
    ):
        """Tests that all subscriptions are removed when a dashboard is unshared"""
        dashboard = create_dashboard(admin_account, is_shared=True)
        AccountDashboardSubscription.objects.create(
            account=non_admin_account,
            dashboard=dashboard,
        )
        self._post_toggle_shared(client, dashboard.id, False)

        assert not AccountDashboardSubscription.objects.filter(
            dashboard=dashboard
        ).exists()

    def test_given_dashboard_that_does_not_exist_then_return_404(
        self, client, admin_account
    ):
        """
        Tests that 404 is returned when trying to change sharing of a non-existing
        dashboard
        """
        response = self._post_toggle_shared(client, 9999, True)
        assert response.status_code == 404

    def test_given_dashboard_of_other_account_then_return_404(
        self, db, client, admin_account, non_admin_account
    ):
        """
        Tests that 404 is returned when trying to change sharing of another account's
        dashboard
        """
        other_dashboard = create_dashboard(non_admin_account, is_shared=True)
        response = self._post_toggle_shared(client, other_dashboard.id, True)

        assert response.status_code == 404

    @staticmethod
    def _post_toggle_shared(client, dashboard_id, is_shared):
        # Checkbox input returns 'on' if checked
        is_shared_param = 'on' if is_shared else 'off'
        url = reverse('dashboard-toggle-shared', args=(dashboard_id,))
        return client.post(url, data={'is_shared': is_shared_param})


class TestImportDashboardViews:
    @staticmethod
    def _get_file_object(data, name='test.json'):
        """Helper to create a file-like object from a dictionary"""
        file_content = json.dumps(data).encode('utf-8')
        file_obj = BytesIO(file_content)
        file_obj.name = name
        return file_obj

    def test_should_render_import_dashboard_modal(self, client):
        """
        Tests that calling the import_dashboard_modal view will return a fragment
        with a form to import a dashboard
        """
        url = reverse('import-dashboard-modal')
        response = client.get(url, follow=True)

        assert 'id="import-dashboard-form"' in smart_str(response.content)

    def test_when_method_is_not_post_then_return_method_not_allowed(self, client):
        """Tests that import_dashboard only accepts POST requests"""
        url = reverse('import-dashboard')
        response = client.get(url)
        assert response.status_code == 405

    @patch("nav.web.webfront.views.can_modify_navlet", return_value=False)
    def test_when_user_is_without_permission_then_return_forbidden(
        self, mock_can_modify, client
    ):
        """Tests that users without permission cannot import dashboards"""
        url = reverse('import-dashboard')
        response = client.post(url)
        assert response.status_code == 403

    def test_when_no_file_is_provided_then_return_error(self, client):
        """Tests that importing without a file returns an error modal"""
        url = reverse('import-dashboard')
        response = client.post(url)

        assert 'You need to provide a file' in smart_str(response.content)

    def test_given_a_valid_dashboard_file_then_create_dashboard(
        self, db, client, valid_dashboard_data
    ):
        """Tests that importing a valid dashboard file creates a new dashboard"""
        file_obj = self._get_file_object(
            valid_dashboard_data, name='test_dashboard.json'
        )

        url = reverse('import-dashboard')
        client.post(url, {'file': file_obj})

        # Verify dashboard was created
        assert AccountDashboard.objects.filter(
            account_id=valid_dashboard_data['account'],
            name=valid_dashboard_data['name'],
        ).exists()

    def test_given_a_valid_dashboard_file_then_return_redirect_header(
        self, db, client, valid_dashboard_data
    ):
        """Tests that importing a valid dashboard file returns a redirect header"""
        file_obj = self._get_file_object(
            valid_dashboard_data, name='test_dashboard.json'
        )
        url = reverse('import-dashboard')
        response = client.post(url, {'file': file_obj})

        dashboard = AccountDashboard.objects.get(
            account_id=valid_dashboard_data['account'],
            name=valid_dashboard_data['name'],
        )

        assert 'HX-Redirect' in response.headers
        assert response.headers['HX-Redirect'] == reverse(
            'dashboard-index-id', args=(dashboard.id,)
        )

    def test_given_dashboard_file_with_invalid_json_then_return_error(self, client):
        """Tests that importing invalid JSON returns an error message"""
        file_content = b'invalid json content'
        file_obj = BytesIO(file_content)
        file_obj.name = 'invalid.json'

        url = reverse('import-dashboard')
        response = client.post(url, {'file': file_obj})

        assert response.status_code == 200
        assert 'File is not a valid dashboard file' in smart_str(response.content)
        assert 'import-dashboard-form' in smart_str(response.content)

    def test_given_dashboard_file_with_missing_fields_then_return_error(self, client):
        """Tests that importing JSON missing required fields returns an error"""
        dashboard_data = {
            'name': 'Test Dashboard',
            # Missing num_columns, version, widgets
        }

        file_obj = self._get_file_object(dashboard_data, name='incomplete.json')

        url = reverse('import-dashboard')
        response = client.post(url, {'file': file_obj})

        assert response.status_code == 200
        assert 'File is not a valid dashboard file' in smart_str(response.content)

    def test_given_widgets_with_invalid_column_numbers_then_return_error(
        self, client, admin_account
    ):
        """Tests that widgets with invalid column numbers return an error"""
        dashboard_data = {
            'name': 'Test Dashboard',
            'num_columns': 2,
            'version': 1,
            'account': admin_account.id,
            'widgets': [
                {
                    'navlet': 'test_navlet',
                    'column': 5,  # Invalid: greater than num_columns
                    'order': 1,
                    'preferences': {},
                }
            ],
        }

        file_obj = self._get_file_object(dashboard_data, name='invalid_column.json')

        url = reverse('import-dashboard')
        response = client.post(url, {'file': file_obj})

        assert response.status_code == 200
        assert 'File is not a valid dashboard file' in smart_str(response.content)

    def test_given_dashboard_file_with_wrong_field_types_then_return_error(
        self, client
    ):
        """Tests that invalid field types return an error"""
        dashboard_data = {
            'name': 'Test Dashboard',
            'num_columns': 'not_an_int',  # Should be int
            'version': 1,
            'widgets': [],
        }

        file_obj = self._get_file_object(dashboard_data, name='wrong_types.json')

        url = reverse('import-dashboard')
        response = client.post(url, {'file': file_obj})

        assert response.status_code == 200
        assert 'File is not a valid dashboard file' in smart_str(response.content)

    def test_given_dashboard_file_with_non_dictionary_data_then_return_error(
        self, client
    ):
        """Tests that non-dictionary JSON data returns an error"""
        dashboard_data = ['not', 'a', 'dictionary']

        file_obj = self._get_file_object(dashboard_data, name='not_dict.json')

        url = reverse('import-dashboard')
        response = client.post(url, {'file': file_obj})

        assert response.status_code == 200
        assert 'File is not a valid dashboard file' in smart_str(response.content)

    def test_given_dashboard_file_with_invalid_widget_structure_then_return_error(
        self, client, valid_dashboard_data
    ):
        """Tests that widgets that are not dictionaries return an error"""
        dashboard_data = valid_dashboard_data.copy()
        dashboard_data['widgets'] = [
            "not_a_dict",  # This should be a dict
            42,  # This should also be a dict
        ]

        file_obj = self._get_file_object(
            dashboard_data, name='invalid_widget_structure.json'
        )

        url = reverse('import-dashboard')
        response = client.post(url, {'file': file_obj})

        assert response.status_code == 200
        assert 'File is not a valid dashboard file' in smart_str(response.content)

    def test_given_dashboard_file_with_widget_missing_required_fields_then_return_error(
        self, client, valid_dashboard_data
    ):
        """Tests that widgets missing required fields return an error"""
        dashboard_data = valid_dashboard_data.copy()
        dashboard_data['widgets'] = [
            {
                'navlet': 'test_navlet',
                'column': 1,
                # Missing 'preferences' and 'order' fields
            }
        ]

        file_obj = self._get_file_object(
            dashboard_data, name='widget_missing_fields.json'
        )

        url = reverse('import-dashboard')
        response = client.post(url, {'file': file_obj})

        assert response.status_code == 200
        assert 'File is not a valid dashboard file' in smart_str(response.content)

    def test_given_dashboard_file_with_widget_wrong_field_types_then_return_error(
        self, client, valid_dashboard_data
    ):
        """Tests that widgets with wrong field types return an error"""
        dashboard_data = valid_dashboard_data.copy()
        dashboard_data['widgets'] = [
            {
                'navlet': None,  # Should be string
                'column': 1.5,  # Should be int
                'preferences': [],  # Should be dict
                'order': True,  # Should be int
            }
        ]

        file_obj = self._get_file_object(dashboard_data, name='widget_wrong_types.json')

        url = reverse('import-dashboard')
        response = client.post(url, {'file': file_obj})

        assert response.status_code == 200
        assert 'File is not a valid dashboard file' in smart_str(response.content)


def create_dashboard(account, name="Test Dashboard", is_default=False, is_shared=False):
    return AccountDashboard.objects.create(
        name=name,
        is_default=is_default,
        account=account,
        is_shared=is_shared,
    )


@pytest.fixture
def valid_dashboard_data(admin_account):
    dashboard_data = {
        'name': 'Valid Dashboard',
        'num_columns': 3,
        'account': admin_account.id,
        'version': 1,
        'widgets': [],
    }
    yield dashboard_data
