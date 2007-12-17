# -*- coding: utf-8 -*-
#
# Copyright 2007 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Authors: Stein Magnus Jodal <stein.magnus.jodal@uninett.no>
#

__copyright__ = "Copyright 2007 UNINETT AS"
__license__ = "GPL"
__author__ = "Stein Magnus Jodal (stein.magnus.jodal@uninett.no)"
__id__ = "$Id$"

import IPy

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import RequestContext

from nav.models.manage import Netbox
from nav.django.shortcuts import render_to_response

from nav.web.templates.IpDevInfoTemplate import IpDevInfoTemplate
from nav.web.ipdevinfo.forms import SearchForm
from nav.web.ipdevinfo.context_processors import search_form_processor

def search(request):
    search_form = None

    if request.method == 'GET':
        search_form = SearchForm(request.GET)
    elif request.method == 'POST':
        search_form = SearchForm(request.POST)

    if search_form is not None and search_form.is_valid():
        # Preprocess query string
        query = search_form.cleaned_data['query'].strip().lower()

        # IPv4, v6 or hostname?
        try:
            ip_version = IPy.parseAddress(query)[1]
        except ValueError:
            ip_version = None

        # Redirect to details view
        if ip_version is not None:
            return HttpResponseRedirect(
                reverse('ipdevinfo-details-by-addr', kwargs={'addr': query}))
        else:
            return HttpResponseRedirect(
                reverse('ipdevinfo-details-by-name', kwargs={'name': query}))

    return render_to_response(IpDevInfoTemplate, 'ipdevinfo/base.html', {},
        context_instance=RequestContext(request,
            processors=[search_form_processor]))

def ipdev_details(request, name=None, addr=None):
    netbox = None

    def get_host_info(host):
        """Lookup information about host in DNS etc."""
        import socket

        # Build a dictionary with information about the host
        host_info = {'host': host, 'addresses': []}

        # Use getaddrinfo, as it supports both IPv4 and v6
        try:
            addrinfo = socket.getaddrinfo(host, None)
        except socket.gaierror, e:
            pass # FIXME

        # For each addr the addr or name resolves to, lookup the reverse and
        # add it to host_info['addresses']
        added_addresses = []
        for (family, socktype, proto, canonname, sockaddr) in addrinfo:
            hostaddr = sockaddr[0]

            # Only add each addr once
            if hostaddr not in added_addresses:
                added_addresses.append(hostaddr)
                this_address = {'addr': hostaddr}
                try:
                    this_address['name'] = socket.gethostbyaddr(hostaddr)[0]
                except socket.herror, (errno, errstr):
                    this_address['error'] = errstr
                host_info['addresses'].append(this_address)
        host_info['addresses'].sort()

        return host_info

    # Lookup IP device in NAV
    if name is not None:
        try:
            # FIXME: Fuzzy match a bit
            netbox = Netbox.objects.get(sysname=name)
        except Netbox.DoesNotExist:
            pass
    elif addr is not None:
        try:
            netbox = Netbox.objects.get(ip=addr)
        except Netbox.DoesNotExist:
            pass
    else:
        # Require name or addr to be set
        HttpResponseRedirect(reverse('ipdevinfo-search'))

    return render_to_response(IpDevInfoTemplate, 'ipdevinfo/ipdev-details.html',
        {
            'host_info': get_host_info(name or addr),
            'netbox': netbox,
        },
        context_instance=RequestContext(request,
            processors=[search_form_processor]))

