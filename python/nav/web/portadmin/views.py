import simplejson

from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response

from nav.django.utils import get_account
from nav.models.manage import Netbox, Interface
from nav.web.portadmin.utils import *
from nav.portadmin.snmputils import *

NAVBAR = [('Home', '/'), ('PortAdmin', None)]
DEFAULT_VALUES = {'title': "PortAdmin", 'navpath': NAVBAR}

def index(request):
    info_dict = {}
    info_dict.update(DEFAULT_VALUES)
    return render_to_response(
          'portadmin/base.html',
          info_dict,
          RequestContext(request)
          )
    
def search_by_ip(request, ip):
    account = get_account(request)
    netbox = Netbox.objects.get(ip=ip)
    swports = netbox.get_swports_sorted()

    info_dict = populate_infodict(account, netbox, swports)

    return render_to_response(
          'portadmin/portlist.html',
          info_dict,
          RequestContext(request)
          )

def search_by_swportid(request, swportid):
    account = get_account(request)
    swport = Interface.objects.get(id=swportid)
    netbox = swport.netbox
    swports = [swport]

    info_dict = populate_infodict(account, netbox, swports)
    
    return render_to_response(
          'portadmin/portlist.html',
          info_dict,
          RequestContext(request)
          )

def populate_infodict(account, netbox, swports):
    get_and_populate_livedata(netbox, swports)
    allowed_vlans = find_and_populate_allowed_vlans(account, netbox, swports)
    netidents = get_netident_for_vlans(allowed_vlans)

    info_dict = {'swports': swports, 'netbox': netbox, 'allowed_vlans': allowed_vlans,
                 'account': account, 'netidents': netidents }
    info_dict.update(DEFAULT_VALUES)
    
    return info_dict

def save_interfaceinfo(request):
    """
    Used from an ajax call to set ifalias and vlan. Use interfaceid to find connectiondata.
    The call expects error and message to be set.
    Error=0 if everything ok
    Message: message to user
    """
    result = {}


    if request.method == 'POST':
        ifalias = str(request.POST.get('ifalias', '')) # Todo: Why the cast to string?
        vlan = int(request.POST.get('vlan'))
        interfaceid = request.POST.get('interfaceid')

        account = get_account(request)
        if vlan in find_allowed_vlans_for_user(account) or is_administrator(account):
            try:
                interface = Interface.objects.get(id=interfaceid)
                netbox = interface.netbox
                fac = SNMPFactory.getInstance(netbox)
                fac.setVlan(interface.ifindex, vlan)
                fac.setIfAlias(interface.ifindex, ifalias)
                result = {'error': 0, 'message': 'Save was successful'}
            except Exception, e:
                result = {'error': 1, 'message': str(e) }
        else:
            # Should only happen if user tries to avoid gui restrictions
            result = {'error': 1, 'message': "Not allowed to edit this port"}
    else:
        result = {'error': 1, 'message': "Wrong request type"}
        
    return HttpResponse(simplejson.dumps(result), mimetype="application/json")
        