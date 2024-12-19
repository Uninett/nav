#
# Copyright (C) 2017 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""NAV test cases"""
import pytest
import django.test


class DjangoTransactionTestCase(django.test.TestCase):
    serialized_rollback = True

    @pytest.fixture(autouse=True)
    def requirements(self, postgresql):
        """Ensures the required pytest fixtures are loaded implicitly for all these tests"""
        pass
