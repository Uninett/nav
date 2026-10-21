from django.urls import reverse

import pytest
from allauth.mfa.models import Authenticator

from nav.models.manage import NetboxGroup
from nav.models.profiles import Account, PrivilegeType
from nav.web.useradmin.forms import PrivilegeForm


def test_given_no_authenticator_then_activated_2fa_is_false(
    db, client, non_admin_account, mfa_globally_enabled
):
    response = client.get(reverse('useradmin-account_list'))
    account = next(
        a for a in response.context['accounts'] if a.pk == non_admin_account.pk
    )
    assert account.activated_2fa is False


def test_given_totp_authenticator_then_activated_2fa_is_true(
    db, client, account_with_totp, mfa_globally_enabled
):
    response = client.get(reverse('useradmin-account_list'))
    account = next(
        a for a in response.context['accounts'] if a.pk == account_with_totp.pk
    )
    assert account.activated_2fa is True


def test_given_webauthn_authenticator_then_activated_2fa_is_true(
    db, client, account_with_webauthn, mfa_globally_enabled
):
    response = client.get(reverse('useradmin-account_list'))
    account = next(
        a for a in response.context['accounts'] if a.pk == account_with_webauthn.pk
    )
    assert account.activated_2fa is True


def test_given_recovery_codes_only_then_activated_2fa_is_false(
    db, client, account_with_recovery_codes_only, mfa_globally_enabled
):
    response = client.get(reverse('useradmin-account_list'))
    account = next(
        a
        for a in response.context['accounts']
        if a.pk == account_with_recovery_codes_only.pk
    )
    assert account.activated_2fa is False


def test_when_operating_as_user_then_it_should_not_crash(db, client, admin_account):
    url = reverse('useradmin-account_detail', args=(admin_account.pk,))
    response = client.post(
        url,
        follow=True,
        data={
            "account": admin_account.pk,
            "submit_sudo": "Operate+as+this+user",
        },
    )
    assert response.status_code == 200


def test_when_creating_new_user_then_user_should_be_active(db, client, admin_account):
    response = client.post(
        reverse('useradmin-account_new'),
        follow=True,
        data={
            "login": "abc",
            "name": "abc",
            "password1": "@e!B>zm5f!}q;5%",
            "password2": "@e!B>zm5f!}q;5%",
            "submit_account": "Create account",
        },
    )

    assert response.status_code == 200
    account = Account.objects.get(login="abc")
    assert account.is_active


@pytest.fixture
def account_with_totp(non_admin_account):
    Authenticator.objects.create(
        user=non_admin_account, type=Authenticator.Type.TOTP, data={}
    )
    return non_admin_account


@pytest.fixture
def account_with_webauthn(non_admin_account):
    Authenticator.objects.create(
        user=non_admin_account, type=Authenticator.Type.WEBAUTHN, data={}
    )
    return non_admin_account


@pytest.fixture
def account_with_recovery_codes_only(non_admin_account):
    Authenticator.objects.create(
        user=non_admin_account, type=Authenticator.Type.RECOVERY_CODES, data={}
    )
    return non_admin_account


@pytest.fixture
def mfa_globally_enabled(monkeypatch):
    monkeypatch.setattr('nav.web.useradmin.utils.is_2fa_globally_enabled', lambda: True)


class TestPrivilegeForm:
    @pytest.fixture
    def device_group(self, db):
        group = NetboxGroup.objects.create(id="SDN", description="SDN switches")
        yield group
        group.delete()

    @pytest.fixture
    def portadmin_type(self, db):
        return PrivilegeType.objects.get(name="portadmin_vlan")

    @pytest.fixture
    def web_access_type(self, db):
        return PrivilegeType.objects.get(name="web_access")

    def test_when_type_is_portadmin_it_should_use_the_device_group_as_target(
        self, portadmin_type, device_group
    ):
        form = PrivilegeForm(
            {"type": portadmin_type.pk, "device_group": device_group.pk}
        )
        assert form.is_valid()
        assert form.cleaned_data["target"] == "SDN"

    def test_when_type_is_portadmin_it_should_ignore_the_target_field(
        self, portadmin_type, device_group
    ):
        form = PrivilegeForm(
            {
                "type": portadmin_type.pk,
                "target": ".*",
                "device_group": device_group.pk,
            }
        )
        assert form.is_valid()
        assert form.cleaned_data["target"] == "SDN"

    def test_when_type_is_portadmin_and_no_device_group_is_chosen_it_should_be_invalid(
        self, portadmin_type
    ):
        form = PrivilegeForm({"type": portadmin_type.pk, "target": ".*"})
        assert not form.is_valid()
        assert "device_group" in form.errors

    def test_when_device_group_does_not_exist_it_should_be_invalid(
        self, portadmin_type
    ):
        form = PrivilegeForm({"type": portadmin_type.pk, "device_group": "NOPE"})
        assert not form.is_valid()
        assert "device_group" in form.errors

    def test_when_type_is_not_portadmin_it_should_keep_the_target(
        self, web_access_type
    ):
        form = PrivilegeForm({"type": web_access_type.pk, "target": "^/foo"})
        assert form.is_valid()
        assert form.cleaned_data["target"] == "^/foo"

    def test_when_type_is_not_portadmin_and_target_is_empty_it_should_be_invalid(
        self, web_access_type
    ):
        form = PrivilegeForm({"type": web_access_type.pk})
        assert not form.is_valid()
        assert "target" in form.errors
