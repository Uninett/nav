"""
Provides helpfunctions for Arnold web and script
"""

import nav.Snmp
import re
import nav.buildconf
import ConfigParser
from IPy import IP
from socket import gethostbyaddr
from nav.db import getConnection
from nav.util import isValidIP
from nav.errors import GeneralException

# Connect to database
conn = getConnection('default')
arnolddb = getConnection('default', 'arnold')

class ChangePortStatusError(GeneralException):
    "An error occured when changing portadminstatus"
    pass

class NoDatabaseInformationError(GeneralException):
    "Could not find information in database for id"
    pass

class PortNotFoundError(GeneralException):
    "Could not find port in database"
    pass

class UnknownTypeError(GeneralException):
    "Unknown type"
    pass

class DbError(GeneralException):
    "Error when querying database"
    pass

class NotSupportedError(GeneralException):
    "This vendor does not support snmp set of vlan"
    pass

class AlreadyBlockedError(GeneralException):
    "This port is already blocked."
    pass

class InExceptionListError(GeneralException):
    "This ip-address is in the exceptionlist and cannot be blocked."
    pass

class FileError(GeneralException):
    "Fileerror"
    pass


# Config-file
configfile = nav.buildconf.sysconfdir + "/arnold/arnold.conf"
config = ConfigParser.ConfigParser()
config.read(configfile)



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


###################################################################################################
# findIdInformation
#
def findIdInformation(id, limit):
    """
    Look in arp and cam tables to find id (which is either ip or
    mac-address). Returns a list with $limit number of dicts
    containing all info from arp and cam joined on mac.
    """

    # Find type of id
    (type,id) = findInputType(id)
    #print "%s is of type %s" %(id, type)

    result = []
    # Get data from database based on id
    if type in ['IP','MAC','SWPORTID']:

        c = conn.cursor()

        # Based on type, use the correct query to find information in the database about id and the switch
        query = """SELECT DISTINCT ON (cam.end_time, cam.netboxid, module, port) *, cam.end_time as endtime FROM arp RIGHT JOIN cam USING (mac)
        WHERE %s=%%s
        AND module IS NOT NULL
        AND port IS NOT NULL
        AND ifindex IS NOT NULL
        ORDER BY cam.end_time DESC LIMIT %%s""" %type.lower()
        
        # Find mac and ip-address of id.
        try:
            c.execute(query, (id, limit))
        except Exception, e:
            print "Error when executing \"%s\" query %s" %(type, e)
            return 1

        if c.rowcount > 0:
            result = c.dictfetchall()
        else:
            result = 1
        
    else:
        raise UnknownTypeError, id

    if result == 1:
        raise NoDatabaseInformationError, id

    return result


###################################################################################################
# findSwportinfo
#
def findSwportinfo(netboxid, ifindex, module, port):
    """
    Find netbox and swportinfo based on input. Return dict with
    info. The dict contains everything from netbox, type, module and
    swport tables related to the id. Also ipaddress, macaddress and
    endtime of id IF AND ONLY IF the id is not an swport.
    """
    c = conn.cursor()

    try:
        query = """SELECT * FROM netbox
        LEFT JOIN type USING (typeid)
        LEFT JOIN module USING (netboxid)
        LEFT JOIN swport USING (moduleid)
        WHERE netboxid=%s
        AND ifindex=%s
        AND module=%s
        AND port=%s"""

        c.execute(query, (netboxid, ifindex, module, port))
    except Exception, e:
        print "Error when executing query \"%s\": %s" %(query, e)
        return 1

    if c.rowcount > 0:
        result = c.dictfetchone()
        
        return result
    else:
        raise PortNotFoundError, (netboxid, ifindex, module,port)


    return 1


###################################################################################################
# findSwportIDinfo
#
def findSwportIDinfo(swportid):
    """
    Join results from netbox, type, module and swport tables based on
    swportid. Returns a dict with info. Same as findSwportinfo only it
    takes other input.
    """

    c = conn.cursor()

    # Get switch-information
    swquery = """SELECT * FROM netbox
    LEFT JOIN type USING (typeid)
    LEFT JOIN module USING (netboxid)
    LEFT JOIN swport USING (moduleid)
    WHERE swportid = %s"""

    try:
        c.execute(swquery, (swportid,))
    except nav.db.driver.ProgrammingError, why:
        raise DbError, why

    if c.rowcount > 0:
        return c.dictfetchone()
    else:
        raise PortNotFoundError, swportid

    return 1



###################################################################################################
# findInputType
#
def findInputType (input):
    """Try to determine whether input is a valid ip-address,
    mac-address or an swportid. Return type and reformatted input as a
    tuple"""

    # Support mac-adresses on xx:xx... format
    input = input.replace(':','')

    if isValidIP(input) and re.match('\d+\.\d+\.\d+\.\d+', input):
        return ("IP", input)
    elif re.match("^[A-Fa-f0-9]{12}$", input):
        return ("MAC",input)
    elif re.match("^\d+$", input):
        return ("SWPORTID",input)

    return ("UNKNOWN",input)


###################################################################################################
# blockPort
#
def blockPort(id, sw, autoenable, autoenablestep, determined, reason, comment, username):
    """Block the port and update database"""

    c = arnolddb.cursor()

    # Check if this id is in the nonblocklist
    if checkNonBlock(id['ip']):
        raise InExceptionListError
        
    
    # Find dns and netbios
    dns = getHostName(id['ip'])
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
        raise DbError, why

    res = c.dictfetchone()


    # if yes and active: do nothing, raise AlreadyBlockedError
    if c.rowcount > 0 and res['blocked_status'] == 'disabled':
        raise AlreadyBlockedError


    elif c.rowcount > 0 and res['blocked_status'] == 'enabled':
        ######################################################
        # block port, update identity, create new event

        print "Found existing row, updating."

        try:
            changePortStatus('disable', sw['ip'], sw['vendorid'], sw['rw'], sw['module'], sw['port'], sw['ifindex'])
        except ChangePortStatusError:
            raise ChangePortStatusError


        # Update existing identity
        query = """UPDATE identity SET
        blocked_status = %%s,
        blocked_reasonid = %%s,
        swportid = %%s,
        ip = %%s,
        mac = %%s,
        dns = %%s,
        netbios = %%s,
        lastchanged = now(),
        autoenable = %s,
        autoenablestep = %%s,
        mail = %%s,
        determined = %%s
        WHERE identityid = %%s
        """ %autoenable

        arglist = ['disabled', reason, sw['swportid'], id['ip'], id['mac'], dns, netbios, autoenablestep, "", determined, res['identityid']]

        doQuery('arnold', query, arglist)


        # Create new event
        query = """INSERT INTO event
        (identityid, event_comment, blocked_status, blocked_reasonid, eventtime, autoenablestep, username)
        VALUES (%s, %s, %s, %s, now(), %s, %s)
        """

        arglist = [res['identityid'], comment, 'disabled' , reason, autoenablestep, username]

        doQuery('arnold', query, arglist)


    else:
        #########################################################
        # block port, create identity, create first event

        print "No existing row found, inserting"

        try:
            changePortStatus('disable', id['ip'], sw['vendorid'], sw['rw'], sw['module'], sw['port'], sw['ifindex'])
        except ChangePortStatusError:
            raise ChangePortStatusError


        # Get nextvalue of sequence to use in both queries
        nextvalq = "SELECT nextval('public.identity_identityid_seq')"
        try:
            c.execute(nextvalq)
        except nav.db.driver.ProgrammingError, why:
            raise DbError, why

        nextval = c.fetchone()[0]


        # Create new identitytuple
        query = """
        INSERT INTO identity
        (identityid, blocked_status, blocked_reasonid, swportid, ip, mac, dns, netbios, starttime, lastchanged, autoenable, autoenablestep, mail, determined)
        VALUES (%%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s, now(), now(), %s, %%s, %%s, %%s)
        """ %autoenable

        arglist = [nextval, 'disabled', reason, sw['swportid'], id['ip'], id['mac'], dns, netbios, autoenablestep, "", determined]

        print arglist

        doQuery('arnold', query, arglist)


        # CReate new event-tuple
        query = """INSERT INTO event
        (identityid, event_comment, blocked_status, blocked_reasonid, eventtime, autoenablestep, username)
        VALUES (%s, %s, %s, %s, now(), %s, %s)
        """
    
        arglist = [nextval, comment, 'disabled' , reason, autoenablestep, username]

        doQuery('arnold', query, arglist)

        

###################################################################################################
# openPort
#
def openPort(id, username):
    """
    Takes as input the identityid of the block and opens the port
    and updates the database
    """

    carnold = arnolddb.cursor()
    cmanage = conn.cursor()

    # Find identityidinformation
    query = """SELECT * FROM identity WHERE identityid = %s"""
    carnold.execute(query, (id, ))

    if carnold.rowcount <= 0:
        raise NoDatabaseInformationError, id

    identityrow = carnold.dictfetchone()

    # Fetch info for this swportid
    swportidquery = """SELECT * FROM netbox
    LEFT JOIN type USING (typeid)
    LEFT JOIN module USING (netboxid)
    LEFT JOIN swport USING (moduleid)
    WHERE swportid = %s"""

    cmanage.execute(swportidquery, (identityrow['swportid'], ))

    if cmanage.rowcount <= 0:
        raise NoDatabaseInformationError, id

    row = cmanage.dictfetchone()

    # Enable port based on information gathered
    try:
        changePortStatus('enable', row['ip'], row['vendorid'], row['rw'], row['module'], row['port'], row['ifindex'])
    except ChangePortStatusError, why:
        raise ChangePortStatusError
    

    # Update identity-table
    updateq = """UPDATE identity SET
    lastchanged = now(),
    blocked_status = 'enabled'
    WHERE identityid = %s"""

    try:
        carnold.execute(updateq, (id, ))
    except nav.db.driver.ProgrammingError, why:
        arnolddb.rollback()
        raise DbError, why

    # Update event-table
    eventq = """INSERT INTO event
    (identityid, blocked_status, eventtime, username) VALUES
    (%s, 'enabled', now(), %s)"""

    try:
        carnold.execute(eventq, (id, username))
        arnolddb.commit()
    except nav.db.driver.ProgrammingError, why:
        arnolddb.rollback()
        raise DbError, why
        

###################################################################################################
# changePortStatus
#
def changePortStatus(action, ip, vendorid, community, module, port, ifindex):
    """
    Use SNMP to disable a interface.
    - Action must be 'enable' or 'disable'.
    - Community must be read/write community
    """

    # We use ifadminstatus to enable and disable ports
    # ifAdminStatus has the following values:
    # 1 - up
    # 2 - down
    # 3 - testing (no operational packets can be passed)
    oid = '.1.3.6.1.2.1.2.2.1.7'

    # We need to check for hp as they don't use the normal ifindex
    # notation
    if vendorid == 'hp':
        # Ensure that module is a string
        module = str(module)
        if int(module) > 0:
            community = community + "@sw" + module

        ifindex = str(ifindex)[-2:]


    query = oid + '.' + str(ifindex)

    print "vendor: %s, ro: %s, ifindex: %s" %(vendorid, community, ifindex)

    # Create snmp-object
    s = nav.Snmp.Snmp(ip,community)


    # Disable or enable based on input
    try:
        if action == 'disable':
            #s.set(query, 'i', 2)
            pass
        elif action == 'enable':
            #s.set(query, 'i', 1)
            pass
        
    except nav.Snmp.AgentError, why:
        raise ChangePortStatusError, why



###################################################################################################
# changePortVlan
#
def changePortVlan(ip, vendorid, ro, rw, ifindex, vlan):
    """
    Use SNMP to change switchport access vlan. Returns vlan on port
    before change if successful.

    Reasons for not succesfull change may be:
    - Wrong community, use rw-community
    - rw-community not set on netbox
    """

    # oid for getting and setting vlan
    # CISCO
    # cisco.ciscoMgmt.ciscoVlanMembershipMIB.ciscoVlanMembershipMIBObjects.vmMembership.vmMembershipTable.vmMembershipEntry.vmVlan.<ifindex>
    if vendorid == 'cisco':
        oid = "1.3.6.1.4.1.9.9.68.1.2.2.1.2"
    else:
        # Nothing else supported :p
        raise NotSupportedError, vendorid


    # Check vlanformat
    if not re.search('\d+', str(vlan)):
        raise ChangePortStatusError, "Wrong format on vlan %s" %vlan


    query = oid + '.' + str(ifindex)


    # Create snmp-object
    snmpget = nav.Snmp.Snmp(ip,ro)
    snmpset = nav.Snmp.Snmp(ip,rw)


    # Regardless of disable or enable, the input-vlan should be the
    # vlan you want to switch to.
    try:
        fromvlan = snmpget.get(query)
    except nav.Snmp.NoSuchObjectError, why:
        raise ChangePortStatusError, why

    # Set to inputvlan

    try:
        snmpset.set(query, 'i', vlan)
    except nav.Snmp.AgentError, why:
        raise ChangePortStatusError, why
    
    return fromvlan



###################################################################################################
# toggleSwportStatus
#
def changeSwportStatus(action, swportid):
    """
    Use snmp to change the ifadminstatus on given swportid.
    action = enable, disable
    """

    if not action in ['enable','disable']:
        raise BlockError, "No such action %s" %action

    c = conn.cursor()

    query = """SELECT * FROM netbox
    LEFT JOIN type USING (typeid)
    LEFT JOIN module USING (netboxid)
    LEFT JOIN swport USING (moduleid)
    WHERE swportid = %s"""

    try:
        c.execute(query, (swportid, ))
    except nav.db.driver.ProgrammingError, why:
        raise DbError, why

    row = c.dictfetchone()

    try:
        changePortStatus(action, row['ip'], row['vendorid'], row['rw'], row['module'], row['port'])
    except ChangePortStatusError:
        raise ChangePortStatusError



###################################################################################################
# sendmail
#
def sendmail():
    """
    NOT IMPLEMENTED: Sends mail.
    """

    pass


###################################################################################################
# addReason
#
def addReason(name, comment):
    """Add a reason for blocking to the database"""

    query = "INSERT INTO blocked_reason (name, comment) VALUES (%s, %s)"
    doQuery('arnold', query, (name, comment))


###################################################################################################
# getReason
#

def getReasons():
    """Returns a dict with the reasons for blocking currently in the database"""

    conn = nav.db.getConnection('default', 'arnold')
    c = conn.cursor()

    query = "SELECT * FROM blocked_reason"
    try:
        c.execute(query)
    except nav.db.driver.ProgrammingError, why:
        raise DbError, why

    return c.dictfetchall()


###################################################################################################
# getHostName
#
def getHostName(ip):
    """
    Get hostname based on ip-address. Return 'N/A' if not found.
    """

    hostname = "N/A"

    try:
        hostname = gethostbyaddr(ip)[0]
    except socket.herror, why:
        pass

    return hostname
    

###################################################################################################
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
        raise DbError, why

    # Return oid of insert
    return c.lastrowid

###################################################################################################
# checkNonBlock
#
def checkNonBlock(ip):
    """
    Checks if the ip is in the nonblocklist. If it is, returns 1,
    else returns 0.
    """

    print nonblockdict

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

