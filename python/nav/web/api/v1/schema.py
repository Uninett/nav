#
# Copyright (C) 2026 Sikt
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
"""OpenAPI schema helpers for the NAV REST API.

drf-spectacular cannot introspect NAV's custom token authentication or the
JWT authentication provided by ``oidc_auth``. The extensions below register
the corresponding OpenAPI security schemes so they appear in the generated
specification. Importing this module is enough to register them, as
drf-spectacular discovers extensions by subclass registration.
"""

from drf_spectacular.extensions import OpenApiAuthenticationExtension


class APITokenScheme(OpenApiAuthenticationExtension):
    """Security scheme for NAV's API token authentication."""

    target_class = 'nav.web.api.v1.auth.APIAuthentication'
    name = 'apiToken'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': (
                'NAV API token. Send as ``Authorization: Token <your-token>``.'
            ),
        }


class JWTScheme(OpenApiAuthenticationExtension):
    """Security scheme for NAV's JSON Web Token authentication."""

    target_class = 'oidc_auth.authentication.JSONWebTokenAuthentication'
    name = 'jwtAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
        }
