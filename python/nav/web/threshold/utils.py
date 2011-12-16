#
# Copyright 2011 UNINETT AS
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

import re
import logging

logger = logging.getLogger("nav.web.threshold.utils")

PER_CENT_REGEXP = re.compile('^\d+%$', re.UNICODE)
SYSNAME_REGEXP = re.compile('^[\w\-]+([\w\-.]+)*$', re.UNICODE)
VENDOR_REGEXP = re.compile('^\w+$', re.UNICODE)
IFNAME_REGEXP = re.compile('^[a-zA-Z0-9\/\-]+$', re.UNICODE)
DESCR_REGEXP = re.compile('^[a-zA-Z][a-zA-Z\d\ ]+$', re.UNICODE)

def is_string(to_test):
    """Check if the parameter is a string or an unicode-string"""
    if isinstance(to_test, str):
        return True
    if isinstance(to_test, unicode):
        return True
    return False

def is_legal_id(ds_id):
    """Check if the id is a legal id (integer)"""
    if not is_string(ds_id):
        return False
    ds_id.strip()
    if not ds_id.isdigit():
        return False
    return True

def is_legal_operator(operator):
    """An operator should be either '>' or '<'"""
    if not is_string(operator):
        return False
    operator.strip()
    if operator != '<' and operator != '>':
        return False
    return True

def is_percent_value(val):
    return PER_CENT_REGEXP.match(val)

def is_legal_percent_value(value):
    """A per-cent value is between 0 - 100"""
    return (value > -1 and value < 101)

def is_legal_threshold(value, allow_empty=True):
    """A threshold is an inteeger with or without a pre-cent sign"""
    if not is_string(value):
        return False
    if len(value) == 0:
        if allow_empty:
            return True
        else:
            return False
    value.strip()
    is_per_cent = is_percent_value(value)
    if is_per_cent:
        value = re.sub('%', '', value)
    try:
        value = int(value)
    except ValueError, val_err:
        return False
    if is_per_cent:
        if not is_legal_percent_value(value):
            return False
    return True

def is_legal_interfaceid(interface_id):
    """Check if the parameter is a legal interface-identifier"""
    if not is_string(interface_id):
        return False
    interface_id.strip()
    if not interface_id.isdigit():
        return False
    return True

def is_legal_netboxid(netbox_id):
    return is_legal_interfaceid

def is_legal_name(name, regexp, allow_empty=True):
    """Check if a name conforms to the give regular expression"""
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
    """Check if descr is a legal threshold-description"""
    return is_legal_name(descr, DESCR_REGEXP, allow_empty)

def is_legal_sysname(name, allow_empty=True):
    """Is a legal dns-name for a netbox"""
    return is_legal_name(name, SYSNAME_REGEXP, allow_empty)

def is_legal_ifname(ifname, allow_empty=True):
    """Is a legal interface-name"""
    return is_legal_name(ifname, IFNAME_REGEXP, allow_empty)
    
def is_legal_vendor(vendor, allow_empty=True):
    """Is a legal vendor-name for a netbox"""
    return is_legal_name(vendor, VENDOR_REGEXP, allow_empty)

def is_legal_model(model, allow_empty=True):
    """Is a legal model-name for a netbox"""
    return is_legal_name(model, VENDOR_REGEXP, allow_empty)

def is_match(to_test, exactmatch, allow_empty=True):
    """Test if a given value has an exact match"""
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

def is_legal_gw(cat_gw):
    """Check if the string has value 'GW'"""
    return is_match(cat_gw, 'GW')

def is_legal_gsw(cat_gsw):
    """Check if the string has value 'GSW'"""
    return is_match(cat_gsw, 'GSW')

def is_legal_sw(cat_sw):
    """Check if the string has value 'SW'"""
    return is_match(cat_sw, 'SW')

def is_legal_updown(updown):
    """Check if the string has value 'updown'"""
    return is_match(updown, 'updown')
 
def is_legal_ids(ids, allow_empty=True):
    """Check if the ids are in the expected format"""
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
                            cat_gw, cat_gsw, cat_sw, ifname, updown, boxes):
    """Actually convinience wrapper to check all parameters at once"""
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

    if not is_legal_gw(cat_gw):
        logger.error('Illegal category: login=%s; gw=%s' %
            (account.login, cat_gw))
        result = {'error': 1, 'message': 'Illegal category'}
        return result

    if not is_legal_gsw(cat_gsw):
        logger.error('Illegal category: login=%s; gsw=%s' %
            (account.login, cat_gsw))
        result = {'error': 1, 'message': 'Illegal category'}
        return result

    if not is_legal_sw(cat_sw):
        logger.error('Illegal category: login=%s; sw=%s' %
            (account.login, cat_sw))
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

