from nav.models.event import EventQueue
from nav.tests.cases import DjangoTransactionTestCase


class VarmapTestCase(DjangoTransactionTestCase):
    def setUp(self):
        self.event = EventQueue(source_id='ipdevpoll', target_id='eventEngine',
                                event_type_id='info')

    def test_plain_event_can_be_posted(self):
        self.event.save()
        self.assertGreater(self.event.id, 0)

    def test_event_varmap_can_be_saved(self):
        self.event.save()
        self.event.varmap = {'test': 'value'}

    def test_event_varmap_can_be_retrieved_after_save(self):
        self.event.save()
        self.event.varmap = {'test': 'value'}
        event_copy = EventQueue.objects.get(pk=self.event.pk)
        self.assertIn('test', event_copy.varmap)
        self.assertEqual(event_copy.varmap['test'], 'value')

    def test_event_varmap_can_be_replaced(self):
        self.event.save()
        self.event.varmap = {'test': 'value'}
        self.event.varmap = {'something': 'else'}

    def test_event_varmap_single_key_can_be_updated(self):
        self.event.save()
        self.event.varmap = {'test': 'value'}
        self.event.varmap = {'test': 'new value'}

    def test_event_varmap_single_key_can_be_updated_after_reload(self):
        self.event.save()
        self.event.varmap = {'test': 'value'}
        event_copy = EventQueue.objects.get(pk=self.event.pk)
        event_copy.varmap = {'test': 'new value'}
