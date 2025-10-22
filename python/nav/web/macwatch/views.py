#
# Copyright (C) 2011 Uninett AS
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
"""macwatch view definitions"""

from django.http import HttpResponseRedirect
from django.shortcuts import render

from nav.web.auth.utils import get_account

from nav.web.macwatch.forms import MacWatchForm
from nav.web.macwatch.models import MacWatch


NAVBAR = [('Home', '/'), ('MacWatch', None)]
DEFAULT_VALUES = {'title': "MacWatch", 'navpath': NAVBAR}


def do_list(request, messages=None):
    account = get_account(request)
    macwatches = MacWatch.objects.all()
    info_dict = populate_info_dict(account, macwatches=macwatches, messages=messages)
    return render(request, 'macwatch/list_watches.html', info_dict)


def list_watch(request):
    """Render current macwatches and option to add new one."""
    return do_list(request)


def add_macwatch(request):
    """Display form for adding of mac address to watch."""

    account = get_account(request)
    if request.method == 'POST':
        macwatchform = MacWatchForm(request.POST)
        if macwatchform.is_valid():
            # Get user object
            m = MacWatch(
                mac=macwatchform.cleaned_data['macaddress'],
                userid=account,
                description=macwatchform.cleaned_data['description'],
            )
            if macwatchform.prefix_length:
                m.prefix_length = macwatchform.prefix_length
            m.save()
            return HttpResponseRedirect('/macwatch/')
        else:
            messages = ['Illegal input-data']
            info_dict = populate_info_dict(account, messages=messages)
            info_dict['form'] = macwatchform
            return render(request, 'macwatch/addmacwatch.html', info_dict)

    info_dict = populate_info_dict(account)
    macwatchform = MacWatchForm()
    info_dict['form'] = macwatchform
    return render(request, 'macwatch/addmacwatch.html', info_dict)


def delete_macwatch(request, macwatchid):
    """Delete tuple for mac address watch"""

    account = get_account(request)
    # Delete tuple based on url
    if macwatchid:
        # Captured args are always strings. Make it int.
        macwatchid = int(macwatchid)
        try:
            m = MacWatch.objects.get(id=macwatchid)
        except MacWatch.DoesNotExist as e:
            messages = [e]
            return do_list(request, messages)

        if request.method == 'POST':
            if request.POST['submit'] == 'Yes':
                try:
                    m.delete()
                    return HttpResponseRedirect('/macwatch/')
                except Exception as e:  # noqa: BLE001
                    messages = [e]
                    return do_list(request, messages)
            else:
                return HttpResponseRedirect('/macwatch/')
        else:
            info_dict = populate_info_dict(account)
            info_dict['macwatch'] = m
            return render(request, 'macwatch/deletemacwatch.html', info_dict)
    return HttpResponseRedirect('/macwatch/')


def edit_macwatch(request, macwatchid):
    """Edit description on a macwatch - currently not in use"""
    if request.method == 'POST':
        macwatchform = MacWatchForm(request.POST)
        if macwatchform.is_valid():
            m = MacWatch.objects.get(id=macwatchid)
            m.mac = macwatchform.cleaned_data['macaddress']
            m.description = macwatchform.cleaned_data['description']
            m.save()
            return HttpResponseRedirect('/macwatch/')
        else:
            account = get_account(request)
            info_dict = populate_info_dict(account)
            info_dict['form'] = macwatchform
            return render(request, 'macwatch/editmacwatch.html', info_dict)

    if macwatchid:
        m = MacWatch.objects.get(id=macwatchid)
        data = {'macaddress': m.mac, 'description': m.description}
        macwatchform = MacWatchForm(initial=data)
    info_dict = populate_info_dict(account)
    info_dict['form'] = macwatchform
    return render(request, 'macwatch/editmacwatch.html', info_dict)


def populate_info_dict(account, macwatches=None, messages=None):
    info_dict = {'account': account}
    if macwatches:
        info_dict['macwatches'] = macwatches
    if messages:
        info_dict['messages'] = messages
    info_dict.update(DEFAULT_VALUES)
    return info_dict
