import datetime as dt

from django.test import TestCase

from nav.models.event import AlertHistory
from nav.models.event import AlertHistoryVariable
from nav.models.event import EventType
from nav.models.event import Subsystem
from nav.models.fields import INFINITY
from nav.models.manage import Netbox
from nav.models.manage import Category
from nav.models.manage import Room
from nav.models.manage import Organization


class NetboxQuerysetTest(TestCase):
    def setUp(self):
        # Some rows have already been created
        _netbox_data = {
            "room": Room.objects.get(id="myroom"),
            "organization": Organization.objects.get(id="myorg"),
            "category": Category.objects.get(id="SW"),
        }
        TEST_NETBOX_DATA = [
            dict(sysname="foo.bar.com", ip="158.38.152.169", **_netbox_data),
            dict(sysname="bar.bar.com", ip="158.38.152.231", **_netbox_data),
            dict(sysname="spam.bar.com", ip="158.38.152.9", **_netbox_data),
        ]

        self.netboxes = [
            Netbox.objects.create(**netbox_data) for netbox_data in TEST_NETBOX_DATA
        ]
        ah = AlertHistory.objects.create(
            source=Subsystem.objects.first(),
            netbox=self.netboxes[2],
            event_type=EventType.objects.get(id="maintenanceState"),
            start_time=dt.datetime.now(),
            value=0,
            end_time=INFINITY,  # UNRESOLVED
            severity=3,
        )
        AlertHistoryVariable.objects.create(alert_history=ah, variable="netbox")

    def test_on_maintenance_true(self):
        on_maintenance = Netbox.objects.on_maintenance(True)
        self.assertEqual(on_maintenance.count(), 1)
        self.assertEqual(on_maintenance[0], self.netboxes[2])

    def test_on_maintenance_false(self):
        # A netbox not used in this test has already been created
        not_on_maintenance = Netbox.objects.on_maintenance(False)
        self.assertIn(self.netboxes[0], not_on_maintenance)
        self.assertIn(self.netboxes[1], not_on_maintenance)
        self.assertNotIn(self.netboxes[2], not_on_maintenance)
