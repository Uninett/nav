from django.test import TestCase

from nav.models.arnold import Justification

from auditlog import find_modelname
from auditlog.models import LogEntry


class AuditlogTestCase(TestCase):

    def setUp(self):
        self.justification = Justification.objects.create(name='testarossa')

    def test_add_log_entry_actor_only(self):
        LogEntry.add_log_entry(self.justification, u'actor test',
                                  u'actor "{actor}" only is tested')
        l = LogEntry.objects.filter(verb='actor test').get()
        self.assertEqual(l.summary, u'actor "testarossa" only is tested')
        l.delete()

    def test_find_name(self):
        name = find_modelname(self.justification)
        self.assertEqual(name, 'blocked_reason')
