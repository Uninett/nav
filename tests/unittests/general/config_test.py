# Copyright (C) 2009 Uninett AS
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

from __future__ import unicode_literals
import unittest
try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO

from nav import config


class ConfigTestCase(unittest.TestCase):
    def setUp(self):
        mockfile = StringIO("".join([
            '# mock config file\n',
            'foo1=bar1\n',
            'foo2 =  bar2  \n',
            '#foo3=invalid\n',
            'foo4 = bar4 # comment\n',
            '# eof',
            ]))
        self.mockfile = mockfile

        mockinifile = StringIO("".join([
            '# mock config file\n',
            '[section1]\n',
            'foo1=bar1\n',
            'foo2 =  bar2  \n',
            '[section2] \n',
            '#foo3=invalid\n',
            'foo4 = bar4 \n',
            '# eof',
         ]))
        self.mockinifile = mockinifile

    def test_read_flat_config(self):
        values = config.read_flat_config(self.mockfile)
        self.assertEquals(values['foo1'], 'bar1')
        self.assertEquals(values['foo2'], 'bar2')
        self.assertEquals(values['foo4'], 'bar4')
        self.assertFalse('foo3' in values)

    def test_getconfig(self):
        values = config.getconfig(self.mockinifile)
        self.assertEquals(2, len(values.keys()))
        self.assert_('section1' in values)
        self.assert_('section2' in values)

        self.assertEquals(values['section1']['foo1'], 'bar1')
        self.assertEquals(values['section1']['foo2'], 'bar2')
        self.assertEquals(values['section2']['foo4'], 'bar4')
        self.assertFalse('foo3' in values['section2'])
