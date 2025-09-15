from unittest.mock import patch
from django.test import RequestFactory
from django.http import HttpResponse

from nav.web.modals import (
    DEFAULT_MODAL_ID,
    DEFAULT_MODAL_SIZE,
    render_modal,
    resolve_modal,
    render_modal_alert,
)


class TestModalUtilities:
    """Test case for modal utility functions"""

    def setup_method(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('/')

    @patch('nav.web.modals.render')
    def test_should_render_modal_with_defaults(self, mock_render):
        mock_render.return_value = HttpResponse('modal content')
        result = render_modal(self.request, 'test_template.html')

        expected_context = {
            'modal_id': DEFAULT_MODAL_ID,
            'content_template': 'test_template.html',
            'modal_size': DEFAULT_MODAL_SIZE,
            'show_close_button': True,
            'close_on_outside_click': True,
        }

        mock_render.assert_called_once_with(
            self.request, 'modals/_nav_modal.html', expected_context
        )
        assert result == mock_render.return_value

    @patch('nav.web.modals.render')
    def test_should_render_modal_with_custom_context(self, mock_render):
        mock_render.return_value = HttpResponse('modal content')
        template_name = 'custom_template.html'
        context = {'netboxid': '123'}
        modal_id = 'custom-modal'

        render_modal(self.request, template_name, context, modal_id)

        expected_context = {
            'modal_id': modal_id,
            'content_template': template_name,
            'modal_size': DEFAULT_MODAL_SIZE,
            'show_close_button': True,
            'close_on_outside_click': True,
            'netboxid': '123',
        }

        mock_render.assert_called_once_with(
            self.request, 'modals/_nav_modal.html', expected_context
        )

    @patch('nav.web.modals.render')
    def test_should_render_modal_with_custom_size(self, mock_render):
        """Test render_modal with custom size"""
        mock_render.return_value = HttpResponse('modal content')
        template_name = 'size_template.html'
        modal_size = 'large'

        render_modal(self.request, template_name, size=modal_size)

        expected_context = {
            'modal_id': DEFAULT_MODAL_ID,
            'content_template': template_name,
            'modal_size': modal_size,
            'show_close_button': True,
            'close_on_outside_click': True,
        }

        mock_render.assert_called_once_with(
            self.request, 'modals/_nav_modal.html', expected_context
        )

    @patch('nav.web.modals.render')
    def test_resolve_modal_with_defaults(self, mock_render):
        """Test resolve_modal with default parameters"""
        mock_render.return_value = HttpResponse('modal content')
        resolve_modal(self.request)

        expected_context = {
            'modal_id': DEFAULT_MODAL_ID,
            'content_template': None,
        }
        mock_render.assert_called_once_with(
            self.request, 'modals/_nav_modal_resolve.html', expected_context
        )

    @patch('nav.web.modals.render')
    def test_resolve_modal_with_custom_template(self, mock_render):
        """Test resolve_modal with template and context"""
        mock_render.return_value = HttpResponse('resolve content')
        template_name = 'resolve_template.html'
        context = {'success': True}
        modal_id = 'resolve-modal'

        resolve_modal(self.request, template_name, context, modal_id)

        expected_context = {
            'modal_id': modal_id,
            'content_template': template_name,
            'success': True,
        }
        mock_render.assert_called_once_with(
            self.request, 'modals/_nav_modal_resolve.html', expected_context
        )

    @patch('nav.web.modals.render')
    def test_render_modal_alert_custom_modal_id(self, mock_render):
        """Test render_modal_alert with custom modal_id"""
        mock_render.return_value = HttpResponse('alert content')
        message = 'Error occurred!'
        modal_id = 'error-alert'

        render_modal_alert(self.request, message, modal_id)

        expected_context = {'message': message, 'modal_id': modal_id}
        mock_render.assert_called_once_with(
            self.request, 'modals/_nav_modal_alert.html', expected_context
        )

    @patch('nav.web.modals.render')
    def test_should_render_modal_with_close_button_disabled(self, mock_render):
        """Test render_modal with close button disabled"""
        mock_render.return_value = HttpResponse('modal content')
        template_name = 'test_template.html'

        render_modal(self.request, template_name, show_close_button=False)

        expected_context = {
            'modal_id': DEFAULT_MODAL_ID,
            'content_template': template_name,
            'modal_size': DEFAULT_MODAL_SIZE,
            'show_close_button': False,
            'close_on_outside_click': True,
        }

        mock_render.assert_called_once_with(
            self.request, 'modals/_nav_modal.html', expected_context
        )

    @patch('nav.web.modals.render')
    def test_should_render_modal_with_outside_click_disabled(self, mock_render):
        """Test render_modal with outside click closing disabled"""
        mock_render.return_value = HttpResponse('modal content')
        template_name = 'test_template.html'

        render_modal(self.request, template_name, close_on_outside_click=False)

        expected_context = {
            'modal_id': DEFAULT_MODAL_ID,
            'content_template': template_name,
            'modal_size': DEFAULT_MODAL_SIZE,
            'show_close_button': True,
            'close_on_outside_click': False,
        }

        mock_render.assert_called_once_with(
            self.request, 'modals/_nav_modal.html', expected_context
        )

    @patch('nav.web.modals.render')
    def test_should_render_modal_with_both_close_options_disabled(self, mock_render):
        """Test render_modal with both close options disabled for manual control"""
        mock_render.return_value = HttpResponse('modal content')
        template_name = 'test_template.html'

        render_modal(
            self.request,
            template_name,
            show_close_button=False,
            close_on_outside_click=False,
        )

        expected_context = {
            'modal_id': DEFAULT_MODAL_ID,
            'content_template': template_name,
            'modal_size': DEFAULT_MODAL_SIZE,
            'show_close_button': False,
            'close_on_outside_click': False,
        }

        mock_render.assert_called_once_with(
            self.request, 'modals/_nav_modal.html', expected_context
        )
