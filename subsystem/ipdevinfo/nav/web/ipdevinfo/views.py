# -*- coding: utf-8 -*-
#
# Copyright 2007-2008 UNINETT AS
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

__copyright__ = "Copyright 2007-2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Stein Magnus Jodal (stein.magnus.jodal@uninett.no)"
__id__ = "$Id$"

import IPy
import re

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import RequestContext

from nav.models.manage import Netbox, Module, SwPort, GwPort
from nav.models.service import Service
from nav.django.shortcuts import render_to_response, object_list

from nav.web.templates.IpDevInfoTemplate import IpDevInfoTemplate
from nav.web.ipdevinfo.forms import SearchForm
from nav.web.ipdevinfo.context_processors import search_form_processor

def search(request):
    """Search for an IP device"""

    errors = []
    query = None
    netboxes = Netbox.objects.none()

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

        # Find matches to query
        if ip_version is not None:
            netboxes = Netbox.objects.filter(ip=query)
            if len(netboxes) == 0:
                # Could not find IP device, redirect to host detail view
                return HttpResponseRedirect(reverse('ipdevinfo-details-by-addr',
                        kwargs={'addr': query}))
        elif re.match('^[a-z0-9-]+(\.[a-z0-9-]+)*$', query) is not None:
            netboxes = Netbox.objects.filter(sysname__icontains=query)
            if len(netboxes) == 0:
                # Could not find IP device, redirect to host detail view
                return HttpResponseRedirect(reverse('ipdevinfo-details-by-name',
                        kwargs={'name': query}))
        else:
            errors.append('The query does not seem to be a valid IP address'
                + ' (v4 or v6) or a hostname.')

        # If only one hit, redirect to details view
        if len(netboxes) == 1:
            return HttpResponseRedirect(reverse('ipdevinfo-details-by-name',
                    kwargs={'name': netboxes[0].sysname}))

    # Else, show list of results
    return render_to_response(IpDevInfoTemplate, 'ipdevinfo/search.html',
        {
            'errors': errors,
            'query': query,
            'netboxes': netboxes,
        },
        context_instance=RequestContext(request,
            processors=[search_form_processor]))

def ipdev_details(request, name=None, addr=None):
    """Show detailed view of one IP device"""

    def get_host_info(host):
        """Lookup information about host in DNS etc."""
        import socket
        from nav import natsort

        # Build a dictionary with information about the host
        host_info = {'host': host, 'addresses': []}

        # Use getaddrinfo, as it supports both IPv4 and v6
        try:
            addrinfo = socket.getaddrinfo(host, None)
        except socket.gaierror, (errno, errstr):
            addrinfo = []

        # Extract all unique addresses
        unique_addresses = []
        for (family, socktype, proto, canonname, sockaddr) in addrinfo:
            hostaddr = sockaddr[0]
            if hostaddr not in unique_addresses:
                unique_addresses.append(hostaddr)
        unique_addresses.sort(key=natsort.split)

        # Lookup the reverse and add it to host_info['addresses']
        for addr in unique_addresses:
                this = {'addr': addr}
                try:
                    this['name'] = socket.gethostbyaddr(addr)[0]
                except socket.herror, (errno, errstr):
                    this['error'] = errstr
                host_info['addresses'].append(this)

        return host_info

    errors = []
    host_info = get_host_info(name or addr)
    netbox = Netbox.objects.none()

    # Lookup IP device in NAV
    if name is not None:
        try:
            netbox = Netbox.objects.get(sysname=name)
        except Netbox.DoesNotExist:
            pass
    elif addr is not None:
        try:
            netbox = Netbox.objects.get(ip=addr)
        except Netbox.DoesNotExist:
            # Check if any reverse addresses from DNS matches a netbox
            for address in host_info['addresses']:
                if 'name' in address:
                    try:
                        netbox = Netbox.objects.get(sysname=address['name'])
                        break # Exit loop at first match
                    except Netbox.DoesNotExist:
                        pass
    else:
        # Require name or addr to be set
        HttpResponseRedirect(reverse('ipdevinfo-search'))

    return render_to_response(IpDevInfoTemplate,
        'ipdevinfo/ipdev-details.html',
        {
            'errors': errors,
            'host_info': host_info,
            'netbox': netbox,
        },
        context_instance=RequestContext(request,
            processors=[search_form_processor]))

def module_details(request, netbox_sysname, module_number):
    """Show detailed view of one IP device module"""

    module = get_object_or_404(Module, netbox__sysname=netbox_sysname,
        module_number=module_number)

    return render_to_response(IpDevInfoTemplate,
        'ipdevinfo/module-details.html',
        {
            'module': module,
        },
        context_instance=RequestContext(request,
            processors=[search_form_processor]))

def port_details(request, netbox_sysname, module_number, port_type, port_id):
    """Show detailed view of one IP device port"""

    if port_type == 'swport':
        port = get_object_or_404(SwPort, id=port_id)
    elif port_type == 'gwport':
        port = get_object_or_404(GwPort, id=port_id)

    return render_to_response(IpDevInfoTemplate,
        'ipdevinfo/port-details.html',
        {
            'port_type': port_type,
            'port': port,
        },
        context_instance=RequestContext(request,
            processors=[search_form_processor]))

def service_list(request, handler=None):
    """List services with given handler or any handler"""

    page = request.GET.get('page', '1')

    services = Service.objects.select_related(depth=1)
    if handler:
        services = services.filter(handler=handler)

    handler_list = Service.objects.values('handler').distinct()

    # Pass on to generic view
    return object_list(IpDevInfoTemplate,
        request,
        services,
        paginate_by=100,
        page=page,
        template_name='ipdevinfo/service-list.html',
        extra_context={
            'show_ipdev_info': True,
            'handler_list': handler_list,
            'handler': handler,
        },
        allow_empty=True,
        context_processors=[search_form_processor],
        template_object_name='service')

def service_matrix(request):
    """Show service status in a matrix with one IP Device per row and one
    service handler per column"""

    handler_list = [h['handler']
        for h in Service.objects.values('handler').distinct()]

    matrix_dict = {}
    for service in Service.objects.select_related(depth=1):
        if service.netbox.id not in matrix_dict:
            matrix_dict[service.netbox.id] = {
                'sysname': service.netbox.sysname,
                'netbox': service.netbox,
                'services': [None for handler in handler_list],
            }
        index = handler_list.index(service.handler)
        matrix_dict[service.netbox.id]['services'][index] = service

    matrix = matrix_dict.values()

    return render_to_response(IpDevInfoTemplate,
        'ipdevinfo/service-matrix.html',
        {
            'handler_list': handler_list,
            'matrix': matrix,
        },
        context_instance=RequestContext(request,
            processors=[search_form_processor]))
