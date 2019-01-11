#
# Copyright (C) 2016 Uninett AS
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
"""Provides password hashing algorithms for NAV."""
from __future__ import absolute_import

import os
import random
import hashlib
import base64
import re
from nav import errors
from django.utils import crypto, six


def sha1(password, salt):
    return hashlib.sha1(password + salt).digest()


def md5(password, salt):
    return hashlib.md5(password + salt).digest()


def pbkdf2(password, salt):
    return crypto.pbkdf2(password, salt, iterations=10000)


KNOWN_METHODS = {
    'sha1': sha1,
    'md5': md5,
    'pbkdf2': pbkdf2,
}
DEFAULT_METHOD = 'pbkdf2'


def generate_salt():
    """"Generate and return a salt string"""
    saltlen = 8
    if hasattr(os, 'urandom') and callable(os.urandom):
        raw_salt = os.urandom(saltlen)
    else:
        raw_salt = "".join([chr(x) for x in
                            [random.randint(0, 255) for x in range(saltlen)]])

    return base64.encodestring(raw_salt).strip()


class Hash(object):
    """Class to represent a password hash.

    Use str() to extract a string representation of a hash, suitable
    for storage.
    """
    _hashmatch = re.compile(r'\{([^\}]+)\}([^\$]+)\$(.+)$')

    def __init__(self, method=DEFAULT_METHOD, salt=None, password=None):
        """Create a hash object.

        method -- The digest method to use. sha1 and md5 are supported.
        salt -- The salt to use. Will be auto-generated if omitted.
        password -- Password to hash
        """
        if method not in KNOWN_METHODS:
            raise UnknownHashMethodError(method)
        self.method = method
        if not salt:
            self.salt = generate_salt()
        else:
            self.salt = salt
        self.digest = None
        if password is not None:
            self.update(password)

    def __lt__(self, other):
        return str(self) < str(other)

    def __eq__(self, other):
        return str(self) == str(other)

    def __str__(self):
        digest64 = base64.encodestring(self.digest).strip().decode('ASCII')
        return "{%s}%s$%s" % (self.method, self.salt, digest64)

    def update(self, password):
        """Update the hash with a new password."""

        salt = self.salt
        if isinstance(salt, six.text_type):
            salt = salt.encode('utf-8')
        if isinstance(password, six.text_type):
            password = password.encode('utf-8')

        hasher = KNOWN_METHODS[self.method]
        self.digest = hasher(password, salt)

    def set_hash(self, hash):
        """Set the hash directly from a previously stored hash string."""
        match = self._hashmatch.match(hash)
        if not match:
            raise InvalidHashStringError(hash)
        else:
            method = match.group(1)
            if method not in KNOWN_METHODS:
                raise UnknownHashMethodError(method)
            else:
                self.method = method
            self.salt = match.group(2)
            self.digest = base64.decodestring(match.group(3).encode('ASCII'))

    def verify(self, password):
        """Verify a password against this hash."""
        otherhash = self.__class__(method=self.method, salt=self.salt,
                                   password=password)
        return self == otherhash


class InvalidHashStringError(errors.GeneralException):
    """Invalid hash string"""


class UnknownHashMethodError(errors.GeneralException):
    """Unknown hash method"""
