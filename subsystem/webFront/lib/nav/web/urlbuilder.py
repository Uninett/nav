# -*- coding: ISO8859-1 -*-
# $Id$
#
# Copyright 2003, 2004 Norwegian University of Science and Technology
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
# Authors: Stian S�iland <stain@itea.ntnu.no>
#
"""
Generate URLs to different parts of NAV based
on different criteria.
"""

import forgetHTML as html
import forgetSQL
from nav.db import manage

_subsystems = {
    'devbrowser': '/browse',
    'report': '/report',
    'rrd': '/browse/rrd',
    'seeddb': '/seeddb',
    'maintenance':'/maintenance',
}

_divisionClasses = {
    'service': manage.Service,
    'room': manage.Room,
    'org': manage.Org,
    'netbox': manage.Netbox,
    'cat': manage.Cat,
    'type': manage.Type,
    'location': manage.Location,
    'port': manage.Swport,
    'gwport': manage.Gwport,
    'module': manage.Module,
    'vlan':  manage.Vlan,
    'prefix': manage.Prefix,
}

def _getObjectByDivision(division, id):
    try:
        _class = _divisionClasses[division]
    except KeyError:
        raise "Unknown division: %s" % division
    object = _class(id)
    try:
        object.load()
    except forgetSQL.NotFound, e:
        raise "Unknown id %s" % e
    return object

def _getDivisionByObject(object):
    for (division, _class) in _divisionClasses.items():
        if isinstance(object, _class):
            return division
    raise "Unknown division"

def createUrl(object=None, id=None, division=None,
              subsystem="devbrowser", **kwargs):
    if id and object:
        raise "Ambiguous parameters, id and object cannot both be specified"

    if object:
        division = _getDivisionByObject(object)
    # redirect, these things are done by report, not devbrowser
    if subsystem=='devbrowser' and division in 'vlan room cat org type prefix'.split():
        subsystem = 'report'
        if object:
            id = object._getID()[0]

    try:
        url = _subsystems[subsystem] + '/'
    except KeyError:
        raise "Unknown subsystem: %s" % subsystem

    if subsystem == 'devbrowser':
        if id and division not in ('service',):
            object = _getObjectByDivision(division, id)
        if not division and object:
            try:
                division = _getDivisionByObject(object)
            except:
                raise "Unknown object type"
        if division:
            if not division in 'netbox port gwport module'.split():
                url += division + '/'
            if division == 'service' and id:
               url += id + '/'
               return url
            if object:
                try:
                    # Does it exist in the database?
                    object.load()
                except forgetSQL.NotFound, e:
                    raise "Unknown id %s" % e
                if division=="netbox":
                    # nice url
                    url += object.sysname
                elif division == "port" or division == "gwport":
                    module = object.module
                    url += module.netbox.sysname
                    url += '/module%s' % module.module
                    if division == "port":
                        url += '/port%s' % object.swportid
                    else:
                        url += '/gwport%s' % object.gwportid
                elif division=="module":
                    url += object.netbox.sysname
                    url += '/module%s' % object.module
                else:
                    # Turn into strings, possibly join with ,
                    id = [str(x) for x in object._getID()]
                    url += ','.join(id)
                url += '/' # make sure we have trailing /

    elif subsystem == 'maintenance':
        if object:
            id = object._getID()[0]
        if division == 'netbox':
            url += "new?add_netbox=%s" % id
        elif division == 'service':
            url += "new?add_service=%s" % id
    elif subsystem == 'seeddb':
        if object:
            id = object._getID()[0]
        url += '%s/edit/%s' % (division, id)
    elif subsystem == 'report':
        if object:
            id = object._getID()[0]
        if division=="vlan":
            url += 'swporttrunk?vlanid=%s' % id
        elif division=='room':
            url += 'netbox?roomid=%s' % id
        elif division=='cat':
            url += 'netbox?catid=%s' % id
        elif division=='org':
            url += 'org?orgid=%s' % id
        elif division=='type':
            url += 'type?typeid=%s' % id
        elif division=='swport':
            url += 'swport?b1.netboxid=%s' % id
        elif division=='prefix':
            url += 'prefix?prefix.prefixid=%s' % id
    elif subsystem == 'rrd':
        # M�KKAKODEDRITFAEN!
        url += division
        url += "?"
        if type(id) != list:
            # since id might be a list, we always treat
            # it as a list.
            id = [id]
        for i in id:
            url += 'id=%s&amp;' % i
        tf = kwargs.get("tf")
        if tf:
            url += 'tf=%s' % tf
    return url


def createLink(object=None, content=None, id=None, division=None,
               subsystem="devbrowser", **kwargs):
    if content is None:
        if id and object:
            raise "Ambiguous parameters, id and object cannot both be specified"
        if division == 'service':
            content = id
        elif id:
            object = _getObjectByDivision(division, id)
            id = None
        if object:
            content = str(object)
    url = createUrl(id=id, division=division, subsystem=subsystem,
                    object=object, **kwargs)
    return html.Anchor(content, href=url)
