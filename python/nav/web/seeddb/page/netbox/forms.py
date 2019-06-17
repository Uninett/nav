#
# Copyright (C) 2011, 2012 Uninett AS
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
"""Forms for seeddb netbox view"""
import logging
from socket import error as SocketError

from django import forms
from django.db.models import Q
from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import (Layout, Row, Column, Submit,
                                            Fieldset, Field, Div, HTML)
from django.utils import six

from nav.django.forms import HStoreField
from nav.web.crispyforms import LabelSubmit, NavButton
from nav.models.manage import Room, Category, Organization, Netbox
from nav.models.manage import NetboxInfo
from nav.web.seeddb.utils.edit import (resolve_ip_and_sysname, does_ip_exist,
                                       does_sysname_exist)
from nav.web.seeddb.forms import create_hierarchy

_logger = logging.getLogger(__name__)


class MyModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    """
    This class only exists to override Django's unwanted default help text
    for ModelMultipleChoiceField
    """
    def __init__(self, *args, **kwargs):
        super(MyModelMultipleChoiceField, self).__init__(*args, **kwargs)
        self.help_text = kwargs.get('help_text', '')


class NetboxModelForm(forms.ModelForm):
    """Modelform for netbox for use in SeedDB"""
    ip = forms.CharField()
    function = forms.CharField(required=False)
    data = HStoreField(label='Attributes', required=False)
    sysname = forms.CharField(required=False)
    virtual_instance = MyModelMultipleChoiceField(
        queryset=Netbox.objects.none(), required=False,
        label='Virtual instances',
        help_text='The list of virtual instances inside this master device')

    class Meta(object):
        model = Netbox
        fields = ['ip', 'room', 'category', 'organization',
                  'groups', 'sysname', 'type', 'data', 'master',
                  'virtual_instance', 'profiles']
        help_texts = {
            'master': 'Select a master device when this IP Device is a virtual'
                      ' instance'
        }

    def __init__(self, *args, **kwargs):
        super(NetboxModelForm, self).__init__(*args, **kwargs)
        self.fields['organization'].choices = create_hierarchy(Organization)

        # Master and instance related queries
        masters = [n.master.pk for n in
                   Netbox.objects.filter(master__isnull=False)]
        self.fields['master'].queryset = self.create_master_query(masters)
        self.fields['virtual_instance'].queryset = self.create_instance_query(masters)

        if self.instance.pk:
            # Set instances that we are master to as initial values
            self.initial['virtual_instance'] = Netbox.objects.filter(
                master=self.instance)

            # Disable fields based on current state
            if self.instance.master:
                self.fields['virtual_instance'].widget.attrs['disabled'] = True
            if self.instance.pk in masters:
                self.fields['master'].widget.attrs['disabled'] = True

            # Set the inital value of the function field
            try:
                netboxinfo = self.instance.info_set.get(variable='function')
            except NetboxInfo.DoesNotExist:
                pass
            else:
                self.fields['function'].initial = netboxinfo.value

        css_class = 'large-4'
        self.helper = FormHelper()
        self.helper.form_action = ''
        self.helper.form_method = 'POST'
        self.helper.form_id = 'seeddb-netbox-form'
        self.helper.layout = Layout(
            Row(
                Column(
                    Fieldset('Inventory',
                             'ip',
                             Div(id='verify-address-feedback'),
                             'room', 'category', 'organization'),
                    css_class=css_class),
                Column(
                    Fieldset('Management profiles',
                             Field('profiles', css_class='select2'),
                             NavButton('check_connectivity',
                                       'Check connectivity',
                                       css_class='check_connectivity')),
                    Fieldset('Collected info',
                             Div('sysname', 'type',
                                 css_class='hide',
                                 css_id='real_collected_fields')),
                    css_class=css_class),
                Column(
                    Fieldset(
                        'Meta information',
                        'function',
                        Field('groups', css_class='select2'),
                        'data',
                        HTML("<a class='advanced-toggle'><i class='fa fa-caret-square-o-right'>&nbsp;</i>Advanced options</a>"),
                        Div(
                            HTML('<small class="alert-box">NB: An IP Device cannot both have a master and have virtual instances</small>'),
                            'master', 'virtual_instance',
                            css_class='advanced'
                        )
                    ),
                    css_class=css_class),
            ),
            Submit('save_ip_device', 'Save IP device')
        )

    def create_instance_query(self, masters):
        """Creates query for virtual instance multiselect"""
        # - Should not see other masters
        # - Should see those we are master for
        # - Should see those who have no master
        queryset = Netbox.objects.exclude(pk__in=masters).filter(
            Q(master=self.instance.pk) | Q(master__isnull=True))

        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        return queryset

    def create_master_query(self, masters):
        """Creates query for master dropdown list"""
        # - Should not set those who have master as master
        queryset = Netbox.objects.filter(master__isnull=True)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        return queryset

    def clean_ip(self):
        """Make sure IP-address is valid"""
        name = self.cleaned_data['ip'].strip()
        try:
            ip, _ = resolve_ip_and_sysname(name)
        except SocketError:
            raise forms.ValidationError("Could not resolve name %s" % name)
        return six.text_type(ip)

    def clean_sysname(self):
        """Resolve sysname if not set"""
        sysname = self.cleaned_data.get('sysname')
        ip = self.cleaned_data.get('ip')
        if ip and not sysname:
            _, sysname = resolve_ip_and_sysname(ip)
        return sysname

    def clean(self):
        """Make sure that categories that require communities has that"""
        cleaned_data = self.cleaned_data
        ip = cleaned_data.get('ip')
        cat = cleaned_data.get('category')
        profiles = cleaned_data.get('profiles')
        _logger.warning("cleaning profiles: %r", profiles)

        if ip:
            try:
                self._check_existing_ip(ip)
            except IPExistsException as ex:
                self._errors['ip'] = self.error_class(ex.message)
                del cleaned_data['ip']

        if cat and cat.req_snmp and not profiles:
            self._errors['readonly_connection_profile'] = self.error_class(
                ["Category %s requires SNMP access." % cat.id])
            del cleaned_data['readonly_connection_profile']

        return cleaned_data

    def _check_existing_ip(self, ip):
        msg = []
        _, sysname = resolve_ip_and_sysname(ip)
        if does_ip_exist(ip, self.instance.pk):
            msg.append("IP (%s) is already in database" % ip)
        if does_sysname_exist(sysname, self.instance.pk):
            msg.append("Sysname (%s) is already in database" % sysname)
        if msg:
            raise IPExistsException(msg)

    def save(self, commit=True):
        netbox = super(NetboxModelForm, self).save(commit)
        instances = self.cleaned_data.get('virtual_instance')

        # Clean up instances
        Netbox.objects.filter(
            master=netbox).exclude(pk__in=instances).update(master=None)

        # Add new instances
        for instance in instances:
            instance.master = netbox
            instance.save()

        return netbox


class NetboxFilterForm(forms.Form):
    """Form for filtering netboxes on the list page"""
    category = forms.ModelChoiceField(
        Category.objects.order_by('id').all(), required=False)
    room = forms.ModelChoiceField(
        Room.objects.order_by('id').all(), required=False)
    organization = forms.ModelChoiceField(
        Organization.objects.order_by('id').all(), required=False)

    def __init__(self, *args, **kwargs):
        super(NetboxFilterForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = ''
        self.helper.form_method = 'GET'
        self.helper.form_class = 'custom'

        self.helper.layout = Layout(
            Fieldset(
                'Filter devices',
                Row(
                    Column('category', css_class='medium-3'),
                    Column('room', css_class='medium-3'),
                    Column('organization', css_class='medium-3'),
                    Column(LabelSubmit('submit', 'Filter',
                                       css_class='postfix'),
                           css_class='medium-3')
                )
            )
        )


class NetboxMoveForm(forms.Form):
    """Form for moving netboxes to another room and/or organization"""
    room = forms.ModelChoiceField(
        Room.objects.order_by('id').all(), required=False)
    organization = forms.ModelChoiceField(
        Organization.objects.order_by('id').all(), required=False)


class IPExistsException(Exception):
    """Exception raised when a device with the same IP-address exists"""
    pass
