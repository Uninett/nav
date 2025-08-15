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
