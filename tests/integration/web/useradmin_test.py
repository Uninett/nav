from django.urls import reverse


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
