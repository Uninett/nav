#
# Copyright (C) 2019 UNINETT
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
from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import (
    Layout,
    Row,
    Column,
    Fieldset,
    Div,
    Field,
    HTML,
    Submit,
)
from django import forms

from nav.models.manage import ManagementProfile
from nav.web.seeddb.forms import get_formhelper, get_single_layout


class ManagementProfileFilterForm(forms.Form):
    """Form for filtering connection profiles"""
    protocol = forms.ChoiceField(
        required=False,
        choices=ManagementProfile.PROTOCOL_CHOICES)

    def __init__(self, *args, **kwargs):
        super(ManagementProfileFilterForm, self).__init__(*args, **kwargs)
        self.helper = get_formhelper()
        self.helper.layout = get_single_layout('Filter connection profiles',
                                               'protocol')


class DebugFormMixin(forms.Form):
    foo = forms.CharField(required=True)

    fieldset = Fieldset(
        'Debug configuration',
        'foo',
        css_class='management-protocol-debug',
    )


class SnmpFormMixin(forms.Form):  # no shti
    snmp_version = forms.ChoiceField(choices=(
        (2, '2c'),
        (1, '1'),
    ))
    community = forms.CharField(required=True)
    write = forms.BooleanField(
        required=False,
        help_text="Check if this community string enables write access",
    )

    fieldset = Fieldset(
        'SNMP Configuration',
        'snmp_version',
        'community',
        'write',
        css_class='management-protocol-snmp',
    )


class ManagementProfileForm(SnmpFormMixin, DebugFormMixin, forms.ModelForm):
    """Form for editing/adding connection profiless"""
    class Meta(object):
        model = ManagementProfile
        fields = ['name', 'description', 'protocol']

    def __init__(self, *args, **kwargs):
        super(ManagementProfileForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_action = ''
        self.helper.form_method = 'POST'
        self.helper.form_id = 'seeddb-management-profile-form'

        fieldsets = [
            base.fieldset
            for base in self.__class__.__bases__
            if hasattr(base, 'fieldset')
        ]
        config_column = Column(*fieldsets, css_class='large-8')

        self.helper.layout = Layout(
            Row(
                Column(
                    Fieldset(
                        'Basic profile',
                        'name', 'description', 'protocol',
                    ),
                    css_class='large-4',
                ),
                config_column,
            ),
            Submit('submit', 'Save management profile')
        )
        self.__class__.__bases__
