#
# Copyright (C) 2011, 2012 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""NAV network topology detection program"""

from argparse import ArgumentParser
from functools import wraps
import inspect
import logging
import sys
import atexit

from django.db.models import Q
import django.db

from nav import buildconf
from nav import daemon
from nav.debug import log_stacktrace, log_last_django_query
from nav.logs import init_generic_logging
from nav.topology.layer2 import update_layer2_topology
from nav.topology.analyze import (
    AdjacencyReducer,
    build_candidate_graph_from_db,
    get_aggregate_mapping,
)
from nav.topology.vlan import VlanGraphAnalyzer, VlanTopologyUpdater

from nav.models.manage import Vlan, Prefix

LOG_FILE = 'navtopology.log'
PID_FILE = 'navtopology.pid'

_logger = logging.getLogger(__name__)


def main():
    """Program entry point"""
    parser = make_option_parser()
    options = parser.parse_args()

    init_generic_logging(
        logfile=LOG_FILE,
        stderr=options.stderr,
        stdout=True,
        read_config=True,
    )
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
        delete_unused_prefixes()
        delete_unused_vlans()


def int_list(value):
    return [int(x) for x in value.split(",")]


def make_option_parser():
    """Sets up and returns a command line option parser."""
    parser = ArgumentParser(
        description=("Detects and updates the network topology in your NAV database")
    )
    parser.add_argument(
        '--version', action='version', version='NAV ' + buildconf.VERSION
    )
    parser.add_argument("--l2", action="store_true", help="Detect physical topology")
    parser.add_argument("--vlan", action="store_true", help="Detect vlan subtopologies")
    parser.add_argument(
        "-i",
        dest="include_vlans",
        type=int_list,
        metavar="vlan[,...]",
        help="Only analyze the VLANs included in this list",
    )
    parser.add_argument(
        "-s", "--stderr", action="store_true", help="Log to stderr (even if not a tty)"
    )
    return parser


def with_exception_logging(func):
    """Decorates a function to log unhandled exceptions"""

    def _decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:  # noqa: BLE001
            stacktrace = inspect.trace()[1:]
            _logger = logging.getLogger(__name__)
            _logger.exception("An unhandled exception occurred")
            log_last_django_query(_logger)
            log_stacktrace(logging.getLogger('nav.topology.stacktrace'), stacktrace)
            raise

    return wraps(func)(_decorator)


@with_exception_logging
def do_layer2_detection():
    """Detect and update layer 2 topology"""
    candidates = build_candidate_graph_from_db()
    aggregates = get_aggregate_mapping(include_stacks=True)
    reducer = AdjacencyReducer(candidates, aggregates)
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
    """Deletes vlans unassociated with prefixes or switch ports"""
    unused = Vlan.objects.filter(prefixes__isnull=True, swport_vlans__isnull=True)
    if unused:
        _logger.info("deleting unused vlans: %r", unused)
        unused.delete()


@with_exception_logging
def delete_unused_prefixes():
    """
    Deletes prefixes that are unassociated with any router port and were not
    manually entered into NAV.
    """
    holy_vlans = Q(vlan__net_type__in=('scope', 'reserved', 'static'))
    unused_prefixes = Prefix.objects.filter(gwport_prefixes__isnull=True).exclude(
        holy_vlans
    )

    if unused_prefixes:
        _logger.info(
            "deleting unused prefixes: %s",
            ", ".join(p.net_address for p in unused_prefixes),
        )
        cursor = django.db.connection.cursor()
        # Use raw SQL to avoid Django's emulated cascading deletes
        cursor.execute(
            'DELETE FROM prefix WHERE prefixid IN %s',
            (tuple([p.id for p in unused_prefixes]),),
        )


def verify_singleton():
    """Verifies that we are the single running navtopology process.

    If a navtopology process is already running, we exit this process.

    """

    try:
        daemon.justme(PID_FILE)
    except daemon.AlreadyRunningError as error:
        print("navtopology is already running (%d)" % error.pid, file=sys.stderr)
        sys.exit(1)

    daemon.writepidfile(PID_FILE)
    atexit.register(daemon.daemonexit, PID_FILE)


if __name__ == '__main__':
    main()
