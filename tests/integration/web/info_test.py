# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
from django.urls import reverse

from nav.web.info.searchproviders import SearchProvider

#########
# Tests #
#########


def test_search_for_nonascii_characters_should_not_crash(client):
    url = reverse('info-search') + '?query=æøå'
    response = client.get(url)
    assert response.status_code == 200


def test_failing_searchprovider_should_not_crash_search_page(
        client, failing_searchprovider):
    url = reverse('info-search') + '?query=Da%20Truf'
    response = client.get(url)
    assert response.status_code == 200


def test_failures_should_be_mentioned_in_search_page(client,
                                                     failing_searchprovider):
    url = reverse('info-search') + '?query=Da%20Truf'
    response = client.get(url)
    assert failing_searchprovider in response.content.decode('utf-8')


############
# Fixtures #
############


@pytest.fixture
def failing_searchprovider():
    """
    Inserts (into NAV's list of search providers to use) a provider that
    raises an exception.
    """
    from django.conf import settings
    provider = '{module}.{klass}'.format(module=__name__,
                                         klass=FailingSearchProvider.__name__)
    if provider not in settings.SEARCHPROVIDERS:
        settings.SEARCHPROVIDERS.append(provider)

    yield provider

    if provider in settings.SEARCHPROVIDERS:
        index = settings.SEARCHPROVIDERS.index(provider)
        del settings.SEARCHPROVIDERS[index]


class FailingSearchProvider(SearchProvider):
    """A search provider that only raises exceptions"""
    def fetch_results(self):
        raise Exception("Riddikulus")
