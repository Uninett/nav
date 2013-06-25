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
import math

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
        self.show_unused_addresses = show_unused_addresses
        self.color_configuration = ColorConfig(configfile)

    @property
    def template(self):
        return 'report/matrixIPv4.html'

    def render(self):

        nodes = IPtools.sort_nets_by_address(self.tree_nets.keys())
        self.nodes = [
            (net, self._write_subnets(self.tree_nets[net], 1))
            for net in nodes
        ]

    def _write_subnets(self, net, depth):

        nodes = IPtools.sort_nets_by_address(net.keys())
        lastnet = None
        html = []

        for subnet in nodes:
            if lastnet is None:
                lastnet = subnet

            if subnet in self.matrix_nets:
                if self.show_unused_addresses:
                    html.extend(
                        _printNetsInRange(
                            lastnet,
                            subnet,
                            depth,
                            len(self.column_headings)))
                lastnet = subnet
                tr = '<tr><td>{0} {1}</td>'.format(
                    _printDepth(depth),
                    _netlink(subnet))
                html.append(tr)

                host_nybbles_map = IPtools.getLastbitsIpMap(
                    self.matrix_nets[subnet].keys())
                next_header_idx = -1

                if self.has_too_small_nets(subnet):
                    td = """
                        <td colspan="{0}"
                            style="background-color:{1};
                                   text-align:center;">
                                Too many small nets</td>
                    """.format(
                        len(self.column_headings),
                        self._loadColor(0, 'large'))

                elif host_nybbles_map is None:
                # i.e. there exist a net with no
                # subnets <==> net spans whole row
                    ip = IPy.IP(subnet)
                    meta = metaIP.MetaIP(ip)
                    td = """
                        <td colspan="{0}"
                            style="background-color:{1};
                                  text-align:center;">
                            {2}</td>
                    """.format(
                        len(self.column_headings),
                        self._loadColor(meta.usage_percent, meta.nettype),
                        _matrixlink(0, ip))

                else:
                # The net exists and have subnets
                    td = ''
                    for i in self.column_headings:
                        if self.column_headings.index(i) < next_header_idx:
                            continue

                        i = i.lower()
                        if i in host_nybbles_map:
                            ip = host_nybbles_map[i]
                            meta = metaIP.MetaIP(ip)
                            td += """
                                <td class="gnu" colspan="{0}"
                                    style="background-color:{1};
                                          text-align:center;">
                                    {2}</td>
                            """.format(
                                _colspan(ip, self.end_net),
                                self._loadColor(meta.usage_percent, meta.nettype),
                                _matrixlink(i, ip))
                            next_header_idx = (self.column_headings.index(i.upper())
                                               + int(_colspan(ip, self.end_net)))
                        else:
                            td += '<td colspan="1">&nbsp;</td>'
                html.append(td)
                html.append('</tr>')
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
                    html.extend(
                        _printNetsInRange(
                            mnets[-1],
                            subnet_extended,
                            depth))
                lastnet = subnet
                meta = metaIP.MetaIP(subnet)
                tr = """
                    <tr>
                        <td>{0} {1}</td>
                        <td colspan="{2}"
                            style="background-color:{3};
                                  text-align:center;">
                            {4}
                        </td>
                    </tr>
                """.format(
                    _printDepth(depth),
                    _netlink(subnet, append_term_and_prefix=True),
                    len(self.column_headings),
                    self._loadColor(meta.usage_percent, meta.nettype),
                    _supernetMatrixlink(subnet))
                html.append(tr)
                html.extend(self._write_subnets(net[subnet], depth + 1))
                html.extend(self._writeRemainingBlankNets(subnet, depth + 1))
        return html

    def _writeRemainingBlankNets(self, ip, depth):
        if not self.show_unused_addresses:
            return []

        html = []
        tTree = self.tree
        subtree = IPtree.getSubtree(tTree, ip)
        matrix_net_prefixlen = (self.matrix_nets and
                                self.matrix_nets.keys()[0].prefixlen() or
                                24)
        nets = self.generateMatrixNets(ip)

        for net in nets:
            overlap = False
            for subnet in subtree.keys():
                if subnet.overlaps(net) == 1:
                    overlap = True
                    continue

            if overlap or IPtree.search(subtree, net):
                continue
            else:
                tr = """
                    <tr>
                        <td>{0} {1}</td>
                        <td colspan="{2}">&nbsp;</td>
                    </tr>
                """.format(
                    _printDepth(depth),
                    _netlink(net),
                    len(self.column_headings))
                html.append(tr)
        return html

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


def _printNetsInRange(net1, net2, depth, columns):
    html = []
    if net1.prefixlen() == net2.prefixlen():
        diff = netDiff(net1, net2)
        if len(diff) > 1:
            for net in diff[1:]:
                tr = """
                    <tr>
                        <td>{0} {1}</td>
                        <td colspan="{2}">&nbsp;</td>
                    </tr>
                """.format(_printDepth(depth), _netlink(net), columns)
                html.append(tr)
    return html


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


def _colspan(ip, end_net):
    return int(math.pow(2, end_net.prefixlen() - ip.prefixlen()))


def _printDepth(depth):
    space = '&nbsp;'
    space *= depth
    return space
