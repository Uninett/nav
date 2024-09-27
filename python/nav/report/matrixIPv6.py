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

from nav.django.templatetags.report import report
from nav.report import IPtools, metaIP
from nav.report.matrix import Matrix, Link

_logger = logging.getLogger(__name__)


class MatrixIPv6(Matrix):
    """This class serves as an interface for the prefix matrix."""

    def __init__(self, start_net, end_net=None):
        Matrix.__init__(self, start_net, end_net=end_net, bits_in_matrix=4)
        self.column_headings = ["%X" % i for i in range(0, 16)]
        self.visible_column_headings = self.column_headings
        self.num_columns = len(self.column_headings)

    def build(self):
        nets = IPtools.sort_nets_by_address(self.tree_nets.keys())
        self.nodes = [
            self.Node(net, self._write_subnets(self.tree_nets[net])) for net in nets
        ]

    def _write_subnets(self, net):
        nodes = IPtools.sort_nets_by_address(net.keys())
        subnet_matrix = []  # The resulting list of rows to display

        for subnet in nodes:
            matrix_row = []  # contains all cells in the row
            extra_rows = []  # For large nets

            matrix_row.append(self._create_index_cell(subnet))

            if subnet in self.matrix_nets:
                # We have data for this subnet, create cells for that data
                matrix_row.extend(self._create_data_row(subnet))
            else:
                # subnet is larger than row size
                num_extra_rows = self._add_large_subnet(subnet, matrix_row)
                extra_rows = self._create_extra_rows(num_extra_rows, subnet)

            subnet_matrix.append(matrix_row)
            subnet_matrix.extend(extra_rows)

        return subnet_matrix

    @staticmethod
    def _get_content(nybble, ip):
        return '{}::/{}'.format(nybble, ip.prefixlen())

    @staticmethod
    def _netlink(ip, append_term_and_prefix=False):
        """Creates the content for the index row"""
        ip = metaIP.MetaIP(ip).getTreeNet()
        url = report("prefix", netaddr=ip + '*', op_netaddr="like")
        text = ip + 'x'
        return Link(url, text, 'Go to prefix report')
