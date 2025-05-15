#
# Copyright (C) 2023 Sikt
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
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Defines types and enumerations for SNMP communication parameters"""

from enum import Enum


class SecurityLevel(Enum):
    """SNMPv3 security levels"""

    NO_AUTH_NO_PRIV = "noAuthNoPriv"
    AUTH_NO_PRIV = "authNoPriv"
    AUTH_PRIV = "authPriv"


class AuthenticationProtocol(Enum):
    """SNMPv3 authentication protocols supported by NET-SNMP"""

    MD5 = "MD5"
    SHA = "SHA"
    SHA512 = "SHA-512"
    SHA384 = "SHA-384"
    SHA256 = "SHA-256"
    SHA224 = "SHA-224"


class PrivacyProtocol(Enum):
    """SNMPv3 privacy protocols supported by NET-SNMP"""

    DES = "DES"
    AES = "AES"
