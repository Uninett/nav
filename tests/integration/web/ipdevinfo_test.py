# -*- coding: utf-8 -*-

import re
from datetime import datetime, timedelta
from unittest.mock import patch

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
    Sensor,
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


def test_when_module_name_contains_slash_then_module_details_should_not_crash(
    client, netbox
):
    module = netbox.modules.first()
    module.name = "1/A"
    module.save()
    url = reverse('ipdevinfo-module-details', args=(netbox.sysname, "1/A"))
    response = client.get(url)
    assert netbox.sysname in smart_str(response.content)
    assert module.name in smart_str(response.content)


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


class TestSensorDetailsViews:
    """200-check coverage for the htmx-driven sensor-details endpoints.

    Previously the sensor-details web layer had no test coverage at all,
    which would let a URL-pattern or import regression slip through CI
    unnoticed (cf. the trailing-slash bug that hid in the watchdog views
    for several releases).
    """

    def test_when_logged_in_then_sensor_details_should_respond_with_200(
        self, client, boolean_sensor
    ):
        url = reverse('sensor-details', args=[boolean_sensor.pk])
        response = client.get(url)
        assert response.status_code == 200

    def test_when_logged_in_then_sensor_on_off_state_should_respond_with_200(
        self, client, boolean_sensor
    ):
        url = reverse('sensor-on-off-state', args=[boolean_sensor.pk])
        with patch('nav.web.ipdevinfo.views.get_metric_data', return_value=[]):
            response = client.get(url)
        assert response.status_code == 200

    def test_when_posting_with_sensor_id_then_add_user_navlet_sensor_should_respond_with_200(  # noqa: E501
        self, client, boolean_sensor
    ):
        url = reverse('add-user-navlet-sensor')
        response = client.post(f"{url}?sensor_id={boolean_sensor.pk}")
        assert response.status_code == 200

    def test_when_getting_then_add_user_navlet_sensor_should_respond_with_400(
        self, client
    ):
        url = reverse('add-user-navlet-sensor')
        response = client.get(url)
        assert response.status_code == 400


###
#
# Fixtures
#
###


@pytest.fixture()
def boolean_sensor(db, netbox):
    """A minimal boolean sensor attached to the test netbox."""
    return Sensor.objects.create(
        netbox=netbox,
        oid='.1.3.6.1.4.1.1.1',
        unit_of_measurement=Sensor.UNIT_TRUTHVALUE,
        data_scale=Sensor.SCALE_UNITS,
        precision=0,
        human_readable='Example boolean sensor',
        name='example-boolean',
        internal_name='example-boolean',
        mib='EXAMPLE-MIB',
        on_state_sys=1,
    )


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


def _interface_details_url(interface):
    return reverse(
        'ipdevinfo-interface-details',
        kwargs={
            'netbox_sysname': interface.netbox.sysname,
            'port_id': interface.id,
        },
    )


class TestPortDetailsTopology:
    def test_when_viewing_aggregate_then_the_page_should_render_the_topology_tree(
        self, client, juniper_aggregate_factory
    ):
        topo = juniper_aggregate_factory()
        response = client.get(_interface_details_url(topo["ae0"]))
        content = smart_str(response.content)
        assert response.status_code == 200
        assert 'topology-tree' in content
        assert 'aria-current="true"' in content
        assert topo["dist_a"].sysname in content
        assert topo["dist_b"].sysname in content
        assert 'topology-legend' in content
        assert 'Layered below (ifStack)' in content

    def test_when_aggregate_has_no_neighbour_then_the_current_node_should_show_na(
        self, client, juniper_aggregate_factory
    ):
        topo = juniper_aggregate_factory()
        response = client.get(_interface_details_url(topo["ae0"]))
        content = smart_str(response.content)
        # The N/A must belong to the current (aggregate) node: only its branch
        # emits the "&rarr; <em>N/A</em>" arrow sequence, so anchor on that.
        assert re.search(
            r'topology-current-interface.*?&rarr;\s*<em>N/A</em>', content, re.S
        )

    def test_when_viewing_lone_port_with_neighbour_then_no_legend_should_be_shown(
        self, client, netbox_factory, interface_factory
    ):
        peer = netbox_factory("peer.example.org", "10.4.0.2")
        remote = interface_factory(peer, "GigabitEthernet0/2", 1)
        box = netbox_factory("cisco-sw.example.org", "10.4.0.1")
        port = interface_factory(box, "GigabitEthernet1/0/1", 1, to_interface=remote)

        response = client.get(_interface_details_url(port))
        content = smart_str(response.content)
        assert response.status_code == 200
        assert 'aria-current="true"' in content
        assert peer.sysname in content
        assert 'topology-legend' not in content

    def test_when_viewing_lone_port_without_neighbour_then_it_should_show_na(
        self, client, netbox_factory, interface_factory
    ):
        box = netbox_factory("cisco-sw2.example.org", "10.5.0.1")
        port = interface_factory(box, "GigabitEthernet1/0/2", 1)

        response = client.get(_interface_details_url(port))
        content = smart_str(response.content)
        assert response.status_code == 200
        assert '<em>N/A</em>' in content
        assert 'topology-legend' not in content

    def test_when_a_member_is_down_then_only_that_member_should_be_struck_through(
        self, client, juniper_aggregate_factory
    ):
        topo = juniper_aggregate_factory(down_member=True)
        response = client.get(_interface_details_url(topo["ae0"]))
        content = smart_str(response.content)
        assert '(Down)' in content
        assert '<del>xe-0/2/3</del>' in content  # the down physical member
        assert '<del>xe-0/2/2</del>' not in content  # the up physical is not struck
