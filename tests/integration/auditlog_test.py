from django.test import TestCase

from nav.bootstrap import bootstrap_django
bootstrap_django(__file__)

from nav.models.arnold import Justification

from nav.auditlog import find_modelname
from nav.auditlog.models import LogEntry


class AuditlogTestCase(TestCase):

    def setUp(self):
        # This specific model is used because it is very simple
        self.justification = Justification.objects.create(name='testarossa')

    def test_add_log_entry_actor_only(self):
        LogEntry.add_log_entry(self.justification, u'actor test',
                                  u'actor "{actor}" only is tested')
        l = LogEntry.objects.filter(verb='actor test').get()
        self.assertEqual(l.summary, u'actor "testarossa" only is tested')
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
