# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2010 UNINETT AS
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
import datetime

from twisted.internet import reactor, defer, task, threads
from twistedsnmp import snmpprotocol, agentproxy

import nav.models
import django.db.models.fields.related
from django.db import transaction

from nav.util import round_robin
from nav import ipdevpoll, toposort
from nav.ipdevpoll.plugins import plugin_registry
import storage
import shadows
import jobs
from dataloader import NetboxLoader

logger = logging.getLogger(__name__)
ports = round_robin([snmpprotocol.port() for i in range(10)])

def django_debug_cleanup():
    """Resets Django's list of logged queries.

    When DJANGO_DEBUG is set to true, Django will log all generated SQL queries
    in a list, which grows indefinitely.  This is ok for short-lived processes;
    not so much for daemons.  We may want those queries in the short-term, but
    in the long-term the ever-growing list is uninteresting and also bad.

    This should be called once-in-a-while from every thread that has Django
    database access, as the queries list is stored in thread-local data.

    """
    import gc
    import django.db
    from django.conf import settings

    query_count = len(django.db.connection.queries)
    if query_count:
        logger.debug("Removing %d logged Django queries", query_count)
        django.db.reset_queries()
        gc.collect()

class AbortedJobError(Exception):
    """Signals an aborted collection job."""
    def __init__(self, msg, cause=None):
        super(AbortedJobError, self).__init__(msg, cause )
        self.cause = cause


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

        instance_name = (self.name, "(%s)" % netbox.sysname)
        instance_queue_name = ("queue",) + instance_name
        self.logger = \
            ipdevpoll.get_instance_logger(self, ".".join(instance_name))
        self.queue_logger = \
            ipdevpoll.get_instance_logger(self, ".".join(instance_queue_name))

        self.plugins = plugins or []
        self.logger.debug("Job %r initialized with plugins: %r",
                          self.name, self.plugins)
        self.plugin_iterator = iter([])
        self.containers = storage.ContainerRepository()
        self.storage_queue = []

        # Initialize netbox in container
        nb = self.container_factory(shadows.Netbox, key=None)
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
                plugin = plugin_class(self.netbox, agent=self.agent,
                                      containers=self.containers)
                plugins.append(plugin)
            else:
                self.logger.debug("Plugin %s wouldn't handle %s",
                                  plugin_name, self.netbox.sysname)

        if not plugins:
            self.logger.debug("No plugins for this job")
            return

        self.logger.debug("Plugins to call: %s",
                          ",".join([p.name() for p in plugins]))

        return plugins

    def _iterate_plugins(self, plugins):
        """Iterates plugins."""
        plugins = iter(plugins)

        def log_plugin_failure(failure, plugin_instance):
            if failure.check(defer.TimeoutError):
                self.logger.error("Plugin %s reported a timeout",
                                  plugin_instance)
            else:
                self.logger.error("Plugin %s reported an unhandled failure:"
                                  "\n%s",
                                  plugin_instance, failure.getTraceback())
            return failure

        def next_plugin(result=None):
            try:
                plugin_instance = plugins.next()
            except StopIteration:
                return result

            self.logger.debug("Now calling plugin: %s", plugin_instance)
            self._start_plugin_timer(plugin_instance)

            df = plugin_instance.handle()
            df.addErrback(self._stop_plugin_timer)
            df.addErrback(log_plugin_failure, plugin_instance)
            df.addCallback(self._stop_plugin_timer)
            df.addCallback(next_plugin)
            return df

        return next_plugin()

    def run(self):
        """Starts a polling job for netbox and returns a Deferred."""
        plugins = self.find_plugins()
        self._reset_timers()
        if not plugins:
            return defer.succeed(None)

        self.logger.info("Starting job %r for %s",
                         self.name, self.netbox.sysname)

        def wrap_up_job(result):
            self.logger.info("Job %s for %s done.", self.name,
                             self.netbox.sysname)
            self._log_timings()
            return result

        def plugin_failure(failure):
            self._log_timings()
            raise AbortedJobError("Job aborted due to plugin failure",
                                  cause=failure.value)

        def save_failure(failure):
            self.logger.error("Save stage failed with unhandled error:\n%s",
                              failure.getTraceback())
            self._log_timings()
            raise AbortedJobError("Job aborted due to save failure",
                                  cause=failure.value)

        def log_abort(failure):
            if failure.check(AbortedJobError):
                self.logger.error("Job %r for %s aborted.",
                                  self.name, self.netbox.sysname)
            return failure

        def save(resutl):
            df = self.save_container()
            df.addErrback(save_failure)
            df.addCallback(wrap_up_job)
            return df

        # The action begins here
        df = self._iterate_plugins(plugins)
        df.addErrback(plugin_failure)
        df.addCallback(save)
        df.addErrback(log_abort)
        return df

    def _reset_timers(self):
        self._start_time = datetime.datetime.now()
        self._plugin_times = []

    def _start_plugin_timer(self, plugin):
        timings = [plugin.__class__.__name__, datetime.datetime.now()]
        self._plugin_times.append(timings)

    def _stop_plugin_timer(self, result=None):
        timings = self._plugin_times[-1]
        timings.append(datetime.datetime.now())
        return result

    def _log_timings(self):
        stop_time = datetime.datetime.now()
        job_total = stop_time-self._start_time

        times = [(plugin, stop-start)
                 for (plugin, start, stop) in self._plugin_times]
        plugin_total = sum((i[1] for i in times), datetime.timedelta(0))
        
        times.append(("Plugin total", plugin_total))
        times.append(("Job total", job_total))
        times.append(("Job overhead", job_total - plugin_total))

        log_text = []
        longest_label = max(len(i[0]) for i in times)
        format = "%%-%ds: %%s" % longest_label

        for plugin, delta in times:
            log_text.append(format % (plugin, delta))

        dashes = "-" * max(len(i) for i in log_text)
        log_text.insert(-3, dashes)
        log_text.insert(-2, dashes)

        log_text.insert(0, "Job %r timings for %s:" % 
                        (self.name, self.netbox.sysname))

        logger = ipdevpoll.get_instance_logger(self, "timings")
        logger.debug("\n".join(log_text))


    def save_container(self):
        """
        Parses the container and finds a sane storage order. We do this
        so we get ForeignKeys stored before the objects that are using them
        are stored.
        """
        @transaction.commit_on_success
        def complete_save_cycle():
            try:
                # Prepare all shadow objects for storage.
                self.prepare_containers_for_save()
                # Traverse all the objects in the storage container and generate
                # the storage queue
                self.populate_storage_queue()
                # Actually save to the database
                result = self.perform_save()
                self.log_timed_result(result, "Storing to database complete")
                # Do cleanup for the known container classes.
                self.cleanup_containers_after_save()
            finally:
                django_debug_cleanup()

        df = threads.deferToThread(complete_save_cycle)
        return df

    def prepare_containers_for_save(self):
        """Execute the prepare_for_save-method on all shadow classes with known
        instances.

        """
        for cls in self.containers.keys():
            cls.prepare_for_save(self.containers)

    def cleanup_containers_after_save(self):
        """Execute the cleanup_after_save-method on all shadow classes with
        known instances.

        """
        self.logger.debug("Running cleanup routines for %d classes (%r)",
                          len(self.containers), self.containers.keys())
        try:
            for cls in self.containers.keys():
                cls.cleanup_after_save(self.containers)
        except Exception, e:
            self.logger.exception("Caught exception during cleanup. "
                                  "Last class = %s",
                                  cls.__name__)
            import django.db
            if django.db.connection.queries:
                self.logger.error("The last query was: %s",
                                  django.db.connection.queries[-1])
            raise e

    def log_timed_result(self, res, msg):
        self.logger.debug(msg + " (%0.3f ms)" % res)

    def perform_save(self):
        start_time = time.time()
        try:
            self.storage_queue.reverse()
            if self.queue_logger.getEffectiveLevel() <= logging.DEBUG:
                self.queue_logger.debug(pprint.pformat(
                        [(id(o), o) for o in self.storage_queue]))

            while self.storage_queue:
                obj = self.storage_queue.pop()
                obj_model = obj.convert_to_model(self.containers)
                if obj.delete and obj_model:
                        obj_model.delete()
                else:
                    try:
                        # Skip if object exists in database and no fields
                        # are touched
                        if obj.getattr(obj, obj.get_primary_key().name) \
                            and not obj.get_touched():
                            continue
                    except AttributeError:
                        pass
                    if obj_model:
                        obj_model.save()
                        # In case we saved a new object, store a reference to
                        # the newly allocated primary key in the shadow object.
                        # This is to ensure that other shadows referring to
                        # this shadow will know about this change.
                        if not obj.get_primary_key():
                            obj.set_primary_key(obj_model.pk)
                        obj._touched = []

            end_time = time.time()
            total_time = (end_time - start_time) * 1000.0

            if self.queue_logger.getEffectiveLevel() <= logging.DEBUG:
                self.queue_logger.debug("containers after save: %s",
                                        pprint.pformat(self.containers))

            return total_time
        except Exception, e:
            self.logger.exception("Caught exception during save. "
                                  "Last object = %s. Last model: %s",
                                  obj, obj_model)
            import django.db
            if django.db.connection.queries:
                self.logger.error("The last query was: %s", 
                                  django.db.connection.queries[-1])
            raise e

    def populate_storage_queue(self):
        """Naive population of the storage queue.

        Assuming there are no inter-dependencies between instances of a single
        shadow class, the only relevant ordering is the one between the
        container types themselves.  This method will only order instances
        according to the dependency (topological) order of their classes.

        """
        for shadow_class in sorted_shadow_classes:
            if shadow_class in self.containers:
                shadows = self.containers[shadow_class].values()
                self.storage_queue.extend(shadows)

    def container_factory(self, container_class, key):
        """Container factory function"""
        return self.containers.factory(key, container_class)


class NetboxScheduler(object):
    """Netbox job schedule handler.

    An instance of this class takes care of scheduling, running and
    rescheduling of a single JobHandler for a single netbox.

    """

    ip_map = {}
    """A map of ip addresses there are currently active JobHandlers for.

    Scheduling will not allow simultaneous runs against the same IP
    address, so as to not overload the SNMP agent at that address.

    key: value  -->  str(ip): JobHandler instance
    """

    deferred_map = {} # Map active JobHandlers' deferred objects

    DEFAULT_INTERVAL = 3600.0 # seconds


    def __init__(self, jobname, netbox, interval=None, plugins=None):
        self.jobname = jobname
        self.netbox = netbox
        self.logger = \
            ipdevpoll.get_instance_logger(self, "%s.(%s)" % 
                                          (self.jobname, netbox.sysname))

        self.plugins = plugins or []
        self.interval = interval or self.DEFAULT_INTERVAL
        self.active = True

    def start(self):
        """Start polling schedule."""
        self.loop = task.LoopingCall(self.run_job)
        deferred = self.loop.start(interval=self.interval, now=True)
        return deferred

    def cancel(self):
        """Cancel scheduling of this job for this box.

        Future runs will not be scheduled after this."""
        self.loop.stop()
        self.logger.debug("Job %r cancelled for %s",
                          self.jobname, self.netbox.sysname)

    def _map_cleanup(self, result, job_handler):
        """Remove a JobHandler from internal data structures."""
        if job_handler.netbox.ip in NetboxScheduler.ip_map:
            del NetboxScheduler.ip_map[job_handler.netbox.ip]
        if job_handler in self.deferred_map:
            del self.deferred_map[job_handler]
        return result

    def run_job(self, dummy=None):
        ip = self.netbox.ip
        if ip in NetboxScheduler.ip_map:
            # We won't start a JobHandler now because a JobHandler is
            # already polling this IP address.
            other_job_handler = NetboxScheduler.ip_map[ip]
            self.logger.info(
                "Job %r is still running for %s, waiting for it to finish "
                "before starting %r",
                other_job_handler.name, self.netbox.sysname,
                self.jobname)
            if id(self.netbox) == id(other_job_handler.netbox):
                self.logger.debug(
                    "other job is working on an identical netbox instance")

            # Reschedule this function to be called as soon as the
            # other JobHandler is finished
            self.deferred_map[other_job_handler].addCallback(self.run_job)
        else:
            # We're ok to start a polling run.
            job_handler = JobHandler(self.jobname, self.netbox, 
                                     plugins=self.plugins)
            NetboxScheduler.ip_map[ip] = job_handler
            deferred = job_handler.run()
            self.deferred_map[job_handler] = deferred
            # Make sure to remove from ip_map as soon as this run is over
            deferred.addErrback(self._reschedule)
            deferred.addErrback(self._log_unhandled_error, job_handler)

            deferred.addCallback(self._map_cleanup, job_handler)
            deferred.addCallback(self._log_time_to_next_run)

    def _reschedule(self, failure):
        """Examines the job failure and reschedules the job if needed."""
        failure.trap(AbortedJobError)
        delay = 60
        self.logger.info("Rescheduling %r for %s in %d seconds",
                         self.jobname, self.netbox.sysname, delay)
        self.loop.call.reset(delay)

    def _log_unhandled_error(self, failure, job_handler):
        self.logger.exception(
            "Unhandled exception raised by JobHandler: %s\n%s",
            failure.getErrorMessage(),
            failure.getTraceback()
            )
        return failure

    def _log_time_to_next_run(self, thing=None):
        if hasattr(self.loop, 'call') and self.loop.call is not None:
            next_time = \
                datetime.datetime.fromtimestamp(self.loop.call.getTime())
            self.logger.debug("Next %r job for %s will be at %s",
                              self.jobname, self.netbox.sysname, next_time)
        return thing


class Scheduler(object):
    """Controller of the polling schedule.

    A scheduler allocates individual job schedules for each netbox.
    It will reload the list of netboxes from the database at set
    intervals; any netbox removed from the database will have its jobs
    descheduled, while new netboxes that appear will be scheduled
    immediately.

    There should only be one single Scheduler instance in an ipdevpoll
    process, although a singleton pattern will not be enforced by this
    class.

    """
    def __init__(self):
        self.netboxes = NetboxLoader()
        self.netbox_schedulers_map = {}

    def run(self):
        """Initiate scheduling of polling."""
        self.netbox_reload_loop = task.LoopingCall(self.reload_netboxes)
        # FIXME: Interval should be configurable
        deferred = self.netbox_reload_loop.start(interval=2*60.0, now=True)
        return deferred

    def reload_netboxes(self):
        """Reload the set of netboxes to poll and update schedules."""
        deferred = self.netboxes.load_all()
        deferred.addCallback(self.process_reloaded_netboxes)
        return deferred

    def process_reloaded_netboxes(self, result):
        """Process the result of a netbox reload and update schedules."""
        (new_ids, removed_ids, changed_ids) = result

        # Deschedule removed and changed boxes
        for netbox_id in removed_ids.union(changed_ids):
            self.cancel_netbox_schedulers(netbox_id)

        # Schedule new and changed boxes
        for netbox_id in new_ids.union(changed_ids):
            self.add_netbox_schedulers(netbox_id)

    def add_netbox_schedulers(self, netbox_id):
        for jobname,(interval, plugins) in jobs.get_jobs().items():
            self.add_netbox_scheduler(jobname, netbox_id, interval, plugins)
            
    def add_netbox_scheduler(self, jobname, netbox_id, interval, plugins):
        netbox = self.netboxes[netbox_id]
        scheduler = NetboxScheduler(jobname, netbox, interval, plugins)

        if netbox.id not in self.netbox_schedulers_map:
            self.netbox_schedulers_map[netbox.id] = [scheduler]
        else:
            self.netbox_schedulers_map[netbox.id].append(scheduler)
        return scheduler.start()

    def cancel_netbox_schedulers(self, netbox_id):
        if netbox_id in self.netbox_schedulers_map:
            schedulers = self.netbox_schedulers_map[netbox_id]
            for scheduler in schedulers:
                scheduler.cancel()
            del self.netbox_schedulers_map[netbox_id]
            return len(schedulers)
        else:
            return 0

def get_shadow_sort_order():
    """Return a topologically sorted list of shadow classes."""
    def get_dependencies(shadow_class):
        return shadow_class.get_dependencies()

    shadow_classes = storage.shadowed_classes.values()
    graph = toposort.build_graph(shadow_classes, get_dependencies)
    sorted_classes = toposort.topological_sort(graph)
    return sorted_classes


# As this module is loaded, we want to build a list of shadow classes
# sorted in topological order.  This only needs to be done once.  The
# list is used to find the correct order in which to store shadow
# objects at the end of a job.
sorted_shadow_classes = get_shadow_sort_order()
