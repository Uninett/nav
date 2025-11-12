import json
from io import BytesIO
from urllib.parse import quote

import pytest
from django.http import Http404
from django.test import Client
from django.urls import reverse
from django.utils.encoding import smart_str
from mock import Mock, patch

from nav.models.profiles import (
    Account,
    AccountDashboard,
    AccountDashboardSubscription,
    AccountNavlet,
)
from nav.web.webfront import find_dashboard, get_dashboards_for_account
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


class TestDeleteDashboardView:
    """Tests for the delete_dashboard view which allows deleting dashboards"""

    def test_given_dashboard_when_delete_unconfirmed_then_do_not_delete_dashboard(
        self, db, client, admin_account
    ):
        """
        Tests that the dashboard is not deleted when deletion is not yet confirmed
        """
        dashboard = self._create_dashboard(
            admin_account,
            name="to_be_deleted",
            is_default=False,
        )
        url = reverse("delete-dashboard", args=(dashboard.pk,))
        response = client.post(url)

        assert response.status_code == 200
        assert AccountDashboard.objects.filter(id=dashboard.id).exists()

    def test_given_dashboard_id_when_delete_unconfirmed_then_render_confirmation(
        self, db, client, admin_account
    ):
        """
        Tests that the deletion confirmation is rendered when deletion is unconfirmed
        """
        dashboard = self._create_dashboard(
            admin_account,
            name="to_be_deleted",
            is_default=False,
        )
        url = reverse("delete-dashboard", args=(dashboard.pk,))
        response = client.post(url)

        assert response.status_code == 200
        assert 'id="delete-dashboard-confirmation"' in smart_str(response.content)

    def test_given_dashboard_with_subscribers_then_render_subscriber_warning(
        self, db, client, admin_account, non_admin_account
    ):
        """Tests that the deletion confirmation shows subscriber info when applicable"""
        dashboard = self._create_dashboard(
            admin_account,
            is_shared=True,
        )
        AccountDashboardSubscription.objects.create(
            account=non_admin_account,
            dashboard=dashboard,
        )
        url = reverse("delete-dashboard", args=(dashboard.pk,))
        response = client.post(url)
        response_content = smart_str(response.content)

        assert response.status_code == 200
        assert 'data-test-id="subscriber-warning"' in response_content

    def test_given_dashboard_when_delete_confirmed_then_delete_dashboard(
        self, db, client, admin_account
    ):
        """Tests that an existing dashboard can be deleted"""
        dashboard = self._create_dashboard(admin_account)
        url = reverse("delete-dashboard", args=(dashboard.pk,))
        response = client.post(
            url,
            data={"confirm_delete": "true"},
            follow=True,
        )

        assert response.status_code == 200
        assert not AccountDashboard.objects.filter(id=dashboard.id).exists()

    def test_given_last_dashboard_of_account_then_render_error_message(
        self, db, client, admin_account
    ):
        """Tests that the last dashboard cannot be deleted"""

        # Ensure only one dashboard exists for the account
        AccountDashboard.objects.filter(account=admin_account).delete()
        dashboard = self._create_dashboard(admin_account, name="last_dashboard")

        url = reverse("delete-dashboard", args=(dashboard.pk,))
        response = client.post(
            url,
        )

        assert response.status_code == 200
        assert "Cannot delete last dashboard" in smart_str(response.content)
        assert AccountDashboard.objects.filter(id=dashboard.id).exists()

    def test_given_default_dashboard_of_account_then_render_error_message(
        self, db, client, admin_account
    ):
        """Tests that the default dashboard cannot be deleted"""
        # Ensure at least one non-default dashboard exists
        self._create_dashboard(admin_account, name="non_default_dashboard")
        default_dashboard = AccountDashboard.objects.get(
            is_default=True, account=admin_account
        )
        url = reverse("delete-dashboard", args=(default_dashboard.pk,))
        response = client.post(url)

        assert response.status_code == 200
        assert "Cannot delete default dashboard" in smart_str(response.content)
        assert AccountDashboard.objects.filter(id=default_dashboard.id).exists()

    @staticmethod
    def _create_dashboard(
        account, name="to_be_deleted", is_default=False, is_shared=False
    ):
        return AccountDashboard.objects.create(
            name=name,
            is_default=is_default,
            account=account,
            is_shared=is_shared,
        )


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


class TestDashboardIndexView:
    def test_given_no_dashboard_id_then_return_default_dashboard(
        self, db, client, admin_account
    ):
        """Tests that the default dashboard is shown when no ID is given"""
        default_dashboard = AccountDashboard.objects.get(
            is_default=True, account=admin_account
        )
        url = reverse('dashboard-index')
        response = client.get(url)

        assert response.status_code == 200
        assert response.context['dashboard'].id == default_dashboard.id

    def test_given_valid_dashboard_id_then_return_that_dashboard(
        self, db, client, admin_account
    ):
        """Tests that the specified dashboard is shown when a valid ID is given"""
        dashboard = create_dashboard(admin_account)
        url = reverse('dashboard-index-id', args=(dashboard.id,))
        response = client.get(url)

        assert response.status_code == 200
        assert response.context['dashboard'].id == dashboard.id

    def test_given_dashboard_id_that_does_not_exist_then_return_404(
        self, db, client, admin_account
    ):
        """Tests that 404 is returned when a non-existing ID is given"""
        url = reverse('dashboard-index-id', args=(9999,))
        response = client.get(url)

        assert response.status_code == 404

    def test_given_dashboard_id_for_other_account_when_shared_then_return_dashboard(
        self, db, client, admin_account, non_admin_account
    ):
        """Tests that a shared dashboard of another account can be accessed"""
        other_dashboard = create_dashboard(non_admin_account, is_shared=True)
        url = reverse('dashboard-index-id', args=(other_dashboard.id,))
        response = client.get(url)

        assert response.status_code == 200
        assert response.context['dashboard'].id == other_dashboard.id

    def test_given_dashboard_id_for_other_account_when_not_shared_then_return_404(
        self, db, client, admin_account, non_admin_account
    ):
        """
        Tests that 404 is returned when trying to access another account's dashboard
        """
        other_dashboard = create_dashboard(non_admin_account, is_shared=False)
        url = reverse('dashboard-index-id', args=(other_dashboard.id,))
        response = client.get(url)

        assert response.status_code == 404

    def test_given_subscribed_dashboard_id_then_return_dashboard(
        self, db, client, admin_account, non_admin_account
    ):
        """Tests that a subscribed dashboard of another account can be accessed"""
        other_dashboard = create_dashboard(non_admin_account, is_shared=True)
        AccountDashboardSubscription.objects.create(
            account=admin_account,
            dashboard=other_dashboard,
        )
        url = reverse('dashboard-index-id', args=(other_dashboard.id,))
        response = client.get(url)

        assert response.status_code == 200
        assert response.context['dashboard'].id == other_dashboard.id

    def test_given_subscribed_dashboard_id_then_return_is_subscribed(
        self, db, client, admin_account, non_admin_account
    ):
        """Tests that a subscribed dashboard of another account can be accessed"""
        other_dashboard = create_dashboard(non_admin_account, is_shared=True)
        AccountDashboardSubscription.objects.create(
            account=admin_account,
            dashboard=other_dashboard,
        )
        url = reverse('dashboard-index-id', args=(other_dashboard.id,))
        response = client.get(url)

        assert response.status_code == 200
        assert response.context['is_subscribed'] is True

    def test_given_own_dashboard_id_then_return_can_edit_true(
        self, db, client, admin_account
    ):
        """Tests that can_edit is True for own dashboards"""
        own_dashboard = create_dashboard(admin_account, is_shared=False)
        url = reverse('dashboard-index-id', args=(own_dashboard.id,))
        response = client.get(url)

        assert response.status_code == 200
        assert response.context['can_edit'] is True

    def test_given_other_account_dashboard_id_then_return_can_edit_false(
        self, db, client, admin_account, non_admin_account
    ):
        """Tests that can_edit is False for other account's dashboards"""
        other_dashboard = create_dashboard(non_admin_account, is_shared=True)
        url = reverse('dashboard-index-id', args=(other_dashboard.id,))
        response = client.get(url)

        assert response.status_code == 200
        assert response.context['can_edit'] is False

    def test_given_subscribed_dashboard_then_include_dashboard_in_response_list(
        self, db, client, admin_account, non_admin_account
    ):
        """
        Tests that subscribed dashboards of other accounts are included in the list
        """
        subscribed_dashboard = create_dashboard(non_admin_account, is_shared=True)
        AccountDashboardSubscription.objects.create(
            account=admin_account,
            dashboard=subscribed_dashboard,
        )
        url = reverse('dashboard-index')
        response = client.get(url)

        assert response.status_code == 200
        assert subscribed_dashboard in response.context['dashboards']

    def test_given_shared_dashboard_id_when_not_subscribed_then_include_dashboard_last(
        self, db, client, admin_account, non_admin_account
    ):
        """
        Tests that a shared dashboard of another account is included last in the list
        when the current account is not subscribed
        """
        shared_dashboard = create_dashboard(non_admin_account, is_shared=True)
        url = reverse('dashboard-index-id', args=(shared_dashboard.id,))
        response = client.get(url)

        assert response.status_code == 200
        dashboards = response.context['dashboards']
        assert dashboards[-1] == shared_dashboard


class TestToggleDashboardSubscriptionView:
    def test_when_not_subscribed_then_subscribe(
        self, db, client, admin_account, non_admin_account
    ):
        """Tests that a dashboard can be subscribed to"""
        other_dashboard = create_dashboard(non_admin_account, is_shared=True)
        url = reverse('dashboard-toggle-subscribe', args=(other_dashboard.id,))
        client.post(url, follow=True)

        assert other_dashboard.is_subscribed(admin_account) is True

    def test_when_subscribed_then_unsubscribe(
        self, db, client, admin_account, non_admin_account
    ):
        """Tests that a dashboard can be unsubscribed from"""
        other_dashboard = create_dashboard(non_admin_account, is_shared=True)
        AccountDashboardSubscription.objects.create(
            account=admin_account,
            dashboard=other_dashboard,
        )
        url = reverse('dashboard-toggle-subscribe', args=(other_dashboard.id,))
        client.post(url, follow=True)

        assert other_dashboard.is_subscribed(admin_account) is False

    def test_given_dashboard_that_does_not_exist_then_return_404(
        self, db, client, admin_account
    ):
        """
        Tests that 404 is returned when trying to subscribe to a non-existing dashboard
        """
        url = reverse('dashboard-toggle-subscribe', args=(9999,))
        response = client.post(url)

        assert response.status_code == 404

    def test_given_existing_dashboard_when_not_shared_then_return_404(
        self, db, client, admin_account, non_admin_account
    ):
        """
        Tests that 404 is returned when trying to subscribe to a non-shared dashboard
        """
        other_dashboard = create_dashboard(non_admin_account, is_shared=False)
        url = reverse('dashboard-toggle-subscribe', args=(other_dashboard.id,))
        response = client.post(url)

        assert response.status_code == 404

    def test_given_existing_shared_dashboard_id_then_return_refresh_header(
        self, db, client, admin_account, non_admin_account
    ):
        """
        Tests that subscribing to a shared dashboard returns a response with
        HX-Refresh header set to true
        """
        shared_dashboard = create_dashboard(non_admin_account, is_shared=True)
        url = reverse('dashboard-toggle-subscribe', args=(shared_dashboard.id,))
        response = client.post(url)

        assert response.status_code == 200
        assert 'HX-Refresh' in response.headers
        assert response.headers['HX-Refresh'] == 'true'


class TestToggleDashboardSharingView:
    def test_given_unshared_dashboard_it_should_toggle_is_shared(
        self, db, client, admin_account
    ):
        """Tests that a dashboard can be shared"""
        dashboard = create_dashboard(admin_account, is_shared=False)
        self._post_toggle_shared(client, dashboard.id, True)

        dashboard.refresh_from_db()
        assert dashboard.is_shared is True

    def test_given_shared_dashboard_it_should_toggle_is_shared(
        self, db, client, admin_account
    ):
        """Tests that a dashboard can be unshared"""
        dashboard = create_dashboard(admin_account, is_shared=True)
        self._post_toggle_shared(client, dashboard.id, False)

        dashboard.refresh_from_db()
        assert dashboard.is_shared is False

    def test_given_any_dashboard_when_is_shared_is_unchanged_it_should_do_nothing(
        self, db, client, admin_account
    ):
        """Tests that nothing changes when the sharing status is unchanged"""
        for is_shared in (False, True):
            dashboard = create_dashboard(admin_account, is_shared=is_shared)
            self._post_toggle_shared(client, dashboard.id, is_shared)

            dashboard.refresh_from_db()
            assert dashboard.is_shared is is_shared

    def test_given_shared_dashboard_with_subscriptions_when_unsharing_it_should_remove_subscriptions(  # noqa: E501
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

    def test_given_dashboard_that_does_not_exist_it_should_return_404(
        self, client, admin_account
    ):
        """
        Tests that 404 is returned when trying to change sharing of a non-existing
        dashboard
        """
        response = self._post_toggle_shared(client, 9999, True)
        assert response.status_code == 404

    def test_given_dashboard_of_other_account_it_should_return_404(
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
    def _post_toggle_shared(client: Client, dashboard_id: int, is_shared: bool):
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


class TestExportDashboardView:
    """
    Tests for the export_dashboard view which allows exporting a dashboard as JSON
    """

    def test_given_dashboard_id_when_account_is_owner_then_return_file(
        self, db, client, admin_account
    ):
        """Tests that the owner of a dashboard can export it"""
        dashboard = create_dashboard(admin_account, name="My Dashboard")
        create_widget(dashboard)

        url = reverse('export-dashboard', args=(dashboard.id,))
        response = client.get(url)

        assert response.status_code == 200
        assert response.json()['name'] == dashboard.name

    def test_given_shared_dashboard_id_when_account_is_not_owner_then_return_file(
        self, db, client, non_admin_account
    ):
        """Tests that a shared dashboard can be exported by another account"""
        dashboard = create_dashboard(
            non_admin_account, name="Shared Dashboard", is_shared=True
        )
        create_widget(dashboard)

        url = reverse('export-dashboard', args=(dashboard.id,))
        response = client.get(url)

        assert response.status_code == 200
        assert response.json()['name'] == dashboard.name

    def test_given_unshared_dashboard_id_when_account_is_not_owner_then_return_404(
        self, db, client, non_admin_account
    ):
        """Tests that an unshared dashboard cannot be exported by another account"""
        dashboard = create_dashboard(
            non_admin_account, name="Private Dashboard", is_shared=False
        )
        create_widget(dashboard)

        url = reverse('export-dashboard', args=(dashboard.id,))
        response = client.get(url)

        assert response.status_code == 404

    def test_given_dashboard_id_that_does_not_exist_then_return_404(self, client):
        """Tests that 404 is returned when trying to export a non-existing dashboard"""
        url = reverse('export-dashboard', args=(9999,))
        response = client.get(url)

        assert response.status_code == 404

    def test_exported_file_should_have_correct_headers(self, db, client, admin_account):
        """Tests that the exported file has the correct headers"""
        dashboard = create_dashboard(admin_account, name="My Dashboard")
        create_widget(dashboard)

        url = reverse('export-dashboard', args=(dashboard.id,))
        response = client.get(url)

        assert response.status_code == 200
        assert response['Content-Type'] == 'application/json'
        assert (
            response['Content-Disposition']
            == f'attachment; filename={quote(dashboard.name)}.json'
        )


class TestFindDashboardUtil:
    """
    Tests for the find_dashboard utility function which determines which dashboard
    to show based on the given account and optional dashboard ID
    """

    def test_given_no_dashboard_id_then_return_default_dashboard(
        self, db, non_admin_account
    ):
        """Tests that the default dashboard is returned when no ID is given"""
        default_dashboard = AccountDashboard.objects.get(
            is_default=True, account=non_admin_account
        )

        dashboard = find_dashboard(non_admin_account)
        assert dashboard == default_dashboard

    def test_given_valid_dashboard_id_then_return_that_dashboard(
        self, db, non_admin_account
    ):
        """Tests that the specified dashboard is returned when a valid ID is given"""
        dashboard = create_dashboard(non_admin_account, name="Test dashboard")

        found_dashboard = find_dashboard(non_admin_account, dashboard_id=dashboard.id)
        assert found_dashboard == dashboard

    def test_given_dashboard_id_that_does_not_exist_then_return_404(
        self, db, non_admin_account
    ):
        """Tests that 404 is raised when a non-existing dashboard ID is given"""

        with pytest.raises(Http404):
            find_dashboard(non_admin_account, dashboard_id=9999)

    def test_given_no_dashboard_id_when_no_default_and_no_dashboards_then_return_404(
        self, db, non_admin_account
    ):
        """Tests that 404 is raised when no dashboards exist for the account"""
        # Clean up any existing dashboards
        AccountDashboard.objects.filter(account=non_admin_account).delete()
        with pytest.raises(Http404):
            find_dashboard(non_admin_account)

    def test_given_no_dashboard_id_then_returns_dashboard_with_most_widgets(
        self, db, non_admin_account
    ):
        """
        Tests that when no ID is given and no default dashboard is set, the dashboard
        with the most widgets is returned
        """
        # Clean up any existing dashboards
        AccountDashboard.objects.filter(account=non_admin_account).delete()
        # Create first dashboard with three widgets
        first_dashboard = create_dashboard(non_admin_account, name="First")
        for _ in range(3):
            create_widget(first_dashboard)
            create_widget(first_dashboard)
        # Create second dashboard with no widgets
        create_dashboard(non_admin_account, name="Second")

        dashboard = find_dashboard(non_admin_account)
        assert dashboard == first_dashboard

    def test_given_dashboard_id_for_other_account_when_shared_then_return_dashboard(
        self, db, non_admin_account, admin_account
    ):
        """Tests that a shared dashboard of another account can be accessed"""
        other_dashboard = create_dashboard(admin_account, name="Other", is_shared=True)
        found_dashboard = find_dashboard(
            non_admin_account, dashboard_id=other_dashboard.id
        )
        assert found_dashboard == other_dashboard

    def test_given_dashboard_id_for_other_account_when_not_shared_then_return_404(
        self, db, client, non_admin_account, admin_account
    ):
        """
        Test that 404 is raised when accessing a non-shared dashboard of another account
        """
        other_dashboard = create_dashboard(admin_account, name="Other", is_shared=False)

        with pytest.raises(Http404):
            find_dashboard(non_admin_account, dashboard_id=other_dashboard.id)

    def test_given_own_dashboard_then_find_dashboard_sets_shared_by_other_to_false(
        self, db, non_admin_account
    ):
        """Tests that find_dashboard sets shared_by_other to False for own dashboards"""
        dashboard = create_dashboard(non_admin_account, name="Own", is_shared=True)
        found_dashboard = find_dashboard(non_admin_account, dashboard_id=dashboard.id)
        assert found_dashboard.shared_by_other is False

    def test_given_dashboard_of_another_account_then_find_dashboard_sets_shared_by_other_to_true(  # noqa: E501
        self, db, non_admin_account, admin_account
    ):
        """
        Test that find_dashboard sets shared_by_other to True for other a dashboard
        of another account
        """
        other_dashboard = create_dashboard(admin_account, name="Other", is_shared=True)
        found_dashboard = find_dashboard(
            non_admin_account, dashboard_id=other_dashboard.id
        )
        assert found_dashboard.shared_by_other is True


class TestGetDashboardsForAccount:
    """
    Tests for the get_dashboards_for_account utility function which retrieves all
    dashboards for a given account, including shared dashboards from other accounts
    """

    def test_given_account_then_return_all_own_dashboards(self, db, non_admin_account):
        """Tests that all own dashboards are returned"""
        default_dashboard = AccountDashboard.objects.get(
            is_default=True, account=non_admin_account
        )
        other_dashboard = create_dashboard(
            non_admin_account, name="Own 1", is_shared=False
        )

        dashboards = get_dashboards_for_account(non_admin_account)
        assert default_dashboard in dashboards
        assert other_dashboard in dashboards

    def test_given_account_with_no_subscriptions_then_return_own_dashboards(
        self, db, non_admin_account, admin_account
    ):
        """
        Tests that only own dashboards are returned when there are no subscriptions
        """
        own_dashboard = create_dashboard(non_admin_account, name="Own", is_shared=False)
        shared_dashboard = create_dashboard(
            admin_account, name="Shared", is_shared=True
        )

        dashboards = get_dashboards_for_account(non_admin_account)
        assert own_dashboard in dashboards
        assert shared_dashboard not in dashboards

    def test_given_account_with_subscriptions_then_return_shared_dashboards(
        self, db, non_admin_account, admin_account
    ):
        """Tests that shared dashboards are returned when there are subscriptions"""
        own_dashboard = create_dashboard(non_admin_account, name="Own", is_shared=False)
        shared_dashboard = create_dashboard(
            admin_account, name="Shared", is_shared=True
        )
        AccountDashboardSubscription.objects.create(
            account=non_admin_account,
            dashboard=shared_dashboard,
        )

        dashboards = get_dashboards_for_account(non_admin_account)

        assert own_dashboard in dashboards
        assert shared_dashboard in dashboards

    def test_given_dashboard_subscription_then_shared_by_other_is_set_correctly(
        self, db, non_admin_account, admin_account
    ):
        """
        Tests that shared_by_other is set correctly for shared dashboards
        """
        shared_dashboard = create_dashboard(
            admin_account, name="Shared", is_shared=True
        )
        AccountDashboardSubscription.objects.create(
            account=non_admin_account,
            dashboard=shared_dashboard,
        )

        dashboards = get_dashboards_for_account(non_admin_account)
        assert all(
            dashboard.shared_by_other is (dashboard.account != non_admin_account)
            for dashboard in dashboards
        )

    def test_given_dashboard_subscription_then_can_edit_is_set_correctly(
        self, db, non_admin_account, admin_account
    ):
        """
        Tests that can_edit is set correctly for shared dashboards
        """
        shared_dashboard = create_dashboard(
            admin_account, name="Shared", is_shared=True
        )
        AccountDashboardSubscription.objects.create(
            account=non_admin_account,
            dashboard=shared_dashboard,
        )
        dashboards = get_dashboards_for_account(non_admin_account)
        assert all(
            dashboard.can_edit is (dashboard.account == non_admin_account)
            for dashboard in dashboards
        )
        assert len(dashboards) == 2  # Default + shared


class TestDashboardSearchViews:
    def test_should_render_search_dashboard_modal(self, client):
        """
        Tests that calling the search_dashboard_modal view will return a fragment
        with a form to search dashboards
        """
        url = reverse('dashboard-search-modal')
        response = client.get(url)

        assert 'id="dashboard-search-form"' in smart_str(response.content)

    def test_given_dashboard_name_then_return_matching_dashboards(
        self, db, client, non_admin_account
    ):
        """Tests that searching returns matching dashboards"""
        shared_dashboard = create_dashboard(
            non_admin_account, name="A cool dashboard", is_shared=True
        )

        url = reverse('dashboard-search')
        response = client.post(url, {'search': 'cool'})

        assert response.status_code == 200
        assert shared_dashboard in response.context['dashboards']

    def test_given_account_name_then_return_matching_dashboards(
        self, db, client, non_admin_account, admin_account
    ):
        """Tests that searching returns matching dashboards by account name"""
        shared_dashboard = create_dashboard(
            non_admin_account, name="A cool dashboard", is_shared=True
        )

        url = reverse('dashboard-search')
        response = client.post(url, {'search': non_admin_account.name})

        assert response.status_code == 200
        assert shared_dashboard in response.context['dashboards']

    def test_given_account_login_then_return_matching_dashboards(
        self, db, client, non_admin_account, admin_account
    ):
        """Tests that searching returns matching dashboards by account login"""
        shared_dashboard = create_dashboard(
            non_admin_account, name="A cool dashboard", is_shared=True
        )

        url = reverse('dashboard-search')
        response = client.post(url, {'search': non_admin_account.login})

        assert response.status_code == 200
        assert shared_dashboard in response.context['dashboards']

    def test_given_empty_search_then_return_empty_list(
        self, db, client, non_admin_account
    ):
        """Tests that searching with an empty string returns an empty list"""
        create_dashboard(non_admin_account, name="A cool dashboard", is_shared=True)

        url = reverse('dashboard-search')
        response = client.post(url, {'search': ''})

        assert response.status_code == 200
        assert len(response.context['dashboards']) == 0

    def test_given_empty_search_then_return_empty_template(
        self, db, client, non_admin_account
    ):
        """Tests that searching with an empty string returns an empty template"""
        create_dashboard(non_admin_account, name="A cool dashboard", is_shared=True)

        url = reverse('dashboard-search')
        response = client.post(url, {'search': ''})

        assert response.status_code == 200
        assert 'No dashboards found' not in smart_str(response.content)
        assert 'search-result-item' not in smart_str(response.content)

    def test_given_no_matching_dashboards_then_return_empty_list(
        self, db, client, non_admin_account
    ):
        """Tests that searching returns an empty list when there are no matches"""
        create_dashboard(non_admin_account, name="A cool dashboard", is_shared=True)

        url = reverse('dashboard-search')
        response = client.post(url, {'search': 'nonexistent'})

        assert response.status_code == 200
        assert len(response.context['dashboards']) == 0

    def test_given_dashboard_name_when_account_is_owner_then_return_empty_list(
        self, db, client, admin_account
    ):
        """Tests that searching does not return own dashboards"""
        own_dashboard = create_dashboard(
            admin_account, name="A cool dashboard", is_shared=False
        )

        url = reverse('dashboard-search')
        response = client.post(url, {'search': 'cool'})

        assert response.status_code == 200
        assert own_dashboard not in response.context['dashboards']
        assert len(response.context['dashboards']) == 0

    def test_given_empty_result_then_return_no_dashboards_message(
        self, db, client, non_admin_account
    ):
        """Tests that searching with no results returns a no dashboards message"""
        create_dashboard(non_admin_account, name="A cool dashboard", is_shared=True)

        url = reverse('dashboard-search')
        response = client.post(url, {'search': 'nonexistent'})

        assert response.status_code == 200
        assert 'No dashboards found' in smart_str(response.content)


def create_dashboard(account, name="Test Dashboard", is_default=False, is_shared=False):
    return AccountDashboard.objects.create(
        name=name,
        is_default=is_default,
        account=account,
        is_shared=is_shared,
    )


def create_widget(dashboard, navlet='nav.web.navlets.welcome.WelcomeNavlet'):
    return AccountNavlet.objects.create(
        dashboard=dashboard,
        account=dashboard.account,
        navlet=navlet,
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
