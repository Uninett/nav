

from nav.db.manage import *

class editdbLocation(Location):
    def getOptions(cls):
        options = []
        for entry in cls.getAllIterator(orderBy='locationid'):
            options.append((entry.locationid,entry.descr))    
        return options       
    getOptions = classmethod(getOptions)

class editdbOrg(Org):
    def getOptions(cls):
        options = []
        for entry in cls.getAllIterator(orderBy='orgid'):
            options.append((entry.orgid,entry.descr))    
        return options       
    getOptions = classmethod(getOptions)

class editdbVendor(Vendor):
    def getOptions(cls):
        options = []
        for entry in cls.getAllIterator(orderBy='vendorid'):
            options.append((entry.vendorid,entry.vendorid))    
        return options       
    getOptions = classmethod(getOptions)

class editdbTypegroup(Typegroup):
    def getOptions(cls):
        options = []
        for entry in cls.getAllIterator(orderBy='typegroupid'):
            text = entry.typegroupid + ': ' + entry.descr
            options.append((entry.typegroupid,text))    
        return options       
    getOptions = classmethod(getOptions)


class editdbNetbox(Netbox):
    # added catid
    _sqlFields =  {'catid': 'catid',
                   'cat': 'catid',
                   'device': 'deviceid',
                   'ip': 'ip',
                   'netboxid': 'netboxid',
                   'org': 'orgid',
                   'orgid': 'orgid',
                   'prefix': 'prefixid',
                   'ro': 'ro',
                   'room': 'roomid',
                   'roomid': 'roomid',
                   'rw': 'rw',
                   'snmp_agent': 'snmp_agent',
                   'snmp_version': 'snmp_version',
                   'subcat': 'subcat',
                   'sysname': 'sysname',
                   'type': 'typeid',
                   'up': 'up'}


class editdbType(Type):
    # adds typegroupid and vendorid
    _sqlFields =  {'cdp': 'cdp',
                   'descr': 'descr',
                   'frequency': 'frequency',
                   'sysobjectid': 'sysobjectid',
                   'tftp': 'tftp',
                   'typegroupid': 'typegroupid',
                   'typegroup': 'typegroupid',
                   'typeid': 'typeid',
                   'typename': 'typename',
                   'vendor': 'vendorid',
                   'vendorid': 'vendorid'}

class editdbRoom(Room):
    _sqlFields =  {'descr': 'descr',
                  'locationid': 'locationid',
                  'location': 'locationid',
                  'opt1': 'opt1',
                  'opt2': 'opt2',
                  'opt3': 'opt3',
                  'opt4': 'opt4',
                  'roomid': 'roomid'}
    _sqlLinks =  {}
    _userClasses = {}
    #_userClasses =  {'location': 'Location'}
    _userClasses = {}
    _sqlPrimary =  ('roomid',)
    _shortView =  ()
    _sqlTable =  'room'
    _descriptions =  {}

#class editdbRoom(Room):
#    # reassign locationid to locationid
#    _sqlFields =  {'descr': 'descr',
#                   'location': 'locationid',
#                   #'locationid': 'locationid',
#                   'room2': 'room2',
#                   'room3': 'room3',
#                   'room4': 'room4',
#                   'room5': 'room5',
#                   'roomid': 'roomid'}


class ServiceEditdb(Service):
    _sqlFields =  {'active': 'active',
                  'handler': 'handler',
                  'netbox': 'netboxid',
                  'serviceid': 'serviceid',
                  'up': 'up',
                  'version': 'version',
        		  'sysname': 'netbox.sysname'}
    _sqlLinks =  (('netboxid','netbox.netboxid'),)
    _userClasses =  {'netbox': Netbox}
    _sqlPrimary =  ('serviceid',)
    _shortView =  ()
    _sqlTable =  'service'
    _descriptions =  {}

