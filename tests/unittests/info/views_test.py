#
# Copyright (C) 2012 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

"""Unittests for web/info"""

import unittest

from nav.web.info.searchproviders import SearchResult, SearchProvider
from nav.web.info.views import has_results, has_only_one_result
from nav.web.info.forms import SearchForm


class MockProvider(SearchProvider):
    def fetch_results(self):
        return []


class ViewsTest(unittest.TestCase):
    """Testclass for helperfunctions in info's views module"""

    def setUp(self):
        """Test setup"""

        searchresult = SearchResult('test', None)
        self.searchprovider0 = MockProvider()
        self.searchprovider1 = MockProvider()
        self.searchprovider2 = MockProvider()

        self.searchprovider1.results.append(searchresult)
        self.searchprovider2.results.extend([searchresult, searchresult])

    def test_has_results(self):
        """Tests for the has_results function"""

        providers = [self.searchprovider0, self.searchprovider1, self.searchprovider2]

        self.assertTrue(has_results(providers))
        self.assertTrue(len(has_results(providers)) == 2)
        self.assertFalse(has_results([self.searchprovider0]))

    def test_has_only_one_result(self):
        """Tests for the has_only_one_result function"""

        self.assertFalse(has_only_one_result([self.searchprovider0]))

        self.assertTrue(
            has_only_one_result([self.searchprovider0, self.searchprovider1])
        )

        self.assertFalse(
            has_only_one_result(
                [self.searchprovider0, self.searchprovider1, self.searchprovider2]
            )
        )

        self.assertFalse(has_only_one_result([self.searchprovider2]))

    def test_search_form(self):
        form = SearchForm({'query': 'Test '})
        form.is_valid()
        self.assertEqual(form.cleaned_data['query'], 'Test')
