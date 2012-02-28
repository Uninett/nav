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
"""cam record storage and handling.

Updating NAV's cam table goes rougly like this:

* Load all open CAM records for the current netbox.

  - In the database, an open cam record is considered one whose
    end_time='infinity' or whose miss_count is NON-NULL.

* An ifindex+mac combination the collector found, which wasn't already in the
  list of open records is added as a new record, with end_time='infinity' and
  miss_count=0.

* An ifindex+mac combination the collector found which is also among the open
  records is left untouched, unless its miss_count <> 0; in such a case the
  miss_count is reset to 0.

* If an ifindex+mac combination from the open records list is not found by the
  collector, we ensure it's end_time is set to anything but infinity, and its
  miss_count is incremented by one.

  - If a record's miss_count becomes greater or equal to MAX_MISS_COUNT, the
    miss_count is set to a NULL value.

The point of miss_count in this algorithm is that closed cam records have a
grace period of MAX_MISS_COUNT collector runs.  If a "closed" cam record is
found again within MAX_MISS_COUNT collector runs, the existing record can be
reclaimed by resetting end_time to infinity.

"""
import datetime
import logging

from nav.models import manage
from django.db.models import Q
from nav.ipdevpoll.storage import Shadow, DefaultManager
from .netbox import Netbox
from .interface import Interface

INFINITY = datetime.datetime.max
MAX_MISS_COUNT = 3

class CamManager(DefaultManager):
    "Manages Cam records"

    _previously_open = None
    _now_open = None
    _missing = None
    _new = None
    _ifnames = None

    def __init__(self, *args, **kwargs):
        super(CamManager, self).__init__(*args, **kwargs)
        self.netbox = self.containers.get(None, Netbox)

    def prepare(self):
        self._load_open_records()
        self._map_found_to_open()
        self._log_stats()
        self._fix_missing_vars()

    def _load_open_records(self):
        match_open = Q(end_time__gte=INFINITY) | Q(miss_count__gte=0)
        camlist = manage.Cam.objects.filter(
            netbox__id=self.netbox.id).filter(match_open)
        self._previously_open = dict( ((cam.ifindex, cam.mac.lower()), cam)
                                      for cam in camlist )

    def _map_found_to_open(self):
        self._now_open = dict( ((cam.ifindex, cam.mac.lower()), cam)
                               for cam in self.get_managed() )
        self._new = set()
        for key, cam in self._now_open.items():
            if key in self._previously_open:
                cam.set_existing_model(self._previously_open[key])
            else:
                self._new.add(cam)

        missing = set(self._previously_open).difference(self._now_open)
        self._missing = dict((key, self._previously_open[key])
                             for key in missing)

    def _log_stats(self):
        if not self._logger.isEnabledFor(logging.DEBUG):
            return
        reclaimable_count = len([cam for cam in self._previously_open.values()
                                 if cam.end_time < INFINITY])
        known_count = len([cam for cam in self.get_managed()
                           if cam.get_existing_model()])
        new_count = len([cam for cam in self.get_managed()
                         if not cam.get_existing_model()])
        missing_count = len(self._missing)
        self._logger.debug(
            "existing=%d (reclaimable=%d) / "
            "found=%d (known=%d new=%d missing=%d)",
            len(self._previously_open), reclaimable_count, len(self._now_open),
            known_count, new_count, missing_count)

    def _fix_missing_vars(self):
        for cam in self.get_managed():
            self._fix_missing_vars_for(cam)

    def _fix_missing_vars_for(self, cam):
        if not cam.netbox:
            cam.netbox = self.netbox
        if not cam.end_time:
            cam.end_time = INFINITY
        cam.miss_count = 0

        if cam in self._new:
            if not cam.start_time:
                cam.start_time = datetime.datetime.now()
            cam.sysname = self.netbox.sysname
            cam.port = self._get_port_for(cam.ifindex)

    def _get_port_for(self, ifindex):
        """Gets a port name from an ifindex, either from newly collected or
        previously saved data.

        """
        port = self.containers.get(ifindex, Interface)
        if port and port.ifname:
            return port.ifname
        else:
            return self._get_saved_ifname_for(ifindex)

    def _get_saved_ifname_for(self, ifindex):
        if not self._ifnames:
            ifcs = manage.Interface.objects.filter(
                netbox__id=self.netbox.id, ifindex__isnull=False
                ).values('ifindex', 'ifname', 'ifdescr')
            self._ifnames = dict(
                (row['ifindex'], row['ifname'] or row['ifdescr'])
                for row in ifcs)

        return self._ifnames.get(ifindex, '')

    def cleanup(self):
        for cam in self._missing.values():
            self._close_missing(cam)

    @staticmethod
    def _close_missing(cam):
        upd = {}
        if cam.end_time >= INFINITY:
            cam.end_time = datetime.datetime.now()
            upd['end_time'] = cam.end_time

        if cam.miss_count >= 0:
            cam.miss_count += 1
            upd['miss_count'] = cam.miss_count

        if cam.miss_count >= MAX_MISS_COUNT:
            cam.miss_count = None
            upd['miss_count'] = cam.miss_count

        if upd:
            manage.Cam.objects.filter(id=cam.id).update(**upd)


# pylint: disable=C0111
class Cam(Shadow):
    __shadowclass__ = manage.Cam
    manager = CamManager

    def get_existing_model(self, containers=None):
        "Returns only a cached object, if available"
        return getattr(self, '_cached_existing_model', None)
