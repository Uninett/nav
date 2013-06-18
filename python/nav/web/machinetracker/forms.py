#
# Copyright (C) 2009-2013 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Machine tracker forms"""

from nav.macaddress import MacPrefix
from nav.web.machinetracker import iprange
from django import forms
from django.forms.util import ErrorList


class IpTrackerForm(forms.Form):
    # IPAddressField only supports IPv4 as of Django 1.1
    ip_range = forms.CharField()
    active = forms.BooleanField(required=False, initial=True)
    inactive = forms.BooleanField(required=False)
    dns = forms.BooleanField(required=False, initial=False)
    netbios = forms.BooleanField(required=False, initial=False)
    days = forms.IntegerField(
        initial=7,
        widget=forms.TextInput(attrs={'size': 3}))

    def clean(self):
        data = self.cleaned_data

        if not data['active'] and not data['inactive']:
            msg = u"Either active, inactive or both must be checked."
            self._errors['active'] = ErrorList([msg])
            del data['active']
            del data['inactive']
        return data

    def clean_ip_range(self):
        data = self.cleaned_data['ip_range']
        try:
            data = iprange.MachinetrackerIPRange.from_string(data)
        except ValueError as error:
            raise forms.ValidationError("Invalid syntax: %s" % error)
        return data


class MacTrackerForm(forms.Form):
    mac = forms.CharField()
    dns = forms.BooleanField(required=False, initial=False)
    netbios = forms.BooleanField(required=False, initial=False)
    days = forms.IntegerField(
        initial=7,
        widget=forms.TextInput(attrs={'size': 3}))

    def clean_mac(self):
        try:
            mac = MacPrefix(self.cleaned_data['mac'])
        except ValueError as error:
            raise forms.ValidationError(error)
        return mac


class SwitchTrackerForm(forms.Form):
    switch = forms.CharField()
    module = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'size': 3}))
    port = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'size': 16}))
    days = forms.IntegerField(
        initial=7,
        widget=forms.TextInput(attrs={'size': 3}))


class NetbiosTrackerForm(forms.Form):
    search = forms.CharField()
    dns = forms.BooleanField(required=False, initial=False)
    days = forms.IntegerField(
        initial=7,
        widget=forms.TextInput(attrs={'size': 3}))

    def clean_search(self):
        """Make sure blank spaces and such is removed from search"""
        return self.cleaned_data['search'].strip()
