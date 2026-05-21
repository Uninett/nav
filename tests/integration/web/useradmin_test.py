from django.urls import reverse

from nav.models.profiles import Account


def test_operate_as_this_user_should_not_crash(db, client, admin_account):
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
