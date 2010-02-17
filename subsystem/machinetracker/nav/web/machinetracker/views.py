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

from nav.models.manage import Arp

from nav.web.machinetracker import forms
from nav.web.machinetracker.utils import hostname

NAVBAR = [('Home', '/'), ('Machinetracker', None)]
IP_TITLE = 'NAV - Machinetracker - IP Search'
MAC_TITLE = 'NAV - Machinetracker - MAC Search'
SWP_TITLE = 'NAV - Machinetracker - Switch Search'
IP_DEFAULTS = {'title': IP_TITLE, 'navpath': NAVBAR}
MAC_DEFAULTS = {'title': MAC_TITLE, 'navpath': NAVBAR}
SWP_DEFAULTS = {'title': SWP_TITLE, 'navpath': NAVBAR}


def ip(request):
    info_dict = {
        'active': {'ip': True},
        'form': forms.IpTrackerForm(),
    }
    info_dict.update(IP_DEFAULTS)
    return render_to_response(
        'machinetracker/ip_search.html',
        info_dict,
        RequestContext(request)
    )

def ip_search(request):
    form = forms.IpTrackerForm(request.GET)
    tracker = None
    if form.is_valid():
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

        from_time = date.today() - timedelta(days=7)

        ip_result = SortedDict()
        if active:
            result = Arp.objects.filter(
                end_time__gt=from_time,
            ).extra(
                where=['ip BETWEEN %s and %s'],
                params=[unicode(from_ip), unicode(to_ip)],
            ).order_by('ip', 'mac', '-start_time')

            for row in result:
                ip = IP(row.ip)
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
                    ip = row.ip
                    mac = row.mac
                    if row.end_time > datetime.now():
                        row.still_active = "Still active"
                    if (ip, mac) not in tracker:
                        if dns:
                            row.dns_lookup = hostname(row.ip) or ""
                        tracker[(ip, mac)] = [row]
                    else:
                        row.ip = ""
                        row.mac = ""
                        row.dns_lookup = "--"
                        tracker[(ip, mac)].append(row)
            elif inactive:
                ip = unicode(ip_key)
                row = {'ip': ip}
                if dns:
                    row['dns_lookup'] = hostname(ip) or ""
                tracker[(ip, "")] = [row]

    info_dict = {
        'active': {'ip': True},
        'form': form,
        'tracker': tracker,
    }
    info_dict.update(IP_DEFAULTS)
    return render_to_response(
        'machinetracker/ip_search.html',
        info_dict,
        RequestContext(request)
    )

def mac(request):
    pass

def switch(request):
    pass
