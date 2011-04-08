# -*- coding: utf-8 -*-
#
# Copyright 2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Authors: Fredrik Skolmli <fredrik.skolmli@uninett.no>
#

__copyright__ = "Copyright 2011 UNINETT AS"
__license__ = "GPL"
__author__ = "Trond Kandal <Trond.Kandal@ntnu.no>"
__id__ = "$Id$"

import re
import logging

logger = logging.getLogger("nav.web.threshold.utils")

per_cent_regexp = re.compile('^\d+%$')
sysname_regexp = re.compile('^[\w\-]+([\w\-.]+)*$')
vendor_regexp = re.compile('^\w+$')
ifname_regexp = re.compile('^[a-zA-Z0-9\/\-]+$')
descr_regexp = re.compile('^[a-zA-Z][a-zA-Z\d\ ]+$')

def is_string(to_test):
    if isinstance(to_test, str):
        return True
    if isinstance(to_test, unicode):
        return True
    return False

def is_legal_id(dsid):
    if not is_string(dsid):
        return False
    dsid.strip()
    if not dsid.isdigit():
        return False
    return True

def is_legal_operator(op):
    if not is_string(op):
        return False
    op.strip()
    if op != '<' and op != '>':
        return False
    return True

def is_legal_percent_value(val):
    return (val > -1 and val < 101)

def is_legal_threshold(val, allow_empty=True):
    if not is_string(val):
        return False
    if len(val) == 0:
        if allow_empty:
            return True
        else:
            return False
    val.strip()
    is_per_cent = per_cent_regexp.match(val)
    if is_per_cent:
        val = re.sub('%', '', val)
    if not val.isdigit():
        return False
    val = int(val)
    if is_per_cent:
        if not is_legal_percent_value(val):
            return False
    else:
        if val < 0:
            return False
    return True

def is_legal_interfaceid(id):
    if not is_string(id):
        return False
    id.strip()
    if not id.isdigit():
        return False
    return True

def is_legal_name(name, regexp, allow_empty=True):
    if not is_string(name):
        return False
    if len(name) == 0:
        if allow_empty:
            return True
        else:
            return False
    name.strip()
    if not regexp.match(name):
        return False
    return True

def is_legal_descr(descr, allow_empty=False):
    return is_legal_name(descr, descr_regexp, allow_empty)

def is_legal_sysname(name, allow_empty=True):
    return is_legal_name(name, sysname_regexp, allow_empty)

def is_legal_ifname(ifname, allow_empty=True):
    return is_legal_name(ifname, ifname_regexp, allow_empty)
    
def is_legal_vendor(vendor, allow_empty=True):
    return is_legal_name(vendor, vendor_regexp, allow_empty)

def is_legal_model(model, allow_empty=True):
    return is_legal_name(model, vendor_regexp, allow_empty)

def is_match(to_test, exactmatch, allow_empty=True):
    if not is_string(to_test):
        return False
    if len(to_test) == 0:
        if allow_empty:
            return True
        else:
            return False
    if to_test != exactmatch:
        return False
    return True

def is_legal_gw(gw):
    return is_match(gw, 'GW')

def is_legal_gsw(gsw):
    return is_match(gsw, 'GSW')

def is_legal_sw(sw):
    return is_match(sw, 'SW')

def is_legal_updown(updown):
    return is_match(updown, 'updown')
 
def is_legal_ids(ids, allow_empty=True):
    if not ids:
        if allow_empty:
            return True
        else:
            return False
    for ident in ids.split('|'):
        if not is_legal_id(ident):
            return False
    return True
           
def is_illegal_parameters(account, descr, sysname, vendor, model,
                                        gw, gsw, sw, ifname, updown, boxes):
    if not is_legal_descr(descr):
        logger.error('Illegal description: login=%s; description=%s' %
            (account.login, descr))
        result = {'error': 1, 'message': 'Illegal description'}
        return result

    if not is_legal_sysname(sysname):
        logger.error('Illegal sysname: login=%s; sysname=%s' %
            (account.login, sysname))
        result = {'error': 1, 'message': 'Illegal sysname'}
        return result

    if not is_legal_ifname(ifname):
        logger.error('Illegal ifname: login=%s; ifname=%s' %
            (account.login, ifname))
        result = {'error': 1, 'message': 'Illegal ifname'}
        return result

    if not is_legal_vendor(vendor):
        logger.error('Illegal vendor: login=%s; vendor=%s' %
            (account.login, vendor))
        result = {'error': 1, 'message': 'Illegal vendor'}
        return result

    if not is_legal_model(model):
        logger.error('Illegal model: login=%s; model=%s' %
            (account.login, model))
        result = {'error': 1, 'message': 'Illegal model'}
        return result

    if not is_legal_gw(gw):
        logger.error('Illegal category: login=%s; gw=%s' %
            (account.login, gw))
        result = {'error': 1, 'message': 'Illegal category'}
        return result

    if not is_legal_gsw(gsw):
        logger.error('Illegal category: login=%s; gsw=%s' %
            (account.login, gsw))
        result = {'error': 1, 'message': 'Illegal category'}
        return result

    if not is_legal_sw(sw):
        logger.error('Illegal category: login=%s; sw=%s' %
            (account.login, sw))
        result = {'error': 1, 'message': 'Illegal category'}
        return result

    if not is_legal_updown(updown):
        logger.error('Illegal up/down: login=%s; updown=%s' %
            (account.login, updown))
        result = {'error': 1, 'message': 'Illegal up/down check'}
        return result

    if not is_legal_ids(boxes):
        logger.error('Illegal identity: login=%s; ids=%s' %
            (account.login, boxes))
        result = {'error': 1, 'message': 'Illegal identity'}
        return result
    return None

