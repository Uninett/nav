import pytest

from nav.models.manage import (
    ManagementProfile,
    NetboxProfile,
    NetboxEntity,
    Netbox,
    Device,
)


def test_get_snmp_config_should_pick_highest_available_snmp_version(
    db,
    localhost,
    wanted_profile,
    faulty_profile,
    snmpv1_string_profile,
    snmpv1_integer_profile,
    null_profile,
):
    for profile in (
        faulty_profile,
        snmpv1_integer_profile,
        wanted_profile,
        snmpv1_string_profile,
        null_profile,
    ):
        profile.save()
        NetboxProfile(netbox=localhost, profile=profile).save()

    assert (
        localhost._get_snmp_config(variable="community")
        == wanted_profile.configuration["community"]
    )


def test_netbox_should_be_annotated_with_chassis_serial(db, localhost):
    """Mainly, this verifies that regressions haven't rendered the raw SQL used to
    annotate netboxes with serial numbers incompatible with the current schema.
    """
    for index, serial in enumerate(["first", "second"]):
        device = Device(serial=serial)
        device.save()
        chassis = NetboxEntity(
            netbox=localhost,
            device=device,
            index=index,
            physical_class=NetboxEntity.CLASS_CHASSIS,
        )
        chassis.save()

    netbox = Netbox.objects.with_chassis_serials().filter(id=localhost.id)[0]
    assert netbox.chassis_serial == "first"


def test_netbox_mac_addresses_should_return_distinct_set_of_addresses(
    db, localhost: Netbox
):
    mac = "00:c0:ff:ee:ba:be"
    localhost.info_set.create(key="lldp", variable="chassis_mac", value=mac)
    localhost.info_set.create(key="bridge_info", variable="base_address", value=mac)

    assert localhost.mac_addresses == set([mac])


@pytest.fixture
def wanted_profile():
    return ManagementProfile(
        protocol=ManagementProfile.PROTOCOL_SNMP,
        name="wanted",
        configuration={"version": "2c", "community": "42"},
    )


@pytest.fixture
def faulty_profile():
    return ManagementProfile(
        protocol=ManagementProfile.PROTOCOL_SNMP, name="faulty", configuration={}
    )


@pytest.fixture
def null_profile():
    return ManagementProfile(
        protocol=ManagementProfile.PROTOCOL_SNMP,
        name="null",
        configuration={"version": None},
    )


@pytest.fixture
def snmpv1_string_profile():
    return ManagementProfile(
        protocol=ManagementProfile.PROTOCOL_SNMP,
        name="onestring",
        configuration={"version": "1", "community": "onestring"},
    )


@pytest.fixture
def snmpv1_integer_profile():
    return ManagementProfile(
        protocol=ManagementProfile.PROTOCOL_SNMP,
        name="oneinteger",
        configuration={"version": 1, "community": "oneinteger"},
    )
