#
# Copyright (C) 2013 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""High level synchronouse NAV API for NetSNMP"""

from __future__ import absolute_import, unicode_literals

from collections import namedtuple
from ctypes import (c_int, sizeof, byref, cast, POINTER, c_char, c_char_p,
                    c_uint, c_ulong, c_uint64)

from django.utils import six
from IPy import IP
from pynetsnmp import netsnmp
from pynetsnmp.netsnmp import (Session, SNMP_MSG_GETNEXT, mkoid, lib,
                               netsnmp_pdu_p, getResult, netsnmp_pdu,
                               SNMP_MSG_GETBULK, SNMP_MSG_SET, SNMP_MSG_GET)

from nav.oids import OID
from .errors import (
    EndOfMibViewError,
    NoSuchObjectError,
    SnmpError,
    TimeOutException,
    UnsupportedSnmpVersionError
)

PDUVarbind = namedtuple("PDUVarbind", ['oid', 'type', 'value'])

SNMPERR_MAP = dict(
    (value, name)
    for name, value in vars(netsnmp).items()
    if name.startswith('SNMPERR_')
)

__all__ = ['Snmp', 'OID', 'SNMPERR_MAP', 'snmp_api_errstring', 'PDUVarbind']

TYPEMAP = {
    'i': netsnmp.ASN_INTEGER,
    'u': netsnmp.ASN_UNSIGNED,
    't': netsnmp.ASN_TIMETICKS,
    'a': netsnmp.ASN_IPADDRESS,
    'o': netsnmp.ASN_OBJECT_ID,
    's': netsnmp.ASN_OCTET_STR,
    'U': netsnmp.ASN_COUNTER64,
    'x': netsnmp.ASN_OCTET_STR,
}


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
            raise UnsupportedSnmpVersionError(self.version)
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
        :returns: The response value

        """
        oid = OID(query)
        response = self.handle.sget([oid])
        if response:
            value = response.get(oid, None)
            if isinstance(value, tuple):
                return OID(value)
            return value
        else:
            return None

    @staticmethod
    def translate_type(type):
        """Translate type to fit backend library"""
        if type in TYPEMAP:
            value_type = TYPEMAP[type]
            # TODO: verify that the type is defined for the selected SNMP ver
        else:
            raise ValueError("type must be one of %r, not %r" %
                             (TYPEMAP.keys(), type))
        return value_type

    def set(self, query, type, value):
        """Performs an SNMP SET operations.

        :param query: OID to set
        :param type: type of value to set. This may be
        i: INTEGER
        u: unsigned INTEGER
        t: TIMETICKS
        a: IPADDRESS
        o: OBJID
        s: OCTETSTRING
        U: COUNTER64 (version 2 and above)
        x: OCTETSTRING
        :param value: the value to set. Must ofcourse match type: i = 2,
         s = 'string'
        """
        self.handle.sset([
            PDUVarbind(OID(query), self.translate_type(type), value)])

    def multi_set(self, varbinds):
        """Performs SNMP set with multiple operations

        :type varbinds: list[PDUVarbind]
        """
        self.handle.sset([
            PDUVarbind(OID(v.oid), self.translate_type(v.type), v.value)
            for v in varbinds])

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
            response_oid, value = list(response.items())[0]
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
            raise UnsupportedSnmpVersionError(
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
    """An extension of netsnmp.Session to provide multiple synchronous
    operations.

    """
    def sget(self, oids):
        req = self._create_request(SNMP_MSG_GET)
        for oid in oids:
            oid = mkoid(oid)
            lib.snmp_add_null_var(req, oid, len(oid))
        response = netsnmp_pdu_p()
        if lib.snmp_synch_response(self.sess, req, byref(response)) == 0:
            _raise_on_protocol_error(response)
            result = dict(getResult(response.contents))
            lib.snmp_free_pdu(response)
            return result
        else:
            _raise_on_error(self.sess.contents.s_snmp_errno)

    def sgetnext(self, root):
        req = self._create_request(SNMP_MSG_GETNEXT)
        oid = mkoid(root)
        lib.snmp_add_null_var(req, oid, len(oid))

        response = netsnmp_pdu_p()
        if lib.snmp_synch_response(self.sess, req, byref(response)) == 0:
            _raise_on_protocol_error(response)
            result = dict(getResult(response.contents))
            lib.snmp_free_pdu(response)
            return result
        else:
            _raise_on_error(self.sess.contents.s_snmp_errno)

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
            _raise_on_protocol_error(response)
            result = getResult(response.contents)
            lib.snmp_free_pdu(response)
            return result
        else:
            _raise_on_error(self.sess.contents.s_snmp_errno)

    def sset(self, varbinds):
        """:type varbinds: list[PDUVarbinds]"""
        req = self._create_request(SNMP_MSG_SET)
        for varbind in varbinds:
            oid = mkoid(varbind.oid)
            converter = CONVERTER_MAP[varbind.type]
            data, size = converter(varbind.value)
            lib.snmp_pdu_add_variable(req, oid, len(oid), varbind.type,
                                      data, size)

        response = netsnmp_pdu_p()
        if lib.snmp_synch_response(self.sess, req, byref(response)) == 0:
            _raise_on_protocol_error(response)
            result = dict(getResult(response.contents))
            lib.snmp_free_pdu(response)
            return result
        else:
            _raise_on_error(self.sess.contents.s_snmp_errno)

#
# Functions for converting Python values to C data types suitable for ASN
# and BER encoding in the NET-SNMP library.
#


CONVERTER_MAP = {}


def converts(asn_type):
    """Decorator to register a function as a converter of a Python value to a
    specific ASN data type.

    """
    def _register(func):
        CONVERTER_MAP[asn_type] = func
        return func
    return _register


@converts(netsnmp.ASN_INTEGER)
def asn_integer(value):
    value = c_int(value)
    return byref(value), sizeof(value)


@converts(netsnmp.ASN_UNSIGNED)
def asn_unsigned(value):
    value = c_uint(value)
    return byref(value), sizeof(value)


@converts(netsnmp.ASN_TIMETICKS)
def asn_timeticks(value):
    value = c_ulong(value)
    return byref(value), sizeof(value)


@converts(netsnmp.ASN_IPADDRESS)
def asn_ipaddress(value):
    ipaddr = IP(value)
    value = c_ulong(ipaddr.int())
    return byref(value), sizeof(value)


@converts(netsnmp.ASN_OBJECT_ID)
def asn_object_id(value):
    value = mkoid(OID(value))
    return byref(value), sizeof(value)


@converts(netsnmp.ASN_OCTET_STR)
def asn_octet_str(value):
    if not isinstance(value, six.binary_type):
        raise TypeError("Byte string expected")
    string = c_char_p(value)
    return string, len(value)


@converts(netsnmp.ASN_COUNTER64)
def asn_counter64(value):
    value = c_uint64(value)
    return byref(value), sizeof(value)


# Some global ctypes initializations needed for the snmp_api_errstring function
_charptr = POINTER(c_char)
netsnmp.lib.snmp_api_errstring.restype = _charptr
netsnmp.lib.snmp_errstring.restype = _charptr


def snmp_api_errstring(err_code):
    """Converts an SNMP API error code to an error string"""
    buf = netsnmp.lib.snmp_api_errstring(err_code)
    return cast(buf, c_char_p).value.decode('utf-8')


def snmp_errstring(err_status):
    """Converts an SNMP protocol error status to an error string"""
    buf = netsnmp.lib.snmp_errstring(err_status)
    return cast(buf, c_char_p).value.decode('utf-8')


def _raise_on_error(err_code):
    """Raises an appropriate NAV exception for a non-null SNMP err_code value.

    Does nothing if err_code is 0.

    """
    if err_code == 0:
        return
    elif err_code == netsnmp.SNMPERR_TIMEOUT:
        raise TimeOutException(snmp_api_errstring(err_code))
    else:
        raise SnmpError("%s: %s" % (SNMPERR_MAP.get(err_code, ''),
                                    snmp_api_errstring(err_code)))


def _raise_on_protocol_error(response):
    """Raises an appropriate NAV exception for a non-zero SNMP protocol error
     status value.

    """
    response = response.contents
    if response.errstat > 0:
        errstring = snmp_errstring(response.errstat)
        if response.errstat == netsnmp.SNMP_ERR_NOSUCHNAME:
            raise NoSuchObjectError(errstring)
        if response.errstat > 0:
            raise SnmpError(errstring)

    # check for SNMP varbind exception values
    var = response.variables
    while var:
        var = var.contents
        oid = OID([var.name[i] for i in range(var.name_length)])
        vtype = ord(var.type)
        if vtype in (netsnmp.SNMP_NOSUCHINSTANCE, netsnmp.SNMP_NOSUCHOBJECT):
            raise NoSuchObjectError(oid)
        elif vtype == netsnmp.SNMP_ENDOFMIBVIEW:
            raise EndOfMibViewError(oid)
        var = var.next_variable
