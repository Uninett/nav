import pytest

from nav.models.manage import (
    ManagementProfile,
    NetboxProfile,
    NetboxEntity,
    Netbox,
    Device,
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
