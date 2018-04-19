# -*- coding: utf-8 -*-
from mock import MagicMock
import pytest

from django.test.client import RequestFactory
from django.core.urlresolvers import reverse

from nav.tests.cases import DjangoTransactionTestCase
from nav.models.profiles import AlertProfile, Account
from nav.web.alertprofiles.views import set_active_profile


class ProfileTest(DjangoTransactionTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.url_root = '/alertprofiles/profiles/save/'

    def test_profile_with_nonascii_name_should_be_saved(self):
        request = self.factory.get(self.url_root)
        request.account = Account.objects.get(pk=Account.ADMIN_ACCOUNT)
        request.session = MagicMock()
        profile = AlertProfile(account=request.account, name=u'ÆØÅ')
        profile.save()

        self.assertIsNone(set_active_profile(request, profile))


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
