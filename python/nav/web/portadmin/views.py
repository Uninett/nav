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
import configparser
import logging
import json

from operator import or_ as OR
from functools import reduce

from django.http import HttpResponse, JsonResponse
from django.template import RequestContext, Context
from django.shortcuts import render, render_to_response, get_object_or_404
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.views.decorators.http import require_POST

from nav.auditlog.models import LogEntry

from nav.django.utils import get_account
from nav.web.utils import create_title
from nav.models.manage import Netbox, Interface
from nav.web.portadmin.utils import (get_and_populate_livedata,
                                     find_and_populate_allowed_vlans,
                                     get_aliastemplate, get_ifaliasformat,
                                     save_to_database,
                                     check_format_on_ifalias,
                                     find_allowed_vlans_for_user_on_netbox,
                                     find_allowed_vlans_for_user,
                                     filter_vlans, fetch_voice_vlans,
                                     should_check_access_rights,
                                     mark_detained_interfaces,
                                     read_config, is_cisco,
                                     add_dot1x_info,
                                     is_restart_interface_enabled,
                                     is_write_mem_enabled, get_trunk_edit)
from nav.Snmp.errors import SnmpError, TimeOutException
from nav.portadmin.snmputils import SNMPFactory, SNMPHandler
from .forms import SearchForm

_logger = logging.getLogger("nav.web.portadmin")


def get_base_context(additional_paths=None, form=None):
    """Returns a base context for portadmin

    :type additional_paths: list of tuple
    """
    navpath = [('Home', '/'), ('PortAdmin', reverse('portadmin-index'))]
    if additional_paths:
        navpath += additional_paths
    form = form if form else SearchForm()
    return {
        'navpath': navpath,
        'title': create_title(navpath),
        'form': form
    }


def default_render(request):
    """Default render for errors etc"""
    return render(request, 'portadmin/base.html',
                  get_base_context(form=get_form(request)))


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
        Q(ip=query)
    ]
    netboxes = Netbox.objects.filter(
        reduce(OR, netbox_filters)).order_by('sysname')
    interfaces = Interface.objects.filter(
        ifalias__icontains=query).order_by('netbox__sysname', 'ifname')
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
        _logger.error("Netbox %s not found; DoesNotExist = %s",
                      kwargs.get('sysname') or kwargs.get('ip'),
                      do_not_exist_ex)
        messages.error(request, 'Could not find IP device')
        return default_render(request)
    else:
        if not netbox.type:
            messages.error(request, 'IP device found but has no type')
            return default_render(request)

        interfaces = netbox.get_swports_sorted()
        if len(interfaces) == 0:
            messages.error(request, 'IP device has no ports (yet)')
            return default_render(request)
        return render(request, 'portadmin/netbox.html',
                      populate_infodict(request, netbox, interfaces))


def search_by_interfaceid(request, interfaceid):
    """View for showing a search done by interface id"""
    try:
        interface = Interface.objects.get(id=interfaceid)
    except Interface.DoesNotExist as do_not_exist_ex:
        _logger.error("Interface %s not found; DoesNotExist = %s",
                      interfaceid, do_not_exist_ex)
        messages.error(request,
                       'Could not find interface with id %s' %
                       str(interfaceid))
        return default_render(request)
    else:
        netbox = interface.netbox
        if not netbox.type:
            messages.error(request, 'IP device found but has no type')
            return default_render(request)

        interfaces = [interface]
        return render(request, 'portadmin/netbox.html',
                      populate_infodict(request, netbox, interfaces))


def populate_infodict(request, netbox, interfaces):
    """Populate a dictionary used in every http response"""
    allowed_vlans = []
    voice_vlan = None
    readonly = False
    config = read_config()

    try:
        fac = get_and_populate_livedata(netbox, interfaces)
        allowed_vlans = find_and_populate_allowed_vlans(
            request.account, netbox, interfaces, fac)
        voice_vlan = fetch_voice_vlan_for_netbox(request, fac, config)
        if voice_vlan:
            if is_cisco_voice_enabled(config) and is_cisco(netbox):
                set_voice_vlan_attribute_cisco(voice_vlan, interfaces, fac)
            else:
                set_voice_vlan_attribute(voice_vlan, interfaces)
        mark_detained_interfaces(interfaces)
        if is_dot1x_enabled:
            add_dot1x_info(interfaces, fac)
    except TimeOutException:
        readonly = True
        messages.error(request, "Timeout when contacting %s. Values displayed "
                                "are from database" % netbox.sysname)
        if not netbox.read_only:
            messages.error(request, "Read only community not set")
    except SnmpError:
        readonly = True
        messages.error(request, "SNMP error when contacting %s. Values "
                                "displayed are from database" % netbox.sysname)

    if check_read_write(netbox, request):
        readonly = True

    ifaliasformat = get_ifaliasformat(config)
    aliastemplate = ''
    if ifaliasformat:
        tmpl = get_aliastemplate()
        aliastemplate = tmpl.render(Context({'ifaliasformat': ifaliasformat}))

    save_to_database(interfaces)

    auditlog_api_parameters = {
        'object_model': 'interface',
        'object_pks': ','.join([str(i.pk) for i in interfaces]),
        'subsystem': 'portadmin'
    }

    info_dict = get_base_context([(netbox.sysname, )], form=get_form(request))
    info_dict.update(
        {
            'interfaces': interfaces,
            'netbox': netbox,
            'voice_vlan': voice_vlan,
            'allowed_vlans': allowed_vlans,
            'readonly': readonly,
            'aliastemplate': aliastemplate,
            'trunk_edit': get_trunk_edit(config),
            'auditlog_api_parameters': json.dumps(auditlog_api_parameters)
        }
    )
    return info_dict


def is_dot1x_enabled(config):
    """Checks of dot1x config option is true"""
    section = 'general'
    option = 'enabledot1x'
    try:
        return (config.has_option(section, option) and
                config.getboolean(section, option))
    except ValueError:
        pass

    return False


def is_cisco_voice_enabled(config):
    """Checks if the Cisco config option is enabled"""
    section = 'general'
    option = 'cisco_voice_vlan'
    if config.has_section(section):
        if config.has_option(section, option):
            return config.getboolean(section, option)
    return False


def fetch_voice_vlan_for_netbox(request, factory, config=None):
    """Fetch the voice vlan for this netbox

    There may be multiple voice vlans configured. Pick the one that exists
    on this netbox. If multiple vlans exist, we cannot know which one to use.

    """
    if config is None:
        config = read_config()

    voice_vlans = fetch_voice_vlans(config)
    if not voice_vlans:
        return

    voice_vlans_on_netbox = list(set(voice_vlans) &
                                 set(factory.get_available_vlans()))
    if not voice_vlans_on_netbox:
        # Should this be reported? At the moment I do not think so.
        return
    if len(voice_vlans_on_netbox) > 1:
        messages.error(request, 'Multiple voice vlans configured on this '
                                'netbox')
        return

    return voice_vlans_on_netbox[0]


def set_voice_vlan_attribute(voice_vlan, interfaces):
    """Set an attribute on the interfaces to indicate voice vlan behavior"""
    if voice_vlan:
        for interface in interfaces:
            if not interface.trunk:
                continue
            allowed_vlans = interface.swportallowedvlan.get_allowed_vlans()
            interface.voice_activated = (len(allowed_vlans) == 1 and
                                         voice_vlan in allowed_vlans)


def set_voice_vlan_attribute_cisco(voice_vlan, interfaces, fac):
    """Set voice vlan attribute for Cisco voice vlan"""
    voice_mapping = fac.get_cisco_voice_vlans()
    for interface in interfaces:
        voice_activated = voice_mapping.get(interface.ifindex) == voice_vlan
        interface.voice_activated = voice_activated


def check_read_write(netbox, request):
    """Add a message to user explaining why he can't edit anything

    :returns: flag indicating readonly or not
    """
    if not netbox.read_write:
        messages.error(request,
                       "Write community not set for this device, "
                       "changes cannot be saved")
        return True
    return False


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
            if interface.vlan in [v.vlan for v in
                                  find_allowed_vlans_for_user_on_netbox(
                                      account, interface.netbox)]:
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
    """Use snmp to set the values in the request on the netbox"""

    fac = get_factory(interface.netbox)

    if fac:
        # Order is important here, set_voice need to be before set_vlan
        set_voice_vlan(fac, interface, request)
        set_ifalias(account, fac, interface, request)
        set_vlan(account, fac, interface, request)
        set_admin_status(fac, interface, request)
        save_to_database([interface])
    else:
        messages.info(request, 'Could not connect to netbox')


def build_ajax_messages(request):
    """Create a structure suitable for converting to json from messages"""
    ajax_messages = []
    for message in messages.get_messages(request):
        ajax_messages.append({
            'level': message.level,
            'message': message.message,
            'extra_tags': message.tags
        })
    return ajax_messages


def set_ifalias(account, fac, interface, request):
    """Set ifalias on netbox if it is requested"""
    if 'ifalias' in request.POST:
        ifalias = request.POST.get('ifalias')
        if check_format_on_ifalias(ifalias):
            try:
                fac.set_if_alias(interface.ifindex, ifalias)
                interface.ifalias = ifalias
                LogEntry.add_log_entry(
                    account,
                    u'set-ifalias',
                    u'{actor}: {object} - ifalias set to "%s"' % ifalias,
                    subsystem=u'portadmin',
                    object=interface,
                )
                _logger.info('%s: %s:%s - ifalias set to "%s"', account.login,
                             interface.netbox.get_short_sysname(),
                             interface.ifname, ifalias)
            except SnmpError as error:
                _logger.error('Error setting ifalias: %s', error)
                messages.error(request, "Error setting ifalias: %s" % error)
        else:
            messages.error(request, "Wrong format on port description")


def set_vlan(account, fac, interface, request):
    """Set vlan on netbox if it is requested"""
    if 'vlan' in request.POST:
        try:
            vlan = int(request.POST.get('vlan'))
        except ValueError:
            messages.error(request, "Ignoring request to set vlan={}".format(
                request.POST.get('vlan')))
            return

        try:
            if is_cisco(interface.netbox):
                # If Cisco and trunk voice vlan (not Cisco voice vlan),
                # we have to set native vlan instead of access vlan
                config = read_config()
                voice_activated = request.POST.get('voice_activated', False)
                if not is_cisco_voice_enabled(config) and voice_activated:
                    fac.set_native_vlan(interface, vlan)
                else:
                    fac.set_vlan(interface, vlan)
            else:
                fac.set_vlan(interface, vlan)

            interface.vlan = vlan
            LogEntry.add_log_entry(
                account,
                u'set-vlan',
                u'{actor}: {object} - vlan set to "%s"' % vlan,
                subsystem=u'portadmin',
                object=interface,
            )
            _logger.info('%s: %s:%s - vlan set to %s', account.login,
                         interface.netbox.get_short_sysname(),
                         interface.ifname, vlan)
        except (SnmpError, TypeError) as error:
            _logger.error('Error setting vlan: %s', error)
            messages.error(request, "Error setting vlan: %s" % error)


def set_voice_vlan(fac, interface, request):
    """Set voicevlan on interface

    A voice vlan is a normal vlan that is defined by the user of NAV as
    a vlan that is used only for ip telephone traffic.

    To set a voice vlan we have to make sure the interface is configured
    to tag both the voicevlan and the "access-vlan".

    """
    if 'voicevlan' in request.POST:
        config = read_config()
        voice_vlan = fetch_voice_vlan_for_netbox(request, fac, config)
        use_cisco_voice_vlan = (is_cisco_voice_enabled(config) and
                                is_cisco(interface.netbox))

        # Either the voicevlan is turned off or turned on
        turn_on_voice_vlan = request.POST.get('voicevlan') == 'true'
        account = get_account(request)
        try:
            if turn_on_voice_vlan:
                if use_cisco_voice_vlan:
                    fac.set_cisco_voice_vlan(interface, voice_vlan)
                else:
                    fac.set_voice_vlan(interface, voice_vlan)
                _logger.info('%s: %s:%s - %s', account.login,
                             interface.netbox.get_short_sysname(),
                             interface.ifname, 'voice vlan enabled')
            else:
                if use_cisco_voice_vlan:
                    fac.disable_cisco_voice_vlan(interface)
                else:
                    fac.set_access(interface, interface.vlan)
                _logger.info('%s: %s:%s - %s', account.login,
                             interface.netbox.get_short_sysname(),
                             interface.ifname, 'voice vlan disabled')
        except (SnmpError, ValueError, NotImplementedError) as error:
            messages.error(request, "Error setting voicevlan: %s" % error)


def set_admin_status(fac, interface, request):
    """Set admin status for the interface
    :type fac: nav.portadmin.snmputils.SNMPFactory
    :type request: django.http.HttpRequest
    """
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
                _logger.info('%s: Setting ifadminstatus for %s to %s',
                             account.login, interface, 'up')
                fac.set_if_up(interface.ifindex)
            elif adminstatus == status_down:
                LogEntry.add_log_entry(
                    account,
                    u'disable-interface',
                    u'{actor} disabled interface {object}',
                    subsystem=u'portadmin',
                    object=interface,
                )
                _logger.info('%s: Setting ifadminstatus for %s to %s',
                             account.login, interface, 'down')
                fac.set_if_down(interface.ifindex)
        except (SnmpError, ValueError) as error:
            messages.error(request, "Error setting ifadminstatus: %s" % error)


def response_based_on_result(result):
    """Return response based on content of result

    result: dict containing result and message keys

    """
    if result['messages']:
        return JsonResponse(result, status=500)
    else:
        return JsonResponse(result)


def render_trunk_edit(request, interfaceid):
    """Controller for rendering trunk edit view"""

    config = read_config()
    interface = Interface.objects.get(pk=interfaceid)
    agent = get_factory(interface.netbox)
    if request.method == 'POST':
        try:
            handle_trunk_edit(request, agent, interface)
        except SnmpError as error:
            messages.error(request, 'Error editing trunk: %s' % error)
        else:
            messages.success(request, 'Trunk edit successful')

    account = request.account
    netbox = interface.netbox
    check_read_write(netbox, request)
    try:
        vlans = agent.get_netbox_vlans()  # All vlans on this netbox
        native_vlan, trunked_vlans = agent.get_native_and_trunked_vlans(
            interface)
    except SnmpError:
        vlans = native_vlan = trunked_vlans = allowed_vlans = None
        messages.error(request, 'Error getting trunk information')
    else:
        if should_check_access_rights(account):
            allowed_vlans = find_allowed_vlans_for_user_on_netbox(
                account, interface.netbox, agent)
        else:
            allowed_vlans = vlans

    extra_path = [(netbox.sysname,
                   reverse('portadmin-sysname',
                           kwargs={'sysname': netbox.sysname})),
                  ("Trunk %s" % interface,)]

    context = get_base_context(extra_path)
    context.update({'interface': interface, 'available_vlans': vlans,
                    'native_vlan': native_vlan, 'trunked_vlans': trunked_vlans,
                    'allowed_vlans': allowed_vlans,
                    'trunk_edit': get_trunk_edit(config)})

    return render_to_response('portadmin/trunk_edit.html',
                              context,
                              RequestContext(request))


def handle_trunk_edit(request, agent, interface):
    """Edit a trunk"""

    native_vlan = int(request.POST.get('native_vlan', 1))
    trunked_vlans = [int(vlan) for vlan in request.POST.getlist('trunk_vlans')]

    if should_check_access_rights(get_account(request)):
        # A user can avoid the form restrictions by sending a forged post
        # request Make sure only the allowed vlans are set

        old_native, old_trunked = agent.get_native_and_trunked_vlans(interface)
        allowed_vlans = [v.vlan for v in
                         find_allowed_vlans_for_user(get_account(request))]

        trunked_vlans = filter_vlans(trunked_vlans, old_trunked, allowed_vlans)
        native_vlan = (native_vlan if native_vlan in allowed_vlans
                       else old_native)

    _logger.info('Interface %s - native: %s, trunk: %s', interface,
                 native_vlan, trunked_vlans)
    LogEntry.add_log_entry(
        request.account,
        u'set-vlan',
        u'{actor}: {object} - native vlan: "%s", trunk vlans: "%s"' % (native_vlan, trunked_vlans),
        subsystem=u'portadmin',
        object=interface,
    )

    if trunked_vlans:
        agent.set_trunk(interface, native_vlan, trunked_vlans)
    else:
        agent.set_access(interface, native_vlan)


@require_POST
def restart_interface(request):
    """Restart the interface by setting admin status to down and up"""
    if not is_restart_interface_enabled():
        _logger.debug('Not doing a restart of interface, it is configured off')
        return HttpResponse()

    interface = get_object_or_404(
        Interface, pk=request.POST.get('interfaceid'))

    fac = get_factory(interface.netbox)
    if fac:
        adminstatus = fac.get_if_admin_status(interface.ifindex)
        if adminstatus == SNMPHandler.IF_ADMIN_STATUS_DOWN:
            _logger.debug('Not restarting %s as it is down', interface)
            return HttpResponse()

        _logger.debug('Restarting interface %s', interface)
        try:
            # Restart interface so that client fetches new address
            fac.restart_if(interface.ifindex)
        except TimeOutException:
            # Swallow this exception as it is not important. Others should
            # create an error
            pass
        return HttpResponse()
    else:
        return HttpResponse(status=500)


@require_POST
def write_mem(request):
    """Do a write mem on the netbox"""
    if not is_write_mem_enabled():
        _logger.debug('Not doing a write mem, it is configured off')
        return HttpResponse("Write mem is configured to not be done")

    interface = get_object_or_404(
        Interface, pk=request.POST.get('interfaceid'))

    fac = get_factory(interface.netbox)
    if fac:
        try:
            fac.write_mem()
        except SnmpError as error:
            error_message = 'Error doing write mem on {}: {}'.format(
                fac.netbox, error)
            _logger.error(error_message)
            return HttpResponse(error_message, status=500)
        except AttributeError:
            error_message = 'Error doing write mem on {}: {}'.format(
                fac.netbox, 'Write to memory not supported')
            _logger.error(error_message)
            return HttpResponse(error_message, status=500)

        return HttpResponse()
    else:
        return HttpResponse(status=500)


def get_factory(netbox):
    """Get a SNMP factory instance"""
    config = read_config()
    timeout = get_config_value(config, 'general', 'timeout', fallback=3)
    retries = get_config_value(config, 'general', 'retries', fallback=3)

    try:
        return SNMPFactory.get_instance(netbox, timeout=timeout,
                                        retries=retries)
    except SnmpError as error:
        _logger.error('Error getting snmpfactory instance %s: %s',
                      netbox, error)


def get_config_value(config, section, key, fallback=None):
    """Get the value of key from a ConfigParser object, with fallback"""
    try:
        return config.get(section, key)
    except (configparser.NoOptionError, configparser.NoSectionError):
        return fallback
