from __future__ import unicode_literals

from django.utils.encoding import force_text
from django.db.models import Q

from . import find_modelname
from .models import LogEntry

LATEST_N_AUDITLOG_ENTRIES = 15


def get_auditlog_entries(iterable, limit=LATEST_N_AUDITLOG_ENTRIES, subsystem=None):
    modelname = find_modelname(list(iterable)[0])
    pks = [force_text(i.pk) for i in iterable]
    object_query = Q(object_pk__in=pks, object_model=modelname)
    target_query = Q(target_pk__in=pks, object_model=modelname)
    actor_query = Q(actor_pk__in=pks, object_model=modelname)
    filter_query = object_query | target_query | actor_query
    qs = LogEntry.objects.filter(filter_query)
    if subsystem:
        qs = qs.filter(subsystem=subsystem)
    entries = qs.distinct().order_by('-timestamp')[:limit]
    return entries
