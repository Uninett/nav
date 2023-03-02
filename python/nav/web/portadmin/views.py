#
# Copyright (C) 2011-2015 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""View controller for PortAdmin"""
import logging
import json

from operator import or_ as OR
from functools import reduce

from django.http import HttpResponse, JsonResponse, HttpRequest
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from django.views.decorators.http import require_POST

from nav.auditlog.models import LogEntry

from nav.django.utils import get_account
from nav.util import is_valid_ip
from nav.web.utils import create_title
from nav.models.manage import Netbox, Interface
from nav.web.portadmin.utils import (
    get_and_populate_livedata,
    find_and_populate_allowed_vlans,
    get_aliastemplate,
    save_to_database,
    check_format_on_ifalias,
    find_allowed_vlans_for_user_on_netbox,
    find_allowed_vlans_for_user,
    filter_vlans,
    should_check_access_rights,
    mark_detained_interfaces,
    is_cisco,
    add_dot1x_info,
)
from nav.portadmin.config import CONFIG
from nav.portadmin.snmp.base import SNMPHandler
from nav.portadmin.management import ManagementFactory
from nav.portadmin.handlers import (
    ManagementHandler,
    NoResponseError,
    ProtocolError,
    ManagementError,
)
from .forms import SearchForm
from ...portadmin.handlers import DeviceNotConfigurableError

_logger = logging.getLogger("nav.web.portadmin")


def get_base_context(additional_paths=None, form=None):
    """Returns a base context for portadmin

    :type additional_paths: list of tuple
    """
    navpath = [('Home', '/'), ('PortAdmin', reverse('portadmin-index'))]
    if additional_paths:
        navpath += additional_paths
    form = form if form else SearchForm()
    return {'navpath': navpath, 'title': create_title(navpath), 'form': form}


def default_render(request):
    """Default render for errors etc"""
    return render(
        request, 'portadmin/base.html', get_base_context(form=get_form(request))
    )


def get_form(request):
    """If we are searching for something, return a bound form with the
    search parameter"""
    if 'query' in request.GET:
        return SearchForm(request.GET)


def index(request):
    """View for showing main page"""
    netboxes = []
    interfaces = []
    form = get_form(request)
    if form and form.is_valid():
        netboxes, interfaces = search(form.cleaned_data['query'])
        if len(netboxes) == 1 and not interfaces:
            return search_by_sysname(request, netboxes[0].sysname)
        elif len(interfaces) == 1 and not netboxes:
            return search_by_interfaceid(request, interfaces[0].id)
    else:
        form = SearchForm()
    context = get_base_context(form=form)
    context['netboxes'] = netboxes
    context['interfaces'] = interfaces

    return render(request, 'portadmin/base.html', context)


def search(query):
    """Search for something in portadmin"""
    netbox_filters = [
        Q(sysname__icontains=query),
    ]
    if is_valid_ip(query, strict=True):
        netbox_filters.append(Q(ip=query))
    netboxes = Netbox.objects.filter(reduce(OR, netbox_filters)).order_by('sysname')
    interfaces = Interface.objects.filter(ifalias__icontains=query).order_by(
        'netbox__sysname', 'ifname'
    )
    return netboxes, interfaces


def search_by_ip(request, ip):
    """View for showing a search done by ip-address"""
    return search_by_kwargs(request, ip=ip)


def search_by_sysname(request, sysname):
    """View for showing a search done by sysname"""
    return search_by_kwargs(request, sysname=sysname)


def search_by_kwargs(request, **kwargs):
    """Search by keyword arguments"""
    try:
        netbox = Netbox.objects.get(**kwargs)
    except Netbox.DoesNotExist as do_not_exist_ex:
        _logger.error(
            "Netbox %s not found; DoesNotExist = %s",
            kwargs.get('sysname') or kwargs.get('ip'),
            do_not_exist_ex,
        )
        messages.error(request, 'Could not find IP device')
        return default_render(request)
    else:
        if not netbox.type:
            messages.error(request, 'IP device found but has no type')
            return default_render(request)

        interfaces = netbox.get_swports_sorted()
        if not interfaces:
            messages.error(request, 'IP device has no ports (yet)')
            return default_render(request)
        return render(
            request,
            'portadmin/netbox.html',
            populate_infodict(request, netbox, interfaces),
        )


def search_by_interfaceid(request, interfaceid):
    """View for showing a search done by interface id"""
    try:
        interface = Interface.objects.get(id=interfaceid)
    except Interface.DoesNotExist as do_not_exist_ex:
        _logger.error(
            "Interface %s not found; DoesNotExist = %s", interfaceid, do_not_exist_ex
        )
        messages.error(
            request, 'Could not find interface with id %s' % str(interfaceid)
        )
        return default_render(request)
    else:
        netbox = interface.netbox
        if not netbox.type:
            messages.error(request, 'IP device found but has no type')
            return default_render(request)

        interfaces = [interface]
        return render(
            request,
            'portadmin/netbox.html',
            populate_infodict(request, netbox, interfaces),
        )


def populate_infodict(request, netbox, interfaces):
    """Populate a dictionary used in every http response"""
    allowed_vlans = []
    voice_vlan = None
    readonly = False
    handler = None

    try:
        handler = get_and_populate_livedata(netbox, interfaces)
        allowed_vlans = find_and_populate_allowed_vlans(
            request.account, netbox, interfaces, handler
        )
        voice_vlan = fetch_voice_vlan_for_netbox(request, handler)
        if voice_vlan:
            if CONFIG.is_cisco_voice_enabled() and is_cisco(netbox):
                set_voice_vlan_attribute_cisco(voice_vlan, interfaces, handler)
            else:
                set_voice_vlan_attribute(voice_vlan, interfaces)
        mark_detained_interfaces(interfaces)
        if CONFIG.is_dot1x_enabled():
            add_dot1x_info(interfaces, handler)
    except NoResponseError:
        readonly = True
        messages.error(
            request,
            "%s did not respond within the set timeouts. Values displayed are from database"
            % netbox.sysname,
        )
        if isinstance(
            handler, SNMPHandler
        ) and not netbox.get_preferred_snmp_management_profile(writeable=False):
            messages.error(request, "Read only management profile not set")
    except ProtocolError:
        readonly = True
        messages.error(
            request,
            "Protocol error when contacting %s. Values displayed are from database"
            % netbox.sysname,
        )
    except DeviceNotConfigurableError as error:
        readonly = True
        messages.error(request, str(error))

    if handler and not handler.is_configurable():
        add_readonly_reason(request, handler)
        readonly = True

    ifaliasformat = CONFIG.get_ifaliasformat()
    aliastemplate = ''
    if ifaliasformat:
        tmpl = get_aliastemplate()
        aliastemplate = tmpl.render({'ifaliasformat': ifaliasformat})

    save_to_database(interfaces)

    auditlog_api_parameters = {
        'object_model': 'interface',
        'object_pks': ','.join([str(i.pk) for i in interfaces]),
        'subsystem': 'portadmin',
    }

    info_dict = get_base_context([(netbox.sysname,)], form=get_form(request))
    info_dict.update(
        {
            'handlertype': type(handler).__name__,
            'interfaces': interfaces,
            'netbox': netbox,
            'voice_vlan': voice_vlan,
            'allowed_vlans': allowed_vlans,
            'readonly': readonly,
            'aliastemplate': aliastemplate,
            'trunk_edit': CONFIG.get_trunk_edit(),
            'auditlog_api_parameters': json.dumps(auditlog_api_parameters),
        }
    )
    return info_dict


def fetch_voice_vlan_for_netbox(request: HttpRequest, handler: ManagementHandler):
    """Fetch the voice vlan for this netbox

    There may be multiple voice vlans configured. Pick the one that exists
    on this netbox. If multiple vlans exist, we cannot know which one to use.

    """
    voice_vlans = CONFIG.fetch_voice_vlans()
    if not voice_vlans:
        return

    voice_vlans_on_netbox = list(set(voice_vlans) & set(handler.get_netbox_vlan_tags()))
    if not voice_vlans_on_netbox:
        # Should this be reported? At the moment I do not think so.
        return
    if len(voice_vlans_on_netbox) > 1:
        messages.error(request, 'Multiple voice vlans configured on this ' 'netbox')
        return

    return voice_vlans_on_netbox[0]


def set_voice_vlan_attribute(voice_vlan, interfaces):
    """Set an attribute on the interfaces to indicate voice vlan behavior"""
    if voice_vlan:
        for interface in interfaces:
            if not interface.trunk:
                continue
            allowed_vlans = interface.swport_allowed_vlan.get_allowed_vlans()
            interface.voice_activated = (
                len(allowed_vlans) == 1 and voice_vlan in allowed_vlans
            )


def set_voice_vlan_attribute_cisco(voice_vlan, interfaces, handler: ManagementHandler):
    """Set voice vlan attribute for Cisco voice vlan"""
    voice_mapping = handler.get_cisco_voice_vlans()
    for interface in interfaces:
        voice_activated = voice_mapping.get(interface.ifindex) == voice_vlan
        interface.voice_activated = voice_activated


def add_readonly_reason(request: HttpRequest, mgmt_handler: ManagementHandler):
    """Adds a message to the request's session, explaining why this device cannot be
    configured through PortAdmin.
    """
    try:
        mgmt_handler.raise_if_not_configurable()
    except DeviceNotConfigurableError as error:
        messages.error(request, str(error))


def save_interfaceinfo(request):
    """Set ifalias and/or vlan on netbox

    messages: created from the results from the messages framework

    interfaceid must be a part of the request
    ifalias, vlan and voicevlan are all optional

    """
    if request.method == 'POST':
        interface = Interface.objects.get(pk=request.POST.get('interfaceid'))
        account = get_account(request)

        # Skip a lot of queries if access_control is not turned on
        if should_check_access_rights(account):
            _logger.info('Checking access rights for %s', account)
            if interface.vlan in [
                v.vlan
                for v in find_allowed_vlans_for_user_on_netbox(
                    account, interface.netbox
                )
            ]:
                set_interface_values(account, interface, request)
            else:
                # Should only happen if user tries to avoid gui restrictions
                messages.error(request, 'Not allowed to edit this interface')
        else:
            set_interface_values(account, interface, request)
    else:
        messages.error(request, 'Wrong request type')

    result = {"messages": build_ajax_messages(request)}
    return response_based_on_result(result)


def set_interface_values(account, interface, request):
    """Configures an interface according to the values from the request"""

    handler = get_management_handler(interface.netbox)

    if handler:
        # Order is important here, set_voice need to be before set_vlan
        set_voice_vlan(handler, interface, request)
        set_ifalias(account, handler, interface, request)
        set_vlan(account, handler, interface, request)
        set_admin_status(handler, interface, request)
        save_to_database([interface])
    else:
        messages.info(request, 'Could not connect to netbox')


def build_ajax_messages(request):
    """Create a structure suitable for converting to json from messages"""
    ajax_messages = []
    for message in messages.get_messages(request):
        ajax_messages.append(
            {
                'level': message.level,
                'message': message.message,
                'extra_tags': message.tags,
            }
        )
    return ajax_messages


def set_ifalias(account, handler: ManagementHandler, interface, request):
    """Set ifalias on netbox if it is requested"""
    if 'ifalias' in request.POST:
        ifalias = request.POST.get('ifalias')
        if check_format_on_ifalias(ifalias):
            try:
                handler.set_interface_description(interface, ifalias)
                interface.ifalias = ifalias
                LogEntry.add_log_entry(
                    account,
                    u'set-ifalias',
                    u'{actor}: {object} - ifalias set to "%s"' % ifalias,
                    subsystem=u'portadmin',
                    object=interface,
                )
                _logger.info(
                    '%s: %s:%s - ifalias set to "%s"',
                    account.login,
                    interface.netbox.get_short_sysname(),
                    interface.ifname,
                    ifalias,
                )
            except ManagementError as error:
                _logger.error('Error setting port description: %s', error)
                messages.error(request, "Error setting port description: %s" % error)
        else:
            messages.error(request, "Wrong format on port description")


def set_vlan(account, handler: ManagementHandler, interface, request):
    """Set vlan on netbox if it is requested"""
    if 'vlan' in request.POST:
        try:
            vlan = int(request.POST.get('vlan'))
        except ValueError:
            messages.error(
                request,
                "Ignoring request to set vlan={}".format(request.POST.get('vlan')),
            )
            return

        try:
            if is_cisco(interface.netbox):
                # If Cisco and trunk voice vlan (not Cisco voice vlan),
                # we have to set native vlan instead of access vlan
                voice_activated = request.POST.get('voice_activated', False)
                if not CONFIG.is_cisco_voice_enabled() and voice_activated:
                    handler.set_native_vlan(interface, vlan)
                else:
                    handler.set_vlan(interface, vlan)
            else:
                handler.set_vlan(interface, vlan)

            interface.vlan = vlan
            LogEntry.add_log_entry(
                account,
                u'set-vlan',
                u'{actor}: {object} - vlan set to "%s"' % vlan,
                subsystem=u'portadmin',
                object=interface,
            )
            _logger.info(
                '%s: %s:%s - vlan set to %s',
                account.login,
                interface.netbox.get_short_sysname(),
                interface.ifname,
                vlan,
            )
        except (ManagementError, TypeError) as error:
            _logger.error('Error setting vlan: %s', error)
            messages.error(request, "Error setting vlan: %s" % error)


def set_voice_vlan(handler: ManagementHandler, interface, request):
    """Set voicevlan on interface

    A voice vlan is a normal vlan that is defined by the user of NAV as
    a vlan that is used only for ip telephone traffic.

    To set a voice vlan we have to make sure the interface is configured
    to tag both the voicevlan and the "access-vlan".

    """
    if 'voicevlan' in request.POST:
        cdp_changed = False
        voice_vlan = fetch_voice_vlan_for_netbox(request, handler)
        use_cisco_voice_vlan = CONFIG.is_cisco_voice_enabled() and is_cisco(
            interface.netbox
        )
        enable_cdp_for_cisco_voice_port = CONFIG.is_cisco_voice_cdp_enabled()

        # Either the voicevlan is turned off or turned on
        turn_on_voice_vlan = request.POST.get('voicevlan') == 'true'
        account = get_account(request)
        try:
            if turn_on_voice_vlan:
                if use_cisco_voice_vlan:
                    handler.set_cisco_voice_vlan(interface, voice_vlan)
                    if enable_cdp_for_cisco_voice_port:
                        handler.enable_cisco_cdp(interface)
                        cdp_changed = True
                else:
                    handler.set_interface_voice_vlan(interface, voice_vlan)
                _logger.info(
                    '%s: %s:%s - %s%s',
                    account.login,
                    interface.netbox.get_short_sysname(),
                    interface.ifname,
                    'voice vlan enabled',
                    ', CDP enabled' if cdp_changed else '',
                )
            else:
                if use_cisco_voice_vlan:
                    handler.disable_cisco_voice_vlan(interface)
                    if enable_cdp_for_cisco_voice_port:
                        handler.disable_cisco_cdp(interface)
                        cdp_changed = True
                else:
                    handler.set_access(interface, interface.vlan)
                _logger.info(
                    '%s: %s:%s - %s%s',
                    account.login,
                    interface.netbox.get_short_sysname(),
                    interface.ifname,
                    'voice vlan disabled',
                    ', CDP disabled' if cdp_changed else '',
                )
        except (ManagementError, ValueError, NotImplementedError) as error:
            messages.error(request, "Error setting voicevlan: %s" % error)


def set_admin_status(handler: ManagementHandler, interface, request: HttpRequest):
    """Set admin status for the interface"""
    status_up = '1'
    status_down = '2'
    account = request.account

    if 'ifadminstatus' in request.POST:
        adminstatus = request.POST['ifadminstatus']
        try:
            if adminstatus == status_up:
                LogEntry.add_log_entry(
                    account,
                    u'enable-interface',
                    u'{actor} enabled interface {object}',
                    subsystem=u'portadmin',
                    object=interface,
                )
                _logger.info(
                    '%s: Setting ifadminstatus for %s to %s',
                    account.login,
                    interface,
                    'up',
                )
                handler.set_interface_up(interface)
            elif adminstatus == status_down:
                LogEntry.add_log_entry(
                    account,
                    u'disable-interface',
                    u'{actor} disabled interface {object}',
                    subsystem=u'portadmin',
                    object=interface,
                )
                _logger.info(
                    '%s: Setting ifadminstatus for %s to %s',
                    account.login,
                    interface,
                    'down',
                )
                handler.set_interface_down(interface)
        except (ManagementError, ValueError) as error:
            messages.error(request, "Error setting ifadminstatus: %s" % error)


def response_based_on_result(result):
    """Return response based on content of result

    result: dict containing result and message keys

    """
    if result['messages']:
        return JsonResponse(result, status=400)
    else:
        return JsonResponse(result)


def render_trunk_edit(request, interfaceid):
    """Controller for rendering trunk edit view"""

    interface = Interface.objects.get(pk=interfaceid)
    handler = get_management_handler(interface.netbox)
    if request.method == 'POST':
        try:
            handle_trunk_edit(request, handler, interface)
        except ManagementError as error:
            messages.error(request, 'Error editing trunk: %s' % error)
        else:
            messages.success(request, 'Trunk edit successful')

    account = request.account
    netbox = interface.netbox
    add_readonly_reason(request, handler)
    try:
        vlans = handler.get_netbox_vlans()  # All vlans on this netbox
        native_vlan, trunked_vlans = handler.get_native_and_trunked_vlans(interface)
    except ManagementError as error:
        vlans = native_vlan = trunked_vlans = allowed_vlans = None
        messages.error(request, 'Error getting trunk information: {}'.format(error))
    else:
        if should_check_access_rights(account):
            allowed_vlans = find_allowed_vlans_for_user_on_netbox(
                account, interface.netbox, handler
            )
        else:
            allowed_vlans = vlans

    extra_path = [
        (
            netbox.sysname,
            reverse('portadmin-sysname', kwargs={'sysname': netbox.sysname}),
        ),
        ("Trunk %s" % interface,),
    ]

    context = get_base_context(extra_path)
    context.update(
        {
            'interface': interface,
            'available_vlans': vlans,
            'native_vlan': native_vlan,
            'trunked_vlans': trunked_vlans,
            'allowed_vlans': allowed_vlans,
            'trunk_edit': CONFIG.get_trunk_edit(),
            'readonly': not handler.is_configurable(),
        }
    )

    return render(request, 'portadmin/trunk_edit.html', context)


def handle_trunk_edit(request, agent, interface):
    """Edit a trunk"""

    native_vlan = int(request.POST.get('native_vlan', 1))
    trunked_vlans = [int(vlan) for vlan in request.POST.getlist('trunk_vlans')]

    if should_check_access_rights(get_account(request)):
        # A user can avoid the form restrictions by sending a forged post
        # request Make sure only the allowed vlans are set

        old_native, old_trunked = agent.get_native_and_trunked_vlans(interface)
        allowed_vlans = [
            v.vlan for v in find_allowed_vlans_for_user(get_account(request))
        ]

        trunked_vlans = filter_vlans(trunked_vlans, old_trunked, allowed_vlans)
        native_vlan = native_vlan if native_vlan in allowed_vlans else old_native

    _logger.info(
        'Interface %s - native: %s, trunk: %s', interface, native_vlan, trunked_vlans
    )
    LogEntry.add_log_entry(
        request.account,
        u'set-vlan',
        u'{actor}: {object} - native vlan: "%s", trunk vlans: "%s"'
        % (native_vlan, trunked_vlans),
        subsystem=u'portadmin',
        object=interface,
    )

    if trunked_vlans:
        agent.set_trunk(interface, native_vlan, trunked_vlans)
    else:
        agent.set_access(interface, native_vlan)
    if CONFIG.is_commit_enabled():
        agent.commit_configuration()


@require_POST
def restart_interfaces(request):
    """Restart the interface by setting admin status to down and up"""
    if not CONFIG.is_restart_interface_enabled():
        _logger.debug("Not doing a restart of interfaces, it is configured off")
        return HttpResponse()

    interfaceids = request.POST.getlist(
        "interfaceid", request.POST.getlist("interfaceid[]")
    )
    if not interfaceids:
        return HttpResponse(status=400, content=b"Missing interfaceid argument")
    interfaces = Interface.objects.filter(pk__in=interfaceids).select_related("netbox")
    if not interfaces:
        return HttpResponse(status=400, content=b"No interfaces selected")
    netboxes = set(i.netbox for i in interfaces)
    if len(netboxes) > 1:
        return HttpResponse(
            status=400, content=b"Can't restart interfaces from different netboxes"
        )
    netbox = list(netboxes)[0]

    handler = get_management_handler(netbox)
    if handler:
        try:
            # Restart interface so that clients fetch new addresses
            handler.cycle_interfaces(interfaces)
        except NoResponseError:
            # Failures aren't grossly important here, we ignore them
            pass
        return HttpResponse()
    else:
        return HttpResponse(status=500, content=b"Could not create management handler")


@require_POST
def commit_configuration(request):
    """Commit pending config changes to startup config"""
    if not CONFIG.is_commit_enabled():
        _logger.debug('Not doing a configuration commit, it is configured off')
        return HttpResponse("Configuration commit is configured to not be done")

    interface = get_object_or_404(Interface, pk=request.POST.get('interfaceid'))

    handler = get_management_handler(interface.netbox)
    if handler:
        try:
            handler.commit_configuration()
        except ManagementError as error:
            error_message = 'Error committing configuration on {}: {}'.format(
                handler.netbox, error
            )
            _logger.error(error_message)
            return HttpResponse(error_message, status=500)
        except (AttributeError, NotImplementedError):
            error_message = 'Error committing configuration on {}: {}'.format(
                handler.netbox, 'Configuration commit not supported'
            )
            _logger.error(error_message)
            return HttpResponse(error_message, status=500)

        return HttpResponse()
    else:
        return HttpResponse(status=500)


def get_management_handler(netbox: Netbox) -> ManagementHandler:
    """Gets a ManagementHandler instance from the ManagementFactory"""
    timeout = CONFIG.getfloat("general", "timeout", fallback=3)
    retries = CONFIG.getint("general", "retries", fallback=3)

    try:
        return ManagementFactory.get_instance(netbox, timeout=timeout, retries=retries)
    except ManagementError as error:
        _logger.error('Error getting ManagementHandler instance %s: %s', netbox, error)
