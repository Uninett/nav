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

import unittest

from nav import bitvector


class BitVectorTestCase(unittest.TestCase):
    """Tests for nav.bitvector.BitVector class"""

    def setUp(self):
        self.zerobits = bitvector.BitVector(b'\x00' * 8)

        self.somebits = bitvector.BitVector(b'\x00' * 8)
        self.somebits[5] = True
        self.somebits[50] = True

    def test_unmodified_vector_size(self):
        self.assertEqual(64, len(self.zerobits))

    def test_modified_vector_size(self):
        self.assertEqual(64, len(self.somebits))

    def test_individual_modified_bits(self):
        self.assertEqual(True, bool(self.somebits[5]))
        self.assertEqual(True, bool(self.somebits[50]))

    def test_modified_string(self):
        self.assertEqual(b'\x04\x00\x00\x00\x00\x00 \x00', self.somebits.to_bytes())

    def test_modified_binary_string(self):
        self.assertEqual(
            '0000010000000000000000000000000000000000000000000010000000000000',
            self.somebits.to_binary(),
        )

    def test_unmodified_binary_string(self):
        self.assertEqual('0' * 64, self.zerobits.to_binary())
