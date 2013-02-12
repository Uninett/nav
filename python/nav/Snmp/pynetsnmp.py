#
# Copyright (C) 2013 UNINETT
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
"""High level synchronouse NAV API for NetSNMP"""

from __future__ import absolute_import
from _ctypes import POINTER
from pynetsnmp.CONSTANTS import SNMP_MSG_GETBULK
from .import errors

from nav.oids import OID
from pynetsnmp.netsnmp import (Session, SNMP_MSG_GETNEXT, mkoid, lib,
                               netsnmp_pdu_p, byref, getResult, cast,
                               netsnmp_pdu)

from IPy import IP

__all__ = ['Snmp', 'OID']

class Snmp(object):
    """Provides simple, synchronouse snmpget, snmpwalk and snmpjog(tm)
    operations using pynetsnmp (NetSNMP).

    """

    def __init__(self, host, community="public", version="1", port=161,
                 retries=3, timeout=1):
        """Makes a new Snmp-object.

        :param host: hostname or IP address
        :param community: community (password), defaults to "public"
        :param port: udp port number, defaults to "161"

        """

        self.host = host
        self.community = str(community)
        self.version = str(version)
        if self.version == '2':
            self.version = '2c'
        if self.version not in ('1', '2c'):
            raise errors.UnsupportedSnmpVersionError(self.version)
        self.port = int(port)
        self.retries = retries
        self.timeout = timeout

        self.handle = _MySnmpSession(self._build_cmdline())
        self.handle.open()

    def _build_cmdline(self):
        try:
            address = IP(self.host)
        except ValueError:
            host = self.host
        else:
            host = ('udp6:[%s]' % self.host if address.version() == 6
                    else self.host)

        return (
            '-v' + self.version,
            '-c', self.community,
            '-r', str(self.retries),
            '-t', str(self.timeout),
            '%s:%s' % (host, self.port)
            )

    def __del__(self):
        self.handle.close()

    def get(self, query="1.3.6.1.2.1.1.1.0"):
        """Performs an SNMP GET query.

        :param query: OID to query for.
        :returns: The response value as a string.

        """
        oid = OID(query)
        response = self.handle.sget([oid])
        if response:
            value = response.get(oid, None)
            if isinstance(value, tuple):
                return str(OID(value))[1:]
            else:
                return value
        else:
            return ''

    # FIXME: Implement a working version of this
    def __set(self, query, type, value):
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
            raise errors.TimeOutException(e)
        except snmperror.NetworkError, e:
            raise errors.NetworkError(e)

        # Decode raw response/answer
        rsp = self._ver.Message()
        rsp.berDecode(answer)

        # ensure the response matches the request
        if not req.apiAlphaMatch(rsp):
            raise errors.SnmpError("Response did not match request")

        # Check for errors in the response
        self._error_check(rsp)

    def walk(self, query="1.3.6.1.2.1.1.1.0"):
        """Performs an SNMP walk operation.

        :param query: root OID for walk
        :returns: A list of (response_oid, value) pairs.

        """
        result = []
        root_oid = OID(query)
        current_oid = root_oid

        while 1:
            response = self.handle.sgetnext(current_oid)
            if response is None:
                break
            response_oid, value = response.items()[0]
            if value is None:
                break

            current_oid = OID(response_oid)
            if (not root_oid.is_a_prefix_of(current_oid)
                or current_oid == root_oid):
                break

            if isinstance(value, tuple):
                value = str(OID(value))[1:]
            result.append((str(current_oid)[1:], value))

        return result

    def jog(self, query="1.3.6.1.2.1.1.1.0"):
        """Performs an SNMP walk operation, stripping the query prefix from
        the response.

        :param query: root OID for walk
        :returns: A list of (response_oid, value) pairs,
                  where the query prefix has been stripped from the
                  response_oids.

        """
        prefix = OID(query)
        walked = self.walk(query)
        result = [(str(OID(oid).strip_prefix(prefix))[1:], value)
                  for oid, value in walked]
        return result

    NON_REPEATERS = 0
    MAX_REPETITIONS = 15
    def bulkwalk(self, query="1.3.6.1.2.1.1.1.0", strip_prefix=False):
        """Performs an SNMP walk on the host, using GETBULK requests.

        Will raise an UnsupportedSnmpVersionError if the current
        version is anything other than 2c.

        :param query: root OID for walk
        :param strip_prefix: A boolean. Set to True to strip the query prefix
                             from the OIDs in the response. Default is False.
        :returns: A list of (response_oid, value) pairs,
                  where the query prefix has been stripped from the
                  response_oids.

        """
        if str(self.version) != "2c":
            raise errors.UnsupportedSnmpVersionError(
                "Cannot use BULKGET in SNMP version " + self.version)
        result = []
        root_oid = OID(query)
        current_oid = root_oid

        while 1:
            response = self.handle.sgetbulk(self.NON_REPEATERS,
                                            self.MAX_REPETITIONS, [current_oid])
            if response is None:
                break
            for response_oid, value in response:
                if value is None:
                    return result

                current_oid = OID(response_oid)
                if (not root_oid.is_a_prefix_of(current_oid)
                    or current_oid == root_oid):
                    return result

                if isinstance(value, tuple):
                    value = str(OID(value))[1:]
                result.append((str(current_oid)[1:], value))

        return result

class _MySnmpSession(Session):
    def sgetnext(self, root):
        req = self._create_request(SNMP_MSG_GETNEXT)
        oid = mkoid(root)
        lib.snmp_add_null_var(req, oid, len(oid))

        response = netsnmp_pdu_p()
        if lib.snmp_synch_response(self.sess, req, byref(response)) == 0:
            result = dict(getResult(response.contents))
            lib.snmp_free_pdu(response)
            return result

    def sgetbulk(self, nonrepeaters, maxrepetitions, oids):
        req = self._create_request(SNMP_MSG_GETBULK)
        req = cast(req, POINTER(netsnmp_pdu))
        req.contents.errstat = nonrepeaters
        req.contents.errindex = maxrepetitions
        for oid in oids:
            oid = mkoid(oid)
            lib.snmp_add_null_var(req, oid, len(oid))

        response = netsnmp_pdu_p()
        if lib.snmp_synch_response(self.sess, req, byref(response)) == 0:
            result = getResult(response.contents)
            lib.snmp_free_pdu(response)
            return result
