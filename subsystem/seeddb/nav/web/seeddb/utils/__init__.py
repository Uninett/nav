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

from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect

from nav.django.utils import get_verbose_name
from nav.web.message import new_message, Messages

ITEMS_PER_PAGE = 100

def get_object(object_class, object_id):
    if not object_id:
        return None
    return object_class.objects.get(id=object_id)

def get_form(request, form_class, object):
    if request.method == 'POST':
        form = form_class(request.POST, instance=object)
    else:
        form = form_class(instance=object)
    return form

def should_update_primary_key(object, form):
    return object and object.id != form.cleaned_data['id']

def primary_key_update(object, form):
    from django.db import connection
    cur = connection.cursor()

    table = object._meta.db_table
    pk_col = object._meta.get_field('id').db_column
    old_pk_val = getattr(object, object._meta.get_field('id').attname)
    new_pk_val = form.cleaned_data['id']

    sql = 'UPDATE "%s" ' % table
    sql += 'SET "%s" = %%s ' % pk_col
    sql += 'WHERE "%s" = %%s' % pk_col

    params = (new_pk_val, old_pk_val)
    cur.execute(sql, params)

    return new_pk_val

def render_seeddb_edit(request, object_class, form_class, object_id, identifier_attr='pk', title_attr='pk', extra_context={}):
    object = None
    identifier = None
    title = None
    verbose_name = object_class._meta.verbose_name
    if object_id:
        try:
            params = {identifier_attr: object_id}
            object = object_class.objects.get(**params)
        except object_class.DoesNotExist:
            return HttpResponseRedirect(reverse(form_class.REDIRECT))
        identifier = getattr(object, identifier_attr)
        title = getattr(object, title_attr)
    if request.method == 'POST':
        form = form_class(request.POST, instance=object)
        if form.is_valid():
            if 'id' in form.cleaned_data and should_update_primary_key(object, form):
                new_pk = primary_key_update(object, form)
                return render_seeddb_edit(request, object_class, form_class,
                    new_pk, identifier_attr, title_attr, extra_context)

            object = form.save()
            identifier = getattr(object, identifier_attr)
            title = getattr(object, title_attr)
            new_message(request._req,
                 "Saved %s %s" % (verbose_name, title),
                 Messages.SUCCESS)
            return HttpResponseRedirect(reverse(form_class.REDIRECT, args=(identifier,)))
    else:
        form = form_class(instance=object)

    context = {
        'object': object,
        'form': form,
        'title': 'Add new %s' % verbose_name,
        'active': {'add': True},
    }
    if object:
        context.update({
            'title': 'Edit %s "%s"' % (verbose_name, title),
            'active': {'edit': True},
        })
    extra_context.update(context)
    return render_to_response('seeddb/edit.html',
        extra_context, RequestContext(request))

def group_query(qs, identifier):
    objects = {}
    for object in qs:
        if object[identifier] not in objects:
            objects[object[identifier]] = []
        objects[object[identifier]].append(object)
    return objects
