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
from django.core.urlresolvers import reverse
from django.forms.models import modelformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import (Layout, Fieldset, Row, Column,
                                            HTML, Submit)
from nav.models.profiles import NavbarLink, Account
from nav.web.crispyforms import CheckBox, NavSubmit


class LoginForm(forms.Form):
    origin = forms.CharField(widget=forms.HiddenInput, required=False)
    username = forms.CharField(label='Username')
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(render_value=False))

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = 'webfront-login'
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'username', 'password', 'origin',
            Submit('submit', 'Log in', css_class='small expand')
        )


class NavbarlinkForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NavbarlinkForm, self).__init__(*args, **kwargs)
        self.empty_permitted = True
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.render_unmentioned_fields = True

        self.helper.layout = Layout(
            Row(
                Column('name', css_class='medium-5'),
                Column('uri', css_class='medium-5'),
                Column(HTML('<label>&nbsp;</label>'),
                       CheckBox('DELETE'), css_class='link-delete medium-2'),
            ),
        )

NavbarLinkFormSet = modelformset_factory(
    NavbarLink, exclude=('account',),
    form=NavbarlinkForm, extra=2, can_delete=1)


class ChangePasswordForm(forms.Form):
    """Form for changing password for an account"""
    old_password = forms.CharField(label='Old password',
                                   widget=forms.widgets.PasswordInput)
    new_password1 = forms.CharField(label='New password (>= 8 characters)',
                                    min_length=Account.MIN_PASSWD_LENGTH,
                                    widget=forms.widgets.PasswordInput)
    new_password2 = forms.CharField(label='Repeat password',
                                    min_length=Account.MIN_PASSWD_LENGTH,
                                    widget=forms.widgets.PasswordInput)

    def __init__(self, *args, **kwargs):
        if 'my_account' in kwargs:
            self.account = kwargs.pop('my_account')
        else:
            self.account = None

        super(ChangePasswordForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                'Change password',
                'old_password', 'new_password1', 'new_password2',
                Submit('submit', 'Change password', css_class='small')
            )
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


class ColumnsForm(forms.Form):
    """Form for choosing number of columns on webfront"""
    _choices = [('2', '2 columns'), ('3', '3 columns'), ('4', '4 columns')]
    num_columns = forms.ChoiceField(choices=_choices, label='Number of columns')

    def __init__(self, *args, **kwargs):
        super(ColumnsForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse(
            'webfront-preferences-setwidgetcolumns')

        self.helper.layout = Layout(
            Fieldset(
                'Number of columns for widgets',
                'num_columns',
                NavSubmit('submit', 'Save')
            )
        )
