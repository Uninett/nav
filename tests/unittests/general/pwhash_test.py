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

import pytest

from nav import pwhash


class TestPwHash(object):
    """Tests for nav.pwhash.Hash class"""

    def test_methods_are_callable(self):
        """All values in the known_methods dictionary must be callable"""
        for method in pwhash.KNOWN_METHODS.values():
            assert callable(method)

    def test_sha1_hash(self):
        hash = pwhash.Hash('sha1', 'e7MaFMQE', 'foobar')
        assert '{sha1}e7MaFMQE$cCqMIINS5t85J0MIgNwMprXBfLA=' == str(hash)

    def test_md5_hash(self):
        hash = pwhash.Hash('md5', 'e7MaFMQE', 'foobar')
        assert '{md5}e7MaFMQE$wbzoUnM9Jju9ob9bY29+hA==' == str(hash)

    def test_pbkdf25_hash(self):
        hash = pwhash.Hash('pbkdf2', 'e7MaFMQE', 'foobar')
        assert '{pbkdf2}e7MaFMQE$7j7bgQb8xED7mEY+8g1QM2zs/ispKZVeNEv/nMCYPX0=' == str(
            hash
        )

    def test_unknown_hash(self):
        with pytest.raises(pwhash.UnknownHashMethodError):
            pwhash.Hash('montyhash', 'e7MaFMQE', 'foobar')

    def test_verify_sha1_hash(self):
        hash = pwhash.Hash()
        hash.set_hash('{sha1}e7MaFMQE$cCqMIINS5t85J0MIgNwMprXBfLA=')
        assert hash.verify('foobar')
        assert not hash.verify('blueparrot')

    def test_verify_md5_hash(self):
        hash = pwhash.Hash()
        hash.set_hash('{md5}e7MaFMQE$wbzoUnM9Jju9ob9bY29+hA==')
        assert hash.verify('foobar')
        assert not hash.verify('blueparrot')

    def test_bad_hash(self):
        hash = pwhash.Hash()
        with pytest.raises(pwhash.InvalidHashStringError):
            hash.set_hash('badc0ffee')

    def test_verifyable_hash(self):
        password = 'foobar'
        hash = pwhash.Hash(password=password)
        hashed = str(hash)
        hash2 = pwhash.Hash()
        hash2.set_hash(hashed)
        assert hash2.verify(password)
