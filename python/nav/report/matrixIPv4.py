# -*- coding: utf-8 -*-
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
import string
import IPy
from IPy import IP

import nav.path
from nav.web.templates.MatrixIPv4Template import MatrixIPv4Template
from nav.report import utils, IPtools, IPtree, metaIP
from nav.report.IPtools import netDiff
from nav.report.matrix import Matrix
from nav.report.colorconfig import ColorConfig

configfile = os.path.join(nav.path.sysconfdir,"report/matrix.conf")


class MatrixIPv4(Matrix):
    """This class serves as an interface for the prefix matrix.

    Call getTemplateResponse() to get the template response."""

    def __init__(self,start_net,show_unused_addresses,end_net=None,bits_in_matrix=3):
        Matrix.__init__(self,start_net,end_net=end_net,bits_in_matrix=bits_in_matrix)
        self.column_headings = self._getColumnHeaders()
        self.show_unused_addresses = show_unused_addresses

    def getTemplateResponse(self):
        template = MatrixIPv4Template()
        template.path = [("Home", "/"), ("Report", "/report/"), ("Prefix Matrix",False)]

        #functions and classes
        template.MetaIP = getattr(metaIP,"MetaIP")
        template.IP = getattr(IPy,"IP")
        template.getLastbitsIpMap = getattr(IPtools,"getLastbitsIpMap")
        template.sort_nets_by_address = getattr(IPtools,"sort_nets_by_address")
        template.sub = getattr(utils,"sub")
        template.netDiff = getattr(IPtools,"netDiff")
        template.has_too_small_nets = getattr(self,"has_too_small_nets")
        template.getSubtree = getattr(IPtree,"getSubtree")
        template.generateMatrixNets = getattr(self,"generateMatrixNets")
        template.search = getattr(IPtree,"search")

        #variables
        template.start_net = self.start_net
        template.end_net = self.end_net
        template.tree_nets = self.tree_nets
        template.matrix_nets = self.matrix_nets
        template.tree = self.tree
        template.column_headings = self.column_headings
        template.bits_in_matrix = self.bits_in_matrix
        template.color_configuration = ColorConfig(configfile)
        template.show_unused_addresses = self.show_unused_addresses
        return template.respond()

    def _getColumnHeaders(self):
        msb = 8 - (self.end_net.prefixlen()-self.bits_in_matrix) % 8
        lsb = msb - self.bits_in_matrix
        if lsb <= 0:
            lsb = 1
        if msb <= 0:
            msb = 1
        return [str((2**lsb)*i) for i in range(0,msb)]

    def generateMatrixNets(self,supernet):
        """Generates all the matrix nets which belongs under ``supernet''."""
        import math

        matrix_prefixlen = self.end_net.prefixlen() - self.bits_in_matrix
        maskdiff = matrix_prefixlen - supernet.prefixlen()
        number_of_nets = int(math.pow(2,maskdiff))
        start_net = IP("/".join([supernet.net().strNormal(),str(matrix_prefixlen)]))

        #hack, assumes matrix_prefixlen == 24
        end_net_third_octet = int(supernet.net().strNormal().split(".")[2])+number_of_nets
        end_net_ip = ".".join(supernet.net().strNormal().split(".")[:2] + [str(end_net_third_octet),"0"])
        end_net = IP("/".join([end_net_ip,"24"]))

        return netDiff(start_net,end_net)
