#
# Copyright (C) 2013 UNINETT AS
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
"""Forms for netbox group info page"""


from django import forms


class NetboxGroupForm(forms.Form):
    """Form for searching for netbox groups"""

    query = forms.CharField(max_length=100, label='')

    def clean_query(self):
        """Returns a cleaned version of the searchstring"""
        return self.cleaned_data['query'].strip()
