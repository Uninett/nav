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
import IPy

import nav.path
from nav.report import IPtools, IPtree, metaIP
from nav.report.IPtools import netDiff
from nav.report.matrix import Matrix
from nav.report.colorconfig import ColorConfig


configfile = os.path.join(nav.path.sysconfdir, "report/matrix.conf")


class MatrixIPv4(Matrix):
    """This class serves as an interface for the prefix matrix."""

    def __init__(self, start_net, show_unused_addresses, end_net=None,
                 bits_in_matrix=3):
        Matrix.__init__(self, start_net, end_net=end_net,
                        bits_in_matrix=bits_in_matrix)
        self.column_headings = self._getColumnHeaders()
        self.num_columns = len(self.column_headings)
        self.show_unused_addresses = show_unused_addresses
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
                if self.show_unused_addresses:
                    subnet_matrix.extend(
                        self._netsInRange(
                            lastnet,
                            subnet,
                            depth))

                lastnet = subnet
                matrix_row = [
                    self.Cell(
                        colspan=1,
                        color=None,
                        content='{0} {1}'.format(
                            Matrix.printDepth(depth),
                            _netlink(subnet)))
                ]

                host_nybbles_map = IPtools.getLastbitsIpMap(
                    self.matrix_nets[subnet].keys())
                next_header_idx = -1

                if self.has_too_small_nets(subnet):
                    matrix_row.append(
                        self.Cell(
                            colspan=self.num_columns,
                            color=self._loadColor(0, 'large'),
                            content='Too many small nets')
                    )

                elif host_nybbles_map is None:
                # i.e. there exist a net with no
                # subnets <==> net spans whole row
                    ip = IPy.IP(subnet)
                    meta = metaIP.MetaIP(ip)
                    matrix_row.append(
                        self.Cell(
                            colspan=self.num_columns,
                            color=self._loadColor(
                                meta.usage_percent,
                                meta.nettype),
                            content=_matrixlink(0, ip))
                    )

                else:
                # The net exists and have subnets
                    for i in self.column_headings:
                        if self.column_headings.index(i) < next_header_idx:
                            continue

                        key = i.lower()
                        if key in host_nybbles_map:
                            ip = host_nybbles_map[key]
                            meta = metaIP.MetaIP(ip)
                            matrix_cell = self.Cell(
                                colspan=self._colspan(ip),
                                color=self._loadColor(
                                    meta.usage_percent,
                                    meta.nettype),
                                content=_matrixlink(key, ip))
                            next_header_idx = (self.column_headings.index(i)
                                               + int(self._colspan(ip)))
                        else:
                            matrix_cell = self.Cell(
                                colspan=1,
                                color=None,
                                content='&nbsp;')
                        matrix_row.append(matrix_cell)
                subnet_matrix.append(matrix_row)
            else:
                if (self.matrix_nets
                    and lastnet.prefixlen() <
                        self.matrix_nets.keys()[0].prefixlen()):
                    mnets = self.generateMatrixNets(lastnet)
                    subnet_extended = IPy.IP(
                        '/'.join([
                            subnet.net.strNormal(),
                            str(self.matrix_nets.keys()[0].prefixlen())
                        ]))
                    subnet_matrix.extend(
                        self._netsInRange(
                            mnets[-1],
                            subnet_extended,
                            depth))
                lastnet = subnet
                meta = metaIP.MetaIP(subnet)
                matrix_row = [
                    self.Cell(
                        colspan=1,
                        color=None,
                        content='{0} {1}'.format(
                            Matrix.printDepth(depth),
                            _netlink(subnet, True))),
                    self.Cell(
                        colspan=self.num_columns,
                        color=self._loadColor(
                            meta.usage_percent,
                            meta.nettype),
                        content=_supernetMatrixlink(subnet))
                ]
                subnet_matrix.append(matrix_row)
                subnet_matrix.extend(
                    self._write_subnets(net[subnet], depth + 1))
                subnet_matrix.extend(
                    self._remainingBlankNets(subnet, depth + 1))
        return subnet_matrix

    def _remainingBlankNets(self, ip, depth):
        if not self.show_unused_addresses:
            return []

        rows = []
        tTree = self.tree
        subtree = IPtree.getSubtree(tTree, ip)
        nets = self.generateMatrixNets(ip)

        for net in nets:
            overlap = False
            for subnet in subtree.keys():
                if subnet.overlaps(net) == 1:
                    overlap = True
                    continue  # FIXME: break mebbe?

            if overlap or IPtree.search(subtree, net):
                continue
            else:
                rows.append([
                    self.Cell(
                        colspan=1,
                        color=None,
                        content='{0} {1}'.format(
                            Matrix.printDepth(depth),
                            _netlink(net))),
                    self.Cell(
                        colspan=self.num_columns,
                        color=None,
                        content='&nbsp;')
                ])
        return rows

    def _loadColor(self, percent, nettype):
        if nettype == 'static' or nettype == 'scope' or nettype == 'reserved':
            return self.color_configuration.extras.get('other')
        elif nettype == 'large':
            return self.color_configuration.extras.get('large')
        else:
            limits = self.color_configuration.limits.items()
            limits.sort(
                key=lambda x: x[0],
                reverse=True)
            for limit in limits:
                if percent >= int(limit[0]):
                    return limit[1]

    def _getColumnHeaders(self):
        msb = 8 - (self.end_net.prefixlen()-self.bits_in_matrix) % 8
        lsb = msb - self.bits_in_matrix
        if lsb <= 0:
            lsb = 1
        if msb <= 0:
            msb = 1
        return [str((2**lsb)*i) for i in range(0, msb)]

    def generateMatrixNets(self, supernet):
        """Generates all the matrix nets which belongs under ``supernet''."""
        matrix_prefixlen = self.end_net.prefixlen() - self.bits_in_matrix
        start_net = supernet.net().make_net(matrix_prefixlen)

        #hack, assumes matrix_prefixlen == 24
        max_address = supernet[-1]
        end_net = max_address.make_net(24)

        return netDiff(start_net, end_net)

    def _netsInRange(self, net1, net2, depth):
        rows = []
        if net1.prefixlen() == net2.prefixlen():
            diff = netDiff(net1, net2)
            if len(diff) > 1:
                for net in diff[1:]:
                    rows.append([
                        self.Cell(
                            colspan=1,
                            color=None,
                            content='{0} {1}'.format(
                                Matrix.printDepth(depth),
                                _netlink(net))),
                        self.Cell(
                            colspan=self.num_columns,
                            color=None,
                            content='&nbsp;')
                    ])
        return rows

    def __repr__(self):
        return "%s(%r, %r, %r, %r)" % (self.__class__.__name__,
                                       self.start_net,
                                       self.show_unused_addresses,
                                       self.end_net,
                                       self.bits_in_matrix)


def _supernetMatrixlink(ip):
    meta = metaIP.MetaIP(ip)
    return """
        <a href="/machinetracker/?prefixid={0}"
           title="{1}/{2}">
           ({3}%)</a>
    """.format(
        meta.prefixid,
        meta.active_ip_cnt,
        meta.max_ip_cnt,
        meta.usage_percent)


def _matrixlink(nybble, ip):
    meta = metaIP.MetaIP(ip)
    return """
        <a href="/report/prefix?prefixid={0}">
            .{1}/{2}
        </a>
        <a href="/machinetracker/?prefixid={3}"
           title="{4}/{5}">
            ({6}%)
        </a>
    """.format(
        meta.prefixid,
        nybble,
        ip.prefixlen(),
        meta.prefixid,
        meta.active_ip_cnt,
        meta.max_ip_cnt,
        meta.usage_percent)


def _netlink(ip, append_term_and_prefix=False):
    nip = metaIP.MetaIP(ip).getTreeNet()
    if append_term_and_prefix:
        return """
            <a href="/report/matrix?scope={0}">
                {1}
            </a>""".format(ip.strNormal(), ip.strNormal())
    else:
        return """
            <a href="/report/prefix?netaddr={0}.%&op_netaddr=like">
                {1}
            </a>""".format(nip, nip)

