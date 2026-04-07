#
# Copyright (C) 2026 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
from urllib.parse import urlparse, parse_qs

from django.test import Client
from django.urls import reverse


class TestLoginRedirect:
    def test_when_unauthenticated_user_accesses_protected_page_then_login_should_redirect_back(  # noqa: E501
        self, db, admin_username, admin_password
    ):
        client = Client()
        protected_url = '/ipdevinfo/'

        # Unauthenticated request to a protected page should redirect to login
        response = client.get(protected_url)
        assert response.status_code == 302
        redirect_url = response['Location']

        parsed = urlparse(redirect_url)
        query = parse_qs(parsed.query)

        # The redirect should use 'next', not 'origin'
        assert 'next' in query, f"Expected 'next' in query params, got: {parsed.query}"
        assert 'origin' not in query
        assert query['next'][0] == protected_url

        # Log in via the redirect URL
        login_url = reverse('account_login')
        response = client.post(
            login_url,
            {
                'login': admin_username,
                'password': admin_password,
                'next': query['next'][0],
            },
        )
        # allauth redirects to the 'next' URL after successful login
        assert response.status_code == 302
        assert response['Location'] == protected_url
