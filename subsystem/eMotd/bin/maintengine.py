#!/usr/bin/env python
"""
$Id$

This file is part of the NAV project.

This module contains functionality related to eMotd and maintenance.

Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Bjørn Ove Grøtan <bjorn.grotan@itea.ntnu.no>
"""

##
# import modules and set path
#from nav.db.manage import Emotd,Emotd_related,Maintenance
#from nav.db.manage import Eventq,Eventqvar,Eventtype,Netbox,Service,Room
from nav import db

from mx import DateTime

##
# some placeholders
events = []
states = ['scheduled','active','passed','overridden']
debug = False
connection = db.getConnection('eventEngine','manage')
database = connection.cursor()


def schedule():
    """ Check if there are maintenances to be schedule """
    sql = "update maintenance set state = 'scheduled' where state is null or state not in ('scheduled','active','passed','overridden')"
    database.execute(sql)
    connection.commit()
    

def check_state():
    """ 
    Checks if there are some maintenances to be set active 
    (e.g. send maintenenaceOn)
    """
    sql = "select maintenanceid,emotdid from maintenance where maint_start < now() and state='scheduled'"
    database.execute(sql)
    for (mid,emotdid) in database.fetchall():
        e = {}
        e['type'] = 'active'
        e['emotdid'] = emotdid
        e['maintenanceid'] = mid
        events.append(e)
        
    sql = "select maintenanceid,emotdid from maintenance where maint_end < now() and state='active'"
    database.execute(sql)
    for (mid,emotdid) in database.fetchall():
        e = {}
        e['type'] = 'passed'
        e['emotdid'] = emotdid
        e['maintenanceid'] = mid
        events.append(e)
    # bør ha magi for å sjekke overlappende tidsvinduer med overlappende bokser... jeje


def send_event():
    """ Sends events to EventQueue based on table 'maintenance' """
    for event in events:
        emotdid = event['emotdid']
        mid = event['maintenanceid']
        type = event['type']
        
        sql = "select key,value from emotd_related where emotdid=%d" % int(emotdid)
        database.execute(sql)
        
        for (key,val) in database.fetchall():
            target = 'eventEngine'
            subsystem = 'emotd'
            severity = 50
            source = subsystem #'maintenance'
            eventtype = 'maintenanceState'
            state = 'e'
            value = 0
            if type == 'active':
                state = 's'
                value = 100
            database.execute("select nextval('eventq_eventqid_seq')")
            eventqid = database.fetchone()[0]
            if key=='netbox':
                database.execute("select deviceid,sysname from netbox where netboxid = %d" % int(val))
                (deviceid,sysname) = database.fetchone()[0]
                database.execute("insert into eventq (eventqid,target,eventtypeid,netboxid,deviceid,source,severity,state,value) values (%d,'%s','%s',%d,%d,'%s',%d,'%s',%d)" % (int(eventqid), target, eventtype, int(val), int(deviceid), source, severity, state, value))
                database.execute("insert into eventqvar (eventqid,var,val) values (%d, '%s', '%s')" % (int(eventqid), key, sysname))
            elif key=='room' or key=='location':
                database.execute("insert into eventq (eventqid,target,eventtypeid,source,severity,state,value) values (%d,'%s','%s','%s',%d,'%s',%d)" % (int(eventqid), target, eventtype, source, severity, state, value))
                database.execute("insert into eventqvar (eventqid,var,val) values (%d, '%s', '%s')" % (int(eventqid), key, val))
            elif key=='module':
                database.execute("select netboxid, deviceid, module, descr from module where moduleid=%d" % int(val))
                (netboxid, deviceid, module, descr) = database.fetchone()
                database.execute("insert into eventq (eventqid,target,eventtypeid,netboxid,deviceid,source,severity,state,value) values (%d,'%s','%s',%d,%d,'%s',%d,'%s',%d)" % (int(eventqid), target, eventtype, int(netboxid), int(deviceid), source, severity, state, value))
                database.execute("insert into eventqvar (eventqid,var,val) values (%d, '%s', '%s')" % (int(eventqid), key, module + ":" + descr))
            elif key=='service':
                database.execute("select netboxid, handler from service where serviceid=%d" % int(val))
                (netboxid, handler) = database.fetchone()
                database.execute("insert into eventq (eventqid,target,eventtypeid,netboxid,subid,source,severity,state,value) values (%d,'%s','%s',%d,%d,'%s',%d,'%s',%d)" % (int(eventqid), target, eventtype, int(netboxid), int(val), source, severity, state, value))
                database.execute("insert into eventqvar (eventqid,var,val) values (%d, '%s', '%s')" % (int(eventqid), key, handler))
            else:
                raise repr("Unrecognised equipment key")

                
        database.execute("update maintenance set state='%s' where maintenanceid = %d" % (type, int(mid)))
        connection.commit()


if __name__ == '__main__':
    schedule()
    check_state()
    send_event()
