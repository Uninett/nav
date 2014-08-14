#
# Copyright 2010 (C) Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""View controller for PortAdmin"""
import simplejson
import logging

from operator import or_ as OR

from django.http import HttpResponse
from django.template import RequestContext, Context
from django.shortcuts import render_to_response
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import Q

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
                                     mark_detained_interfaces)
from nav.Snmp.errors import SnmpError, TimeOutException
from nav.portadmin.snmputils import SNMPFactory
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
        'header': {'name': 'PortAdmin',
                   'description': 'Configure interfaces on ip devices'},
        'navpath': navpath,
        'title': create_title(navpath),
        'form': form
    }


def index(request):
    """View for showing main page"""
    netboxes = []
    interfaces = []
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
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

    return render_to_response('portadmin/base.html',
                              context,
                              RequestContext(request))


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
    info_dict = get_base_context()
    account = get_account(request)
    try:
        netbox = Netbox.objects.get(ip=ip)
    except Netbox.DoesNotExist, do_not_exist_ex:
        _logger.error("Netbox with ip %s not found; DoesNotExist = %s",
                      ip, do_not_exist_ex)
        messages.error(request,
                       'Could not find netbox with ip-address %s' % str(ip))
        return render_to_response('portadmin/base.html',
                                  info_dict,
                                  RequestContext(request))
    else:
        interfaces = netbox.get_swports_sorted()
        info_dict = populate_infodict(request, account, netbox, interfaces)
        return render_to_response(
            'portadmin/netbox.html',
            info_dict,
            RequestContext(request))


def search_by_sysname(request, sysname):
    """View for showing a search done by sysname"""
    info_dict = get_base_context()
    account = get_account(request)
    try:
        netbox = Netbox.objects.get(sysname=sysname)
    except Netbox.DoesNotExist, do_not_exist_ex:
        _logger.error("Netbox %s not found; DoesNotExist = %s",
                      sysname, do_not_exist_ex)
        messages.error(request,
                       'Could not find netbox with sysname %s' % sysname)
        return render_to_response('portadmin/base.html',
                                  info_dict,
                                  RequestContext(request))
    else:
        interfaces = netbox.get_swports_sorted()
        info_dict = populate_infodict(request, account, netbox, interfaces)
        return render_to_response('portadmin/netbox.html',
                                  info_dict,
                                  RequestContext(request))


def search_by_interfaceid(request, interfaceid):
    """View for showing a search done by interface id"""
    info_dict = get_base_context()
    account = get_account(request)
    try:
        interface = Interface.objects.get(id=interfaceid)
    except Interface.DoesNotExist, do_not_exist_ex:
        _logger.error("Interface %s not found; DoesNotExist = %s",
                      interfaceid, do_not_exist_ex)
        messages.error(request,
                       'Could not find interface with id %s' %
                       str(interfaceid))
        return render_to_response('portadmin/base.html',
                                  info_dict,
                                  RequestContext(request))
    else:
        netbox = interface.netbox
        interfaces = [interface]
        info_dict = populate_infodict(request, account, netbox, interfaces)
        return render_to_response('portadmin/netbox.html',
                                  info_dict,
                                  RequestContext(request))


def populate_infodict(request, account, netbox, interfaces):
    """Populate a dictionary used in every http response"""

    allowed_vlans = []
    voice_vlan = None
    readonly = False
    try:
        fac = get_and_populate_livedata(netbox, interfaces)
        allowed_vlans = find_and_populate_allowed_vlans(account, netbox,
                                                        interfaces, fac)
        voice_vlan = fetch_voice_vlan_for_netbox(request, fac)
        mark_detained_interfaces(interfaces)
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

    ifaliasformat = get_ifaliasformat()
    aliastemplate = ''
    if ifaliasformat:
        tmpl = get_aliastemplate()
        aliastemplate = tmpl.render(Context({'ifaliasformat': ifaliasformat}))

    save_to_database(interfaces)

    if voice_vlan:
        set_voice_vlan_attribute(voice_vlan, interfaces)

    info_dict = get_base_context([(netbox.sysname, )])
    info_dict.update({'interfaces': interfaces,
                      'netbox': netbox,
                      'voice_vlan': voice_vlan,
                      'allowed_vlans': allowed_vlans,
                      'account': account,
                      'readonly': readonly,
                      'aliastemplate': aliastemplate})
    return info_dict


def fetch_voice_vlan_for_netbox(request, factory):
    """Fetch the voice vlan for this netbox

    There may be multiple voice vlans configured. Pick the one that exists
    on this netbox. If multiple vlans exist, we cannot know which one to use.

    """
    voice_vlans = fetch_voice_vlans()
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
    try:
        fac = SNMPFactory.get_instance(interface.netbox)
    except SnmpError, error:
        _logger.error('Error getting snmpfactory instance %s: %s',
                      interface.netbox, error)
        messages.info(request, 'Could not connect to netbox')
    else:
        # Order is important here, set_voice need to be before set_vlan
        set_voice_vlan(fac, interface, request)
        set_ifalias(account, fac, interface, request)
        set_vlan(account, fac, interface, request)
        set_admin_status(fac, interface, request)
        write_to_memory(fac)
        save_to_database([interface])


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
                _logger.info('%s: %s:%s - ifalias set to "%s"' % (
                    account.login, interface.netbox.get_short_sysname(),
                    interface.ifname, ifalias))
            except SnmpError, error:
                _logger.error('Error setting ifalias: %s', error)
                messages.error(request, "Error setting ifalias: %s" % error)
        else:
            messages.error(request, "Wrong format on ifalias")


def set_vlan(account, fac, interface, request):
    """Set vlan on netbox if it is requested"""
    if 'vlan' in request.POST:
        vlan = int(request.POST.get('vlan'))

        # If the voice_vlan flag is flagged we need to take some extra care
        voice_activated = request.POST.get('voice_activated', False)
        try:
            # If Cisco and voice vlan, we have to set native vlan instead of
            # access vlan
            if interface.netbox.type.vendor.id == 'cisco' and voice_activated:
                fac.set_native_vlan(interface, vlan)
            else:
                fac.set_vlan(interface.ifindex, vlan)

            interface.vlan = vlan
            _logger.info('%s: %s:%s - vlan set to %s' % (
                account.login, interface.netbox.get_short_sysname(),
                interface.ifname, vlan))
        except (SnmpError, TypeError), error:
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
        voice_vlan = fetch_voice_vlan_for_netbox(request, fac)
        # Either the voicevlan is turned off or turned on
        turn_on_voice_vlan = request.POST.get('voicevlan') == 'true'
        account = get_account(request)
        try:
            if turn_on_voice_vlan:
                _logger.info('%s: %s:%s - %s', account.login,
                             interface.netbox.get_short_sysname(),
                             interface.ifname, 'voice vlan enabled')
                fac.set_voice_vlan(interface, voice_vlan)
            else:
                _logger.info('%s: %s:%s - %s', account.login,
                             interface.netbox.get_short_sysname(),
                             interface.ifname, 'voice vlan disabled')
                fac.set_access(interface, interface.vlan)
        except (SnmpError, ValueError) as error:
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
                _logger.info('%s: Setting ifadminstatus for %s to %s',
                             account.login, interface, 'up')
                fac.set_if_up(interface.ifindex)
            elif adminstatus == status_down:
                _logger.info('%s: Setting ifadminstatus for %s to %s',
                             account.login, interface, 'down')
                fac.set_if_down(interface.ifindex)
        except (SnmpError, ValueError) as error:
            messages.error(request, "Error setting ifadminstatus: %s" % error)


def write_to_memory(fac):
    """Write changes on netbox to memory using snmp"""
    try:
        fac.write_mem()
    except SnmpError, error:
        _logger.error('Error doing write mem on %s: %s' % (fac.netbox, error))


def response_based_on_result(result):
    """Return response based on content of result

    result: dict containing result and message keys

    """
    if result['messages']:
        return HttpResponse(simplejson.dumps(result), status=500,
                            mimetype="application/json")
    else:
        return HttpResponse(simplejson.dumps(result),
                            mimetype="application/json")


def render_trunk_edit(request, interfaceid):
    """Controller for rendering trunk edit view"""

    interface = Interface.objects.get(pk=interfaceid)
    agent = SNMPFactory().get_instance(interface.netbox)
    if request.method == 'POST':
        try:
            handle_trunk_edit(request, agent, interface)
        except SnmpError, error:
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
                    'allowed_vlans': allowed_vlans})

    return render_to_response('portadmin/trunk_edit.html',
                              context,
                              RequestContext(request))


def handle_trunk_edit(request, agent, interface):
    """Edit a trunk"""

    native_vlan = int(request.POST.get('native_vlan'))
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

    if trunked_vlans:
        agent.set_trunk(interface, native_vlan, trunked_vlans)
    else:
        agent.set_access(interface, native_vlan)


def restart_interface(request):
    """Restart the interface by setting admin status to down and up"""
    if request.method == 'POST':
        try:
            interface = Interface.objects.get(
                pk=request.POST.get('interfaceid'))
        except Interface.DoesNotExist:
            return HttpResponse(status=404)

        try:
            fac = SNMPFactory.get_instance(interface.netbox)
        except SnmpError, error:
            _logger.error('Error getting snmpfactory instance when '
                          'restarting interface %s: %s',
                          interface.netbox, error)
            return HttpResponse(status=500)

        # Restart interface so that client fetches new address
        fac.restart_if(interface.ifindex)
        return HttpResponse()

    return HttpResponse(status=400)
