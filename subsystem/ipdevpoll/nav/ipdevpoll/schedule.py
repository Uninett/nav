# -*- coding: utf-8 -*-
#
# Copyright (C) 2008, 2009 UNINETT AS
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
"""Handle scheduling of polling jobs."""

import logging
import pprint
import time

from twisted.internet import reactor, defer, task, threads
from twistedsnmp import snmpprotocol, agentproxy

import django.db.models.fields.related
from django.db import transaction


from nav.util import round_robin
from nav import ipdevpoll
from nav.ipdevpoll.plugins import plugin_registry
import storage

logger = logging.getLogger(__name__)
ports = round_robin([snmpprotocol.port() for i in range(10)])

class JobHandler(object):

    """Handles a single polling job against a single netbox.

    An instance of this class performs a polling job, as described by
    a job specification in the config file, for a single netbox.  It
    will handle the dispatch of polling plugins, and contain state
    information for the job.

    """

    def __init__(self, name, netbox, plugins=None):
        self.name = name
        self.netbox = netbox
        self.logger = \
            ipdevpoll.get_instance_logger(self, "%s.[%s]" % 
                                          (self.name, netbox.sysname))

        self.plugins = plugins or []
        self.logger.debug("Job %r initialized with plugins: %r",
                          self.name, self.plugins)
        self.plugin_iterator = iter([])
        self.containers = {}
        self.storage_queue = []

        # Initialize netbox in container
        nb = self.container_factory(storage.Netbox, key=None)
        nb.id = netbox.id

        port = ports.next()

        self.agent = agentproxy.AgentProxy(
            self.netbox.ip, 161,
            community = self.netbox.read_only,
            snmpVersion = 'v%s' % self.netbox.snmp_version,
            protocol = port.protocol,
        )
        self.logger.debug("AgentProxy created for %s: %s",
                          self.netbox.sysname, self.agent)


    def find_plugins(self):
        """Populate the internal plugin list with plugin class instances."""

        plugins = []

        for plugin_name in self.plugins:
            if plugin_name not in plugin_registry:
                self.logger.error("A non-existant plugin %r is configured "
                                  "for job %r", plugin_name, self.name)
                continue
            plugin_class = plugin_registry[plugin_name]

            # Check if plugin wants to handle the netbox at all
            if plugin_class.can_handle(self.netbox):
                plugin = plugin_class(self.netbox, job_handler=self)
                plugins.append(plugin)
            else:
                self.logger.debug("Plugin %s wouldn't handle %s",
                                  plugin_name, self.netbox.sysname)

        if not plugins:
            self.logger.warning("No plugins for this job")
            return

        self.logger.debug("Plugins to call: %s",
                          ",".join([p.name() for p in plugins]))

        self.plugin_iterator = iter(plugins)

    def run(self):
        """Start a polling run against a netbox and retun a deferred."""

        self.logger.info("Starting polling run")
        self.find_plugins()
        self.deferred = defer.Deferred()

        # Hop on to the first plugin
        self._nextplugin()
        return self.deferred

    def _nextplugin(self, result=None):
        """Callback that advances to the next plugin in the sequence."""
        try:
            self.current_plugin = self.plugin_iterator.next()
        except StopIteration:
            return self._done()
        else:
            self.logger.debug("Now calling plugin: %s", self.current_plugin)
            df = self.current_plugin.handle()
            # Make sure we advance to next plugin when this one is done
            df.addCallback(self._nextplugin)
            df.addErrback(self._error)

    def _error(self, failure):
        """Error callback that handles plugin failures."""
        if failure.check(ipdevpoll.FatalPluginError):
            # Handle known exceptions from plugins
            self.logger.error("Aborting poll run due to error in plugin "
                              "%s: %s",
                              self.current_plugin, failure.getErrorMessage())
        else:
            # For unknown failures we dump a traceback.  The
            # JobHandler will eat all plugin errors to protect the
            # daemon process.
            self.logger.error("Aborting poll run due to unknown error in "
                              "plugin %s\n%s",
                              self.current_plugin, failure.getTraceback())

        # FIXME why is this commented out?
        #self.deferred.errback(err)
        #return self.deferred

    def _done(self):
        """Performs internal cleanup and callback firing.

        This is called after successful poll run.

        """
        self.save_container()
        self.logger.info("Job done")

        # Fire the callback chain
        self.deferred.callback(self)
        return self.deferred

    @defer.deferredGenerator
    def save_container(self):
        """
        Parses the container and finds a sane storage order. We do this
        so we get ForeignKeys stored before the objects that are using them
        are stored.
        """

        # Traverse all the objects in the storage container and generate
        # the storage queue
        # Actually save to the database
        df = threads.deferToThread(self.traverse_all_instances)
        dw = defer.waitForDeferred(df)
        yield dw

        df = threads.deferToThread(self.perform_save)
        df.addCallback(self.log_timed_result, "Storing to database complete")
        dw = defer.waitForDeferred(df)
        yield dw

    def log_timed_result(self, res, msg):
        self.logger.debug(msg + " (%0.3f ms)" % res)

    @transaction.commit_manually
    def perform_save(self):
        start_time = time.time()
        try:
            self.storage_queue.reverse()
            while self.storage_queue:
                obj = self.storage_queue.pop()
                if obj.delete:
                    obj.get_model().delete()
                else:
                    try:
                        # Skip if object exists in database, and no fields
                        # are touched
                        if obj.getattr(obj, obj.__shadowclass__._meta.pk.name) \
                            and not obj.get_touched():
                            continue
                    except AttributeError:
                        pass
                    obj.get_model().save()
                    obj._touched = []

            transaction.commit()
            end_time = time.time()
            total_time = (end_time - start_time) * 1000.0
            return total_time
        except Exception, e:
            self.logger.debug("Caught exception during save. Last object = %s. Exception:\n%s" % (obj, e))
            transaction.rollback()

    def traverse_all_instances(self):
        for key in self.containers.keys():
            for instance in  self.containers[key].values():
                if instance in self.storage_queue:
                    continue
                l = self.traverse_instance_for_storage(instance, self.storage_queue)
                self.storage_queue.extend([r for r in l if r not in self.storage_queue])

    def traverse_instance_for_storage(self, instance, storage_queue):
        try:
            storage_queue.insert(0, instance)

            for field in instance.__class__._fields:
                t = instance.__class__.__shadowclass__._meta.get_field(field)
                if issubclass(t.__class__, django.db.models.fields.related.ForeignKey):
                    if t.rel.to in storage.shadowed_classes:
                        if not storage.shadowed_classes[t.rel.to] in self.containers:
                            pass
                        else:
                            # If the foreignkey is not None, then traverse that object as well
                            if not getattr(instance, field):
                                continue
                            if getattr(instance, field) in self.containers[storage.shadowed_classes[t.rel.to]].values():
                                storage_queue = self.traverse_instance_for_storage(getattr(instance, field), storage_queue)
        except Exception, e:
            self.logger.error(e)
        return storage_queue


    def container_factory(self, container_class, key):
        """Container factory function"""
        if not issubclass(container_class, storage.Shadow):
            raise ValueError("%s is not a shadow container class" % container_class)

        if container_class not in self.containers or \
                key not in self.containers[container_class]:

            obj = container_class()
            if container_class not in self.containers:
                self.containers[container_class] = {}
            self.containers[container_class][key] = obj

        else:
            obj = self.containers[container_class][key]

        return obj


class Schedule(object):

    """Netbox polling schedule handler.

    Does not employ task.LoopingCall because we want to reschedule at
    the end of each JobHandler, not run the handler at fixed times.

    """

    ip_map = {}
    """A map of ip addresses there are currently active JobHandlers for.

    Scheduling will not allow simultaineous runs against the same IP
    address, so as to not overload the SNMP agent at that address.

    key: value  -->  str(ip): JobHandler instance
    """
    INTERVAL = 3600.0 # seconds


    def __init__(self, jobname, netbox, interval=None, plugins=None):
        self.jobname = jobname
        self.netbox = netbox
        self.logger = \
            ipdevpoll.get_instance_logger(self, "%s.[%s]" % 
                                          (self.jobname, netbox.sysname))

        self.plugins = plugins or []
        self.interval = interval or self.INTERVAL

    def start(self):
        """Start polling schedule."""
        return self._do_poll()

    def _reschedule(self, dummy=None):
        self.delayed = reactor.callLater(self.interval, self._do_poll)
        self.logger.debug("Rescheduling job %r for %s in %s seconds",
                          self.jobname, self.netbox.sysname, self.interval)
        return dummy

    def _map_cleanup(self, handler):
        """Remove a handler from the ip map."""
        if handler.netbox.ip in Schedule.ip_map:
            del Schedule.ip_map[handler.netbox.ip]
        return handler

    def _do_poll(self, dummy=None):
        ip = self.netbox.ip
        if ip in Schedule.ip_map:
            # We won't start a runhandler now because a runhandler is
            # already polling this IP address.
            other_handler = Schedule.ip_map[ip]
            self.logger.info("schedule clash: waiting for run for %s to "
                             "finish before starting run for %s",
                             other_handler.netbox, self.netbox)
            if id(self.netbox) == id(other_handler.netbox):
                self.logger.debug("Clashing instances are identical")

            # Reschedule this function to be called as soon as the
            # other runhandler is finished
            other_handler.deferred.addCallback(self._do_poll)
        else:
            # We're ok to start a polling run.
            handler = JobHandler(self.jobname, self.netbox, plugins=self.plugins)
            Schedule.ip_map[ip] = handler
            deferred = handler.run()
            # Make sure to remove from map and reschedule next run as
            # soon as this one is over.
            deferred.addCallback(self._map_cleanup)
            deferred.addCallback(self._reschedule)
        return dummy
