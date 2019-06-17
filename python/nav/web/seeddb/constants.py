# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

from nav.models.manage import (
    Netbox,
    NetboxType,
    ManagementProfile,
    NetboxProfile,
    Room,
    Location,
    Organization,
    Device,
    Usage,
    Vendor,
    NetboxGroup,
    Vlan,
    Prefix,
)
from nav.models.service import Service

TITLE_DEFAULT = 'NAV - Seed Database'
NAVPATH_DEFAULT = [('Home', '/'), ('Seed DB', '/seeddb/')]
SEEDDB_EDITABLE_MODELS = (
    Netbox,
    NetboxType,
    ManagementProfile,
    NetboxProfile,
    Room,
    Location,
    Organization,
    Device,
    Usage,
    Vendor,
    NetboxGroup,
    Vlan,
    Prefix,
    Service,
)
