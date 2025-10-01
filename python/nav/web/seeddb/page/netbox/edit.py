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

import copy
import socket
from socket import error as SocketError
import logging

from django.db import transaction
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST

from nav.auditlog.models import LogEntry
from nav.models.manage import Netbox, NetboxCategory, NetboxType, NetboxProfile
from nav.models.manage import NetboxInfo, ManagementProfile
from nav.Snmp import safestring
from nav.Snmp.errors import SnmpError
from nav.Snmp.profile import get_snmp_session_for_profile
from nav import napalm
from nav.util import is_valid_ip
from nav.web.auth.utils import get_account
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
            account = get_account(request)
            log_netbox_change(account, old_netbox, netbox)
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


@require_POST
def check_connectivity(request):
    """
    HTMX endpoint to validate an IP address or hostname and
    associated management profiles.

    - Checks if both IP address and management profiles are provided.
    - If the IP is invalid, attempts to resolve it as a hostname and
      prompts for address selection.
    - If the IP is valid, returns a loading status to trigger connectivity tests.
    """

    ip_address = request.POST.get('ip', '').strip()
    profile_ids = request.POST.getlist('profiles')

    if not (ip_address and profile_ids):
        return render(
            request,
            'seeddb/_seeddb_check_connectivity_response.html',
            {
                'status': 'error',
                'message': (
                    'We need an IP-address and at least one management profile '
                    'to talk to the device.'
                ),
            },
        )

    if not is_valid_ip(ip_address, strict=True):
        return _handle_invalid_ip(request, ip_address)

    return render(
        request,
        'seeddb/_seeddb_check_connectivity_response.html',
        {
            'status': 'loading',
        },
    )


def _handle_invalid_ip(request: HttpRequest, ip_address: str):
    """
    Handle the case where the given IP address is not valid.

    Attempts to resolve it as a hostname and returns the results.
    """
    try:
        address_tuples = socket.getaddrinfo(ip_address, None, 0, socket.SOCK_STREAM)
        sorted_tuples = sorted(
            address_tuples, key=lambda item: socket.inet_pton(item[0], item[4][0])
        )
        addresses = [x[4][0] for x in sorted_tuples]
    except (socket.error, UnicodeError) as error:
        context = {
            'status': 'error',
            'message': str(error),
        }
    else:
        context = {
            'status': 'select-address',
            'addresses': addresses,
            'hostname': ip_address,
        }

    return render(
        request,
        'seeddb/_seeddb_check_connectivity_response.html',
        context,
    )


@require_POST
def load_connectivity_test_results(request):
    """
    HTMX endpoint to perform connectivity tests for given management profiles.

    Returns test results, including sysname and netbox type, grouped by
    success or failure.
    """

    ip_address = request.POST.get('ip')
    profile_ids = request.POST.getlist('profiles')
    profiles = ManagementProfile.objects.filter(id__in=profile_ids)
    _logger.debug(
        "testing management profiles against %s: %r = %r",
        ip_address,
        profile_ids,
        profiles,
    )
    if not profiles:
        return render(
            request,
            'seeddb/_seeddb_check_connectivity_results.html',
        )

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
            result[profile.id].update(
                {
                    "id": profile.id,
                    "name": profile.name,
                    "status": False,
                    "error_message": (
                        "Connectivity check not supported for profile with",
                        f"protocol {profile.get_protocol_display()}",
                    ),
                }
            )

        if response:
            response["id"] = profile.id
            response["name"] = profile.name
            response["url"] = reverse(
                "seeddb-management-profile-edit",
                kwargs={"management_profile_id": profile.id},
            )
            result[profile.id].update(response)
            if response.get("type"):
                netbox_type = response["type"]

    # split result by status for better display: status True and False
    success_profiles = [p for p in result.values() if p.get('status')]
    failed_profiles = [p for p in result.values() if not p.get('status')]

    data = {
        'sysname': sysname,
        'netbox_type': netbox_type,
        'profiles': {
            'succeeded': success_profiles,
            'failed': failed_profiles,
        },
    }
    return render(
        request,
        'seeddb/_seeddb_check_connectivity_results.html',
        data,
    )


def get_snmp_read_only_variables(ip_address: str, profile: ManagementProfile):
    """Tests and retrieves basic netbox clasification from an SNMP profile"""
    result = {}
    if profile.configuration.get("write"):
        result = snmp_write_test(ip_address, profile)
    else:
        result["type"] = get_netbox_type(ip_address, profile)
        result["status"] = check_snmp_version(ip_address, profile)
        if not result["status"]:
            result["error_message"] = "SNMP connection failed"
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
        testresult['error_message'] = error.args[0]
        testresult['status'] = False
    except UnicodeDecodeError as error:
        _logger.exception(
            "Could not decode SNMP response for profile %s with address %s: %s",
            profile.name,
            ip,
            error,
        )
        testresult['custom_error'] = 'UnicodeDecodeError'
        testresult['error_message'] = 'Could not decode SNMP response'
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
    except Exception:  # noqa: BLE001
        return False
    else:
        return True


def test_napalm_connectivity(ip_address: str, profile: ManagementProfile) -> dict:
    """Tests connectivity of a NAPALM profile and returns a status dictionary"""
    try:
        with napalm.connect(ip_address, profile):
            return {"status": True}
    except Exception as error:  # noqa: BLE001
        _logger.exception("Could not connect to %s using NAPALM profile", ip_address)
        error_message = str(error)
        if error_message == 'None':
            error_message = 'Connection failed'
        return {"status": False, "error_message": error_message}


def get_sysname(ip_address):
    """Get sysname from equipment with the given IP-address"""
    try:
        _, sysname = resolve_ip_and_sysname(ip_address)
        return sysname
    except (SocketError, UnicodeError):
        return None


def get_netbox_type(ip_addr, profile):
    """Gets the netbox type of the ip_addr"""
    netbox_type = snmp_type(ip_addr, profile)
    return netbox_type


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
    elif function == '':
        NetboxInfo.objects.filter(netbox=netbox, variable='function').delete()

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


def validate_ip_address(request):
    """Endpoint to check if an address is a valid IP address"""
    address = request.GET.get('address')
    if not address or not is_valid_ip(address.strip(), strict=True):
        return HttpResponse(status=400)
    return HttpResponse(status=200)
