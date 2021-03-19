#
# Copyright (C) 2014 Uninett AS
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
"""Tests for the WatchDog tests..."""

from unittest import TestCase
from mock import Mock, patch
from datetime import datetime, timedelta

import pytest

from nav.watchdog import tests


@pytest.fixture
def netboxes():
    with patch('nav.watchdog.tests.Netbox') as netbox:
        n1 = Mock()
        n1.ip = '129.241.23.23'
        n2 = Mock()
        n2.ip = '129.241.23.24'
        netbox.objects.all = Mock(return_value=[n1, n2])
        yield netbox


@patch(
    'nav.watchdog.tests.reverse_lookup',
    new=Mock(
        return_value={
            '129.241.23.23': ['netbox1'],
            '129.241.23.24': ['netbox1'],
            "10.0.0.42": ValueError("DNS Error when looking up 10.0.0.42"),
        }
    ),
)
class TestDuplicateHostname(object):
    def test_get_status(self, netboxes):
        self.test = tests.TestDuplicateHostnameForIP()
        assert self.test.get_status() == tests.STATUS_NOT_OK

    def test_status_when_initialized_is_unknown(self, netboxes):
        self.test = tests.TestDuplicateHostnameForIP()
        assert self.test.status == tests.STATUS_UNKNOWN

    def test_length_of_errors_when_initialized_is_zero(self, netboxes):
        self.test = tests.TestDuplicateHostnameForIP()
        assert len(self.test.errors) == 0

    def test_length_of_errors_when_run_is_one(self, netboxes):
        self.test = tests.TestDuplicateHostnameForIP()
        self.test.run()
        assert len(self.test.errors) == 1

    def test_errors_should_be_of_type_testresult(self, netboxes):
        self.test = tests.TestDuplicateHostnameForIP()
        self.test.run()
        assert isinstance(self.test.errors.pop(), tests.TestResult)


@patch('nav.watchdog.tests.TestNewCamAndArpRecords.get_latest')
class TestNewCamAndArp(object):
    def create_mock_time(self, seconds, endtime=None):
        if endtime is None:
            endtime = datetime.max
        return Mock(
            start_time=datetime.now() - timedelta(seconds=seconds), end_time=endtime
        )

    def test_no_arp_or_cam_records(self, get_latest):
        get_latest.return_value = None
        test = tests.TestNewCamAndArpRecords()
        assert test.get_status() == tests.STATUS_OK

    def test_cam_not_collected(self, get_latest):
        get_latest.return_value = self.create_mock_time(
            tests.TestNewCamAndArpRecords.slack + 10
        )
        test = tests.TestNewCamAndArpRecords()
        assert isinstance(test.test_cam(), tests.TestResult)

    def test_cam_collected(self, get_latest):
        get_latest.return_value = self.create_mock_time(
            tests.TestNewCamAndArpRecords.slack - 10
        )
        test = tests.TestNewCamAndArpRecords()
        assert test.test_cam() is None

    def test_arp_not_collected(self, get_latest):
        get_latest.return_value = self.create_mock_time(
            tests.TestNewCamAndArpRecords.slack + 10
        )
        test = tests.TestNewCamAndArpRecords()
        assert isinstance(test.test_arp(), tests.TestResult)

    def test_arp_collected(self, get_latest):
        get_latest.return_value = self.create_mock_time(
            tests.TestNewCamAndArpRecords.slack - 10
        )
        test = tests.TestNewCamAndArpRecords()
        assert test.test_arp() is None

    def test_both_collected(self, get_latest):
        get_latest.return_value = self.create_mock_time(
            tests.TestNewCamAndArpRecords.slack - 10
        )
        test = tests.TestNewCamAndArpRecords()
        assert test.get_status() == tests.STATUS_OK
        assert len(test.errors) == 0

    def test_none_collected(self, get_latest):
        get_latest.return_value = self.create_mock_time(
            tests.TestNewCamAndArpRecords.slack + 10
        )
        test = tests.TestNewCamAndArpRecords()
        assert test.get_status() == tests.STATUS_NOT_OK
        assert len(test.errors) == 2
