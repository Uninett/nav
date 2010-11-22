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
    # Fetch live data from netbox
    handler = SNMPFactory.getInstance(netbox)
    live_ifaliases = create_dict_from_tuplelist(handler.getAllIfAlias())
    live_vlans = create_dict_from_tuplelist(handler.getAllVlans())
    
    update_swports_with_snmpdata(swports, live_ifaliases, live_vlans)
    allowed_vlans = find_allowed_vlans_for_user_on_netbox(account, netbox)    
    
    info_dict = {'swports': swports, 'netbox': netbox, 'allowed_vlans': allowed_vlans }
    info_dict.update(DEFAULT_VALUES)
    
    return render_to_response(
          'portadmin/portlist.html',
          info_dict,
          RequestContext(request)
          )
    
def search_by_swportid(request, swportid):
    swport = Interface.objects.get(id=swportid)
    netbox = swport.netbox

    info_dict = {'swports': [swport], 'netbox': netbox }
    info_dict.update(DEFAULT_VALUES)
    
    return render_to_response(
          'portadmin/portlist.html',
          info_dict,
          RequestContext(request)
          )
