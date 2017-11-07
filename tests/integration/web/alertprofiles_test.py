# -*- coding: utf-8 -*-
from mock import MagicMock
from nav.tests.cases import DjangoTransactionTestCase
from django.test.client import RequestFactory

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
