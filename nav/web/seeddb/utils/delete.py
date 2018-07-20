#
# Copyright (C) 2011, 2012 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

"""Functions for deleting objects from seeddb.
"""

import logging

from django.db import connection, transaction, IntegrityError
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect

from nav.django.utils import get_model_and_name, get_all_related_objects
from nav.web.message import new_message, Messages
from nav.auditlog.models import LogEntry

LOGGER = logging.getLogger(__name__)


@transaction.atomic()
def qs_delete(queryset):
    """Deletes objects from the database.

    Given a queryset containing the objects to be deleted, this method will
    either delete all without error, or delete none if there's an error.
    """
    quote_name = connection.ops.quote_name

    pk_list = tuple([obj.pk for obj in queryset])
    primary_key = queryset.model._meta.pk.db_column
    table = queryset.model._meta.db_table

    cursor = connection.cursor()
    sql = "DELETE FROM %(table)s WHERE %(field)s IN %%s" % {
        'table': quote_name(table),
        'field': quote_name(primary_key),
    }
    cursor.execute(sql, (pk_list,))
    return cursor.rowcount


def render_delete(request, model, redirect, whitelist=None, extra_context=None,
                  pre_delete_operation=None, delete_operation=qs_delete):
    """Handles input and rendering of general delete page.
    """
    if request.method != 'POST':
        return HttpResponseRedirect(reverse(redirect))
    if not len(request.POST.getlist('object')):
        new_message(request,
                    "You need to select at least one object to edit",
                    Messages.ERROR)
        return HttpResponseRedirect(reverse(redirect))

    if not whitelist:
        whitelist = []
    if not extra_context:
        extra_context = {}

    objects = model.objects.filter(
        pk__in=request.POST.getlist('object')
    ).order_by('pk')
    related = dependencies(objects, whitelist)

    for obj in objects:
        if obj.pk in related:
            obj.related_objects = related[obj.pk]

    if request.POST.get('confirm'):
        try:
            if pre_delete_operation:
                pre_delete_operation(objects)
            if delete_operation:
                delete_operation(objects)
        except IntegrityError as ex:
            # We can't delete.
            # Some of the objects we want to delete is referenced by another
            # table without any ON DELETE rules.
            msg = "Integrity failed: %s" % ex
            new_message(request, msg, Messages.ERROR)
        except Exception as ex:
            # Something else went wrong
            LOGGER.exception("Unhandled exception during delete: %r", request)
            msg = "Error: %s" % ex
            new_message(request, msg, Messages.ERROR)
        else:
            if delete_operation:
                new_message(request,
                            "Deleted %i rows" % len(objects), Messages.SUCCESS)
                log_deleted(request.account, objects, template=u'{actor} deleted {object}')
            else:
                new_message(request,
                            "Scheduled %i rows for deletion" % len(objects), Messages.SUCCESS)
                log_deleted(request.account, objects, template=u'{actor} scheduled {object} for deletion')
            return HttpResponseRedirect(reverse(redirect))

    info_dict = {
        'objects': objects,
        'sub_active': {'list': True},
    }
    extra_context.update(info_dict)
    return render_to_response('seeddb/delete.html',
        extra_context, RequestContext(request))


def log_deleted(account, objects, template):
    """Log the deletion of each object"""
    for obj in objects:
        LogEntry.add_delete_entry(account, obj, template=template)


def dependencies(queryset, whitelist):
    """Looks up related objects for the provided queryset.
    Only looks up models provided in the whitelist.

    Will only display related objects, not what will happen if the user choose
    to delete the objects in the queryset. The exact nature is defined in the
    database, and can range from CASCADE (all dependent rows are all deleted)
    to nothing, which will probably cause the delete statement to fail.
    """
    primary_keys = [obj.pk for obj in queryset]
    related = get_all_related_objects(queryset.model)

    related_objects = {}
    for rel in related:
        model, name = get_model_and_name(rel)
        if model not in whitelist:
            continue
        field = rel.field.name
        lookup = "%s__in" % field
        params = {lookup: primary_keys}
        objects = model.objects.filter(**params)
        for obj in objects:
            obj.object_name = name
            attr = getattr(obj, '%s_id' % field)
            if attr not in related_objects:
                related_objects[attr] = []
            related_objects[attr].append(obj)

    return related_objects
