from datetime import datetime, timedelta
from types import SimpleNamespace

from django.urls import reverse
from django.utils.encoding import smart_str

from nav.models.fields import INFINITY
from nav.models.manage import Arp
from nav.web.machinetracker.utils import collapse_overlapping
from nav.web.machinetracker.views import VALID_HELP_TAB_NAMES, get_netbios_query


def _row(start, end, sysname):
    return SimpleNamespace(
        ip="10.0.0.42",
        mac="ca:fe:ba:be:f0:01",
        start_time=start,
        end_time=end,
        sysname=sysname,
    )


class TestCollapseOverlapping:
    def test_given_two_still_active_rows_it_should_collapse_to_one(self):
        now = datetime.now()
        rows = [
            _row(now - timedelta(hours=1), INFINITY, "router-a"),
            _row(now - timedelta(hours=2), INFINITY, "router-b"),
        ]
        kept = collapse_overlapping(rows)
        assert len(kept) == 1
        assert kept[0].sysname == "router-a"  # newer start_time wins

    def test_given_disjoint_history_rows_it_should_preserve_them(self):
        now = datetime.now()
        rows = [
            _row(now - timedelta(hours=1), now, "router-a"),
            _row(now - timedelta(hours=4), now - timedelta(hours=3), "router-a"),
        ]
        assert len(collapse_overlapping(rows)) == 2

    def test_given_overlapping_pair_plus_disjoint_it_should_keep_two(self):
        now = datetime.now()
        rows = [
            _row(now - timedelta(hours=1), INFINITY, "router-a"),
            _row(now - timedelta(hours=2), INFINITY, "router-b"),
            _row(now - timedelta(hours=5), now - timedelta(hours=4), "router-a"),
        ]
        assert len(collapse_overlapping(rows)) == 2


def test_given_collapse_option_it_should_merge_duplicate_active_rows(db, client):
    mac = "ca:fe:ba:be:f0:02"
    ip = "10.0.0.43"
    for sysname in ("router-a", "router-b"):
        Arp(
            ip=ip,
            mac=mac,
            sysname=sysname,
            start_time=datetime.now(),
            end_time=INFINITY,
        ).save()

    url = reverse('machinetracker-ip')
    params = {'ip_range': ip, 'period_filter': 'active', 'days': 7, 'source': 'on'}

    without = client.get(url, dict(params))
    assert without.context['ip_tracker_count'] == 2

    with_collapse = client.get(url, dict(params, collapse='on'))
    assert with_collapse.context['ip_tracker_count'] == 1


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
