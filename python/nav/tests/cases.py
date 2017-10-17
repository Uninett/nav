#
# Copyright (C) 2010 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""NAV test cases"""
import django.test


class DjangoTransactionTestCase(django.test.TestCase):
    serialized_rollback = True

    def _pre_setup(self):
        print "PRE SETUP!!!!"
        return super(DjangoTransactionTestCase, self)._pre_setup()

    def _fixture_setup(self):
        print "LOADING FIXTURES!! " + repr(self.fixtures)
        return super(DjangoTransactionTestCase, self)._fixture_setup()
