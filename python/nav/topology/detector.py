#
# Copyright (C) 2011 UNINETT AS
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

from nav import buildconf
from nav.topology.layer2 import update_layer2_topology
from nav.topology.analyze import AdjacencyReducer, build_candidate_graph_from_db

def main():
    """Program entry point"""
    parser = make_option_parser()
    parser.parse_args()

    do_layer2_detection()

def make_option_parser():
    """Sets up and returns a command line option parser."""
    parser = OptionParser(
        version="NAV " + buildconf.VERSION,
        epilog="Detects and updates the network topology in the NAV database"
        )
    return parser

def do_layer2_detection():
    """Detect and update layer 2 topology"""
    reducer = AdjacencyReducer(build_candidate_graph_from_db())
    reducer.reduce()
    links = reducer.get_single_edges_from_ports()
    update_layer2_topology(links)


if __name__ == '__main__':
    main()
