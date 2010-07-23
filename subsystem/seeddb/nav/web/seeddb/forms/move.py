# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

from django import forms

from nav.Snmp import Snmp, TimeOutException, SnmpError
from nav.models.cabling import Cabling, Patch
from nav.models.manage import Netbox, NetboxType, Room, Location, Organization, Usage, Vendor, Subcategory, Vlan, Prefix, Category
from nav.models.service import Service


class RoomMoveForm(forms.Form):
    location = forms.ModelChoiceField(Location.objects.order_by('id').all(), required=True)

class NetboxMoveForm(forms.Form):
    room = forms.ModelChoiceField(Room.objects.order_by('id').all())
    organization = forms.ModelChoiceField(Organization.objects.order_by('id').all())
