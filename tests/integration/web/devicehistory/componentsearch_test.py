import pytest

from nav.web.devicehistory.utils.componentsearch import get_component_search_results
from nav.models.manage import Device, Location, Room

BUTTON_TEXT_PATTERN = 'Submit %s components'


class TestGetComponentSearchResults:
    def test_should_return_result_for_existing_room(self, db, new_room):
        results = get_component_search_results(new_room.id, BUTTON_TEXT_PATTERN)
        assert 'room' in results

    def test_should_return_existing_room_in_search_results(self, db, new_room):
        results = get_component_search_results(new_room.id, BUTTON_TEXT_PATTERN)
        room_result = results['room']
        search_values = room_result['values']

        room_ids = [room_id for _, rooms in search_values for room_id, _ in rooms]
        assert new_room.id in room_ids

    def test_should_include_component_name_in_button_text_pattern(self, db, new_room):
        results = get_component_search_results(new_room.id, BUTTON_TEXT_PATTERN)
        room_result = results['room']
        assert 'Room' in room_result['button']

    def test_should_correctly_format_button_text(self, db, new_room):
        results = get_component_search_results(new_room.id, BUTTON_TEXT_PATTERN)
        room_result = results['room']
        assert room_result['button'] == 'Submit Room components'

    def test_when_button_text_pattern_is_invalid_then_throw_value_error(
        self, db, new_room
    ):
        with pytest.raises(ValueError):
            get_component_search_results(new_room.id, 'Invalid pattern')

    def test_when_room_component_is_excluded_should_not_return_existing_room_in_results(
        self, db, new_room
    ):
        results = get_component_search_results(
            new_room.id, button_text=BUTTON_TEXT_PATTERN, exclude=[Room]
        )
        assert 'room' not in results

    def test_should_return_empty_results_for_non_existing_component(self, db):
        results = get_component_search_results(
            "non-existing-component", BUTTON_TEXT_PATTERN
        )
        assert results == {}

    def test_when_given_inactive_device_serial_return_results(self, inactive_device):
        results = get_component_search_results(
            inactive_device.serial, BUTTON_TEXT_PATTERN
        )
        inactive_result = results['inactive_device']
        assert inactive_result is not None

        search_values = inactive_result['values']
        device_ids = [result[0] for result in search_values]
        assert inactive_device.id in device_ids

    def test_when_given_inactive_device_serial_return_correct_select_label(
        self, inactive_device
    ):
        results = get_component_search_results(
            inactive_device.serial, BUTTON_TEXT_PATTERN
        )
        inactive_result = results['inactive_device']
        assert inactive_result['label'] == 'Inactive Device'


@pytest.fixture
def new_room(db):
    location = Location(id="testlocation")
    location.save()
    room = Room(id="testroom", description="Test Room", location=location)
    room.save()
    yield room
    room.delete()
    location.delete()


@pytest.fixture
def inactive_device(db):
    device = Device(serial="inactivedevice")
    device.save()
    yield device
    device.delete()
