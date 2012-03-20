#
# Copyright (C) 2011, 2012 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""NAV network topology detection program"""

from optparse import OptionParser
from functools import wraps
import inspect
import logging
import sys
import os
import atexit

from nav import buildconf
from nav import daemon
from nav.debug import log_stacktrace, log_last_django_query
from nav.topology.layer2 import update_layer2_topology
from nav.topology.analyze import AdjacencyReducer, build_candidate_graph_from_db
from nav.topology.vlan import VlanGraphAnalyzer, VlanTopologyUpdater

LOGFILE_NAME = 'navtopology.log'
LOGFILE_PATH = os.path.join(buildconf.localstatedir, 'log', LOGFILE_NAME)
PIDFILE_PATH = os.path.join(buildconf.localstatedir, 'run', 'navtopology.pid')


def main():
    """Program entry point"""
    parser = make_option_parser()
    (options, _args) = parser.parse_args()

    init_logging()
    if options.l2 or options.vlan:
        # protect against multiple invocations of long-running jobs
        verify_singleton()
    if options.l2:
        do_layer2_detection()
    if options.vlan:
        if options.include_vlans:
            vlans = [int(v) for v in options.include_vlans]
        else:
            vlans = []
        do_vlan_detection(vlans)
        delete_unused_vlans()

def make_option_parser():
    """Sets up and returns a command line option parser."""
    parser = OptionParser(
        version="NAV " + buildconf.VERSION,
        description=("Detects and updates the network topology in your NAV "
                     "database")
        )

    parser.add_option("--l2", action="store_true", dest="l2",
                      help="Detect physical topology")
    parser.add_option("--vlan", action="store_true", dest="vlan",
                      help="Detect vlan subtopologies")
    parser.add_option("-i", dest="include_vlans", default="",
                      metavar="vlan[,...]",
                      help="Only analyze the VLANs included in this list")
    return parser

def init_logging():
    """Initializes logging for this program"""
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s %(name)s] %(message)s")
    handler = logging.FileHandler(LOGFILE_PATH, 'a')
    handler.setFormatter(formatter)

    root = logging.getLogger('')
    root.addHandler(handler)

    import nav.logs
    nav.logs.set_log_levels()

def with_exception_logging(func):
    """Decorates a function to log unhandled exceptions"""
    def _decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            stacktrace = inspect.trace()[1:]
            logger = logging.getLogger(__name__)
            logger.exception("An unhandled exception occurred")
            log_last_django_query(logger)
            log_stacktrace(logging.getLogger('nav.topology.stacktrace'),
                           stacktrace)
            raise

    return wraps(func)(_decorator)

@with_exception_logging
def do_layer2_detection():
    """Detect and update layer 2 topology"""
    reducer = AdjacencyReducer(build_candidate_graph_from_db())
    reducer.reduce()
    links = reducer.get_single_edges_from_ports()
    update_layer2_topology(links)

@with_exception_logging
def do_vlan_detection(vlans):
    analyzer = VlanGraphAnalyzer()
    if vlans:
        analyzer.analyze_vlans_by_id(vlans)
    else:
        analyzer.analyze_all()
    ifc_vlan_map = analyzer.add_access_port_vlans()
    update = VlanTopologyUpdater(ifc_vlan_map)
    update()

@with_exception_logging
def delete_unused_vlans():
    "Deletes vlans unassociated with prefixes or switch ports"
    from nav.models.manage import Vlan
    unused = Vlan.objects.filter(prefix__isnull=True, swportvlan__isnull=True)
    unused.delete()

def verify_singleton():
    """Verifies that we are the single running navtopology process.

    If a navtopology process is already running, we exit this process.

    """

    try:
        daemon.justme(PIDFILE_PATH)
    except daemon.AlreadyRunningError, error:
        print >> sys.stderr, "navtopology is already running (%d)" % error.pid
        sys.exit(1)

    daemon.writepidfile(PIDFILE_PATH)
    atexit.register(daemon.daemonexit, PIDFILE_PATH)

if __name__ == '__main__':
    main()
