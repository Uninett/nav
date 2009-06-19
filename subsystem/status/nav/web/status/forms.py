# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#

from django import forms

from nav.models.profiles import StatusPreference
from nav.models.manage import Netbox
from nav.web import serviceHelper

class NoneWidget(forms.widgets.Widget):
    '''Does not render a form widget, only a simple paragraph.'''
    def render(self, name, value, attrs=None, choices=()):
        for choice in self.choices:
            if choice[0] == value:
                value = choice[1]
        return forms.widgets.mark_safe(u'<p>%s</p>' % value)

class SectionForm(forms.ModelForm):
    name = forms.CharField()
    type = forms.ChoiceField(choices=StatusPreference.SECTION_CHOICES,
        widget=NoneWidget)

    class Meta:
        model = StatusPreference

    def __init__(self, *args, **kwargs):
        super(SectionForm, self).__init__(*args, **kwargs)
        
        # All section types except threshold let's the user choose state
        if self.instance.type != StatusPreference.SECTION_THRESHOLD:
            selected_states = self.instance.states
            if selected_states:
                selected_states = selected_states.split(',')

            self.fields['state_choice'] = forms.MultipleChoiceField(
                choices=Netbox.UP_CHOICES,
                initial=selected_states
            )

        # No categories choice for services, instead it's a service choice
        if self.instance.type == StatusPreference.SECTION_SERVICE:
            services = [(s,s) for s in serviceHelper.getCheckers()]
            selected_services = self.instance.services
            if selected_services:
                selected_services = selected_services.split(',')

            self.fields['categories'] = None
            self.fields['service_choice'] = forms.MultipleChoiceField(
                choices=services,
                initial=selected_services
            )

    def save(self, *args, **kwargs):
        '''Probably a bad idea to save this form automatically.'''
        raise Exception('Oh no you didn\'t!')
