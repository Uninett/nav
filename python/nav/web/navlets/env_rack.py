#
# Copyright (C) 2016 Uninett AS
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
"""Module containing EnvironmentRackWidget"""

from django import forms

from nav.models.rack import Rack
from . import Navlet


class RackSearchForm(forms.Form):
    """Form for searching for a rack"""
    rack = forms.ModelChoiceField(queryset=Rack.objects.all().order_by(
        'room', 'rackname'))

    def clean_rack(self):
        """clean_rack makes sure the rack refers to the primary key

        This is done because the rack is stored as a preference, and thus cannot
        be a model instace
        """
        rack = self.cleaned_data.get('rack')
        if rack:
            return rack.pk
        return rack


class EnvironmentRackWidget(Navlet):
    """Widget for displaying an environment rack"""

    title = 'Environment rack'
    description = (
        'Displays a selected rack of environment sensors from a specific room'
    )
    refresh_interval = 60000  # 60 seconds
    is_editable = True

    def get_template_basename(self):
        return 'envrack'

    def get_context_data_view(self, context):
        context['rackid'] = self.preferences.get('rack')
        context['refresh_interval'] = self.preferences.get(
            'refresh_interval', self.refresh_interval)
        return context

    def get_context_data_edit(self, context):
        try:
            rack = Rack.objects.get(pk=self.preferences.get('rack'))
            form = RackSearchForm(initial={'rack': rack})
        except (Rack.DoesNotExist, ValueError):
            form = RackSearchForm()

        context['form'] = form
        return context

    def post(self, request, **kwargs):
        """Save preferences"""
        form = RackSearchForm(request.POST)
        return super(EnvironmentRackWidget, self).post(request, form=form)
