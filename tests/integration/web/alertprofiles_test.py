# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from random import randint

from mock import MagicMock
import pytest

from django.test.client import RequestFactory
from django.core.urlresolvers import reverse
from django.utils.encoding import smart_text

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
    assert "admin" in smart_text(response.content)


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
    assert "Saved profile" in smart_text(response.content)
    assert AlertProfile.objects.filter(name=profile_name).count() > 0


def test_alertprofiles_confirm_remove_profile(db, client, dummy_profile):
    url = reverse('alertprofiles-profile-remove')
    response = client.post(url, follow=True, data={
        'confirm': '1',
        'element': [dummy_profile.id],
    })
    assert response.status_code == 200
    assert AlertProfile.objects.filter(pk=dummy_profile.pk).count() == 0


def test_alertprofiles_remove_profile(db, client, activated_dummy_profile):
    url = reverse('alertprofiles-profile-remove')
    response = client.post(url, follow=True, data={
        'profile': [activated_dummy_profile.id],
    })
    assert response.status_code == 200
    assert "Confirm deletion" in smart_text(response.content)
    assert activated_dummy_profile.name in smart_text(response.content)
    assert AlertProfile.objects.filter(
        pk=activated_dummy_profile.pk).count() == 1


def test_alertprofiles_activate_profile(db, client, dummy_profile):
    # remarkably, activation/deactivation of profiles belong in the remove view!
    url = reverse('alertprofiles-profile-remove')
    response = client.post(url, follow=True, data={
        'activate': dummy_profile.id,
    })
    assert response.status_code == 200
    assert "Active profile set" in smart_text(response.content)
    assert dummy_profile.name in smart_text(response.content)
    preference = AlertPreference.objects.get(account=dummy_profile.account)
    assert preference.active_profile == dummy_profile


def test_alertprofiles_deactivate_profile(db, client, activated_dummy_profile):
    # remarkably, activation/deactivation of profiles belong in the remove view!
    url = reverse('alertprofiles-profile-remove')
    response = client.post(url, follow=True, data={
        'deactivate': activated_dummy_profile.id,
    })
    assert response.status_code == 200
    print(type(response.content))
    assert "was deactivated" in smart_text(response.content)
    assert activated_dummy_profile.name in smart_text(response.content)
    preference = AlertPreference.objects.get(
        account=activated_dummy_profile.account)
    assert preference.active_profile is None

#
# fixtures and helpers
#


@pytest.fixture(scope='function')
def dummy_profile():
    account = Account.objects.get(id=Account.ADMIN_ACCOUNT)
    profile = AlertProfile(account=account,
                           name=u'ÆØÅ Profile %d' % randint(1, 1000))
    profile.save()
    return profile


@pytest.fixture(scope='function')
def activated_dummy_profile(dummy_profile):
    preference = AlertPreference(account=dummy_profile.account,
                                 active_profile=dummy_profile)
    preference.save()
    return dummy_profile
