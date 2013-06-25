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
import math
import nav.path
from nav.report import IPtools, metaIP
from nav.report.matrix import Matrix
from nav.report.colorconfig import ColorConfig


configfile = os.path.join(nav.path.sysconfdir, "report/matrix.conf")


class MatrixIPv6(Matrix):
    """This class serves as an interface for the prefix matrix."""

    template = 'report/matrixIPv6.html'

    def __init__(self, start_net, end_net=None):
        Matrix.__init__(self, start_net, end_net=end_net, bits_in_matrix=4)
        self.column_headings = ["%X" % i for i in range(0, 16)]
        self.color_configuration = ColorConfig(configfile)

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
                # FIXME?: Why no IPv6 method?
                if IPtools.isIntermediateNets(lastnet, subnet):
                    html.append(_printBlankRow(self.column_headings))

                lastnet = subnet

                html.append('<tr>')
                td = '<td>' + _printDepth(depth)
                td += _netlink(subnet) + '</td>'
                html.append(td)

                host_nybbles_map = IPtools.getLastbitsIpMap(
                    self.matrix_nets[subnet].keys())
                next_header_idx = -1
                for i in self.column_headings:
                    if self.column_headings.index(i) < next_header_idx:
                        continue

                    i = i.lower()
                    if i in host_nybbles_map:
                        meta = metaIP.MetaIP(host_nybbles_map[i])
                        ip = host_nybbles_map[i]
                        td = """<td colspan="{0}"
                                    style="background-color:{1};
                                    text-align:center;">
                                    {2}
                            </td>""".format(_colspan(ip, self.end_net), meta.ipv6_color, _matrixlink(i, ip))
                        next_header_idx = self.column_headings.index(
                            i.upper()) + int(_colspan(ip, self.end_net))
                    else:
                        td = '<td colspan="1">&nbsp;</td>'
                    html.append(td)
                html.append('</tr>')
            else:
                html.append(_printBlankRow())
                lastnet = subnet
                meta = metaIP.MetaIP(subnet)
                tr = """
                    <tr>
                        <td>{0}{1}</td>
                        <td colspan="{2}">&nbsp;</td>
                    </tr>
                """.format(
                    _printDepth(depth),
                    _netlink(subnet, True),
                    len(self.column_headings))
                html.append(tr)
                html.extend(self._write_subnets(net[subnet], depth + 1))
        return html


def _matrixlink(nybble, ip):
    meta = metaIP.MetaIP(ip)
    return """
            <a href="/report/prefix?prefixid={0}"
               title="Active IPs: {1}">
               {2}::/{3}
           </a>""".format(
        meta.prefixid,
        meta.active_ip_cnt,
        nybble,
        ip.prefixlen())


def _netlink(ip, append_term_and_prefix=False):

    nip = metaIP.MetaIP(ip).getTreeNet(leadingZeros=True)
    link = metaIP.MetaIP(ip).getTreeNet(leadingZeros=False)[:-1] + '_::'
    text = nip[:-1] + 'x'

    if append_term_and_prefix:
        return """
            <a class="monosp"
               href="/report/matrix?scope={0}::/{1}">
               {2}::/{3}
            </a>""".format(nip, ip.prefixlen(), nip, ip.prefixlen())
    else:
        return """
            <a class="monosp"
               href="/report/prefix?netaddr={0}&op_netaddr=like">
               {1}
            </a>""".format(link, text)


def _colspan(ip, end_net):
    return int(math.pow(2, end_net.prefixlen() - ip.prefixlen()))


def _printDepth(depth):
    space = '&nbsp;'
    space *= depth
    return space


def _printBlankRow(column_headings):
    span = len(column_headings) + 1
    return '<tr><td class="blank" colspan="{0}"></td></tr>'.format(span)