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
from nav.models import manage
from nav.portadmin.config import CONFIG
from nav.portadmin.cnaas_nms.lowlevel import get_api
from nav.portadmin.handlers import ManagementHandler


class CNaaSNMSMixIn(ManagementHandler):
    """MixIn to override all write-operations from
    nav.portadmin.handlers.ManagementHandler and instead direct them through a CNaaS
    NMS instance's REST API.

    """

    def __init__(self, netbox: manage.Netbox, **kwargs):
        super().__init__(netbox, **kwargs)
        config = CONFIG.get_cnaas_nms_config()
        self._api = get_api(config.url, config.token)

    def set_interface_description(self, interface: manage.Interface, description: str):
        raise NotImplementedError

    def set_interface_down(self, interface: manage.Interface):
        raise NotImplementedError

    def set_interface_up(self, interface: manage.Interface):
        raise NotImplementedError

    def commit_configuration(self):
        raise NotImplementedError
