#
# Copyright (C) 2008 Uninett AS
# Copyright (C) 2022 Sikt
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
"""Forms for the user admin system"""

from datetime import date, timedelta

from django import forms
from django.utils.encoding import force_str

from nav.web.crispyforms import (
    set_flat_form_attributes,
    FlatFieldset,
    FormColumn,
    FormRow,
    SubmitField,
)

from nav.models.profiles import Account, AccountGroup, PrivilegeType
from nav.models.manage import Organization
from nav.models.api import APIToken, JWTRefreshToken
from nav.web.api.v1.views import get_endpoints as get_api_endpoints
from nav.util import auth_token


class AccountGroupForm(forms.ModelForm):
    """Form for adding or editing a group on the group page"""

    name = forms.CharField(required=True)
    description = forms.CharField(required=True)

    def __init__(self, *args, **kwargs):
        super(AccountGroupForm, self).__init__(*args, **kwargs)

        self.attrs = set_flat_form_attributes(
            form_fields=[
                FlatFieldset(
                    legend="Group info",
                    fields=[
                        self["name"],
                        self["description"],
                        SubmitField(
                            name="submit_group",
                            value="Save changes",
                            css_classes="small",
                        ),
                    ],
                )
            ]
        )

    class Meta(object):
        model = AccountGroup
        fields = ('name', 'description')


class AccountForm(forms.ModelForm):
    """Form for creating and editing an account"""

    password1 = forms.CharField(
        label='New password (>= 8 characters)',
        min_length=Account.MIN_PASSWD_LENGTH,
        widget=forms.widgets.PasswordInput,
    )
    password2 = forms.CharField(
        label='Repeat password',
        min_length=Account.MIN_PASSWD_LENGTH,
        widget=forms.widgets.PasswordInput,
        required=False,
    )
    login = forms.CharField(required=True)
    name = forms.CharField(required=True)

    def __init__(self, *args, **kwargs):
        super(AccountForm, self).__init__(*args, **kwargs)
        account = kwargs.get('instance', False)

        if account:
            self.fields['password1'].required = False

            if kwargs["instance"].id == Account.DEFAULT_ACCOUNT:
                # We don't want to enable significant changes to the anonymous account
                self.fields["password1"].widget.attrs["readonly"] = True
                self.fields["password2"].widget.attrs["readonly"] = True
                self.fields["login"].widget.attrs["readonly"] = True

        submit_value = "Save changes" if account else "Create account"

        self.attrs = set_flat_form_attributes(
            form_fields=[
                FlatFieldset(
                    legend="Account",
                    fields=[
                        self["login"],
                        self["name"],
                        self["password1"],
                        self["password2"],
                        SubmitField(
                            "submit_account", submit_value, css_classes="small"
                        ),
                    ],
                )
            ],
        )

    def clean_password1(self):
        """Validate password"""
        password1 = self.data.get('password1')
        password2 = self.data.get('password2')

        if password1 != password2:
            raise forms.ValidationError('Passwords did not match')
        return password1

    def is_valid(self):
        if not super(AccountForm, self).is_valid():
            self.data = self.data.copy()
            if 'password1' in self.data:
                del self.data['password1']
            if 'password2' in self.data:
                del self.data['password2']
            return False
        return True

    class Meta(object):
        model = Account
        exclude = ('password', 'ext_sync', 'organizations', 'preferences')


class ExternalAccountForm(AccountForm):
    """Form for editing an externally managed account"""

    def __init__(self, *args, **kwargs):
        super(AccountForm, self).__init__(*args, **kwargs)

        # We don't want to enable local password editing for accounts that are
        # managed externally.
        del self.fields['password1']
        del self.fields['password2']
        self.fields['login'].widget.attrs['readonly'] = True

        self.attrs = set_flat_form_attributes(
            form_fields=[
                FlatFieldset(
                    legend="Account",
                    fields=[
                        self["login"],
                        self["name"],
                        SubmitField(
                            "submit_account", "Save changes", css_classes="small"
                        ),
                    ],
                    template="useradmin/frag-external-account-fieldset.html",
                )
            ],
        )


class PrivilegeForm(forms.Form):
    """Form for adding a privilege to a group from the group page"""

    type = forms.models.ModelChoiceField(PrivilegeType.objects.all(), label='')
    target = forms.CharField(
        required=True, label='', widget=forms.TextInput(attrs={'placeholder': 'Target'})
    )

    def __init__(self, *args, **kwargs):
        super(PrivilegeForm, self).__init__(*args, **kwargs)
        self.fields['type'].widget.attrs.update({"class": "select2"})
        self.attrs = set_flat_form_attributes(
            form_fields=[
                FormRow(
                    fields=[
                        FormColumn(fields=[self["type"]], css_classes="medium-3"),
                        FormColumn(fields=[self["target"]], css_classes="medium-6"),
                        FormColumn(
                            fields=[
                                SubmitField(
                                    "submit_privilege", "Grant", css_classes="postfix"
                                )
                            ],
                            css_classes="medium-3",
                        ),
                    ]
                )
            ]
        )


class OrganizationAddForm(forms.Form):
    """Form for adding an organization to an account"""

    def __init__(self, account, *args, **kwargs):
        super(OrganizationAddForm, self).__init__(*args, **kwargs)
        if account:
            query = Organization.objects.exclude(id__in=account.organizations.all())
        else:
            query = Organization.objects.all()

        self.fields['organization'] = forms.models.ModelChoiceField(
            queryset=query, required=True, label=''
        )
        self.fields['organization'].widget.attrs.update({"class": "select2"})
        self.attrs = set_flat_form_attributes(
            form_fields=[self["organization"]],
            submit_field=SubmitField(
                "submit_org", "Add organization", css_classes="postfix"
            ),
        )


class GroupAddForm(forms.Form):
    """Form for adding a group to an account from the account page"""

    def __init__(self, account, *args, **kwargs):
        super(GroupAddForm, self).__init__(*args, **kwargs)
        if account:
            query = AccountGroup.objects.exclude(id__in=account.groups.all())
        else:
            query = AccountGroup.objects.all()

        self.fields['group'] = forms.models.ModelChoiceField(
            queryset=query, required=True, label=''
        )
        self.fields['group'].widget.attrs.update({'class': 'select2'})
        self.attrs = set_flat_form_attributes(
            form_fields=[
                FormRow(
                    fields=[
                        FormColumn(fields=[self['group']], css_classes='medium-8'),
                        FormColumn(
                            fields=[
                                SubmitField(
                                    'submit_group',
                                    'Add membership',
                                    css_classes='postfix',
                                )
                            ],
                            css_classes='medium-4',
                        ),
                    ]
                )
            ]
        )


class AccountAddForm(forms.Form):
    """Form for adding a user to a group from the group page"""

    def __init__(self, group, *args, **kwargs):
        super(AccountAddForm, self).__init__(*args, **kwargs)
        if group:
            query = Account.objects.exclude(id__in=group.accounts.all())
        else:
            query = Account.objects.all()

        self.fields['account'] = forms.models.ModelChoiceField(
            query,
            required=True,
            widget=forms.Select(attrs={'class': 'select2'}),
            label='',
        )
        self.attrs = set_flat_form_attributes(
            submit_field=SubmitField(
                'submit_account', 'Add to group', css_classes='postfix'
            )
        )


def _get_default_expires():
    return date.today() + timedelta(days=365)


class ReadonlyField(forms.CharField):
    """A readonly text field"""

    def widget_attrs(self, widget):
        attrs = super(ReadonlyField, self).widget_attrs(widget)
        attrs.update({'readonly': 'True'})
        return attrs


class TokenForm(forms.ModelForm):
    """Form for creating a new token"""

    token = ReadonlyField(initial=auth_token)
    permission = forms.ChoiceField(
        choices=APIToken.permission_choices,
        help_text=APIToken.permission_help_text,
        initial='read',
    )
    available_endpoints = get_api_endpoints()
    endpoints = forms.MultipleChoiceField(
        required=False, choices=sorted(available_endpoints.items())
    )
    expires = forms.DateField(
        initial=_get_default_expires, widget=forms.DateInput(attrs={'type': 'date'})
    )

    def __init__(self, *args, **kwargs):
        super(TokenForm, self).__init__(*args, **kwargs)

        # If we are editing an existing token, convert the previously chosen
        # endpoints from a dictionary to a list of keys. The 'clean_endpoints'
        # method does the opposite when saving.
        if self.instance and self.instance.endpoints:
            self.initial['endpoints'] = list(self.instance.endpoints.keys())

        if self.instance.id:
            submit_message = "Save token"
        else:
            submit_message = "Save new token"

        self.attrs = set_flat_form_attributes(
            form_id="edit-token-form",
            form_fields=[
                FormRow(
                    fields=[
                        FormColumn(
                            fields=[
                                FlatFieldset(
                                    legend="Token details",
                                    fields=[
                                        self["token"],
                                        self["permission"],
                                        self["expires"],
                                        self["comment"],
                                    ],
                                )
                            ],
                            css_classes="large-4 small-12",
                        ),
                        FormColumn(
                            fields=[
                                FlatFieldset(
                                    legend="Token endpoints", fields=[self["endpoints"]]
                                )
                            ],
                            css_classes="large-8 small-12",
                        ),
                    ]
                )
            ],
            submit_field=SubmitField("submit", submit_message, css_classes="small"),
        )

    def clean_endpoints(self):
        """Convert endpoints from list to dictionary"""
        endpoints = self.cleaned_data.get('endpoints')
        return {x: force_str(self.available_endpoints.get(x)) for x in endpoints}

    class Meta(object):
        model = APIToken
        fields = ['token', 'permission', 'expires', 'comment', 'endpoints']


class JWTRefreshTokenCreateForm(forms.ModelForm):
    """Form for creating a new refresh token"""

    name = forms.CharField(label='Token name')
    permission = forms.ChoiceField(
        choices=APIToken.permission_choices,
        help_text=APIToken.permission_help_text,
        initial='read',
    )
    available_endpoints = get_api_endpoints()
    endpoints = forms.MultipleChoiceField(
        required=False, choices=sorted(available_endpoints.items())
    )
    description = forms.CharField(label='Description', required=False)

    def __init__(self, *args, **kwargs):
        super(JWTRefreshTokenCreateForm, self).__init__(*args, **kwargs)

        self.attrs = set_flat_form_attributes(
            form_id="edit-jwt-form",
            form_fields=[
                FormRow(
                    fields=[
                        FormColumn(
                            fields=[
                                FlatFieldset(
                                    legend="Token details",
                                    fields=[
                                        self["name"],
                                        self["description"],
                                        self["permission"],
                                    ],
                                )
                            ],
                            css_classes="large-4 small-12",
                        ),
                        FormColumn(
                            fields=[
                                FlatFieldset(
                                    legend="Token endpoints", fields=[self["endpoints"]]
                                )
                            ],
                            css_classes="large-8 small-12",
                        ),
                    ]
                )
            ],
            submit_field=SubmitField("submit", "Save token", css_classes="small"),
        )

    def clean_endpoints(self):
        """Convert endpoints from list to dictionary"""
        endpoints = self.cleaned_data.get('endpoints')
        return {x: force_str(self.available_endpoints.get(x)) for x in endpoints}

    class Meta(object):
        model = JWTRefreshToken
        fields = ['name', 'description', 'permission', 'endpoints']


class JWTRefreshTokenEditForm(forms.ModelForm):
    """Form for editing an existing refresh token"""

    name = forms.CharField(label='Token name')
    description = forms.CharField(label='Description', required=False)

    def __init__(self, *args, **kwargs):
        super(JWTRefreshTokenEditForm, self).__init__(*args, **kwargs)

        self.attrs = set_flat_form_attributes(
            form_id="edit-jwt-form",
            form_fields=[
                FormRow(
                    fields=[
                        FormColumn(
                            fields=[
                                FlatFieldset(
                                    legend="Token details",
                                    fields=[self["name"], self["description"]],
                                )
                            ],
                            css_classes="large-4 small-12",
                        ),
                    ]
                )
            ],
            submit_field=SubmitField("submit", "Save token", css_classes="small"),
        )

    class Meta(object):
        model = JWTRefreshToken
        fields = ['name', 'description']
