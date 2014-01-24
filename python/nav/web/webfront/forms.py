# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms_foundation.layout import Submit


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
            Submit('submit', 'Log in', css_class='small')
        )


class PersonalNavbarForm(forms.Form):
    id = forms.IntegerField(
        widget=forms.widgets.HiddenInput(),
        required=False
    )
    name = forms.CharField()
    url = forms.CharField()
    navbar = forms.BooleanField(required=False)
    qlink1 = forms.BooleanField(required=False)
    qlink2 = forms.BooleanField(required=False)


class NavbarForm(PersonalNavbarForm):
    name = forms.CharField(
        widget=forms.widgets.TextInput(attrs={
            'readonly': 'readonly'
        }),
        required=False
    )
    url = forms.CharField(
        widget=forms.widgets.TextInput(attrs={
            'readonly': 'readonly'
        }),
        required=False
    )
