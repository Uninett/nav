# -*- coding: ISO8859-1 -*-
#
# Copyright 2003, 2004 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#
# $Id: $
# Authors: Magnus Nordseth <magnun@itea.ntnu.no>
#          Erik Gorset     <erikgors@stud.ntnu.no>
#

import time
import socket
import sys
import types
import config
import mailAlert
import RunQueue
import db
import rrd
import event
from select import select
from errno import errorcode
from Socket import Socket
from debug import debug

TIMEOUT = 5 #default, hardcoded timeout :)

class AbstractChecker:
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
    def __init__(self,type,service,port=0,status=event.Event.UP):
        """
        type is the name of the handler (subclass)
        service is a dict containing ip, sysname, netboxid, serviceid,
        version and extra arguments to the handler
        status defaults to up, but can be overridden.
        """
        self._conf=config.serviceconf()
        self.setType(type)
        self.setServiceid(service['id'])
        self.setIp(service['ip'])
        self.setNetboxid(service['netboxid'])
        self.setArgs(service['args'])
        self.setVersion(service['version'])
        self.setSysname(service['sysname'])
        self.setDeviceid(service['deviceid'])
        # This is (and should be) used by all subclasses
        self.setPort(int(service['args'].get('port', port)))
        self.setStatus(status)
        self.setTimestamp(0)
        timeout = self.getArgs().get('timeout', self._conf.get("%s timeout" % self.getType(), self._conf.get('timeout',TIMEOUT)))
        self.setTimeout(int(timeout))
        self.db=db.db(config.dbconf())
        # self.alerter=mailAlert.mailAlert()
        debug("New checker instance for %s:%s " % (self.getSysname(), self.getType()),6)
        self.runcount=0
        self.rq=RunQueue.RunQueue()
        
    def run(self):
        """
        Calls executeTest(). If the status has changed it schedules a new
        test. If the service has been unavailable for more than self.runcount
        times, it marks the service as down.
        """
        version = self.getVersion()
        status, info = self.executeTest()
        service="%s:%s" % (self.getSysname(), self.getType())
        debug("%-20s -> %s" % (service, info), 6)

        if status == event.Event.UP:
            # Dirty hack to check if we timed out...
            # this is needed as ssl-socket calls may hang
            # in python < 2.3
            if self.getResponsetime() > 2 * self.getTimeout():
                debug("Adjusting status due to high responsetime (%s, %s)" % (service, self.getResponsetime()))
                status = event.Event.DOWN
                self.setResponsetime(2 * self.getTimeout())

        if status != self.getStatus() and self.runcount < int(self._conf.get('retry',3)):
            delay = int(self._conf.get('retry delay',5))
            self.runcount+=1
            debug("%-20s -> State changed. New check in %i sec. (%s, %s)" % (service, delay, status, info))
            # Updates rrd every time to get proper 'uptime' for the service
            self.updateRrd()
            priority=delay+time.time()
            # Queue ourself
            self.rq.enq((priority,self))
            return

        if status != self.getStatus():
            debug("%-20s -> %s, %s" % (service, status, info),1)
            newEvent=event.Event(self.getServiceid(),
                         self.getNetboxid(),
                         self.getDeviceid(),
                         event.Event.serviceState,
                         "serviceping",
                         status,
                         info
                         )

            # Post to the NAV alertq
            self.db.newEvent(newEvent)
            self.setStatus(status)
        
        if version != self.getVersion() and self.getStatus() == event.Event.UP:
            newEvent=event.Event(self.getServiceid(),
                         self.getNetboxid(),
                         self.getDeviceid(),
                         "version",
                         "serviceping",
                         status,
                         info,
                         version=self.getVersion()
                         )
            self.db.newEvent(newEvent)
        self.updateRrd()
        self.setTimestamp()
        self.runcount=0

    def updateRrd(self):
        try:
            rrd.update(self.getNetboxid(),
                   self.getSysname(),
                   'N',
                   self.getStatus(),
                   self.getResponsetime(),
                   self.getServiceid(),
                   self.getType()
                   )
        except Exception,e:
            service = "%s:%s" % (self.getSysname(), self.getType())
            debug("rrd update failed for %s [%s]" % (service,e),3)
        

    def executeTest(self):
        """
        Executes and times the test.
        Calls self.execute() which should be overridden
        by each subclass.
        """
        start = time.time()
        try:
            status,info = self.execute()
        except Exception,info:
            status = event.Event.DOWN
            info = str(info)
        self.setResponsetime(time.time()-start)
        return status, info

    def setServiceid(self,serviceid):
        """Sets the serviceid according to the database"""
        self._serviceid = serviceid
    def getServiceid(self):
        """Returns the serviceid """
        return self._serviceid
    def setNetboxid(self,netboxid):
        """Sets the netboxid according to the database """
        self._netboxid = netboxid
    def getNetboxid(self):
        """Returns the netboxid """
        return self._netboxid
    def setDeviceid(self, deviceid):
        """Sets the deviceid"""
        self._deviceid=deviceid
    def getDeviceid(self):
        return self._deviceid
    def getResponsetime(self):
        """Returns the responsetime of this service """
        return self._usage
    def setSysname(self, sysname):
        """Sets the sysname """
        self._sysname=sysname
    def getSysname(self):
        """Returns the sysname of which this service is running on.
        If no sysname is specified, the ip address is returned."""
        if self._sysname:
            return self._sysname
        else:
            return self.getIp()
    def setResponsetime(self,usage):
        """Sets the responsetime of this service. Is updated by self.run() """
        self._usage = usage
    def getStatus(self):
        """Returns the current status of this service. Typically
        Event.UP or Event.DOWN"""
        return self._status
    def setStatus(self,status):
        """Sets the current status. Is updated by self.run() """
        self._status = status
    def getTimestamp(self):
        """Returns the time of last check. """
        return self._timestamp
    def setTimestamp(self,when = -1):
        """Updates the time of last check. If no argument is
        supplied, it defaults to time.time()"""
        if when == -1:
            when = time.time()
        self._timestamp= when
    def setTimeout(self,value):
        """Sets the timeout value for this service. """
        self._timeout = value
    def getTimeout(self):
        """Returns the timeout value for this service. """
        return self._timeout
    def setArgs(self,args):
        self._args = args
    def getArgs(self):
        """Returns a dict containing all (nonstandard) arguments passed
        in to this handler. This could be port, username, password or any
        other argument a handler might need."""
        return self._args
    def setType(self,type):
        """Sets the name of the handler. This is used by the
        constructor."""
        self._type = type
    def getType(self):
        """Returns the name of the handler. """
        return self._type
    def setIp(self, ip):
        """Sets the ip address to connect to """
        self._ip = ip
    def getIp(self):
        """Returns the ip address to connect to """
        return self._ip
    def setPort(self, port):
        """Sets the port number to connect to. The constructor
        parses the arguments (self.getArgs()) and gets the port
        argument. If no port argument is specified, it sets the port
        to 0."""
        self._port = port
    def getPort(self):
        """Returns the port supplied as an argument to
        the test. If no argument is supplied, this function
        returns 0.
        This allows you to do (and i encourage you to)
        self.setPort(self.getPort() or DEFAULT_PORT_FOR_SERVICE)
        in your subclass."""
        return self._port
    def getAddress(self):
        """Returns a tuple (ip, port) """
        return (self._ip, self._port)
    def setAddress(self,address):
        """This should not be used. Set the ip address and port independently
        instead."""
        self._address = address
    def setVersion(self,version):
        """Sets the version of the service. Updateded by self.run() """
        self._version = version
    def getVersion(self):
        """Returns the current version of the service."""
        return self._version
    def __eq__(self,obj):
        return self.getServiceid() == obj.getServiceid() and self.getArgs() == obj.getArgs()
    def __cmp__(self,obj):
        return self.getTimestamp().__cmp__(obj.getTimestamp())
    def __hash__(self):
        value = self.getServiceid() + self.getArgs().__str__().__hash__() + self.getAddress().__hash__()
        value = value % 2**31
        return int(value)
    def __repr__(self):
        s = '%i: %s %s %s' % (self.getServiceid(),self.getType(),str(self.getAddress()),str(self.getArgs()))
        return s.ljust(60) + self.getStatus()


