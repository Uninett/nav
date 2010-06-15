#
# Copyright (C) 2003 Norwegian University of Science and Technology
# Copyright (C) 2006, 2007, 2010 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""High level NAV API for PySNMP SE."""
import re
import os
from errors import *

from pysnmp.asn1.oid import OID
from pysnmp.mapping.udp import error as snmperror
from pysnmp.mapping.udp.role import Manager
from pysnmp.proto.api import alpha

def oid_to_str(oid):
    """Converts an OID object/tuplet to a dotted string representation."""
    if not isinstance(oid, basestring):
        oid = "." + ".".join(str(i) for i in oid)
    return oid

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
        if self.version == '1':
            self._ver = alpha.protoVersions[alpha.protoVersionId1]
        elif self.version.startswith('2'):
            self._ver = alpha.protoVersions[alpha.protoVersionId2c]
        else:
            raise UnsupportedSnmpVersionError(self.version)
        self.port = int(port)
        self.retries = retries
        self.timeout = timeout
        self.reporttype = reporttype

        self.handle = Manager()
        self.handle.timeout = float(timeout)


    def get(self,query = "1.3.6.1.2.1.1.1.0"):
        """
        Does snmpget query on the host.
        query: OID to use in the query

        returns the result as a string.
        """

        if not query.startswith("."):
            query = "." + query

        # Create SNMP GET request
        req = self._ver.Message()
        req.apiAlphaSetCommunity(self.community)
        pdu = self._ver.GetRequestPdu()
        pdu.apiAlphaSetVarBindList((query, self._ver.Null()))
        req.apiAlphaSetPdu(pdu)

        # Encode SNMP request message and try to send it to SNMP agent and
        # receive a response
        try:
            self.handle.send(
                req.berEncode(), dst=(self.host, self.port))
            (answer, src) = self.handle.receive()
        except snmperror.NoResponseError, e:
            raise TimeOutException(e)
        except snmperror.NetworkError, e:
            raise NetworkError(e)

        # Decode raw response/answer
        rsp = self._ver.Message()
        rsp.berDecode(answer)

        # ensure the response matches the request
        if not req.apiAlphaMatch(rsp):
            raise SnmpException("Response did not match request")

        # Check for errors in the response
        self._error_check(rsp)

        # Fetch the value from the response
        var_bind = rsp.apiAlphaGetPdu().apiAlphaGetVarBindList()[0]
        oid, value = var_bind.apiAlphaGetOidVal()

        # Return the value
        if isinstance(value, (OID, self._ver.ObjectIdentifier)):
            realvalue = oid_to_str(value)
        else:
            realvalue = value.get()
        return realvalue


    def set(self, query, type, value):
        """Does snmpset query on the host.

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

        """
        # Translate type to fit backend library
        typemap = {
            'i': 'Integer',
            'u': 'Unsigned32',
            't': 'TimeTicks',
            'a': 'IpAddress',
            'o': 'ObjectIdentifier',
            's': 'OctetString',
            'U': 'Counter64',
            'x': 'OctetString',
        }
        if type in typemap:
            value_class = typemap[type]
            if not hasattr(self._ver, value_class):
                raise ValueError("%s not supported in SNMP version %s" %
                                 (value_class, self.version))
            else:
                value_class = getattr(self._ver, value_class)
        else:
            raise ValueError("type must be one of %r, not %r" %
                             (typemap.keys(), type))

        # Make request and responsehandler
        pdu = self._ver.SetRequestPdu()
        req = self._ver.Message()
        req.apiAlphaSetCommunity(self.community)
        req.apiAlphaSetPdu(pdu)

        # Encode oids and values
        obj = OID(query)
        obj_val = value_class(value)
        pdu.apiAlphaSetVarBindList((obj, obj_val))

        # Try to send query and get response
        try:
            self.handle.send(
                req.berEncode(), dst=(self.host, self.port))
            (answer, src) = self.handle.receive()
        except snmperror.NoResponseError, e:
            raise TimeOutException(e)
        except snmperror.NetworkError, e:
            raise NetworkError(e)

        # Decode raw response/answer
        rsp = self._ver.Message()
        rsp.berDecode(answer)

        # ensure the response matches the request
        if not req.apiAlphaMatch(rsp):
            raise SnmpException("Response did not match request")

        # Check for errors in the response
        self._error_check(rsp)

    def walk(self,query = "1.3.6.1.2.1.1.1.0"):
        """
        Does snmpwalk on the host.
        query: OID to use in the query

        returns an array containing key-value-pairs, where the
        returned OID is the key.
        """

        result = []
        root_oid = OID(query)

        # Create SNMP GETNEXT request
        req = self._ver.Message()
        req.apiAlphaSetCommunity(self.community)
        pdu = self._ver.GetNextRequestPdu()
        pdu.apiAlphaSetVarBindList((query, self._ver.Null()))
        req.apiAlphaSetPdu(pdu)

        current_oid = root_oid
        # Traverse agent MIB
        while 1:
            # Encode SNMP request message and try to send it to SNMP agent and
            # receive a response
            try:
                self.handle.send(
                    req.berEncode(), dst=(self.host, self.port))
                (answer, src) = self.handle.receive()
            except snmperror.NoResponseError, e:
                raise TimeOutException(e)
            except snmperror.NetworkError, e:
                raise NetworkError(e)

            # Decode raw response/answer
            rsp = self._ver.Message()
            rsp.berDecode(answer)

            # ensure the response matches the request
            if not req.apiAlphaMatch(rsp):
                raise SnmpException("Response did not match request")

            # Check for errors in the response
            try:
                self._error_check(rsp)
            except EndOfMibViewError:
                # We just fell off the face of the earth (or walked outside the
                # agent's MIB view).  Return whatever results we got.
                return result

            # Fetch the (first) Object ID and value pair from the response,
            # (there shouldn't be more than one pair)
            varbind = rsp.apiAlphaGetPdu().apiAlphaGetVarBindList()[0]
            name, value = varbind.apiAlphaGetOidVal()
            response_oid = name.get()

            # Check for reasons to stop walking
            if not root_oid.isaprefix(response_oid):
                # If the current GETNEXT response came from outside the
                # tree we are traversing, get the hell out of here, we're
                # done walking the subtree.
                return result
            elif response_oid == current_oid:
                # If the GETNEXT response contains the same object ID as the
                # request, something has gone wrong, and we didn't see it
                # further up.  Just return whatever results we got.
                return result
            else:
                # The Snmp API uses string-based OIDs, not tuples or objects,
                # so convert if needed:
                if isinstance(value, (OID, self._ver.ObjectIdentifier)):
                    realvalue = oid_to_str(value)
                else:
                    realvalue = value.get()
                result.append((oid_to_str(response_oid), realvalue))

            # Update request ID
            new_id = pdu.apiAlphaGetRequestId() + 1
            pdu.apiAlphaSetRequestId(new_id)

            # Load the next request with the OID received in the last response
            pdu.apiAlphaSetVarBindList((response_oid, self._ver.Null()))
            current_oid = response_oid

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

        result = []
        root_oid = OID(query)

        # Create SNMP GETNEXT request
        req = self._ver.Message()
        req.apiAlphaSetCommunity(self.community)
        pdu = self._ver.GetBulkRequestPdu()
        pdu.apiAlphaSetVarBindList((query, self._ver.Null()))
        pdu.apiAlphaSetMaxRepetitions(256)
        req.apiAlphaSetPdu(pdu)

        current_oid = root_oid
        # Traverse agent MIB
        while 1:
            # Encode SNMP request message and try to send it to SNMP agent and
            # receive a response
            try:
                self.handle.send(
                    req.berEncode(), dst=(self.host, self.port))
                (answer, src) = self.handle.receive()
            except snmperror.NoResponseError, e:
                raise TimeOutException(e)
            except snmperror.NetworkError, e:
                raise NetworkError(e)

            # Decode raw response/answer
            rsp = self._ver.Message()
            rsp.berDecode(answer)

            # Check for errors in the response
            try:
                self._error_check(rsp)
            except EndOfMibViewError:
                # Since we are retrieving multiple values, this SNMP
                # exception must be handled in the loop below instead
                pass

            last_response_oid = None
            for varbind in rsp.apiAlphaGetPdu().apiAlphaGetVarBindList():
                name, value = varbind.apiAlphaGetOidVal()
                rsp_oid = name.get()

                # Check for reasons to stop walking
                if isinstance(value, self._ver.EndOfMibView):
                    # Nothing more to see here, move along
                    return result
                if not root_oid.isaprefix(rsp_oid):
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
                    oid = rsp_oid
                    if strip_prefix:
                        oid = oid[len(root_oid):]
                    # The Snmp API uses string-based OIDs, not tuples or objects,
                    # so convert if needed:
                    if isinstance(value, (OID, self._ver.ObjectIdentifier)):
                        realvalue = oid_to_str(value)
                    else:
                        realvalue = value.get()

                    result.append((oid_to_str(oid), realvalue))
                    last_response_oid = rsp_oid

            # Update request ID
            new_id = pdu.apiAlphaGetRequestId() + 1
            pdu.apiAlphaSetRequestId(new_id)

            # Load the next request with the last OID received in the
            # last response
            pdu.apiAlphaSetVarBindList((last_response_oid, self._ver.Null()))
            current_oid = last_response_oid

    def _error_check(self, rsp):
        """Check a decoded response structure for agent errors or exceptions,
        and raise Python exceptions accordingly."""
        error_status = rsp.apiAlphaGetPdu().apiAlphaGetErrorStatus()
        if error_status:
            # Error status 2 means noSuchName (i.e. the OID asked for
            # doesn't exist in the agent's MIB view)
            if int(error_status) == 2:
                raise NoSuchObjectError("No such name")
            else:
                raise AgentError("Error in response: %s" % error_status)
            # Cases we should handle include

        # Check the varbind list for snmp v2c exceptions
        varbinds = rsp.apiAlphaGetPdu().apiAlphaGetVarBindList()
        for varbind in varbinds:
            obj, value = varbind.apiAlphaGetOidVal()
            if isinstance(value,
                         (self._ver.NoSuchObject, self._ver.NoSuchInstance)):
                raise NoSuchObjectError(obj)
            elif isinstance(value, self._ver.EndOfMibView):
                raise EndOfMibViewError(obj)
