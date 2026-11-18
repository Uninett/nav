from datetime import datetime, timedelta

from django.urls import reverse
from django.utils.encoding import smart_str

from nav.models.fields import INFINITY
from nav.models.manage import Arp
from nav.web.machinetracker.views import VALID_HELP_TAB_NAMES, get_netbios_query


def test_given_collapse_option_it_should_merge_duplicate_active_rows(db, client):
    mac = "ca:fe:ba:be:f0:02"
    ip = "10.0.0.43"
    older = datetime.now() - timedelta(hours=2)
    newer = datetime.now() - timedelta(hours=1)
    Arp(ip=ip, mac=mac, sysname="router-a", start_time=older, end_time=INFINITY).save()
    Arp(ip=ip, mac=mac, sysname="router-b", start_time=newer, end_time=INFINITY).save()

    url = reverse('machinetracker-ip')
    params = {'ip_range': ip, 'period_filter': 'active', 'days': 7, 'source': 'on'}

    without = client.get(url, dict(params))
    assert without.context['ip_tracker_count'] == 2

    with_collapse = client.get(url, dict(params, collapse='on'))
    assert with_collapse.context['ip_tracker_count'] == 1
    (row,) = with_collapse.context['ip_tracker'][(ip, mac)]
    assert row.start_time == older
    assert row.end_time == INFINITY
    assert row.still_active
    assert "router-a" in row.sysname and "router-b" in row.sysname


def test_given_collapse_option_it_should_not_merge_different_macs(db, client):
    ip = "10.0.0.44"
    for mac in ("ca:fe:ba:be:f0:03", "ca:fe:ba:be:f0:04"):
        Arp(
            ip=ip,
            mac=mac,
            sysname="router-a",
            start_time=datetime.now(),
            end_time=INFINITY,
        ).save()

    url = reverse('machinetracker-ip')
    params = {'ip_range': ip, 'period_filter': 'active', 'days': 7, 'collapse': 'on'}

    response = client.get(url, params)
    assert response.context['ip_tracker_count'] == 2


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
