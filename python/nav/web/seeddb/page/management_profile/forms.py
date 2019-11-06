#
# Copyright (C) 2019 Uninett AS
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
from django import forms

from nav.models.manage import ManagementProfile
from nav.web.seeddb.forms import get_formhelper, get_single_layout

PROTOCOL_CHOICES = dict(ManagementProfile.PROTOCOL_CHOICES)


class ManagementProfileFilterForm(forms.Form):
    """Form for filtering connection profiles"""
    protocol = forms.ChoiceField(
        required=False,
        choices=ManagementProfile.PROTOCOL_CHOICES)

    def __init__(self, *args, **kwargs):
        super(ManagementProfileFilterForm, self).__init__(*args, **kwargs)
        self.helper = get_formhelper()
        self.helper.layout = get_single_layout('Filter connection profiles', 'protocol')


class ProtocolSpecificMixIn(object):
    """Mixin class for protocol specific management configuration forms.

    Provides the necessary functionality for translating form fields into
    JSON-compatible configuration dicts, as required by the
    ManagementProfile.configuration field.

    """
    def __init__(self, *args, **kwargs):
        super(ProtocolSpecificMixIn, self).__init__(*args, **kwargs)

        if self.instance:
            cfg = self.instance.configuration
            for field in self.Meta.configuration_fields:
                if field in cfg:
                    self.fields[field].initial = cfg.get(field)

    def _post_clean(self):
        super(ProtocolSpecificMixIn, self)._post_clean()
        cfg = self.instance.configuration
        for field in self.Meta.configuration_fields:
            if field in self.cleaned_data:
                cfg[field] = self.cleaned_data.get(field)


class DebugForm(ProtocolSpecificMixIn, forms.ModelForm):
    PROTOCOL = ManagementProfile.PROTOCOL_DEBUG
    PROTOCOL_NAME = PROTOCOL_CHOICES.get(PROTOCOL)

    class Meta(object):
        model = ManagementProfile
        configuration_fields = ['foo']
        fields = []

    foo = forms.CharField(required=True)


class SnmpForm(ProtocolSpecificMixIn, forms.ModelForm):
    PROTOCOL = ManagementProfile.PROTOCOL_SNMP
    PROTOCOL_NAME = PROTOCOL_CHOICES.get(PROTOCOL)

    class Meta(object):
        model = ManagementProfile
        configuration_fields = ['version', 'community', 'write']
        fields = []

    version = forms.ChoiceField(choices=(
        (2, '2c'),
        (1, '1'),
    ))
    community = forms.CharField(required=True)
    write = forms.BooleanField(
        required=False,
        help_text="Check if this community string enables write access",
    )


FORM_MAPPING = {
    form_class.PROTOCOL: form_class
    for form_class in ProtocolSpecificMixIn.__subclasses__()
}


class ManagementProfileForm(forms.ModelForm):
    """Form for editing/adding connection profiless"""
    class Meta(object):
        model = ManagementProfile
        fields = ['name', 'description', 'protocol']

    def __init__(self, *args, **kwargs):
        super(ManagementProfileForm, self).__init__(*args, **kwargs)

    def get_protocol_form_class(self):
        """Returns the protocol-specific form class that corresponds with the selected
        management protocol of this profile.

        """
        return FORM_MAPPING.get(self.cleaned_data['protocol'])

    @staticmethod
    def get_protocol_forms():
        """Returns a list of all known protocol-specific sub-form classes"""
        return FORM_MAPPING.values()
