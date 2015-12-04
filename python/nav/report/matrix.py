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
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details. You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Builds the prefix matrix."""
import math
import IPy
from collections import namedtuple

from nav.report import metaIP, IPtools, IPtree


import logging
_logger = logging.getLogger(__name__)


class Cell(object):
    """Represents a table cell in subnet matrix"""
    def __init__(self, **kwargs):
        self.prefixid = kwargs.get('prefixid', '')
        self.colspan = kwargs.get('colspan', 1)
        self.rowspan = kwargs.get('rowspan', 1)
        self.content = kwargs.get('content', '&nbsp;')
        self.is_empty = kwargs.get('is_empty', False)
        self.netaddr = kwargs.get('netaddr')


class Matrix(object):
    """This class is "abstract" and should not be instansiated directly.

    Superclass with usefull methods for IP matrices.

    Direct known subclasses:
            nav.report.matrixIPv6
            nav.report.matrixIPv4
    """

    Node = namedtuple(
        'Node',
        'net subnets'
    )

    def __init__(self, start_net, end_net=None, bits_in_matrix=3):

        if end_net is None:
            end_net = IPtools.getLastSubnet(start_net)
        self.start_net = start_net
        self.end_net = end_net
        self.bits_in_matrix = bits_in_matrix
        self.tree = IPtree.buildTree(
            start_net,
            end_net,
            bits_in_matrix=bits_in_matrix,
            add_missing_nets=True)
        self.tree_nets = self.extract_tree_nets()
        self.matrix_nets = self.extract_matrix_nets()
        self.heading_colspan = 1
        self.nodes = None
        self.num_columns = None
        self.column_headings = None

    def build(self):
        """Builds the datastructure for the template to render

            Must be overriden and implemented by subclasses
        """
        raise NotImplementedError('Must be implemented in subclass')

    def has_too_small_nets(self, net):
        """
        Returns True if argument ``net'' has too many small subnets for the
        matrix.
        """
        for net in IPtree.getSubtree(self.tree, net):
            if net.prefixlen() > self.end_net.prefixlen():
                return True
        return False

    def extract_matrix_nets(self):
        """These should be shown as horizontal rows in the matrix."""
        return IPtree.extractSubtreesWithPrefixLength(
            self.tree, self.end_net.prefixlen()-self.bits_in_matrix)

    def extract_tree_nets(self):
        """These should be listed vertically in the leftmost column."""
        return IPtree.removeSubnetsWithPrefixLength(
            self.tree, self.end_net.prefixlen()-self.bits_in_matrix+1)

    def _colspan(self, ip):
        return min(self.num_columns,
                   int(math.pow(2, self.end_net.prefixlen() - ip.prefixlen())))

    def _get_row_size(self):
        """Gets the prefixlength for a row"""
        return self.end_net.prefixlen() - self.bits_in_matrix

    def _create_data_row(self, subnet):
        """Create a data row containing a list of cells

        :rtype: list[Cell]
        """
        if self.has_too_small_nets(subnet):
            return [self._create_to_small_subnets_cell()]

        elif self.matrix_nets[subnet]:
            _logger.debug('divided into several smaller nets')
            # this subnet is divided into parts
            host_nybbles_map = IPtools.getLastbitsIpMap(
                self.matrix_nets[subnet].keys())
            _logger.debug('nybbels: %s', host_nybbles_map)
            return self._add_child_nets(host_nybbles_map)

        else:
            # this subnet spans the whole row
            meta = metaIP.MetaIP(subnet)
            return [self._create_cell(subnet, meta)]

    def _add_child_nets(self, host_nybbles_map):
        next_header_idx = -1
        cells = []
        for i in self.column_headings:
            if self.column_headings.index(i) < next_header_idx:
                continue

            key = i.lower()
            if key in host_nybbles_map:
                ip = host_nybbles_map[key]
                meta = metaIP.MetaIP(ip)
                matrix_cell = self._create_cell(ip, meta, key=key)
                next_header_idx = (self.column_headings.index(i)
                                   + int(self._colspan(ip)))
            else:
                matrix_cell = Cell(is_empty=True)
            cells.append(matrix_cell)

        return cells

    def _create_cell(self, ip, meta, rowspan=1, key=0):
        """Creates a table cell based on ip"""
        return Cell(
            prefixid=meta.prefixid,
            colspan=self._colspan(ip),
            rowspan=rowspan,
            content=self._get_content(key, ip),
            netaddr=ip)

    @staticmethod
    def _create_empty_cell():
        return Cell(colspan=80, color=None, is_empty=True)

    def _create_index_cell(self, subnet, link=True):
        """Creates the cell for the first column in the matrix

        This cell typically displays the subnet

        :param link: If the cell should contain a link to subnet or not
        """
        if link:
            return Cell(content=self._netlink(subnet))
        else:
            return Cell(content=metaIP.MetaIP(subnet).getTreeNet())

    def _create_to_small_subnets_cell(self):
        return Cell(
            colspan=self.num_columns,
            color=self._get_color('large'),
            content='Too many small nets')

    def _add_large_subnet(self, subnet, matrix_row):
        """Adds correct rowspan to cell for large nets """
        meta = metaIP.MetaIP(subnet)
        rowspan = 2 ** (self._get_row_size() - subnet.prefixlen())
        matrix_row.append(self._create_cell(subnet, meta, rowspan=rowspan))

        # Return the number of extra rows that need to be made
        return rowspan - 1

    def _create_extra_rows(self, num_extra_rows, subnet):
        extra_nets = []
        row_net = IPy.IP('{}/{}'.format(subnet.net(), self._get_row_size()))
        for _ in range(num_extra_rows):
            row_net = IPtools.get_next_subnet(row_net)
            extra_nets.append(
                [self._create_index_cell(row_net, link=False)])
        return extra_nets

    @staticmethod
    def _get_content(key, ip):
        raise NotImplementedError

    @staticmethod
    def _netlink(ip, append_term_and_prefix=False):
        raise NotImplementedError

    @staticmethod
    def _get_color(nettype):
        """Gets the css-class name added to the cell based on usage"""

        if nettype == 'static' or nettype == 'scope' or nettype == 'reserved':
            return 'subnet_other'
        elif nettype == 'large':
            return 'subnet_large'
