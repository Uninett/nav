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

        # handle that follow-ups copies manitenance units from its parent
        sql = "select key,value,type from emotd_related inner join emotd using (emotdid) where emotdid=%d and (emotd.replaces_emotd is null and maintenance.state = 'scheduled' or emotd.replaces_emotd is not null and maintenance.state = 'active')" % int(emotdid)
        database.execute(sql)
        
        for (key,val,emotdtype) in database.fetchall():
            target = 'eventEngine'
            subsystem = 'emotd'
            severity = 50
            source = subsystem #'maintenance'
            eventtype = 'maintenanceState'
            state = 'e'
            value = 0
            if type == 'active':
                if emotdtype=='info':
                    severity = 10
                elif emotdtype=='internal':
                    severity = 20
                elif emotdtype=='scheduled':
                    severity = 60
                elif emotdtype=='error':
                    severity = 80
                state = 's'
                value = 100

            # type-dependant handling

            # type netbox
            if key=='netbox':

                #get new eventqid to insert into eventq AND eventqvar
                database.execute("select nextval('eventq_eventqid_seq')")
                eventqid = database.fetchone()[0]

                #select info from the netbox
                database.execute("select deviceid,sysname from netbox where netboxid = %d" % int(val))
                result = database.fetchone()
                if result:
                    (deviceid,sysname) = result

                    #insert into eventq
                    database.execute("insert into eventq (eventqid,target,eventtypeid,netboxid,deviceid,source,severity,state,value) values (%d,'%s','%s',%d,%d,'%s',%d,'%s',%d)" % (int(eventqid), target, eventtype, int(val), int(deviceid), source, severity, state, value))

                    #insert sysname into eventqvar
                    database.execute("insert into eventqvar (eventqid,var,val) values (%d, '%s', '%s')" % (int(eventqid), key, sysname))

            # type room or location
            elif key=='room' or key=='location':
                if key=='room':
                    #get all netboxes from this room
                    database.execute("select netboxid, sysname, deviceid from netbox where roomid=%s",(val,))
                else:
                    #get all netboxes from this location
                    database.execute("select netboxid, sysname, deviceid from netbox inner join room using (roomid) where locationid=%s",(val,))

                #for each netbox
                for (netboxid, sysname, deviceid) in database.fetchall():

                    #get eventqid
                    database.execute("select nextval('eventq_eventqid_seq')")
                    eventqid = database.fetchone()[0]

                    #insert into eventq
                    database.execute("insert into eventq (eventqid,target,eventtypeid,netboxid,deviceid,source,severity,state,value) values (%d,'%s','%s','%s','%s','%s',%d,'%s',%d)" % (int(eventqid), target, eventtype, int(netboxid), int(deviceid), source, severity, state, value))

                    #insert sysname into eventqvar
                    database.execute("insert into eventqvar (eventqid,var,val) values (%d, '%s', '%s')" % (int(eventqid), 'netbox', sysname))

            #type module
            elif key=='module':

                #get eventqid
                database.execute("select nextval('eventq_eventqid_seq')")
                eventqid = database.fetchone()[0]

                #select useful information regarding this module
                database.execute("select netboxid, deviceid, module, descr from module where moduleid=%d" % int(val))
                result = database.fetchone()
                if result:
                    (netboxid, deviceid, module, descr) = result

                    #insert into eventq
                    database.execute("insert into eventq (eventqid,target,eventtypeid,netboxid,deviceid,source,severity,state,value) values (%d,'%s','%s',%d,%d,'%s',%d,'%s',%d)" % (int(eventqid), target, eventtype, int(netboxid), int(deviceid), source, severity, state, value))

                    #insert into eventqvar
                    database.execute("insert into eventqvar (eventqid,var,val) values (%d, '%s', '%s')" % (int(eventqid), key, module + ":" + descr))

            #type service
            elif key=='service':

                #get eventqid
                database.execute("select nextval('eventq_eventqid_seq')")
                eventqid = database.fetchone()[0]

                #select useful information regarding the service
                database.execute("select netboxid, handler from service where serviceid=%d" % int(val))
                result = database.fetchone()
                if result:
                    (netboxid, handler) = result

                    #insert into eventq
                    database.execute("insert into eventq (eventqid,target,eventtypeid,netboxid,subid,source,severity,state,value) values (%d,'%s','%s',%d,%d,'%s',%d,'%s',%d)" % (int(eventqid), target, eventtype, int(netboxid), int(val), source, severity, state, value))

                    #insert into eventqvar
                    database.execute("insert into eventqvar (eventqid,var,val) values (%d, '%s', '%s')" % (int(eventqid), key, handler))
            else:

                #never happens
                raise repr("Unrecognised equipment key")

        #update maintenance states
        database.execute("update maintenance set state='%s' where maintenanceid = %d" % (type, int(mid)))

        #commit transaction
        connection.commit()


if __name__ == '__main__':
    schedule()
    check_state()
    send_event()
