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
"""macwatch form definitions"""

from django import forms
from nav.web.crispyforms import set_flat_form_attributes, FlatFieldset, SubmitField
from nav.web.macwatch.models import MacWatch
from nav.web.macwatch.utils import MAC_ADDR_MAX_LEN
from nav.web.macwatch.utils import MAC_ADDR_MIN_LEN
from nav.web.macwatch.utils import strip_delimiters
from nav.web.macwatch.utils import has_legal_values
from nav.web.macwatch.utils import add_zeros_to_mac_addr


class MacWatchForm(forms.Form):
    """A class to clean and sanitize input-data for macwatch."""

    prefix_length = None
    macaddress = forms.CharField(max_length=17)
    description = forms.CharField(max_length=200, required=False)

    def __init__(self, *args, **kwargs):
        super(MacWatchForm, self).__init__(*args, **kwargs)
        self.attrs = set_flat_form_attributes(
            form_fields=[
                FlatFieldset(
                    legend="Add mac to watch list",
                    fields=[self['macaddress'], self['description']],
                ),
                SubmitField(value='Add', css_classes='small'),
            ]
        )

    def clean_macaddress(self):
        """Validate macaddress"""
        macaddress = self.cleaned_data.get('macaddress', '')

        filteredmacaddress = strip_delimiters(macaddress)
        if len(filteredmacaddress) < MAC_ADDR_MIN_LEN:
            raise forms.ValidationError("Mac address/prefix is too short")
        if len(filteredmacaddress) > MAC_ADDR_MAX_LEN:
            raise forms.ValidationError("Mac address is too long")

        # Number hex-digits (or so-called nybbles),- since prefix may
        # get specified in hex-digits.
        # Set when a mac-address prefix is given.
        addr_len = len(filteredmacaddress)
        if addr_len >= MAC_ADDR_MIN_LEN and addr_len < MAC_ADDR_MAX_LEN:
            self.prefix_length = addr_len

        filteredmacaddress = add_zeros_to_mac_addr(filteredmacaddress)

        if not has_legal_values(filteredmacaddress):
            raise forms.ValidationError("Illegal values or format for mac address.")

        if int(MacWatch.objects.filter(mac=filteredmacaddress).count()) > 0:
            raise forms.ValidationError("This mac address is already watched.")

        return filteredmacaddress
