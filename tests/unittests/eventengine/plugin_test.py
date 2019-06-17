from __future__ import unicode_literals
import pytest
from mock import Mock
from django.utils import six

from nav.eventengine.config import EventEngineConfig
from nav.eventengine.engine import EventEngine
from nav.eventengine.plugin import UnsupportedEvent, EventHandler
from nav.eventengine.plugin import _find_package_modules
from nav.eventengine.plugins.delayedstate import DelayedStateHandler


class _EmptyHandler(EventHandler):
    handled_types = ()


def test_can_handle_should_return_true_by_default():
    assert _EmptyHandler.can_handle(object())


class _BoxStateHandler(EventHandler):
    handled_types = ['boxState']


def test_handler_should_raise_on_unsupported_event():
    with pytest.raises(UnsupportedEvent):
        event = Mock()
        event.event_type_id = 'something'
        _BoxStateHandler(event, None)


def test_handler_should_construct_fine_on_supported_event():
    event = Mock()
    event.event_type_id = 'boxState'
    assert _BoxStateHandler(event, None)


def test_find_package_modules_is_list():
    modules = _find_package_modules('nav.eventengine.plugins')
    assert not isinstance(modules, six.string_types)
    assert len(modules) >= 0


def test_boxstate_plugin_should_be_found():
    from nav.eventengine.plugins.boxstate import BoxStateHandler
    classes = EventHandler.load_and_find_subclasses()
    assert BoxStateHandler in classes


def test_delayedhandler_sets_timeouts_from_config():
    class TestHandler(DelayedStateHandler):
        handled_types = ('testState',)
        ALERT_WAIT_TIME = 'test.alert'
        WARNING_WAIT_TIME = 'test.warning'

    class MockedConfig(EventEngineConfig):
        DEFAULT_CONFIG_FILES = ()

    config = MockedConfig()
    config.set('timeouts', 'test.warning', '20s')
    config.set('timeouts', 'test.alert', '1m')
    engine = EventEngine(config=config)
    event = Mock('Event')
    event.event_type_id = 'testState'

    handler = TestHandler(event, engine)
    assert handler.WARNING_WAIT_TIME == 20
    assert handler.ALERT_WAIT_TIME == 60
