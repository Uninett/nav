#
# Copyright (C) 2026 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Integration tests for the macwatch CLI tool"""

import pytest

from nav.bin.macwatch import post_event
from nav.models.event import EventQueue
from nav.models.manage import Cam
from nav.web.macwatch.models import MacWatch

WATCHED_MAC = "00:11:22:33:44:55"


class TestPostEvent:
    def test_when_called_then_post_event_should_return_true(self, cam, mac_watch):
        assert post_event(mac_watch, cam)

    def test_when_saving_fails_then_post_event_should_not_queue_the_event(
        self, cam, mac_watch
    ):
        cam.sysname = None  # violates eventqvar.val NOT NULL
        assert not post_event(mac_watch, cam)
        assert not EventQueue.objects.filter(
            netbox=cam.netbox, source_id="macwatch"
        ).exists()

    def test_when_called_then_post_event_should_queue_a_macwarning_event(
        self, cam, mac_watch
    ):
        post_event(mac_watch, cam)
        event = get_macwatch_event(cam.netbox)

        assert event.source_id == "macwatch"
        assert event.target_id == "eventEngine"
        assert event.event_type_id == "info"
        assert event.severity == 5
        assert event.value == 100

    def test_when_cam_has_module_then_post_event_should_include_it_in_varmap(
        self, cam, mac_watch
    ):
        cam.module = "1"
        post_event(mac_watch, cam)

        assert get_macwatch_event(cam.netbox).varmap == {
            "sysname": cam.sysname,
            "module": "1",
            "port": cam.port,
            "mac": WATCHED_MAC,
            "macwatch-mac": WATCHED_MAC,
            "alerttype": "macWarning",
        }

    def test_when_cam_has_no_module_then_post_event_should_omit_it_from_varmap(
        self, cam, mac_watch
    ):
        cam.module = ""
        post_event(mac_watch, cam)

        assert get_macwatch_event(cam.netbox).varmap == {
            "sysname": cam.sysname,
            "port": cam.port,
            "mac": WATCHED_MAC,
            "macwatch-mac": WATCHED_MAC,
            "alerttype": "macWarning",
        }

    def test_when_cam_has_no_port_then_post_event_should_post_it_as_an_empty_string(
        self, cam, mac_watch
    ):
        cam.port = None
        post_event(mac_watch, cam)

        assert get_macwatch_event(cam.netbox).varmap == {
            "sysname": cam.sysname,
            "port": "",
            "mac": WATCHED_MAC,
            "macwatch-mac": WATCHED_MAC,
            "alerttype": "macWarning",
        }


def get_macwatch_event(netbox):
    return EventQueue.objects.get(netbox=netbox, source_id="macwatch")


@pytest.fixture
def cam(db, localhost):
    """Returns an unsaved Cam record of the watched MAC on localhost"""
    return Cam(
        netbox=localhost,
        sysname=localhost.sysname,
        ifindex=1,
        port="ge-0/0/1",
        mac=WATCHED_MAC,
    )


@pytest.fixture
def mac_watch():
    """Returns an unsaved MacWatch for the watched MAC"""
    return MacWatch(mac=WATCHED_MAC)
