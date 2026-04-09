"""Integration tests for the messages form"""

from datetime import datetime, timedelta

import pytest

from nav.models.msgmaint import (
    MaintenanceTask,
    Message,
    MessageToMaintenanceTask,
)
from nav.web.messages.forms import MessageForm


class TestMessageForm:
    def test_when_instance_is_unsaved_then_it_should_not_raise(self, db):
        form = MessageForm(instance=Message())
        assert form.initial['maintenance_tasks'] == []

    def test_when_instance_is_saved_then_it_should_fetch_maintenance_tasks(
        self, message, maintenance_task
    ):
        MessageToMaintenanceTask(
            message=message, maintenance_task=maintenance_task
        ).save()

        form = MessageForm(instance=message)
        assert form.initial['maintenance_tasks'] == [maintenance_task.pk]


@pytest.fixture
def message(db):
    message = Message(
        title="Test message",
        description="A test message",
        publish_start=datetime.now(),
        publish_end=datetime.now() + timedelta(days=7),
        author="testuser",
        last_changed=datetime.now(),
    )
    message.save()
    return message


@pytest.fixture
def maintenance_task(db):
    task = MaintenanceTask(
        start_time=datetime.now(),
        end_time=datetime.now() + timedelta(hours=1),
        description="Test task",
        author="testuser",
        state=MaintenanceTask.STATE_SCHEDULED,
    )
    task.save()
    return task
