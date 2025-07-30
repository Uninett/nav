# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

from django import forms
from django.forms.models import modelformset_factory
from nav.models.profiles import NavbarLink, Account
from nav.web.crispyforms import (
    SubmitField,
    set_flat_form_attributes,
    FlatFieldset,
)


class LoginForm(forms.Form):
    origin = forms.CharField(widget=forms.HiddenInput, required=False)
    username = forms.CharField(label='Username')
    password = forms.CharField(
        label='Password', widget=forms.PasswordInput(render_value=False)
    )

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.attrs = set_flat_form_attributes(
            form_action='webfront-login',
            form_fields=[self['username'], self['password'], self['origin']],
            submit_field=SubmitField(value='Log in', css_classes='small expand'),
        )


class NavbarlinkForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NavbarlinkForm, self).__init__(*args, **kwargs)
        self.empty_permitted = True
        self.render_unmentioned_fields = True
        self.attrs = set_flat_form_attributes(
            form_fields=[
                self['name'],
                self['uri'],
            ]
        )


NavbarLinkFormSet = modelformset_factory(
    NavbarLink, exclude=('account',), form=NavbarlinkForm, extra=2, can_delete=1
)


class ChangePasswordForm(forms.Form):
    """Form for changing password for an account"""

    old_password = forms.CharField(
        label='Old password', widget=forms.widgets.PasswordInput
    )
    new_password1 = forms.CharField(
        label='New password (>= 8 characters)',
        min_length=Account.MIN_PASSWD_LENGTH,
        widget=forms.widgets.PasswordInput,
    )
    new_password2 = forms.CharField(
        label='Repeat password',
        min_length=Account.MIN_PASSWD_LENGTH,
        widget=forms.widgets.PasswordInput,
    )

    def __init__(self, *args, **kwargs):
        if 'my_account' in kwargs:
            self.account = kwargs.pop('my_account')
        else:
            self.account = None

        super(ChangePasswordForm, self).__init__(*args, **kwargs)

        self.attrs = set_flat_form_attributes(
            form_id="change-password-form",
            form_action='webfront-preferences-changepassword',
            form_fields=[
                FlatFieldset(
                    legend='Change password',
                    fields=[
                        self['old_password'],
                        self['new_password1'],
                        self['new_password2'],
                        SubmitField(value='Change password', css_classes='small'),
                    ],
                )
            ],
        )

    def clean_old_password(self):
        """Verify that old password is correct"""
        old_password = self.cleaned_data['old_password']
        is_valid_password = self.account.check_password(old_password)
        if not is_valid_password:
            self.clear_passwords(self.cleaned_data)
            raise forms.ValidationError('Password is incorrect')
        return

    def clean(self):
        """Check that passwords match. If not clear form data"""
        cleaned_data = super(ChangePasswordForm, self).clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')

        if password1 != password2:
            self.clear_passwords(cleaned_data)
            raise forms.ValidationError('Passwords did not match')
        return cleaned_data

    @staticmethod
    def clear_passwords(cleaned_data):
        """Clear passwords from the cleaned data"""
        if 'new_password1' in cleaned_data:
            del cleaned_data['new_password1']
        if 'new_password2' in cleaned_data:
            del cleaned_data['new_password2']
        if 'old_password' in cleaned_data:
            del cleaned_data['old_password']
