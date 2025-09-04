from unittest.mock import patch

import pytest
from django.test.client import RequestFactory
from django.urls import reverse

from nav.models.profiles import Account, AccountDashboard, AccountNavlet
from nav.web.navlets import add_navlet, modify_navlet


class TestAddUserNavletView:
    def test_when_using_get_method_then_return_400(self, client, dashboard):
        response = client.get(_get_dashboard_url(dashboard))
        assert response.status_code == 400

    def test_given_payload_without_navlet_then_return_400(self, client, dashboard):
        response = client.post(_get_dashboard_url(dashboard), data={})
        assert response.status_code == 400

    def test_given_payload_with_navlet_then_return_200(
        self, client, admin_account, dashboard
    ):
        payload = {'navlet': 'nav.web.navlets.alert.AlertWidget'}
        response = client.post(_get_dashboard_url(dashboard), data=payload)
        assert response.status_code == 200

    def test_given_payload_with_navlet_for_different_account_then_return_404(
        self, client, other_account_dashboard
    ):
        payload = {'navlet': 'nav.web.navlets.alert.AlertWidget'}
        response = client.post(
            _get_dashboard_url(other_account_dashboard), data=payload
        )
        assert response.status_code == 404


class TestAddNavletModalView:
    """Integrations tests for showing the add navlet modal."""

    def test_should_render_add_navlet_modal(self, client, dashboard):
        response = client.get(reverse('add-navlet-modal', args=[dashboard.id]))
        assert response.status_code == 200
        assert 'id="navlet-list"' in str(response.content)


class TestAddNavletView:
    """Integration tests for the creation of a new navlet."""

    def test_add_navlet_with_no_preferences(self, admin_account, dashboard):
        navlet_class = 'nav.web.navlets.alert.AlertWidget'
        navlet_obj = add_navlet(admin_account, navlet_class, dashboard=dashboard)
        assert navlet_obj.preferences == {} or isinstance(navlet_obj.preferences, dict)


class TestModifyNavlet:
    @patch('nav.web.navlets.can_modify_navlet', return_value=False)
    def test_when_account_is_not_permitted_to_modify_then_return_403(
        self, client, admin_account, dashboard
    ):
        def dummy_func(navlet, _request):
            return navlet

        request = RequestFactory().post('/fake-url')
        response = modify_navlet(
            dummy_func, admin_account, request, "Something went wrong"
        )
        assert response.status_code == 403


class TestRemoveUserNavletModalView:
    """Integration tests for showing the remove navlet modal."""

    def test_should_render_remove_navlet_modal(self, client, new_navlet):
        response = client.get(reverse('remove-user-navlet-modal', args=[new_navlet.pk]))
        assert response.status_code == 200
        assert f'name="navletid" value="{new_navlet.id}"' in str(response.content)


class TestRemoveUserNavletView:
    """Integration tests for removing a user navlet."""

    def test_when_navletid_not_in_payload_then_return_400(self, client):
        response = client.post(reverse('remove-user-navlet'), data={})
        assert response.status_code == 400

    def test_given_existing_navlet_then_remove_it(self, client, new_navlet):
        payload = {'navletid': new_navlet.pk}
        response = client.post(reverse('remove-user-navlet'), data=payload)
        assert response.status_code == 200

    def test_given_existing_navlet_and_insufficient_permissions_then_return_error(
        self, client, new_navlet
    ):
        with patch('nav.web.navlets.can_modify_navlet', return_value=False):
            response = client.post(
                reverse('remove-user-navlet'), data={'navletid': new_navlet.pk}
            )
        assert b"You are not permitted to remove this widget" in response.content

    def test_given_non_existing_navlet_then_return_error(self, client):
        payload = {'navletid': 99999}
        response = client.post(reverse('remove-user-navlet'), data=payload)
        assert b"This widget no longer exists" in response.content


def _get_dashboard_url(dashboard: AccountDashboard):
    return reverse('add-user-navlet', args=[dashboard.id])


@pytest.fixture
def dashboard(db, admin_account):
    dashboard = AccountDashboard(
        account=admin_account, name='Test Dashboard', is_default=True
    )
    dashboard.save()
    yield dashboard
    dashboard.delete()


@pytest.fixture
def other_account_dashboard(db):
    account = Account(
        login='other_user',
        name='Other User',
        password='apasswordthatislongenough123',
    )
    account.save()
    dashboard = AccountDashboard(
        account=account, name='Other Dashboard', is_default=True
    )
    dashboard.save()
    yield dashboard
    account.delete()


@pytest.fixture
def new_navlet(db, admin_account, dashboard):
    navlet = AccountNavlet(
        account=admin_account,
        dashboard=dashboard,
        navlet='nav.web.navlets.alert.AlertWidget',
        preferences={},
    )
    navlet.save()
    yield navlet
    navlet.delete()
