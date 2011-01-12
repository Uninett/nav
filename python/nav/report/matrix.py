# -*- coding: utf-8 -*-
#
# Copyright (C) 2003-2004 Norwegian University of Science and Technology
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

from nav.report.IPtree import buildTree
from nav.report.IPtree import getSubtree
from nav.report.IPtree import removeSubnetsWithPrefixLength
from nav.report.IPtree import extractSubtreesWithPrefixLength
from nav.report.IPtools import getLastSubnet

class Matrix:

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
        self.tree = buildTree(start_net, end_net, bits_in_matrix=bits_in_matrix, add_missing_nets=True)
        self.tree_nets = self.extractTreeNets()
        self.matrix_nets = self.extractMatrixNets()

    def getTemplateResponse(self):
        abstract()

    def has_too_small_nets(self,net):
        """Returns true if argument ``net'' has too many small subnets for the matrix."""
        for net in getSubtree(self.tree,net):
            if net.prefixlen() > self.end_net.prefixlen():
                return True
        return False

    def extractMatrixNets(self):
        """These should be shown as horizontal rows in the matrix."""
        return extractSubtreesWithPrefixLength(self.tree,self.end_net.prefixlen()-self.bits_in_matrix)

    def extractTreeNets(self):
        """These should be listed vertically in the leftmost column."""
        return removeSubnetsWithPrefixLength(self.tree,self.end_net.prefixlen()-self.bits_in_matrix+1)

#because I'm a Java guy
def abstract():
    import inspect
    caller = inspect.getouterframes(inspect.currentframe())[1][3]
    raise NotImplementedError(" ".join([caller,"must be implemented in subclass"]))
