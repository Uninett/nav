#
# Copyright (C) 2003-2004 Norwegian University of Science and Technology
# Copyright (C) 2012 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Builds the prefix matrix."""
import math
import logging
from collections import namedtuple

from nav.report.IPtree import buildTree
from nav.report.IPtree import getSubtree
from nav.report.IPtree import removeSubnetsWithPrefixLength
from nav.report.IPtree import extractSubtreesWithPrefixLength
from nav.report.IPtools import getLastSubnet

logger = logging.getLogger("nav.report.matrix")


class Matrix:

    Node = namedtuple(
        'Node',
        'net subnets'
    )
    Cell = namedtuple(
        'Cell',
        'colspan color content'
    )

    def __init__(self, start_net, end_net=None, bits_in_matrix=3):
        """This class is "abstract" and should not be instansiated directly.

        Superclass with usefull methods for IP matrices.

        Direct known subclasses:
                nav.report.matrixIPv6
                nav.report.matrixIPv4
        """

        if end_net is None:
            end_net = getLastSubnet(start_net)
        self.start_net = start_net
        self.end_net = end_net
        self.bits_in_matrix = bits_in_matrix
        self.tree = buildTree(
            start_net,
            end_net,
            bits_in_matrix=bits_in_matrix,
            add_missing_nets=True)
        self.tree_nets = self.extract_tree_nets()
        self.matrix_nets = self.extract_matrix_nets()
        self.heading_colspan = 1
        self.nodes = None

    def build(self):
        """Builds the datastructure for the template to render

            Must be overriden and implemented by subclasses
        """
        raise NotImplementedError('Must be implemented in subclass')

    def has_too_small_nets(self, net):
        """Returns true if argument ``net'' has too many small subnets for the matrix."""
        for net in getSubtree(self.tree, net):
            if net.prefixlen() > self.end_net.prefixlen():
                return True
        return False

    def extract_matrix_nets(self):
        """These should be shown as horizontal rows in the matrix."""
        return extractSubtreesWithPrefixLength(
            self.tree, self.end_net.prefixlen()-self.bits_in_matrix)

    def extract_tree_nets(self):
        """These should be listed vertically in the leftmost column."""
        return removeSubnetsWithPrefixLength(
            self.tree, self.end_net.prefixlen()-self.bits_in_matrix+1)

    def _colspan(self, ip):
        return int(math.pow(2, self.end_net.prefixlen() - ip.prefixlen()))

    @staticmethod
    def print_depth(depth):
        space = '&nbsp;'
        space *= depth
        return space
