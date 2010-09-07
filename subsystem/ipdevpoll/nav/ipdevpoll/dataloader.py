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
from the database can be executed in a separate thread to avoid
interfering with the daemon's asynchronous operations.

"""

import logging

from twisted.internet import threads
from django.db import transaction

from nav.models import manage
from nav import ipdevpoll
import storage
from utils import django_debug_cleanup

class NetboxLoader(dict):
    """Loads netboxes from the database, synchronously or asynchronously.

    Access as a dictionary to retrieve information about the loaded
    netboxes.  The dictionary keys are netbox table primary keys, the
    values are shadows.Netbox objects.

    """

    def __init__(self):
        super(NetboxLoader, self).__init__()
        self.peak_count = 0
        self._logger = ipdevpoll.get_instance_logger(self, id(self))

    @transaction.commit_manually
    def load_all_s(self):
        """Synchronously load netboxes from database.

        Returns:

          A three-tuple, (new_ids, lost_ids, changed_ids), whose elements are
          sets of netbox IDs.

          - The first set are IDs that a new since the last load operation.

          - The second is the set of IDs that have been removed since the last
            load operation.

          - The third is the set of IDs of netboxes whose information have
            changed in the database since the last load operation.

        """
        queryset = manage.Netbox.objects.select_related(depth=1).filter(
            read_only__isnull=False, up='y')
        netbox_list = storage.shadowify_queryset(queryset)
        netbox_dict = dict((netbox.id, netbox) for netbox in netbox_list)

        django_debug_cleanup()

        previous_ids = set(self.keys())
        current_ids = set(netbox_dict.keys())
        lost_ids = previous_ids.difference(current_ids)
        new_ids = current_ids.difference(previous_ids)

        same_ids = previous_ids.intersection(current_ids)
        changed_ids = set(i for i in same_ids
                          if is_netbox_changed(self[i], netbox_dict[i]))

        # update self
        for i in lost_ids:
            del self[i]
        for i in new_ids:
            self[i] = netbox_dict[i]
        for i in same_ids:
            self[i].copy(netbox_dict[i])

        self.peak_count = max(self.peak_count, len(self))

        self._logger.info(
            "Loaded %d netboxes from database "
            "(%d new, %d removed, %d changed, %d peak)",
            len(netbox_dict), len(new_ids), len(lost_ids), len(changed_ids),
            self.peak_count
            )

        # We didn't change anything, but roll back the current transaction to
        # avoid idling
        transaction.rollback()

        return (new_ids, lost_ids, changed_ids)

    def load_all(self):
        """Asynchronously load netboxes from database."""
        return threads.deferToThread(self.load_all_s)


def is_netbox_changed(netbox1, netbox2):
    """Determine whether a netbox' information has changed enough to
    warrant a schedule change.

    """
    if netbox1.id != netbox2.id:
        raise Exception("netbox1 and netbox2 do not represent the same netbox")

    for attr in ('ip', 
                 'type', 
                 'read_only', 
                 'snmp_version', 
                 'device',
                 ):
        if getattr(netbox1, attr) != getattr(netbox2, attr):
                return True

    # Switching from up_to_date to not up_to_date warrants a reload, but not
    # the other way around.
    if netbox1.up_to_date and not netbox2.up_to_date:
        return True

    return False


