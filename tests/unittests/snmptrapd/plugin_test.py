from mock import Mock, patch
import pytest
from unittest import TestCase
import sys
from nav.snmptrapd.plugin import load_handler_modules, ModuleLoadError


class SnmptrapdPluginTest(TestCase):
    def setUp(self):
        self.plugin_a = Mock(name='snmptrapd plugin a')
        self.plugin_a.strip.return_value = 'nav.snmptrapd.handlers.foo'

        self.plugin_b = Mock(name='snmptrapd plguin b')
        self.plugin_b.strip.return_value = 'nav.snmptrapd.handlers.bar'
        del self.plugin_b.initialize

        def raise_exception():
            raise Exception('boom')

        self.bad_plugin = Mock(name='snmptrapd plugin which is bad')
        self.bad_plugin.strip.return_value = 'nav.snmptrapd.handlers.bad_plugin'
        self.bad_plugin.initialize = raise_exception

        self.patcher = patch.dict(
            sys.modules,
            {
                'nav.snmptrapd.handlers.foo': self.plugin_a,
                'nav.snmptrapd.handlers.bar': self.plugin_b,
                'nav.snmptrapd.handlers.bad_plugin': self.bad_plugin,
                'nav.snmptrapd.handlers.non_existent': None,
            },
        )
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_plugin_loader_raises_no_exception_if_plugin_has_initialize_method(self):
        loader = load_handler_modules([self.plugin_a])
        assert loader[0] == __import__(
            'nav.snmptrapd.handlers.foo', globals(), locals(), ['foo']
        )

        assert hasattr(loader[0], 'initialize')

    def test_plugin_loader_raises_no_exception_if_plugin_has_no_initialize_method(self):
        loader = load_handler_modules([self.plugin_b])
        assert loader[0] == __import__(
            'nav.snmptrapd.handlers.bar', globals(), locals(), ['bar']
        )

        assert not hasattr(loader[0], 'initialize')

    def test_plugin_loader_calls_initialize_method_if_it_exists(self):
        loader = load_handler_modules([self.plugin_a])

        assert self.plugin_a.initialize.call_count == 1
        assert loader[0] == self.plugin_a

    def test_plugin_loads_all_plugins(self):
        loader = load_handler_modules([self.plugin_a, self.plugin_b])

        assert self.plugin_a.initialize.call_count == 1
        assert loader == [self.plugin_a, self.plugin_b]

    def test_plugin_raises_module_load_error_on_bad_plugin(self):
        with pytest.raises(ModuleLoadError):
            load_handler_modules([self.bad_plugin])

    def test_plugin_raises_module_load_error_import_error(self):
        with pytest.raises(ModuleLoadError):
            load_handler_modules(['nav.snmptrapd.handlers.non_existent'])
