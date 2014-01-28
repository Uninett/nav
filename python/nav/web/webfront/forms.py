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
from django.forms.models import BaseModelFormSet
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms_foundation.layout import Submit
from nav.models.profiles import NavbarLink


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

class YourLinksFormSet(BaseModelFormSet):

    def __init__(self, *args, **kwargs):
        account = kwargs.pop('account', None)

        super(YourLinksFormSet, self).__init__(*args, **kwargs)

        self.queryset= NavbarLink.objects.filter(account=account)

        self.helper = FormHelper()
        self.helper.form_action = 'webfront-preferences'
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'name', 'url',
            NavSubmit('submit', 'Lagre')
        )

    class Meta:
        model = NavbarLink
        exclude = ('account',)

    


class NavbarlinkForm(forms.Form):
    id = forms.IntegerField(
        widget=forms.widgets.HiddenInput(),
        required=False
    )
    name = forms.CharField()
    url = forms.CharField()
