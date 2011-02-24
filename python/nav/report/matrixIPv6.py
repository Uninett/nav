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
import nav.path
from nav.report import utils, IPtools, metaIP
from nav.report.matrix import Matrix
from nav.report.colorconfig import ColorConfig
from nav.web.templates.MatrixIPv6Template import MatrixIPv6Template

configfile = os.path.join(nav.path.sysconfdir,"report/matrix.conf")


class MatrixIPv6(Matrix):
    """This class serves as an interface for the prefix matrix.

    Call getTemplateResponse() to get the template response."""

    def __init__(self, start_net, end_net=None):
        Matrix.__init__(self, start_net, end_net=end_net, bits_in_matrix=4)
        self.column_headings = ["%X" % i for i in range(0, 16)]

    def getTemplateResponse(self):
        template = MatrixIPv6Template()
        template.path = [("Home", "/"), ("Report", "/report/"),
                         ("Prefix Matrix", False)]

        #functions and classes
        template.sort_nets_by_address = getattr(IPtools,"sort_nets_by_address")
        template.MetaIP = getattr(metaIP,"MetaIP")
        template.getLastbitsIpMap = getattr(IPtools,"getLastbitsIpMap")
        template.sub = getattr(utils,"sub")
        template.stringDotJoin = getattr(string,"join")
        template.isIntermediateNets = getattr(IPtools,"isIntermediateNets")

        #variables
        template.start_net = self.start_net
        template.end_net = self.end_net
        template.tree_nets = self.tree_nets
        template.matrix_nets = self.matrix_nets
        template.column_headings = self.column_headings
        template.bits_in_matrix = self.bits_in_matrix
        template.color_configuration = ColorConfig(configfile)
        return template.respond()
