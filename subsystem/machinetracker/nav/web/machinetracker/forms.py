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

from django import forms

class MachineTrackerForm(forms.Form):
    dns = forms.BooleanField(required=False, initial=False)
    days = forms.IntegerField(
        initial=7,
        widget=forms.TextInput(attrs={'size': '3'}))

class IpTrackerForm(MachineTrackerForm):
    # IPAddressField only supports IPv4 as of Django 1.1
    from_ip = forms.CharField()
    to_ip = forms.CharField(required=False)
    active = forms.BooleanField(required=False, initial=True)
    inactive = forms.BooleanField(required=False)

class MacTrackerForm(MachineTrackerForm):
    # FIXME Maybe a RegexField?
    mac = forms.CharField()

class SwitchTrackerForm(MachineTrackerForm):
    switch = forms.CharField()
    module = forms.IntegerField(required=False)
    interface = forms.CharField(required=False)
