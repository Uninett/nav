#
# Copyright (C) 2017 Uninett AS
# Copyright (C) 2022 Sikt
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

from django.utils.encoding import force_str
from django.db.models import Q

from nav.models.profiles import Account
from . import find_modelname
from .models import LogEntry


LATEST_N_AUDITLOG_ENTRIES = 15


def get_auditlog_entries(
    modelname=None,
    queryset=None,
    pks=None,
    limit=LATEST_N_AUDITLOG_ENTRIES,
    subsystem=None,
):
    """Get up to <limit> entries involving <modelname>

    Limit results to <pks>, <queryset> and/or <subsystem>
    """
    assert modelname or queryset, (
        "At least one of <modelname> or <queryset> must be given"
    )
    if pks is None:
        pks = []
    if queryset is not None and queryset.exists():
        qs_pks = set(force_str(o.pk) for o in queryset)
        if qs_pks:
            if pks:
                pks = qs_pks.intersection(pks)
            else:
                pks = qs_pks
        if modelname is None:
            modelname = find_modelname(queryset[0])
    object_query = Q(object_model=modelname)
    target_query = Q(target_model=modelname)
    actor_query = Q(actor_model=modelname)
    filter_query = object_query | target_query | actor_query
    qs = LogEntry.objects.filter(filter_query)
    if pks:
        object_query = Q(object_pk__in=pks)
        target_query = Q(target_pk__in=pks)
        actor_query = Q(actor_pk__in=pks)
        filter_query = object_query | target_query | actor_query
        qs = qs.filter(filter_query)
    if subsystem:
        qs = qs.filter(subsystem=subsystem)
    entries = qs.distinct().order_by('-timestamp')[:limit]
    return entries


def get_all_historical_actors():
    "List all recorded actors (need not be accounts!), including deleted ones"
    actors = set()
    for pk, summary in LogEntry.objects.values_list("actor_pk", "summary").distinct():
        name = summary.split(' ', 1)[0].strip(':')
        actors.add((name, pk))
    return sorted(actors)


def get_lurkers():
    "Get a list of current accounts that have no actor entries in the audit log"
    actor_pks = [pk for _, pk in get_all_historical_actors()]
    return Account.objects.exclude(pk__in=actor_pks)


def get_zombies():
    "Get a list of accounts that should have been deleted according to the auditlog"
    deleted_accounts = LogEntry.objects.filter(
        verb="delete-account",
    )
    deleted_account_ids = [
        int(pk)
        for pk in deleted_accounts.exclude(
                object_pk__isnull=True,
        ).values_list("object_pk", flat=True)
    ]
    return Account.objects.filter(pk__in=deleted_account_ids)
