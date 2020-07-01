#
# Copyright (C) 2021 UNINETT
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Low-level CNaaS-NMS REST API access using simple_rest_client"""
from simple_rest_client.api import API
from simple_rest_client.resource import Resource
from simple_rest_client.exceptions import ClientError


def get_api(url, token):
    """Returns a CNaaS NMS API instance from a URL and a token"""
    default_headers = {
        "Authorization": "Bearer {}".format(token),
    }
    api = API(
        api_root_url=url,
        headers=default_headers,
        params={},
        timeout=2,
        append_slash=False,
        json_encode_body=True,
    )
    api.add_resource(resource_name="devices", resource_class=DeviceResource)
    api.add_resource(resource_name="interfaces", resource_class=InterfaceResource)
    api.add_resource(resource_name="device_sync", resource_class=DeviceSyncResource)
    api.add_resource(resource_name="job")

    return api


class DeviceResource(Resource):
    """Defines operations on the devices endpoint"""

    actions = {
        "retrieve": {"method": "GET", "url": "/devices?filter[management_ip]={}"}
    }


class InterfaceResource(Resource):
    """Defines operations on the interface sub-resource of a device"""

    actions = {
        "list": {"method": "GET", "url": "/device/{}/interfaces"},
        "configure": {
            "method": "PUT",
            "url": "/device/{}/interfaces",
        },
    }


class DeviceSyncResource(Resource):
    """Defines the API syncto operations"""

    actions = {"syncto": {"method": "POST", "url": "/device_syncto"}}
