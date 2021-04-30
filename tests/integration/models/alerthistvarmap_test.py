from datetime import datetime

from nav.models.event import EventQueue, AlertHistory
import pytest


def test_plain_alerthist_can_be_posted(simple_alerthist):
    simple_alerthist.save()
    assert simple_alerthist.id > 0


def test_alerthist_varmap_can_be_saved(simple_alerthist):
    simple_alerthist.save()
    simple_alerthist.varmap = {
        EventQueue.STATE_START: {'test': 'startvalue'},
        EventQueue.STATE_END: {'test': 'endvalue'},
    }


def test_alerthist_varmap_can_be_retrieved_after_save(simple_alerthist):
    simple_alerthist.save()
    simple_alerthist.varmap = {
        EventQueue.STATE_START: {'test': 'startvalue'},
        EventQueue.STATE_END: {'test': 'endvalue'},
    }
    hist_copy = AlertHistory.objects.get(pk=simple_alerthist.pk)
    assert EventQueue.STATE_START in hist_copy.varmap
    assert EventQueue.STATE_END in hist_copy.varmap
    assert 'test' in hist_copy.varmap[EventQueue.STATE_START]
    assert hist_copy.varmap[EventQueue.STATE_START]['test'] == 'startvalue'


def test_alerthist_varmap_can_be_replaced(simple_alerthist):
    simple_alerthist.save()
    simple_alerthist.varmap = {
        EventQueue.STATE_START: {'test': 'startvalue'},
        EventQueue.STATE_END: {'test': 'endvalue'},
    }
    simple_alerthist.varmap = {
        EventQueue.STATE_START: {'thingamabob': 'another startvalue'},
        EventQueue.STATE_END: {'thingamabob': 'another endvalue'},
    }


def test_alerthist_varmap_single_key_can_be_updated(simple_alerthist):
    simple_alerthist.save()
    simple_alerthist.varmap = {
        EventQueue.STATE_START: {'test': 'Johann Gambolputty'},
        EventQueue.STATE_END: {'test': 'von Ulm'},
    }
    simple_alerthist.varmap = {
        EventQueue.STATE_START: {'test': 'Johann Gambolputty'},
        EventQueue.STATE_END: {'test': 'de von Ausfern-schplenden...'},
    }


def test_alerthist_varmap_single_key_can_be_updated_after_reload(simple_alerthist):
    simple_alerthist.save()
    simple_alerthist.varmap = {
        EventQueue.STATE_START: {'test': 'Johann Gambolputty'},
        EventQueue.STATE_END: {'test': 'von Ulm'},
    }
    hist_copy = AlertHistory.objects.get(pk=simple_alerthist.pk)
    hist_copy.varmap = {
        EventQueue.STATE_START: {'test': 'Johann Gambolputty'},
        EventQueue.STATE_END: {'test': 'de von Ausfern-schplenden...'},
    }


@pytest.fixture
def simple_alerthist():
    hist = AlertHistory(
        source_id='ipdevpoll',
        event_type_id='info',
        start_time=datetime.now(),
        value=0,
        severity=3,
    )
    yield hist
    if hist.pk:
        hist.delete()
