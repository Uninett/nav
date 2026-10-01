from unittest.mock import Mock, patch

import pytest

from nav.models.rack import Rack
from nav.web.navlets.env_rack import EnvironmentRackWidget


@pytest.fixture
def mock_rack_get():
    with patch.object(Rack, 'objects') as objects:
        objects.get = Mock()
        yield objects.get


class TestEnvironmentRackWidgetView:
    def test_given_existing_rack_when_viewing_then_rack_should_be_in_context(
        self, mock_rack_get
    ):
        rack = Mock(spec=Rack)
        mock_rack_get.return_value = rack

        context = get_view_context({'rack': 43})

        mock_rack_get.assert_called_once_with(pk=43)
        assert context['rack'] is rack
        assert context['rackid'] == 43
        assert 'doesnotexist' not in context

    def test_given_deleted_rack_when_viewing_then_doesnotexist_should_be_set(
        self, mock_rack_get
    ):
        mock_rack_get.side_effect = Rack.DoesNotExist

        context = get_view_context({'rack': 43})

        assert context['doesnotexist'] == 43
        assert 'rack' not in context

    def test_given_invalid_rack_id_when_viewing_then_doesnotexist_should_be_set(
        self, mock_rack_get
    ):
        mock_rack_get.side_effect = ValueError

        context = get_view_context({'rack': 'invalid'})

        assert context['doesnotexist'] == 'invalid'
        assert 'rack' not in context

    def test_given_no_rack_preference_when_viewing_then_it_should_not_look_up_rack(
        self, mock_rack_get
    ):
        context = get_view_context({})

        mock_rack_get.assert_not_called()
        assert context['rackid'] is None
        assert 'rack' not in context
        assert 'doesnotexist' not in context

    def test_given_refresh_interval_preference_when_viewing_then_it_should_be_used(
        self, mock_rack_get
    ):
        context = get_view_context({'refresh_interval': 30000})

        assert context['refresh_interval'] == 30000


def get_view_context(preferences):
    widget = EnvironmentRackWidget(preferences=preferences)
    return widget.get_context_data_view({})
