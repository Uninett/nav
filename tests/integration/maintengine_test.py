from datetime import datetime, timedelta

import pytest

from nav import maintengine
from nav.models.msgmaint import MaintenanceTask, MaintenanceComponent


class TestCancelTasksWithoutComponents:
    def test_it_should_cancel_active_empty_tasks(self, empty_task):
        assert empty_task.state == MaintenanceTask.STATE_ACTIVE
        maintengine.cancel_tasks_without_components()
        empty_task.refresh_from_db()
        assert empty_task.state == MaintenanceTask.STATE_CANCELED

    def test_it_should_not_cancel_scheduled_empty_tasks(self, scheduled_empty_task):
        assert scheduled_empty_task.state == MaintenanceTask.STATE_SCHEDULED
        maintengine.cancel_tasks_without_components()
        scheduled_empty_task.refresh_from_db()
        assert scheduled_empty_task.state == MaintenanceTask.STATE_SCHEDULED

    def test_it_should_not_cancel_nonempty_tasks(self, half_empty_task):
        assert half_empty_task.state == MaintenanceTask.STATE_ACTIVE
        maintengine.cancel_tasks_without_components()
        half_empty_task.refresh_from_db()
        assert half_empty_task.state == MaintenanceTask.STATE_ACTIVE


@pytest.fixture
def empty_task(db):
    task = MaintenanceTask(
        start_time=datetime.now() - timedelta(minutes=30),
        end_time=datetime.now() + timedelta(minutes=30),
        description="Test task",
        state=MaintenanceTask.STATE_ACTIVE,
    )
    task.save()
    component = MaintenanceComponent(
        maintenance_task=task,
        key="netbox",
        value=99999,
    )
    component.save()

    yield task


@pytest.fixture
def scheduled_empty_task(empty_task):
    empty_task.state = MaintenanceTask.STATE_SCHEDULED
    empty_task.start_time = datetime.now() + timedelta(minutes=30)
    empty_task.end_time = datetime.now() + timedelta(minutes=60)
    empty_task.save()
    yield empty_task


@pytest.fixture
def half_empty_task(empty_task, localhost):
    component = MaintenanceComponent(maintenance_task=empty_task, component=localhost)
    component.save()
    yield empty_task
