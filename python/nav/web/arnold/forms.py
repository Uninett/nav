#
# Copyright (C) 2012 (SD -311000) UNINETT AS
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
"""Forms for Arnold"""

from django import forms

class JustificationForm(forms.Form):
    """Form for adding a new justificaton"""
    name = forms.CharField(label="Name:")
    description = forms.CharField(label="Description", required=False)
    justificationid = forms.IntegerField(widget=forms.HiddenInput(),
                                         required=False)


class HistorySearchForm(forms.Form):
    """Form for searching in history"""
    days = forms.IntegerField(widget=forms.TextInput({'size': 3}))
