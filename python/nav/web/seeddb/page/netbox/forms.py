#
# Copyright (C) 2011, 2012 UNINETT AS
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

from socket import error as SocketError
from django import forms
from django.db.models import Q

from nav.models.manage import Room, Category, Organization, Netbox
from nav.models.manage import Subcategory, NetboxCategory
from nav.Snmp import Snmp, TimeOutException, SnmpError
from nav.web.seeddb.utils.edit import resolve_ip_and_sysname, does_ip_exist
from nav.web.seeddb.utils.edit import does_sysname_exist

READONLY_WIDGET_ATTRS = {
    'readonly': 'readonly',
    'class': 'readonly',
}

class NetboxForm(forms.Form):
    id = forms.IntegerField(
        required=False, widget=forms.HiddenInput)
    ip = forms.CharField()
    room = forms.ModelChoiceField(queryset=Room.objects.order_by('id'))
    category = forms.ModelChoiceField(queryset=Category.objects.all())
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.order_by('id'))
    read_only = forms.CharField(required=False)
    read_write = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        self.sysname = None
        self.snmp_version = '1'
        super(NetboxForm, self).__init__(*args, **kwargs)

    def clean_ip(self):
        name = self.cleaned_data['ip'].strip()
        try:
            ip, sysname = resolve_ip_and_sysname(name)
        except SocketError:
            raise forms.ValidationError("Could not resolve name %s" % name)
        self.sysname = sysname
        return unicode(ip)

    def clean(self):
        cleaned_data = self.cleaned_data
        netboxid = cleaned_data.get('id')
        ip = cleaned_data.get('ip')
        cat = cleaned_data.get('category')
        ro_community = cleaned_data.get('read_only')
        rw_community = cleaned_data.get('read_write')
        self.snmp_version = '1'

        if ip:
            try:
                self._check_existing_ip(ip, netboxid)
            except IPExistsException, ex:
                self._errors['ip'] = self.error_class(ex.message)
                del cleaned_data['ip']

        if cat and cat.req_snmp and not ro_community:
            self._errors['read_only'] = self.error_class(
                ["Category %s requires SNMP access." % cat.id])
            del cleaned_data['category']
            del cleaned_data['read_only']

        if ro_community and ip:
            try:
                self._check_ro_community(ip, ro_community, cat)
            except SNMPException, ex:
                self._errors['read_only'] = self.error_class(ex.message)
                del cleaned_data['read_only']

        if rw_community and ip:
            try:
                self._check_rw_community(ip, rw_community)
            except SNMPException, ex:
                self._errors['read_write'] = self.error_class(ex.message)
                del cleaned_data['read_write']

        return cleaned_data

    def _check_existing_ip(self, ip, netboxid):
        msg = []
        if does_ip_exist(ip, netboxid):
            msg.append("IP (%s) is already in database" % ip)
        if does_sysname_exist(self.sysname, netboxid):
            msg.append("Sysname (%s) is already in database" % self.sysname)
        if len(msg) > 0:
            raise IPExistsException(msg)

    def _check_ro_community(self, ip, ro_community, cat):
        non_req_message = (
            "SNMP is not required for this category, if you don't "
            "need SNMP please leave the 'Read only' field empty.")

        try:
            version = self.get_snmp_version(ip, ro_community)
        except Exception, error:
            msg = ("Unhandled exception occurred during SNMP "
                   "communication: %s." % error)
            if cat and not cat.req_snmp:
                msg = (msg, non_req_message)
            else:
                msg = (msg,)
            raise SNMPException(msg)

        if not version:
            if cat and cat.req_snmp:
                msg = (
                    "No SNMP response on read only community.",
                    "Is read only community correct?")
            else:
                msg = (
                    "No SNMP response on read only community.",
                    non_req_message)
            raise ROCommunityException(msg)
        else:
            self.snmp_version = version

    def _check_rw_community(self, ip, rw_community):
        location = self.get_and_set_syslocation(ip, rw_community)
        if not location:
            msg = (
                "No SNMP response on read/write community.",
                "Is read/write community correct?")
            raise RWCommunityException(msg)

    @staticmethod
    def get_snmp_version(ip, community):
        sysobjectid = '1.3.6.1.2.1.1.2.0'
        try:
            try:
                snmp = Snmp(ip, community, '2c')
                snmp.get(sysobjectid)
                snmp_version = '2c'
            except Exception:
                snmp = Snmp(ip, community, '1')
                snmp.get(sysobjectid)
                snmp_version = '1'
        except SnmpError:
            return None
        else:
            return snmp_version

    @staticmethod
    def get_and_set_syslocation(ip, community):
        syslocation = '1.3.6.1.2.1.1.6.0'
        try:
            try:
                snmp = Snmp(ip, community, '2c')
                value = snmp.get(syslocation)
                snmp.set(syslocation, 's', value)
            except TimeOutException:
                snmp = Snmp(ip, community, '1')
                value = snmp.get(syslocation)
                snmp.set(syslocation, 's', value)
        except SnmpError:
            return None
        else:
            return True


class NetboxReadonlyForm(NetboxForm):
    sysname = forms.CharField()
    netbox_type = forms.CharField(required=False)
    type = forms.IntegerField(required=False,
        widget=forms.HiddenInput)
    snmp_version = forms.IntegerField(
        widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super(NetboxReadonlyForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if field in ('id', 'type'):
                continue
            self.fields[field].widget = forms.TextInput(
                attrs=READONLY_WIDGET_ATTRS)

class NetboxSerialForm(forms.Form):
    serial = forms.CharField(required=False)
    function = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        self.netbox_id = kwargs.pop('netbox_id', None)
        super(NetboxSerialForm, self).__init__(*args, **kwargs)
        initial = kwargs.get('initial')
        if initial and initial.get('serial'):
            self.fields['serial'].widget = forms.TextInput(
                attrs=READONLY_WIDGET_ATTRS)

    def clean_serial(self):
        serial = self.cleaned_data['serial']
        try:
            if self.netbox_id:
                netbox = Netbox.objects.get(
                    Q(device__serial=serial),
                    ~Q(id=self.netbox_id))
            else:
                netbox = Netbox.objects.get(device__serial=serial)
        except Netbox.DoesNotExist:
            return serial
        else:
            raise forms.ValidationError(
                "Serial (%s) is already taken by %s" % (serial, netbox))

class NetboxSubcategoryForm(forms.Form):
    def __init__(self, *args, **kwargs):
        queryset = kwargs.pop('queryset')
        super(NetboxSubcategoryForm, self).__init__(*args, **kwargs)
        self.fields['subcategories'] = forms.ModelMultipleChoiceField(
            queryset=queryset, required=False)

def get_netbox_subcategory_form(category, netbox_id=None, post_data=None):
    subcat = Subcategory.objects.filter(category=category).order_by('id')
    if subcat.count() > 0:
        if netbox_id and not post_data:
            subcats = NetboxCategory.objects.filter(
                netbox=netbox_id).values_list('category', flat=True)
            initial = {'subcategories': subcats}
            return NetboxSubcategoryForm(queryset=subcat, initial=initial)
        elif post_data:
            return NetboxSubcategoryForm(post_data, queryset=subcat)
        else:
            return NetboxSubcategoryForm(queryset=subcat)
    else:
        return None

class SNMPException(Exception):
    pass

class SNMPCommunityException(SNMPException):
    pass

class ROCommunityException(SNMPCommunityException):
    pass

class RWCommunityException(SNMPCommunityException):
    pass

class IPExistsException(Exception):
    pass
