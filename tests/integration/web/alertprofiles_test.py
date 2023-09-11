# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from random import randint

from mock import MagicMock
import pytest

from django.test.client import RequestFactory
from django.urls import reverse
from nav.compatibility import smart_str
from nav.models.profiles import (
    Account,
    AlertAddress,
    AlertPreference,
    AlertProfile,
    AlertSender,
    Expression,
    Filter,
    MatchField,
    Operator,
)
from nav.web.alertprofiles.views import set_active_profile


def test_profile_with_nonascii_name_should_be_saved(db):
    factory = RequestFactory()
    request = factory.get(reverse('alertprofiles-profile-save'))
    request.account = Account.objects.get(pk=Account.ADMIN_ACCOUNT)
    request.session = MagicMock()
    profile = AlertProfile(account=request.account, name=u'ÆØÅ')
    profile.save()

    assert set_active_profile(request, profile) is None


@pytest.mark.parametrize(
    "view",
    [
        'alertprofiles-overview',
        'alertprofiles-profile',
        'alertprofiles-profile-new',
        'alertprofiles-sms',
        'alertprofiles-address',
        'alertprofiles-address-new',
        'alertprofiles-filters',
        'alertprofiles-filters-new',
        'alertprofiles-filter_groups',
        'alertprofiles-filter_groups-new',
        'alertprofiles-matchfields',
        'alertprofiles-matchfields-new',
        'alertprofiles-permissions',
    ],
)
def test_alertprofiles_view(client, view):
    """Simple GET tests for various non-modifying alertprofiles views"""
    url = reverse(view)
    response = client.get(url)
    assert "admin" in smart_str(response.content)


def test_alertprofiles_save_profile(db, client):
    url = reverse('alertprofiles-profile-save')
    profile_name = 'Catch 22'

    response = client.post(
        url,
        follow=True,
        data={
            'name': profile_name,
            'daily_dispatch_time': '08:00',
            'weekly_dispatch_time': '08:00',
            'weekly_dispatch_day': AlertProfile.MONDAY,
        },
    )

    assert response.status_code == 200
    print(response.content)
    assert "Saved profile" in smart_str(response.content)
    assert AlertProfile.objects.filter(name=profile_name).count() > 0


def test_alertprofiles_confirm_remove_profile(db, client, dummy_profile):
    url = reverse('alertprofiles-profile-remove')
    response = client.post(
        url,
        follow=True,
        data={
            'confirm': '1',
            'element': [dummy_profile.id],
        },
    )
    assert response.status_code == 200
    assert AlertProfile.objects.filter(pk=dummy_profile.pk).count() == 0


def test_alertprofiles_remove_profile(db, client, activated_dummy_profile):
    url = reverse('alertprofiles-profile-remove')
    response = client.post(
        url,
        follow=True,
        data={
            'profile': [activated_dummy_profile.id],
        },
    )
    assert response.status_code == 200
    assert "Confirm deletion" in smart_str(response.content)
    assert activated_dummy_profile.name in smart_str(response.content)
    assert AlertProfile.objects.filter(pk=activated_dummy_profile.pk).count() == 1


def test_alertprofiles_activate_profile(db, client, dummy_profile):
    # remarkably, activation/deactivation of profiles belong in the remove view!
    url = reverse('alertprofiles-profile-remove')
    response = client.post(
        url,
        follow=True,
        data={
            'activate': dummy_profile.id,
        },
    )
    assert response.status_code == 200
    assert "Active profile set" in smart_str(response.content)
    assert dummy_profile.name in smart_str(response.content)
    preference = AlertPreference.objects.get(account=dummy_profile.account)
    assert preference.active_profile == dummy_profile


def test_alertprofiles_deactivate_profile(db, client, activated_dummy_profile):
    # remarkably, activation/deactivation of profiles belong in the remove view!
    url = reverse('alertprofiles-profile-remove')
    response = client.post(
        url,
        follow=True,
        data={
            'deactivate': activated_dummy_profile.id,
        },
    )
    assert response.status_code == 200
    print(type(response.content))
    assert "was deactivated" in smart_str(response.content)
    assert activated_dummy_profile.name in smart_str(response.content)
    preference = AlertPreference.objects.get(account=activated_dummy_profile.account)
    assert preference.active_profile is None


def test_alertprofiles_add_private_filter_should_succeed(client):
    """Tests that an admin can POST a new private filter"""
    url = reverse("alertprofiles-filters-save")
    data = {
        "id": "",
        "name": "foobar",
        "owner": "admin",
    }
    response = client.post(url, data=data, follow=True)
    assert response.status_code == 200


def test_alertprofiles_add_public_filter_should_succeed(client):
    """Tests that an admin can POST a new public filter"""
    url = reverse("alertprofiles-filters-save")
    data = {
        "id": "",
        "name": "foobar",
    }
    response = client.post(url, data=data, follow=True)
    assert response.status_code == 200


def test_alertprofiles_add_expression_with_valid_ipv4_address_should_succeed(
    client, dummy_filter
):
    """Tests that an expression with a valid IPv4 address can be added"""
    ip_match_field = MatchField.objects.get(data_type=MatchField.IP)
    url = reverse("alertprofiles-filters-saveexpression")
    data = {
        "filter": dummy_filter.pk,
        "match_field": ip_match_field.pk,
        "operator": Operator.EQUALS,
        "value": "172.0.0.1",
    }
    response = client.post(url, data=data, follow=True)
    assert response.status_code == 200
    assert Expression.objects.filter(
        filter=dummy_filter,
        match_field=ip_match_field,
        operator=Operator.EQUALS,
        value=data["value"],
    ).exists()
    assert f"Added expression to filter {dummy_filter}" in smart_str(response.content)


def test_alertprofiles_add_expression_with_valid_ipv6_address_should_succeed(
    client, dummy_filter
):
    """Tests that an expression with a valid IPv6 address can be added"""
    url = reverse("alertprofiles-filters-saveexpression")
    ip_match_field = MatchField.objects.get(data_type=MatchField.IP)
    data = {
        "filter": dummy_filter.pk,
        "match_field": ip_match_field.pk,
        "operator": Operator.EQUALS,
        "value": "2001:db8:3333:4444:5555:6666:7777:8888",
    }
    response = client.post(url, data=data, follow=True)
    assert response.status_code == 200
    assert Expression.objects.filter(
        filter=dummy_filter,
        match_field=ip_match_field,
        operator=Operator.EQUALS,
        value=data["value"],
    ).exists()
    assert f"Added expression to filter {dummy_filter}" in smart_str(response.content)


def test_alertprofiles_add_expression_with_valid_cidr_address_should_succeed(
    client, dummy_filter
):
    """Tests that an expression with a valid CIDR address can be added"""
    url = reverse("alertprofiles-filters-saveexpression")
    ip_match_field = MatchField.objects.get(data_type=MatchField.IP)
    data = {
        "filter": dummy_filter.pk,
        "match_field": ip_match_field.pk,
        "operator": Operator.EQUALS,
        "value": "129.241.190.0/24",
    }
    response = client.post(url, data=data, follow=True)
    assert response.status_code == 200
    assert Expression.objects.filter(
        filter=dummy_filter,
        match_field=ip_match_field,
        operator=Operator.EQUALS,
        value=data["value"],
    ).exists()
    assert f"Added expression to filter {dummy_filter}" in smart_str(response.content)


def test_alertprofiles_add_expression_with_non_valid_ip_address_should_fail(
    client, dummy_filter
):
    """Tests that an expression with a not valid IP address cannot be added"""
    ip_match_field = MatchField.objects.get(data_type=MatchField.IP)
    url = reverse("alertprofiles-filters-saveexpression")
    data = {
        "filter": dummy_filter.pk,
        "match_field": ip_match_field.pk,
        "operator": Operator.EQUALS,
        "value": "wrong",
    }
    response = client.post(url, data=data, follow=True)
    assert response.status_code == 200
    assert not Expression.objects.filter(
        filter=dummy_filter,
        match_field=ip_match_field,
        operator=Operator.EQUALS,
        value=data["value"],
    ).exists()
    assert f"Invalid IP address: {data['value']}" in smart_str(response.content)


def test_alertprofiles_add_expression_with_non_valid_cidr_address_should_fail(
    client, dummy_filter
):
    """Tests that an expression with a not valid CIDR address cannot be added"""
    ip_match_field = MatchField.objects.get(data_type=MatchField.IP)
    url = reverse("alertprofiles-filters-saveexpression")
    data = {
        "filter": dummy_filter.pk,
        "match_field": ip_match_field.pk,
        "operator": Operator.EQUALS,
        "value": "10.0.2.1/28",
    }
    response = client.post(url, data=data, follow=True)
    assert response.status_code == 200
    assert not Expression.objects.filter(
        filter=dummy_filter,
        match_field=ip_match_field,
        operator=Operator.EQUALS,
        value=data["value"],
    ).exists()
    assert f"Invalid IP address: {data['value']}" in smart_str(response.content)


def test_alertprofiles_add_expression_with_multiple_valid_ip_addresses_should_succeed(
    client, dummy_filter
):
    """Tests that an expression with multiple valid IP addresses can be added"""
    ip_match_field = MatchField.objects.get(data_type=MatchField.IP)
    url = reverse("alertprofiles-filters-saveexpression")
    data = {
        "filter": dummy_filter.pk,
        "match_field": ip_match_field.pk,
        "operator": Operator.IN,
        "value": "172.0.0.1 2001:db8:3333:4444:5555:6666:7777:8888 129.241.190.0/24",
    }
    response = client.post(url, data=data, follow=True)
    assert response.status_code == 200
    assert Expression.objects.filter(
        filter=dummy_filter,
        match_field=ip_match_field,
        operator=Operator.IN,
        value=data["value"].replace(' ', '|'),
    ).exists()
    assert f"Added expression to filter {dummy_filter}" in smart_str(response.content)


def test_alertprofiles_add_expression_with_multiple_non_valid_ip_addresses_should_fail(
    client, dummy_filter
):
    """Tests that an expression with a not valid IP address cannot be added"""
    ip_match_field = MatchField.objects.get(data_type=MatchField.IP)
    valid_ip = "172.0.0.1"
    invalid_ip = "wrong"
    url = reverse("alertprofiles-filters-saveexpression")
    data = {
        "filter": dummy_filter.pk,
        "match_field": ip_match_field.pk,
        "operator": Operator.IN,
        "value": f"{valid_ip} {invalid_ip}",
    }
    response = client.post(url, data=data, follow=True)
    assert response.status_code == 200
    assert not Expression.objects.filter(
        filter=dummy_filter,
        match_field=ip_match_field,
        operator=Operator.IN,
        value=data["value"],
    ).exists()
    assert f"Invalid IP address: {invalid_ip}" in smart_str(response.content)


def test_alertprofiles_add_expression_with_multiple_alert_types_should_succeed(
    client, dummy_filter
):
    """Tests that an expression with multiple alert types can be added"""
    string_match_field = MatchField.objects.get(name="Alert type")
    url = reverse("alertprofiles-filters-saveexpression")
    data = {
        "filter": dummy_filter.pk,
        "match_field": string_match_field.pk,
        "operator": Operator.IN,
        "value": ["apDown", "apUp"],
    }
    response = client.post(url, data=data, follow=True)
    assert response.status_code == 200
    assert Expression.objects.filter(
        filter=dummy_filter,
        match_field=string_match_field,
        operator=Operator.IN,
        value="|".join(data["value"]),
    ).exists()
    assert f"Added expression to filter {dummy_filter}" in smart_str(response.content)


def test_set_accountgroup_permissions_should_not_crash(db, client):
    """Regression test for #2281"""
    url = reverse('alertprofiles-permissions-save')
    response = client.post(
        url,
        follow=True,
        data={
            'filter_group': '71',  # G01 All alerts, as hardcoded in navprofiles.sql
            'group': '3',  # Authenticated users
        },
    )
    assert response.status_code == 200


def test_alertprofiles_add_slack_address_with_valid_url_should_succeed(client):
    """Tests that a slack address with a valid absolute url can be added"""
    valid_url = "https://example.com"
    slack = AlertSender.objects.get(name=AlertSender.SLACK)
    url = reverse("alertprofiles-address-save")
    data = {
        "address": valid_url,
        "type": slack.pk,
    }
    response = client.post(url, data=data, follow=True)
    assert response.status_code == 200
    assert AlertAddress.objects.filter(
        type=slack,
        address=valid_url,
    ).exists()
    assert f"Saved address {valid_url}" in smart_str(response.content)


def test_alertprofiles_add_slack_address_with_a_valid_but_not_absolute_url_should_fail(
    client,
):
    """Tests that a slack address with a not valid url cannot be added"""
    non_absolute_url = "www.example.com"
    slack = AlertSender.objects.get(name=AlertSender.SLACK)
    url = reverse("alertprofiles-address-save")
    data = {
        "address": non_absolute_url,
        "type": slack.pk,
    }
    response = client.post(url, data=data, follow=True)
    assert response.status_code == 200
    assert not AlertAddress.objects.filter(
        type=slack,
        address=non_absolute_url,
    ).exists()
    assert "Not a valid absolute url." in smart_str(response.content)


def test_alertprofiles_add_slack_address_with_non_valid_url_should_fail(client):
    """Tests that a slack address with a not valid url cannot be added"""
    invalid_url = "abc"
    slack = AlertSender.objects.get(name=AlertSender.SLACK)
    url = reverse("alertprofiles-address-save")
    data = {
        "address": invalid_url,
        "type": slack.pk,
    }
    response = client.post(url, data=data, follow=True)
    assert response.status_code == 200
    assert not AlertAddress.objects.filter(
        type=slack,
        address=invalid_url,
    ).exists()
    assert "Not a valid absolute url." in smart_str(response.content)


def test_alertprofiles_add_valid_email_address_should_succeed(client):
    """Tests that a valid email address can be added"""
    valid_email_address = "hello@example.com"
    email = AlertSender.objects.get(name=AlertSender.EMAIL)
    url = reverse("alertprofiles-address-save")
    data = {
        "address": valid_email_address,
        "type": email.pk,
    }
    response = client.post(url, data=data, follow=True)
    assert response.status_code == 200
    assert AlertAddress.objects.filter(
        type=email,
        address=valid_email_address,
    ).exists()
    assert f"Saved address {valid_email_address}" in smart_str(response.content)


def test_alertprofiles_add_invalid_email_address_should_fail(client):
    """Tests that an invalid email address cannot be added"""
    invalid_email_address = "abc"
    email = AlertSender.objects.get(name=AlertSender.EMAIL)
    url = reverse("alertprofiles-address-save")
    data = {
        "address": invalid_email_address,
        "type": email.pk,
    }
    response = client.post(url, data=data, follow=True)
    assert response.status_code == 200
    assert not AlertAddress.objects.filter(
        type=email,
        address=invalid_email_address,
    ).exists()
    assert "Not a valid email address." in smart_str(response.content)


def test_alertprofiles_add_valid_phone_number_should_succeed(client):
    """Tests that a valid phone number can be added"""
    valid_phone_number = "47474747"
    sms = AlertSender.objects.get(name=AlertSender.SMS)
    url = reverse("alertprofiles-address-save")
    data = {
        "address": valid_phone_number,
        "type": sms.pk,
    }
    response = client.post(url, data=data, follow=True)
    assert response.status_code == 200
    assert AlertAddress.objects.filter(
        type=sms,
        address=valid_phone_number,
    ).exists()
    assert f"Saved address {valid_phone_number}" in smart_str(response.content)


def test_alertprofiles_add_invalid_phone_number_should_fail(client):
    """Tests that an invalid phone number cannot be added"""
    invalid_phone_number = "abc"
    sms = AlertSender.objects.get(name=AlertSender.SMS)
    url = reverse("alertprofiles-address-save")
    data = {
        "address": invalid_phone_number,
        "type": sms.pk,
    }
    response = client.post(url, data=data, follow=True)
    assert response.status_code == 200
    assert not AlertAddress.objects.filter(
        type=sms,
        address=invalid_phone_number,
    ).exists()
    assert "Not a valid phone number." in smart_str(response.content)


#
# fixtures and helpers
#


@pytest.fixture(scope='function')
def dummy_profile():
    account = Account.objects.get(id=Account.ADMIN_ACCOUNT)
    profile = AlertProfile(account=account, name=u'ÆØÅ Profile %d' % randint(1, 1000))
    profile.save()
    return profile


@pytest.fixture(scope='function')
def activated_dummy_profile(dummy_profile):
    preference = AlertPreference(
        account=dummy_profile.account, active_profile=dummy_profile
    )
    preference.save()
    return dummy_profile


@pytest.fixture(scope="function")
def dummy_filter():
    filtr = Filter(name="dummy", owner=Account.objects.get(id=Account.ADMIN_ACCOUNT))
    filtr.save()
    return filtr
