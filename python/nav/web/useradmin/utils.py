#
# Copyright (C) 2008, 2011, 2020 Uninett AS
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

from django.conf import settings
from django.db.models import Exists, OuterRef

from allauth.mfa.models import Authenticator


def is_2fa_globally_enabled():
    """Convenience method to check if 2fa is globally enabled"""
    return bool(getattr(settings, 'MFA_SUPPORTED_TYPES', []))


def annotate_accounts_with_2fa_status(queryset):
    """
    If 2fa is globally activated,
    annotate a provided account queryset with an activated_2fa boolean field.
    """
    if not is_2fa_globally_enabled():
        return queryset

    return queryset.annotate(
        activated_2fa=Exists(
            Authenticator.objects.filter(
                user=OuterRef('pk'),
                type__in=[Authenticator.Type.TOTP, Authenticator.Type.WEBAUTHN],
            )
        )
    )
