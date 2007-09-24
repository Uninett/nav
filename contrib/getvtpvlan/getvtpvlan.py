#!/usr/bin/env python
"""
Utility script to fill the netbox_vtpvlan table of NAV.  It was made
only as an excercise in Python SNMP querying, and as a temporary
band-aid to getDeviceData's apparent inability to properly fill this
table at times.

The script will only query netboxes that the OID tester has deemed compatible
with the vtpVlanState OID from CISCO-VTP-MIB, and is typically only applicable
for Cisco devices.
"""

__author__ = 'Morten Brekkevold <morten.brekkevold@uninett.no>'
__copyright__ = '2007 UNINETT AS'
__license__ = 'GPLv2'
__version__ = '$Id$'

import sys
from nav import Snmp
from nav import db
try:
    set
except NameError:
    from sets import Set as set

def query_vlans(sysname,ip,ro,version,oid):
    s = Snmp.Snmp(ip, community=ro, version=version==2 and '2c' or 1)
    method = version == 2 and hasattr(s, 'bulkwalk') and s.bulkwalk or s.jog
    if sys.stdout.isatty():
        print "%s method is %s" % (sysname, method.__name__)
    response = method(oid)
    for index,value in response:
        if value == 1:
            vlan = int(index.split('.')[-1])
            yield vlan

select_sql = """SELECT vtpvlan
                FROM netbox_vtpvlan
                WHERE netboxid=%s"""

delete_sql = """DELETE FROM netbox_vtpvlan
                WHERE netboxid=%s
                AND vtpvlan IN (%s)"""

insert_sql = """INSERT INTO netbox_vtpvlan
                (netboxid, vtpvlan)
                VALUES (%s, %s)"""

def main(args):
    conn = db.getConnection('default')
    sql = """SELECT netboxid, sysname,ip,ro,snmp_version,snmpoid
             FROM netbox n
             NATURAL JOIN netboxsnmpoid ns
             NATURAL JOIN snmpoid s
             WHERE n.up='y' AND s.oidkey='vtpVlanState'"""
    boxes = conn.cursor()
    boxes.execute(sql)
    for netboxid, sysname,ip,ro,version,oid in boxes.fetchall():
        try:
            current_vlans = set(query_vlans(sysname,ip,ro,version,oid))
        except Exception, e:
            print >> sys.stderr, "Exception occurred when querying %s:\n%s" % (sysname, e)
            continue

        cursor = conn.cursor()
        # Get list of previously collected vlans
        cursor.execute(select_sql % netboxid)
        old_vlans = set([r[0] for r in cursor.fetchall()])

        gone_vlans = old_vlans.difference(current_vlans)
        new_vlans = current_vlans.difference(old_vlans)

        if sys.stdout.isatty():
            print "%s (current): %s" % (sysname, list(current_vlans))
            if old_vlans:
                print "%s (old)    : %s" % (sysname, list(old_vlans))
            if gone_vlans:
                print "%s (gone)   : %s" % (sysname, list(gone_vlans))
            if new_vlans:
                print "%s (new)    : %s" % (sysname, list(new_vlans))
            print ""

        # Remove the vlans that have disappeared
        if gone_vlans:
            gone_vlan_string = ",".join([str(v) for v in gone_vlans])
            cursor.execute(delete_sql % (netboxid, gone_vlan_string))

        # Insert new vlans
        for vlan in new_vlans:
            cursor.execute(insert_sql, (netboxid, vlan))
        conn.commit()

if __name__ == '__main__':
    main(sys.argv[1:])

