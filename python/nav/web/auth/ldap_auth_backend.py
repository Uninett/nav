#
# Copyright (C) 2025 Sikt
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
"""
LDAP authentication backend for Django's authentication framework, supporting the
specific legacy quirks of LDAP authentication in NAV.
"""

import typing

from nav.models.profiles import Account, AccountGroup

if typing.TYPE_CHECKING:
    from nav.web.auth.ldap import LDAPUser


def _handle_ldap_admin_status(ldap_user: "LDAPUser", nav_account: Account) -> None:
    is_admin = ldap_user.is_admin()
    # Only modify admin status if an entitlement is configured in webfront.conf
    if is_admin is not None:
        admin_group = AccountGroup.objects.get(id=AccountGroup.ADMIN_GROUP)
        if is_admin:
            nav_account.groups.add(admin_group)
        else:
            nav_account.groups.remove(admin_group)
