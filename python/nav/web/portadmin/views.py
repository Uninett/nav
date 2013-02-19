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

from django.http import HttpResponse
from django.template import RequestContext, Context
from django.shortcuts import render_to_response

from nav.django.utils import get_account
from nav.models.manage import Netbox, Interface
from nav.web.portadmin.utils import (get_and_populate_livedata,
                                     find_and_populate_allowed_vlans,
                                     get_aliastemplate, get_ifaliasformat,
                                     save_to_database,
                                     check_format_on_ifalias,
                                     is_administrator,
                                     find_allowed_vlans_for_user)
from nav.Snmp.errors import SnmpError
from nav.portadmin.snmputils import SNMPFactory
from nav.bitvector import BitVector

NAVBAR = [('Home', '/'), ('PortAdmin', None)]
DEFAULT_VALUES = {'title': "PortAdmin", 'navpath': NAVBAR}

_logger = logging.getLogger("nav.web.portadmin")


def index(request):
    """View for showing main page"""
    info_dict = {}
    info_dict.update(DEFAULT_VALUES)
    return render_to_response('portadmin/base.html',
                              info_dict,
                              RequestContext(request))


def search_by_ip(request, ip):
    """View for showing a search done by ip-address"""
    errors = []
    info_dict = {}
    account = get_account(request)
    netbox = None
    try:
        netbox = Netbox.objects.get(ip=ip)
    except Netbox.DoesNotExist, do_not_exist_ex:
        netbox = None
        _logger.error("Netbox with ip %s not found; DoesNotExist = %s",
                      ip, do_not_exist_ex)
        errors.append('Could not find netbox with ip-address %s' % str(ip))

    if not netbox:
        info_dict.update(DEFAULT_VALUES)
        info_dict['errors'] = errors
        return render_to_response('portadmin/base.html',
                                  info_dict,
                                  RequestContext(request))
    interfaces = netbox.get_swports_sorted()
    info_dict = populate_infodict(account, netbox, interfaces)
    return render_to_response(
        'portadmin/portlist.html',
        info_dict,
        RequestContext(request))


def search_by_sysname(request, sysname):
    """View for showing a search done by sysname"""
    errors = []
    info_dict = {}
    account = get_account(request)
    netbox = None
    try:
        netbox = Netbox.objects.get(sysname=sysname)
    except Netbox.DoesNotExist, do_not_exist_ex:
        netbox = None
        _logger.error("Netbox %s not found; DoesNotExist = %s",
                      sysname, do_not_exist_ex)
        errors.append('Could not find netbox with sysname %s' % sysname)

    if not netbox:
        info_dict.update(DEFAULT_VALUES)
        info_dict['errors'] = errors
        return render_to_response('portadmin/base.html',
                                  info_dict,
                                  RequestContext(request))
    interfaces = netbox.get_swports_sorted()
    info_dict = populate_infodict(account, netbox, interfaces)
    return render_to_response('portadmin/portlist.html',
                              info_dict,
                              RequestContext(request))


def search_by_interfaceid(request, interfaceid):
    """View for showing a search done by interface id"""
    errors = []
    info_dict = {}
    account = get_account(request)
    interface = None
    try:
        interface = Interface.objects.get(id=interfaceid)
    except Interface.DoesNotExist, do_not_exist_ex:
        interface = None
        _logger.error("Interface %s not found; DoesNotExist = %s",
                      interfaceid, do_not_exist_ex)
        errors.append('Could not find interface with id %s' % str(interfaceid))

    if not interface:
        info_dict.update(DEFAULT_VALUES)
        info_dict['errors'] = errors
        return render_to_response('portadmin/base.html',
                                  info_dict,
                                  RequestContext(request))
    netbox = interface.netbox
    interfaces = [interface]
    info_dict = populate_infodict(account, netbox, interfaces)
    return render_to_response('portadmin/portlist.html',
                              info_dict,
                              RequestContext(request))


def populate_infodict(account, netbox, interfaces):
    """Populate a dictionary used in every http response"""
    errors = []
    allowed_vlans = []
    try:
        get_and_populate_livedata(netbox, interfaces)
        allowed_vlans = find_and_populate_allowed_vlans(account, netbox,
                                                        interfaces)
    except SnmpError:
        errors.append("Timeout when contacting netbox.")
        if not netbox.read_only:
            errors.append("Read only community not set")
            errors.append("Values displayed are from database")
    except Exception, error:
        errors.append(str(error))

    if not netbox.read_write:
        errors.append("Write community not set for this device, "
                      "changes cannot be saved")

    ifaliasformat = get_ifaliasformat()
    aliastemplate = ''
    if ifaliasformat:
        tmpl = get_aliastemplate()
        aliastemplate = tmpl.render(Context({'ifaliasformat': ifaliasformat}))

    save_to_database(interfaces)

    info_dict = {'interfaces': interfaces,
                 'netbox': netbox,
                 'allowed_vlans': allowed_vlans,
                 'account': account,
                 'aliastemplate': aliastemplate,
                 'errors': errors}
    info_dict.update(DEFAULT_VALUES)
    return info_dict


def save_interfaceinfo(request):
    """Set ifalias and/or vlan on netbox

    messages: are returned as a part of the response object. If it is empty
    the response is ok, otherwise an error has occured.

    interfaceid must be a part of the request
    ifalias and vlan are both optional

    """
    messages = []
    if request.method == 'POST':
        interfaceid = request.POST.get('interfaceid')
        interface = Interface.objects.get(pk=interfaceid)
        account = get_account(request)

        if is_allowed_to_edit(interface, account):
            try:
                fac = SNMPFactory.get_instance(interface.netbox)
            except SnmpError, error:
                _logger.error('Error getting snmpfactory instance %s: %s',
                              interface.netbox, error)
                messages.append('Could not connect to netbox')
            else:
                messages.append(set_ifalias(account, fac, interface, request))
                messages.append(set_vlan(account, fac, interface, request))
                write_to_memory(fac)
                save_to_database([interface])
        else:
            # Should only happen if user tries to avoid gui restrictions
            messages.append('Not allowed to edit this interface')
    else:
        messages.append('Wrong request type')

    messages = [x for x in messages if x]
    result = {"messages": messages} if messages else {}
    return response_based_on_result(result)


def is_allowed_to_edit(interface, account):
    """Check is account is allowed to edit interface with this vlan"""
    vlan_numbers = [v.vlan for v in find_allowed_vlans_for_user(account)]
    return interface.vlan in vlan_numbers or is_administrator(account)


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
                return "Error setting ifalias: %s" % error
        else:
            return "Wrong format on ifalias"


def set_vlan(account, fac, interface, request):
    """Set vlan on netbox if it is requested"""
    if 'vlan' in request.POST:
        vlan = int(request.POST.get('vlan'))
        try:
            fac.set_vlan(interface.ifindex, vlan)
            interface.vlan = vlan
            _logger.info('%s: %s:%s - vlan set to %s' % (
                account.login, interface.netbox.get_short_sysname(),
                interface.ifname, vlan))
        except (SnmpError, TypeError), error:
            _logger.error('Error setting vlan: %s', error)
            return "Error setting vlan: %s" % error


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
    if 'messages' in result:
        return HttpResponse(simplejson.dumps(result), status=500,
                            mimetype="application/json")
    else:
        return HttpResponse(simplejson.dumps(result),
                            mimetype="application/json")


def render_trunk_edit(request, interfaceid):
    """Controller for rendering trunk edit view"""

    from nav.portadmin.snmputils import SNMPFactory

    interface = Interface.objects.get(pk=interfaceid)
    agent = SNMPFactory().get_instance(interface.netbox)

    available_vlans = agent.get_available_vlans()
    native_vlan, trunked_vlans = agent.get_native_and_trunked_vlans(interface)

    return render_to_response('portadmin/trunk_edit.html',
                              {'interface': interface,
                               'available_vlans': available_vlans,
                               'native_vlan': native_vlan,
                               'trunked_vlans': trunked_vlans},
                              RequestContext(request))

