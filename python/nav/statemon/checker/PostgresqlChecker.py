# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 University of Tromsø
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

import psycopg2
from nav.statemon.abstractChecker import AbstractChecker
from nav.statemon.event import Event

class PostgresqlChecker(AbstractChecker):
    def __init__(self, service, **kwargs):
        AbstractChecker.__init__(self, 'postgresql', service,  port=5432, **kwargs)

    def execute(self):
        kw = {}

        # Build keywords from arguments
        args = self.getArgs()
        for (name, value) in args.items():
            if name in ('user', 'password', 'database'):
                # Must convert to str here because psycopg2 complains
                # if keywords are unicode. ("Keywords must be strings")
                kw[str(name)] = value
                
        (kw['host'], kw['port']) = self.getAddress()
        
        print(kw)

        try:
            psycopg2.connect(**kw)
        except Exception, e:
            # Get first line of exception message
            msg = str(e).split('\n')[0]
            return (Event.DOWN, msg)

        return (Event.UP, 'alive')
