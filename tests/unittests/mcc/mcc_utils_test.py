#
# Copyright (C) 2010 UNINETT AS
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
"""Integration tests for the nav.mcc.utils module."""
import unittest
from StringIO import StringIO

from nav.mcc import utils

class ConfigRootTest(unittest.TestCase):
    def test_plain_gconfigroot(self):
        cfg = StringIO(
            '$gConfigRoot = "/usr/local/nav/etc/cricket-config";\n')
        self.assertEquals(
            utils.get_configroot(cfg),
            "/usr/local/nav/etc/cricket-config")

    def test_commented_out_gconfigroot_is_ignored(self):
        cfg = StringIO(
            '# $gConfigRoot = "something";\n'
            '$gConfigRoot = "/usr/local/nav/etc/cricket-config";\n')
        self.assertEquals(
            utils.get_configroot(cfg),
            "/usr/local/nav/etc/cricket-config")

    def test_compound_gconfigroot(self):
        cfg = StringIO(
            '$othervalue = "/usr/local/nav/etc";\n'
            '$gConfigRoot = "$othervalue/cricket-config";\n')
        self.assertEquals(
            utils.get_configroot(cfg),
            "/usr/local/nav/etc/cricket-config")

