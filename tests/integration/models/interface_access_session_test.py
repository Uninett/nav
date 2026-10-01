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
"""Tests for the database constraints of the InterfaceAccessSession model"""

import pytest
from django.db import IntegrityError, transaction

from nav.models.manage import InterfaceAccessSession


def test_when_interface_is_deleted_then_its_access_sessions_should_be_deleted(
    interface,
):
    session = InterfaceAccessSession.objects.create(
        interface=interface, session_key="a"
    )

    interface.delete()

    assert not InterfaceAccessSession.objects.filter(pk=session.pk).exists()


def test_when_session_key_is_reused_on_same_interface_then_save_should_fail(
    interface,
):
    InterfaceAccessSession.objects.create(interface=interface, session_key="a")

    with pytest.raises(IntegrityError), transaction.atomic():
        InterfaceAccessSession.objects.create(interface=interface, session_key="a")


def test_when_session_key_is_reused_on_other_interface_then_save_should_succeed(
    interface, other_interface
):
    InterfaceAccessSession.objects.create(interface=interface, session_key="a")
    InterfaceAccessSession.objects.create(interface=other_interface, session_key="a")

    assert InterfaceAccessSession.objects.filter(session_key="a").count() == 2


def test_when_vlan_tag_is_missing_then_save_should_succeed(interface):
    session = InterfaceAccessSession.objects.create(
        interface=interface, session_key="a", vlan_tag=None
    )

    session.refresh_from_db()
    assert session.vlan_tag is None


@pytest.mark.parametrize("vlan_tag", [0, 4095])
def test_when_vlan_tag_is_out_of_range_then_save_should_fail(interface, vlan_tag):
    with pytest.raises(IntegrityError), transaction.atomic():
        InterfaceAccessSession.objects.create(
            interface=interface, session_key="a", vlan_tag=vlan_tag
        )


@pytest.mark.parametrize("field", ["method", "domain", "status"])
def test_when_enumerated_field_has_unknown_value_then_save_should_fail(
    interface, field
):
    with pytest.raises(IntegrityError), transaction.atomic():
        InterfaceAccessSession.objects.create(
            interface=interface, session_key="a", **{field: "bogus"}
        )


@pytest.mark.parametrize(
    "field, choices",
    [
        ("method", InterfaceAccessSession.METHOD_CHOICES),
        ("domain", InterfaceAccessSession.DOMAIN_CHOICES),
        ("status", InterfaceAccessSession.STATUS_CHOICES),
    ],
)
def test_when_enumerated_field_has_any_model_choice_then_save_should_succeed(
    interface, field, choices
):
    for index, (value, _label) in enumerate(choices):
        InterfaceAccessSession.objects.create(
            interface=interface, session_key=str(index), **{field: value}
        )

    assert InterfaceAccessSession.objects.filter(interface=interface).count() == len(
        choices
    )


def test_when_session_is_updated_then_first_seen_should_not_change(interface):
    session = InterfaceAccessSession.objects.create(
        interface=interface, session_key="a"
    )
    first_seen = session.first_seen

    session.status = InterfaceAccessSession.STATUS_AUTHORIZED
    session.save()

    session.refresh_from_db()
    assert session.first_seen == first_seen


def test_when_client_mac_is_saved_then_it_should_be_stored_as_macaddr(interface):
    session = InterfaceAccessSession.objects.create(
        interface=interface, session_key="a", client_mac="00-11-22-AA-BB-CC"
    )

    session.refresh_from_db()
    assert session.client_mac == "00:11:22:aa:bb:cc"


@pytest.fixture
def interface(switch, interface_factory):
    return interface_factory(switch, "GigabitEthernet1/0/1", 1)


@pytest.fixture
def other_interface(switch, interface_factory):
    return interface_factory(switch, "GigabitEthernet1/0/2", 2)


@pytest.fixture
def switch(netbox_factory):
    return netbox_factory("access-session-sw.example.org", "10.99.0.1")
