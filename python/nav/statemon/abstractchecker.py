#
# Copyright (C) 2018 Uninett AS
# Copyright (C) 2022 Sikt
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
"""Base functionality for service checkers"""

import time
import logging

from nav.statemon import config, RunQueue, db, statistics, event


_logger = logging.getLogger(__name__)
TIMEOUT = 5  # default, hardcoded timeout :)


class AbstractChecker(object):
    """
    This is the superclass for each handler. Note that it is
    'abstract' and should not be instanciated directly. If you want to
    check a service that is not supported by NAV, you have to
    write your own handler. This is done quite easily by subclassing
    this class.

    Quick how-to:
    Let's say we want to create a handler for the gopher service.
    Create a new file called GopherHandler.py in the handler/
    subdirectory. (the filename must be on that form).
    This file should look something like this:

    from abstractHandler import AbstractHandler # this is important
    from event import Event
    class GopherHandler(AbstractHandler):
      def __init__(self, service, **kwargs):
            # gopher usually runs on port 70
        AbstractHandler.__init__(self, "gopher", service, port=70 **kwargs)

      def execute(self):
        # In case you need user/pass you can do like this:
        args = self.getArgs()
        user = args.get("username", "")
        pass = args.get("password", "")
            # Now you need to do the actual check
        # I don't implement it now, but every exception is
        # caught by the suberclass, and will mark the service
        # as down. If you want to create a more understandable
        # error message you should catch the Exception here and
        # return Event.DOWN, "some valid error message"
        # You should try to extract a version number from the server.
        version = ""
        # and then we return status UP, and our version string.
        return Event.UP, version
    """

    IPV6_SUPPORT = False
    DESCRIPTION = ""
    ARGS = ()
    OPTARGS = ()

    def __init__(self, service, port=0, status=event.Event.UP):
        """
        type is the name of the handler (subclass)
        service is a dict containing ip, sysname, netboxid, serviceid,
        version and extra arguments to the handler
        status defaults to up, but can be overridden.
        """
        self.response_time = None
        self._conf = config.serviceconf()
        self.serviceid = service['id']
        self.ip = service['ip']
        self.netboxid = service['netboxid']
        self.args = service['args']
        self.version = service['version']
        self._sysname = service['sysname']
        # This is (and should be) used by all subclasses
        self.port = int(service['args'].get('port', port))
        self.status = status
        self.timestamp = 0
        timeout = self.args.get(
            'timeout',
            self._conf.get(
                "%s timeout" % self.get_type(), self._conf.get('timeout', TIMEOUT)
            ),
        )
        self.timeout = int(timeout)
        self.db = db.db()
        _logger.info("New checker instance for %s:%s ", self.sysname, self.get_type())
        self.runcount = 0
        self.runq = RunQueue.RunQueue()

    def run(self):
        """
        Calls execute_test(). If the status has changed it schedules a new
        test. If the service has been unavailable for more than self.runcount
        times, it marks the service as down.
        """
        orig_version = self.version
        status, info = self.execute_test()
        service = "%s:%s" % (self.sysname, self.get_type())
        _logger.info("%-20s -> %s", service, info)

        if status != self.status and (self.runcount < int(self._conf.get('retry', 3))):
            delay = int(self._conf.get('retry delay', 5))
            self.runcount += 1
            _logger.info(
                "%-20s -> State changed. New check in %i sec. (%s, %s)",
                service,
                delay,
                status,
                info,
            )
            # Update metrics every time to get proper 'uptime' for the service
            self.update_stats()
            priority = delay + time.time()
            # Queue ourself
            self.runq.enq((priority, self))
            return

        if status != self.status:
            _logger.critical("%-20s -> %s, %s", service, status, info)
            new_event = event.Event(
                self.serviceid,
                self.netboxid,
                None,  # deviceid
                event.Event.serviceState,
                "serviceping",
                status,
                info,
            )

            # Post to the NAV alertq
            self.db.new_event(new_event)
            self.status = status

        if orig_version != self.version and self.status == event.Event.UP:
            new_event = event.Event(
                self.serviceid,
                self.netboxid,
                None,  # deviceid
                "version",
                "serviceping",
                status,
                info,
                version=self.version,
            )
            self.db.new_event(new_event)
        self.update_stats()
        self.update_timestamp()
        self.runcount = 0

    def update_stats(self):
        """Send an updated metric to the Graphite backend"""
        try:
            statistics.update(
                self.sysname,
                'N',
                self.status,
                self.response_time,
                self.serviceid,
                self.get_type(),
            )
        except Exception as err:  # noqa: BLE001
            service = "%s:%s" % (self.sysname, self.get_type())
            _logger.error("statistics update failed for %s [%s]", service, err)

    def execute_test(self):
        """
        Executes and times the test.
        Calls self.execute() which should be overridden
        by each subclass.
        """
        start = time.time()
        try:
            status, info = self.execute()
        except Exception as error:  # noqa: BLE001
            status = event.Event.DOWN
            info = str(error)
        self.response_time = time.time() - start
        return status, info

    def execute(self):
        """Executes the actual service test implemented by a plugin"""
        raise NotImplementedError

    @property
    def sysname(self):
        """Returns the sysname of which this service is running on.
        If no sysname is specified, the ip address is returned."""
        if self._sysname:
            return self._sysname
        else:
            return self.ip

    @sysname.setter
    def sysname(self, name):
        """Sets the sysname"""
        self._sysname = name

    def update_timestamp(self):
        """Updates the time of last check to the current time"""
        self.timestamp = time.time()

    @classmethod
    def get_type(cls):
        """Returns the name of the handler."""
        suffix = "checker"
        name = cls.__name__.lower()
        name = name.removesuffix(suffix)
        return name

    def get_address(self):
        """Returns a tuple (ip, port)"""
        return self.ip, self.port

    def __eq__(self, obj):
        return self.serviceid == getattr(
            obj, 'serviceid', None
        ) and self.args == getattr(obj, 'args', None)

    def __lt__(self, obj):
        return self.timestamp < getattr(obj, 'timestamp', None)

    def __hash__(self):
        tup = (self.serviceid, str(self.args), self.get_address())
        return hash(tup)

    def __repr__(self):
        rep = '%i: %s %s %s' % (
            self.serviceid,
            self.get_type(),
            self.get_address(),
            self.args,
        )
        return rep.ljust(60) + self.status
