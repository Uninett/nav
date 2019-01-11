#
# Copyright (C) 2010-2015 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Bulk import format parsers."""

from __future__ import absolute_import

import csv
import re
import io

from django.utils import six
from IPy import IP

from nav.errors import GeneralException
from nav.models.manage import Location, Room, Organization, Vendor, Usage


class BulkParser(six.Iterator):
    """Abstract base class for bulk parsers"""
    format = ()
    required = 0
    restkey = None
    restkey_format = None

    def __init__(self, data, delimiter=None):
        if hasattr(data, 'seek'):
            self.data = data
        else:
            if six.PY3:
                if isinstance(data, six.binary_type):
                    self.data = io.StringIO(data.decode('utf-8'))
                else:
                    self.data = io.StringIO(data)
            else:
                self.data = io.BytesIO(data)

        if delimiter is None:
            try:
                self.dialect = csv.Sniffer().sniff(self.data.read(200),
                                                   delimiters=';:,')
            except csv.Error:
                self.dialect = None
                self.delimiter = ':'
            else:
                self.delimiter = self.dialect.delimiter
            finally:
                self.data.seek(0)

        self.reader = csv.DictReader(CommentStripper(self.data),
                                     fieldnames=self.format,
                                     delimiter=self.delimiter,
                                     restkey=self.restkey)
        self.line_num = 0

    def __iter__(self):
        return self

    def __next__(self):
        """Generate next parsed row"""
        row = six.next(self.reader)
        # although the DictReader doesn't return blank lines, we want
        # to count them so we can pinpoint errors exactly within the
        # source file.
        self.line_num = self.reader.reader.line_num

        self.validate_row(row)
        return row

    def validate_row(self, row):
        """Validate an entire row"""
        for fieldnum in range(self.required):
            fieldname = self.format[fieldnum]
            if not fieldname in row or not row[fieldname]:
                raise RequiredFieldMissing(self.line_num, fieldname)

        for fieldname, value in row.items():
            if not self.is_valid_fieldvalue(fieldname, value):
                raise InvalidFieldValue(self.line_num, fieldname, value)

    def is_valid_fieldvalue(self, fieldname, value):
        """Verify the validity of a specific value"""
        validatorname = "_validate_%s" % fieldname
        if (hasattr(self, validatorname) and
                callable(getattr(self, validatorname))):
            return getattr(self, validatorname)(value)
        else:
            return True

    @classmethod
    def get_header(cls):
        """Returns a comment header describing the bulk format.

        The comment header is built automatically using information provided
        the descendant BulkParser class.

        """
        separator = ':'
        required = separator.join(cls.format[:cls.required])
        optional = separator.join(cls.format[cls.required:])
        restkey_format = (cls.restkey_format and cls.restkey_format or
                          cls.restkey)
        rest = "%s%s..." % (restkey_format, separator)

        header = "#" + required
        if cls.required < len(cls.format) or cls.restkey:
            header += '['
            header += optional and separator + optional or ''
            header += cls.restkey and separator + rest or ''
            header += ']'

        return header


# don't complain about simple iterators, mr. Pylint!
# pylint: disable=R0903
class CommentStripper(six.Iterator):
    """Iterator that strips comments from the input iterator"""
    COMMENT_PATTERN = re.compile(r'\W*#[^\n\r]*')

    def __init__(self, source_iterator):
        self.source_iterator = source_iterator

    def __iter__(self):
        return self

    def __next__(self):
        """Returns next line"""
        line = six.next(self.source_iterator)
        return self.COMMENT_PATTERN.sub('', line)


def validate_attribute_list(value):
    """Validates simple attribute lists.

    Any 'restkey' column that has the required 'variable=value' format can be
    validated by this function. Variable names and variable values themselves
    are not validated in any way, just that there is a minimum of one equals
    sign in there.
    """
    if not isinstance(value, list):
        return False
    for arg in value:
        items = arg.split('=', 1)
        if len(items) < 2:
            return False
    return True


class NetboxBulkParser(BulkParser):
    """Parses the netbox bulk format"""
    format = ('roomid', 'ip', 'orgid', 'catid', 'snmp_version', 'ro', 'rw',
              'master', 'function', 'data')
    required = 4
    restkey = 'netboxgroup'

    @staticmethod
    def _validate_ip(value):
        try:
            IP(value)
        except ValueError:
            return False
        else:
            return True

    @staticmethod
    def _validate_snmp_version(value):
        if not value:
            return True  # empty values are ok
        try:
            return int(value) in (1, 2)
        except ValueError:
            return False

    @staticmethod
    def _validate_data(datastring):
        try:
            if datastring:
                items = (item.split('=', 1) for item in datastring.split('|'))
                if items:
                    dict(items)
        except ValueError:
            return False
        else:
            return True


class UsageBulkParser(BulkParser):
    """Parses the usage bulk format"""
    format = ('usageid', 'descr')
    required = 2
    restkey = None
    usageid_maxlength = getattr(Usage, '_meta').get_field('id').max_length

    @classmethod
    def _validate_usageid(cls, value):
        return len(value) <= cls.usageid_maxlength


class LocationBulkParser(BulkParser):
    """Parses the location bulk format"""
    format = ('locationid', 'parent', 'descr')
    required = 1
    locationid_maxlength = getattr(Location, '_meta').get_field('id').max_length

    @classmethod
    def _validate_locationid(cls, value):
        return len(value) <= cls.locationid_maxlength


class OrgBulkParser(BulkParser):
    """Parses the organization bulk format"""
    format = ('orgid', 'parent', 'description')
    restkey = 'attr'
    required = 1
    _validate_attr = staticmethod(validate_attribute_list)
    orgid_maxlength = getattr(Organization, '_meta').get_field('id').max_length

    @classmethod
    def _validate_orgid(cls, value):
        return len(value) <= cls.orgid_maxlength


class PrefixBulkParser(BulkParser):
    """Parses the prefix bulk format"""
    format = ('netaddr', 'nettype',
              'orgid', 'netident', 'usage', 'description', 'vlan')
    required = 2

    @staticmethod
    def _validate_netaddr(value):
        try:
            IP(value)
        except ValueError:
            return False
        else:
            return True

    @staticmethod
    def _validate_vlan(vlan):
        try:
            if vlan is not None:
                int(vlan)
        except ValueError:
            return False
        else:
            return True


class RoomBulkParser(BulkParser):
    """Parses the room bulk format"""
    format = ('roomid', 'locationid', 'descr', 'position')
    restkey = 'attr'
    required = 2
    _validate_attr = staticmethod(validate_attribute_list)
    roomid_maxlength = getattr(Room, '_meta').get_field('id').max_length

    @classmethod
    def _validate_roomid(cls, value):
        return len(value) <= cls.roomid_maxlength


class ServiceBulkParser(BulkParser):
    """Parses the service bulk format"""
    format = ('host', 'service')
    restkey = 'arg'
    required = 2
    _validate_arg = staticmethod(validate_attribute_list)


class NetboxGroupBulkParser(BulkParser):
    """Parses the netboxgroup bulk format"""
    format = ('netboxgroupid', 'description')
    required = 2


class NetboxTypeBulkParser(BulkParser):
    """Parses the type bulk format"""
    format = ('vendorid', 'typename', 'sysobjectid',
              'description')
    required = 3


class VendorBulkParser(BulkParser):
    """Parses the vendor bulk format"""
    format = ('vendorid',)
    required = 1
    vendorid_maxlength = getattr(Vendor, '_meta').get_field('id').max_length

    @classmethod
    def _validate_vendorid(cls, value):
        return len(value) <= cls.vendorid_maxlength


class CablingBulkParser(BulkParser):
    """Parses the cabling bulk format"""
    format = ('roomid', 'jack', 'building', 'targetroom', 'category',
              'descr')
    required = 5


class PatchBulkParser(BulkParser):
    """Parses the patch bulk format"""
    format = ('sysname', 'port', 'roomid', 'jack',
              'split')
    required = 4


#
# exceptions
#
class BulkParseError(GeneralException):
    """Bulk import parse error"""

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self)


class RequiredFieldMissing(BulkParseError):
    """A required field is missing"""

    def __init__(self, line_num, missing_field):
        super(RequiredFieldMissing, self).__init__()
        self.line_num = line_num
        self.missing_field = missing_field

    def __str__(self):
        return "%s: '%s' on line %d" % (self.__doc__,
                                        self.missing_field,
                                        self.line_num,
                                        )


class InvalidFieldValue(BulkParseError):
    """A field value is invalid"""

    def __init__(self, line_num, field, value):
        super(InvalidFieldValue, self).__init__()
        self.line_num = line_num
        self.field = field
        self.value = value

    def __str__(self):
        return ("%s: '%s' is invalid value for field '%s' on line %d" %
                (self.__doc__, self.value, self.field, self.line_num))
