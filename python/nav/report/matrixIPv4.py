#
# Copyright (C) 2007-2008 Uninett AS
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
# more details. You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""This class serves as an interface for the prefix matrix."""

import logging

from django.urls import reverse

from nav.django.templatetags.report import report
from nav.report import IPtools, metaIP
from nav.report.matrix import Matrix, Link, Cell

_logger = logging.getLogger(__name__)


class MatrixIPv4(Matrix):
    """This class serves as an interface for the prefix matrix."""

    def __init__(self, start_net, show_unused_addresses, end_net=None,
                 bits_in_matrix=3):
        Matrix.__init__(self, start_net, end_net=end_net,
                        bits_in_matrix=bits_in_matrix)
        self.column_headings = self._get_column_headers()
        self.visible_column_headings = self.column_headings[::4]
        self.num_columns = len(self.column_headings)
        self.show_unused_addresses = show_unused_addresses
        self.heading_colspan = 4

    def build(self):
        nets = IPtools.sort_nets_by_address(self.tree_nets.keys())
        self.nodes = [
            self.Node(net, self._write_subnets(net, self.tree_nets[net]))
            for net in nets
        ]

    def _write_subnets(self, net, nets):
        """Create a subnet structure

        :param net: IP instance of prefix to display
        :param nets: List of nets (rows) that have subnets. The subnets are
                     located in self.matrix_nets
        """

        large_subnets = []  # When displaying unused addresses, we need to know
                            # about the subnets that span more than one row
        subnet_matrix = []  # The resulting list of rows to display

        # Initially, create the rows (subnets) we're going to display
        if self.show_unused_addresses:
            row_size = self._get_row_size()
            subnets = IPtools.create_subnet_range(net, row_size)
            large_subnets = [x for x in nets.keys()
                             if x.prefixlen() < row_size]
        else:
            subnets = IPtools.sort_nets_by_address(nets.keys())

        while subnets:
            subnet = subnets.pop(0)

            matrix_row = []  # contains all cells in the row
            extra_rows = []  # For large nets

            matrix_row.append(self._create_index_cell(subnet))

            if subnet in self.matrix_nets:
                # We have data for this subnet, create cells for that data
                matrix_row.extend(self._create_data_row(subnet))
            else:
                # Either this subnet is bigger then a row or no subnet
                # exists here - we need to find out

                if self.show_unused_addresses:
                    # Find out if this subnet is part of a bigger subnet that
                    # should be displayed here
                    index = self._find_large_net(subnet, large_subnets)
                    if index is not None:
                        num_extra_rows = self._add_large_subnet(
                            large_subnets.pop(index), matrix_row)
                        extra_rows = self._get_extra_rows(num_extra_rows,
                                                          subnets)
                    else:
                        matrix_row.append(self._create_empty_cell())
                else:
                    # This net spans more then one row
                    num_extra_rows = self._add_large_subnet(subnet, matrix_row)
                    extra_rows = self._get_extra_rows(num_extra_rows, subnet)

            subnet_matrix.append(matrix_row)

            # These rows needs to be added after the main row is created for
            # nets that span more then one row
            subnet_matrix.extend(extra_rows)

        return subnet_matrix

    @staticmethod
    def _find_large_net(subnet, large_subnets):
        """Returns the index of the first large_subnet that overlaps subnet"""
        for index, large_net in enumerate(large_subnets):
            if large_net.overlaps(subnet):
                return index

    def _get_extra_rows(self, num_extra_rows, thing):
        """Returns the extra rows when dealing with large subnets

        Two cases (thing is different in these two cases):
        1: if we display unused address rows, we need to pop from the generated
           subnets.
        2: when displaying only used, we need to create new rows

        A row consists of a list containing one index cell
        """
        if self.show_unused_addresses:
            assert isinstance(thing, list)
            return [
                [self._create_index_cell(thing.pop(0), link=False)]
                for _ in range(num_extra_rows)
            ]
        else:
            return self._create_extra_rows(num_extra_rows, thing)

    def _get_row_size(self):
        """Gets the prefixlength for a row"""
        return self.end_net.prefixlen() - self.bits_in_matrix

    def _get_column_headers(self):
        netsize = self.end_net.len()
        factor = 32 - self.end_net.prefixlen()
        return [str((2**factor)*i) for i in range(0, 256//netsize)]
        # return [str((2**lsb)*i) for i in range(0, msb)]

    def __repr__(self):
        return "%s(%r, %r, %r, %r)" % (self.__class__.__name__,
                                       self.start_net,
                                       self.show_unused_addresses,
                                       self.end_net,
                                       self.bits_in_matrix)

    @staticmethod
    def _get_content(nybble, ip):
        return ".{}/{}".format(nybble, ip.prefixlen())

    @staticmethod
    def _netlink(ip, append_term_and_prefix=False):
        nip = metaIP.MetaIP(ip).getTreeNet()
        if append_term_and_prefix:
            url = reverse(
                'report-matrix-scope',
                kwargs={'scope': ip.strNormal().replace('/', '%2F')})
            text = ip.strNormal()
        else:
            url = report("prefix", netaddr=nip + ".*", op_netaddr="like")
            text = nip
        return Link(url, text, 'Go to prefix report')

    def _create_too_small_subnets_cell(self):
        return Cell(
            colspan=self.num_columns,
            color=self._get_color('large'),
            content='Too many small nets')
