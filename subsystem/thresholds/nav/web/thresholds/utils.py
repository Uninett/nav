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
#

__copyright__ = "Copyright 2011 UNINETT AS"
__license__ = "GPL"
__author__ = "Trond Kandal <Trond.Kandal@ntnu.no>"
__id__ = "$Id$"

import logging

from nav.models.manage import Netbox, Interface
from nav.models.rrd import RrdFile, RrdDataSource

# Thresholds, per cent.
THRESHOLD_MIN = 0
THRESHOLD_MAX = 100

LEGAL_OPERATORS = ['greater', 'equals', 'less']
OPERATORS_MAP = {
    'greater': '>',
    'equals': None,
    'less': '<' }

logger = logging.getLogger("nav.web.thresholds")

def is_legal_interfaceid(interfaceid):
    if not interfaceid:
        return False
    interfaceid.strip()
    return interfaceid.isdigit()

def get_interface(interfaceid):
    if not interfaceid:
        return None
    interfaceid = int(interfaceid)
    interfaces = None
    try :
        interfaces = Interface.objects.filter(id=interfaceid)
    except Exception, e:
        logger.error(e)
        return None
    # One id ==> one interface
    if len(interfaces) != 1:
        logger.error("%d inyterfaces found" % len(interfaces))
        return None
    return interfaces[0]

def get_rrdfiles_objects(interface):
    if not interface:
        return None
    rrd_files = None
    try :
        rrd_files = RrdFile.objects.filter(key='interface',
                                        value=str(interface.id))
    except Exception, e:
        logger.error(e)
        rrd_files = None
    if not rrd_files or len(rrd_files) < 1:
        return None
    return rrd_files

def is_legal_datasourceid(req, datasourceid):
    if not datasourceid:
        return False
    if not datasourceid.isdigit():
        return False
    datasourceid = int(datasourceid.strip())
    return (datasourceid in req._req.session['rrd_data_sources'])

def is_legal_threshold(threshold):
    if not threshold:
        return False
    if not threshold.isdigit():
        return False
    threshold = int(threshold.strip())
    return (threshold >= THRESHOLD_MIN and
                threshold <= THRESHOLD_MAX)

def is_legal_operator(operator):
    if not operator:
        return False
    return (operator in LEGAL_OPERATORS)

def get_operator(op):
    if not op:
        return None
    return OPERATORS_MAP.get(op, None)

def get_rrd_data_sources(rrd_files):
    if not rrd_files:
        return None
    rrd_data_sources = []
    for rrd_file in rrd_files:
        try :
            rrd_data_sources.extend(
                RrdDataSource.objects.filter(rrd_file=rrd_file.id))
        except Exception, e:
            logger.error(e)
    if len(rrd_data_sources) < 1:
        return None
    return rrd_data_sources

def get_rrd_data_source(datasourceid):
    if not datasourceid:
        return None
    datasource = None
    try :
        datasource = RrdDataSource.objects.get(id=datasourceid)
    except Exception, e:
        logger.error(e)
        return None
    return datasource
