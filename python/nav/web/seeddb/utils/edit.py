# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
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

import logging
from socket import gethostbyaddr, gethostbyname, error as SocketError

from IPy import IP

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, Http404
from django.db.models import Q
from django.urls import reverse, NoReverseMatch

from nav.web.message import new_message, Messages
from nav.models.manage import Netbox, NetboxCategory, NetboxGroup

_logger = logging.getLogger(__name__)


def render_edit(
    request,
    model,
    form_model,
    object_id,
    redirect,
    template='seeddb/edit.html',
    lon=None,
    lat=None,
    extra_context=None,
    action='edit',
):
    """Handles editing for objects in seeddb."""
    if not extra_context:
        extra_context = {}

    obj = _get_object(model, object_id)
    verbose_name = model._meta.verbose_name

    if not obj and (lat and lon):
        obj = model(position='({0},{1})'.format(lat, lon))

    original_pk = getattr(obj, 'pk', None)
    if action == 'copy' and original_pk:
        obj.pk = None
    if request.method == 'POST':
        form = form_model(request.POST, instance=obj)
        if form.is_valid():
            # TODO: It's kinda hackish to put this here. Discuss during review
            # Store devices in group when editing a device group (which we
            # have no idea if we are doing or not)
            if model == NetboxGroup:
                netboxes = request.POST.getlist('netboxes')
                _logger.debug('netboxes in group: %s', netboxes)
                # Save model but make sure m2m is not saved. See
                # https://docs.djangoproject.com/en/1.4/topics/db/models
                # /#extra-fields-on-many-to-many-relationships
                obj = form.save(commit=False)
                obj.save()
                _connect_group_to_devices(obj, netboxes)
            else:
                obj = form.save()

            new_message(request, "Saved %s %s" % (verbose_name, obj), Messages.SUCCESS)
            try:
                return HttpResponseRedirect(reverse(redirect, args=(obj.pk,)))
            except NoReverseMatch:
                return HttpResponseRedirect(reverse(redirect))
    else:
        form = form_model(instance=obj)

    context = {
        'object': obj,
        'form': form,
        'title': 'Add new %s' % verbose_name,
        'verbose_name': verbose_name,
        'sub_active': {'add': True},
    }
    if obj:
        if obj.pk:
            context.update(
                {
                    'title': 'Edit %s' % verbose_name,
                    'detail_page_name': obj,
                    'sub_active': {'edit': True},
                }
            )
        else:
            context.update(
                {
                    'title': 'Copy %s "%s"' % (verbose_name, original_pk),
                    'sub_active': {'edit': True},
                }
            )
    context.update(extra_context)
    return render(request, template, context)


def _get_object(model, object_id, identifier_attr='pk'):
    """Get object if it exists, else raise 404"""
    try:
        return get_object_or_404(model, **{identifier_attr: object_id})
    except Http404:
        pass


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
        sysname = gethostbyaddr(str(ip_addr))[0]
    except SocketError:
        sysname = str(ip_addr)
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
        ip_qs = Netbox.objects.filter(Q(ip=str(ip_addr)), ~Q(id=netbox_id))
    else:
        ip_qs = Netbox.objects.filter(ip=str(ip_addr))
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


def _connect_group_to_devices(group, netbox_ids):
    """
    Connect a NetboxGroup and Netboxes by creating instances of
    NetboxCategories

    :param nav.models.manage.NetboxGroup group: A netboxgroup
    :param list[str] netbox_ids: a result from a request.POST.getlist that
                                 should contain netbox id's as strings
    """
    netboxids = [int(x) for x in netbox_ids]

    # Delete existing netboxcategories that are not in request
    NetboxCategory.objects.filter(category=group).exclude(
        netbox__pk__in=netboxids
    ).delete()

    # Add new netboxcategories that are in request
    for netboxid in netboxids:
        try:
            NetboxCategory.objects.get(category=group, netbox__pk=netboxid)
        except NetboxCategory.DoesNotExist:
            netbox = Netbox.objects.get(pk=netboxid)
            NetboxCategory.objects.create(category=group, netbox=netbox)
