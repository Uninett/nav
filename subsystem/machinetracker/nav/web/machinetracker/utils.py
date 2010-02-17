# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#

from socket import gethostbyaddr, herror

def hostname(addr):
    dns = _Hostname()
    return dns.lookup(addr)

class _Hostname:
    cache = {}

    def lookup(self, addr):
        if addr in self.cache:
            return self.cache[addr]
        try:
            dns = gethostbyaddr(addr)
        except herror:
            return None
        self.cache[addr] = dns[0]
        return dns[0]
