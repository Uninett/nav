# -*- coding: ISO8859-1 -*-
#
# Copyright 2003 Norwegian University of Science and Technology
# Copyright 2006, 2007 UNINETT AS
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
# Authors: Sigurd Gartmann
#          Morten Brekkevold <morten.brekkevold@uninett.no>
#
"""This module is a higher level interface to SNMP query functionality
for NAV, as pysnmp2 is quite low-level and tedious to work with.

The module uses the version 2 branch of pysnmp.
"""
import re
import os
# Make sure Ubuntu/Debian picks the correct pysnmp API version:
os.environ['PYSNMP_API_VERSION'] = 'v2'
import pysnmp # Version 2
from pysnmp import role, v1, v2c, asn1
# Ugly hack to escape inconsistencies in pysnmp2
try:
    v1.RESPONSE
except:
    v1.RESPONSE = v1.GETRESPONSE
from nav.errors import GeneralException
    
class SnmpError(GeneralException):
    """SNMP Error"""

class TimeOutException(SnmpError):
    """Timed out waiting for SNMP response"""
    
class NameResolverException(SnmpError):
    """NameResolverException"""

class NetworkError(SnmpError):
    """NetworkError"""

class AgentError(SnmpError):
    """SNMP agent responded with error"""

class EndOfMibViewError(AgentError):
    """SNMP request was outside the agent's MIB view"""

class UnsupportedSnmpVersionError(SnmpError):
    """Unsupported SNMP protocol version"""

class NoSuchObjectError(SnmpError):
    """SNMP agent did not know of this object"""
    

class Snmp(object):
    """Simple class that provides snmpget, snmpwalk and snmpjog(tm)
    functionality.  Snmpget returns the result as one string.
    Snmpwalk returns the subtree as an array containing OID,
    value-pairs.  Snmpjog returns the result as snmpwalk does, the
    difference is that snmpjog chops off (each line) the OID-prefix
    used in the query.
    """
    def __init__(self, host, community="public", version="1", port=161,
                 retries=3, timeout=1, reporttype=None):
        """
        Makes a new Snmp-object.
        host: hostname
        community: community (password), defaults to "public"
        port: port, defaults to "161"
        """
        
        self.host = host
        self.community = community
        self.version = str(version)
        self.port = int(port)
        self.retries = retries
        self.timeout = timeout
        self.reporttype = reporttype

        self.handle = role.manager()
        self.handle.timeout = float(timeout)


    def get(self,query = "1.3.6.1.2.1.1.1.0"):
        """
        Does snmpget query on the host.
        query: OID to use in the query

        returns the result as a string.
        """

        if not query.startswith("."):
            query = "." + query

        # Choose protocol version specific module
        try:
            snmp = eval('v' + self.version)
        except (NameError, AttributeError):
            raise UnsupportedSnmpVersionError(self.version)

        objectid = asn1.OBJECTID()
        oid = objectid.encode(query)

        # Create SNMP GET request
        req = snmp.GETREQUEST()
        req['community'] = self.community
        req['encoded_oids'] = [oid]

        # Create SNMP response message framework
        rsp = snmp.RESPONSE()

        # Encode SNMP request message and try to send it to SNMP agent and
        # receive a response
        try:
            (answer, src) = self.handle.send_and_receive(
                req.encode(), dst=(self.host, self.port))
        except role.NoResponse, e:
            raise TimeOutException(e)
        except role.NetworkError, n:
            raise NetworkError(n)


        # Decode raw response/answer
        rsp.decode(answer)

        # Check for errors in the response
        self._error_check(rsp)

        # Fetch the value from the response
        rsp_value = asn1.decode(rsp['encoded_vals'][0])[0]

        # Return the value as a proper Python type:
        return rsp_value()


    def set(self, query, type, value):
        """
        Does snmpset query on the host.
        query: oid to use in snmpset
        type: type of value to set. This may be
        i: INTEGER
        u: unsigned INTEGER
        t: TIMETICKS
        a: IPADDRESS
        o: OBJID
        s: OCTETSTRING
        U: COUNTER64 (version 2 and above)
        x: OCTETSTRING
        value: the value to set. Must ofcourse match type: i = 2, s = 'string'
        
        Heavily influenced by:
        http://pysnmp.sourceforge.net/examples/2.x/snmpset.html
        """

        if not query.startswith("."):
            query = "." + query
            
        # Choose protocol version specific module
        try:
            snmp = eval('v' + self.version)
        except (NameError, AttributeError):
            raise UnsupportedSnmpVersionError(self.version)

        # Translate type to fit asn1 library
        if type == 'i': type = 'INTEGER'
        if type == 'u': type = 'UNSIGNED32'
        if type == 't': type = 'TIMETICKS'
        if type == 'a': type = 'IPADDRESS'
        if type == 'o': type = 'OBJECTID'
        if type == 's': type = 'OCTETSTRING'
        if type == 'U': type = 'COUNTER64'
        if type == 'x': type = 'OCTETSTRING'

        # Make request and responsehandler
        req = snmp.SETREQUEST()
        req['community'] = self.community
        rsp = snmp.GETRESPONSE()
            
        # Encode oids and values
        encoded_oids = []
        encoded_vals = []
            
        encoded_oids.append(asn1.OBJECTID().encode(query))
        encoded_vals.append(eval('asn1.'+type+'()').encode(value))
            
        # Try to send query and get response
        try:
            (answer, src) = self.handle.send_and_receive(
                req.encode(encoded_oids=encoded_oids,
                           encoded_vals=encoded_vals),
                dst=(self.host, self.port))
                
            # Decode response (an octet-string) into an snmp-message
            rsp.decode(answer)
                
            if rsp['error_status']:
                raise AgentError, str(snmp.SNMPError(rsp['error_status']))
            
        except (role.NoResponse, role.NetworkError), why:
            raise NetworkError, why
            
            
    def walk(self,query = "1.3.6.1.2.1.1.1.0"):
        """
        Does snmpwalk on the host.
        query: OID to use in the query

        returns an array containing key-value-pairs, where the
        returned OID is the key.
        """
        if not query.startswith("."):
            query = "." + query
        
        # Choose protocol version specific module
        try:
            snmp = eval('v' + self.version)
        except (NameError, AttributeError):
            raise UnsupportedSnmpVersionError(self.version)

        result = []
        root_oid = asn1.OBJECTID()
        root_oid.encode(query)

        # Create SNMP GETNEXT request
        req = snmp.GETNEXTREQUEST()
        req['community'] = self.community
        req['encoded_oids'] = [root_oid.encode()]

        # Create a response message framework
        rsp = snmp.RESPONSE()

        current_oid = root_oid
        # Traverse agent MIB
        while 1:
            # Encode SNMP request message and try to send it to SNMP agent and
            # receive a response
            try:
                (answer, src) = self.handle.send_and_receive(
                    req.encode(), dst=(self.host, self.port))
            except role.NoResponse, e:
                raise TimeOutException(e)
            except role.NetworkError, n:
                raise NetworkError(n)


            # Decode raw response/answer
            rsp.decode(answer)

            # Check for errors in the response
            try:
                self._error_check(rsp)
            except EndOfMibViewError:
                # We just fell off the face of the earth (or walked outside the
                # agent's MIB view).  Return whatever results we got.
                return result

            # Fetch the (first) Object ID and value pair from the response,
            # (there shouldn't be more than one pair)
            rsp_oid = asn1.decode(rsp['encoded_oids'][0])[0]
            rsp_value = asn1.decode(rsp['encoded_vals'][0])[0]

            # Check for reasons to stop walking
            if not root_oid.isaprefix(rsp_oid()):
                # If the current GETNEXT response came from outside the
                # tree we are traversing, get the hell out of here, we're
                # done walking the subtree.
                return result
            elif rsp_oid == current_oid:
                # If the GETNEXT response contains the same object ID as the
                # request, something has gone wrong, and we didn't see it
                # further up.  Just return whatever results we got.
                return result
            else:
                result.append((rsp_oid(), rsp_value()))

            # Update request ID
            req['request_id'] += 1

            # Load the next request with the OID received in the last response
            req['encoded_oids'] = rsp['encoded_oids']
            current_oid = rsp_oid
    
    def jog(self,query = "1.3.6.1.2.1.1.1.0"):
        """Does a modified snmpwalk on the host. The query OID is
        chopped off the returned OID for each line in the result.
        query: OID to use in the query

        returns an array containing key-value-pairs, where the key is
        the returned OID minus the OID in the query, i.e query: 1.2.3,
        snmpwalk returned oid:1.2.3.4.5, snmpjog returned key: 4.5
        """
        walked = self.walk(query)
        result = []
        if walked:
            for oid,value in walked:
                #found = re.search(query,oid)
                key = re.sub('\.?' + query + '\.?','',oid)
                result.append((key,value))
        
        return result

    def bulkwalk(self,query = "1.3.6.1.2.1.1.1.0", strip_prefix=False):
        """
        Performs an SNMP walk on the host, using GETBULK requests.
        Will raise an UnsupportedSnmpVersionError if the current
        version is anything other than 2c.
        
          query: OID to use in the query

          strip_prefix: If True, strips the query OID prefix from the
                        response OIDs.

        returns an array containing key-value-pairs, where the
        returned OID is the key.
        """
        if str(self.version) != "2c":
            raise UnsupportedSnmpVersionError(
                "Cannot use BULKGET in SNMP version " + self.version)
        
        if not query.startswith("."):
            query = "." + query
        
        # Choose protocol version specific module
        snmp = v2c

        result = []
        root_oid = asn1.OBJECTID()
        root_oid.encode(query)

        # Create SNMP GETNEXT request
        req = snmp.GETBULKREQUEST()
        req['community'] = self.community
        req['encoded_oids'] = [root_oid.encode()]
        req['max_repetitions'] = 256

        # Create a response message framework
        rsp = snmp.RESPONSE()

        current_oid = root_oid
        # Traverse agent MIB
        while 1:
            # Encode SNMP request message and try to send it to SNMP agent and
            # receive a response
            try:
                (answer, src) = self.handle.send_and_receive(
                    req.encode(), dst=(self.host, self.port))
            except role.NoResponse, e:
                raise TimeOutException(e)
            except role.NetworkError, n:
                raise NetworkError(n)

            # Decode raw response/answer
            rsp.decode(answer)

            # Check for errors in the response
            try:
                self._error_check(rsp)
            except EndOfMibViewError:
                # Since we are retrieving multiple values, this SNMP
                # exception must be handled in the loop below instead
                pass

            last_response_oid = None
            for encoded_oid, encoded_val in \
                    zip(rsp['encoded_oids'], rsp['encoded_vals']):
                rsp_oid = asn1.decode(encoded_oid)[0]
                rsp_value = asn1.decode(encoded_val)[0]

                # Check for reasons to stop walking
                if isinstance(rsp_value, asn1.endOfMibView):
                    # Nothing more to see here, move along
                    return result
                if not root_oid.isaprefix(rsp_oid()):
                    # If the current value came from outside the tree we
                    # are traversing, get the hell out of here, we're done
                    # walking the subtree.
                    return result
                elif rsp_oid == current_oid:
                    # If the GETNEXT response contains the same object
                    # ID as the request, something has gone wrong, and
                    # we didn't see it further up.  Just return
                    # whatever results we got.
                    return result
                else:
                    oid = rsp_oid()
                    if strip_prefix:
                        oid = oid[len(query)+1:]
                    result.append((oid, rsp_value()))
                    last_response_oid = rsp_oid

            # Update request ID
            req['request_id'] += 1

            # Load the next request with the last OID received in the
            # last response
            req['encoded_oids'] = rsp['encoded_oids'][-1:]
            current_oid = last_response_oid

    def _error_check(self, rsp):
        """Check a decoded response structure for agent errors or exceptions,
        and raise Python exceptions accordingly."""
        # Check for remote SNMP agent failure (v1)
        if rsp['error_status']:
            error_index = rsp['error_index']-1
            error_oid = asn1.decode(rsp['encoded_oids'][error_index])[0]
            error_value = asn1.decode(rsp['encoded_oids'][error_index])[0]
            # Error status 2 means noSuchName (i.e. the OID asked for
            # doesn't exist in the agent's MIB view)
            if rsp['error_status'] == 2:
               raise NoSuchObjectError(error_oid())
            else:
               raise AgentError("Error code %s at index %s (%s, %s)" % \
                                (rsp['error_status'],
                                 rsp['error_index'],
                                 error_oid,
                                 error_value))

        rsp_oids = [asn1.decode(o)[0] for o in rsp['encoded_oids']]
        rsp_values = [asn1.decode(v)[0] for v in rsp['encoded_vals']]

        for rsp_oid, rsp_value in zip(rsp_oids, rsp_values):
            # Check for SNMP v2c agent exceptions
            if isinstance(rsp_value, (asn1.noSuchObject, asn1.noSuchInstance)):
                raise NoSuchObjectError(rsp_oid)
            elif isinstance(rsp_value, asn1.endOfMibView):
                raise EndOfMibViewError(rsp_oid())
