import pytest
from mock import Mock
from nav.eventengine.plugin import UnsupportedEvent, EventHandler

class _EmptyHandler(EventHandler):
    pass

def test_can_handle_should_return_true_by_default():
    assert _EmptyHandler.can_handle(object())

class _BoxStateHandler(EventHandler):
    handled_types = ['boxState']

def test_handler_should_raise_on_unsupported_event():
    with pytest.raises(UnsupportedEvent):
        event = Mock()
        event.event_type_id = 'something'
        _BoxStateHandler(event)

def test_handler_should_construct_fine_on_supported_event():
    event = Mock()
    event.event_type_id = 'boxState'
    assert _BoxStateHandler(event)
