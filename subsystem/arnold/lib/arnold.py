#
# Copyright 2008 Norwegian University of Science and Technology
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
# Authors: John-Magne Bredal <john.m.bredal@ntnu.no>
#

__copyright__ = "Copyright 2008 Norwegian University of Science and Technology"
__license__ = "GPL"
__author__ = "John-Magne Bredal (john.m.bredal@ntnu.no)"


"""
Provides helpfunctions for Arnold web and script
"""

import nav.Snmp
import re, os, sys
import ConfigParser
import logging
import socket
import email.Message
import email.Header
import email.Charset
import commands
from IPy import IP
import psycopg2.extras

import nav.buildconf
import nav.bitvector
from nav.db import getConnection
from nav.util import isValidIP
from nav.errors import GeneralException


class ChangePortStatusError(GeneralException):
    "An error occured when changing portadminstatus"
    pass

class ChangePortVlanError(GeneralException):
    "An error occured when changing portvlan"
    pass

class NoDatabaseInformationError(GeneralException):
    "Could not find information in database for id"
    pass

class PortNotFoundError(GeneralException):
    "Could not find port in database"
    pass

class UnknownTypeError(GeneralException):
    "Unknown type (not ip or mac)"
    pass

class DbError(GeneralException):
    "Error when querying database"
    pass

class NotSupportedError(GeneralException):
    "This vendor does not support snmp set of vlan"
    pass

class NoSuchProgramError(GeneralException):
    "No such program"
    pass

class WrongCatidError(GeneralException):
    "Arnold is not permitted to block ports on equipment of this category"
    pass

class AlreadyBlockedError(GeneralException):
    "This port is already blocked or quarantined."
    pass

class InExceptionListError(GeneralException):
    "This ip-address is in the exceptionlist and cannot be blocked."
    pass

class FileError(GeneralException):
    "Fileerror"
    pass

class BlockonTrunkError(GeneralException):
    "No action on trunked interface allowed"
    pass


# Config-file
configfile = nav.buildconf.sysconfdir + "/arnold/arnold.conf"
config = ConfigParser.ConfigParser()
config.read(configfile)

logger = logging.getLogger("nav.arnold")
    

def parseNonblockFile(file):
    """
    Parse nonblocklist and make it ready for use.
    """

    nonblockdict = {}
    nonblockdict['ip'] = {}
    nonblockdict['range'] = {}

    # Open nonblocklist, parse it.
    try:
        f = open(file)
    except IOError, why:
        raise FileError, why

    for line in f.readlines():

        line = line.strip()
        
        # Skip comments
        if line.startswith('#'):
            continue

        if re.search('^\d+\.\d+\.\d+\.\d+$', line):
            # Single ip-address
            nonblockdict['ip'][line] = 1
        elif re.search('^\d+\.\d+\.\d+\.\d+\/\d+$', line):
            # Range
            nonblockdict['range'][line] = 1

    f.close()

    return nonblockdict


# nonblocklist
nonblockfile = nav.buildconf.sysconfdir + "/arnold/nonblock.conf"
try:
    nonblockdict = parseNonblockFile(nonblockfile)
except FileError, why:
    raise FileError



###############################################################################
# findIdInformation
#
def findIdInformation(id, limit):
    """
    Look in arp and cam tables to find id (which is either ip or
    mac-address). Returns a list with $limit number of dicts
    containing all info from arp and cam joined on mac.
    """

    # Connect to database
    conn = getConnection('default')

    # Find type of id
    (type,id) = findInputType(id)
    #print "%s is of type %s" %(id, type)

    result = []
    # Get data from database based on id
    if type in ['IP','MAC']:

        c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        query = ""

        if type == 'IP':

            # Find cam-tuple which relates to the time where this ip was last
            # active.
            query = """
            SELECT *, cam.start_time AS starttime, cam.end_time AS endtime
            FROM cam
            JOIN (SELECT ip, mac, start_time AS ipstarttime,
            end_time AS ipendtime
                  FROM arp
                  WHERE ip=%s
                  ORDER BY end_time DESC
                  LIMIT 2) arpaggr USING (mac)
            WHERE (cam.start_time, cam.end_time)
            OVERLAPS (arpaggr.ipstarttime, arpaggr.ipendtime)
            ORDER BY endtime DESC
            LIMIT %s
            """

        elif type == 'MAC':

            # Fetch last camtuple regarding this macaddress
            query = """
            SELECT *, cam.start_time AS starttime, cam.end_time AS endtime
            FROM cam
            WHERE mac = %s
            ORDER BY endtime DESC
            LIMIT %s
            """
        
        try:
            c.execute(query, (id, limit))
        except Exception, e:
            logger.error('findIDInformation: Error in query %s: %s'
                         %(query, e))
            raise DbError, e

        if c.rowcount > 0:
            result = [dict(row) for row in c.fetchall()]

            # Walk through result replacing DateTime(infinity) with
            # string "Still Active". Else the date showing will be
            # 999999-12-31 00:00:00.00. This of course also removes
            # the datetime-object.
            for row in result:
                if row['endtime'].year == 999999:
                    row['endtime'] = 'Still Active'
                else:
                    row['endtime'] = row['endtime'].strftime('%Y-%m-%d %H:%M:%S')

                if not row.has_key('ip'):
                    row['ip'] = '0.0.0.0'
                    
        else:
            result = 1
        
    else:
        raise UnknownTypeError, id

    if result == 1:
        raise NoDatabaseInformationError, id

    return result

###############################################################################
# findSwportinfo
#
def findSwportinfo(netboxid, ifindex, module):
    """
    Find netbox and swportinfo based on input. Return dict with
    info. The dict contains everything from netbox, type, module and
    swport tables related to the id. Also ipaddress, macaddress and
    endtime of id IF AND ONLY IF the id is not an swport.
    """

    # Connect to database
    conn = getConnection('default')
    c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    try:
        query = """SELECT * FROM netbox
        LEFT JOIN type USING (typeid)
        LEFT JOIN module USING (netboxid)
        LEFT JOIN swport USING (moduleid)
        WHERE netboxid=%s
        AND ifindex=%s
        AND module=%s"""

        c.execute(query, (netboxid, ifindex, module))
    except Exception, e:
        logger.error("findSwportinfo: Error in query %s: %s" %(query, e))
        raise DbError, e

    if c.rowcount > 0:
        result = dict(c.fetchone())
        
        return result
    else:
        raise PortNotFoundError, (netboxid, ifindex, module)


    return 1


###############################################################################
# findSwportIDinfo
#
def findSwportIDinfo(swportid):
    """
    Join results from netbox, type, module and swport tables based on
    swportid. Returns a dict with info. Same as findSwportinfo only it
    takes other input.
    """

    # Connect to database
    conn = getConnection('default')
    c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Get switch-information
    swquery = """SELECT * FROM netbox
    LEFT JOIN type USING (typeid)
    LEFT JOIN module USING (netboxid)
    LEFT JOIN swport USING (moduleid)
    WHERE swportid = %s"""

    try:
        c.execute(swquery, (swportid,))
    except nav.db.driver.ProgrammingError, why:
        logger.error("findSwportIDinfo: Error in query %s, %s" %(swquery, why))
        raise DbError, why

    if c.rowcount > 0:
        return dict(c.fetchone())
    else:
        raise PortNotFoundError, swportid

    return 1



###############################################################################
# findInputType
#
def findInputType (input):
    """Try to determine whether input is a valid ip-address,
    mac-address or an swportid. Return type and reformatted input as a
    tuple"""

    # Support mac-adresses on xx:xx... format
    mac = input.replace(':','')

    # idValidIP returns 10.0.0.0 if you type 10.0.0. Check that this is not the
    # case.
    if isValidIP(input) and not isValidIP(input).endswith('.0'):
        return ("IP", input)
    elif re.match("^[A-Fa-f0-9]{12}$", mac):
        return ("MAC",input)
    elif re.match("^\d+$", input):
        return ("SWPORTID",input)

    return ("UNKNOWN",input)


###############################################################################
# blockPort
#
def blockPort(id, sw, autoenable, autoenablestep, determined, reason, comment, username, type, vlan=False):
    """
    Block the port or change vlan on port and update database.
    type: block or quarantine.
    vlan: Must be set if this is a quarantine attempt
    """

    # Type determines if this is an attempt to block the port or
    # change to a quarantine vlan
    if type not in ['block','quarantine']:
        logger.info("Type must be block or quarantine: %s" %type)
        # At the moment we just return silently as this should be a
        # programmer-error only. A better solution if we need to be
        # more verbose is to make an error-class and raise an
        # exception.
        return

    if type == 'quarantine' and not vlan:
        logger.error("Vlan must be set to quarantine a port.")
        return

    if type == 'block':
        action = 'disabled'
    else:
        action = 'quarantined'


    # Connect to database
    arnolddb = getConnection('default', 'arnold')
    c = arnolddb.cursor(cursor_factory=psycopg2.extras.DictCursor)

    logger.info("blockPort: Trying to %s %s" %(type, id['ip']))
        

    # Check if this id is in the nonblocklist
    if checkNonBlock(id['ip']):
        raise InExceptionListError

    allowtypes = [x.strip() for x in config.get('arnold','allowtypes').split(',')]

    if sw['catid'] not in allowtypes:
        logger.info("blockPort: Not allowed to %s on %s" %(type, sw['catid']))
        raise WrongCatidError, sw['catid']
        

    if sw['trunk']:
        logger.info("blockPort: This is a trunk. No action allowed.")
        raise BlockonTrunkError

    
    # Find dns and netbios
    dns = getHostName(id['ip'])
    # This is so slow...bu!
    netbios = getNetbios(id['ip'])
    if netbios == 1:
        netbios = ""

    # autoenablestep
    autoenablestep = 2

    # autoenable
    if not autoenable:
        autoenable = "NULL"
    else:
        autoenable = "now() + interval '%s day'" %(autoenable)

    # check format on the input
    if reason:
        reason = int(reason)

    # Check if a block exists with this swport/mac-address combo.
    # if yes and active: do nothing, raise AlreadyBlockedError
    # if yes and inactive: block port, update identity, create new event
    # if no: block port, create identity, create first event

    query = "SELECT * FROM identity WHERE swportid = %s AND mac = %s"
    try:
        c.execute(query, (sw['swportid'], id['mac']))
    except nav.db.driver.ProgrammingError, why:
        logger.error("blockPort: Error in sql: %s, %s" %(query, why))
        raise DbError, why

    res = c.fetchone()


    # if yes and active: do nothing, raise AlreadyBlockedError
    if c.rowcount > 0 and res['blocked_status'] in ['disabled', 'quarantined']:
        logger.info("blockPort: This port is already %s" %action)
        raise AlreadyBlockedError


    elif c.rowcount > 0 and res['blocked_status'] == 'enabled':
        ######################################################
        # block port, update identity, create new event

        logger.info("blockPort: This port has been blocked/quarantined \
        before, updating")

        if type == 'block':

            fromvlan = vlan = 0
            
            try:
                changePortStatus('disable', sw['ip'], sw['vendorid'], sw['rw'],
                                 sw['module'], sw['port'], sw['ifindex'])
            except ChangePortStatusError, e:
                logger.error("blockPort: Error changing portstatus: %s" %e)
                raise ChangePortStatusError

        elif type == 'quarantine':
            
            try:
                fromvlan = changePortVlan(sw['ip'], sw['ifindex'], vlan)
            except (DbError, NotSupportedError, ChangePortStatusError,
                    ChangePortVlanError), e:
                logger.error("blockPort: Error changing vlan: %s" %e)
                raise ChangePortVlanError


        else:
            # Log and return
            logger.error("Type not recognised: %s" %type)
            return

        # Update existing identity
        query = """UPDATE identity SET
        blocked_status = %%s, blocked_reasonid = %%s, swportid = %%s,
        ip = %%s, mac = %%s, dns = %%s, netbios = %%s, lastchanged = now(),
        autoenable = %s, autoenablestep = %%s, mail = %%s,
        determined = %%s, fromvlan = %%s, tovlan = %%s
        WHERE identityid = %%s
        """ %autoenable
            

        arglist=[action, reason, sw['swportid'], id['ip'], id['mac'], \
                 dns, netbios, autoenablestep, "", determined, \
                 fromvlan, vlan, res['identityid']]


        doQuery('arnold', query, arglist)

        # Create new event
        query = """INSERT INTO event
        (identityid, event_comment, blocked_status, blocked_reasonid,
        eventtime, autoenablestep, username)
        VALUES (%s, %s, %s, %s, now(), %s, %s)
        """

        arglist = [res['identityid'], comment, action , reason, \
                   autoenablestep, username]

        doQuery('arnold', query, arglist)


    else:
        #########################################################
        # block port, create identity, create first event

        logger.info("blockPort: Not %s before, creating new identity" %action)

        # Get nextvalue of sequence to use in both queries
        nextvalq = "SELECT nextval('identity_identityid_seq')"
        try:
            c.execute(nextvalq)
        except nav.db.driver.ProgrammingError, why:
            raise DbError, why

        nextval = c.fetchone()[0]

        
        if type == 'block':
            try:
                changePortStatus('disable', sw['ip'], sw['vendorid'], sw['rw'],
                                 sw['module'], sw['port'], sw['ifindex'])
            except ChangePortStatusError:
                logger.error("blockPort: Error changing portstatus: %s" %e)
                raise ChangePortStatusError

            # Create new identitytuple
            query = """
            INSERT INTO identity
            (identityid, blocked_status, blocked_reasonid, swportid, ip, mac,
            dns, netbios, starttime, lastchanged, autoenable, autoenablestep,
            mail, determined) 
            VALUES (%%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, now(), now(),
            %s, %%s, %%s, %%s)
            """ %autoenable
            
            arglist = [nextval, action, reason, sw['swportid'], id['ip'], \
                       id['mac'], dns, netbios, autoenablestep, "", determined]
            

        elif type == 'quarantine':

            try:
                fromvlan = changePortVlan(sw['ip'], sw['ifindex'], vlan)
            except (DbError, NotSupportedError, ChangePortStatusError,
                    ChangePortVlanError), e:
                logger.error("blockPort: Error changing vlan: %s" %e)
                raise ChangePortVlanError

            # Create new identitytuple
            query = """
            INSERT INTO identity
            (identityid, blocked_status, blocked_reasonid, swportid, ip, mac,
            dns, netbios, starttime, lastchanged, autoenable, autoenablestep,
            mail, determined, fromvlan, tovlan) 
            VALUES (%%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, now(), now(),
            %s, %%s, %%s, %%s, %%s, %%s)
            """ %autoenable
            
            arglist = [nextval, action, reason, sw['swportid'], id['ip'], \
                       id['mac'], dns, netbios, autoenablestep, "", \
                       determined, fromvlan, vlan]

        else:
            logger.error("Type not recognised: %s" %type)
            return


        doQuery('arnold', query, arglist)


        # Create new event-tuple
        query = """INSERT INTO event
        (identityid, event_comment, blocked_status, blocked_reasonid,
        eventtime, autoenablestep, username)
        VALUES (%s, %s, %s, %s, now(), %s, %s)
        """
    
        arglist = [nextval, comment, action , reason, autoenablestep, username]

        doQuery('arnold', query, arglist)


    logger.info("Successfully %s %s" %(action, id['ip']))

        

###############################################################################
# openPort
#
def openPort(id, username, eventcomment=""):
    """
    Takes as input the identityid of the block and username. Opens the
    port (either enable or change vlan) and updates the database.

    If port is not found in the database we assume that the
    switch/module has been replaced. As this normally means that the
    port is enabled, we enable the port in the arnold-database.
    """

    logger.info("openPort: Trying to open identity with id %s" %id)

    # Connect to database
    conn = getConnection('default')
    arnolddb = getConnection('default', 'arnold')

    carnold = arnolddb.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cmanage = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Find identityidinformation
    query = """SELECT * FROM identity WHERE identityid = %s"""
    carnold.execute(query, (id, ))

    if carnold.rowcount <= 0:
        raise NoDatabaseInformationError, id

    identityrow = carnold.fetchone()

    # Fetch info for this swportid
    swportidquery = """SELECT * FROM netbox
    LEFT JOIN type USING (typeid)
    LEFT JOIN module USING (netboxid)
    LEFT JOIN swport USING (moduleid)
    WHERE swportid = %s"""

    cmanage.execute(swportidquery, (identityrow['swportid'], ))

    # If port exists, enable it with SNMP
    if cmanage.rowcount > 0:
        row = cmanage.fetchone()
        status = identityrow['blocked_status']

        if status == 'disabled':
            # Enable port based on information gathered
            try:
                changePortStatus('enable', row['ip'], row['vendorid'],
                                 row['rw'], row['module'], row['port'],
                                 row['ifindex'])
            except ChangePortStatusError, why:
                logger.error("openPort: Error when changing portstatus: %s"
                             %why)
                raise ChangePortStatusError

        elif status == 'quarantined':
            # Change vlan to fromvlan stored in database
            try:
                changePortVlan(row['ip'], row['ifindex'],
                               identityrow['fromvlan'])
            except (DbError, NotSupportedError, ChangePortVlanError), e:
                logger.error("openPort: %s", e)
                raise ChangePortVlanError
            
    else:
        # If port was not found, reflect this in event-comment
        eventcomment = """Port was not found because switch/module
        replaced. Port enabled in database only."""
        

    # Update identity-table
    updateq = """UPDATE identity SET
    lastchanged = now(),
    blocked_status = 'enabled',
    fromvlan = NULL, tovlan = NULL
    WHERE identityid = %s"""

    try:
        carnold.execute(updateq, (id, ))
    except nav.db.driver.ProgrammingError, why:
        arnolddb.rollback()
        raise DbError, why

    # Update event-table
    eventq = """INSERT INTO event
    (identityid, blocked_status, eventtime, username, event_comment) VALUES
    (%s, 'enabled', now(), %s, %s)"""

    try:
        carnold.execute(eventq, (id, username, eventcomment))
        arnolddb.commit()
    except nav.db.driver.ProgrammingError, why:
        arnolddb.rollback()
        raise DbError, why

    # Raise exception to catch for notifying user of lack of swport
    if cmanage.rowcount <= 0:
        raise NoDatabaseInformationError, id

    logger.info("openPort: Port successfully opened")



###############################################################################
# changePortStatus
#
def changePortStatus(action, ip, vendorid, community, module, port, ifindex):
    """
    Use SNMP to disable a interface.
    - Action must be 'enable' or 'disable'.
    - Community must be read/write community
    - IP is the ip of the switch to change portstatus on

    Todo: Remove vendorid, community, module, port and fetch that from
    database
    """

    # We use ifadminstatus to enable and disable ports
    # ifAdminStatus has the following values:
    # 1 - up
    # 2 - down
    # 3 - testing (no operational packets can be passed)
    oid = '.1.3.6.1.2.1.2.2.1.7'

    ifindex = str(ifindex)
    query = oid + '.' + ifindex

    logger.debug("vendor: %s, ro: %s, ifindex: %s, module: %s"
                 %(vendorid, community, ifindex, module))

    # Create snmp-object
    s = nav.Snmp.Snmp(ip,community)


    # Disable or enable based on input
    try:
        if action == 'disable':
            logger.info("Disabling ifindex %s on %s with %s"
                        %(ifindex, ip, query))
            s.set(query, 'i', 2)
            pass
        elif action == 'enable':
            logger.info("Enabling ifindex %s on %s with %s"
                        %(ifindex, ip, query))
            s.set(query, 'i', 1)
            pass
        
    except nav.Snmp.AgentError, why:
        logger.error("Error when executing snmpquery: %s" %why)
        raise ChangePortStatusError, why



###############################################################################
# changePortVlan
#
def changePortVlan(ip, ifindex, vlan):
    """
    Use SNMP to change switchport access vlan. Returns vlan on port
    before change if successful.

    ip: ip of netbox
    ifindex: ifindex of swport in manage-db
    vlan: vlanid to change to

    Reasons for not successful change may be:
    - Wrong community, use rw-community
    - rw-community not set on netbox
    - port is a trunk
    """

    logger.debug("changePortVlan got %s, %s, %s" %(ip, ifindex, vlan))

    # Connect to database
    conn = getConnection('default')
    c = conn.cursor()

    q = """SELECT vendorid, ro, rw
    FROM netbox
    LEFT JOIN type USING (typeid)
    WHERE ip = %s
    """

    # type is the TYPE in the snmpset-query
    type = ''

    try:
        c.execute(q, (ip, ))
    except nav.db.driver.ProgrammingError, e:
        raise DbError, e

    vendorid, ro, rw = c.fetchone()

    # oid for getting and setting vlan
    # CISCO
    # cisco.ciscoMgmt.ciscoVlanMembershipMIB.ciscoVlanMembershipMIBObjects.
    # vmMembership.vmMembershipTable.vmMembershipEntry.vmVlan.<ifindex>
    if vendorid == 'cisco':

        oid = "1.3.6.1.4.1.9.9.68.1.2.2.1.2"
        type = 'i'

    elif vendorid == 'hp':

        oid = "1.3.6.1.2.1.17.7.1.4.5.1.1"
        type = 'u'

    else:

        # Nothing else supported :p As we use Q-BRIDGE-MIB this is
        # possibly incorrect, but testing on other vendors is needed.

        raise NotSupportedError, vendorid


    # Check vlanformat
    if not re.search('\d+', str(vlan)):
        raise ChangePortVlanError, "Wrong format on vlan %s" %vlan


    # Make query based on oid and ifindex
    query = oid + '.' + str(ifindex)

    # Create snmp-objects
    snmpget = nav.Snmp.Snmp(ip,ro)
    snmpset = nav.Snmp.Snmp(ip,rw)

    # Fetch the vlan currently on the port
    try:
        fromvlan = snmpget.get(query)
    except (nav.Snmp.NoSuchObjectError, nav.Snmp.TimeOutException), why:
        raise ChangePortVlanError, why

    # If the vlan on the interface is the same as we try to set, do
    # nothing.
    if fromvlan == int(vlan):
        return fromvlan

    # Set to inputvlan. This will fail if the vlan does not exist on
    # the netbox, luckily.

    try:
        snmpset.set(query, type, vlan)
        pass
    except nav.Snmp.AgentError, why:
        raise ChangePortVlanError, why

    # Ok, here comes the tricky part. On HP if we change vlan on a
    # port using dot1qPvid, the fromvlan will put the vlan in
    # trunkmode. To remedy this we use dot1qVlanStaticEgressPorts to
    # fetch and unset the tagged vlans.

    # The good thing about this is that it should work on any netbox
    # that supports Q-BRIDGE-MIB.

    # TODO: Test on other netbox/vendor types
    # TODO: We are fscked if the stuff below fails as we have already
    # changed vlan. Howto fix?

    if vendorid == 'hp':
        # Fetch dot1qVlanStaticEgressPorts
        dot1qVlanStaticEgressPorts = '1.3.6.1.2.1.17.7.1.4.3.1.2.' + \
                                     str(fromvlan)
        try:
            hexports = snmpget.get(dot1qVlanStaticEgressPorts)
        except nav.Snmp.NoSuchObjectError, why:
            raise ChangePortVlanError, why

        # Create new octetstring and set it
        newhexports = computeOctetString(hexports, ifindex, 'disable')

        try:
            snmpset.set(dot1qVlanStaticEgressPorts, 's', newhexports)
            pass
        except nav.Snmp.NoSuchObjectError, why:
            raise ChangePortVlanError, why
    
    return fromvlan



###############################################################################
# toggleSwportStatus
#
def changeSwportStatus(action, swportid):
    """
    Use snmp to change the ifadminstatus on given swportid.
    action = enable, disable
    """

    if not action in ['enable','disable']:
        raise BlockError, "No such action %s" %action

    # Connect to database
    conn = getConnection('default')
    c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    query = """SELECT * FROM netbox
    LEFT JOIN type USING (typeid)
    LEFT JOIN module USING (netboxid)
    LEFT JOIN swport USING (moduleid)
    WHERE swportid = %s"""

    try:
        c.execute(query, (swportid, ))
    except nav.db.driver.ProgrammingError, why:
        raise DbError, why

    row = c.fetchone()

    try:
        changePortStatus(action, row['ip'], row['vendorid'], row['rw'],
                         row['module'], row['port'], row['ifindex'])
    except ChangePortStatusError:
        raise ChangePortStatusError



###############################################################################
# sendmail
#
def sendmail(fromaddr, toaddr, subject, msg):
    """
    Sends mail using mailprogram configured in arnold.conf (default
    sendmail).
    NB: Expects all strings to be in utf-8 format.
    """

    # Get mailprogram from config-file
    mailprogram = config.get('arnold','mailprogram')

    try:
        p = os.popen(mailprogram, 'w')
    except NameError, why:
        raise NoSuchProgramError, mailprogram


    toaddr = "john.m.bredal@ntnu.no"

    # Define charset and set content-transfer-encoding to
    # quoted-printable
    c = email.Charset.Charset('utf-8')
    c.header_encoding = email.Charset.QP
    c.body_encoding = email.Charset.QP

    # Create message-object, fill it and set correct charset.
    m = email.Message.Message()
    h = email.Header.Header(subject, c)
    m['To'] = toaddr
    m['From'] = fromaddr
    m['Subject'] = h

    m.set_charset(c)
    m.set_payload(msg)

    # send mail
    p.write(m.as_string())

    exitcode = p.close()
    if exitcode:
        logger.info("Exit code: %s" % exitcode)


###############################################################################
# addReason
#
def addReason(name, comment, id=0):
    """Add a reason for blocking to the database"""

    id = int(id)

    if id:
        query = """UPDATE blocked_reason SET name=%s, comment=%s
        WHERE blocked_reasonid = %s"""
        doQuery('arnold', query, (name, comment, id))
    else:
        query = "INSERT INTO blocked_reason (name, comment) VALUES (%s, %s)"
        doQuery('arnold', query, (name, comment))


###############################################################################
# getReason
#
def getReasons():
    """
    Returns a dict with the reasons for blocking currently in the
    database
    """

    conn = nav.db.getConnection('default', 'arnold')
    c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    query = "SELECT * FROM blocked_reason ORDER BY blocked_reasonid"
    try:
        c.execute(query)
    except nav.db.driver.ProgrammingError, why:
        raise DbError, why

    return [dict(row) for row in c.fetchall()]


###############################################################################
# getHostName
#
def getHostName(ip):
    """
    Get hostname based on ip-address. Return 'N/A' if not found.
    """

    hostname = "N/A"

    try:
        hostname = socket.gethostbyaddr(ip)[0]
    except socket.herror, why:
        pass

    return hostname


###############################################################################
# getNetbios
#
def getNetbios(ip):
    """
    Get netbiosname of computer with ip
    """

    # Try to locate nmblookup
    status, output = commands.getstatusoutput('which nmblookup')
    if status > 0:
        return 1

    status, output = commands.getstatusoutput(output + " -A " + ip)
    if status > 0:
        return 1

    # For each line in output, try to find name of computer.
    for line in output.split("\n\t"):
        if re.search("<00>", line):
            m = re.search("(\S+)\s+<00>", line)
            return m.group(1) or 1
            
    # If it times out or for some other reason doesn't match...
    return 1


###############################################################################
# doQuery
#
def doQuery(database, query, args):
    """
    Execute a query. Use this for updates/inserts.
    - database: database to execute query in.
    - query:    query with placeholders
    - args:     list/tuple with values for the placeholders
    """

    conn = nav.db.getConnection('default', database)
    c = conn.cursor()

    try:
        c.execute(query, args)
        conn.commit()
    except nav.db.driver.ProgrammingError, why:
        conn.rollback()
        logger.error("doQuery: Error in sql %s: %s" %(query, why))
        raise DbError, why

    # Return oid of insert
    return c.lastrowid

###############################################################################
# checkNonBlock
#
def checkNonBlock(ip):
    """
    Checks if the ip is in the nonblocklist. If it is, returns 1,
    else returns 0.
    """

    #print nonblockdict
    
    # We have the result of the nonblock.cfg-file in the dict
    # nonblockdict. This dict contains 3 things:
    # 1 - Specific ip-addresses
    # 2 - Ip-ranges (129.241.xxx.xxx/xx)
    # 3 - Ip lists (129.241.xxx.xxx-xxx)

    # Specific ip-addresses
    if ip in nonblockdict['ip']:
        return 1

    # Ip-ranges
    for range in nonblockdict['range']:
        if ip in IP(range):
            return 1
        
    return 0


###############################################################################
# computeOctetString
#
def computeOctetString(hexstring, port, action='enable'):
    """
    hexstring: the returnvalue of the snmpquery
    port: the number of the port to add
    """
    
    bit = nav.bitvector.BitVector(hexstring)

    # Add port to string
    port = port - 1
    if action == 'enable':
        bit[port] = 1
    else:
        bit[port] = 0
        
    return str(bit)
