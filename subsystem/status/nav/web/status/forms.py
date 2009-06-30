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

from itertools import chain
from django import forms
from django.utils.encoding import force_unicode

from nav.models.profiles import StatusPreference
from nav.models.manage import Netbox
from nav.web import serviceHelper

class StatusTypeWidget(forms.widgets.HiddenInput):
    '''Users should not change status type, so we have a special widget for it.
    
    Renders a hidden input field with the status type and a simple textual
    representation.
    '''
    def render(self, name, value, attrs=None, choices=()):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        final_attrs['value'] = force_unicode(value)
        output = [u'<input%s>' % forms.util.flatatt(final_attrs)]

        for option_value, option_label in chain(self.choices, choices):
            if option_value == value:
                break
        output.append(u'%s<br />' % force_unicode(option_label))
        return forms.widgets.mark_safe(u'\n'.join(output))

class SectionForm(forms.ModelForm):
    name = forms.CharField()
    type = forms.ChoiceField(
        choices=StatusPreference.SECTION_CHOICES,
        widget=StatusTypeWidget()
    )
    position = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    account = forms.IntegerField(required=False)

    class Meta:
        model = StatusPreference

    def __init__(self, *args, **kwargs):
        type = kwargs.pop('type', None)
        super(SectionForm, self).__init__(*args, **kwargs)

        if not type:
            type = self.instance.type
        
        # All section types except threshold let's the user choose state
        if type != StatusPreference.SECTION_THRESHOLD:
            selected_states = self.instance.states
            if selected_states:
                selected_states = selected_states.split(',')

            self.fields['state_choice'] = forms.MultipleChoiceField(
                choices=Netbox.UP_CHOICES,
                initial=selected_states
            )

        # No categories choice for services, instead it's a service choice
        if type in (StatusPreference.SECTION_SERVICE, StatusPreference.SECTION_SERVICE_MAINTENANCE):
            services = [(s,s) for s in serviceHelper.getCheckers()]
            selected_services = self.instance.services
            if selected_services:
                selected_services = selected_services.split(',')

            del self.fields['categories']
            self.fields['service_choice'] = forms.MultipleChoiceField(
                choices=services,
                initial=selected_services
            )

    def clean(self, *args, **kwargs):
        # Different requirements for different types
        type = self.cleaned_data.get('type')
        categories = self.cleaned_data.get('categories')
        services = self.cleaned_data.get('service_choice')
        if type == 'service' or type == 'service_maintenance':
            # Service needs service and should not have categories.
            if not services:
                raise forms.ValidationError('No services selected')
            else:
                # Services are stored as a comma separated string.
                # Also, the options from the form are in service_state.
                #
                # Join the service_choice list and pass it to services.
                self.cleaned_data['services'] = ",".join(services)
                self.cleaned_data['categories'] = []
        else:
            # Netbox needs categories and should not have services
            if not categories:
                raise forms.ValidationError('No categories selected')
            else:
                self.cleaned_data['categories'] = categories
                self.cleaned_data['services'] = ''

        if type != StatusPreference.SECTION_THRESHOLD:
            # States are stored as a comma separated string.
            # Also, the options from the form are in state_choice.
            #
            # Join the state_choice list and pass it to states.
            states = self.cleaned_data.get('state_choice')
            self.cleaned_data['states'] = ",".join(states)

        return self.cleaned_data

    def save(self, account=None, position=None, commit=True):
        # Look away!
        self.cleaned_data['account'] = account
        self.cleaned_data['position'] = position
        # You can look again.

        return super(SectionForm, self).save(commit=commit)

class AddSectionForm(forms.Form):
    section = forms.ChoiceField(
        choices=StatusPreference.SECTION_CHOICES,
        label='Add section',
    )
