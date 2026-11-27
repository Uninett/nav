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
"""Integration tests for storing access sessions collected by ipdevpoll"""

from unittest.mock import Mock, patch

import pytest
from twisted.internet import defer

from nav.ipdevpoll.jobs import JobHandler
from nav.ipdevpoll.plugins import cisco_access_sessions, plugin_registry
from nav.ipdevpoll.shadows.access_session import make_session_key
from nav.models.manage import InterfaceAccessSession

IFINDEX = 10101
UNKNOWN_IFINDEX = 99999
CISCO_SYSOBJECTID = "1.3.6.1.4.1.9.1.617"
FIRST_ID = b"\x0a\x00\x00\x01"
SECOND_ID = b"\x0a\x00\x00\x02"
MAC_OCTETS = b"\x00\x11\x22\xaa\xbb\xcc"


@pytest.mark.twisted
async def test_when_sessions_are_found_then_they_should_be_stored(cisco_switch):
    await _run_job(cisco_switch, {FIRST_ID: _row(330), SECOND_ID: _row(340)})

    stored = _stored_vlans_by_key(cisco_switch)
    assert stored == {make_session_key(FIRST_ID): 330, make_session_key(SECOND_ID): 340}


@pytest.mark.twisted
async def test_when_session_changes_then_it_should_be_updated_in_place(cisco_switch):
    await _run_job(cisco_switch, {FIRST_ID: _row(330, "running")})
    before = _stored_session(cisco_switch, FIRST_ID)

    await _run_job(cisco_switch, {FIRST_ID: _row(330, "authorizationSuccess")})

    after = _stored_session(cisco_switch, FIRST_ID)
    assert after.status == InterfaceAccessSession.STATUS_AUTHORIZED
    assert after.pk == before.pk
    assert after.first_seen == before.first_seen


@pytest.mark.twisted
async def test_when_session_disappears_then_it_should_be_deleted(cisco_switch):
    await _run_job(cisco_switch, {FIRST_ID: _row(330), SECOND_ID: _row(340)})

    await _run_job(cisco_switch, {FIRST_ID: _row(330)})

    assert set(_stored_vlans_by_key(cisco_switch)) == {make_session_key(FIRST_ID)}


@pytest.mark.twisted
async def test_when_no_sessions_are_found_then_only_this_switch_should_lose_its_sessions(  # noqa: E501
    cisco_switch, other_switch_session
):
    await _run_job(cisco_switch, {FIRST_ID: _row(330)})

    await _run_job(cisco_switch, {})

    assert _stored_vlans_by_key(cisco_switch) == {}
    assert InterfaceAccessSession.objects.filter(pk=other_switch_session.pk).exists()


@pytest.mark.twisted
async def test_when_session_is_on_unknown_ifindex_then_it_should_not_be_stored(
    cisco_switch,
):
    await _run_job(
        cisco_switch, {FIRST_ID: _row(330)}, unknown_port_sessions=[SECOND_ID]
    )

    assert set(_stored_vlans_by_key(cisco_switch)) == {make_session_key(FIRST_ID)}
    assert not cisco_switch.interfaces.filter(ifindex=UNKNOWN_IFINDEX).exists()


@pytest.mark.twisted
async def test_when_identity_collection_is_turned_off_then_identity_should_be_cleared(
    cisco_switch,
):
    identity = {
        "cafSessionClientMacAddress": MAC_OCTETS,
        "cafSessionAuthUserName": "alice",
    }
    await _run_job(
        cisco_switch, {FIRST_ID: _row(330, **identity)}, collect_client_identity=True
    )
    collected = _stored_session(cisco_switch, FIRST_ID)

    await _run_job(cisco_switch, {FIRST_ID: _row(330)})

    cleared = _stored_session(cisco_switch, FIRST_ID)
    assert (collected.client_mac, collected.username) == ("00:11:22:aa:bb:cc", "alice")
    assert (cleared.client_mac, cleared.username) == (None, None)


async def _run_job(
    netbox, sessions_by_id, collect_client_identity=False, unknown_port_sessions=()
):
    job = JobHandler("access_sessions", netbox.pk, plugins=["cisco_access_sessions"])
    job.agent = Mock()
    job._create_agentproxy = Mock()
    job._destroy_agentproxy = Mock()

    sessions = {(IFINDEX, sid): row for sid, row in sessions_by_id.items()}
    sessions.update(
        ((UNKNOWN_IFINDEX, sid), _row(330)) for sid in unknown_port_sessions
    )
    mib = Mock()
    mib.get_sessions.return_value = defer.succeed(sessions)
    mib.get_session_methods.return_value = defer.succeed(
        {key: {"dot1x": "authcSuccess"} for key in sessions}
    )
    plugin = cisco_access_sessions.CiscoAccessSessions
    with (
        patch.dict(plugin_registry, {"cisco_access_sessions": plugin}),
        patch.object(cisco_access_sessions, "CiscoAuthFrameworkMib", return_value=mib),
        patch.object(
            cisco_access_sessions.CiscoAccessSessions,
            "collect_client_identity",
            collect_client_identity,
        ),
    ):
        await job.run()


def _stored_vlans_by_key(netbox):
    return dict(
        InterfaceAccessSession.objects.filter(interface__netbox=netbox).values_list(
            "session_key", "vlan_tag"
        )
    )


def _stored_session(netbox, session_id):
    return InterfaceAccessSession.objects.get(
        interface__netbox=netbox, session_key=make_session_key(session_id)
    )


def _row(vlan, status="authorizationSuccess", **identity):
    return {
        "cafSessionStatus": status,
        "cafSessionDomain": "data",
        "cafSessionAuthVlan": vlan,
        **identity,
    }


@pytest.fixture
def cisco_switch(management_profile, switch_factory):
    from nav.models.manage import NetboxProfile, NetboxType

    switch = switch_factory("access-sw.example.org", "10.99.0.1")
    switch.type = NetboxType.objects.get(sysobjectid=CISCO_SYSOBJECTID)
    switch.save()
    NetboxProfile(netbox=switch, profile=management_profile).save()
    return switch


@pytest.fixture
def other_switch_session(switch_factory):
    switch = switch_factory("other-sw.example.org", "10.99.0.2")
    return InterfaceAccessSession.objects.create(
        interface=switch.interfaces.get(), session_key=make_session_key(FIRST_ID)
    )


@pytest.fixture
def switch_factory():
    """Returns a factory for switches with one interface, committed for real.

    The transactional db fixture can't be used here: ipdevpoll reads and writes
    through its own database thread, which can't see uncommitted rows from the
    test's transaction.  So every switch created is deleted on teardown, along
    with its interfaces and sessions.
    """
    from nav.models.manage import Interface, Netbox

    created = []

    def _make(sysname, ip):
        switch = Netbox.objects.create(
            ip=ip,
            sysname=sysname,
            organization_id="myorg",
            room_id="myroom",
            category_id="SW",
        )
        created.append(switch.pk)
        Interface.objects.create(
            netbox=switch,
            ifname="GigabitEthernet1/0/1",
            ifdescr="GigabitEthernet1/0/1",
            ifindex=IFINDEX,
        )
        return switch

    yield _make
    Netbox.objects.filter(pk__in=created).delete()
