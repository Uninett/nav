from nav.models.event import EventQueue
import pytest


def test_plain_event_can_be_posted(simple_event):
    simple_event.save()
    assert simple_event.id > 0


def test_event_varmap_can_be_saved(simple_event):
    simple_event.save()
    simple_event.varmap = {'test': 'value'}


def test_event_varmap_can_be_retrieved_after_save(simple_event):
    simple_event.save()
    simple_event.varmap = {'test': 'value'}
    event_copy = EventQueue.objects.get(pk=simple_event.pk)
    assert 'test' in event_copy.varmap
    assert event_copy.varmap['test'] == 'value'


def test_event_varmap_can_be_replaced(simple_event):
    simple_event.save()
    simple_event.varmap = {'test': 'value'}
    simple_event.varmap = {'something': 'else'}


def test_event_varmap_single_key_can_be_updated(simple_event):
    simple_event.save()
    simple_event.varmap = {'test': 'value'}
    simple_event.varmap = {'test': 'new value'}


def test_event_varmap_single_key_can_be_updated_after_reload(simple_event):
    simple_event.save()
    simple_event.varmap = {'test': 'value'}
    event_copy = EventQueue.objects.get(pk=simple_event.pk)
    event_copy.varmap = {'test': 'new value'}


@pytest.fixture
def simple_event():
    event = EventQueue(
        source_id='ipdevpoll', target_id='eventEngine', event_type_id='info'
    )
    yield event
    if event.pk:
        event.delete()
