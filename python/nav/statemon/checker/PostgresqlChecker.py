# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""PostgreSQL service checker"""

import psycopg2
from nav.statemon.abstractchecker import AbstractChecker
from nav.statemon.event import Event


class PostgresqlChecker(AbstractChecker):
    """PostgreSQL"""

    IPV6_SUPPORT = True
    DESCRIPTION = "PostgreSQL"
    ARGS = (
        ('user', ''),
        ('password', ''),
    )
    OPTARGS = (
        ('port', ''),
        ('timeout', ''),
        ('database', ''),
    )

    def __init__(self, service, **kwargs):
        AbstractChecker.__init__(self, service, port=5432, **kwargs)

    def execute(self):
        kwargs = {}

        # Build keywords from arguments
        for name, value in self.args.items():
            if name in ('user', 'password', 'database'):
                # Must convert to str here because psycopg2 complains
                # if keywords are unicode. ("Keywords must be strings")
                kwargs[str(name)] = value

        (kwargs['host'], kwargs['port']) = self.get_address()

        try:
            psycopg2.connect(**kwargs)
        except Exception as err:  # noqa: BLE001
            # Get first line of exception message
            msg = str(err).split('\n')[0]
            return Event.DOWN, msg

        return Event.UP, 'alive'
