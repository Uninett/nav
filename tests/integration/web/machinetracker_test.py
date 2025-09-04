from datetime import datetime

from django.urls import reverse
from django.utils.encoding import smart_str

from nav.models.fields import INFINITY
from nav.models.manage import Arp
from nav.web.machinetracker.views import VALID_HELP_TAB_NAMES, get_netbios_query


def test_get_netbios_query_should_not_fail(db):
    mac = "ca:fe:ba:be:f0:01"
    Arp(ip="10.0.0.42", mac=mac, start_time=datetime.now(), end_time=INFINITY).save()
    result = Arp.objects.filter(mac=mac, end_time=INFINITY).extra(
        select={"netbiosname": get_netbios_query()}
    )
    assert len(result) == 1


class TestRenderSearchHelpModal:
    def test_given_valid_tab_names_then_return_200_for_all(self, client):
        for tab_name in VALID_HELP_TAB_NAMES:
            url = reverse('machinetracker-search-help-modal', args=[tab_name])
            response = client.get(url)
            assert response.status_code == 200

    def test_given_valid_tab_names_then_return_correct_modal_id_for_all(self, client):
        for tab_name in VALID_HELP_TAB_NAMES:
            url = reverse('machinetracker-search-help-modal', args=[tab_name])
            response = client.get(url)
            assert f'id="{tab_name}-search-help"' in smart_str(response.content)

    def test_given_invalid_tab_name_then_return_400(self, client):
        url = reverse('machinetracker-search-help-modal', args=['invalid-tab-name'])
        response = client.get(url)
        assert response.status_code == 400
