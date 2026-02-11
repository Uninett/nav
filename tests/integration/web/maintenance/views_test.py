#
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
import datetime

import pytest
from django.urls import reverse

from django.utils.encoding import smart_str
from nav.models.manage import Netbox, Room, Location
from nav.models.msgmaint import MaintenanceTask


class TestMaintenanceCalendarView:
    def test_calendar_renders_when_no_arguments_given(self, client):
        response = client.get('/maintenance/', follow=True)
        assert response.status_code == 200

    def test_calendar_still_renders_when_invalid_arguments_given(self, client):
        response = client.get('/maintenance/?year=invalid&month=invalid', follow=True)
        assert response.status_code == 200


class TestAddMaintenanceTask:
    def test_valid_data_without_end_time_should_suceed(self, db, client, localhost):
        url = reverse('maintenance-new')
        data = {
            "start_time": "2023-11-21 12:40",
            "no_end_time": "on",
            "description": "maintenance",
            "netbox": localhost.pk,
            "save": "Save+task",
        }

        response = client.post(
            url,
            follow=True,
            data=data,
        )

        assert response.status_code == 200
        assert f'Saved task {data["description"]}' in smart_str(response.content)
        assert MaintenanceTask.objects.filter(description=data["description"]).exists()

    def test_valid_data_with_end_time_should_suceed(self, db, client, localhost):
        url = reverse('maintenance-new')
        data = {
            "start_time": "2023-11-21 12:40",
            "end_time": "2023-11-25 12:40",
            "description": "maintenance",
            "netbox": localhost.pk,
            "save": "Save+task",
        }

        response = client.post(
            url,
            follow=True,
            data=data,
        )

        assert response.status_code == 200
        assert f'Saved task {data["description"]}' in smart_str(response.content)
        assert MaintenanceTask.objects.filter(description=data["description"]).exists()

    def test_with_non_int_netbox_key_should_fail(self, db, client):
        url = reverse('maintenance-new')
        data = {
            "start_time": "2023-11-21 12:40",
            "no_end_time": "on",
            "description": "maintenance",
            "netbox": "137'",
            "save": "Save+task",
        }

        response = client.post(
            url,
            follow=True,
            data=data,
        )

        assert response.status_code == 200
        assert "netbox: argument needs to be a number" in smart_str(response.content)
        assert not MaintenanceTask.objects.filter(
            description=data["description"]
        ).exists()

    def test_with_non_int_netbox_key_in_url_should_fail(self, db, client):
        url = reverse('maintenance-new') + '?netbox=foobar'

        response = client.get(url, follow=True)

        assert response.status_code == 200
        assert "netbox: argument needs to be a number" in smart_str(response.content)

    def test_with_non_existent_netbox_key_in_url_should_fail(self, db, client):
        last_netbox_id = getattr(Netbox.objects.last(), "pk", 0)
        url = (
            reverse('maintenance-new')
            + f'?netbox={last_netbox_id + 1}&netbox={last_netbox_id + 2}'
        )

        response = client.get(url, follow=True)

        assert response.status_code == 200
        assert "netbox: no elements with the given identifiers found" in smart_str(
            response.content
        )

    def test_with_end_time_before_start_time_should_fail(self, db, client, localhost):
        url = reverse('maintenance-new')
        data = {
            "start_time": "2023-11-22 14:35",
            "end_time": "2023-11-08 14:35",
            "description": "maintenance",
            "netbox": localhost.pk,
            "save": "Save+task",
        }

        response = client.post(
            url,
            follow=True,
            data=data,
        )

        assert response.status_code == 200
        assert "End time must be after start time" in smart_str(response.content)
        assert not MaintenanceTask.objects.filter(
            description=data["description"]
        ).exists()


class TestEditMaintenanceTask:
    def test_when_existing_task_is_requested_it_should_render_with_intact_description(
        self, db, client, localhost, empty_maintenance_task
    ):
        url = reverse("maintenance-edit", kwargs={"task_id": empty_maintenance_task.id})
        response = client.get(url, follow=True)

        assert response.status_code == 200
        assert empty_maintenance_task.description in smart_str(response.content)


class TestSearchMaintenanceComponents:
    def test_given_an_existing_room_then_component_search_should_return_results(
        self, db, client, new_room
    ):
        url = reverse('maintenance-component-search')
        response = client.post(url, {'search': new_room.id})
        assert response.status_code == 200
        assert new_room.id in smart_str(response.content)

    def test_given_a_non_existing_component_then_component_search_should_return_no_hits(
        self, client
    ):
        url = reverse('maintenance-component-search')
        response = client.post(url, {'search': 'nonexistent-component'})
        assert response.status_code == 200
        assert "No hits" in smart_str(response.content)

    def test_given_an_empty_query_then_component_search_should_return_no_hits(
        self, client
    ):
        url = reverse('maintenance-component-search')
        response = client.post(url, {'search': ''})
        assert response.status_code == 200
        assert "No hits" in smart_str(response.content)

    def test_when_searching_by_room_description_then_it_should_return_matching_rooms(
        self, db, client, new_room
    ):
        url = reverse('maintenance-component-search')
        response = client.post(url, {'search': 'Test Room'})
        assert response.status_code == 200
        assert new_room.id in smart_str(response.content)

    def test_when_searching_by_location_description_then_it_should_return_results(
        self, db, client, location_with_description
    ):
        url = reverse('maintenance-component-search')
        response = client.post(url, {'search': 'Building'})
        assert response.status_code == 200
        assert location_with_description.id in smart_str(response.content)


class TestBrowseMaintenanceComponents:
    def test_when_component_browse_is_called_with_post_then_it_should_fail(
        self, db, client
    ):
        url = reverse('maintenance-component-browse')
        response = client.post(url, {})
        assert response.status_code == 405

    def test_when_no_locations_exist_then_component_browse_should_show_empty_message(
        self, db, client
    ):
        Location.objects.all().delete()
        url = reverse('maintenance-component-browse')
        response = client.get(url)
        assert response.status_code == 200
        assert 'No locations found' in smart_str(response.content)

    def test_when_locations_exist_then_component_browse_should_include_them(
        self, db, client, location_with_description
    ):
        url = reverse('maintenance-component-browse')
        response = client.get(url)
        assert response.status_code == 200
        assert location_with_description.id in smart_str(response.content)

    def test_when_nested_locations_exist_then_component_browse_should_show_hierarchy(
        self, db, client, nested_locations
    ):
        parent_location, child_location = nested_locations
        url = reverse('maintenance-component-browse')
        response = client.get(url)
        assert response.status_code == 200
        assert parent_location.id in smart_str(response.content)
        assert child_location.id in smart_str(response.content)

    def test_when_rooms_exist_then_component_browse_should_group_them_under_location(
        self, db, client, location_with_rooms
    ):
        location, rooms = location_with_rooms
        url = reverse('maintenance-component-browse')
        response = client.get(url)
        content = smart_str(response.content)
        assert response.status_code == 200
        assert location.id in content
        for room in rooms:
            assert room.id in content


class TestSelectMaintenanceComponents:
    def test_given_an_existing_room_then_component_select_should_return_results(
        self, db, client, new_room
    ):
        url = reverse('maintenance-component-select')
        response = client.post(
            url,
            {
                'room': new_room.id,
            },
        )
        assert response.status_code == 200
        assert f"name=\"room\" value=\"{new_room.id}\"" in smart_str(response.content)

    def test_when_adding_room_via_add_room_then_it_should_merge_with_existing_rooms(
        self, db, client, location_with_rooms
    ):
        location, rooms = location_with_rooms
        room1, room2 = rooms
        url = reverse('maintenance-component-select')
        response = client.post(
            url,
            {
                'room': room1.id,
                'add_room': room2.id,
            },
        )
        assert response.status_code == 200
        content = smart_str(response.content)
        assert f"name=\"room\" value=\"{room1.id}\"" in content
        assert f"name=\"room\" value=\"{room2.id}\"" in content

    def test_when_adding_location_via_add_loc_then_it_should_merge_with_existing(
        self, db, client, nested_locations
    ):
        parent, child = nested_locations
        url = reverse('maintenance-component-select')
        response = client.post(
            url,
            {
                'location': parent.id,
                'add_loc': child.id,
            },
        )
        assert response.status_code == 200
        content = smart_str(response.content)
        assert f"name=\"location\" value=\"{parent.id}\"" in content
        assert f"name=\"location\" value=\"{child.id}\"" in content

    def test_should_remove_given_room_from_response(self, db, client, new_room):
        url = reverse('maintenance-component-select')
        response = client.post(
            url,
            {
                'room': new_room.id,
                'remove_room': new_room.id,
                'remove': [''],
            },
        )
        assert response.status_code == 200
        assert f"name=\"room\" value=\"{new_room.id}\"" not in smart_str(
            response.content
        )

    def test_when_given_all_components_to_remove_then_it_should_return_none(
        self, db, client, new_room
    ):
        url = reverse('maintenance-component-select')
        room = new_room
        location_id = room.location.id
        response = client.post(
            url,
            {
                'room': room.id,
                'remove_room': room.id,
                'location': location_id,
                'remove_location': location_id,
                'remove': [''],
            },
        )
        assert response.status_code == 200
        assert "(none)" in smart_str(response.content)


@pytest.fixture
def empty_maintenance_task(db):
    now = datetime.datetime.now()
    task = MaintenanceTask(
        start_time=now,
        end_time=now + datetime.timedelta(hours=1),
        description="Temporary test fixture task",
    )
    task.save()
    yield task
    task.delete()


@pytest.fixture
def new_room(db):
    location = Location(id="testlocation")
    location.save()
    room = Room(id="123", description="Test Room", location=location)
    room.save()
    yield room
    room.delete()
    location.delete()


@pytest.fixture
def location_with_description(db):
    location = Location(id="testloc", description="Building A")
    location.save()
    yield location
    location.delete()


@pytest.fixture
def nested_locations(db):
    parent = Location(id="parentloc", description="Parent Location")
    parent.save()
    child = Location(id="childloc", description="Child Location", parent=parent)
    child.save()
    yield parent, child
    child.delete()
    parent.delete()


@pytest.fixture
def location_with_rooms(db):
    location = Location(id="testloc2", description="Location with Rooms")
    location.save()
    room1 = Room(id="testroom1", description="Room 1", location=location)
    room1.save()
    room2 = Room(id="testroom2", description="Room 2", location=location)
    room2.save()
    yield location, [room1, room2]
    room1.delete()
    room2.delete()
    location.delete()
