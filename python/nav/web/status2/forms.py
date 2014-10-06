#
# Copyright (C) 2014 UNINETT AS
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
"""Forms for the status page"""
from operator import itemgetter

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import Layout, Row, Column

from nav.models.event import EventType
from nav.models.manage import Organization, Category


class StatusPanelForm(forms.Form):
    """Form representing the status panel options for the user"""

    def __init__(self, *args, **kwargs):
        super(StatusPanelForm, self).__init__(*args, **kwargs)
        self.fields['alert_type'] = forms.MultipleChoiceField(
            choices=get_alert_types(),
            required=False
        )
        self.fields['category'] = forms.MultipleChoiceField(
            choices=[(c.id, c.id) for c in Category.objects.all()],
            required=False
        )
        self.fields['organization'] = forms.MultipleChoiceField(
            choices=[(o.id, o.id) for o in Organization.objects.all()],
            required=False
        )

        self.helper = FormHelper()
        self.helper.form_id = 'status-panel'
        self.helper.form_action = ''
        self.helper.form_method = 'POST'
        self.helper.layout = Layout(
            Row(
                Column('alert_type', css_class='medium-4'),
                Column('category', css_class='medium-4'),
                Column('organization', css_class='medium-4'),
            )
        )


def get_alert_types():
    alert_types = {}
    for e in EventType.objects.all():
        if len(e.alerttype_set.all()):
            if e.id not in alert_types:
                alert_types[e.id] = []
            for a in e.alerttype_set.all().order_by('name'):
                alert_types[e.id].append((a.name, a.name))

    return sorted(alert_types.items(), key=itemgetter(0))
