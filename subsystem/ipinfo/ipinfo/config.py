#
# Copyright 2005 Norwegian University of Science and Technology
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
# $Id$
#

"""Configuration classes for IP Info Center."""

from IPy import IP
from os.path import join
import nav.path

class UnrealDict(dict):
    "Dictionary that returns None when accessing non-existant keys"
    def __getitem__(self, key):
        if key not in self:
            return None
        else:
            return dict.__getitem__(self, key)

class Rule:
    def __init__(self, condition, output):
        self.condition = condition
        self.output = output

    def eval(self, locals={}):
        """
        Evaluate the condition in the context of locals.

        Also adds the IPy.IP class to the global and local namespace, for
        convenience of IP address space calculations in rules.
        """
        newlocals = locals.copy()
        newlocals['IP'] = IP
        try:
            result = eval(self.condition,
                          {'IP': IP},
                          UnrealDict(newlocals))
        except NameError, err:
            # Ignore NameErrors and return false for this condition
            return False
        else:
            return result

    def out(self, locals={}):
        "Fill output using locals and return the string"
        return self.output % UnrealDict(locals)

    def __repr__(self):
        return '<Rule: On """%s""" output """%s""">' % (self.condition,
                                                        self.output)

class Configuration(list):
    def __init__(self, buffer):
        list.__init__(self)
        self.parse(buffer)

    def parse(self, buffer):
        def getnextrule():
            try:
                index = self._buffer.index('{')
            except ValueError:
                return
            condition = self._buffer[:index]
            condition = condition.strip().replace('\n', ' ')
            self._buffer = self._buffer[index+1:]

            try:
                index = self._buffer.index('}')
            except ValueError:
                return
            output = self._buffer[:index].strip()
            self._buffer = self._buffer[index+1:]

            return Rule(condition, output)

        del self[:]
        self._buffer = buffer
        while True:
            rule = getnextrule()
            if not rule: break
            self.append(rule)

    def output(self, locals={}):
        out = ""
        for rule in self:
            if rule.eval(locals):
                out += rule.out(locals)
        return out

def config(filename):

    """Reads a config file and returns a Configuration object.

    Also removes comment lines from the file first.
    """
    f = file(filename, 'r')
    bufferedlines = [line for line in f.readlines()
                     if not line.startswith('#')]
    f.close()
    return Configuration(''.join(bufferedlines))

def theConfig():
    """Read and return the 'official' NAV configuration for IP Info."""
    filename = join(nav.path.sysconfdir, 'webfront', 'ipinfo.conf')
    return config(filename)
