#
# Copyright 2011 (C) UNINETT AS
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
import simplejson
import logging

from django.http import HttpResponse
from django.template import RequestContext
from django.template import Context
from django.shortcuts import render_to_response

from nav.django.utils import get_account
from nav.models.manage import Netbox
from nav.models.manage import PowerSupply

NAVBAR = [('Home', '/'), ('PowerSupplies', None)]
DEFAULT_VALUES = {'title': "PowerSupplies", 'navpath': NAVBAR}

logger = logging.getLogger("nav.web.powersupplies")

def index(request):
    info_dict = {}
    headers = ['Netbox', 'IP', 'Power-supply module', 'Model', 'Description', 'State', 'Down since',]
    info_dict['headers'] = headers
    info_dict['account'] = get_account(request)
    info_dict['states'] = PowerSupply.objects.all().order_by('netbox')
    info_dict.update(DEFAULT_VALUES)
    return render_to_response(
          'powersupplies/index.html',
          info_dict,
          RequestContext(request)
          )
