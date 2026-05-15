from django.urls import reverse

from allauth.mfa.models import Authenticator
import pytest


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


def test_given_no_authenticator_then_activated_2fa_is_false(
    db, client, non_admin_account
):
    response = client.get(reverse('useradmin-account_list'))
    account = next(
        a for a in response.context['accounts'] if a.pk == non_admin_account.pk
    )
    assert account.activated_2fa is False


def test_given_totp_authenticator_then_activated_2fa_is_true(
    db, client, account_with_totp
):
    response = client.get(reverse('useradmin-account_list'))
    account = next(
        a for a in response.context['accounts'] if a.pk == account_with_totp.pk
    )
    assert account.activated_2fa is True


def test_given_webauthn_authenticator_then_activated_2fa_is_true(
    db, client, account_with_webauthn
):
    response = client.get(reverse('useradmin-account_list'))
    account = next(
        a for a in response.context['accounts'] if a.pk == account_with_webauthn.pk
    )
    assert account.activated_2fa is True


def test_given_recovery_codes_only_then_activated_2fa_is_false(
    db, client, account_with_recovery_codes_only
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
