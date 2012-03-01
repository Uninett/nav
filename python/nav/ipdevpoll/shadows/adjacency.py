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
"adjacency candidate storage and handling"

from nav.models import manage
from nav.ipdevpoll.storage import Shadow, DefaultManager
from .netbox import Netbox

MAX_MISS_COUNT = 3

class AdjacencyManager(DefaultManager):
    "Manages AdjacencyCandidate records"

    def __init__(self, *args, **kwargs):
        super(AdjacencyManager, self).__init__(*args, **kwargs)
        self.netbox = self.containers.get(None, Netbox)

# pylint: disable=C0111
class AdjacencyCandidate(Shadow):
    __shadowclass__ = manage.AdjacencyCandidate
    manager = AdjacencyManager

    def get_existing_model(self, containers=None):
        "Returns only a cached object, if available"
        return getattr(self, '_cached_existing_model', None)
