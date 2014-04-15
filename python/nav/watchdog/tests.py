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

import collections
import itertools
from datetime import datetime, timedelta
from django.utils.timesince import timesince

from nav.asyncdns import reverse_lookup
from nav.models.manage import IpdevpollJobLog, Netbox, Arp, Cam


STATUS_OK = 'ok'
STATUS_NOT_OK = 'not_ok'
STATUS_UNKNOWN = 'unknown'


class TestResult(object):
    """Result for test errors"""

    def __init__(self, description, obj=None):
        self.description = description  # The human readable description
        self.obj = obj  # An optional object representing the test

    def __unicode__(self):
        return unicode(self.description)

    def __str__(self):
        return unicode(self).encode('utf-8')


class Test(object):
    """Interface for all test classes"""

    name = 'Test'
    description = 'A WatchDog test'

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

    name = 'Overdue jobs'
    description = 'Tests if there exists any overdue ipdevpoll jobs'

    @staticmethod
    def _get_errors():
        """
        Fetches the overdue jobs from ipdevpolljoblog. Because some jobs will
        take some time to run, give some slack to what is considered overdue.
        """
        slack = 120  # Seconds

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
          WHERE now() - interval '1 second' * interval > end_time
          ORDER BY netboxid;
        """

        errors = []
        for job in IpdevpollJobLog.objects.raw(query):
            should_have_run = job.end_time + timedelta(seconds=job.interval)
            overdue_by = datetime.now() - should_have_run
            if overdue_by.seconds > slack:
                time_since = timesince(datetime.now() - overdue_by)
                descr = "Job {} on {} is overdue by {}".format(
                    job.job_name, job.netbox.sysname, time_since)
                errors.append(TestResult(descr, job))

        return errors


class TestFailedJobs(Test):
    """Tests if there are any ipdevpolljobs that have failed"""

    name = 'Failed jobs'
    description = 'Tests if there exists any failed ipdevpoll jobs'

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
          ORDER BY netboxid;
        """

        return [TestResult(str(x), x)
                for x in IpdevpollJobLog.objects.raw(query)]


class TestDuplicateHostnameForIP(Test):
    """
    Tests of there are any number of IP-addresses that resolve to the same
    hostname
    """

    name = 'Duplicate Hostname'
    description = 'Tests if there are IP-addresses that resolve to the ' \
                  'same hostname'

    @staticmethod
    def _get_errors():
        """Fetches duplicate hostnames"""
        ip_addresses = [n.ip for n in Netbox.objects.all()]
        reverse_names = reverse_lookup(ip_addresses)
        flatten = list(itertools.chain(*reverse_names.values()))
        duplicates = set([x for x in flatten if flatten.count(x) > 1])
        results = collections.defaultdict(list)

        for hostname in duplicates:
            for ip, hostlist in reverse_names.items():
                if hostname in hostlist:
                    results[hostname].append(ip)

        errors = []
        for hostname, iplist in results.items():
            error = 'The hostname {} is used by these IP-addresses: {}'.format(
                hostname, ', '.join(iplist))
            errors.append(TestResult(error))

        return errors


class TestNoRouterInterfaces(Test):
    """Test if any router has no router-interfaces"""

    name = 'No router interfaces'
    description = 'Tests if there are routers that do not have any router interfaces'

    @staticmethod
    def _get_errors():
        """Fetches routers with no router interfaces"""
        results = []
        for netbox in Netbox.objects.filter(category__in=['GW', 'GSW']):
            if netbox.get_gwports().count() <= 0:
                descr = "{} has no router-interfaces".format(netbox.sysname)
                results.append(TestResult(descr, netbox))

        return results


class TestNoSwitchPorts(Test):
    """Test if any switch has no switch ports"""

    name = 'No switch ports'
    description = 'Tests if there are any switches that do not have any switch ports'

    @staticmethod
    def _get_errors():
        """Fetches switches with no switch ports"""
        results = []
        for netbox in Netbox.objects.filter(category__in=['GSW', 'SW']):
            if netbox.get_swports().count() <= 0:
                descr = "{} has no switch ports".format(netbox.sysname)
                results.append(TestResult(descr, netbox))

        return results


class TestAbnormalInterfaceCount(Test):
    """Tests for abnormal interface counts on devices"""

    # Random number, should be sanitized. Max for a Cisco 7200 with
    # 12.3T software is 20000. 5000 is above most of the other though.
    # But what is the case where this test is needed?
    abnormal_amount = 5000
    name = 'Abnormal interface count'
    description = 'Tests if there are IP Devices with more than {} ' \
        'interfaces'.format(abnormal_amount)

    def _get_errors(self):
        """Fetches netboxes with an abnormal amount of interfaces"""
        results = []
        for netbox in Netbox.objects.all().order_by('sysname'):
            count = netbox.interface_set.count()
            if count > self.abnormal_amount:
                descr = "{} has {} interfaces".format(netbox.sysname, count)
                results.append(TestResult(descr, netbox))

        return results


class TestNewCamAndArpRecords(Test):
    """Tests for new Arp and Cam records"""

    recently = 60 * 60  # 1 hour in seconds
    name = "ARP and CAM"
    description = "Tests if ARP and CAM has been collected the last hour"

    def _get_errors(self):
        """Checks for latest cam and arp"""
        latest_cam = Cam.objects.all().order_by('-start_time')[0]
        latest_arp = Arp.objects.all().order_by('-start_time')[0]

        now = datetime.now()
        cam_diff = now - latest_cam.start_time
        arp_diff = now - latest_arp.start_time

        results = []
        if cam_diff.seconds > self.recently:
            descr = 'CAM-records has not been collected the last {}'.format(
                timesince(latest_cam.start_time))
            results.append(TestResult(descr, latest_cam))

        if arp_diff.seconds > self.recently:
            descr = 'ARP-records has not been collected the last {}'.format(
                    timesince(latest_arp.start_time))
            results.append(TestResult(descr, latest_arp))

        return results
