# -*- coding: ISO8859-1 -*-
#
# Copyright 2003 Norwegian University of Science and Technology
# Copyright 2006 UNINETT AS
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
#          Morten Vold <morten.vold@uninett.no>
#
"""This module is a higher level interface to SNMP query functionality
for NAV, as pysnmp2 is quite low-level and tedious to work with.

The module uses the version 2 branch of pysnmp.
"""
import re
import exceptions
import pysnmp # Version 2
from pysnmp import role, v1, v2c, asn1
# Ugly hack to escape inconsistencies in pysnmp2
try:
    v1.RESPONSE
except:
    v1.RESPONSE = v1.GETRESPONSE
    
class TimeOutException(exceptions.Exception):
    def __init__(self, err_msg=None):
        exceptions.Exception.__init__(self)

        if err_msg is not None:
            self.err_msg = str(err_msg)
        else:
            self.err_msg = ''

    def __str__(self):
        return self.err_msg

    def __repr__(self):
        return self.__class__.__name__ + '(' + self.err_msg + ')'
    
class NameResolverException(exceptions.Exception):
    def __init__(self, err_msg=None):
        exceptions.Exception.__init__(self)

        if err_msg is not None:
            self.err_msg = str(err_msg)
        else:
            self.err_msg = ''

    def __str__(self):
        return self.err_msg

    def __repr__(self):
        return self.__class__.__name__ + '(' + self.err_msg + ')'
    

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

        self.handle = role.manager((host,port))


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
            raise 'Unsupported SNMP protocol version: %s' % (self.version)

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
            (answer, src) = self.handle.send_and_receive(req.encode())
        except role.NoResponse, e:
            #timeout
            raise TimeOutException(e)
        except role.NetworkError, n:
            #dns
            raise NameResolverException(n)

        # Decode raw response/answer
        rsp.decode(answer)
        # Fetch Object ID's and associated values
        oids = [objectid.decode(o)[0] for o in rsp['encoded_oids']]
        values = [asn1.decode(v)[0] for v in rsp['encoded_vals']]

        # Check for remote SNMP agent failure
        if rsp['error_status']:
            raise "Snmp error %s at %s (%s, %s)" % \
                  (rsp['error_status'],
                   rsp['error_index'],
                   oids[rsp['error_index']-1],
                   values[rsp['error_index']-1])

        # Since we're only asking for one value, only return the first
        # result, decoded to its correct Python data type
        return values[0]()


    def walk(self,query = "1.3.6.1.2.1.1.1.0"):
        """
        Does snmpwalk on the host.
        query: OID to use in the query

        returns an array containing key-value-pairs, where the
        returned OID is the key.
        """
        if not query.startswith("."):
            query = "." + query
        
        try:
            snmp = eval('v' + self.version)
        except (NameError, AttributeError):
            raise 'Unsupported SNMP protocol version: %s' % (self.version)

        result = []
        root_oid = asn1.OBJECTID()
        root_oid.encode(query)

        # Create SNMP GET/GETNEXT request
        req = snmp.GETREQUEST()
        nextReq = snmp.GETNEXTREQUEST()
        for r in (req, nextReq):
            r['community'] = self.community
            r['encoded_oids'] = [root_oid.encode()]

        # Create a response message framework
        rsp = snmp.RESPONSE()

        # Traverse agent MIB
        while 1:
            # Encode SNMP request message and try to send it to SNMP agent and
            # receive a response
            try:
                (answer, src) = self.handle.send_and_receive(req.encode())
            except role.NoResponse, e:
                raise TimeOutException(e)
            except role.NetworkError, n:
                raise NameResolverException(n)


            # Decode raw response/answer
            rsp.decode(answer)
            # Fetch Object ID's and associated values
            oids = [asn1.OBJECTID().decode(o)[0] for o in rsp['encoded_oids']]
            values = [asn1.decode(v)[0] for v in rsp['encoded_vals']]

            # Check for remote SNMP agent failure
            if rsp['error_status']:
                # SNMP agent reports 'no such name' when walk is over
                if rsp['error_status'] == 2:
                    # Switch over to GETNEXT req on error
                    # XXX what if one of multiple vars fails?
                    if not (req is nextReq):
                        req = nextReq
                        continue
                else:
                    raise "Snmp error %s at %s (%s, %s)" % \
                          (rsp['error_status'],
                           rsp['error_index'],
                           oids[rsp['error_index']-1],
                           values[rsp['error_index']-1])

            # If the current GETNEXT response came from outside the
            # tree we are traversing, get the hell out of here, we're
            # done walking the subtree.
            if not root_oid.isaprefix(oids[0]):
                return result
            else:
                result.append((oids[0], values[0]()))

            # Update request ID
            req['request_id'] += 1

            # Switch over GETNEXT PDU for if not done
            if not (req is nextReq):
                req = nextReq

            # Load the next request with the OID received in the last response
            req['encoded_oids'] = rsp['encoded_oids']
    
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
