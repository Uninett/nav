# -*- coding: utf-8 -*-
#
# Copyright 2008 UNINETT AS
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
# Authors: Magnus Motzfeldt Eide <magnus.eide@uninett.no>
#

__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Magnus Motzfeldt Eide (magnus.eide@uninett.no)"
__id__ = "$Id$"

import time
import operator
from datetime import date
from django import newforms as forms

# FIXME Optgroups in ChoiceField does not work before rev 7977 of
# django. Use GroupedChoiceField from djangosnippets in the mean time.
from nav.django.widgets import GroupedSelect, GroupedChoiceField

from nav.models.event import EventType, AlertType

class HistoryFilterForm(forms.Form):
    from_date = forms.DateField(
        initial=date.fromtimestamp(time.time() - 7 * 24 * 60 * 60),
        required=False
    )
    to_date = forms.DateField(initial=date.today(), required=False)
    type = GroupedChoiceField(required=False)
    loc = forms.MultipleChoiceField(widget=forms.MultipleHiddenInput, required=False)
    room = forms.MultipleChoiceField(widget=forms.MultipleHiddenInput, required=False)
    netbox = forms.MultipleChoiceField(widget=forms.MultipleHiddenInput, required=False)
    module = forms.MultipleChoiceField(widget=forms.MultipleHiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        super(HistoryFilterForm, self).__init__(*args, **kwargs)

        alert_types = AlertType.objects.all().order_by('event_type', 'id')
        event_types = {}

        for t in alert_types:
            if t.event_type.id not in event_types.keys():
                event_types[t.event_type.id] = []
            event_types[t.event_type.id].append((t.id, t.name))

        all_choice = (
            None, (
                ('all', 'All'),
            )
        )
        choices = [all_choice]
        for key, values in event_types.items():
            choices.append((key, values))

        choices.sort(key=operator.itemgetter(0))
        self.fields['type'] = GroupedChoiceField(choices, required=False)
