"""Tests for the messages form"""

from unittest.mock import MagicMock, patch

from nav.models.msgmaint import Message
from nav.web.messages.forms import MessageForm


class TestMessageForm:
    def test_when_instance_is_unsaved_then_it_should_not_raise(self):
        form = MessageForm(instance=Message())
        assert form.initial['maintenance_tasks'] == []

    @patch('nav.web.messages.forms.MessageToMaintenanceTask.objects.filter')
    @patch('django.forms.models.model_to_dict', return_value={})
    def test_when_instance_is_saved_then_it_should_fetch_maintenance_tasks(
        self, _mock_model_to_dict, mock_filter
    ):
        task = MagicMock()
        task.maintenance_task.pk = 42
        mock_filter.return_value.all.return_value = [task]

        message = Message()
        message.pk = 1

        form = MessageForm(instance=message)
        assert form.initial['maintenance_tasks'] == [42]
        mock_filter.assert_called_once_with(message=message)
