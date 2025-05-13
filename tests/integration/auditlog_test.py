from django.test import TestCase

from nav.models.arnold import Justification

from nav.auditlog import find_modelname
from nav.auditlog.models import LogEntry
from nav.auditlog.utils import get_auditlog_entries


class AuditlogModelTestCase(TestCase):
    def setUp(self):
        # This specific model is used because it is very simple
        self.justification = Justification.objects.create(name='testarossa')

    def test_str(self):
        LogEntry.add_log_entry(self.justification, 'str test', 'foo')
        log_entry = LogEntry.objects.filter(verb='str test').get()
        self.assertEqual(str(log_entry), 'foo')
        log_entry.delete()

    def test_add_log_entry_bad_template(self):
        with self.assertLogs(level='ERROR') as log:
            LogEntry.add_log_entry(
                self.justification, 'bad template test', 'this is a {bad} template'
            )
            log_entry = LogEntry.objects.filter(verb='bad template test').get()
            self.assertEqual(
                log_entry.summary, 'Error creating summary - see error log'
            )
            log_entry.delete()
            self.assertEqual(len(log.output), 1)
            self.assertEqual(len(log.records), 1)
            self.assertIn('KeyError when creating summary:', log.output[0])

    def test_add_log_entry_actor_only(self):
        LogEntry.add_log_entry(
            self.justification, 'actor test', 'actor "{actor}" only is tested'
        )
        log_entry = LogEntry.objects.filter(verb='actor test').get()
        self.assertEqual(log_entry.summary, 'actor "testarossa" only is tested')
        log_entry.delete()

    def test_add_create_entry(self):
        LogEntry.add_create_entry(self.justification, self.justification)
        log_entry = LogEntry.objects.filter(verb='create-justification').get()
        self.assertEqual(log_entry.summary, 'testarossa created testarossa')
        log_entry.delete()

    def test_add_delete_entry(self):
        LogEntry.add_delete_entry(self.justification, self.justification)
        log_entry = LogEntry.objects.filter(verb='delete-justification').get()
        self.assertEqual(log_entry.summary, 'testarossa deleted testarossa')
        log_entry.delete()

    def test_compare_objects(self):
        justification_1 = Justification.objects.create(
            name='ferrari', description='Psst!'
        )
        justification_2 = Justification.objects.create(name='lambo', description='Hush')
        LogEntry.compare_objects(
            self.justification,
            justification_1,
            justification_2,
            ('name', 'description'),
            ('description',),
        )
        log_entry = LogEntry.objects.filter(verb='edit-justification-name').get()
        self.assertEqual(
            log_entry.summary,
            'testarossa edited lambo: name changed from \'ferrari\' to \'lambo\'',
        )
        log_entry.delete()
        log_entry = LogEntry.objects.filter(verb='edit-justification-description').get()
        self.assertEqual(
            log_entry.summary, 'testarossa edited lambo: description changed'
        )
        log_entry.delete()

    def test_addLog_entry_before(self):
        LogEntry.add_log_entry(self.justification, 'actor test', 'blbl', before=1)
        log_entry = LogEntry.objects.filter(verb='actor test').get()
        self.assertEqual(log_entry.before, '1')
        log_entry.delete()

    def test_find_name(self):
        name = find_modelname(self.justification)
        self.assertEqual(name, 'blocked_reason')


class AuditlogUtilsTestCase(TestCase):
    def setUp(self):
        # This specific model is used because it is very simple
        self.justification = Justification.objects.create(name='testarossa')

    def test_get_auditlog_entries(self):
        modelname = 'blocked_reason'  # Justification's db_table
        justification_1 = Justification.objects.create(name='j1')
        justification_2 = Justification.objects.create(name='j2')
        LogEntry.add_create_entry(self.justification, justification_1)
        LogEntry.add_log_entry(
            self.justification,
            'greet',
            '{actor} greets {object}',
            object=justification_2,
            subsystem="hello",
        )
        LogEntry.add_log_entry(
            self.justification,
            'deliver',
            '{actor} delivers {object} to {target}',
            object=justification_1,
            target=justification_2,
            subsystem='delivery',
        )
        entries = get_auditlog_entries(modelname=modelname)
        self.assertEqual(entries.count(), 3)
        entries = get_auditlog_entries(modelname=modelname, subsystem='hello')
        self.assertEqual(entries.count(), 1)
        entries = get_auditlog_entries(modelname=modelname, pks=[justification_1.pk])
        self.assertEqual(entries.count(), 2)
