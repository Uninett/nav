#
# Copyright (C) 2014 UNINETT AS
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
"""Util functions for WatchDog"""

import json
from .tests import Test


def get_statuses():
    """Runs and returns all tests"""

    # Not sure this is kosher
    test_results = []
    for cls in Test.__subclasses__():
        test = cls()
        test.run()
        test_results.append(test)

    return test_results


def get_statuses_as_json():
    """Runs and returns all tests in JSON format"""
    return json.dumps([serialize(x) for x in get_statuses()])


def serialize(test):
    """Creates an object suitable for json out of a test

    :param test: A test instance
    """
    return {
        'name': test.name,
        'decription': test.description,
        'status': test.get_status(),  # Also runs the test
        'errors': test.errors
    }
