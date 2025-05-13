#
# Copyright (C) 2012 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
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
from collections import namedtuple

from django.db.models import Q
from django.db import transaction

from nav.models import manage
from nav.models.fields import INFINITY
from nav.ipdevpoll.storage import DefaultManager
from .netbox import Netbox
from .interface import Interface

MAX_MISS_COUNT = 3


Cam = namedtuple('Cam', 'ifindex mac')
Cam.sentinel = Cam(None, None)

CamDetails = namedtuple('CamDetails', 'id end_time miss_count')


class CamManager(DefaultManager):
    """Manages Cam records"""

    _previously_open = None
    _now_open = None
    _keepers = None
    _missing = None
    _new = None
    _ifnames = None

    def __init__(self, *args, **kwargs):
        super(CamManager, self).__init__(*args, **kwargs)
        self.netbox = self.containers.get(None, Netbox)

    def prepare(self):
        self._remove_sentinel()
        self._load_open_records()
        self._map_found_to_open()
        self._log_stats()

    def _remove_sentinel(self):
        if Cam.sentinel in self.containers[Cam]:
            del self.containers[Cam][Cam.sentinel]

    def _load_open_records(self):
        match_open = Q(end_time__gte=INFINITY) | Q(miss_count__gte=0)
        camlist = manage.Cam.objects.filter(netbox__id=self.netbox.id)
        camlist = camlist.filter(match_open).values_list(
            'ifindex', 'mac', 'id', 'end_time', 'miss_count'
        )
        self._previously_open = dict(
            (Cam(*cam[0:2]), CamDetails(*cam[2:])) for cam in camlist
        )

    def _map_found_to_open(self):
        self._now_open = set(self.get_managed())
        self._new = self._now_open.difference(self._previously_open)

        missing = set(self._previously_open).difference(self._now_open)
        self._missing = set(self._previously_open[key] for key in missing)

        self._keepers = self._now_open.intersection(self._previously_open)

    def _log_stats(self):
        if not self._logger.isEnabledFor(logging.DEBUG):
            return
        reclaimable_count = sum(
            1 for cam in self._previously_open.values() if cam.end_time < INFINITY
        )
        self._logger.debug(
            "existing=%d (reclaimable=%d) / found=%d (known=%d new=%d missing=%d)",
            len(self._previously_open),
            reclaimable_count,
            len(self._now_open),
            len(self._keepers),
            len(self._new),
            len(self._missing),
        )

    @transaction.atomic()
    def save(self):
        # Reuse the same object over and over in an attempt to avoid the
        # overhead of Python object creation
        record = manage.Cam(
            netbox_id=self.netbox.id,
            sysname=self.netbox.sysname,
            start_time=datetime.datetime.now(),
            end_time=INFINITY,
        )
        for cam in self._new:
            record.id = None
            record.port = self._get_port_for(cam.ifindex)
            record.ifindex = cam.ifindex
            record.mac = cam.mac
            record.save()

        # reclaim recently closed records
        keepers = (self._previously_open[cam] for cam in self._keepers)
        reclaim = [cam.id for cam in keepers if cam.end_time < INFINITY]
        if reclaim:
            self._logger.debug("reclaiming %r", reclaim)
            manage.Cam.objects.filter(id__in=reclaim).update(
                end_time=INFINITY, miss_count=0
            )

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
                (row['ifindex'], row['ifname'] or row['ifdescr']) for row in ifcs
            )

        return self._ifnames.get(ifindex, '')

    def cleanup(self):
        for cam_detail in self._missing:
            self._close_missing(cam_detail)

    @classmethod
    def _close_missing(cls, cam_detail):
        upd = {}
        cls._logger.debug("closing %r", cam_detail)
        if cam_detail.end_time >= INFINITY:
            upd['end_time'] = datetime.datetime.now()

        if cam_detail.miss_count >= 0:
            miss_count = cam_detail.miss_count + 1
            upd['miss_count'] = miss_count if miss_count < MAX_MISS_COUNT else None

        if upd:
            manage.Cam.objects.filter(id=cam_detail.id).update(**upd)

    @classmethod
    def add_sentinel(cls, containers):
        """Adds a Cam cleanup sentinel to a ContainerRepository, signifying
        that a full CAM collection has taken place and that old CAM records
        can be safely expired.

        """
        containers.setdefault(Cam, {})[Cam.sentinel] = Cam.sentinel


Cam.manager = CamManager
CamManager.sentinel = Cam.sentinel
