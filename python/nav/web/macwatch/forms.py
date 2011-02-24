# -*- coding: utf-8 -*-
#
# Copyright 2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#

__copyright__ = "Copyright 2011 UNINETT AS"
__license__ = "GPL"
__author__ = "John-Magne Bredal <john.m.bredal@ntnu.no> and Trond Kandal <Trond.Kandal@ntnu.no>"
__id__ = "$Id$"

import re

from django import forms
from nav.web.macwatch.models import MacWatch

class MacWatchForm(forms.Form):
    macaddress = forms.CharField(max_length=17)
    description = forms.CharField(max_length=200, required=False)

    def clean_macaddress(self):
        """ Validate macaddress """
        macaddress = self.cleaned_data.get('macaddress','')

        # Filter : which is a common separator for mac addresses
        filteredmacaddress = re.sub(":", "", macaddress)

        if not re.match("[a-fA-F0-9]{12}$", filteredmacaddress):
            raise forms.ValidationError("Wrong format on mac address.")

        if int(MacWatch.objects.filter(mac=macaddress).count()) > 0:
            raise forms.ValidationError("This mac address is already watched.")
        
        return filteredmacaddress
