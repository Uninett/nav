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
"""Dummy service checker: It will always report a success status"""

from nav.daemon import safesleep as sleep
from nav.statemon.abstractchecker import AbstractChecker
from nav.statemon.event import Event


class DummyChecker(AbstractChecker):
    """Dummy"""

    IPV6_SUPPORT = True

    def execute(self):
        import random

        sleep(random.random() * 10)
        return Event.UP, 'OK'
