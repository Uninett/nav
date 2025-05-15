#
# Copyright (C) 2017 UNINETT
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""H3C specific PortAdmin SNMP handling"""

from nav import Snmp
from nav.oids import OID
from nav.portadmin.snmp.base import SNMPHandler, translate_protocol_errors
from nav.enterprise.ids import VENDOR_ID_H3C


class H3C(SNMPHandler):
    """HP Comware Platform Software handler"""

    VENDOR = VENDOR_ID_H3C

    hh3cCfgOperateType = '1.3.6.1.4.1.25506.2.4.1.2.4.1.2'
    hh3cCfgOperateRowStatus = '1.3.6.1.4.1.25506.2.4.1.2.4.1.9'

    def __init__(self, netbox, **kwargs):
        super(H3C, self).__init__(netbox, **kwargs)

    @translate_protocol_errors
    def commit_configuration(self):
        """Use hh3c-config-man-mib to save running config to startup"""

        running_to_startup = 1
        create_and_go = 4

        # Find the next available row for configuring and store it as a suffix
        active_rows = [
            OID(o[0])[-1] for o in self._bulkwalk(self.hh3cCfgOperateRowStatus)
        ]
        try:
            suffix = str(max(active_rows) + 1)
        except ValueError:
            suffix = '1'

        operation_type_oid = '.'.join([self.hh3cCfgOperateType, suffix])
        operation_status_oid = '.'.join([self.hh3cCfgOperateRowStatus, suffix])

        handle = self._get_read_write_handle()
        handle.multi_set(
            [
                Snmp.PDUVarbind(operation_type_oid, 'i', running_to_startup),
                Snmp.PDUVarbind(operation_status_oid, 'i', create_and_go),
            ]
        )
