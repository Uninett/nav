from __future__ import print_function, unicode_literals

import configparser
import pytest
import signal
import time
from nav.config import find_configfile
from nav.snmptrapd.plugin import load_handler_modules


# Implementation tests for plugins

def test_loading_plugin_with_initialize_method_raises_no_exception():
    loader = load_handler_modules(['nav.snmptrapd.handlers.weathergoose'])

    assert loader[0] == __import__('nav.snmptrapd.handlers.weathergoose',
                                   globals(), locals(), ['weathergoose'])

    assert hasattr(loader[0], 'initialize')


def test_plugin_loader_raises_no_exception_if_plugin_has_no_initialize_method():
    loader = load_handler_modules(['nav.snmptrapd.handlers.airespace'])

    assert loader[0] == __import__('nav.snmptrapd.handlers.airespace',
                                   globals(), locals(), 'airespace')
    assert not hasattr(loader[0], 'initialize')


def test_plugin_loader_reading_in_modules_from_config_file():
    configfile = find_configfile("snmptrapd.conf")
    config = configparser.ConfigParser()
    config.read(configfile)
    list_from_config = config.get('snmptrapd', 'handlermodules').split(',')

    assert type(list_from_config) == list
    if len(list_from_config) <= 0:
        pytest.skip("Requires at least one plugin in snmptrapd.conf to run"
                    " this integration test with loading plugins")

    loaded_modules = load_handler_modules(list_from_config)
    assert len(list_from_config) == len(loaded_modules)


def test_traplistener_does_not_raise_error_on_signals():
    class TestIsOk(Exception):
        pass

    def second_alarm(*_):
        print("Second ALRM signal received")
        raise TestIsOk()

    def first_alarm(*_):
        print("First ALRM signal received")
        signal.signal(signal.SIGALRM, second_alarm)
        signal.alarm(1)

    signal.signal(signal.SIGALRM, first_alarm)

    from nav.snmptrapd.agent_pynetsnmp import TrapListener

    handler = TrapListener(('127.0.0.1', 0))
    signal.alarm(1)
    time.sleep(0.5)
    handler.open()
    try:
        with pytest.raises(TestIsOk):
            handler.listen('public', lambda x, y: None)
    finally:
        handler.close()
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
        signal.alarm(0)
