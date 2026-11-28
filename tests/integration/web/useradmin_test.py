from datetime import datetime, timedelta

from django.urls import reverse

import pytest
from allauth.mfa.models import Authenticator

from nav.models.api import APIToken, JWTRefreshToken
from nav.models.profiles import (
    Account,
    AccountGroup,
    Organization,
    Privilege,
    PrivilegeType,
)


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


def test_account_detail_page_should_render_for_existing_account(
    db, client, non_admin_account
):
    response = client.get(
        reverse('useradmin-account_detail', args=(non_admin_account.pk,))
    )
    assert response.status_code == 200
    assert response.context['account'] == non_admin_account


def test_when_editing_account_then_name_should_be_updated(
    db, client, non_admin_account
):
    response = client.post(
        reverse('useradmin-account_detail', args=(non_admin_account.pk,)),
        data={
            "login": non_admin_account.login,
            "name": "Renamed User",
            "password1": "",
            "password2": "",
            "submit_account": "Save changes",
        },
    )
    assert response.status_code == 302
    non_admin_account.refresh_from_db()
    assert non_admin_account.name == "Renamed User"
    assert non_admin_account.check_password("password")


def test_when_editing_account_with_new_password_then_password_should_change(
    db, client, non_admin_account
):
    new_password = "a-new-s3cret-pw"
    client.post(
        reverse('useradmin-account_detail', args=(non_admin_account.pk,)),
        data={
            "login": non_admin_account.login,
            "name": non_admin_account.name,
            "password1": new_password,
            "password2": new_password,
            "submit_account": "Save changes",
        },
    )
    non_admin_account.refresh_from_db()
    assert non_admin_account.check_password(new_password)


def test_when_passwords_do_not_match_then_account_should_not_be_saved(
    db, client, non_admin_account
):
    response = client.post(
        reverse('useradmin-account_detail', args=(non_admin_account.pk,)),
        data={
            "login": non_admin_account.login,
            "name": "Should Not Stick",
            "password1": "first-password",
            "password2": "second-password",
            "submit_account": "Save changes",
        },
    )
    assert response.status_code == 200
    assert not response.context['account_form'].is_valid()
    non_admin_account.refresh_from_db()
    assert non_admin_account.name != "Should Not Stick"
    assert non_admin_account.check_password("password")


def test_when_sudoing_to_nonexistent_account_then_it_should_redirect(db, client):
    response = client.post(
        reverse('useradmin-account_detail', args=(Account.ADMIN_ACCOUNT,)),
        data={"account": 987654, "submit_sudo": "Operate as this user"},
    )
    assert response.status_code == 302


def test_account_delete_should_ask_for_confirmation_on_get(
    db, client, non_admin_account
):
    response = client.get(
        reverse('useradmin-account_delete', args=(non_admin_account.pk,))
    )
    assert response.status_code == 200
    assert Account.objects.filter(pk=non_admin_account.pk).exists()


def test_when_deleting_account_then_account_should_be_removed(
    db, client, non_admin_account
):
    response = client.post(
        reverse('useradmin-account_delete', args=(non_admin_account.pk,))
    )
    assert response.status_code == 302
    assert response.url == reverse('useradmin-account_list')
    assert not Account.objects.filter(pk=non_admin_account.pk).exists()


@pytest.mark.parametrize("account_id", [Account.ADMIN_ACCOUNT, Account.DEFAULT_ACCOUNT])
def test_when_deleting_system_account_then_it_should_be_kept(db, client, account_id):
    response = client.post(reverse('useradmin-account_delete', args=(account_id,)))
    assert response.status_code == 302
    assert response.url == reverse('useradmin-account_detail', args=(account_id,))
    assert Account.objects.filter(pk=account_id).exists()


def test_when_deleting_nonexistent_account_then_it_should_redirect_to_list(db, client):
    response = client.post(reverse('useradmin-account_delete', args=(987654,)))
    assert response.status_code == 302
    assert response.url == reverse('useradmin-account_list')


def test_when_adding_organization_to_account_then_account_should_belong_to_it(
    db, client, non_admin_account, organization
):
    response = client.post(
        reverse('useradmin-account_detail', args=(non_admin_account.pk,)),
        data={"organization": organization.pk, "submit_org": "Add organization"},
    )
    assert response.status_code == 302
    assert organization in non_admin_account.organizations.all()


def test_when_removing_organization_from_account_then_membership_should_end(
    db, client, non_admin_account, organization
):
    non_admin_account.organizations.add(organization)
    url = reverse(
        'useradmin-account_organization_remove',
        args=(non_admin_account.pk, organization.pk),
    )
    assert client.get(url).status_code == 200
    assert organization in non_admin_account.organizations.all()

    response = client.post(url)
    assert response.status_code == 302
    assert organization not in non_admin_account.organizations.all()


def test_when_adding_group_to_account_then_account_should_be_a_member(
    db, client, non_admin_account, group
):
    response = client.post(
        reverse('useradmin-account_detail', args=(non_admin_account.pk,)),
        data={"group": group.pk, "submit_group": "Add membership"},
    )
    assert response.status_code == 302
    assert group in non_admin_account.groups.all()


def test_when_adding_default_account_to_admin_group_then_it_should_be_refused(
    db, client, default_account
):
    admin_group = AccountGroup.objects.get(pk=AccountGroup.ADMIN_GROUP)
    client.post(
        reverse('useradmin-account_detail', args=(default_account.pk,)),
        data={"group": admin_group.pk, "submit_group": "Add membership"},
    )
    assert admin_group not in default_account.groups.all()


def test_when_removing_group_from_account_then_membership_should_end(
    db, client, non_admin_account, group
):
    group.accounts.add(non_admin_account)
    url = reverse(
        'useradmin-account_group_remove', args=(non_admin_account.pk, group.pk)
    )
    assert client.get(url).status_code == 200
    assert group in non_admin_account.groups.all()

    response = client.post(url)
    assert response.status_code == 302
    assert group not in non_admin_account.groups.all()


def test_when_removing_account_from_protected_group_then_it_should_be_refused(
    db, client, non_admin_account
):
    everyone = AccountGroup.objects.get(pk=AccountGroup.EVERYONE_GROUP)
    client.post(
        reverse(
            'useradmin-account_group_remove', args=(non_admin_account.pk, everyone.pk)
        )
    )
    assert everyone in non_admin_account.groups.all()


def test_when_removing_admin_from_admin_group_then_it_should_be_refused(
    db, client, admin_account
):
    admin_group = AccountGroup.objects.get(pk=AccountGroup.ADMIN_GROUP)
    client.post(
        reverse(
            'useradmin-account_group_remove', args=(admin_account.pk, admin_group.pk)
        )
    )
    assert admin_group in admin_account.groups.all()


def test_group_list_should_include_existing_groups(db, client, group):
    response = client.get(reverse('useradmin-group_list'))
    assert response.status_code == 200
    assert group in response.context['groups']


def test_when_creating_group_then_group_should_exist(db, client):
    response = client.post(
        reverse('useradmin-group_new'),
        data={
            "name": "netops",
            "description": "Network operators",
            "submit_group": "Save changes",
        },
    )
    group = AccountGroup.objects.get(name="netops")
    assert response.status_code == 302
    assert response.url == reverse('useradmin-group_detail', args=(group.pk,))
    assert group.description == "Network operators"
    group.delete()


def test_when_group_form_is_incomplete_then_no_group_should_be_created(db, client):
    response = client.post(
        reverse('useradmin-group_new'),
        data={"name": "nodescription", "submit_group": "Save changes"},
    )
    assert response.status_code == 200
    assert not AccountGroup.objects.filter(name="nodescription").exists()


def test_when_deleting_group_then_group_should_be_removed(db, client, group):
    url = reverse('useradmin-group_delete', args=(group.pk,))
    assert client.get(url).status_code == 200
    assert AccountGroup.objects.filter(pk=group.pk).exists()

    response = client.post(url)
    assert response.status_code == 302
    assert response.url == reverse('useradmin-group_list')
    assert not AccountGroup.objects.filter(pk=group.pk).exists()


def test_when_deleting_system_group_then_it_should_be_kept(db, client):
    response = client.post(
        reverse('useradmin-group_delete', args=(AccountGroup.ADMIN_GROUP,))
    )
    assert response.status_code == 302
    assert AccountGroup.objects.filter(pk=AccountGroup.ADMIN_GROUP).exists()


def test_when_deleting_nonexistent_group_then_it_should_redirect_to_list(db, client):
    response = client.post(reverse('useradmin-group_delete', args=(987654,)))
    assert response.status_code == 302
    assert response.url == reverse('useradmin-group_list')


def test_when_adding_account_to_group_then_account_should_be_a_member(
    db, client, group, non_admin_account
):
    response = client.post(
        reverse('useradmin-group_detail', args=(group.pk,)),
        data={"account": non_admin_account.pk, "submit_account": "Add to group"},
    )
    assert response.status_code == 302
    assert non_admin_account in group.accounts.all()


def test_when_removing_account_from_group_page_then_membership_should_end(
    db, client, group, non_admin_account
):
    group.accounts.add(non_admin_account)
    response = client.post(
        reverse('useradmin-group_account_remove', args=(group.pk, non_admin_account.pk))
    )
    assert response.status_code == 302
    assert response.url == reverse('useradmin-group_detail', args=(group.pk,))
    assert non_admin_account not in group.accounts.all()


def test_when_granting_privilege_then_group_should_have_it(
    db, client, group, privilege_type
):
    response = client.post(
        reverse('useradmin-group_detail', args=(group.pk,)),
        data={
            "type": privilege_type.pk,
            "target": "/some/path",
            "submit_privilege": "Grant",
        },
    )
    assert response.status_code == 302
    assert group.privileges.filter(type=privilege_type, target="/some/path").exists()


def test_when_granting_same_privilege_twice_then_only_one_should_exist(
    db, client, group, privilege_type
):
    data = {
        "type": privilege_type.pk,
        "target": "/some/path",
        "submit_privilege": "Grant",
    }
    url = reverse('useradmin-group_detail', args=(group.pk,))
    client.post(url, data=data)
    client.post(url, data=data)
    assert (
        group.privileges.filter(type=privilege_type, target="/some/path").count() == 1
    )


def test_when_revoking_privilege_then_group_should_lose_it(
    db, client, group, privilege_type
):
    privilege = Privilege.objects.create(
        group=group, type=privilege_type, target="/some/path"
    )
    url = reverse('useradmin-group_privilege_remove', args=(group.pk, privilege.pk))
    assert client.get(url).status_code == 200
    assert Privilege.objects.filter(pk=privilege.pk).exists()

    response = client.post(url)
    assert response.status_code == 302
    assert not Privilege.objects.filter(pk=privilege.pk).exists()


def test_token_list_should_include_existing_tokens(db, client, api_token):
    response = client.get(reverse('useradmin-token_list'))
    assert response.status_code == 200
    assert api_token in response.context['object_list']


def test_token_detail_should_render(db, client, api_token):
    response = client.get(reverse('useradmin-token_detail', args=(api_token.pk,)))
    assert response.status_code == 200
    assert response.context['object'] == api_token


def test_when_expiring_token_then_it_should_no_longer_be_valid(db, client, api_token):
    response = client.post(reverse('useradmin-token_expire', args=(api_token.pk,)))
    assert response.status_code == 302
    api_token.refresh_from_db()
    assert api_token.is_expired()


def test_token_expire_should_reject_get_requests(db, client, api_token):
    response = client.get(reverse('useradmin-token_expire', args=(api_token.pk,)))
    assert response.status_code == 405
    api_token.refresh_from_db()
    assert not api_token.is_expired()


def test_when_deleting_token_then_token_should_be_removed(db, client, api_token):
    response = client.post(reverse('useradmin-token_delete', args=(api_token.pk,)))
    assert response.status_code == 302
    assert response.url == reverse('useradmin-token_list')
    assert not APIToken.objects.filter(pk=api_token.pk).exists()


def test_when_editing_token_then_comment_and_permission_should_be_updated(
    db, client, api_token
):
    response = client.post(
        reverse('useradmin-token_edit', args=(api_token.pk,)),
        data={
            "token": api_token.token,
            "permission": "write",
            "expires": (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d"),
            "comment": "updated comment",
        },
    )
    assert response.status_code == 302
    api_token.refresh_from_db()
    assert api_token.comment == "updated comment"
    assert api_token.permission == "write"


def test_when_viewing_default_account_then_it_should_render(
    db, client, default_account
):
    response = client.get(
        reverse('useradmin-account_detail', args=(default_account.pk,))
    )
    assert response.status_code == 200


def test_when_viewing_locked_account_then_it_should_render(db, client, locked_account):
    response = client.get(
        reverse('useradmin-account_detail', args=(locked_account.pk,))
    )
    assert response.status_code == 200
    assert not response.context['account'].is_active


def test_when_editing_externally_managed_account_then_password_is_not_offered(
    db, client, non_admin_account
):
    non_admin_account.ext_sync = "ldap"
    non_admin_account.save()
    response = client.get(
        reverse('useradmin-account_detail', args=(non_admin_account.pk,))
    )
    form = response.context['account_form']
    assert 'password1' not in form.fields
    assert 'password2' not in form.fields


def test_when_removing_organization_not_on_account_then_it_should_redirect(
    db, client, non_admin_account, organization
):
    response = client.post(
        reverse(
            'useradmin-account_organization_remove',
            args=(non_admin_account.pk, organization.pk),
        )
    )
    assert response.status_code == 302
    assert response.url == reverse(
        'useradmin-account_detail', args=(non_admin_account.pk,)
    )


def test_when_removing_group_not_on_account_then_it_should_redirect(
    db, client, non_admin_account, group
):
    response = client.post(
        reverse('useradmin-account_group_remove', args=(non_admin_account.pk, group.pk))
    )
    assert response.status_code == 302
    assert response.url == reverse(
        'useradmin-account_detail', args=(non_admin_account.pk,)
    )


def test_when_removing_group_from_nonexistent_account_then_it_should_redirect(
    db, client, group
):
    response = client.post(
        reverse('useradmin-account_group_remove', args=(987654, group.pk))
    )
    assert response.status_code == 302
    assert response.url == reverse('useradmin-account_list')


def test_when_revoking_missing_privilege_then_group_should_be_unchanged(
    db, client, group
):
    response = client.post(
        reverse('useradmin-group_privilege_remove', args=(group.pk, 987654))
    )
    assert response.status_code == 302
    assert AccountGroup.objects.filter(pk=group.pk).exists()


def test_when_revoking_privilege_from_nonexistent_group_then_it_should_redirect(
    db, client
):
    response = client.post(
        reverse('useradmin-group_privilege_remove', args=(987654, 1))
    )
    assert response.status_code == 302
    assert response.url == reverse('useradmin-group_list')


def test_jwt_token_list_should_include_existing_tokens(db, client, jwt_token):
    response = client.get(reverse('useradmin-jwt_list'))
    assert response.status_code == 200
    assert jwt_token in response.context['object_list']


def test_jwt_token_detail_should_render(db, client, jwt_token):
    response = client.get(reverse('useradmin-jwt_detail', args=(jwt_token.pk,)))
    assert response.status_code == 200
    assert response.context['object'] == jwt_token


def test_when_revoking_jwt_token_then_it_should_be_marked_revoked(
    db, client, jwt_token
):
    response = client.post(reverse('useradmin-jwt_revoke', args=(jwt_token.pk,)))
    assert response.status_code == 302
    jwt_token.refresh_from_db()
    assert jwt_token.revoked


def test_jwt_revoke_should_reject_get_requests(db, client, jwt_token):
    response = client.get(reverse('useradmin-jwt_revoke', args=(jwt_token.pk,)))
    assert response.status_code == 405
    jwt_token.refresh_from_db()
    assert not jwt_token.revoked


def test_when_editing_jwt_token_then_name_and_description_should_be_updated(
    db, client, jwt_token
):
    response = client.post(
        reverse('useradmin-jwt_edit', args=(jwt_token.pk,)),
        data={"name": "renamed-jwt", "description": "new description"},
    )
    assert response.status_code == 302
    jwt_token.refresh_from_db()
    assert jwt_token.name == "renamed-jwt"
    assert jwt_token.description == "new description"


def test_when_deleting_jwt_token_then_token_should_be_removed(db, client, jwt_token):
    response = client.post(reverse('useradmin-jwt_delete', args=(jwt_token.pk,)))
    assert response.status_code == 302
    assert response.url == reverse('useradmin-jwt_list')
    assert not JWTRefreshToken.objects.filter(pk=jwt_token.pk).exists()


@pytest.fixture
def jwt_token(db):
    token = JWTRefreshToken.objects.create(
        name="test-jwt",
        expires=datetime.now() + timedelta(days=30),
        activates=datetime.now() - timedelta(days=1),
        hash="not-a-real-hash",
    )
    yield token
    token.delete()


@pytest.fixture
def group(db):
    group = AccountGroup.objects.create(name="testers", description="Test group")
    yield group
    group.delete()


@pytest.fixture
def organization(db):
    return Organization.objects.get(pk="myorg")


@pytest.fixture
def privilege_type(db):
    privilege_type, _ = PrivilegeType.objects.get_or_create(name="web_access")
    return privilege_type


@pytest.fixture
def api_token(db, admin_account):
    token = APIToken.objects.create(
        token="secret-token",
        expires=datetime.now() + timedelta(days=30),
        client=admin_account,
        comment="test token",
    )
    yield token
    token.delete()


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
