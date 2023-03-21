# -*- coding: utf-8 -*-
from django.urls import reverse


def test_search_for_ip_devices_should_not_crash(client):
    url = reverse('info-search') + '?query=a'
    response = client.get(url)
    assert response.status_code == 200


def test_search_for_rooms_should_not_crash(client):
    url = reverse('room-search') + '?query=a'
    response = client.get(url)
    assert response.status_code == 200


def test_search_for_locations_should_not_crash(client):
    url = reverse('location-search') + '?query=a'
    response = client.get(url)
    assert response.status_code == 200


def test_search_for_vlans_should_not_crash(client):
    url = reverse('vlan-index') + '?query=a'
    response = client.get(url)
    assert response.status_code == 200


def test_search_for_prefixes_should_not_crash(client):
    url = reverse('prefix-index') + '?query=a'
    response = client.get(url)
    assert response.status_code == 200


def test_search_for_device_groups_should_not_crash(client):
    url = reverse('netbox-group') + '?query=a'
    response = client.get(url)
    assert response.status_code == 200
