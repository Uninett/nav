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

"""Controls add and edit of ip devices"""

# pylint: disable=F0401

import copy
import socket
from socket import error as SocketError
import logging

from django.urls import reverse
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.db import transaction
from django.contrib import messages

from nav.auditlog.models import LogEntry
from nav.models.manage import Netbox, NetboxCategory, NetboxType, NetboxProfile
from nav.models.manage import NetboxInfo, ManagementProfile
from nav.Snmp import Snmp, safestring
from nav.Snmp.errors import SnmpError
from nav.Snmp.profile import get_snmp_session_for_profile
from nav import napalm
from nav.util import is_valid_ip
from nav.web.seeddb import reverse_lazy
from nav.web.seeddb.utils.edit import resolve_ip_and_sysname
from nav.web.seeddb.page.netbox import NetboxInfo as NI
from nav.web.seeddb.page.netbox.forms import NetboxModelForm


_logger = logging.getLogger(__name__)


def log_netbox_change(account, old, new):
    """Log specific user initiated changes to netboxes"""

    # If this is a new netbox
    if not old:
        LogEntry.add_create_entry(account, new)
        return

    # Compare changes from old to new
    attribute_list = [
        'category',
        'ip',
        'room',
        'organization',
    ]
    LogEntry.compare_objects(
        account,
        old,
        new,
        attribute_list,
    )


def netbox_edit(request, netbox_id=None, suggestion=None, action='edit'):
    """Controller for edit or create of netbox"""
    info = NI()
    netbox = None
    copy_url = None
    if netbox_id:
        netbox = get_object_or_404(Netbox, pk=netbox_id)
        if action == 'edit':
            copy_url = reverse_lazy(
                info.copy_url_name, kwargs={'action': 'copy', 'netbox_id': netbox_id}
            )

    if request.method == 'POST':
        if action == 'copy':
            # Remove stuff that should not be copied over
            post = request.POST.copy()
            post.pop('sysname', None)
            post.pop('type', None)
            post.pop('virtual_instance', None)
            form = NetboxModelForm(post)
        else:
            form = NetboxModelForm(request.POST, instance=netbox)
        if form.is_valid():
            old_netbox = copy.deepcopy(netbox)
            netbox = netbox_do_save(form)
            messages.add_message(request, messages.SUCCESS, 'IP Device saved')
            log_netbox_change(request.account, old_netbox, netbox)
            return redirect(reverse('seeddb-netbox-edit', args=[netbox.pk]))
        else:
            messages.add_message(request, messages.ERROR, 'Form was not valid')
    else:
        if suggestion:
            form = NetboxModelForm(instance=netbox, initial={'ip': suggestion})
        else:
            form = NetboxModelForm(instance=netbox)

    page_title = "Add new IP Device"
    if netbox:
        page_title = "Edit IP Device"
        if action == 'copy':
            page_title = "Copy IP Device"
    context = info.template_context
    context.update(
        {
            'object': netbox,
            'form': form,
            'title': page_title,
            '_navpath': [('Edit Device', reverse_lazy('seeddb-netbox-edit'))],
            'sub_active': netbox and {'edit': True} or {'add': True},
            'tab_template': 'seeddb/tabs_generic.html',
            'copy_url': copy_url,
            'copy_title': 'Use this netbox as a template for creating a new netbox',
            'action': action,
        }
    )
    return render(request, 'seeddb/netbox_wizard.html', context)


def get_read_only_variables(request):
    """Fetches read only attributes for an IP-address"""
    ip_address = request.GET.get('ip_address')
    profile_ids = request.GET.getlist('profiles[]')
    profiles = ManagementProfile.objects.filter(id__in=profile_ids)
    _logger.debug(
        "testing management profiles against %s: %r = %r",
        ip_address,
        profile_ids,
        profiles,
    )
    if not profiles:
        raise Http404

    sysname = get_sysname(ip_address)
    netbox_type = None

    result = {p.id: {} for p in profiles}
    for profile in profiles:
        if profile.is_snmp:
            response = get_snmp_read_only_variables(ip_address, profile)
        elif profile.protocol == profile.PROTOCOL_NAPALM:
            response = test_napalm_connectivity(ip_address, profile)
        else:
            response = None

        if response:
            response["name"] = profile.name
            response["url"] = reverse(
                "seeddb-management-profile-edit",
                kwargs={"management_profile_id": profile.id},
            )
            result[profile.id].update(response)
            if response.get("type"):
                netbox_type = response["type"]

    data = {
        'sysname': sysname,
        'netbox_type': netbox_type,
        'profiles': result,
    }
    return JsonResponse(data)


def get_snmp_read_only_variables(ip_address: str, profile: ManagementProfile):
    """Tests and retrieves basic netbox clasification from an SNMP profile"""
    result = {}
    if profile.configuration.get("write"):
        result = snmp_write_test(ip_address, profile)
    else:
        result["type"] = get_type_id(ip_address, profile)
        result["status"] = check_snmp_version(ip_address, profile)
    return result


def snmp_write_test(ip, profile):
    """Tests that an SNMP profile really has write access.

    Tests by fetching sysLocation.0 and setting the same value.  This will fail if
    the device only allows writing to other parts of its mib view.
    """

    testresult = {
        'error_message': '',
        'custom_error': '',
        'status': False,
        'syslocation': '',
    }

    syslocation = '1.3.6.1.2.1.1.6.0'
    value = ''
    try:
        snmp = get_snmp_session_for_profile(profile)(ip)
        value = safestring(snmp.get(syslocation))
        snmp.set(syslocation, 's', value.encode('utf-8'))
    except SnmpError as error:
        testresult['error_message'] = error.args
        testresult['status'] = False
    except UnicodeDecodeError as error:
        testresult['custom_error'] = 'UnicodeDecodeError'
        testresult['error_message'] = error.args
        testresult['status'] = False
    else:
        testresult['status'] = True

    testresult['syslocation'] = value
    return testresult


def check_snmp_version(ip, profile):
    """Check if version of snmp is supported by device"""
    sysobjectid = '1.3.6.1.2.1.1.2.0'
    try:
        snmp = get_snmp_session_for_profile(profile)(ip)
        snmp.get(sysobjectid)
    except Exception:  # pylint: disable=W0703
        return False
    else:
        return True


def test_napalm_connectivity(ip_address: str, profile: ManagementProfile) -> dict:
    """Tests connectivity of a NAPALM profile and returns a status dictionary"""
    try:
        with napalm.connect(ip_address, profile) as device:
            return {"status": True}
    except Exception as error:
        _logger.exception("Could not connect to %s using NAPALM profile", ip_address)
        return {"status": False, "error_message": str(error)}


def get_sysname(ip_address):
    """Get sysname from equipment with the given IP-address"""
    try:
        _, sysname = resolve_ip_and_sysname(ip_address)
        return sysname
    except (SocketError, UnicodeError):
        return None


def get_type_id(ip_addr, profile):
    """Gets the id of the type of the ip_addr"""
    netbox_type = snmp_type(ip_addr, profile)
    if netbox_type:
        return netbox_type.id


def snmp_type(ip_addr, profile: ManagementProfile):
    """Query ip for sysobjectid using form data"""
    snmp = get_snmp_session_for_profile(profile)(ip_addr)
    try:
        sysobjectid = snmp.get('.1.3.6.1.2.1.1.2.0')
    except SnmpError:
        return None
    sysobjectid = str(sysobjectid).lstrip('.')
    try:
        netbox_type = NetboxType.objects.get(sysobjectid=sysobjectid)
        return netbox_type
    except NetboxType.DoesNotExist:
        return None


@transaction.atomic()
def netbox_do_save(form):
    """Save netbox.

    Netboxgroups needs to be set manually because of database structure, thus
    we do a commit=False save first.
    """

    netbox = form.save(commit=False)  # Prevents saving m2m relationships
    netbox.save()

    # Save the function field
    function = form.cleaned_data['function']
    if function:
        try:
            func = NetboxInfo.objects.get(netbox=netbox, variable='function')
        except NetboxInfo.DoesNotExist:
            func = NetboxInfo(netbox=netbox, variable='function', value=function)
        else:
            func.value = function
        func.save()

    # Save the groups
    netboxgroups = form.cleaned_data['groups']
    NetboxCategory.objects.filter(netbox=netbox).delete()
    for netboxgroup in netboxgroups:
        NetboxCategory.objects.create(netbox=netbox, category=netboxgroup)

    # Update the list of management profiles
    current_profiles = set(form.cleaned_data['profiles'])
    old_profiles = set(netbox.profiles.all())
    to_add = current_profiles.difference(old_profiles)
    to_remove = old_profiles.difference(current_profiles)
    for profile in to_remove:
        NetboxProfile.objects.get(netbox=netbox, profile=profile).delete()
    for profile in to_add:
        NetboxProfile(netbox=netbox, profile=profile).save()

    return netbox


def get_address_info(request):
    """Displays a template for the user for manual verification of the
    address"""

    address = request.GET.get('address')
    if address:
        if is_valid_ip(address):
            return JsonResponse({'is_ip': True})

        try:
            address_tuples = socket.getaddrinfo(address, None, 0, socket.SOCK_STREAM)
            sorted_tuples = sorted(
                address_tuples, key=lambda item: socket.inet_pton(item[0], item[4][0])
            )
            addresses = [x[4][0] for x in sorted_tuples]
        except socket.error as error:
            context = {'error': str(error)}
        except UnicodeError as error:
            context = {'error': str(error)}
        else:
            context = {
                'addresses': addresses,
            }

        return JsonResponse(context)
    else:
        return HttpResponse('No address given', status=400)
