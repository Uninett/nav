#
# Copyright (C) 2009-2012 Uninett AS
# Copyright (C) 2022 Sikt
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
"""Job handling."""

import time
import datetime
import pprint
import logging
import threading
import gc
from itertools import cycle

from twisted.internet import defer, reactor
from twisted.internet.error import TimeoutError

from nav.ipdevpoll import ContextLogger
from nav.ipdevpoll.snmp import snmpprotocol, AgentProxy
from nav.ipdevpoll.snmp.common import SnmpError
from nav.metrics.carbon import send_metrics
from nav.metrics.templates import metric_prefix_for_ipdevpoll_job
from nav.models import manage
from nav.util import splitby
from nav.ipdevpoll import db
from .plugins import plugin_registry
from . import storage, shadows, dataloader
from .utils import log_unhandled_failure

_logger = logging.getLogger(__name__)
ports = cycle([snmpprotocol.port() for i in range(50)])


class AbortedJobError(Exception):
    """Signals an aborted collection job."""

    def __init__(self, msg, cause=None):
        Exception.__init__(self, msg, cause)
        self.cause = cause

    def __str__(self):
        return str(self.args[0]) + (" (cause=%r)" % self.cause if self.cause else "")


class SuggestedReschedule(AbortedJobError):
    """Can be raised by plugins to abort and reschedule a job at a specific
    later time, without necessarily logging it as a job failure.

    """

    def __init__(self, msg=None, cause=None, delay=60):
        self.delay = delay
        super(SuggestedReschedule, self).__init__(
            msg="Job was suggested rescheduled in %d seconds" % self.delay, cause=cause
        )


class JobHandler(object):
    """Handles a single polling job against a single netbox.

    An instance of this class performs a polling job, as described by
    a job specification in the config file, for a single netbox.  It
    will handle the dispatch of polling plugins, and contain state
    information for the job.

    """

    _logger = ContextLogger()
    _queue_logger = ContextLogger(suffix='queue')
    _timing_logger = ContextLogger(suffix='timings')
    _start_time = datetime.datetime.min

    def __init__(self, name, netbox, plugins=None, interval=None):
        self.name = name
        self.netbox_id = netbox
        self.netbox: shadows.Netbox = None
        self.cancelled = threading.Event()
        self.interval = interval

        self.plugins = plugins or []
        self._log_context = {}
        self.containers = storage.ContainerRepository()
        self.storage_queue = []

        self.agent = None

    def _create_agentproxy(self):
        if self.agent:
            self._destroy_agentproxy()

        if not self.netbox.snmp_parameters:
            self.agent = None
            return

        port = next(ports)
        self.agent = AgentProxy(
            self.netbox.ip,
            161,
            protocol=port.protocol,
            snmp_parameters=self.netbox.snmp_parameters,
        )
        try:
            self.agent.open()
        except SnmpError as error:
            self.agent.close()
            session_count = self.agent.count_open_sessions()
            job_count = self.get_instance_count()
            self._logger.error(
                "%s (%d currently open SNMP sessions, %d job handlers)",
                error,
                session_count,
                job_count,
            )
            raise AbortedJobError("Cannot open SNMP session", cause=error)
        else:
            self._logger.debug(
                "AgentProxy created for %s: %s", self.netbox.sysname, self.agent
            )

    def _destroy_agentproxy(self):
        if self.agent:
            self._logger.debug("Destroying agentproxy", self.agent)
            self.agent.close()
        self.agent = None

    @defer.inlineCallbacks
    def _find_plugins(self):
        """Populate the internal plugin list with plugin class instances."""
        from nav.ipdevpoll.config import ipdevpoll_conf

        plugin_classes = [plugin_registry[name] for name in self._get_valid_plugins()]
        willing_plugins = yield self._get_willing_plugins(plugin_classes)

        plugins = [
            cls(
                self.netbox,
                agent=self.agent,
                containers=self.containers,
                config=ipdevpoll_conf,
            )
            for cls in willing_plugins
        ]

        if not plugins:
            return None

        return plugins

    def _get_valid_plugins(self):
        valid_plugins, invalid_plugins = splitby(
            lambda name: name in plugin_registry, self.plugins
        )
        if list(invalid_plugins):
            self._logger.error(
                "Non-existent plugins were configured for job %r (ignoring them): %r",
                self.name,
                list(invalid_plugins),
            )
        return valid_plugins

    @defer.inlineCallbacks
    def _get_willing_plugins(self, plugin_classes):
        willing_plugins = []
        unwilling_plugins = []
        for cls in plugin_classes:
            try:
                can_handle = yield defer.maybeDeferred(cls.can_handle, self.netbox)
            except db.ResetDBConnectionError:
                raise
            # We very intentionally log and ignore unhandled exception here, to ensure
            # the stability of the ipdevpoll daemon
            except Exception:  # noqa: BLE001
                self._logger.exception("Unhandled exception from can_handle(): %r", cls)
                can_handle = False
            if can_handle:
                willing_plugins.append(cls)
            else:
                unwilling_plugins.append(cls)

        for willingness, plugins in [
            ('unwilling', unwilling_plugins),
            ('willing', willing_plugins),
        ]:
            if plugins:
                self._logger.debug(
                    "%s plugins: %r", willingness, [cls.__name__ for cls in plugins]
                )
            else:
                self._logger.debug("no %s plugins", willingness)

        return willing_plugins

    def _iterate_plugins(self, plugins):
        """Iterates plugins."""
        plugins = iter(plugins)

        def log_plugin_failure(failure, plugin_instance):
            if failure.check(TimeoutError, defer.TimeoutError):
                self._logger.debug(
                    "Plugin %s reported a timeout", plugin_instance.alias, exc_info=True
                )
                raise AbortedJobError(
                    "Plugin %s reported a timeout" % plugin_instance.alias
                )
            elif failure.check(SuggestedReschedule):
                self._logger.debug(
                    "Plugin %s suggested a reschedule in %d seconds",
                    plugin_instance,
                    failure.value.delay,
                )
            elif failure.check(db.ResetDBConnectionError):
                pass
            else:
                log_unhandled_failure(
                    self._logger,
                    failure,
                    "Plugin %s reported an unhandled failure",
                    plugin_instance,
                )
            return failure

        def next_plugin(result=None):
            self._raise_if_cancelled()
            try:
                plugin_instance = next(plugins)
            except StopIteration:
                return result

            self._logger.debug("Now calling plugin: %s", plugin_instance)
            self._start_plugin_timer(plugin_instance)

            df = defer.maybeDeferred(plugin_instance.handle)
            df.addErrback(self._stop_plugin_timer)
            df.addErrback(log_plugin_failure, plugin_instance)
            df.addCallback(self._stop_plugin_timer)
            df.addCallback(next_plugin)
            return df

        return next_plugin()

    @defer.inlineCallbacks
    def run(self):
        """Starts a polling job for netbox.

        :returns: A Deferred, whose result will be True when the job did
                  something, or False when the job did nothing (i.e. no
                  plugins ran).

        """
        self.netbox = yield db.run_in_thread(dataloader.load_netbox, self.netbox_id)
        self._log_context.update(dict(job=self.name, sysname=self.netbox.sysname))
        self._logger.debug(
            "Job %r started for netbox %s with plugins: %r",
            self.name,
            self.netbox_id,
            self.plugins,
        )
        # Initialize netbox in container
        self._container_factory(
            shadows.Netbox, key=None, id=self.netbox.id, sysname=self.netbox.sysname
        )

        self._create_agentproxy()
        plugins = yield self._find_plugins()
        self._reset_timers()
        if not plugins:
            self._destroy_agentproxy()
            return False

        self._logger.debug("Starting job %r for %s", self.name, self.netbox.sysname)

        def wrap_up_job(_result):
            self._logger.debug("Job %s for %s done.", self.name, self.netbox.sysname)
            self._log_timings()
            return True

        def plugin_failure(failure):
            self._log_timings()
            if not failure.check(AbortedJobError):
                raise AbortedJobError(
                    "Job aborted due to plugin failure", cause=failure.value
                )
            return failure

        def save_failure(failure):
            if not failure.check(db.ResetDBConnectionError):
                log_unhandled_failure(
                    self._logger, failure, "Save stage failed with unhandled error"
                )
            self._log_timings()
            raise AbortedJobError(
                "Job aborted due to save failure", cause=failure.value
            )

        def log_abort(failure):
            if failure.check(SuggestedReschedule):
                return failure
            if failure.check(AbortedJobError):
                self._logger.error(
                    "Job %r for %s aborted: %s",
                    self.name,
                    self.netbox.sysname,
                    failure.value,
                )
            return failure

        def save(result):
            if self.cancelled.is_set():
                return wrap_up_job(result)

            df = self._save_container()
            df.addErrback(save_failure)
            df.addCallback(wrap_up_job)
            return df

        shutdown_trigger_id = reactor.addSystemEventTrigger(
            "before", "shutdown", self.cancel
        )

        def cleanup(result):
            self._destroy_agentproxy()
            reactor.removeSystemEventTrigger(shutdown_trigger_id)
            return result

        def log_externally_success(result):
            self._log_job_externally(True if result else None)
            return result

        def log_externally_failure(result):
            self._log_job_externally(False)
            return result

        # The action begins here
        df = self._iterate_plugins(plugins)
        df.addErrback(plugin_failure)
        df.addCallback(save)
        df.addErrback(log_abort)
        df.addBoth(cleanup)
        df.addCallbacks(log_externally_success, log_externally_failure)
        yield df
        return True

    def cancel(self):
        """Cancels a running job.

        Job stops at the earliest convenience.
        """
        self.cancelled.set()
        self._logger.info("Cancelling running job")

    def _reset_timers(self):
        self._start_time = datetime.datetime.now()
        self._plugin_times = []

    def _start_plugin_timer(self, plugin):
        now = datetime.datetime.now()
        timings = [plugin.__class__.__name__, now, now]
        self._plugin_times.append(timings)

    def _stop_plugin_timer(self, result=None):
        timings = self._plugin_times[-1]
        timings[-1] = datetime.datetime.now()
        return result

    def _log_timings(self):
        stop_time = datetime.datetime.now()
        job_total = stop_time - self._start_time

        times = [(plugin, stop - start) for (plugin, start, stop) in self._plugin_times]
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

        log_text.insert(0, "Job %r timings for %s:" % (self.name, self.netbox.sysname))

        self._timing_logger.debug("\n".join(log_text))

    def get_current_runtime(self):
        """Returns time elapsed since the start of the job as a timedelta."""
        return datetime.datetime.now() - self._start_time

    def _save_container(self):
        """
        Parses the container and finds a sane storage order. We do this
        so we get ForeignKeys stored before the objects that are using them
        are stored.
        """

        @db.cleanup_django_debug_after
        def complete_save_cycle():
            # Traverse all the classes in the container repository and
            # generate the storage queue
            self._populate_storage_queue()
            # Prepare all shadow objects for storage.
            self._prepare_containers_for_save()
            # Actually save to the database
            result = self._perform_save()
            self._log_timed_result(result, "Storing to database complete")
            # Do cleanup for the known container classes.
            self._cleanup_containers_after_save()

        df = db.run_in_thread(complete_save_cycle)
        return df

    def _prepare_containers_for_save(self):
        """Runs every queued manager's prepare routine"""
        for manager in self.storage_queue:
            self._raise_if_cancelled()
            manager.prepare()

    def _cleanup_containers_after_save(self):
        """Runs every queued manager's cleanup routine"""
        self._logger.debug(
            "Running cleanup routines for %d managers: %r",
            len(self.storage_queue),
            self.storage_queue,
        )
        try:
            for manager in self.storage_queue:
                self._raise_if_cancelled()
                manager.cleanup()
        except AbortedJobError:
            raise
        except Exception:  # noqa: BLE001
            self._logger.exception(
                "Caught exception during cleanup. Last manager = %r", manager
            )
            import django.db

            if django.db.connection.queries:
                self._logger.error(
                    "The last query was: %s", django.db.connection.queries[-1]
                )
            raise

    def _log_timed_result(self, res, msg):
        self._logger.debug(msg + " (%0.3f ms)" % res)

    def _perform_save(self):
        start_time = time.time()
        manager = None
        try:
            self._log_containers("containers before save")

            for manager in self.storage_queue:
                self._raise_if_cancelled()
                manager.save()

            end_time = time.time()
            total_time = (end_time - start_time) * 1000.0

            self._log_containers("containers after save")

            return total_time
        except AbortedJobError:
            raise
        except Exception:  # noqa: BLE001
            self._logger.exception(
                "Caught exception during save. Last manager = %s. Last model = %s",
                manager,
                getattr(manager, 'cls', None),
            )
            import django.db

            if django.db.connection.queries:
                self._logger.error(
                    "The last query was: %s", django.db.connection.queries[-1]
                )
            raise

    def _log_containers(self, prefix=None):
        log = self._queue_logger
        if not log.isEnabledFor(logging.DEBUG):
            return
        log.debug(
            "%s%s", prefix and "%s: " % prefix, pprint.pformat(dict(self.containers))
        )

    def _populate_storage_queue(self):
        """Naive population of the storage queue.

        Assuming there are no inter-dependencies between instances of a single
        shadow class, the only relevant ordering is the one between the
        container types themselves.  This method will only order instances
        according to the dependency (topological) order of their classes.

        """
        for shadow_class in self.containers.sortedkeys():
            manager = shadow_class.manager(shadow_class, self.containers)
            self.storage_queue.append(manager)

    def _container_factory(self, container_class, key, *args, **kwargs):
        """Container factory function"""
        return self.containers.factory(key, container_class, *args, **kwargs)

    def _raise_if_cancelled(self):
        """Raises an AbortedJobError if the current job is cancelled"""
        if self.cancelled.is_set():
            raise AbortedJobError("Job was already cancelled")

    @classmethod
    def get_instance_count(cls):
        """Returns the number of JobHandler instances as seen by the garbage
        collector.

        """
        return len([o for o in gc.get_objects() if isinstance(o, cls)])

    @defer.inlineCallbacks
    def _log_job_externally(self, success=True):
        """Logs a job to the database"""
        duration = self.get_current_runtime()
        duration_in_seconds = (
            duration.days * 86400 + duration.seconds + duration.microseconds / 1e6
        )
        timestamp = time.time()

        def _create_record(timestamp):
            netbox = manage.Netbox.objects.get(id=self.netbox.id)
            if netbox.deleted_at:
                _logger.info(
                    "Not logging job to db; delete of this IP device"
                    " was requested at %s",
                    netbox.deleted_at,
                )
                return

            log = manage.IpdevpollJobLog(
                netbox_id=self.netbox.id,
                job_name=self.name,
                end_time=datetime.datetime.fromtimestamp(timestamp),
                duration=duration_in_seconds,
                success=success,
                interval=self.interval,
            )
            log.save()

        def _log_to_graphite():
            prefix = metric_prefix_for_ipdevpoll_job(self.netbox.sysname, self.name)
            runtime_path = prefix + ".runtime"
            runtime = (runtime_path, (timestamp, duration_in_seconds))
            send_metrics([runtime])

        _log_to_graphite()
        try:
            yield db.run_in_thread(_create_record, timestamp)
        except db.ResetDBConnectionError:
            pass  # this is being logged all over the place at the moment
        except Exception as error:  # noqa: BLE001
            _logger.warning("failed to log job to database: %s", error)
