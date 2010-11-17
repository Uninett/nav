# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
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

from django.db import connection, transaction, IntegrityError
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect

from nav.web.message import new_message, Messages

def render_delete(request, model, redirect, whitelist=[], extra_context={}):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse(redirect))
    if not len(request.POST.getlist('object')):
        new_message(
            request._req,
            "You need to select at least one object to edit",
            Messages.ERROR)
        return HttpResponseRedirect(reverse(redirect))

    objects = model.objects.filter(
        pk__in=request.POST.getlist('object')
    ).order_by('pk')
    related = dependencies(objects, whitelist)

    for obj in objects:
        if obj.pk in related:
            obj.related_objects = related[obj.pk]

    if request.POST.get('confirm'):
        try:
            qs_delete(objects)
        except IntegrityError, ex:
            # We can't delete.
            # Some of the objects we want to delete is referenced by another
            # table without any ON DELETE rules.
            msg = "Integrity failed: %s" % ex
            new_message(request._req, msg, Messages.ERROR)
        except Exception, ex:
            # Something else went wrong
            msg = "Error: %s" % ex
            new_message(request._req, msg, Messages.ERROR)
        else:
            new_message(
                request._req,
                "Deleted %i rows" % len(objects),
                Messages.SUCCESS)
            return HttpResponseRedirect(reverse(redirect))

    info_dict = {
        'objects': objects,
        'sub_active': {'list': True},
    }
    extra_context.update(info_dict)
    return render_to_response('seeddb/delete.html',
        extra_context, RequestContext(request))

def dependencies(queryset, whitelist):
    primary_keys = [obj.pk for obj in queryset]
    related = queryset.model._meta.get_all_related_objects()
#    related += queryset.model._meta.get_all_related_many_to_many_objects()

    related_objects = {}
    for rel in related:
        if rel.model not in whitelist:
            continue
        name = rel.var_name
        field = rel.field.name
        lookup = "%s__in" % field
        params = {lookup: primary_keys}
        objects = rel.model.objects.filter(**params)
        for obj in objects:
            obj.object_name = name
            attr = getattr(obj, '%s_id' % field)
            if attr not in related_objects:
                related_objects[attr] = []
            related_objects[attr].append(obj)

    return related_objects

@transaction.commit_manually
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
    try:
        cursor.execute(sql, (pk_list,))
    except:
        # Something went wrong, rollback and re-raise exception
        transaction.rollback()
        raise
    else:
        transaction.commit()
        # FIXME Right return value?
        return cursor.rowcount
