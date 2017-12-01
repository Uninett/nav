from django.core.urlresolvers import reverse
from django.http import Http404
from django.test.client import RequestFactory
from mock import MagicMock

from nav.models.profiles import Account, AlertProfile
from nav.web.seeddb.page.netbox.edit import netbox_edit

import pytest


def test_usage_edit_url_should_allow_slashes():
    assert reverse('seeddb-usage-edit', args=('TEST/SLASH',))


def test_editing_deleted_netboxes_should_raise_404():
    netboxid = 666  # Assuming no such netbox exists in test data set!
    factory = RequestFactory()
    url = reverse('seeddb-netbox-edit', args=(netboxid,))
    request = factory.get(url)
    request.account = Account.objects.get(pk=Account.ADMIN_ACCOUNT)
    request.session = MagicMock()

    with pytest.raises(Http404):
        netbox_edit(request, netboxid)
