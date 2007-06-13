# -*- coding: UTF-8 -*-
# $Id$
#
# Copyright 2003, 2004 Norwegian University of Science and Technology
# Copyright 2007 UNINETT AS
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
# Authors: Hans Jørgen Hoel <hansjorg@orakel.ntnu.no>
#          Stein Magnus Jodal <stein.magnus.jodal@uninett.no>
#
"""
Common functions for Device Management modules
"""

### Imports

try:
    from mod_python import apache
except:
    pass # To allow use of pychecker

import nav.db.manage
from nav.web.TreeSelect import TreeSelect, Select, UpdateableSelect, Option, SimpleSelect
from nav.web import SearchBox

from nav.web.devicemanagement.constants import *
from nav.web.devicemanagement.widget import Widget

### Common functions

def newWidget(oldWidget):
    # Creates a copy of a general widget object
    widget = Widget(oldWidget.controlname,
                    oldWidget.type,
                    oldWidget.name,
                    oldWidget.value,
                    oldWidget.options,
                    oldWidget.required)
    return widget

def executeSQL(sql,fetch=False):
    connection = nav.db.getConnection('devicemanagement','manage')
    database = connection.cursor()
    # Clean sql string
    database.execute(sql)
    result = None
    if fetch:
        result = database.fetchall()
    return result

def updateFields(fields,table,idfield,updateid):
    sql = 'UPDATE ' + table + ' SET '
    first = True
    for field,value in fields.items():
        if not first:
            sql += ','
        sql += field + "='" + value + "'"
        first = False
    sql += ' WHERE ' + idfield + "='" + str(updateid) + "'"
    executeSQL(sql)

def insertFields(fields,table,sequence=None):
    # Add a new entry using the dict fields which contain
    # key,value pairs 

    # Sequence is a tuple (idfield,sequencename). If given, get
    # the nextval from sequence and set the idfield to this value
    nextid = None
    if sequence:
        idfield,seq = sequence
        sql = "SELECT nextval('%s')" % (seq,)
        result = executeSQL(sql,fetch=True)
        nextid = str(result[0][0])
        fields[idfield] = nextid

    sql = 'INSERT INTO ' + table + ' ('
    first = True
    for field,value in fields.items():
        if not first:
            sql += ','
        sql += field
        first = False
    sql += ') VALUES ('
    first = True
    for field,value in fields.items():
        if not first:
            sql += ','
        sql += "'" + value + "'"
        first = False
    sql += ')'
    executeSQL(sql)
    return nextid

def makeMainMenu(selected):
    menu = []

    i = 0
    for item in MAIN_MENU:
        path = item[1]
        if i == selected:
            path = None
        menu.append([item[0],path,item[2]])
        i += 1
    return menu

def makeTreeSelect(req,serialSearch=False,size=20):
    # Make the searchbox
    searchbox = SearchBox.SearchBox(req,
                'Type a room id, an ip or a (partial) sysname',
                title='Quicksearch')
    if serialSearch:
        searchbox.addSearch('serial',
                            'serialnumber',
                            'Device',
                            {'devices': ['device','deviceid']},
                            like = 'serial')
    searchbox.addSearch('host',
                        'ip or hostname',
                        'Netbox',
                        {'rooms': ['room','roomid'],
                         'locations': ['room','location','locationid'],
                         'netboxes': ['netboxid']},
                        call = SearchBox.checkIP)
    searchbox.addSearch('room',
                        'room id',
                        'Room',
                        {'rooms': ['roomid'],
                         'locations': ['location','locationid']},
                        where = "roomid = '%s'")
    sr = searchbox.getResults(req)

    # Make treeselect
    selectbox = TreeSelect()
    multiple = False

    if not sr.has_key('devices'):
        sr['devices'] = []

    if len(sr['devices']):
        select = SimpleSelect(CN_DEVICE,
                              "Devices matching serial '%s'" % \
                              (searchbox.getQuery(req),),
                              initTable='Device', 
                              initTextColumn='serial',
                              initIdColumn='deviceid',
                              initIdList = sr['devices'],
                              multiple = True,
                              multipleSize = size,
                              optionFormat = '$d',
                              orderByValue = True)

        selectbox.addSelect(select)
    else:
        select = Select(CN_LOCATION,
                        'Location',
                        multiple = True,
                        multipleSize = size,
                        initTable='Location', 
                        initTextColumn='descr',
                        initIdColumn='locationid',
                        preSelected = sr['locations'],
                        optionFormat = '$v ($d)',
                        orderByValue = True)

        select2 = UpdateableSelect(select,
                                   CN_ROOM,
                                   'Room',
                                   'Room',
                                   'descr',
                                   'roomid',
                                   'locationid',
                                   multiple=True,
                                   multipleSize=size,
                                   preSelected = sr['rooms'],
                                   optionFormat = '$v ($d)',
                                   orderByValue = True)

        select3 = UpdateableSelect(select2,
                                   CN_BOX,
                                   'Box',
                                   'Netbox',
                                   'sysname',
                                   'netboxid',
                                   'roomid',
                                   multiple=multiple,
                                   multipleSize=size,
                                   preSelected = sr['netboxes'])

        select4 = UpdateableSelect(select3,
                                   CN_MODULE,
                                   'Module',
                                   'Module',
                                   'module',
                                   'moduleid',
                                   'netboxid',
                                   multiple=multiple,
                                   multipleSize=size,
                                   onchange='',
                                   optgroupFormat = '$d') 
        # onchange='' since this doesn't update anything

        selectbox.addSelect(select)
        selectbox.addSelect(select2)
        selectbox.addSelect(select3)
        selectbox.addSelect(select4)

    selectbox.update(req.form)

    return (searchbox,selectbox)

def redirect(req, url):
    req.headers_out.add("Location", url)
    raise apache.SERVER_RETURN, apache.HTTP_MOVED_TEMPORARILY

def makewherelist(orglist):
    whereList = ''
    if orglist:
        first = True
        for org in orglist:
            if not first:
                whereList += ' or '
            whereList += "orgid='" + org + "'"
            first = False
        return whereList
    else:
        return None

def memberoforg(req):
    where = makewherelist(req.session['user'].getOrgIds())

    # if superuser, no restrictions based on orgids
    superuser = False
    #for group in req.session['user'].getGroups():
    #    if group.id == 1:
    #        superuser = True
    #        break

    if superuser == True:
        where = []
    return where
