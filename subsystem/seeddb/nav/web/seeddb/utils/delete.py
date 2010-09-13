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
from django.core.paginator import Paginator, InvalidPage
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect

from nav.django.utils import get_verbose_name
from nav.web.message import new_message, Messages
from nav.web.seeddb.forms.move import MoveOperationForm

def render_delete(request, model, redirect, extra_context={}):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse(redirect))
    if not len(request.POST.getlist('object')):
        new_message(request._req, "You need to select at least one object to edit", Messages.ERROR)
        return HttpResponseRedirect(reverse(redirect))

    objects = model.objects.filter(pk__in=request.POST.getlist('object'))


    if request.POST.get('confirm'):
        try:
            qs_delete(objects)
        except IntegrityError, ex:
            # We can't delete.
            # Some of the objects we want to delete is referenced by another table
            # without any ON DELETE rules.
            msg = "Integrity failed: %s" % ex
            new_message(request._req, msg, Messages.ERROR)
        except Exception, ex:
            # Something else went wrong
            msg = "Error: %s" % ex
            new_message(request._req, msg, Messages.ERROR)
        else:
            new_message(request._req, "YAY", Messages.SUCCESS)
            return HttpResponseRedirect(reverse(redirect))

    info_dict = {
        'objects': objects,
    }
    extra_context.update(info_dict)
    return render_to_response('seeddb/delete.html',
        extra_context, RequestContext(request))

def dependencies(qs):
    primary_keys = [object.pk for object in qs]
    related = qs.model._meta.get_all_related_objects()
#    related += qs.model._meta.get_all_related_many_to_many_objects()

    related_objects = {}
    for rel in related:
        field = rel.field.name
        accessor = rel.get_accessor_name()
        lookup = "%s__in" % field
        params = {lookup: primary_keys}
        objects = related.model.objects.filter(**params)

    return related_objects

@transaction.commit_manually
def qs_delete(qs):
    """Deletes objects from the database.

    Given a queryset containing the objects to be deleted, this method will
    either delete all without error, or delete none if there's an error.
    """
    qn = connection.ops.quote_name

    pk_list = [object.pk for object in qs]
    primary_key = qs.model._meta.pk.db_column
    table = qs.model._meta.db_table

    cursor = connection.cursor()
    sql = "DELETE FROM %(table)s WHERE %(field)s IN (%%s)" % {
        'table': qn(table),
        'field': qn(primary_key),
    }
    try:
        cursor.execute(sql, pk_list)
    except:
        # Something went wrong, rollback and re-raise exception
        transaction.rollback()
        raise
    else:
        transaction.commit()
        # FIXME Right return value?
        return cursor.rowcount
