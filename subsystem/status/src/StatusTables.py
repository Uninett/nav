"""
$Id$

This file id part of the NAV project.

Contains custom forgetSQL clases for the status page

Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Hans Jørgen Hoel <hansjorg@orakel.ntnu.no>
"""

#################################################
## Imports

from nav.db.forgotten.navprofiles import *
from nav.db.manage import *

#################################################
## Classes

# tables from manage
class AlerthistStatusNetbox(Alerthist):
    _sqlFields =  {'alerthistid': 'alerthistid',
                  'device': 'deviceid',
                  'end_time': 'end_time',
                  'eventtype': 'eventtypeid',
                  'netbox': 'netboxid',
                  'severity': 'severity',
                  'source': 'source',
                  'start_time': 'start_time',
                  'subid': 'subid',
                  'value': 'value',
                  'up': 'netbox.up',
                  'sysname': 'netbox.sysname',
                  'orgid': 'netbox.orgid',
                  'ip': 'netbox.ip'}
    _sqlLinks =  (('netboxid', 'netbox.netboxid'),)
    _userClasses =  {'device': Device, 'eventtype': Eventtype, 'netbox': Netbox}
    _sqlPrimary =  ('alerthistid',)
    _shortView =  ()
    _sqlTable =  'alerthist'
    _descriptions =  {}


class AlerthistStatusService(Alerthist):
    _sqlFields =  {'alerthistid': 'alerthistid',
                  'device': 'deviceid',
                  'end_time': 'end_time',
                  'eventtype': 'eventtypeid',
                  'netbox': 'netboxid',
                  'severity': 'severity',
                  'source': 'source',
                  'start_time': 'start_time',
                  'subid': 'subid',
                  'value': 'value',
                  'up': 'service.up',
                  'sysname': 'netbox.sysname',
                  'orgid': 'netbox.orgid',
                  'handler': 'service.handler'}
    _sqlLinks =  (('netboxid', 'netbox.netboxid'),('subid','service.serviceid'))
    _userClasses =  {'device': Device, 'eventtype': Eventtype, 'netbox': Netbox}
    _sqlPrimary =  ('alerthistid',)
    _shortView =  ()
    _sqlTable =  'alerthist'
    _descriptions =  {}
                   
# tables from navprofiles
class AccountpropertyStatus(Accountproperty):
    _sqlFields =  {'account': 'accountid', 'property': 'property', 'value': 
'value'
}
    _sqlLinks =  {}
    _userClasses =  {'account': 'Account'}
    _shortView =  ()
    _sqlTable =  'accountproperty'
    _descriptions =  {}
    _sqlPrimary = ('accountid',)
