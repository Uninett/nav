#
# Copyright (C) 2009-2013 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Machine tracker forms"""

from django import forms

from nav.macaddress import MacPrefix
from nav.web.machinetracker import iprange

from ..utils import validate_timedelta_for_overflow


class MachineTrackerForm(forms.Form):
    """General fields for forms in machinetracker"""

    dns = forms.BooleanField(
        required=False, initial=False, help_text="Show dns (if any)"
    )
    days = forms.IntegerField(
        initial=7,
        widget=forms.TextInput(attrs={'size': 3}),
        help_text="Days back in time to search",
    )
    vendor = forms.BooleanField(
        required=False, initial=False, help_text="Show vendor name (if any)"
    )

    def clean_days(self):
        """Clean the days fields"""
        data = int(self.cleaned_data['days'])
        if data < -1:
            # -1 has a specific meaning of "only active", for backwards
            # compatibility. Anything else is an error.
            raise forms.ValidationError(
                "I can't see into the future. Please enter a positive number."
            )

        validate_timedelta_for_overflow(days=data)

        return data


class IpTrackerForm(MachineTrackerForm):
    """Form for searching by IP-address"""

    choices = [('active', 'Active'), ('inactive', 'Inactive'), ('both', 'Both')]

    ip_range = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'IP-address or range'})
    )
    period_filter = forms.ChoiceField(
        widget=forms.RadioSelect(), choices=choices, initial='active'
    )
    netbios = forms.BooleanField(
        required=False, initial=False, help_text="Show netbios name (if any)"
    )

    source = forms.BooleanField(
        required=False,
        initial=False,
        help_text="Show which router the data is retrieved from",
    )

    def clean_ip_range(self):
        """Clean the ip_range field"""
        data = self.cleaned_data['ip_range']
        try:
            data = iprange.MachinetrackerIPRange.from_string(data)
        except ValueError as error:
            raise forms.ValidationError("Invalid syntax: %s" % error)
        return data


class MacTrackerForm(MachineTrackerForm):
    """Form for searching by MAC-address"""

    mac = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Mac-address'}))
    netbios = forms.BooleanField(
        required=False, initial=False, help_text="Netbios name (if any)"
    )

    def clean_mac(self):
        """Clean the mac field"""
        try:
            mac = MacPrefix(self.cleaned_data['mac'])
        except ValueError as error:
            raise forms.ValidationError(error)
        return mac


class SwitchTrackerForm(forms.Form):
    """Form for searching by switch fields"""

    switch = forms.CharField()
    module = forms.CharField(required=False, widget=forms.TextInput(attrs={'size': 3}))
    port = forms.CharField(required=False, widget=forms.TextInput(attrs={'size': 16}))
    days = forms.IntegerField(initial=7, widget=forms.TextInput(attrs={'size': 3}))
    vendor = forms.BooleanField(
        required=False, initial=False, help_text="Show vendor name (if any)"
    )


class NetbiosTrackerForm(MachineTrackerForm):
    """Form for searching by netbios name"""

    search = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Netbios name'})
    )

    def clean_search(self):
        """Make sure blank spaces and such is removed from search"""
        return self.cleaned_data['search'].strip()
