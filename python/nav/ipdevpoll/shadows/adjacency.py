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

    _existing = None
    _missing = None

    def __init__(self, *args, **kwargs):
        super(AdjacencyManager, self).__init__(*args, **kwargs)
        self.netbox = self.containers.get(None, Netbox)

    def prepare(self):
        self._load_existing()
        self._map_existing()

    def _load_existing(self):
        candidates = manage.AdjacencyCandidate.objects.filter(
            netbox__id=self.netbox.id)
        self._existing = dict((candidate_key(c), c) for c in candidates)

    def _map_existing(self):
        found = dict((candidate_key(c), c) for c in self.get_managed())
        for key, cand in found.items():
            if key in self._existing:
                cand.set_existing_model(self._existing[key])
                # always reset miss_count of found records
                cand.miss_count = 0

        missing = set(self._existing.keys()).difference(found)
        self._missing = [self._existing[key] for key in missing]

    def cleanup(self):
        self._handle_missing()
        self._delete_expired()

    def _handle_missing(self):
        for cand in self._missing:
            db_cand = manage.AdjacencyCandidate.objects.filter(id=cand.id)
            db_cand.update(miss_count=cand.miss_count+1)

    def _delete_expired(self):
        expired = manage.AdjacencyCandidate.objects.filter(
            netbox__id=self.netbox.id,
            miss_count__gte=MAX_MISS_COUNT)
        expired.delete()


# pylint: disable=C0111
class AdjacencyCandidate(Shadow):
    __shadowclass__ = manage.AdjacencyCandidate
    manager = AdjacencyManager

    def get_existing_model(self, containers=None):
        "Returns only a cached object, if available"
        return getattr(self, '_cached_existing_model', None)

def candidate_key(cand):
    "return a (hopefully) unique dict key for a candidate object"
    # all this getattr yaking is trying to reduce the number of db fetches
    return ((getattr(cand, 'interface_id', None)
             or cand.interface and cand.interface.id),

            (getattr(cand, 'to_netbox_id', None)
             or cand.to_netbox and cand.to_netbox.id),

            (getattr(cand, 'to_interface_id', None)
             or cand.to_interface and cand.to_interface.id),

            cand.source)
