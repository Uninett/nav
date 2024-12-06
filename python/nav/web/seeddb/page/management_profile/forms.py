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
from nav.web.seeddb.forms import get_single_layout

PROTOCOL_CHOICES = dict(ManagementProfile.PROTOCOL_CHOICES)


class ManagementProfileFilterForm(forms.Form):
    """Form for filtering connection profiles"""

    protocol = forms.ChoiceField(
        required=False, choices=ManagementProfile.PROTOCOL_CHOICES
    )

    def __init__(self, *args, **kwargs):
        super(ManagementProfileFilterForm, self).__init__(*args, **kwargs)

        self.attrs = get_single_layout(
            heading="Filter connection profiles", filter_field=self["protocol"]
        )


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


class HttpApiForm(ProtocolSpecificMixIn, forms.ModelForm):
    PROTOCOL = ManagementProfile.PROTOCOL_HTTP_API
    PROTOCOL_NAME = PROTOCOL_CHOICES.get(PROTOCOL)

    class Meta(object):
        model = ManagementProfile
        configuration_fields = ['api_key', 'service']
        fields = []

    api_key = forms.CharField(
        label="API key",
        help_text="Key/token to authenticate to the service",
        required=True,
    )

    service = forms.ChoiceField(
        choices=(("Palo Alto ARP", "Palo Alto ARP"),),
        help_text="",
        required=True,
    )


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

    version = forms.ChoiceField(
        choices=(
            (2, '2c'),
            (1, '1'),
        )
    )
    community = forms.CharField(required=True)
    write = forms.BooleanField(
        required=False,
        help_text="Check if this community string enables write access",
    )


class SnmpV3Form(ProtocolSpecificMixIn, forms.ModelForm):
    PROTOCOL = ManagementProfile.PROTOCOL_SNMPV3
    PROTOCOL_NAME = PROTOCOL_CHOICES.get(PROTOCOL)
    NOTABENE = "SNMPv3 is not yet fully supported in NAV"

    class Meta(object):
        model = ManagementProfile
        configuration_fields = [
            "sec_level",
            "auth_protocol",
            "sec_name",
            "auth_password",
            "priv_protocol",
            "priv_password",
            "write",
        ]
        fields = []

    sec_level = forms.ChoiceField(
        label="Security level",
        choices=(
            ("noAuthNoPriv", "noAuthNoPriv"),
            ("authNoPriv", "authNoPriv"),
            ("authPriv", "authPriv"),
        ),
        help_text="The required SNMPv3 security level",
    )
    auth_protocol = forms.ChoiceField(
        label="Authentication protocol",
        choices=(
            ("MD5", "MD5"),
            ("SHA", "SHA"),
            ("SHA-512", "SHA-512"),
            ("SHA-384", "SHA-384"),
            ("SHA-256", "SHA-256"),
            ("SHA-224", "SHA-224"),
        ),
        help_text="Authentication protocol to use",
    )
    sec_name = forms.CharField(
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
        label="Security name",
        help_text=(
            "The username to authenticate as.  This is required even if noAuthPriv "
            "security mode is selected."
        ),
    )
    auth_password = forms.CharField(
        widget=forms.PasswordInput(render_value=True, attrs={"autocomplete": "off"}),
        label="Authentication password",
        help_text=(
            "The password to authenticate the user. Required for authNoPriv or "
            "authPriv security levels."
        ),
        required=False,
    )
    priv_protocol = forms.ChoiceField(
        label="Privacy protocol",
        choices=(
            ("DES", "DES"),
            ("AES", "AES"),
        ),
        help_text="Privacy protocol to use.  Required for authPriv security level.",
        required=False,
    )
    priv_password = forms.CharField(
        widget=forms.PasswordInput(render_value=True, attrs={"autocomplete": "off"}),
        label="Privacy password",
        help_text=(
            "The password to use for DES or AES encryption.  Required for authPriv "
            "security level."
        ),
        required=False,
    )
    write = forms.BooleanField(
        initial=False,
        required=False,
        label="Enables write access",
        help_text="Check this if this profile enables write access",
    )

    def clean_auth_password(self):
        level = self.cleaned_data.get("sec_level")
        password = self.cleaned_data.get("auth_password").strip()
        if level.startswith("auth") and not password:
            raise forms.ValidationError(
                f"Authentication password must be set for security level {level}"
            )
        return password

    def clean_priv_password(self):
        level = self.cleaned_data.get("sec_level")
        password = self.cleaned_data.get("priv_password").strip()
        if level == "authPriv" and not password:
            raise forms.ValidationError(
                f"Privacy password must be set for security level {level}"
            )
        return password


class NapalmForm(ProtocolSpecificMixIn, forms.ModelForm):
    PROTOCOL = ManagementProfile.PROTOCOL_NAPALM
    PROTOCOL_NAME = PROTOCOL_CHOICES.get(PROTOCOL)

    class Meta(object):
        model = ManagementProfile
        configuration_fields = [
            "driver",
            "username",
            "password",
            "private_key",
            "use_keys",
            "alternate_port",
            "timeout",
        ]
        fields = []

    driver = forms.ChoiceField(
        choices=(("JunOS", "JunOS"),),
        initial="JunOS",
        help_text="Which NAPALM driver to use",
    )
    username = forms.CharField(required=True, help_text="User name to use for login")
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=True),
        help_text="Password to use for login",
    )
    private_key = forms.CharField(
        required=False,
        widget=forms.Textarea(),
        help_text="SSH private key to use for login",
    )
    use_keys = forms.BooleanField(
        required=False, help_text="Check to try the available keys in ~/.ssh/"
    )
    alternate_port = forms.IntegerField(
        required=False,
        help_text="Alternate port (default port value varies with vendor)",
        min_value=1,
        max_value=65535,
    )
    timeout = forms.IntegerField(
        required=False,
        help_text="Timeout value in seconds",
        min_value=1,
        max_value=600,
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
