from nav.ipdevpoll.plugins.entity import Entity
from nav.ipdevpoll.shadows import Device
from nav.ipdevpoll.storage import ContainerRepository


def test_entity_sets_software_version_of_entity_with_lowest_index(localhost):
    result = {
        2: {
            'entPhysicalIndex': None,
            'entPhysicalDescr': 'ProCurve J9086A Switch 2610-24/12PWR',
            'entPhysicalVendorType': '.1.3.6.1.4.1.11.2.3.7.11.80',
            'entPhysicalContainedIn': 0,
            'entPhysicalClass': 'chassis',
            'entPhysicalParentRelPos': -1,
            'entPhysicalName': 'Chassis',
            'entPhysicalHardwareRev': '1990-3656',
            'entPhysicalFirmwareRev': 'R.10.06',
            'entPhysicalSoftwareRev': 'R.11.25',
            'entPhysicalSerialNum': 'CN931ZQ0H6',
            'entPhysicalMfgName': 'Hewlett-Packard',
            'entPhysicalModelName': 'J9086A',
            'entPhysicalAlias': '',
            'entPhysicalAssetID': '',
            'entPhysicalIsFRU': True,
            'entPhysicalMfgDate': None,
            'entPhysicalUris': None,
            'entPhysicalUUID': None,
            0: 2,
        },
        1: {
            'entPhysicalIndex': None,
            'entPhysicalDescr': 'ProCurve J9086A Switch 2610-24/12PWR',
            'entPhysicalVendorType': '.1.3.6.1.4.1.11.2.3.7.11.80',
            'entPhysicalContainedIn': 0,
            'entPhysicalClass': 'chassis',
            'entPhysicalParentRelPos': -1,
            'entPhysicalName': 'Chassis',
            'entPhysicalHardwareRev': '1990-3656',
            'entPhysicalFirmwareRev': 'R.10.06',
            'entPhysicalSoftwareRev': 'R.12.25',
            'entPhysicalSerialNum': 'CN931ZQ0H6',
            'entPhysicalMfgName': 'Hewlett-Packard',
            'entPhysicalModelName': 'J9086A',
            'entPhysicalAlias': '',
            'entPhysicalAssetID': '',
            'entPhysicalIsFRU': True,
            'entPhysicalMfgDate': None,
            'entPhysicalUris': None,
            'entPhysicalUUID': None,
            0: 1,
        },
    }
    entity = Entity(netbox=localhost, agent=None, containers=ContainerRepository())
    entity.ignored_serials = []
    entity._process_entities(result)

    assert entity.containers[Device]["CN931ZQ0H6"].software_version == 'R.12.25'
