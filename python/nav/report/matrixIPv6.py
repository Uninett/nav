#
# Copyright (C) 2007-2008 UNINETT AS
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
"""This class serves as an interface for the prefix matrix."""
import os
import nav.path

from django.core.urlresolvers import reverse

from nav.report import IPtools, metaIP
from nav.report.matrix import Matrix
from nav.report.colorconfig import ColorConfig


configfile = os.path.join(nav.path.sysconfdir, "report/matrix.conf")


class MatrixIPv6(Matrix):
    """This class serves as an interface for the prefix matrix."""

    def __init__(self, start_net, end_net=None):
        Matrix.__init__(self, start_net, end_net=end_net, bits_in_matrix=4)
        self.column_headings = ["%X" % i for i in range(0, 16)]
        self.visible_column_headings = self.column_headings
        self.num_columns = len(self.column_headings)
        self.color_configuration = ColorConfig(configfile)

    def build(self):

        nets = IPtools.sort_nets_by_address(self.tree_nets.keys())

        self.nodes = [
            self.Node(net, self._write_subnets(self.tree_nets[net], 1))
            for net in nets
        ]

    def _write_subnets(self, net, depth):

        nodes = IPtools.sort_nets_by_address(net.keys())
        lastnet = None
        subnet_matrix = []

        for subnet in nodes:
            if lastnet is None:
                lastnet = subnet

            if subnet in self.matrix_nets:
                if IPtools.isIntermediateNets(lastnet, subnet):
                    subnet_matrix.append(None)

                lastnet = subnet

                matrix_row = [
                    self.Cell(
                        colspan=1,
                        color=None,
                        content='{0}{1}'.format(
                            Matrix.print_depth(depth),
                            _netlink(subnet)))
                ]

                host_nybbles_map = IPtools.getLastbitsIpMap(
                    self.matrix_nets[subnet].keys())
                next_header_idx = -1
                for i in self.column_headings:
                    if self.column_headings.index(i) < next_header_idx:
                        continue

                    key = i.lower()
                    if key in host_nybbles_map:
                        meta = metaIP.MetaIP(host_nybbles_map[key])
                        ip = host_nybbles_map[key]
                        matrix_cell = self.Cell(
                            colspan=self._colspan(ip),
                            color=meta.ipv6_color,
                            content=_matrixlink(key, ip))
                        next_header_idx = self.column_headings.index(
                            i) + int(self._colspan(ip))
                    else:
                        matrix_cell = self.Cell(
                            colspan=1,
                            color=None,
                            content='&nbsp;')
                    matrix_row.append(matrix_cell)
                subnet_matrix.append(matrix_row)
            else:
                subnet_matrix.append(None)
                lastnet = subnet
                matrix_row = [
                    self.Cell(
                        colspan=1,
                        color=None,
                        content='{0}{1}'.format(
                            Matrix.print_depth(depth),
                            _netlink(subnet, True))),
                    self.Cell(
                        colspan=self.num_columns,
                        color=None,
                        content='&nbsp;')
                ]
                subnet_matrix.append(matrix_row)
                subnet_matrix.extend(
                    self._write_subnets(net[subnet], depth + 1))
        return subnet_matrix


def _matrixlink(nybble, ip):
    meta = metaIP.MetaIP(ip)
    url = reverse(
        'report-prefix-prefix',
        kwargs={'prefix_id': meta.prefixid})
    return '<a href="{0}" title="active IPs: {1}">{2}::/{3}</a>'.format(
        url,
        meta.active_ip_cnt,
        nybble,
        ip.prefixlen())


def _netlink(ip, append_term_and_prefix=False):

    nip = metaIP.MetaIP(ip).getTreeNet(leadingZeros=True)
    link = metaIP.MetaIP(ip).getTreeNet(leadingZeros=False)[:-1] + '_::'

    if append_term_and_prefix:
        url = reverse(
            'report-matrix-scope',
            kwargs={'scope': '{0}::%2F{1}'.format(nip, ip.prefixlen())})
        text = '{0}::/{1}'.format(nip, ip.prefixlen())
    else:
        url = reverse('report-prefix-netaddr', kwargs={'netaddr': link})
        text = nip[:-1] + 'x'
    return '<a class="monosp" href="{0}">{1}</a>'.format(url, text)
