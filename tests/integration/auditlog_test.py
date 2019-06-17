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
        LogEntry.add_log_entry(self.justification, u'str test', 'foo')
        l = LogEntry.objects.filter(verb='str test').get()
        self.assertEqual(str(l), 'foo')
        l.delete()

    def test_add_log_entry_bad_template(self):
        LogEntry.add_log_entry(self.justification, u'bad template test',
                                  u'this is a {bad} template')
        l = LogEntry.objects.filter(verb='bad template test').get()
        self.assertEqual(l.summary, u'Error creating summary - see error log')
        l.delete()
#         # When on python3:
#         with self.assertLogs(level='ERROR') as log:
#             # run body
#             self.assertEqual(len(log.output), 1)
#             self.assertEqual(len(log.records), 1)
#             self.assertIn('KeyError when creating summary:', log.output[0])

    def test_add_log_entry_actor_only(self):
        LogEntry.add_log_entry(self.justification, u'actor test',
                                  u'actor "{actor}" only is tested')
        l = LogEntry.objects.filter(verb='actor test').get()
        self.assertEqual(l.summary, u'actor "testarossa" only is tested')
        l.delete()

    def test_add_create_entry(self):
        LogEntry.add_create_entry(self.justification, self.justification)
        l = LogEntry.objects.filter(verb=u'create-justification').get()
        self.assertEqual(l.summary, u'testarossa created testarossa')
        l.delete()

    def test_add_delete_entry(self):
        LogEntry.add_delete_entry(self.justification, self.justification)
        l = LogEntry.objects.filter(verb=u'delete-justification').get()
        self.assertEqual(l.summary, u'testarossa deleted testarossa')
        l.delete()

    def test_compare_objects(self):
        j1 = Justification.objects.create(name='ferrari', description='Psst!')
        j2 = Justification.objects.create(name='lambo', description='Hush')
        LogEntry.compare_objects(self.justification, j1, j2,
                                 ('name', 'description'),
                                 ('description',)
        )
        l = LogEntry.objects.filter(verb=u'edit-justification-name').get()
        self.assertEqual(l.summary,
                         u'testarossa edited lambo: name changed'
                         u" from 'ferrari' to 'lambo'")
        l.delete()
        l = LogEntry.objects.filter(
            verb=u'edit-justification-description'
        ).get()
        self.assertEqual(l.summary,
                         u'testarossa edited lambo: description changed')
        l.delete()

    def test_addLog_entry_before(self):
        LogEntry.add_log_entry(self.justification, u'actor test',
                                  u'blbl', before=1)
        l = LogEntry.objects.filter(verb='actor test').get()
        self.assertEqual(l.before, u'1')
        l.delete()

    def test_find_name(self):
        name = find_modelname(self.justification)
        self.assertEqual(name, 'blocked_reason')


class AuditlogUtilsTestCase(TestCase):
    def setUp(self):
        # This specific model is used because it is very simple
        self.justification = Justification.objects.create(name='testarossa')


    def test_get_auditlog_entries(self):
        modelname = 'blocked_reason'  # Justification's db_table
        j1 = Justification.objects.create(name='j1')
        j2 = Justification.objects.create(name='j2')
        LogEntry.add_create_entry(self.justification, j1)
        LogEntry.add_log_entry(self.justification, u'greet',
                               u'{actor} greets {object}',
                               object=j2, subsystem="hello")
        LogEntry.add_log_entry(self.justification, u'deliver',
                               u'{actor} delivers {object} to {target}',
                               object=j1, target=j2, subsystem='delivery')
        entries = get_auditlog_entries(modelname=modelname)
        self.assertEqual(entries.count(), 3)
        entries = get_auditlog_entries(modelname=modelname, subsystem='hello')
        self.assertEqual(entries.count(), 1)
        entries = get_auditlog_entries(modelname=modelname, pks=[j1.pk])
        self.assertEqual(entries.count(), 2)
