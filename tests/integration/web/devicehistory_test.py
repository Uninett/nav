# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from nav.models.event import EventQueue, EventQueueVar

from django.urls import reverse
from nav.compatibility import smart_str


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
