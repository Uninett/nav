# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from django.urls import reverse
from django.utils.encoding import smart_str

from nav.event2 import EventFactory
from nav.models.event import EventQueue
from nav.models.manage import (
    Netbox,
    Module,
    Interface,
    Device,
    NetboxProfile,
    IpdevpollJobLog,
)
from nav.web.ipdevinfo.utils import get_module_view

import pytest


def test_device_details_should_include_sysname(client, netbox):
    url = reverse('ipdevinfo-details-by-name', args=(netbox.sysname,))
    response = client.get(url)
    assert netbox.sysname in smart_str(response.content)


def test_device_details_should_match_sysname_case_insensitively(client, netbox):
    url = reverse('ipdevinfo-details-by-name', args=(netbox.sysname.upper(),))
    response = client.get(url)
    assert netbox.sysname in smart_str(response.content)


def test_port_search_should_match_case_insensitively(client, netbox):
    ifc = netbox.interfaces.all()[0]
    url = reverse(
        'ipdevinfo-interface-details-by-name',
        kwargs={
            'netbox_sysname': netbox.sysname,
            'port_name': ifc.ifdescr.upper(),
        },
    )
    response = client.get(url)
    assert response.status_code == 200
    assert ifc.ifdescr in smart_str(response.content)


def test_get_port_view_should_not_crash_on_big_interval(client, netbox):
    url = reverse(
        'ipdevinfo-get-port-view',
        kwargs={
            'netbox_sysname': netbox.sysname,
            'perspective': 'swportactive',
        },
    )
    url = url + '?interval=123123123123'
    response = client.get(url)
    assert response.status_code == 200
    assert "They did not have computers" in smart_str(response.content)


@pytest.mark.parametrize(
    "perspective",
    [
        'swportstatus',
        'swportactive',
        'gwportstatus',
        'physportstatus',
    ],
)
def test_get_module_view(netbox, perspective):
    module = netbox.modules.all()[0]
    result = get_module_view(module, perspective='swportstatus', netbox=netbox)
    assert result['object'] == module
    assert 'ports' in result


@pytest.mark.parametrize(
    "badname",
    [
        "02.44.02",  # Looks like an IP address
        "\x01\x9e$ü\x86",  # Cannot be encoded using IDNA for DNS lookups
    ],
)
def test_bad_name_should_not_crash_ipdevinfo(client, badname):
    """Tests "bad" device names to ensure they dont crash ipdevinfo lookup views"""
    url = reverse("ipdevinfo-details-by-name", kwargs={"name": badname})
    response = client.get(url)
    assert response.status_code == 200
    assert badname in smart_str(response.content)


class TestRefreshIpdevinfoJob:
    def test_given_netbox_and_job_posts_refresh_event(db, client, netbox):
        now = datetime.now()
        url = reverse(
            "refresh-ipdevinfo-job",
            kwargs={"netbox_sysname": netbox.sysname, "job_name": "dns"},
        )
        response = client.get(url)
        assert response.status_code == 200
        assert EventQueue.objects.filter(
            source_id="devBrowse",
            target_id="ipdevpoll",
            event_type_id="notification",
            netbox=netbox,
            subid="dns",
            state=EventQueue.STATE_STATELESS,
            time__gte=now,
        ).exists()

    def test_returns_loading_indicator(db, client, netbox):
        url = reverse(
            "refresh-ipdevinfo-job",
            kwargs={"netbox_sysname": netbox.sysname, "job_name": "dns"},
        )
        response = client.get(url)
        assert response.status_code == 200
        assert (
            '<img src="/static/images/select2/select2-spinner.gif" '
            'alt="refresh ongoing"/>' in smart_str(response.content)
        )


class TestRefreshIpdevinfoJobStatusQuery:
    def test_when_job_finished_returns_client(db, client, netbox):
        an_hour_ago = datetime.now() - timedelta(hours=1)
        IpdevpollJobLog.objects.create(netbox=netbox, job_name="dns", duration=30)
        url = reverse(
            "refresh-ipdevinfo-job-status-query",
            kwargs={
                "netbox_sysname": netbox.sysname,
                "job_name": "dns",
                "job_started_timestamp": str(an_hour_ago),
            },
        )
        response = client.get(url)
        assert response.status_code == 200
        assert response.headers["HX-Refresh"]

    def test_when_job_still_running_returns_loading_indicator(db, client, netbox):
        an_hour_ago = datetime.now() - timedelta(hours=1)
        for i in range(30):
            log = IpdevpollJobLog.objects.create(
                netbox=netbox,
                job_name="dns",
                duration=1,
            )
            # this needs to be done after creation due to the `auto_now_add` setting of
            # the end_time field
            log.end_time = an_hour_ago - timedelta(minutes=i)
            log.save()
        url = reverse(
            "refresh-ipdevinfo-job-status-query",
            kwargs={
                "netbox_sysname": netbox.sysname,
                "job_name": "dns",
                "job_started_timestamp": str(datetime.now()),
            },
        )
        response = client.get(url)
        assert response.status_code == 200
        assert (
            '<img src="/static/images/select2/select2-spinner.gif" '
            'alt="refresh ongoing"/>' in smart_str(response.content)
        )

    def test_when_job_runs_for_too_long_returns_error(db, client, netbox):
        an_hour_ago = datetime.now() - timedelta(hours=1)
        for i in range(30):
            log = IpdevpollJobLog.objects.create(
                netbox=netbox,
                job_name="dns",
                duration=1,
            )
            # this needs to be done after creation due to the `auto_now_add` setting of
            # the end_time field
            log.end_time = an_hour_ago - timedelta(minutes=i)
            log.save()
        url = reverse(
            "refresh-ipdevinfo-job-status-query",
            kwargs={
                "netbox_sysname": netbox.sysname,
                "job_name": "dns",
                "job_started_timestamp": str(datetime.now() - timedelta(minutes=5)),
            },
        )
        response = client.get(url)
        assert response.status_code == 200
        assert (
            "Job &#x27;dns&#x27; has been running for an unusually long time. Check the"
            " log messages for eventual errors." in smart_str(response.content)
        )

    def test_when_refresh_event_exists_returns_error(db, client, netbox):
        log = IpdevpollJobLog.objects.create(
            netbox=netbox,
            job_name="dns",
            duration=1,
        )
        # this needs to be done after creation due to the `auto_now_add`    setting of
        # the end_time field
        log.end_time = datetime.now() - timedelta(hours=1)
        log.save()
        refresh_event = EventFactory(
            "devBrowse", "ipdevpoll", event_type="notification"
        )
        event = refresh_event.notify(netbox=netbox, subid="dns")
        event.save()

        url = reverse(
            "refresh-ipdevinfo-job-status-query",
            kwargs={
                "netbox_sysname": netbox.sysname,
                "job_name": "dns",
                "job_started_timestamp": str(datetime.now() - timedelta(minutes=5)),
            },
        )
        response = client.get(url)
        assert response.status_code == 200
        assert (
            "Job &#x27;dns&#x27; was not started. Make sure that ipdevpoll is running."
            in smart_str(response.content)
        )


class TestHostInfoModal:
    def test_should_render_modal(self, client, netbox):
        url = reverse(
            "ipdevinfo-hostinfo",
            args=[netbox.sysname],
        )
        response = client.get(url)
        assert response.status_code == 200
        assert 'id="hostinfo"' in smart_str(response.content)

    def test_when_rendering_modal_then_include_sysname(self, client, netbox):
        url = reverse(
            "ipdevinfo-hostinfo",
            args=[netbox.sysname],
        )
        response = client.get(url)
        assert response.status_code == 200
        assert netbox.sysname in smart_str(response.content)


class TestPoeHintModals:
    def test_should_render_status_hint_modal(self, client, netbox):
        url = reverse('ipdevinfo-poe-status-hint-modal')
        response = client.get(url)
        assert response.status_code == 200
        assert 'id="poe-status-hint"' in smart_str(response.content)

    def test_should_render_classification_hint_modal(self, client, netbox):
        url = reverse('ipdevinfo-poe-classification-hint-modal')
        response = client.get(url)
        assert response.status_code == 200
        assert 'id="poe-classification-hint"' in smart_str(response.content)


###
#
# Fixtures
#
###


@pytest.fixture()
def netbox(db, management_profile):
    box = Netbox(
        ip='10.254.254.254',
        sysname='example-sw.example.org',
        organization_id='myorg',
        room_id='myroom',
        category_id='SW',
    )
    box.save()
    NetboxProfile(netbox=box, profile=management_profile).save()

    device = Device(serial="1234test")
    device.save()
    module = Module(device=device, netbox=box, name='Module 1', model='')
    module.save()

    interface = Interface(netbox=box, module=module, ifname='1', ifdescr='Port 1')
    interface.save()

    return box
