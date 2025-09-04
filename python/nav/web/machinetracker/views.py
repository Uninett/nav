#
# Copyright (C) 2009, 2011-2013 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Machine Tracker view functions"""

from datetime import date, timedelta
from collections import OrderedDict
import logging

from IPy import IP

from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect

from nav.django.utils import reverse_with_query
from nav.models.manage import Arp, Cam, Netbios, Prefix

from nav import asyncdns

from nav.web.machinetracker import forms
from nav.web.machinetracker.utils import ip_dict, UplinkTracker, InterfaceTracker
from nav.web.machinetracker.utils import process_ip_row, track_mac
from nav.web.machinetracker.utils import (
    min_max_mac,
    ProcessInput,
    normalize_ip_to_string,
    get_last_job_log_from_netboxes,
    get_vendor_query,
)
from nav.web.modals import render_modal

NAVBAR = [('Home', '/'), ('Machinetracker', None)]
IP_TITLE = 'NAV - Machinetracker - IP Search'
MAC_TITLE = 'NAV - Machinetracker - MAC Search'
SWP_TITLE = 'NAV - Machinetracker - Switch Search'
NBT_TITLE = 'NAV - Machinetracker - NetBIOS Search'
IP_DEFAULTS = {'title': IP_TITLE, 'navpath': NAVBAR, 'active': {'ip': True}}
MAC_DEFAULTS = {'title': MAC_TITLE, 'navpath': NAVBAR, 'active': {'mac': True}}
SWP_DEFAULTS = {'title': SWP_TITLE, 'navpath': NAVBAR, 'active': {'swp': True}}
NBT_DEFAULTS = {'title': NBT_TITLE, 'navpath': NAVBAR, 'active': {'netbios': True}}
VALID_HELP_TAB_NAMES = ['ip', 'mac', 'switch', 'netbios']

ADDRESS_LIMIT = 4096  # Value for when inactive gets disabled

_logger = logging.getLogger(__name__)


def ip_prefix_search(request, prefix_id, active=False):
    """View to redirect to a proper machine tracker IP range search based on a
    NAV-internal prefix ID.

    """
    prefix = get_object_or_404(Prefix, id=prefix_id)

    kwargs = {"ip_range": prefix.net_address}
    if active:
        kwargs["days"] = -1
    return HttpResponseRedirect(reverse_with_query("machinetracker-ip", **kwargs))


def ip_search(request):
    """Controller for ip search"""
    if 'ip_range' in request.GET:
        return ip_do_search(request)

    info_dict = {'form': forms.IpTrackerForm()}
    info_dict.update(IP_DEFAULTS)
    return render(request, 'machinetracker/ip_search.html', info_dict)


def ip_do_search(request):
    """Search CAM and ARP based on IP range"""
    querydict = ProcessInput(request.GET).ip()
    form = forms.IpTrackerForm(querydict)
    tracker = None
    form_data = {}
    row_count = 0
    from_ip = None
    to_ip = None

    if form.is_valid():
        form_data = form.cleaned_data
        ip_range = form.cleaned_data['ip_range']
        from_ip, to_ip = (ip_range[0], ip_range[-1])
        period_filter = form.cleaned_data['period_filter']
        active = inactive = False

        if period_filter in ['active', 'both']:
            active = True
        if period_filter in ['inactive', 'both']:
            inactive = True

        if (to_ip.int() - from_ip.int()) > ADDRESS_LIMIT:
            inactive = False

        ip_result = get_result(
            form.cleaned_data['days'],
            from_ip,
            to_ip,
            form.cleaned_data['netbios'],
            form.cleaned_data['vendor'],
        )
        ip_range = create_ip_range(inactive, from_ip, to_ip, ip_result)
        tracker = create_tracker(
            active, form.cleaned_data['dns'], inactive, ip_range, ip_result
        )
        row_count = sum(len(mac_ip_pair) for mac_ip_pair in tracker.values())

    info_dict = {
        'form': form,
        'form_data': form_data,
        'ip_tracker': tracker,
        'ip_tracker_count': row_count,
        'subnet_start': str(from_ip),
        'subnet_end': str(to_ip),
        'colspan': find_colspan('ip', form),
    }
    info_dict.update(IP_DEFAULTS)

    return render(request, 'machinetracker/ip_search.html', info_dict)


def get_result(days, from_ip, to_ip, get_netbios=False, get_vendor=False):
    """Gets and formats search result"""
    records = get_arp_records(days, from_ip, to_ip, get_netbios, get_vendor)
    flag_as_fishy(records)
    ip_result = ip_dict(records)
    return ip_result


def get_arp_records(days, from_ip, to_ip, get_netbios=False, get_vendor=False):
    """Gets the result from ARP based on input parameters"""
    from_time = date.today() - timedelta(days=days)
    extra_args = {
        'where': ['ip BETWEEN %s and %s'],
        'params': [str(from_ip), str(to_ip)],
    }
    if get_netbios:
        extra_args['select'] = {'netbiosname': get_netbios_query()}

    result = (
        Arp.objects.filter(end_time__gt=from_time)
        .extra(**extra_args)
        .order_by('ip', 'mac', '-start_time')
    )

    if get_vendor:
        result = result.extra(select={'vendor': get_vendor_query()})

    return result


def flag_as_fishy(records):
    """Flag rows overdue as fishy"""
    netboxes = get_last_job_log_from_netboxes(records, 'ip2mac')
    for row in records:
        if row.netbox in netboxes:
            job_log = netboxes[row.netbox]
            row.fishy = job_log if job_log and job_log.is_overdue() else None


def create_ip_range(inactive, from_ip, to_ip, ip_result):
    """Creates the range of ip objects to use when creating tracker"""
    if inactive:
        ip_range = [IP(ip) for ip in range(from_ip.int(), to_ip.int() + 1)]
    else:
        ip_range = [key for key in ip_result]
    return ip_range


def create_tracker(active, dns, inactive, ip_range, ip_result):
    """Creates a result tracker based on form data"""
    dns_lookups = None
    if dns:
        ips_to_lookup = {str(ip) for ip in ip_range}
        _logger.debug(
            "create_tracker: looking up PTR records for %d addresses)",
            len(ips_to_lookup),
        )
        dns_lookups = asyncdns.reverse_lookup(ips_to_lookup)
        _logger.debug("create_tracker: PTR lookup done")

    tracker = OrderedDict()
    for ip_key in ip_range:
        if active and ip_key in ip_result:
            create_active_row(tracker, dns, dns_lookups, ip_key, ip_result)
        elif inactive and ip_key not in ip_result:
            create_inactive_row(tracker, dns, dns_lookups, ip_key)
    return tracker


def create_active_row(tracker, dns, dns_lookups, ip_key, ip_result):
    """Creates a tracker tuple where the result is active"""
    ip = str(ip_key)
    rows = ip_result[ip_key]
    for row in rows:
        row = process_ip_row(row, dns=False)
        if dns:
            if isinstance(dns_lookups[ip], Exception) or not dns_lookups[ip]:
                row.dns_lookup = ""
            else:
                row.dns_lookup = dns_lookups[ip][0]
        row.ip_int_value = normalize_ip_to_string(row.ip)
        if (row.ip, row.mac) not in tracker:
            tracker[(row.ip, row.mac)] = []
        tracker[(row.ip, row.mac)].append(row)


def create_inactive_row(tracker, dns, dns_lookups, ip_key):
    """Creates a tracker tuple where the result is inactive"""
    ip = str(ip_key)
    row = {'ip': ip, 'ip_int_value': normalize_ip_to_string(ip)}
    if dns:
        if dns_lookups[ip] and not isinstance(dns_lookups[ip], Exception):
            row['dns_lookup'] = dns_lookups[ip][0]
        else:
            row['dns_lookup'] = ""
    tracker[(ip, "")] = [row]


def find_colspan(view, form):
    """Find correct colspan for the view"""
    defaults = {'ip': 5, 'netbios': 7, 'mac': 8}
    colspan = defaults[view]
    netbios = form.data.get('netbios', False)
    dns = form.data.get('dns', False)
    source = form.data.get('source', False)
    vendor = dns = form.data.get('vendor', False)

    if netbios:
        colspan += 1
    if dns:
        colspan += 1
    if source:
        colspan += 1
    if vendor:
        colspan += 1
    return colspan


def mac_search(request):
    """Controller for doing a search based on a mac address"""
    if 'mac' in request.GET:
        return mac_do_search(request)
    info_dict = {'form': forms.MacTrackerForm()}
    info_dict.update(MAC_DEFAULTS)
    return render(request, 'machinetracker/mac_search.html', info_dict)


def mac_do_search(request):
    """Does a search based on a mac address"""
    querydict = ProcessInput(request.GET).mac()
    form = forms.MacTrackerForm(querydict)
    info_dict = {
        'form': form,
        'form_data': None,
        'mac_tracker': None,
        'ip_tracker': None,
        'mac_tracker_count': 0,
        'ip_tracker_count': 0,
        'disable_ip_context': True,
    }
    if form.is_valid():
        _logger.debug("mac_do_search: form is valid")
        mac = form.cleaned_data['mac']
        days = form.cleaned_data['days']
        dns = form.cleaned_data['dns']
        vendor = form.cleaned_data['vendor']
        from_time = date.today() - timedelta(days=days)

        mac_min, mac_max = min_max_mac(mac)

        cam_result = (
            Cam.objects.select_related('netbox')
            .filter(
                end_time__gt=from_time,
            )
            .extra(where=['mac BETWEEN %s and %s'], params=[mac_min, mac_max])
            .order_by('mac', 'sysname', 'module', 'port', '-start_time')
        )

        arp_result = (
            Arp.objects.select_related('netbox')
            .filter(end_time__gt=from_time, mac__range=(mac_min, mac_max))
            .order_by('mac', 'ip', '-start_time')
        )
        if form.cleaned_data['netbios']:
            arp_result = arp_result.extra(select={'netbiosname': get_netbios_query()})

        if vendor:
            cam_result = cam_result.extra(select={'vendor': get_vendor_query()})
            arp_result = arp_result.extra(select={'vendor': get_vendor_query()})

        # Get last ip2mac and topo jobs on netboxes
        netboxes_ip2mac = get_last_job_log_from_netboxes(arp_result, 'ip2mac')
        netboxes_topo = get_last_job_log_from_netboxes(cam_result, 'topo')

        # Flag rows overdue as fishy
        for row in arp_result:
            if row.netbox in netboxes_ip2mac:
                job_log = netboxes_ip2mac[row.netbox]
                fishy = job_log and job_log.is_overdue()
                row.fishy = job_log if fishy else None

        for row in cam_result:
            if row.netbox in netboxes_topo:
                job_log = netboxes_topo[row.netbox]
                fishy = job_log and job_log.is_overdue()
                row.fishy = job_log if fishy else None

        mac_count = len(cam_result)
        ip_count = len(arp_result)
        _logger.debug(
            "mac_do_search: processed %d cam rows and %d arp rows", mac_count, ip_count
        )
        mac_tracker = track_mac(
            ('mac', 'sysname', 'module', 'port'), cam_result, dns=False
        )
        _logger.debug("mac_do_search: track_mac finished")
        uplink_tracker = UplinkTracker(mac_min, mac_max, vendor=vendor)
        interface_tracker = InterfaceTracker(mac_min, mac_max, vendor=vendor)
        ip_tracker = track_mac(('ip', 'mac'), arp_result, dns)

        info_dict.update(
            {
                'form_data': form.cleaned_data,
                'mac_tracker': mac_tracker,
                'uplink_tracker': uplink_tracker,
                'interface_tracker': interface_tracker,
                'ip_tracker': ip_tracker,
                'mac_tracker_count': mac_count,
                'ip_tracker_count': ip_count,
                'ip_tracker_colspan': find_colspan('ip', form),
                'mac_tracker_colspan': find_colspan('mac', form),
            }
        )

    info_dict.update(MAC_DEFAULTS)
    _logger.debug("mac_do_search: rendering")
    return render(request, 'machinetracker/mac_search.html', info_dict)


def switch_search(request):
    """Controller for switch search"""
    if 'switch' in request.GET:
        return switch_do_search(request)
    info_dict = {
        'form': forms.SwitchTrackerForm(),
    }
    info_dict.update(SWP_DEFAULTS)
    return render(request, 'machinetracker/switch_search.html', info_dict)


def switch_do_search(request):
    """Does a search in cam and arp based on a switch"""
    querydict = ProcessInput(request.GET).swp()
    form = forms.SwitchTrackerForm(querydict)
    info_dict = {
        'form': form,
        'form_data': None,
        'mac_tracker': None,
        'mac_tracker_count': 0,
    }
    if form.is_valid():
        switch = form.cleaned_data['switch']
        module = form.cleaned_data.get('module')
        port_interface = form.cleaned_data.get('port')
        days = form.cleaned_data['days']
        from_time = date.today() - timedelta(days=days)
        criteria = {}

        if module:
            criteria['module'] = module

        # If port is specified, match on ifindex
        if port_interface:
            try:
                cam_with_ifindex = Cam.objects.filter(
                    Q(sysname__istartswith=switch)
                    | Q(netbox__sysname__istartswith=switch),
                    end_time__gt=from_time,
                    port=port_interface,
                    **criteria,
                ).values('ifindex')[0]
                criteria['ifindex'] = cam_with_ifindex['ifindex']
            except IndexError:
                criteria['port'] = port_interface

        cam_result = (
            Cam.objects.select_related('netbox')
            .filter(
                Q(sysname__istartswith=switch) | Q(netbox__sysname__istartswith=switch),
                end_time__gt=from_time,
                **criteria,
            )
            .order_by('sysname', 'module', 'mac', '-start_time')
        )

        if form.cleaned_data['vendor']:
            cam_result = cam_result.extra(select={'vendor': get_vendor_query()})

        # Get last topo jobs on netboxes
        netboxes_topo = get_last_job_log_from_netboxes(cam_result, 'topo')

        # Flag rows overdue as fishy
        for row in cam_result:
            if row.netbox in netboxes_topo:
                job_log = netboxes_topo[row.netbox]
                fishy = job_log and job_log.is_overdue()
                row.fishy = job_log if fishy else None

        swp_count = len(cam_result)
        swp_tracker = track_mac(
            ('mac', 'sysname', 'module', 'port'), cam_result, dns=False
        )

        info_dict.update(
            {
                'form_data': form.cleaned_data,
                'mac_tracker': swp_tracker,
                'mac_tracker_count': swp_count,
                'mac_tracker_colspan': find_colspan('mac', form),
            }
        )

    info_dict.update(SWP_DEFAULTS)
    return render(request, 'machinetracker/switch_search.html', info_dict)


def get_netbios_query(separator=', '):
    """Return a query that populates netbios names on an arp query

    Multiple netbiosnames are joined with separator to a single string.
    Populates only if the arp tuple overlaps netbios tuple regarding time.

    Ex:
    Arp.objects.filter(..).extra(select={'netbiosname': get_netbios_query()})

    """
    return (
        """SELECT array_to_string(array_agg(DISTINCT name),'%s')
              FROM netbios
              WHERE arp.ip=netbios.ip AND family(arp.ip) = 4
              AND (arp.start_time, arp.end_time)
                   OVERLAPS (netbios.start_time,
                             netbios.end_time)"""
        % separator
    )


# NetBIOS
def netbios_search(request):
    """Controller for displaying search for NETBIOS name"""
    if 'search' in request.GET:
        return netbios_do_search(request)
    info_dict = {'form': forms.NetbiosTrackerForm()}
    info_dict.update(NBT_DEFAULTS)
    return render(request, 'machinetracker/netbios_search.html', info_dict)


def netbios_do_search(request):
    """Handle a search for a NETBIOS name"""
    form = forms.NetbiosTrackerForm(ProcessInput(request.GET).netbios())
    info_dict = {
        'form': form,
        'form_data': None,
        'netbios_tracker': None,
        'netbios_tracker_count': 0,
    }

    if form.is_valid():
        searchstring = form.cleaned_data['search']
        days = form.cleaned_data['days']
        dns = form.cleaned_data['dns']
        from_time = date.today() - timedelta(days=days)

        filters = (
            Q(mac__istartswith=searchstring)
            | Q(ip__istartswith=searchstring)
            | Q(name__icontains=searchstring)
        )

        result = Netbios.objects.filter(filters, end_time__gt=from_time)
        result = result.order_by('name', 'mac', 'start_time')

        if form.cleaned_data['vendor']:
            result = result.extra(select={'vendor': get_vendor_query()})

        nbt_count = len(result)

        netbios_tracker = track_mac(
            ('ip', 'mac', 'name', 'server', 'username', 'start_time', 'end_time'),
            result,
            dns,
        )

        info_dict.update(
            {
                'form_data': form.cleaned_data,
                'netbios_tracker': netbios_tracker,
                'netbios_tracker_count': nbt_count,
                'colspan': find_colspan('netbios', form),
            }
        )

    info_dict.update(NBT_DEFAULTS)
    return render(request, 'machinetracker/netbios_search.html', info_dict)


def render_search_help_modal(request, tab_name):
    """Render the search help modal for the given tab name."""

    if tab_name not in VALID_HELP_TAB_NAMES:
        return HttpResponse(status=400)  # Bad Request

    template_name = f'machinetracker/_{tab_name}_search_help_modal.html'
    modal_id = f'{tab_name}-search-help'

    return render_modal(request, template_name, modal_id=modal_id, size="large")
