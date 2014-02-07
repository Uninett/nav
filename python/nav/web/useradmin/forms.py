#
# Copyright (C) 2008 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
# pylint: disable=R0903
"""Forms for the user admin system"""
from django import forms

from nav.models.profiles import Account, AccountGroup, PrivilegeType
from nav.models.manage import Organization

from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import (Layout, Fieldset, Submit, Row,
                                            Column, Field, HTML)


class AccountGroupForm(forms.ModelForm):
    """Form for adding or editing a group on the group page"""
    name = forms.CharField(required=True)
    description = forms.CharField(required=True)

    def __init__(self, *args, **kwargs):
        super(AccountGroupForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = ''
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Fieldset('Group', 'name', 'description',
                     Submit('submit_group', 'Save changes')))

    class Meta:
        model = AccountGroup
        fields = ('name', 'description')


class AccountForm(forms.ModelForm):
    """Form for creating and editing an account"""
    password1 = forms.CharField(label='New password (>= 8 characters)',
                                min_length=Account.MIN_PASSWD_LENGTH,
                                widget=forms.widgets.PasswordInput)
    password2 = forms.CharField(label='Repeat password',
                                min_length=Account.MIN_PASSWD_LENGTH,
                                widget=forms.widgets.PasswordInput,
                                required=False)
    login = forms.CharField(required=True)
    name = forms.CharField(required=True)

    def __init__(self, *args, **kwargs):
        super(AccountForm, self).__init__(*args, **kwargs)
        account = kwargs.get('instance', False)
        self.helper = FormHelper()
        self.helper.form_action = ''
        self.helper.form_method = 'POST'

        fieldset_name = 'Account'
        fieldset_args = [fieldset_name]
        default_args = ['login', 'name', 'password1', 'password2']

        if account:
            self.fields['password1'].required = False
            submit_value = 'Save changes'

            # Remove password and login from external accounts
            # This should really be two different forms because of this
            if kwargs['instance'].ext_sync:
                authenticator = "" \
                    "<p class='alert-box'>External authenticator: %s</p>" % (
                    kwargs['instance'].ext_sync)
                del self.fields['password1']
                del self.fields['password2']
                self.fields['login'].widget.attrs['readonly'] = True
                fieldset_args.extend(['login', 'name',
                                      HTML(authenticator)])
            else:
                fieldset_args.extend(default_args)
        else:
            submit_value = 'Create account'
            fieldset_args.extend(default_args)

        submit = Submit('submit_account', submit_value, css_class='small')
        fieldset_args.extend([submit])
        fieldset = Fieldset(*fieldset_args)
        self.helper.layout = Layout(fieldset)

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

    class Meta:
        model = Account
        exclude = ('password', 'ext_sync', 'organizations')


class PrivilegeForm(forms.Form):
    """Form for adding a privilege to a group from the group page"""
    type = forms.models.ModelChoiceField(PrivilegeType.objects.all(), label='',
                                         empty_label='--- Type ---')
    target = forms.CharField(required=True, label='',
                             widget=forms.TextInput(
                                 attrs={'placeholder': 'Target'}))

    def __init__(self, *args, **kwargs):
        super(PrivilegeForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = ""
        self.helper.form_method = "POST"
        self.helper.layout = Layout(
            Row(
                Column(Field('type', css_class='select2'),
                       css_class='medium-3'),
                Column('target', css_class='medium-6'),
                Column(Submit('submit_privilege', 'Grant',
                              css_class='postfix'), css_class='medium-3')
            )
        )


class OrganizationAddForm(forms.Form):
    """Form for adding an organization to an account"""
    def __init__(self, account, *args, **kwargs):
        super(OrganizationAddForm, self).__init__(*args, **kwargs)
        if account:
            query = Organization.objects.exclude(
                id__in=account.organizations.all())
        else:
            query = Organization.objects.all()

        self.fields['organization'] = forms.models.ModelChoiceField(
            queryset=query, required=True, label='')

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column(Field('organization', css_class='select2'),
                       css_class='medium-8'),
                Column(Submit('submit_org', 'Add organization',
                              css_class='postfix'),
                       css_class='medium-4')
            )
        )


class GroupAddForm(forms.Form):
    """Form for adding a group to an account from the account page"""
    def __init__(self, account, *args, **kwargs):
        super(GroupAddForm, self).__init__(*args, **kwargs)
        if account:
            query = AccountGroup.objects.exclude(
                id__in=account.accountgroup_set.all())
        else:
            query = AccountGroup.objects.all()

        self.fields['group'] = forms.models.ModelChoiceField(
            queryset=query, required=True, label='')

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column(Field('group', css_class='select2'),
                       css_class='medium-8'),
                Column(Submit('submit_group', 'Add membership',
                              css_class='postfix'),
                       css_class='medium-4')
            )
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
            query, required=True, widget=forms.Select(), label='',
            empty_label='--- Choose account ---')

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column(Field('account', css_class='select2'),
                       css_class='medium-9'),
                Column(Submit('submit_account', 'Add to group',
                              css_class='postfix'),
                       css_class='medium-3')
            )
        )
