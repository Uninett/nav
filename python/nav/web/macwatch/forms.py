#
# Copyright (C) 2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""macwatch form definitions"""

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
