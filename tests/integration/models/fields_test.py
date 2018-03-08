# -*- coding: utf-8 -*-

from unittest import TestCase
from datetime import datetime as dt

from django.db import models

from nav.models.msgmaint import MaintenanceComponent, MaintenanceTask
from nav.models.event import Subsystem
from nav.models.logger import ErrorError
from nav.models.fields import LegacyGenericForeignKey


class LegacyGenericForeignKeyTest(TestCase):

    def setUp(self):

        self.task = MaintenanceTask(
            start_time=dt(2018,1,1),
            end_time=dt(2018,12,1),
            description='blbl',
            author='barbar',
            state=MaintenanceTask.STATE_ACTIVE,
        )
        self.ee1 = ErrorError(message='a message')
        self.ee1.save()
        self.task.save()

    def test_save_model_with_lgfk(self):
        mc = MaintenanceComponent(
            maintenance_task=self.task,
            key=self.ee1._meta.db_table,
            value=str(self.ee1.id),
        )
        mc.save()
        self.assertEqual(mc.key, self.ee1._meta.db_table)
        self.assertEqual(mc.value, str(self.ee1.id))

    def test_set_get_via_lgfk(self):
        mc = MaintenanceComponent(
            maintenance_task=self.task,
            component=elf.ee1,
        )
        mc.save()
        self.assertEqual(mc.component, self.ee1)
