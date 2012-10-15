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


from IPy import IP
from django import forms

from nav.models.arnold import STATUSES

class JustificationForm(forms.Form):
    """Form for adding a new justificaton"""
    name = forms.CharField(label="Name")
    description = forms.CharField(label="Description", required=False)
    justificationid = forms.IntegerField(widget=forms.HiddenInput(),
                                         required=False)


class QuarantineVlanForm(forms.Form):
    """Form for adding a new quarantine vlan"""
    vlan = forms.IntegerField(label="Vlan")
    description = forms.CharField(label="Description", required=False)
    qid = forms.IntegerField(widget=forms.HiddenInput(),
                             required=False)


class HistorySearchForm(forms.Form):
    """Form for searching in history"""
    days = forms.IntegerField(widget=forms.TextInput({'size': 3}))


class SearchForm(forms.Form):
    """Form for searching for detained computers"""
    search_choices = [('ip', 'IP'), ('mac', 'MAC'), ('netbios', 'Netbios'),
                      ('dns', 'DNS')]
    status_choices = STATUSES + [('any', 'Any')]

    searchtype = forms.ChoiceField(choices=search_choices)
    searchvalue = forms.CharField(required=True)
    status = forms.ChoiceField(choices=status_choices, label='Status')
    days = forms.IntegerField(label='Days', widget=forms.TextInput({'size': 3}))

    def clean_searchvalue(self):
        """Clean whitespace from searchvalue"""
        return self.cleaned_data['searchvalue'].strip()

    def clean(self):
        """Validate on several fields"""
        cleaned_data = self.cleaned_data
        searchtype = cleaned_data.get('searchtype')
        searchvalue = cleaned_data.get('searchvalue')

        if searchtype == 'ip':
            try:
                IP(searchvalue)
            except ValueError:
                self._errors["searchvalue"] = self.error_class(
                    ["IP-address or range is not valid"])
                del cleaned_data["searchvalue"]

        return cleaned_data
