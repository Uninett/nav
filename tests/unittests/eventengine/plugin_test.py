import pytest
from mock import Mock
from nav.eventengine.plugin import UnsupportedEvent, EventHandler
from nav.eventengine.plugin import _find_package_modules

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

def test_find_package_modules_is_list():
    modules = _find_package_modules('nav.eventengine.plugins')
    assert not isinstance(modules, basestring)
    assert len(modules) >= 0

def test_boxstate_plugin_should_be_found():
    from nav.eventengine.plugins.boxstate import BoxStateHandler
    classes = EventHandler.load_and_find_subclasses()
    assert BoxStateHandler in classes
