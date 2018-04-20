# -*- coding: utf-8 -*-
from mock import MagicMock
import pytest

from django.test.client import RequestFactory
from django.core.urlresolvers import reverse

from nav.models.profiles import AlertProfile, Account, AlertPreference
from nav.web.alertprofiles.views import set_active_profile


def test_profile_with_nonascii_name_should_be_saved(db):
    factory = RequestFactory()
    request = factory.get(reverse('alertprofiles-profile-save'))
    request.account = Account.objects.get(pk=Account.ADMIN_ACCOUNT)
    request.session = MagicMock()
    profile = AlertProfile(account=request.account, name=u'ÆØÅ')
    profile.save()

    assert set_active_profile(request, profile) is None


@pytest.mark.parametrize("view", [
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
])
def test_alertprofiles_view(client, view):
    """Simple GET tests for various non-modifying alertprofiles views"""
    url = reverse(view)
    response = client.get(url)
    assert "admin" in response.content


def test_alertprofiles_save_profile(db, client):
    url = reverse('alertprofiles-profile-save')
    profile_name = 'Catch 22'

    response = client.post(url, follow=True, data={
        'name': profile_name,
        'daily_dispatch_time': '08:00',
        'weekly_dispatch_time': '08:00',
        'weekly_dispatch_day': AlertProfile.MONDAY,
    })

    assert response.status_code == 200
    print(response.content)
    assert "Saved profile" in response.content
    assert AlertProfile.objects.filter(name=profile_name).count() > 0


def test_alertprofiles_confirm_remove_profile(db, client):
    account = Account.objects.get(id=Account.ADMIN_ACCOUNT)
    profile = AlertProfile(account=account, name='Dead profile')
    profile.save()

    url = reverse('alertprofiles-profile-remove')
    response = client.post(url, follow=True, data={
        'confirm': '1',
        'element': [profile.id],
    })
    assert response.status_code == 200
    assert AlertProfile.objects.filter(pk=profile.pk).count() == 0


def test_alertprofiles_remove_profile(db, client):
    account = Account.objects.get(id=Account.ADMIN_ACCOUNT)
    profile = AlertProfile(account=account, name='Dead profile')
    profile.save()
    preference = AlertPreference(account=account, active_profile=profile)
    preference.save()

    url = reverse('alertprofiles-profile-remove')
    response = client.post(url, follow=True, data={
        'profile': [profile.id],
    })
    assert response.status_code == 200
    assert "Confirm deletion" in response.content
    assert profile.name in response.content
    assert AlertProfile.objects.filter(pk=profile.pk).count() == 1


def test_alertprofiles_activate_profile(db, client):
    account = Account.objects.get(id=Account.ADMIN_ACCOUNT)
    profile = AlertProfile(account=account, name='My profile')
    profile.save()

    # remarkably, activation/deactivation of profiles belong in the remove view!
    url = reverse('alertprofiles-profile-remove')
    response = client.post(url, follow=True, data={
        'activate': profile.id,
    })
    assert response.status_code == 200
    assert "Active profile set" in response.content
    assert profile.name in response.content
    preference = AlertPreference.objects.get(account=account)
    assert preference.active_profile == profile


def test_alertprofiles_deactivate_profile(db, client):
    account = Account.objects.get(id=Account.ADMIN_ACCOUNT)
    profile = AlertProfile(account=account, name='My profile')
    profile.save()
    preference = AlertPreference(account=account, active_profile=profile)
    preference.save()

    # remarkably, activation/deactivation of profiles belong in the remove view!
    url = reverse('alertprofiles-profile-remove')
    response = client.post(url, follow=True, data={
        'deactivate': profile.id,
    })
    assert response.status_code == 200
    print(response.content)
    assert "was deactivated" in response.content
    assert profile.name in response.content
    preference = AlertPreference.objects.get(account=account)
    assert preference.active_profile is None

