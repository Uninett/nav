#
# Copyright (C) 2007-2008 Uninett AS
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
"""Views for ipdevinfo"""
import json
import re
import logging
import datetime as dt

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.db.models import Q
from django.shortcuts import (render_to_response, get_object_or_404, redirect,
                              render)
from django.template import RequestContext
from django.utils import six

from nav.django.templatetags.thresholds import find_rules
from nav.metrics.errors import GraphiteUnreachableError

from nav.models.manage import (Netbox, Module, Interface, Prefix, Arp, Cam,
                               Sensor, POEGroup, Category)
from nav.models.msgmaint import MaintenanceTask
from nav.models.arnold import Identity
from nav.models.service import Service
from nav.models.profiles import Account
from nav.models.event import AlertHistory
from nav.ipdevpoll.config import get_job_descriptions
from nav.util import is_valid_ip
from nav.web.ipdevinfo.utils import create_combined_urls
from nav.web.utils import create_title, SubListView
from nav.metrics.graphs import Graph

from nav.web.ipdevinfo.forms import (SearchForm, ActivityIntervalForm,
                                     SensorRangesForm)
from nav.web.ipdevinfo.context_processors import search_form_processor
from nav.web.ipdevinfo import utils
from .host_information import get_host_info

NAVPATH = [('Home', '/'), ('IP Device Info', '/ipdevinfo')]
COUNTER_TYPES = ('Octets', 'UcastPkts', 'Errors', 'Discards',
                 'MulticastPkts', 'BroadcastPkts')


_logger = logging.getLogger('nav.web.ipdevinfo')


def find_netboxes(errors, query):
    """Find netboxes based on query parameter

    :param errors: list of errors
    :param query: form input
    :return: querylist
    """
    ip = is_valid_ip(query)
    netboxes = None
    if ip:
        netboxes = Netbox.objects.filter(ip=ip)
    elif is_valid_hostname(query):
        # Check perfect match first
        sysname_filter = Q(sysname=query)
        if settings.DOMAIN_SUFFIX is not None:
            sysname_filter |= Q(sysname='%s%s' %
                                (query, settings.DOMAIN_SUFFIX))
        netboxes = Netbox.objects.filter(sysname_filter)
        if len(netboxes) != 1:
            # No exact match, search for matches in substrings
            netboxes = Netbox.objects.filter(sysname__icontains=query)
    else:
        errors.append('The query does not seem to be a valid IP address'
                      ' (v4 or v6) or a hostname.')

    return netboxes


def search(request):
    """Search for an IP device"""

    titles = NAVPATH
    errors = []
    netboxes = None
    query = None

    if 'query' in request.GET:
        search_form = SearchForm(request.GET)
        if search_form.is_valid():
            # Preprocess query string
            query = search_form.cleaned_data['query'].strip().lower()
            titles = titles + [("Search for %s" % query,)]
            netboxes = find_netboxes(errors, query)

            # If only one hit, redirect to details view
            if netboxes and len(netboxes) == 1:
                return ipdev_details(request, name=netboxes[0].sysname)
    else:
        search_form = SearchForm()

    return render_to_response('ipdevinfo/search.html',
                              {'errors': errors, 'netboxes': netboxes,
                               'navpath': NAVPATH, 'query': query,
                               'title': create_title(titles),
                               'search_form': search_form},
                              context_instance=RequestContext(
                                  request, processors=[search_form_processor]))


def is_valid_hostname(hostname):
    """Check if hostname is valid"""
    return re.match(r'^[a-z0-9-]+(\.[a-z0-9-]+)*$', hostname) is not None


def ipdev_details(request, name=None, addr=None, netbox_id=None):
    """Show detailed view of one IP device"""

    if netbox_id:
        netbox = get_object_or_404(Netbox, id=netbox_id)
        return HttpResponseRedirect(netbox.get_absolute_url())

    def get_netbox(name=None, addr=None):
        """Lookup IP device in NAV by either hostname or IP address.

        :rtype: nav.models.manage.Netbox

        """
        # Prefetch related objects as to reduce number of database queries
        netboxes = Netbox.objects.select_related()
        netbox = None

        if name:
            try:
                if is_valid_ip(name):
                    netbox = netboxes.get(Q(sysname=name) | Q(ip=name))
                else:
                    netbox = netboxes.get(sysname=name)
            except Netbox.DoesNotExist:
                pass
        elif addr:
            try:
                netbox = netboxes.get(ip=addr)
            except Netbox.DoesNotExist:
                pass
        if not netbox:
            host_information = get_host_info(name or addr)
            for address in host_information['addresses']:
                if 'name' in address:
                    try:
                        netbox = netboxes.get(sysname=address['name'])
                        break  # Exit loop at first match
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
        queryset = netbox.alerthistory_set.filter(
            filter_stateful | filter_stateless
            ).order_by('-start_time')
        count = queryset.count()
        raw_alerts = queryset[:max_num_alerts]

        alerts = []
        has_unresolved_alerts = False
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

            if not has_unresolved_alerts and alert.is_open():
                has_unresolved_alerts = True

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
            'has_unresolved_alerts': has_unresolved_alerts
        }

    def get_prefix_info(addr):
        """Return prefix based on address"""
        ipaddr = is_valid_ip(addr)
        if ipaddr:
            prefixes = Prefix.objects.select_related().extra(
                select={"mask_size": "masklen(netaddr)"},
                where=["%s << netaddr AND nettype <> 'scope'"],
                order_by=["-mask_size"], params=[ipaddr])[0:1]
            if prefixes:
                return prefixes[0]
        return None

    def get_arp_info(addr):
        """Return arp based on address"""
        ipaddr = is_valid_ip(addr)
        if ipaddr:
            arp_info = Arp.objects.extra(
                where=["ip = %s"],
                params=[ipaddr]).order_by('-end_time', '-start_time')[0:1]
            if arp_info:
                return arp_info[0]
        return None

    def get_cam_info(mac):
        """Return cam objects based on mac address"""
        cam_info = Cam.objects.filter(mac=mac).order_by('-end_time',
                                                        '-start_time')[0:1]
        return cam_info[0] if cam_info else None

    # Get data needed by the template
    addr = is_valid_ip(addr)
    host_info = None
    netbox = get_netbox(name=name, addr=addr)

    # Assign default values to variables
    no_netbox = {
        'prefix': None,
        'arp': None,
        'cam': None,
        'dt_max': dt.datetime.max,
        'days_since_active': 7,
    }
    alert_info = None
    job_descriptions = None
    system_metrics = netbox_availability = []
    sensor_metrics = []

    graphite_error = False
    # If addr or host not a netbox it is not monitored by NAV
    if netbox is None:
        host_info = get_host_info(name or addr)
        if not addr and len(host_info['addresses']) > 0:
            # Picks the first address in array if addr not specified
            addr = host_info['addresses'][0]['addr']

        no_netbox['prefix'] = get_prefix_info(addr)
        netboxgroups = None
        navpath = NAVPATH + [(host_info['host'], '')]

        if no_netbox['prefix']:
            no_netbox['arp'] = get_arp_info(addr)
            if no_netbox['arp']:
                no_netbox['cam'] = get_cam_info(no_netbox['arp'].mac)
                if no_netbox['arp'].end_time < dt.datetime.max:
                    no_netbox['days_since_active'] = \
                        (dt.datetime.now() - no_netbox['arp'].end_time).days

    else:
        alert_info = get_recent_alerts(netbox)
        netboxgroups = netbox.netboxcategory_set.all()
        navpath = NAVPATH + [(netbox.sysname, '')]
        job_descriptions = get_job_descriptions()

        try:
            system_metrics = netbox.get_system_metrics()
            for metric in system_metrics:
                metric['graphite_data_url'] = Graph(
                    magic_targets=[metric['id']], format='json')
        except GraphiteUnreachableError:
            graphite_error = True

        try:
            netbox_availability = netbox.get_availability()
        except GraphiteUnreachableError:
            graphite_error = True

        for sensor in netbox.sensor_set.all():
            metric_id = sensor.get_metric_name()
            metric = {
                'id': metric_id,
                'sensor': sensor,
                'graphite_data_url': Graph(
                    magic_targets=[metric_id], format='json'),
            }
            sensor_metrics.append(metric)
        find_rules(sensor_metrics)
    # Display info about current and scheduled maintenance tasks
    # related to this device
    current_tasks = MaintenanceTask.objects.current()
    future_tasks = MaintenanceTask.objects.future()
    relevant_current_tasks = []
    relevant_future_tasks = []
    for task in current_tasks:
        if netbox in task.get_event_subjects():
            relevant_current_tasks.append(task)

    for task in future_tasks:
        if netbox in task.get_event_subjects():
            relevant_future_tasks.append(task)

    interfaces = netbox.interface_set.order_by('ifindex') if netbox else []
    for interface in interfaces:
        interface.combined_data_urls = create_combined_urls(
            interface, COUNTER_TYPES)

    # Only display services tab for certain instances
    display_services_tab = netbox and (
        netbox.category.is_srv() or netbox.service_set.count())

    return render_to_response(
        'ipdevinfo/ipdev-details.html',
        {
            'host_info': host_info,
            'netbox': netbox,
            'interfaces': interfaces,
            'counter_types': COUNTER_TYPES,
            'heading': navpath[-1][0],
            'alert_info': alert_info,
            'no_netbox': no_netbox,
            'netboxgroups': netboxgroups,
            'job_descriptions': job_descriptions,
            'navpath': navpath,
            'title': create_title(navpath),
            'system_metrics': system_metrics,
            'netbox_availability': netbox_availability,
            'graphite_error': graphite_error,
            'current_maintenance_tasks': relevant_current_tasks,
            'future_maintenance_tasks': relevant_future_tasks,
            'sensor_metrics': sensor_metrics,
            'display_services_tab': display_services_tab
        },
        context_instance=RequestContext(request,
                                        processors=[search_form_processor]))


def get_port_view(request, netbox_sysname, perspective):
    """Returns a html fragment with all modules and ports on the netbox.

    Arguments:
    netbox_sysname -- ...
    perspective -- decides what kind of ports are included.
    """

    netbox = get_object_or_404(Netbox, sysname=netbox_sysname)

    # Get port activity search interval from form
    activity_interval = 30
    activity_interval_form = None
    if perspective == 'swportactive':
        if 'interval' in request.GET:
            activity_interval_form = ActivityIntervalForm(request.GET)
            if activity_interval_form.is_valid():
                activity_interval = activity_interval_form.cleaned_data[
                    'interval']
        else:
            activity_interval_form = ActivityIntervalForm(
                initial={'interval': activity_interval})

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

    # Min length of ifname for it to be shortened
    ifname_too_long = 12

    return render_to_response(
        'ipdevinfo/modules.html',
        {
            'netbox': netbox,
            'port_view': port_view,
            'ifname_too_long': ifname_too_long,
            'activity_interval_form': activity_interval_form
        },
        context_instance=RequestContext(request))


def module_details(request, netbox_sysname, module_name):
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

    module = get_object_or_404(Module.objects.select_related(),
                               netbox__sysname=netbox_sysname, name=module_name)

    swportstatus_view = get_module_view(module, 'swportstatus')
    swportactive_view = get_module_view(
        module, 'swportactive', activity_interval)
    gwportstatus_view = get_module_view(module, 'gwportstatus')

    navpath = NAVPATH + [
        (netbox_sysname,
         reverse('ipdevinfo-details-by-name',
                 kwargs={'name': netbox_sysname})),
        ('Module Details',)]

    return render_to_response(
        'ipdevinfo/module-details.html',
        {
            'module': module,
            'swportstatus_view': swportstatus_view,
            'swportactive_view': swportactive_view,
            'gwportstatus_view': gwportstatus_view,
            'activity_interval_form': activity_interval_form,
            'activity_interval': activity_interval,
            'navpath': navpath,
            'heading': navpath[-1][0],
            'title': create_title(navpath)
        },
        context_instance=RequestContext(
            request, processors=[search_form_processor]))


def poegroup_details(request, netbox_sysname, grpindex):
    """Show detailed view of one IP device power over ethernet group"""

    poegroup = get_object_or_404(POEGroup.objects.select_related(),
                                 netbox__sysname=netbox_sysname, index=grpindex)

    navpath = NAVPATH + [
        (netbox_sysname,
         reverse('ipdevinfo-details-by-name',
                 kwargs={'name': netbox_sysname})),
        ('PoE Details for ' + poegroup.name,)]

    return render_to_response(
        'ipdevinfo/poegroup-details.html',
        {
            'poegroup': poegroup,
            'navpath': navpath,
            'heading': navpath[-1][0],
            'title': create_title(navpath),
        },
        context_instance=RequestContext(
            request, processors=[search_form_processor]))


def port_details(request, netbox_sysname, port_type=None, port_id=None,
                 port_name=None):
    """Show detailed view of one IP device port"""

    if not (port_id or port_name):
        return Http404

    ports = Interface.objects.select_related()

    if port_id is not None:
        port = get_object_or_404(ports, id=port_id)
    elif port_name is not None:
        try:
            port = ports.get(netbox__sysname=netbox_sysname, ifname=port_name)
        except Interface.DoesNotExist:
            port = get_object_or_404(ports, netbox__sysname=netbox_sysname,
                                     ifdescr=port_name)

    navpath = NAVPATH + [
        (netbox_sysname,
         reverse('ipdevinfo-details-by-name',
                 kwargs={'name': netbox_sysname})), ('Port Details',)]
    heading = title = 'Port details: ' + six.text_type(port)

    try:
        port_metrics = port.get_port_metrics()
        graphite_error = False
    except GraphiteUnreachableError:
        port_metrics = []
        graphite_error = True

    sensor_metrics = []
    for sensor in port.sensor_set.all():
        metric_id = sensor.get_metric_name()
        metric = {
            'id': metric_id,
            'sensor': sensor,
            'graphite_data_url': Graph(
                magic_targets=[metric_id], format='json'),
        }
        sensor_metrics.append(metric)
    find_rules(sensor_metrics)
    # If interface is detained in Arnold, this should be visible on the
    # port details view
    try:
        detention = port.identity_set.get(
            status__in=['quarantined', 'disabled'])
    except Identity.DoesNotExist:
        detention = None

    # Add urls to Graphite to the relevant objects
    port.combined_data_urls = create_combined_urls(port, COUNTER_TYPES)
    for metric in port_metrics:
        metric['graphite_data_url'] = Graph(
            magic_targets=[metric['id']], format='json')

    return render_to_response(
        'ipdevinfo/port-details.html',
        {
            'port_type': port_type,
            'port': port,
            'navpath': navpath,
            'heading': heading,
            'title': title,
            'port_metrics': port_metrics,
            'graphite_error': graphite_error,
            'detention': detention,
            'sensor_metrics': sensor_metrics,
            'alert_info': get_recent_alerts_interface(port)
        },
        context_instance=RequestContext(
            request, processors=[search_form_processor]))


def get_recent_alerts_interface(interface, days_back=7):
    """Returns the most recent linkState events for this interface"""
    lowest_end_time = dt.datetime.now() - dt.timedelta(days=days_back)
    alerts = AlertHistory.objects.filter(
        event_type='linkState',
        subid=interface.pk,
        end_time__gt=lowest_end_time)
    for alert in alerts:
        try:
            message = alert.messages.filter(type='sms')[0].message
        except IndexError:
            message = None
        alert.message = message

    return {
        'alerts': alerts,
        'count': alerts.count(),
        'days_back': days_back,
        'has_unresolved_alerts': any(a.is_open() for a in alerts),
    }


def port_counter_graph(request, interfaceid, kind='Octets'):
    """Creates an url to Graphite for rendering a graph as an image

    Redirects to the created url if successful
    """
    if kind not in ('Octets', 'Errors', 'UcastPkts', 'Discards',
                    'MulticastPkts', 'BroadcastPkts'):
        raise Http404

    timeframe = request.GET.get('timeframe', 'day')
    port = get_object_or_404(Interface, id=interfaceid)
    url = utils.get_interface_counter_graph_url(port, timeframe, kind,
                                                expect='png')

    if url:
        return redirect(url)
    else:
        return HttpResponse(status=500)


def service_list(request, handler=None):
    """List services with given handler or any handler"""

    page = request.GET.get('page', '1')

    services = Service.objects.select_related('netbox').order_by(
        'netbox__sysname', 'handler')
    if handler:
        services = services.filter(handler=handler)

    handler_list = Service.objects.values('handler').distinct()
    navpath = NAVPATH + [('Service List',)]

    # Pass on to generic view
    return SubListView.as_view(
        queryset=services,
        paginate_by=100,
        template_name='ipdevinfo/service-list.html',
        allow_empty=True,
        extra_context={
            'show_ipdev_info': True,
            'handler_list': handler_list,
            'handler': handler,
            'title': create_title(navpath),
            'navpath': navpath,
            'heading': navpath[-1][0],
            'services': services,
            'page': page,
            'context_processors': [search_form_processor],
            'template_object_name': 'service'
        },)(request)


def service_matrix(request):
    """Show service status in a matrix with one IP Device per row and one
    service handler per column"""

    handler_list = [h['handler']
                    for h in Service.objects.values('handler').distinct()]

    matrix_dict = {}
    for service in Service.objects.select_related('netbox'):
        if service.netbox.id not in matrix_dict:
            matrix_dict[service.netbox.id] = {
                'sysname': service.netbox.sysname,
                'netbox': service.netbox,
                'services': [None for _ in handler_list],
            }
        index = handler_list.index(service.handler)
        matrix_dict[service.netbox.id]['services'][index] = service

    matrix = matrix_dict.values()
    navpath = NAVPATH + [('Service Matrix',)]

    return render_to_response(
        'ipdevinfo/service-matrix.html',
        {
            'handler_list': handler_list,
            'matrix': matrix,
            'title': create_title(navpath),
            'navpath': navpath,
            'heading': navpath[-1][0]
        },
        context_instance=RequestContext(
            request, processors=[search_form_processor]))


def render_affected(request, netboxid):
    """Controller for the affected tab in ipdevinfo"""
    netbox = get_object_or_404(Netbox, pk=netboxid)
    netboxes = utils.find_children(netbox)

    affected = utils.sort_by_netbox(
        utils.find_affected_but_not_down(netbox, netboxes))
    unreachable = utils.sort_by_netbox(list(set(netboxes) - set(affected)))

    organizations = utils.find_organizations(unreachable)
    contacts = utils.filter_email(organizations)
    services = Service.objects.filter(netbox__in=unreachable).order_by('netbox')
    affected_hosts = utils.get_affected_host_count(unreachable)

    return render_to_response(
        'ipdevinfo/frag-affected.html', {
            'unreachable': unreachable,
            'affected': affected,
            'services': services,
            'organizations': organizations,
            'contacts': contacts,
            'affected_hosts': affected_hosts
        },
        context_instance=RequestContext(request))


def render_host_info(request, identifier):
    """Controller for getting host info"""
    return render(request, 'ipdevinfo/frag-hostinfo.html', {
        'host_info': get_host_info(identifier)
    })


def unrecognized_neighbors(request, netboxid):
    """Render unrecognized neighbors tab"""
    netbox = get_object_or_404(Netbox, pk=netboxid)
    return render(request, 'ipdevinfo/frag-neighbors.html',
                  {'netbox': netbox, 'categories': Category.objects.all()})


def sensor_details(request, identifier):
    """Controller for getting sensor info"""
    sensor = get_object_or_404(Sensor, pk=identifier)

    if request.method == 'POST':
        form = SensorRangesForm(request.POST)
        if form.is_valid():
            sensor.display_minimum_user = form.cleaned_data['minimum']
            sensor.display_maximum_user = form.cleaned_data['maximum']
            sensor.save()
            return redirect(request.path)

    netbox_sysname = sensor.netbox.sysname

    navpath = NAVPATH + [
        (netbox_sysname,
         reverse('ipdevinfo-details-by-name',
                 kwargs={'name': netbox_sysname})), ('Sensor Details',)]
    heading = title = 'Sensor details: ' + six.text_type(sensor)

    metric = dict(id=sensor.get_metric_name())
    find_rules([metric])

    form = SensorRangesForm(initial={
        'minimum': sensor.get_display_range()[0],
        'maximum': sensor.get_display_range()[1],
    })
    return render(request, 'ipdevinfo/sensor-details.html', {
        'sensor': sensor,
        'navpath': navpath,
        'heading': heading,
        'title': title,
        'metric': metric,
        'form': form,
        'graphite_data_url': Graph(magic_targets=[sensor.get_metric_name()],
                                   format='json')
    })


def save_port_layout_pref(request):
    """Save the ipdevinfo port layout preference"""
    account = request.account
    key = Account.PREFERENCE_KEY_IPDEVINFO_PORT_LAYOUT
    account.preferences[key] = request.GET.get('layout')
    account.save()

    # To use hashes we need to do append it after finding the url
    url = reverse('ipdevinfo-details-by-id',
                  kwargs={'netbox_id': request.GET.get('netboxid')})
    return redirect("{}#!ports".format(url))
