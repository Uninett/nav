from nav.models.manage import Netbox, Room, Location
from nav.web.maintenance.utils import get_component_name


class TestGetComponentName:
    def test_get_component_names(self):
        components = [Netbox, Room, Location]
        expected_names = ["netbox", "room", "loc"]
        calculated_names = [get_component_name(component) for component in components]
        assert calculated_names == expected_names, (
            "Component names do not match expected values."
        )

    def test_should_return_short_name_for_location(self):
        name = get_component_name(Location)
        assert name == "loc"
