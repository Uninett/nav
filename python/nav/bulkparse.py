#
# Copyright (C) 2010 UNINETT
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Bulk import format parsers."""

import csv
import re
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from IPy import IP

from nav.errors import GeneralException

class BulkParser(object):
    format = ()
    required = 0
    restkey = None
    restkey_format = None

    def __init__(self, data, delimiter=None):
        if hasattr(data, 'seek'):
            self.data = data
        else:
            self.data = StringIO(data)

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

    def next(self):
        row = self.reader.next()
        # although the DictReader doesn't return blank lines, we want
        # to count them so we can pinpoint errors exactly within the
        # source file.
        self.line_num = self.reader.reader.line_num

        self.validate_row(row)
        return row

    def validate_row(self, row):
        for fieldnum in range(self.required):
            fieldname = self.format[fieldnum]
            if not row.has_key(fieldname) or not row[fieldname]:
                raise RequiredFieldMissing(self.line_num, fieldname)

        for fieldname, value in row.items():
            if not self.is_valid_fieldvalue(fieldname, value):
                raise InvalidFieldValue(self.line_num, fieldname, value)

    def is_valid_fieldvalue(self, fieldname, value):
        validatorname = "validate_%s" % fieldname
        if (hasattr(self, validatorname) and
            callable(getattr(self, validatorname))):
            return getattr(self, validatorname)(value)
        else:
            return True

    @classmethod
    def get_header(cls):
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

class CommentStripper(object):
    COMMENT_PATTERN = re.compile('\W*#[^\n\r]*')

    def __init__(self, source_iterator):
        self.source_iterator = source_iterator

    def __iter__(self):
        return self

    def next(self):
        line = self.source_iterator.next()
        return self.COMMENT_PATTERN.sub('', line)

class NetboxBulkParser(BulkParser):
    format = ('roomid', 'ip', 'orgid', 'catid',
              'ro', 'serial', 'rw', 'function')
    required = 4
    restkey = 'subcat'

    def validate_ip(self, value):
        try:
            IP(value)
        except ValueError:
            return False
        else:
            return True

class UsageBulkParser(BulkParser):
    format = ('usageid', 'descr')
    required = 2
    restkey = None

class LocationBulkParser(BulkParser):
    format = ('locationid', 'descr')
    required = 2

class OrgBulkParser(BulkParser):
    format = ('orgid',
              'parent', 'description', 'opt1', 'opt2', 'opt3')
    required = 1

class PrefixBulkParser(BulkParser):
    format = ('netaddr', 'nettype',
              'orgid', 'netident', 'usage', 'description', 'vlan')
    required = 2

    def validate_netaddr(self, value):
        try:
            IP(value)
        except ValueError:
            return False
        else:
            return True

    def validate_vlan(self, vlan):
        try:
            if vlan is not None:
                int(vlan)
        except ValueError:
            return False
        else:
            return True

class RoomBulkParser(BulkParser):
    format = ('roomid',
              'locationid', 'descr', 'opt1', 'opt2', 'opt3', 'opt4')
    required = 1

class ServiceBulkParser(BulkParser):
    format = ('host', 'handler')
    restkey = 'arg'
    required = 2

    def validate_arg(self, value):
        if not isinstance(value, list):
            return False
        for arg in value:
            items = arg.split('=', 1)
            if len(items) < 2:
                return False
        return True

class SubcatBulkParser(BulkParser):
    format = ('subcatid', 'catid', 'description')
    required = 3

class NetboxTypeBulkParser(BulkParser):
    format = ('vendorid', 'typename', 'sysobjectid',
              'description', 'cdp', 'tftp')
    required = 3

class VendorBulkParser(BulkParser):
    format = ('vendorid',)
    required = 1

class CablingBulkParser(BulkParser):
    format = ('roomid', 'jack', 'building', 'targetroom', 'category',
              'descr')
    required = 5

class PatchBulkParser(BulkParser):
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
        self.line_num = line_num
        self.field = field
        self.value = value

    def __str__(self):
        return ("%s: '%s' is invalid value for field '%s' on line %d" %
                (self.__doc__, self.value, self.field, self.line_num))

