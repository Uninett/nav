#
# Copyright (C) 2012 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""stp blocked ports storage and handling"""
from nav.models import manage

from nav.ipdevpoll.storage import Shadow, DefaultManager

from .netbox import Netbox

class SwPortBlockedManager(DefaultManager):
    "Manages SwPortBlocked entries"

    _db_blocks = None
    _found_existing_map = {}

    def __init__(self, *args, **kwargs):
        super(SwPortBlockedManager, self).__init__(*args, **kwargs)
        self.netbox = self.containers.get(None, Netbox)

    def prepare(self):
        self._load_and_map_existing_objects()

    def _load_and_map_existing_objects(self):
        blocking = manage.SwPortBlocked.objects.filter(
            interface__netbox__id=self.netbox.id)
        self._db_blocks = dict(((b.interface_id, b.vlan), b)
                               for b in blocking)

        self._found_existing_map = dict(
            (found, self._find_existing_for(found))
            for found in self.get_managed())

        for found, existing in self._found_existing_map.items():
            if existing:
                found.set_existing_model(existing)

    def _find_existing_for(self, found_block):
        key = (found_block.interface.id, found_block.vlan)
        return self._db_blocks.get(key, None)

    def cleanup(self):
        "remove blocking states that weren't found"
        pass # TODO IMPLEMENT ME

class SwPortBlocked(Shadow):
    __shadowclass__ =  manage.SwPortBlocked
    manager = SwPortBlockedManager

    def get_existing_model(self, containers=None):
        "Returns only a cached object, if available"
        return getattr(self, '_cached_existing_model', None)
