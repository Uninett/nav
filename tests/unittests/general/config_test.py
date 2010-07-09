# Copyright (C) 2009 UNINETT AS
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

import unittest
import StringIO

from nav import config

class ConfigTestCase(unittest.TestCase):
    def setUp(self):
        mockfile = StringIO.StringIO("".join([
            '# mock config file\n',
            'foo1=bar1\n',
            'foo2 =  bar2  \n',
            '#foo3=invalid\n',
            'foo4 = bar4 # comment\n',
            '# eof',
            ]))
        self.mockfile = mockfile

        mockinifile = StringIO.StringIO("".join([
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

    def test_readConfig(self):
        values = config.readConfig(self.mockfile)
        self.assertEquals(values['foo1'], 'bar1')
        self.assertEquals(values['foo2'], 'bar2')
        self.assertEquals(values['foo4'], 'bar4')
        self.assertFalse(values.has_key('foo3'))

    def test_getconfig(self):
        values = config.getconfig(self.mockinifile)
        self.assertEquals(2, len(values.keys()))
        self.assert_(values.has_key('section1'))
        self.assert_(values.has_key('section2'))

        self.assertEquals(values['section1']['foo1'], 'bar1')
        self.assertEquals(values['section1']['foo2'], 'bar2')
        self.assertEquals(values['section2']['foo4'], 'bar4')
        self.assertFalse(values['section2'].has_key('foo3'))

