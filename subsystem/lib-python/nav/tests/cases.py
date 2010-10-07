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
import sys
import os

import django.test
from django.db import transaction

class DjangoTransactionTestCase(django.test.TestCase):
    """Runs tests inside a Django transaction, with the ability to load Django
    fixtures at the start of each test.

    django.test.TestCase's _pre_setup() and _post_teardown() methods
    are overridden, since NAV doesn't use Django models to initialize
    the database, and generally does funny things with Django.

    """
    fixtures = []

    def _pre_setup(self):
        transaction.enter_transaction_management()
        transaction.managed(True)
        if hasattr(self, 'fixtures'):
            self._load_fixtures(self.fixtures)

    def _post_teardown(self):
        transaction.rollback()
        transaction.leave_transaction_management()

    def _load_fixtures(self, fixtures):
        from django.core import serializers
        fixture_paths = self._find_fixtures(fixtures)
        if fixtures and not fixture_paths:
            raise Exception("No fixtures found")
        for fixture_path in fixture_paths:
            fixture = file(fixture_path, "r")
            try:
                objects = serializers.deserialize("xml", fixture)
                for obj in objects:
                    obj.save()
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception:
                fixture.close()
                transaction.rollback()
                transaction.leave_transaction_management()
                raise
            fixture.close()

    def _find_fixtures(self, fixtures):
       my_module = sys.modules[self.__module__]
       search_path = [os.path.dirname(my_module.__file__)]
       result = []
       for f in fixtures:
           for dir in search_path:
               filename = os.path.join(dir, f)
               if os.path.exists(filename):
                   result.append(filename)
       return result

