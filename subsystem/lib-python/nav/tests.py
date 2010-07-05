# -*- coding: utf-8 -*-
#
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
"""Unit tests for modules in this package."""

import unittest

from nav import pwhash
class PwHashTestCase(unittest.TestCase):
    """Tests for nav.pwhash.Hash class"""

    def test_methods_are_callable(self):
        """All values in the known_methods dictionary must be callable"""
        for method in pwhash.known_methods.values():
            self.assert_(callable(method))

    def test_sha1_hash(self):
        hash = pwhash.Hash('sha1', 'e7MaFMQE', 'foobar')
        self.assertEquals('{sha1}e7MaFMQE$cCqMIINS5t85J0MIgNwMprXBfLA=',
                          str(hash))
        
    def test_md5_hash(self):
        hash = pwhash.Hash('md5', 'e7MaFMQE', 'foobar')
        self.assertEquals('{md5}e7MaFMQE$wbzoUnM9Jju9ob9bY29+hA==',
                          str(hash))

    def test_unknown_hash(self):
        self.assertRaises(pwhash.UnknownHashMethodError,
                          pwhash.Hash,
                          'montyhash', 'e7MaFMQE', 'foobar')

    def test_verify_sha1_hash(self):
        hash = pwhash.Hash()
        hash.set_hash('{sha1}e7MaFMQE$cCqMIINS5t85J0MIgNwMprXBfLA=')
        self.assert_(hash.verify('foobar'))
        self.assertFalse(hash.verify('blueparrot'))

    def test_verify_md5_hash(self):
        hash = pwhash.Hash()
        hash.set_hash('{md5}e7MaFMQE$wbzoUnM9Jju9ob9bY29+hA==')
        self.assert_(hash.verify('foobar'))
        self.assertFalse(hash.verify('blueparrot'))

    def test_bad_hash(self):
        hash = pwhash.Hash()
        self.assertRaises(pwhash.InvalidHashStringError,
                          hash.set_hash, 'badc0ffee')


from nav import bitvector
class BitVectorTestCase(unittest.TestCase):
    """Tests for nav.bitvector.BitVector class"""

    def setUp(self):
        self.zerobits = bitvector.BitVector('\x00' * 8)

        self.somebits = bitvector.BitVector('\x00' * 8)
        self.somebits[5] = True
        self.somebits[50] = True

    def test_unmodified_vector_size(self):
        self.assertEquals(64, len(self.zerobits))

    def test_modified_vector_size(self):
        self.assertEquals(64, len(self.somebits))

    def test_individual_modified_bits(self):
        self.assertEquals(True, bool(self.somebits[5]))
        self.assertEquals(True, bool(self.somebits[50]))

    def test_modified_string(self):
        self.assertEquals('\x04\x00\x00\x00\x00\x00 \x00',
                          str(self.somebits))

    def test_modified_binary_string(self):
        self.assertEquals('00000100000000000000000000000000'
                          '00000000000000000010000000000000',
                          self.somebits.to_binary())

    def test_unmodified_binary_string(self):
        self.assertEquals('0' * 64, self.zerobits.to_binary())


from nav import natsort
class NatsortTestCase(unittest.TestCase):
    def test_split(self):
        s = natsort.split('foo12bar')
        self.assertEquals(['foo', 12, 'bar'], s)

    def test_natcmp(self):
        self.assertEquals(1, natsort.natcmp('foo12bar', 'foo9bar'))

    def test_inatcmp(self):
        self.assertEquals(1, natsort.inatcmp('Foo12bar', 'foo9bar'))
        self.assertEquals(0, natsort.inatcmp('FoObAr', 'fOoBaR'))

    def test_decorated_sort(self):
        l1 = ['foo12bar', 'foo9bar', 'zero50two', 'Zero51two']
        l2 = ['Zero51two', 'foo9bar', 'foo12bar', 'zero50two']
        self.assertEquals(l2, natsort.decorated_sort(l1))


from nav import util
class UtilTestCase(unittest.TestCase):
    """Test various functions in the util module"""
    def setUp(self):
        self.gradient_start = 0
        self.gradient_stop = 952
        self.gradient_steps = 20
        self.gradient = util.gradient(self.gradient_start,
                                      self.gradient_stop,
                                      self.gradient_steps)
        self.reverse_gradient = util.gradient(self.gradient_stop,
                                              self.gradient_start,
                                              self.gradient_steps)

    def test_gradient_size(self):
        self.assertEquals(self.gradient_steps, len(self.gradient))

    def test_gradient_end_points(self):
        self.assertEquals(self.gradient_start, self.gradient[0])
        self.assertEquals(self.gradient_stop, self.gradient[-1])

    def test_gradient_order(self):
        ordered = sorted(self.gradient)
        self.assertEquals(ordered, self.gradient)

        ordered = sorted(self.reverse_gradient)
        ordered.reverse()
        self.assertEquals(ordered, self.reverse_gradient)

    def test_colortohex(self):
        self.assertEquals('ea702a', util.colortohex((234, 112, 42)))

    def test_isValidIP(self):
        valid_ips = ['129.241.75.1', '10.0.25.62', '2001:700:1::abcd',
                     'fe80::baad']
        invalid_ips = ['www.uninett.no', '92835235', '5:4', '-5325']

        for ip in valid_ips:
            self.assert_(util.isValidIP(ip),
                         msg="%s should be valid" % ip)

        for ip in invalid_ips:
            self.assertFalse(util.isValidIP(ip),
                             msg="%s should be invalid" % ip)


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

# Run all tests if run as a program
if __name__ == '__main__':
    unittest.main()
