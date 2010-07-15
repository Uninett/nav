# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2008 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

import IPy
import re
import datetime as dt

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.db.models import Q
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.views.generic.list_detail import object_list

from nav.models.cabling import Cabling, Patch
from nav.models.event import AlertHistory
from nav.models.manage import Netbox, Module, Interface, Prefix, Vlan, Arp, Cam
from nav.models.rrd import RrdFile, RrdDataSource
from nav.models.service import Service

from nav.web.ipdevinfo.forms import SearchForm, ActivityIntervalForm
from nav.web.ipdevinfo.context_processors import search_form_processor
from nav.web.ipdevinfo import utils

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
            # Check perfect match first
            filter = Q(sysname=query)
            if settings.DOMAIN_SUFFIX is not None:
                filter |= Q(sysname='%s%s' % (query, settings.DOMAIN_SUFFIX))
            netboxes = Netbox.objects.filter(filter)
            if len(netboxes) != 1:
                # No exact match, search for matches in substrings
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
    return render_to_response('ipdevinfo/search.html',
        {
            'errors': errors,
            'query': query,
            'netboxes': netboxes,
        },
        context_instance=RequestContext(request,
            processors=[search_form_processor]))

def ipdev_details(request, name=None, addr=None, netbox_id=None):
    """Show detailed view of one IP device"""

    if netbox_id:
        netbox = get_object_or_404(Netbox, id=netbox_id)
        return HttpResponseRedirect(netbox.get_absolute_url())

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

    def get_netbox(name=None, addr=None, host_info=None):
        """Lookup IP device in NAV by either hostname or IP address"""

        # Prefetch related objects as to reduce number of database queries
        netboxes = Netbox.objects.select_related(depth=2)
        netbox = None

        if name:
            try:
                netbox = netboxes.get(sysname=name)
            except Netbox.DoesNotExist:
                pass
        elif addr:
            try:
                netbox = netboxes.get(ip=addr)
            except Netbox.DoesNotExist:
                pass
        elif host_info:
            for address in host_info['addresses']:
                if 'name' in address:
                    try:
                        netbox = netboxes.get(sysname=address['name'])
                        break # Exit loop at first match
                    except Netbox.DoesNotExist:
                        pass

        return netbox

    def get_recent_alerts(netbox, days_back=7, max_num_alerts=15):
        """Returns the most recents alerts related to a netbox"""

        # Limit to alerts which where closed in the last days or which are
        # still open
        lowest_end_time = dt.datetime.now() - dt.timedelta(days=days_back)

        filter_stateful = Q(end_time__gt=lowest_end_time)
        filter_stateless = (Q(end_time__isnull=True)
            & Q(start_time__gt=lowest_end_time))
        qs = netbox.alerthistory_set.filter(filter_stateful | filter_stateless
            ).order_by('-start_time')
        count = qs.count()
        raw_alerts = qs[:max_num_alerts]

        alerts = []
        for alert in raw_alerts:
            if alert.source.name == 'serviceping':
                try:
                    alert_type = Service.objects.get(id=alert.subid).handler
                except Service.DoesNotExist:
                    alert_type = '%s (%s)' % (alert.event_type, alert.subid)
            else:
                alert_type = '%s' % alert.event_type

            try:
                message = alert.messages.filter(type='sms')[0].message
            except IndexError:
                message = None

            alerts.append({
                'alert': alert,
                'type': alert_type,
                'message': message,
            })

        return {
            'days_back': days_back,
            'alerts': alerts,
            'count': count,
            'is_more_alerts': count > max_num_alerts,
        }

    def get_port_view(netbox, perspective, activity_interval):
        """
        Returns a dict structure with all modules and ports on the netbox.

        Arguments:
        perspective -- decides what kind of ports are included.
        activity_interval -- number of days to check for port activity.

        """

        port_view = {
            'perspective': perspective,
            'modules': [],
            'activity_interval': activity_interval,
            'activity_interval_start':
                dt.datetime.now() - dt.timedelta(days=activity_interval),
        }

        # Check if we got data for the entire search interval
        try:
            port_view['activity_data_start'] = netbox.cam_set.order_by(
                'start_time')[0].start_time
            port_view['activity_data_interval'] = (
                dt.datetime.now() - port_view['activity_data_start']).days
            port_view['activity_complete_data'] = (
                port_view['activity_data_start'] <
                port_view['activity_interval_start'])
        except IndexError:
            port_view['activity_data_start'] = None
            port_view['activity_data_interval'] = 0
            port_view['activity_complete_data'] = False

        # Add the modules
        for module in netbox.module_set.select_related():
            port_view['modules'].append(utils.get_module_view(
                module, perspective, activity_interval))

        # Add interfaces with no module
        port_view['modules'].append(utils.get_module_view(
            None, perspective, activity_interval, netbox))

        return port_view

    def get_prefix_info(addr):
        try:
            return Prefix.objects.select_related().extra(
                select={"mask_size": "masklen(netaddr)"},
                where=["%s << netaddr AND nettype <> 'scope'"],
                order_by=["-mask_size"],
                params=[addr])[0]
        except:
            return None

    def get_arp_info(addr):
        try:
            return Arp.objects.filter(ip=addr).order_by('-end_time', '-start_time')[0]
        except:
            return None


    def get_cam_info(mac):
        try:
            return Cam.objects.filter(mac=mac).order_by('-end_time', '-start_time')[0]
        except:
            return None


    port_view_perspective = request.GET.get('view', None)

    # Get port activity search interval from form
    activity_interval = 30
    if port_view_perspective == 'swportactive':
        if 'interval' in request.GET:
            activity_interval_form = ActivityIntervalForm(request.GET)
            if activity_interval_form.is_valid():
                activity_interval = activity_interval_form.cleaned_data[
                    'interval']
        else:
            activity_interval_form = ActivityIntervalForm(
                initial={'interval': activity_interval})
    else:
        activity_interval_form = None

    # Get data needed by the template
    host_info = get_host_info(name or addr)
    netbox = get_netbox(name=name, addr=addr, host_info=host_info)

    # Assign default values to variables
    no_netbox = {
        'prefix': None,
        'arp': None,
        'cam': None,
        'dt_max': dt.datetime.max,
        'days_since_active': 7,
    }
    alert_info = None
    port_view = None

    # If addr or host not a netbox it is not monitored by NAV
    if netbox is None:
        if addr is None and len(host_info['addresses']) > 0:
            # Picks the first address in array if addr not specified
            addr = host_info['addresses'][0]['addr']

        no_netbox['prefix'] = get_prefix_info(addr)

        if no_netbox['prefix']:
            no_netbox['arp'] = get_arp_info(addr)
            if no_netbox['arp']:
                no_netbox['cam'] = get_cam_info(no_netbox['arp'].mac)
                if no_netbox['arp'].end_time < dt.datetime.max:
                    no_netbox['days_since_active'] = (dt.now() - no_netbox['arp'].end_time).days

    else:
        alert_info = get_recent_alerts(netbox)

        # Select port view to display
        run_port_view = True
        valid_perspectives = ('swportstatus', 'swportactive', 'gwportstatus')
        if port_view_perspective not in valid_perspectives:
            if netbox.get_swports().count():
                port_view_perspective = 'swportstatus'
            elif netbox.get_gwports().count():
                port_view_perspective = 'gwportstatus'
            else:
                run_port_view = False

        if run_port_view:
            port_view = get_port_view(
                netbox, port_view_perspective, activity_interval)

    return render_to_response(
        'ipdevinfo/ipdev-details.html',
        {
            'host_info': host_info,
            'netbox': netbox,
            'alert_info': alert_info,
            'port_view': port_view,
            'activity_interval_form': activity_interval_form,
            'no_netbox': no_netbox,
        },
        context_instance=RequestContext(request,
            processors=[search_form_processor]))

def module_details(request, netbox_sysname, module_number):
    """Show detailed view of one IP device module"""

    def get_module_view(module_object, perspective, activity_interval=None):
        """
        Returns a dict structure with all ports on the module.

        Arguments:
        perspective -- decides what kind of ports are included.
        activity_interval -- number of days to check for port activity.

        """

        module = utils.get_module_view(
            module_object, perspective, activity_interval)

        if activity_interval is not None:
            module['activity_interval'] = activity_interval
            module['activity_interval_start'] = (
                    dt.datetime.now() - dt.timedelta(days=activity_interval))

            # Check if we got data for the entire search interval
            try:
                module['activity_data_start'] = (
                    module_object.netbox.cam_set.order_by(
                        'start_time')[0].start_time)
                module['activity_data_interval'] = (
                    dt.datetime.now() - module['activity_data_start']).days
                module['activity_complete_data'] = (
                    module['activity_data_start'] <
                    module['activity_interval_start'])
            except IndexError:
                module['activity_data_start'] = None
                module['activity_data_interval'] = 0
                module['activity_complete_data'] = False

        return module

    # Get port activity search interval from form
    activity_interval = 30
    if 'interval' in request.GET:
        activity_interval_form = ActivityIntervalForm(request.GET)
        if activity_interval_form.is_valid():
            activity_interval = activity_interval_form.cleaned_data[
                'interval']
    else:
        activity_interval_form = ActivityIntervalForm(
            initial={'interval': activity_interval})

    module = get_object_or_404(Module.objects.select_related(depth=1),
        netbox__sysname=netbox_sysname, module_number=module_number)
    swportstatus_view = get_module_view(module, 'swportstatus')
    swportactive_view = get_module_view(
        module, 'swportactive', activity_interval)
    gwportstatus_view = get_module_view(module, 'gwportstatus')

    return render_to_response(
        'ipdevinfo/module-details.html',
        {
            'module': module,
            'swportstatus_view': swportstatus_view,
            'swportactive_view': swportactive_view,
            'gwportstatus_view': gwportstatus_view,
            'activity_interval_form': activity_interval_form,
        },
        context_instance=RequestContext(request,
            processors=[search_form_processor]))

def port_details(request, netbox_sysname, module_number=None, port_type=None,
    port_id=None, port_name=None):
    """Show detailed view of one IP device port"""

    if not (port_id or port_name):
        return Http404

    ports = Interface.objects.select_related(depth=2)

    if port_id is not None:
        port = get_object_or_404(ports, id=port_id)
    elif port_name is not None:
        port = get_object_or_404(ports, netbox__sysname=netbox_sysname, ifname=port_name)

    return render_to_response(
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

    services = Service.objects.select_related(depth=1).order_by(
        'netbox__sysname', 'handler')
    if handler:
        services = services.filter(handler=handler)

    handler_list = Service.objects.values('handler').distinct()

    # Pass on to generic view
    return object_list(
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
                'services': [None for _ in handler_list],
            }
        index = handler_list.index(service.handler)
        matrix_dict[service.netbox.id]['services'][index] = service

    matrix = matrix_dict.values()

    return render_to_response(
        'ipdevinfo/service-matrix.html',
        {
            'handler_list': handler_list,
            'matrix': matrix,
        },
        context_instance=RequestContext(request,
            processors=[search_form_processor]))
