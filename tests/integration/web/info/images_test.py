"""Tests for the room/location image management views"""

import errno

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from nav.models.images import Image
from nav.models.manage import Room
from nav.models.profiles import Account

NONEXISTENT_IMAGE_ID = 999999


class TestDeleteImage:
    def test_when_image_does_not_exist_then_delete_image_should_return_200(
        self, client
    ):
        url = reverse('image-delete-image')
        response = client.post(url, {'id': NONEXISTENT_IMAGE_ID})
        assert response.status_code == 200

    def test_when_image_already_deleted_then_delete_image_should_say_so(self, client):
        url = reverse('image-delete-image')
        response = client.post(url, {'id': NONEXISTENT_IMAGE_ID})
        assert any('already deleted' in message for message in _messages(response))

    def test_when_id_is_missing_then_delete_image_should_return_400(self, client):
        url = reverse('image-delete-image')
        response = client.post(url, {})
        assert response.status_code == 400

    def test_when_id_is_not_a_number_then_delete_image_should_return_400(self, client):
        url = reverse('image-delete-image')
        response = client.post(url, {'id': 'not-a-number'})
        assert response.status_code == 400

    def test_when_image_exists_then_delete_image_should_remove_the_row(
        self, client, image
    ):
        url = reverse('image-delete-image')
        response = client.post(url, {'id': image.id})
        assert response.status_code == 200
        assert not Image.objects.filter(pk=image.id).exists()

    def test_when_file_already_gone_then_delete_image_should_report_success(
        self, client, image
    ):
        # The fixture image has no backing file on disk, so this exercises the
        # swallowed-ENOENT path; the success message must still be reported.
        url = reverse('image-delete-image')
        response = client.post(url, {'id': image.id})
        assert response.status_code == 200
        assert any('&raquo; deleted' in message for message in _messages(response))

    def test_when_file_deletion_fails_then_delete_image_should_return_500(
        self, client, image, monkeypatch, caplog
    ):
        def raise_permission_denied(*_args, **_kwargs):
            raise OSError(errno.EACCES, "Permission denied")

        monkeypatch.setattr(
            "nav.web.info.images.views.os.unlink", raise_permission_denied
        )
        url = reverse('image-delete-image')
        with caplog.at_level("ERROR", logger="nav.web.info.image"):
            response = client.post(url, {'id': image.id})
        assert response.status_code == 500
        assert "Could not delete image file" in caplog.text


class TestUpdateTitle:
    def test_when_image_does_not_exist_then_update_title_should_return_404(
        self, client
    ):
        url = reverse('image-update-title')
        response = client.post(url, {'id': NONEXISTENT_IMAGE_ID, 'title': 'irrelevant'})
        assert response.status_code == 404

    def test_when_id_is_missing_then_update_title_should_return_400(self, client):
        url = reverse('image-update-title')
        response = client.post(url, {'title': 'irrelevant'})
        assert response.status_code == 400


class TestUpdatePriority:
    def test_when_image_does_not_exist_then_update_priority_should_return_404(
        self, client
    ):
        url = reverse('image-update-priority')
        response = client.post(url, {str(NONEXISTENT_IMAGE_ID): '5'})
        assert response.status_code == 404

    def test_when_id_is_not_a_number_then_update_priority_should_return_400(
        self, client
    ):
        url = reverse('image-update-priority')
        response = client.post(url, {'not-a-number': '5'})
        assert response.status_code == 400


def _messages(response):
    """Return the rendered text of all messages attached to a response"""
    return [str(message) for message in get_messages(response.wsgi_request)]


@pytest.fixture
def image(db):
    """An Image row pointing at a room, with no backing file on disk"""
    room = Room.objects.get(pk='myroom')
    admin = Account.objects.get(id=Account.ADMIN_ACCOUNT)
    image = Image(
        room=room,
        uploader=admin,
        title='Test image',
        path='rooms/myroom',
        name='nonexistent.jpg',
        priority=0,
    )
    image.save()
    return image
