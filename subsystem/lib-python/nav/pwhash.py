# -*- coding: utf-8 -*-
#
# Copyright (C) 2005 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details. 
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Provides password hashing algorithms for NAV."""

import os
import random
import sha
import md5
import base64
import re
import nav.errors

known_methods = {
    'sha1': sha,
    'md5': md5
    }

def generate_salt():
    "Generate and return a salt string"
    saltlen = 6
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
        
    def __init__(self, method='sha1', salt=None, password=None):
        """Create a hash object.

        method -- The digest method to use. sha1 and md5 are supported.
        salt -- The salt to use. Will be auto-generated if omitted.
        password -- Password to hash
        """
        if method not in known_methods:
            raise UnknownHashMethodError, method
        self.method = method
        if not salt:
            self.salt = generate_salt()
        else:
            self.salt = salt
        self.digest = None
        if password is not None:
            self.update(password)

    def __cmp__(self, other):
        return cmp(str(self), str(other))
    
    def __str__(self):
        digest64 = base64.encodestring(self.digest).strip()
        hash = "{%s}%s$%s" % (self.method, self.salt, digest64)
        return hash

    def update(self, password):
        """Update the hash with a new password."""

        if isinstance(password, unicode):
            password = password.encode('utf-8')

        hasher = known_methods[self.method].new(password + self.salt)
        self.digest = hasher.digest()

    def set_hash(self, hash):
        """Set the hash directly from a previously stored hash string."""
        match = self._hashmatch.match(hash)
        if not match:
            raise InvalidHashStringError, hash
        else:
            method = match.group(1)
            if method not in known_methods:
                raise UnknownHashMethodError, method
            else:
                self.method = method
            self.salt = match.group(2)
            self.digest = base64.decodestring(match.group(3))

    def verify(self, password):
        """Verify a password against this hash."""
        otherhash = self.__class__(method=self.method, salt=self.salt,
                                   password=password)
        return self == otherhash

class InvalidHashStringError(nav.errors.GeneralException):
    "Invalid hash string"

class UnknownHashMethodError(nav.errors.GeneralException):
    "Unknown hash method"

