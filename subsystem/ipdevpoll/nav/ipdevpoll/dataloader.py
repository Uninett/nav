# -*- coding: utf-8 -*-
#
# Copyright (C) 2008, 2009 UNINETT AS
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
"""ipdevpoll seed data loading.

To perform its polling duties, the ipdevpoll system must know what
netboxes to poll, what type netboxes are and what vendors they come
from.

This module contains functionality to periodically load from the
database and cache a list of Netboxes to poll.  It also loads and
caches Type and Vendor data.  

Data is loaded synchronously from the database using Django models -
the model objects are "shadowed" using the shadows.Netbox class, so
that the resulting objects will be guaranteed to stay away from the
database during asynchronous operation.  The loading/reloading of data
from the database will be executed in a separate thread to avoid
interfering with the daemon's asynchronous operations.

Periodic reloads are scheduled through the reactor.

"""

import logging

from twisted.internet import reactor, defer, task, threads

from nav.models import manage
from nav import ipdevpoll
import storage


class NetboxLoader(dict):
    def __init__(self):
        super(NetboxLoader, self).__init__()
        self.loop = None
        self._logger = ipdevpoll.get_instance_logger(self, id(self))

    def load_all_s(self):
        """Synchronously load netboxes from database."""
        queryset = manage.Netbox.objects.select_related(depth=2).all()
        netbox_list = storage.shadowify_queryset(queryset)
        netbox_dict = dict((netbox.id, netbox) for netbox in netbox_list)

        previous_ids = set(self.keys())
        current_ids = set(netbox_dict.keys())
        lost_ids = previous_ids.difference(current_ids)
        new_ids = current_ids.difference(previous_ids)
        
        self.clear()
        self.update(netbox_dict)

        self._logger.info(
            "Loaded %d netboxes from database (%d new, %d removed)", 
            len(netbox_dict), len(new_ids), len(lost_ids)
            )
        return len(self)

    def load_all(self):
        """Asynchronously load netboxes from database."""
        return threads.deferToThread(self.load_all_s)

    def initiate_looping_load(self, interval=5*60.0):
        """Run load_all() in five minute intervals.

        Returns a deferred that will fire callbacks after the first
        load operation.

        """
        deferred = self.load_all()
        self.loop = task.LoopingCall(self.load_all)
        self.loop.start(interval, now=False)
        return deferred
