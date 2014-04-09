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
"""Test classes for WatchDog"""

from nav.models.manage import IpdevpollJobLog


STATUS_OK = 'ok'
STATUS_NOT_OK = 'not_ok'
STATUS_UNKNOWN = 'unknown'


class TestResult(object):
    """Result for test errors"""

    def __init__(self, error):
        self.error = error

    def __unicode__(self):
        return unicode(self.error)

    def __str__(self):
        return unicode(self).encode('utf-8')


class Test(object):
    """Interface for all test classes"""

    self.name = 'Test'
    self.description = 'A WatchDog test'

    def __init__(self):
        self.status = STATUS_UNKNOWN
        self.errors = []

    @staticmethod
    def _get_errors():
        """Gets error list for this test"""
        raise NotImplementedError

    def run(self):
        """Runs the test. Sets self.errors and self.status"""
        self.errors = self._get_errors()
        self.status = (STATUS_OK if len(self.errors) == 0
                       else STATUS_NOT_OK)

    def get_status(self):
        """Runs the test and returns status"""
        self.run()
        return self.status


class TestOverdueJobs(Test):
    """Tests if there are any overdue ipdevpoll jobs"""

    self.name = 'Overdue jobs'
    self.description = 'Tests if there exists any overdue ipdevpoll jobs'

    @staticmethod
    def _get_errors():
        """Fetches the overdue jobs from ipdevpolljoblog"""
        query = """
          SELECT ijl.* FROM ipdevpoll_job_log AS ijl
          JOIN
          (
            SELECT netboxid, job_name, MAX(end_time) AS end_time
            FROM ipdevpoll_job_log
            GROUP BY netboxid, job_name
          ) AS foo
          USING (netboxid, job_name, end_time)
          JOIN netbox ON (ijl.netboxid = netbox.netboxid)
          WHERE now() - interval '1 second' * interval > end_time;
        """

        return [TestResult(x) for x in IpdevpollJobLog.objects.raw(query)]


class TestFailedJobs(Test):
    """Tests if there are any ipdevpolljobs that have failed"""

    self.name = 'Failed jobs'
    self.description = 'Tests if there exists any failed ipdevpoll jobs'

    @staticmethod
    def _get_errors():
        """Fetches failed ipdevpoll jobs"""
        query = """
          SELECT ijl.* FROM ipdevpoll_job_log AS ijl
          JOIN
          (
            SELECT netboxid, job_name, MAX(end_time) AS end_time
            FROM ipdevpoll_job_log
            GROUP BY netboxid, job_name
          ) AS foo
          USING (netboxid, job_name, end_time)
          JOIN netbox ON (ijl.netboxid = netbox.netboxid)
          WHERE success = 'f'
        """

        return [TestResult(x) for x in IpdevpollJobLog.objects.raw(query)]
