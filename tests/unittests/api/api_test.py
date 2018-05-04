# -*- coding: utf-8 -*-

from mock import Mock

from nav.web.api.v1.auth import TokenPermission


def test_path_in_endpoints():
    path = '/api/1/room/'
    endpoints = {'room': '/api/1/room/'}

    assert TokenPermission.is_path_in_endpoints(path, endpoints)


def test_missing_slashes():
    path = '/api/1/room/'
    endpoints = {'room': '/api/1/room'}

    assert TokenPermission.is_path_in_endpoints(path, endpoints)


def test_no_version():
    path = '/api/room/'
    endpoints = {'room': '/api/1/room'}

    assert TokenPermission.is_path_in_endpoints(path, endpoints)


def test_multiple_endpoints():
    path = '/api/room/'
    endpoints = {
        'room': '/api/1/room',
        'netbox': '/api/1/netbox',
        'account': '/api/1/account',
    }

    assert TokenPermission.is_path_in_endpoints(path, endpoints)


def test_miss_on_multiple_endpoints():
    path = '/api/1/alert'
    endpoints = {
        'room': '/api/1/room',
        'netbox': '/api/1/netbox',
        'account': '/api/1/account',
    }

    assert not TokenPermission.is_path_in_endpoints(path, endpoints)


def test_sub_endpoints():
    path = '/api/1/prefix/usage/'
    endpoints = {
        'room': '/api/1/prefix',
    }

    assert TokenPermission.is_path_in_endpoints(path, endpoints)
