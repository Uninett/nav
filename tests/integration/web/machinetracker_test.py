from datetime import datetime

from nav.models.fields import INFINITY
from nav.models.manage import Arp
from nav.web.machinetracker.views import get_netbios_query


def test_get_netbios_query_should_not_fail(db):
    mac = "ca:fe:ba:be:f0:01"
    Arp(ip="10.0.0.42", mac=mac, start_time=datetime.now(), end_time=INFINITY).save()
    result = Arp.objects.filter(mac=mac, end_time=INFINITY).extra(
        select={"netbiosname": get_netbios_query()}
    )
    assert len(result) == 1
