import pytest

from nav.web.devicehistory.utils.componentsearch import get_component_search_results
from nav.models.manage import Room, Location


class TestGetComponentSearchResults:
    def test_should_return_result_for_existing_room(self, db, new_room):
        results = get_component_search_results(new_room.id)
        assert 'room' in results

    def test_should_return_existing_room_in_search_results(self, db, new_room):
        results = get_component_search_results(new_room.id)
        room_result = results['room']
        search_values = room_result['values']

        room_ids = [room_id for _, rooms in search_values for room_id, _ in rooms]
        assert new_room.id in room_ids

    def test_when_button_suffix_is_empty_should_return_default_label(
        self, db, new_room
    ):
        results = get_component_search_results(new_room.id)
        room_result = results['room']
        assert room_result['button'] == 'Add Room'

    def test_when_button_suffix_is_set_should_return_custom_label(self, db, new_room):
        results = get_component_search_results(new_room.id, 'events')
        room_result = results['room']
        assert room_result['button'] == 'Add Room events'

    def test_when_room_component_is_excluded_should_not_return_existing_room_in_results(
        self, db, new_room
    ):
        results = get_component_search_results(new_room.id, exclude=[Room])
        assert 'room' not in results

    def test_should_return_empty_results_for_non_existing_component(self, db):
        results = get_component_search_results("non-existing-component")
        assert results == {}


@pytest.fixture
def new_room(db):
    location = Location(id="testlocation")
    location.save()
    room = Room(id="testroom", description="Test Room", location=location)
    room.save()
    yield room
    room.delete()
    location.delete()
