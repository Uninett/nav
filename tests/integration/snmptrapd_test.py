import configparser
import pytest
import signal
import time
from nav.config import find_config_file
from nav.snmptrapd.plugin import load_handler_modules
from nav.snmptrapd.trap import SNMPTrap

# Implementation tests for plugins


def test_loading_plugin_with_initialize_method_raises_no_exception():
    loader = load_handler_modules(['nav.snmptrapd.handlers.weathergoose'])

    assert loader[0] == __import__(
        'nav.snmptrapd.handlers.weathergoose', globals(), locals(), ['weathergoose']
    )

    assert hasattr(loader[0], 'initialize')


def test_plugin_loader_raises_no_exception_if_plugin_has_no_initialize_method():
    loader = load_handler_modules(['nav.snmptrapd.handlers.airespace'])

    assert loader[0] == __import__(
        'nav.snmptrapd.handlers.airespace', globals(), locals(), 'airespace'
    )
    assert not hasattr(loader[0], 'initialize')


def test_plugin_loader_reading_in_modules_from_config_file():
    configfile = find_config_file("snmptrapd.conf")
    config = configparser.ConfigParser()
    config.read(configfile)
    list_from_config = config.get('snmptrapd', 'handlermodules').split(',')

    assert isinstance(list_from_config, list)
    if len(list_from_config) <= 0:
        pytest.skip(
            "Requires at least one plugin in snmptrapd.conf to run"
            " this integration test with loading plugins"
        )

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


class TestSnmpTrap:
    def test_trap_agent_should_be_correctly_identified(self, localhost_using_legacy_db):
        trap = SNMPTrap(
            src="127.0.0.1",
            agent="127.0.0.1",
            type=None,
            genericType=None,
            snmpTrapOID=None,
            uptime=None,
            community="public",
            version=2,
            varbinds={},
        )
        netbox = trap.netbox
        assert netbox.netboxid == localhost_using_legacy_db

    def test_trap_agent_should_be_correctly_identified_if_sent_from_different_ip(
        self, localhost_using_legacy_db, gwportprefix_using_legacy_db
    ):
        trap = SNMPTrap(
            src=localhost_using_legacy_db,
            agent=gwportprefix_using_legacy_db,
            type=None,
            genericType=None,
            snmpTrapOID=None,
            uptime=None,
            community="public",
            version=2,
            varbinds={},
        )
        netbox = trap.netbox
        assert netbox.netboxid == localhost_using_legacy_db


@pytest.fixture()
def interface_using_legacy_db(localhost_using_legacy_db):
    from nav.db import getConnection

    conn = getConnection('default')
    cursor = conn.cursor()

    sql = """
        INSERT INTO interface
        (netboxid)
        VALUES
        (%s)
        RETURNING interfaceid;
        """
    cursor.execute(sql, (localhost_using_legacy_db,))
    interfaceid = cursor.fetchone()[0]
    conn.commit()
    yield interfaceid

    print("teardown interface using legacy connection")
    cursor.execute("DELETE FROM interface WHERE interfaceid=%s", (interfaceid,))
    conn.commit()


@pytest.fixture()
def gwportprefix_using_legacy_db(interface_using_legacy_db):
    gwip = "127.0.0.2"

    from nav.db import getConnection

    conn = getConnection('default')
    cursor = conn.cursor()

    sql = """
        INSERT INTO gwportprefix
        (interfaceid, prefixid, gwip)
        VALUES
        (%s, 1, %s)
        RETURNING gwip;
        """
    cursor.execute(sql, (interface_using_legacy_db, gwip))
    gwip = cursor.fetchone()[0]
    conn.commit()
    yield gwip

    print("teardown gwportprefix using legacy connection")
    cursor.execute("DELETE FROM gwportprefix WHERE gwip=%s", (gwip,))
    conn.commit()
