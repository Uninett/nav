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
from nav.Snmp.errors import TimeOutException
from nav.portadmin.snmputils import SNMPFactory

NAVBAR = [('Home', '/'), ('PortAdmin', None)]
DEFAULT_VALUES = {'title': "PortAdmin", 'navpath': NAVBAR}

_logger = logging.getLogger("nav.web.portadmin")


def index(request):
    """View for showing main page"""
    info_dict = {}
    info_dict.update(DEFAULT_VALUES)
    return render_to_response(
        'portadmin/base.html',
        info_dict,
        RequestContext(request)
    )


def search_by_ip(request, ip):
    """View for showing a search done by ip-address"""
    account = get_account(request)
    netbox = Netbox.objects.get(ip=ip)
    interfaces = netbox.get_swports_sorted()

    info_dict = populate_infodict(account, netbox, interfaces)

    return render_to_response(
        'portadmin/portlist.html',
        info_dict,
        RequestContext(request)
    )


def search_by_sysname(request, sysname):
    """View for showing a search done by sysname"""
    account = get_account(request)
    netbox = Netbox.objects.get(sysname=sysname)
    interfaces = netbox.get_swports_sorted()

    info_dict = populate_infodict(account, netbox, interfaces)

    return render_to_response(
        'portadmin/portlist.html',
        info_dict,
        RequestContext(request)
    )


def search_by_interfaceid(request, interfaceid):
    """View for showing a search done by interface id"""
    account = get_account(request)
    interface = Interface.objects.get(id=interfaceid)
    netbox = interface.netbox
    interfaces = [interface]

    info_dict = populate_infodict(account, netbox, interfaces)

    return render_to_response(
        'portadmin/portlist.html',
        info_dict,
        RequestContext(request)
    )


def populate_infodict(account, netbox, interfaces):
    """Populate a dictionary used in every http response"""
    errors = []
    allowed_vlans = []
    try:
        get_and_populate_livedata(netbox, interfaces)
        allowed_vlans = find_and_populate_allowed_vlans(account, netbox,
                                                        interfaces)
    except TimeOutException:
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

    info_dict = {'interfaces': interfaces, 'netbox': netbox,
                 'allowed_vlans': allowed_vlans,
                 'account': account,
                 'aliastemplate': aliastemplate, 'errors': errors}
    info_dict.update(DEFAULT_VALUES)

    return info_dict


def save_interfaceinfo(request):
    """Used from an ajax call to set ifalias and vlan.

    Message: message to user

    Use interfaceid to find connectiondata. The call expects error and
    message to be set. Error=0 if everything ok

    """
    if request.method == 'POST':
        ifalias = str(request.POST.get('ifalias', ''))
        vlan = int(request.POST.get('vlan'))
        interfaceid = request.POST.get('interfaceid')

        correct_format = check_format_on_ifalias(ifalias)
        if not correct_format:
            result = {'error': 1,
                      'message': 'IfAlias does not match the defined format.'}
            return HttpResponse(simplejson.dumps(result),
                                mimetype="application/json")

        account = get_account(request)
        vlan_numbers = [v.vlan for v in find_allowed_vlans_for_user(account)]
        if vlan in vlan_numbers or is_administrator(account):
            try:
                interface = Interface.objects.get(id=interfaceid)
                netbox = interface.netbox
                fac = SNMPFactory.getInstance(netbox)
                fac.setVlan(interface.ifindex, vlan)
                fac.setIfAlias(interface.ifindex, ifalias)
                try:
                    fac.write_mem()
                except:
                    pass
                result = {'error': 0, 'message': 'Save was successful'}

                interface.vlan = vlan
                interface.ifalias = ifalias
                save_to_database([interface])

                _logger.info(
                    "%s: %s:%s - port description set to %s, vlan set to %s",
                    account.login,
                    netbox.get_short_sysname(),
                    interface.ifname,
                    ifalias,
                    vlan)
            except TimeOutException:
                result = {'error': 1,
                          'message': 'TimeOutException - is read-write '
                                     'community set?'}
            except Exception, error:
                result = {'error': 1, 'message': str(error)}
        else:
            # Should only happen if user tries to avoid gui restrictions
            result = {'error': 1, 'message': "Not allowed to edit this port"}
    else:
        result = {'error': 1, 'message': "Wrong request type"}

    return HttpResponse(simplejson.dumps(result), mimetype="application/json")
