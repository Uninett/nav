# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2012 Uninett AS
# Copyright (C) 2020 Universitetet i Oslo
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

from collections import defaultdict
import logging

import django.db

from nav.models import manage, event
from nav import ipdevpoll
from nav.ipdevpoll.db import django_debug_cleanup, run_in_thread
from nav.ipdevpoll.config import get_netbox_filter
from . import storage


_logger = logging.getLogger(__name__)


def load_netbox(netbox_id):
    """Loads a single Netbox from the database, converted to a Shadow object.

    :param netbox_id: A Netbox integer primary key.
    :type netbox_id: int
    :rtype: nav.ipdevpoll.shadows.netbox.Netbox

    """
    related = ('room__location', 'type__vendor', 'category', 'organization')
    netbox = manage.Netbox.objects.select_related(*related).get(id=netbox_id)
    return storage.shadowify(netbox)


class NetboxLoader(dict):
    """Loads netboxes from the database, synchronously or asynchronously.

    Access as a dictionary to retrieve information about the loaded
    netboxes.  The dictionary keys are netbox table primary keys, the
    values are shadows.Netbox objects.

    """

    _logger = ipdevpoll.ContextLogger()

    def __init__(self):
        super(NetboxLoader, self).__init__()
        self.peak_count = 0
        # touch _logger to initialize logging context right away
        self._logger

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
        related = ('room__location', 'type__vendor', 'category', 'organization')
        snmp_down = set(
            event.AlertHistory.objects.unresolved('snmpAgentState').values_list(
                'netbox__id', flat=True
            )
        )
        self._logger.debug("These netboxes have active snmpAgentStates: %r", snmp_down)
        queryset = manage.Netbox.objects.filter(deleted_at__isnull=True)

        filter_groups_included = get_netbox_filter('groups_included')
        if filter_groups_included:
            queryset = queryset.filter(groups__id__in=filter_groups_included)

        filter_groups_excluded = get_netbox_filter('groups_excluded')
        if filter_groups_excluded:
            queryset = queryset.exclude(groups__id__in=filter_groups_excluded)

        queryset = list(queryset.select_related(*related))
        for netbox in queryset:
            netbox.snmp_up = netbox.id not in snmp_down
        netbox_list = storage.shadowify_queryset(queryset)
        netbox_dict = dict((netbox.id, netbox) for netbox in netbox_list)

        times = load_last_updated_times()
        for netbox in netbox_list:
            netbox.last_updated = times.get(netbox.id, {})

        django_debug_cleanup()

        previous_ids = set(self.keys())
        current_ids = set(netbox_dict.keys())
        lost_ids = previous_ids.difference(current_ids)
        new_ids = current_ids.difference(previous_ids)

        same_ids = previous_ids.intersection(current_ids)
        changed_ids = set(
            i for i in same_ids if is_netbox_changed(self[i], netbox_dict[i])
        )

        # update self
        for i in lost_ids:
            del self[i]
        for i in new_ids:
            self[i] = netbox_dict[i]
        for i in same_ids:
            self[i].copy(netbox_dict[i])

        self.peak_count = max(self.peak_count, len(self))

        anything_changed = len(new_ids) or len(lost_ids) or len(changed_ids)
        log = self._logger.info if anything_changed else self._logger.debug

        log(
            "Loaded %d netboxes from database "
            "(%d new, %d removed, %d changed, %d peak)",
            len(netbox_dict),
            len(new_ids),
            len(lost_ids),
            len(changed_ids),
            self.peak_count,
        )

        return (new_ids, lost_ids, changed_ids)

    def load_all(self):
        """Asynchronously load netboxes from database."""
        return run_in_thread(self.load_all_s)


def is_netbox_changed(netbox1, netbox2):
    """Determine whether a netbox' information has changed enough to
    warrant a schedule change.

    """
    if netbox1.id != netbox2.id:
        raise Exception("netbox1 and netbox2 do not represent the same netbox")

    for attr in (
        'ip',
        'type',
        'up',
        'snmp_up',
        'snmp_parameters',
        'deleted_at',
    ):
        if getattr(netbox1, attr) != getattr(netbox2, attr):
            _logger.debug(
                "%s.%s changed from %r to %r",
                netbox1.sysname,
                attr,
                getattr(netbox1, attr),
                getattr(netbox2, attr),
            )
            return True

    # Switching from up_to_date to not up_to_date warrants a reload, but not
    # the other way around.
    if netbox1.up_to_date and not netbox2.up_to_date:
        return True

    return False


def load_last_updated_times():
    """Loads the last-successful timestamps of each job of each netbox"""
    sql = """SELECT
               netboxid,
               job_name,
               MAX(end_time) AS end_time
             FROM
               ipdevpoll_job_log
             WHERE
               success
             GROUP BY netboxid, job_name
             """
    cursor = django.db.connection.cursor()
    cursor.execute(sql)
    times = defaultdict(dict)
    for netboxid, job_name, end_time in cursor.fetchall():
        times[netboxid][job_name] = end_time
    return dict(times)
