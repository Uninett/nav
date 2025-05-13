# -*- coding: utf-8 -*-

from datetime import datetime as dt


from nav.tests.cases import DjangoTransactionTestCase
from nav.models.msgmaint import MaintenanceComponent, MaintenanceTask
from nav.models.logger import ErrorError


class LegacyGenericForeignKeyTest(DjangoTransactionTestCase):
    def setUp(self):
        self.task = MaintenanceTask(
            start_time=dt(2018, 1, 1),
            end_time=dt(2018, 12, 1),
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

    def test_get_via_lgfk(self):
        mc = MaintenanceComponent(
            maintenance_task=self.task,
            key=self.ee1._meta.db_table,
            value=str(self.ee1.id),
        )
        mc.save()
        self.assertEqual(mc.component, self.ee1)

    def test_set_via_lgfk(self):
        ee2 = ErrorError(message='another message')
        ee2.save()
        mc = MaintenanceComponent(
            maintenance_task=self.task,
            key=self.ee1._meta.db_table,
            value=str(self.ee1.id),
        )
        mc.component = ee2
        mc.save()
        self.assertEqual(mc.component, ee2)
