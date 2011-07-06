# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 UNINETT AS
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

"""Functions for editing general objects in seeddb.

(Not netboxes and services).
"""

from IPy import IP
from socket import gethostbyaddr, gethostbyname, error as SocketError

from django.core.urlresolvers import reverse, NoReverseMatch
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, Http404
from django.db.models import Q

from nav.web.message import new_message, Messages
from nav.models.manage import Netbox

def render_edit(request, model, form_model, object_id, redirect, \
        identifier_attr='pk', title_attr='pk', template='seeddb/edit.html', \
        extra_context=None):
    """Handles editing for objects in seeddb.
    """

    if not extra_context:
        extra_context = {}

    obj = _get_object(model, object_id, identifier_attr)
    (identifier, title) = _get_identifier_title(
        obj, identifier_attr, title_attr)
    verbose_name = model._meta.verbose_name

    if request.method == 'POST':
        form = form_model(request.POST, instance=obj)
        if form.is_valid():
            obj = form.save()
            (identifier, title) = _get_identifier_title(
                obj, identifier_attr, title_attr)
            new_message(request._req,
                 "Saved %s %s" % (verbose_name, title),
                 Messages.SUCCESS)
            try:
                return HttpResponseRedirect(reverse(redirect, args=(identifier,)))
            except NoReverseMatch:
                return HttpResponseRedirect(reverse(redirect))
    else:
        form = form_model(instance=obj)

    context = {
        'object': obj,
        'form': form,
        'title': 'Add new %s' % verbose_name,
        'sub_active': {'add': True},
    }
    if obj:
        context.update({
            'title': 'Edit %s "%s"' % (verbose_name, title),
            'sub_active': {'edit': True},
        })
    extra_context.update(context)
    return render_to_response(template,
        extra_context, RequestContext(request))

def _get_object(model, object_id, identifier_attr):
    """Fetches the object where identifier_attr=object_id.

    model           - the model the lookup is performed on
    object_id       - the value we are looking for
    identifier_attr - the name of the column we are looking for object_id in

    Returns:
     - the object if found
     - none if object_id is a None value

    Raises:
     - Http404 if object_id is not a None value, but a corresponding object was
       not found.
    """
    if object_id:
        try:
            params = {identifier_attr: object_id}
            obj = model.objects.get(**params)
        except model.DoesNotExist:
            raise Http404
        return obj
    return None

def _get_identifier_title(obj, identifier_attr, title_attr):
    """Gets the values for given attributes from an object.

    obj - the object we are looking at
    identifier_attr - the name of the attribute we will use as identifier
    title_attr - the name of the attribute we will use as the title

    Returns:
     - A tuple with the identifier and title.
    """
    identifier = None
    title = None
    if obj:
        identifier = getattr(obj, identifier_attr)
        title = getattr(obj, title_attr)
    return (identifier, title)

def resolve_ip_and_sysname(name):
    """Given a name that can be either an ip or a hostname/domain name, this
    function looks up IP and hostname.

    name - ip or hostname

    Returns:
     - tuple with ip-addres and sysname
    """
    try:
        ip_addr = IP(name)
    except ValueError:
        ip_addr = IP(gethostbyname(name))
    try:
        sysname = gethostbyaddr(unicode(ip_addr))[0]
    except SocketError:
        sysname = unicode(ip_addr)
    return (ip_addr, sysname)

def does_ip_exist(ip_addr, netbox_id=None):
    """Checks if the given IP already exist in database.

    Parameters:
     * ip_addr   - the IP addres to look for.
     * netbox_id - a netbox primary key that can have the given ip_addr, and
                   the function will still return False.

    Returns:
     - True if the IP already exists in the database (and the netbox with the
       IP is not the same as the given netbox_id).
     - False if not.
    """
    if netbox_id:
        ip_qs = Netbox.objects.filter(Q(ip=unicode(ip_addr)), ~Q(id=netbox_id))
    else:
        ip_qs = Netbox.objects.filter(ip=unicode(ip_addr))
    return ip_qs.count() > 0

def does_sysname_exist(sysname, netbox_id=None):
    """Checks if given sysname exists in database.

    Parameters:
     * sysname   - the sysname addres to look for.
     * netbox_id - a netbox primary key that can have the given ip_addr, and
                   the function will still return False.

    Returns:
     - True if the sysname already exists in the database (and the netbox with
       the sysname is not the same as the given netbox_id).
     - False if not.
    """
    if netbox_id:
        sysname_qs = Netbox.objects.filter(Q(sysname=sysname), ~Q(id=netbox_id))
    else:
        sysname_qs = Netbox.objects.filter(sysname=sysname)
    return sysname_qs.count() > 0
