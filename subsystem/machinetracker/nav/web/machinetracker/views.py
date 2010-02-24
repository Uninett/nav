# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#

from IPy import IP
from datetime import date, datetime, timedelta

from django.template import RequestContext
from django.shortcuts import render_to_response
from django.utils.datastructures import SortedDict

from nav.models.manage import Arp, Cam

from nav.web.machinetracker import forms
from nav.web.machinetracker.utils import hostname, track_mac, min_max_mac

NAVBAR = [('Home', '/'), ('Machinetracker', None)]
IP_TITLE = 'NAV - Machinetracker - IP Search'
MAC_TITLE = 'NAV - Machinetracker - MAC Search'
SWP_TITLE = 'NAV - Machinetracker - Switch Search'
IP_DEFAULTS = {'title': IP_TITLE, 'navpath': NAVBAR, 'active': {'ip': True}}
MAC_DEFAULTS = {'title': MAC_TITLE, 'navpath': NAVBAR, 'active': {'mac': True}}
SWP_DEFAULTS = {'title': SWP_TITLE, 'navpath': NAVBAR, 'active': {'swp': True}}


def ip_search(request):
    form = forms.IpTrackerForm(request.GET)
    info_dict = {}
    if not form.is_valid():
        info_dict = {'form': forms.IpTrackerForm()}
    else:
        from_ip_string = form.cleaned_data['from_ip']
        to_ip_string = form.cleaned_data['to_ip']
        dns = form.cleaned_data['dns']
        active = form.cleaned_data['active']
        inactive = form.cleaned_data['inactive']
        days = form.cleaned_data['days']

        from_ip = IP(from_ip_string)
        if to_ip_string:
            to_ip = IP(to_ip_string)
        else:
            to_ip = from_ip

        if 6 in (from_ip.version(), to_ip.version()):
            inactive = False

        from_time = date.today() - timedelta(days=days)

        ip_result = SortedDict()
        if active:
            result = Arp.objects.filter(
                end_time__gt=from_time,
            ).extra(
                where=['ip BETWEEN %s and %s'],
                params=[unicode(from_ip), unicode(to_ip)],
            ).order_by('ip', 'mac', '-start_time').values(
                'ip', 'mac', 'start_time', 'end_time'
            )

            for row in result:
                ip = IP(row['ip'])
                if ip not in ip_result:
                    ip_result[ip] = []
                ip_result[ip].append(row)

        ip_range = []
        if inactive:
            ip_range = [IP(ip) for ip in range(from_ip.int(), to_ip.int() + 1)]
        else:
            ip_range = [key for key in ip_result]

        tracker = SortedDict()
        for ip_key in ip_range:
            if ip_key in ip_result:
                rows = ip_result[ip_key]
                for row in rows:
                    if row['end_time'] > datetime.now():
                        row['still_active'] = "Still active"
                    if dns:
                        row['dns_lookup'] = hostname(row['ip']) or ""
                    if (row['ip'], row['mac']) not in tracker:
                        tracker[(row['ip'], row['mac'])] = []
                    tracker[(row['ip'], row['mac'])].append(row)
            elif inactive:
                ip = unicode(ip_key)
                row = {'ip': ip}
                if dns:
                    row['dns_lookup'] = hostname(ip) or ""
                tracker[(ip, "")] = [row]

        info_dict = {
            'form': forms.IpTrackerForm(initial=form.cleaned_data),
            'form_data': form.cleaned_data,
            'ip_tracker': tracker,
        }

    info_dict.update(IP_DEFAULTS)
    return render_to_response(
        'machinetracker/ip_search.html',
        info_dict,
        RequestContext(request)
    )

def mac_search(request):
    form = forms.MacTrackerForm(request.GET)
    info_dict = {}
    if not form.is_valid():
        info_dict['form'] = forms.MacTrackerForm()
    else:
        mac = form.cleaned_data['mac']
        days = form.cleaned_data['days']
        dns = form.cleaned_data['dns']
        from_time = date.today() - timedelta(days=days)

        mac_min, mac_max = min_max_mac(mac)

        cam_result = Cam.objects.select_related('netbox').filter(
            end_time__gt=from_time
        ).extra(
            where=['mac BETWEEN %s and %s'],
            params=[mac_min, mac_max]
        ).order_by('mac', 'sysname', 'module', 'port', '-start_time').values(
            'sysname', 'module', 'port', 'start_time', 'end_time', 'mac', 'netbox__sysname'
        )

        arp_result = Arp.objects.filter(
            end_time__gt=from_time
        ).extra(
            where=['mac BETWEEN %s and %s'],
            params=[mac_min, mac_max]
        ).order_by('mac', 'ip', '-start_time').values(
            'ip', 'mac', 'start_time', 'end_time'
        )

        mac_tracker = track_mac(('mac', 'sysname', 'module', 'port'), cam_result, dns=False)
        ip_tracker = track_mac(('ip', 'mac'), arp_result, dns)

        info_dict = {
            'form': forms.MacTrackerForm(initial=form.cleaned_data),
            'form_data': form.cleaned_data,
            'mac_tracker': mac_tracker,
            'ip_tracker': ip_tracker,
        }

    info_dict.update(MAC_DEFAULTS)
    return render_to_response(
        'machinetracker/mac_search.html',
        info_dict,
        RequestContext(request)
    )

def switch_search(request):
    form = forms.SwitchTrackerForm(request.GET)
    info_dict = {}
    if not form.is_valid():
        info_dict['form'] = forms.SwitchTrackerForm()
    else:
        switch = form.cleaned_data['switch']
        module = form.cleaned_data.get('module')
        port_interface = form.cleaned_data.get('port')
        days = form.cleaned_data['days']
        from_time = date.today() - timedelta(days=days)

        criteria = {
            'sysname__istartswith': switch,
            'end_time__gt': from_time,
        }
        if module:
            criteria['module'] = module
        if port_interface:
            criteria['port'] = port_interface

        cam_result = Cam.objects.filter(
            **criteria
        ).order_by('sysname', 'module', 'mac', '-start_time').values(
            'sysname', 'module', 'port', 'start_time', 'end_time', 'mac'
        )
        swp_tracker = track_mac(('mac', 'sysname', 'module', 'port'), cam_result, dns=False)

        info_dict = {
            'form': forms.SwitchTrackerForm(initial=form.cleaned_data),
            'form_data': form.cleaned_data,
            'mac_tracker': swp_tracker,
        }

    info_dict.update(SWP_DEFAULTS)
    return render_to_response(
        'machinetracker/switch_search.html',
        info_dict,
        RequestContext(request)
    )
