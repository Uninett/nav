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
import unittest

import django.test
from django.db import transaction

from minimock import Mock

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

class ModPythonTestCase(unittest.TestCase):
    """Test case for simple simulation of requests to mod_python handlers."""
    module_under_test = None

    def setUp(self):
        super(ModPythonTestCase, self).setUp()
        # yes, modifying global state is all the rage these days
        self.user = {'login': u'admin', 'id': 1}
        from nav.web.templates.MainTemplate import MainTemplate
        MainTemplate.user = self.user
        self.module_under_test.apache = Mock('apache')
        self.module_under_test.apache.OK = 200

    def make_request(self, uri):
        """Returns a mocked mod_python request object for the given uri."""
        request = Mock('request')
        request.uri = uri
        request.unparsed_uri = uri
        request.filename = uri.endswith('/') and uri[:-1] or uri

        request.hostname = 'localhost'
        request.is_https = lambda: True
        request.session = {'user': self.user}
        request.headers_in = {'cookie': 'nav_sessid=xxx'}
        request.args = ''
        return request

    def handler_outputs_no_unicode(self, uri):
        request = self.make_request(uri)
        request.write = lambda s: self.assertNotEquals(type(s), unicode)
        self.assertEquals(self.module_under_test.handler(request), 200)

    def handler_should_return_ok_status(self, uri):
        request = self.make_request(uri)
        self.assertEquals(self.module_under_test.handler(request), 200)

