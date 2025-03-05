# -*- coding: utf-8 -*-

from nav.models.event import EventQueue, EventQueueVar
from nav.models.manage import Device, Module, NetboxGroup

from django.urls import reverse
from django.utils.encoding import smart_str


def test_post_device_error_should_succeed(client, localhost):
    error_comment = "comment"
    url = reverse('devicehistory-do-registererror')

    response = client.post(
        url,
        follow=True,
        data={
            "netbox": str(localhost.id),
            "error_comment": error_comment,
            "submit_netbox": "Add+IP+device+error+event",
        },
    )

    assert response.status_code == 200
    assert f"Registered error on netbox {localhost.sysname}" in smart_str(
        response.content
    )
    event = EventQueue.objects.filter(
        event_type_id="deviceNotice", source_id="deviceManagement", netbox=localhost
    ).first()
    assert event
    eventvars = EventQueueVar.objects.filter(event_queue=event)
    assert eventvars
    assert eventvars.filter(variable="alerttype", value="deviceError")
    assert eventvars.filter(variable="comment", value=error_comment)


def test_post_device_error_without_comment_should_ask_for_confirmation(
    client, localhost
):
    url = reverse('devicehistory-do-registererror')

    response = client.post(
        url,
        follow=True,
        data={
            "netbox": str(localhost.id),
            "error_comment": "",
            "submit_netbox": "Add+IP+device+error+event",
        },
    )

    assert response.status_code == 200
    assert (
        "There&#x27;s no error message supplied. Are you sure you want to continue?"
        in smart_str(response.content)
    )
    event = EventQueue.objects.filter(
        event_type_id="deviceNotice", source_id="deviceManagement", netbox=localhost
    ).first()
    assert not event


def test_post_device_error_without_comment_should_succeed_with_confirmation(
    client, localhost
):
    url = reverse('devicehistory-do-registererror')

    response = client.post(
        url,
        follow=True,
        data={
            "netbox": str(localhost.id),
            "error_comment": "",
            "confirm": "yes",
        },
    )

    assert response.status_code == 200
    assert f"Registered error on netbox {localhost.sysname}" in smart_str(
        response.content
    )
    event = EventQueue.objects.filter(
        event_type_id="deviceNotice", source_id="deviceManagement", netbox=localhost
    ).first()
    assert event
    eventvars = EventQueueVar.objects.filter(event_queue=event)
    assert eventvars
    assert eventvars.filter(variable="alerttype", value="deviceError")
    assert eventvars.filter(variable="comment", value="")


def test_get_location_history_should_succeed(client, localhost):
    url = reverse('devicehistory-view')
    response = client.get(
        f"{url}?from_date=2023-01-01&to_date=2025-01-01&eventtype=all&loc={localhost.room.location.id}&submit_module=View+location+history"
    )

    assert response.status_code == 200


def test_get_room_history_should_succeed(client, localhost):
    url = reverse('devicehistory-view')
    response = client.get(
        f"{url}?from_date=2023-01-01&to_date=2025-01-01&eventtype=all&room={localhost.room.id}&submit_module=View+room+history"
    )

    assert response.status_code == 200


def test_get_ip_device_history_should_succeed(client, localhost):
    url = reverse('devicehistory-view')
    response = client.get(
        f"{url}?from_date=2023-01-01&to_date=2025-01-01&eventtype=all&netbox={localhost.id}&submit_module=View+IP+device+history"
    )

    assert response.status_code == 200


def test_get_device_group_history_should_succeed(client, localhost):
    url = reverse('devicehistory-view')
    response = client.get(
        f"{url}?from_date=2023-01-01&to_date=2025-01-01&eventtype=all&netboxgroup={NetboxGroup.objects.first()}&submit_module=View+device+group+history"
    )

    assert response.status_code == 200


def test_get_module_history_should_succeed(db, client, localhost):
    device = Device(serial="1234test")
    device.save()
    module = Module(device=device, netbox=localhost, name='Module 1', model='')
    module.save()

    url = reverse('devicehistory-view')
    response = client.get(
        f"{url}?from_date=2023-01-01&to_date=2025-01-01&eventtype=all&module={module.id}&submit_module=View+romoduleom+history"
    )

    assert response.status_code == 200
