"""
$Id: event.py,v 1.1 2003/06/16 11:51:50 magnun Exp $
This file is part of the NAV project.

Copyright (c) 2002 by NTNU, ITEA nettgruppen

Author: Magnus Nordseth <magnun@stud.ntnu.no>
"""
class Event:
    UP = 'UP'
    DOWN = 'DOWN'
    boxState = 'boxState'
    serviceState = 'serviceState'
    def __init__(self,serviceid,netboxid,deviceid,eventtype,source,status,info='', version=''):
        self.serviceid = serviceid
        self.netboxid = netboxid
        self.deviceid = deviceid
        self.info = info
        self.eventtype = eventtype
        self.status = status
        self.version = version
        self.source = source
            
            
    def __repr__(self):
        return "Service: %s, netbox: %s, eventtype: %s, status: %s" % (self.serviceid,
                                                                       self.netboxid,
                                                                       self.eventtype,
                                                                       self.status)
