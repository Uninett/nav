"""
$Id:

This file is part of the NAV project.

This module contains functionality related to the web toolbox.

Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Bjørn Ove Grøtan <bjorn.grotan@itea.ntnu.no>
"""

##
# import modules and set path
import sys
sys.path = ['/usr/local/nav/navme/lib/python','/usr/local/lib/python2.2/site-packages', '/usr/lib/apache/python/lib/python2.2', '/usr/lib/apache/python/lib/python2.2/plat-linux2', '/usr/lib/apache/python/lib/python2.2/lib-tk', '/usr/lib/apache/python/lib/python2.2/lib-dynload', '/usr/lib/apache/python/lib/python2.2/site-packages', '/usr/local/nav/navme/lib/python', '/usr/local/lib/python2.2/site-packages']

from nav.db.manage import Emotd,Emotd_related,Maintenance,Eventq,Eventqvar,Eventtype
from mx import DateTime

##
# some placeholders
events = []
states = ['scheduled','active','passed','overridden']
debug = True

def schedule():
    ##
    # check if there are maintenances to be schedule
    where = ["maint_start < now()"]
    where.append("maint_end > now()")
    mids = Maintenance.getAllIDs(where)
    if debug:
        print 'debug: Found ', len(mids) , ' maintenences'
    for mid in mids:
        if Maintenance(mid).state not in states:
            m = Maintenance(mid)
            m.state = 'scheduled'
            m.save() 
            if debug:
                print 'maintenance with id %s scheduled' % mid

def check_state():
    ##
    # check if there are some maintenances to be set active (e.g. send maintenenaceOn)
    where = ["maint_start < now()"]
    where.append("maint_end > now()")
    where.append("state = 'scheduled'")
    mids = Maintenance.getAllIDs(where)
    if debug:
        print 'debug: Found ', len(mids) , ' maintenances to change'
    for mid in mids:
        e = {}
        e['type'] = 'maintenanceOn'
        e['emotdid'] = Maintenance(mid).emotd
        e['maintenanceid'] = mid
        events.append(e)
    where = ["maint_start < now()"]
    where.append("maint_end < now()")
    where.append("state = 'active'")
    mids = Maintenance.getAllIDs(where)
    if debug: 
        print 'debug: Found ', len(mids) , ' maintenances to change'
    for mid in mids:
        e = {}
        e['type'] = 'maintenanceOff'
        e['emotdid'] = Maintenance(mid).emotd
        e['maintenanceid'] = mid
        events.append(e)
    # bør ha magi for å sjekke overlappende tidsvinduer med overlappende bokser... jeje


def send_event():
    ##
    # send events
    if debug:
        print 'debug: Found %s events to send to eventq' % len(events)
        print 'debug: ', events
    for event in events:
        mid = event['emotdid']
        maintid = event['maintenanceid']
        where = ["emotdid = %s" % mid] 
        if debug: print 'finner bokser og servicer koblet mot emotd-melding'
        related = Emotd_related.getAll(where)
        if debug: print 'emotdid: ', mid

        if debug: print 'fant %s enheter koblet mot denne meldingen' % len(related) 
        for unit in related:
            ''' send 1(one) event pr netbox/service/module '''
            e = Eventq()
            e.target = 'eventEngine'
            e.subsystem = 'emotd'
            e.eventtype = 'maintenanceState'
            e.netbox = unit.value
            if unit.key == 'service':
                e.subid = unit.value
            if event['type'] == 'maintenanceOn':
                e.state = 'e'
                e.value = 100
                Maintenance(maintid).state = 'active'
            if event['type'] == 'maintenanceOff':
                e.state = 's'
                e.value = 0
                Maintenance(maintid).state = 'passed'
            e.severity = 50
            e.source = 'maintenance'
            e.time = DateTime.now()
            try:
                e.save() # beam me up Scotty!
                if debug:
                    print 'Event %s:%s for %s sent ' % (e.eventtype,e.state,e.netbox)
            except:
                print 'An error occured sending event for %s : %s' % (mid,e.netbox)
        if len(related)<1:
            print 'Error: No netbox/service/module found relating this maintenance-event'


if __name__ == '__main__':
    schedule()
    check_state()
    send_event()
