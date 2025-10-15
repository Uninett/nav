# -*- coding: utf-8 -*-

import os

import pytest
from django.test import RequestFactory
from django.urls import reverse
from django.utils.encoding import smart_str
from mock import MagicMock

from nav.web.auth.utils import set_account
from nav.web.info.images.utils import save_thumbnail
from nav.web.info.room.views import create_csv
from nav.web.info.searchproviders import SearchProvider

#########
# Tests #
#########


def test_search_for_nonascii_characters_should_not_crash(client):
    url = reverse('info-search') + '?query=æøå'
    response = client.get(url)
    assert response.status_code == 200


def test_failing_searchprovider_should_not_crash_search_page(
    client, failing_searchprovider
):
    url = reverse('info-search') + '?query=Da%20Truf'
    response = client.get(url)
    assert response.status_code == 200


def test_failures_should_be_mentioned_in_search_page(client, failing_searchprovider):
    url = reverse('info-search') + '?query=Da%20Truf'
    response = client.get(url)
    assert failing_searchprovider in response.content.decode('utf-8')


def test_room_csv_download_should_not_produce_bytestring_representations(admin_account):
    factory = RequestFactory()
    request = factory.post(
        reverse("room-csv"), data={"roomid": "myroom", "rows": "one;two;three\n"}
    )
    request.session = MagicMock()
    set_account(request, admin_account, cycle_session_id=False)

    response = create_csv(request)  # type: django.http.response.HttpResponse
    assert not response.content.startswith(b"b'")


def test_save_thumbnail_should_produce_a_file(tmpdir):
    """This is more or less a regression test for the third party library Pillow"""
    image = "closet.jpg"
    save_thumbnail(
        imagename=image,
        imagedirectory="tests/functional",
        thumb_dir=tmpdir,
    )
    assert os.path.exists(os.path.join(tmpdir, image))


class TestImageUploadHeader:
    def test_when_rendering_location_image_upload_then_include_location_id(
        self, client
    ):
        url = reverse('location-info-upload', args=['mylocation'])
        response = client.get(url)
        assert 'Images for &laquo;mylocation&raquo;' in smart_str(response.content)

    def test_when_rendering_room_image_upload_then_include_room_id(self, client):
        url = reverse('room-info-upload', args=['myroom'])
        response = client.get(url)
        assert 'Images for &laquo;myroom&raquo;' in smart_str(response.content)

    def test_should_render_image_help_modal(self, client):
        url = reverse('info-image-help-modal')
        response = client.get(url)
        assert 'id="image-help"' in smart_str(response.content)


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

    provider = '{module}.{klass}'.format(
        module=__name__, klass=FailingSearchProvider.__name__
    )
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
