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
from django.http import HttpResponseRedirect, Http404

from nav.django.utils import get_verbose_name
from nav.web.message import new_message, Messages
from nav.models.cabling import Cabling, Patch
from nav.models.manage import Netbox, NetboxType, Room, Location, Organization
from nav.models.manage import Usage, Vendor, Subcategory, Vlan, Prefix
from nav.models.service import Service

from nav.web.seeddb.forms import RoomForm, LocationForm, OrganizationForm, \
    UsageForm, NetboxTypeForm, VendorForm, SubcategoryForm, PrefixForm, \
    CablingForm, PatchForm

model = None
form_model = None
identifier_attr = 'pk'
title_attr = 'pk'
navpath = None
tab_template = ''
template = 'seeddb/edit.html'
redirect = ''

def render_edit(request, model, form_model, object_id, redirect,\
        identifier_attr='pk', title_attr='pk', template='seeddb/edit.html',\
        extra_context={}):

    object = _get_object(model, object_id, identifier_attr)
    (identifier, title) = _get_identifier_title(object, identifier_attr, title_attr)
    verbose_name = model._meta.verbose_name

    if request.method == 'POST':
        form = form_model(request.POST, instance=object)
        if form.is_valid():
            object = form.save()
            (identifier, title) = _get_identifier_title(object, identifier_attr, title_attr)
            new_message(request._req,
                 "Saved %s %s" % (verbose_name, title),
                 Messages.SUCCESS)
            return HttpResponseRedirect(reverse(redirect, args=(identifier,)))
    else:
        form = form_model(instance=object)

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
    return render_to_response(template,
        extra_context, RequestContext(request))

def _get_object(model, object_id, identifier_attr):
    if object_id:
        try:
            params = {identifier_attr: object_id}
            object = model.objects.get(**params)
        except model.DoesNotExist:
            raise Http404
        return object
    return None

def _get_identifier_title(object, identifier_attr, title_attr):
    identifier = None
    title = None
    if object:
        identifier = getattr(object, identifier_attr)
        title = getattr(object, title_attr)
    return (identifier, title)
