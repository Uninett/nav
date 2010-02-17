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

def ip(request):
    return render_to_response(
        'machinetracker/ip_search.html',
        {
            'active': {'ip': True},
            'form': forms.IpTrackerForm(),
        },
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

        result = Arp.objects.filter(
            end_time__gt=from_time,
        ).extra(
            where=['ip BETWEEN %s and %s'],
            params=[unicode(from_ip), unicode(to_ip)],
        ).order_by('ip', 'mac', '-start_time')

        tracker = SortedDict()
        for row in result:
            ip = row.ip
            mac = row.mac
            if row.end_time > datetime.now():
                row.still_active = "Still active"
            if (ip, mac) in tracker:
                if dns:
                    row.dns_lookup = "--"
                row.ip = ""
                row.mac = ""
                tracker[(ip, mac)].append(row)
            else:
                if dns:
                    row.dns_lookup = hostname(row.ip)
                tracker[(ip, mac)] = [row]

    return render_to_response(
        'machinetracker/ip_search.html',
        {
            'active': {'ip': True},
            'form': form,
            'tracker': tracker,
        },
        RequestContext(request)
    )

def mac(request):
    pass

def switch(request):
    pass
