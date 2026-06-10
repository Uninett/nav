import logging

import pytest

from nav.models.event import AlertType, EventQueue, EventType
from nav.snmptrapd.handlers import sysloghandler
from nav.snmptrapd.trap import SNMPTrap


class TestGeneralSyslogHandler:
    def test_module_should_be_importable(self):
        assert sysloghandler is not None

    def test_event_and_alert_types_should_be_created_on_inializing(db):
        sysloghandler.initialize()

        assert EventType.objects.filter(id="haSrgStateChange").exists()
        assert AlertType.objects.filter(name="haSrgStateIneligible").exists()

        assert EventType.objects.filter(id="pingProbe").exists()
        assert AlertType.objects.filter(name="pingProbeFailed").exists()

    def test_handler_should_log_trap(db, mock_ineligible_trap, caplog):
        with caplog.at_level(logging.DEBUG, logger="nav.snmptrapd.sysloghandler"):
            sysloghandler.initialize()
            sysloghandler.handleTrap(trap=mock_ineligible_trap)

        assert "Got jnxSyslogTrap from" in caplog.text

    def test_handler_should_ignore_traps_of_irrelevant_type(db):
        trap = SNMPTrap(
            src="127.0.0.1",
            agent="127.0.0.1",
            type=None,
            genericType=None,
            snmpTrapOID="1.3.6.1.4.1.17373.3.32767.0.   10205",
            uptime=666,
            community="weathergoose",
            version=2,
            varbinds={
                ".1.3.6.1.4.1.17373.3.1.6.0": "2",
                ".1.3.6.1.4.1.17373.3.4.1.5.1": "16",
            },
        )

        sysloghandler.initialize()
        accepted = sysloghandler.handleTrap(trap=trap)

        assert not accepted

    def test_handler_should_ignore_traps_from_unknown_netbox(db, caplog):
        trap = SNMPTrap(
            src="127.0.0.2",
            agent="127.0.0.2",
            type=None,
            genericType=None,
            snmpTrapOID="1.3.6.1.4.1.2636.4.12.0.1",
            uptime=666,
            community="srg",
            version=2,
            varbinds={
                ".1.3.6.1.4.1.2636.3.35.1.1.1.2.15": "JSRPD_HA_SRG_STATE_CHANGE",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.3.15": "\x07\xe9\x06\x15\n)#\x00+\x00\x00",  # noqa: E501
                ".1.3.6.1.4.1.2636.3.35.1.1.1.4.15": "2",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.5.15": "4",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.6.15": "32881",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.7.15": "jsrpd",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.8.15": "test-trd-fw1",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.9.15": "JSRPD_HA_SRG_STATE_CHANGE: SRG[7]:HA  state transitioned [BACKUP -->INELIGIBLE]    Reason: [Control plane down]",  # noqa:    E501
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.1": "srg-id",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.2": "old-state",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.3": "new-state",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.4": "reason",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.1": "7",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.2": "BACKUP",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.3": "INELIGIBLE",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.4": "Control plane down",
            },
        )

        with caplog.at_level(logging.DEBUG, logger="nav.snmptrapd.sysloghandler"):
            sysloghandler.initialize()
            accepted = sysloghandler.handleTrap(trap=trap)

        assert not accepted
        assert "Ignoring syslog trap from unknown netbox" in caplog.text

    def test_map_trap_attributes_matches_correct_attributes_and_values(
        db,
        mock_ineligible_trap,
    ):
        sysloghandler.initialize()
        trap_vars = sysloghandler._map_trap_variables(mock_ineligible_trap)
        trap_attributes = sysloghandler._map_trap_attributes(trap_vars)

        # Check that all key-value pairs are subsets of dict
        assert trap_attributes == trap_attributes | {"srg-id": "7"}
        assert trap_attributes == trap_attributes | {"old-state": "BACKUP"}
        assert trap_attributes == trap_attributes | {"new-state": "INELIGIBLE"}
        assert trap_attributes == trap_attributes | {"reason": "Control plane down"}

    def test_handler_should_ignore_traps_of_irrelevant_event_name(
        db, localhost_using_legacy_db, caplog
    ):
        trap = SNMPTrap(
            src="127.0.0.1",
            agent="127.0.0.1",
            type=None,
            genericType=None,
            snmpTrapOID="1.3.6.1.4.1.2636.4.12.0.1",
            uptime=666,
            community="srg",
            version=2,
            varbinds={
                ".1.3.6.1.4.1.2636.3.35.1.1.1.2.2": "UI_DBASE_LOGIN_EVENT",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.3.2": "\x07\xe9\x06\x14\t4\x08\x00+\x00\x00",  # noqa: E501
                ".1.3.6.1.4.1.2636.3.35.1.1.1.4.2": "6",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.5.2": "24",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.6.2": "49759",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.7.2": "mgd",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.8.2": "test-trd-fw1",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.9.2": "UI_DBASE_LOGIN_EVENT: User 'test' entering configuration mode",  # noqa: E501
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.2.1": "username",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.2.1": "test",
                ".1.3.6.1.6.3.1.1.4.3.0": ".1.3.6.1.4.1.2636.1.1.1.2.142",
            },
        )

        with caplog.at_level(logging.DEBUG, logger="nav.snmptrapd.sysloghandler"):
            sysloghandler.initialize()
            accepted = sysloghandler.handleTrap(trap=trap)

        assert not accepted
        assert "irrelevant event name" in caplog.text


class TestHaSrgChangeHandler:
    def test_handler_should_ignore_traps_indicating_state_change_to_other_than_ineligible_backup_or_active(  # noqa: E501
        db, localhost_using_legacy_db, caplog
    ):
        trap = SNMPTrap(
            src="127.0.0.1",
            agent="127.0.0.1",
            type=None,
            genericType=None,
            snmpTrapOID="1.3.6.1.4.1.2636.4.12.0.1",
            uptime=666,
            community="srg",
            version=2,
            varbinds={
                ".1.3.6.1.4.1.2636.3.35.1.1.1.2.15": "JSRPD_HA_SRG_STATE_CHANGE",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.3.15": "\x07\xe9\x06\x15\n)#\x00+\x00\x00",  # noqa: E501
                ".1.3.6.1.4.1.2636.3.35.1.1.1.4.15": "2",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.5.15": "4",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.6.15": "32881",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.7.15": "jsrpd",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.8.15": "test-trd-fw1",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.9.15": "JSRPD_HA_SRG_STATE_CHANGE: SRG[7]:HA state transitioned [BACKUP -->HOLD] Reason: [Split Brain Prevention logic result]",  # noqa: E501
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.1": "srg-id",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.2": "old-state",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.3": "new-state",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.4": "reason",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.1": "7",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.2": "BACKUP",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.3": "HOLD",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.4": "Split Brain Prevention logic result",  # noqa: E501
            },
        )

        with caplog.at_level(logging.DEBUG, logger="nav.snmptrapd.sysloghandler"):
            sysloghandler.initialize()
            accepted = sysloghandler.handleTrap(trap=trap)

        assert not accepted
        assert (
            "irrelevant change from old state 'BACKUP' to new state 'HOLD'"
            in caplog.text
        )

    def test_handler_should_ignore_traps_indicating_state_change_to_backup_or_active_from_not_hold(  # noqa: E501
        db, localhost_using_legacy_db, caplog
    ):
        trap = SNMPTrap(
            src="127.0.0.1",
            agent="127.0.0.1",
            type=None,
            genericType=None,
            snmpTrapOID="1.3.6.1.4.1.2636.4.12.0.1",
            uptime=666,
            community="srg",
            version=2,
            varbinds={
                ".1.3.6.1.4.1.2636.3.35.1.1.1.2.15": "JSRPD_HA_SRG_STATE_CHANGE",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.3.15": "\x07\xe9\x06\x15\n)#\x00+\x00\x00",  # noqa: E501
                ".1.3.6.1.4.1.2636.3.35.1.1.1.4.15": "2",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.5.15": "4",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.6.15": "32881",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.7.15": "jsrpd",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.8.15": "test-trd-fw1",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.9.15": "JSRPD_HA_SRG_STATE_CHANGE: SRG[7]:HA state transitioned   [BACKUP -->ACTIVE] Reason: [Split Brain Prevention logic result]",  # noqa: E501
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.1": "srg-id",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.2": "old-state",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.3": "new-state",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.4": "reason",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.1": "7",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.2": "BACKUP",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.3": "ACTIVE",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.4": "Split Brain Prevention logic result",  # noqa: E501
            },
        )

        with caplog.at_level(logging.DEBUG, logger="nav.snmptrapd.sysloghandler"):
            sysloghandler.initialize()
            accepted = sysloghandler.handleTrap(trap=trap)

        assert not accepted
        assert (
            "irrelevant change from old state 'BACKUP' to new state 'ACTIVE'"
            in caplog.text
        )

    def test_handler_should_post_event_on_trap_indicating_ineligible_state(
        db, localhost_using_legacy_db, mock_ineligible_trap
    ):
        sysloghandler.initialize()
        accepted = sysloghandler.handleTrap(trap=mock_ineligible_trap)

        assert accepted

        event = EventQueue.objects.filter(
            source_id="snmptrapd",
            target_id="eventEngine",
            netbox_id=localhost_using_legacy_db,
            subid="7",
            event_type_id="haSrgStateChange",
            state="s",
        ).first()

        assert event
        assert event.varmap["alerttype"] == "haSrgStateIneligible"
        assert (
            event.varmap["description"]
            == "JSRPD_HA_SRG_STATE_CHANGE: SRG[7]:HA state transitioned "
            + "[BACKUP -->INELIGIBLE] Reason: [Control plane down]"
        )

    def test_handler_should_post_event_on_trap_indicating_state_change_from_hold_to_backup(  # noqa: E501
        db,
        localhost_using_legacy_db,
    ):
        backup_trap = SNMPTrap(
            src="127.0.0.1",
            agent="127.0.0.1",
            type=None,
            genericType=None,
            snmpTrapOID="1.3.6.1.4.1.2636.4.12.0.1",
            uptime=666,
            community="srg",
            version=2,
            varbinds={
                ".1.3.6.1.4.1.2636.3.35.1.1.1.2.15": "JSRPD_HA_SRG_STATE_CHANGE",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.3.15": "\x07\xe9\x06\x15\n)#\x00+\x00\x00",  # noqa: E501
                ".1.3.6.1.4.1.2636.3.35.1.1.1.4.15": "2",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.5.15": "4",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.6.15": "32881",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.7.15": "jsrpd",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.8.15": "test-trd-fw1",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.9.15": "JSRPD_HA_SRG_STATE_CHANGE: SRG[7]:HA state transitioned [HOLD -->BACKUP] Reason: [Peer state Active received]",  # noqa: E501
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.1": "srg-id",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.2": "old-state",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.3": "new-state",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.4": "reason",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.1": "7",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.2": "HOLD",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.3": "BACKUP",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.4": "Peer state Active received",
            },
        )
        sysloghandler.initialize()
        accepted = sysloghandler.handleTrap(trap=backup_trap)

        assert accepted

        event = EventQueue.objects.filter(
            source_id="snmptrapd",
            target_id="eventEngine",
            netbox_id=localhost_using_legacy_db,
            subid="7",
            event_type_id="haSrgStateChange",
            state="e",
        ).first()

        assert event
        assert event.varmap["alerttype"] == "haSrgStateBackup"
        assert (
            event.varmap["description"]
            == "JSRPD_HA_SRG_STATE_CHANGE: SRG[7]:HA state transitioned "
            + "[HOLD -->BACKUP] Reason: [Peer state Active received]"
        )
        assert event.varmap["old_state"] == "HOLD"
        assert event.varmap["new_state"] == "BACKUP"

    def test_handler_should_post_event_on_trap_indicating_state_change_from_hold_to_active(  # noqa: E501
        db,
        localhost_using_legacy_db,
    ):
        backup_trap = SNMPTrap(
            src="127.0.0.1",
            agent="127.0.0.1",
            type=None,
            genericType=None,
            snmpTrapOID="1.3.6.1.4.1.2636.4.12.0.1",
            uptime=666,
            community="srg",
            version=2,
            varbinds={
                ".1.3.6.1.4.1.2636.3.35.1.1.1.2.15": "JSRPD_HA_SRG_STATE_CHANGE",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.3.15": "\x07\xe9\x06\x15\n)#\x00+\x00\x00",  # noqa: E501
                ".1.3.6.1.4.1.2636.3.35.1.1.1.4.15": "2",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.5.15": "4",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.6.15": "32881",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.7.15": "jsrpd",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.8.15": "test-trd-fw1",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.9.15": "JSRPD_HA_SRG_STATE_CHANGE: SRG[7]:HA state transitioned [HOLD -->ACTIVE] Reason: [Peer state Active received]",  # noqa: E501
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.1": "srg-id",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.2": "old-state",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.3": "new-state",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.4": "reason",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.1": "7",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.2": "HOLD",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.3": "ACTIVE",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.4": "Peer state Active received",
            },
        )

        sysloghandler.initialize()
        accepted = sysloghandler.handleTrap(trap=backup_trap)

        assert accepted

        event = EventQueue.objects.filter(
            source_id="snmptrapd",
            target_id="eventEngine",
            netbox_id=localhost_using_legacy_db,
            subid="7",
            event_type_id="haSrgStateChange",
            state="e",
        ).first()

        assert event
        assert event.varmap["alerttype"] == "haSrgStateActive"
        assert (
            event.varmap["description"]
            == "JSRPD_HA_SRG_STATE_CHANGE: SRG[7]:HA state transitioned "
            + "[HOLD -->ACTIVE] Reason: [Peer state Active received]"
        )
        assert event.varmap["old_state"] == "HOLD"
        assert event.varmap["new_state"] == "ACTIVE"

    def test_handler_should_post_event_on_trap_indicating_state_change_from_ineligible_to_backup(  # noqa: E501
        db,
        localhost_using_legacy_db,
    ):
        backup_trap = SNMPTrap(
            src="127.0.0.1",
            agent="127.0.0.1",
            type=None,
            genericType=None,
            snmpTrapOID="1.3.6.1.4.1.2636.4.12.0.1",
            uptime=666,
            community="srg",
            version=2,
            varbinds={
                ".1.3.6.1.4.1.2636.3.35.1.1.1.2.15": "JSRPD_HA_SRG_STATE_CHANGE",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.3.15": "\x07\xe9\x06\x15\n)#\x00+\x00\x00",  # noqa: E501
                ".1.3.6.1.4.1.2636.3.35.1.1.1.4.15": "2",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.5.15": "4",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.6.15": "32881",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.7.15": "jsrpd",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.8.15": "test-trd-fw1",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.9.15": "JSRPD_HA_SRG_STATE_CHANGE: SRG[7]:HA state transitioned [INELIGIBLE -->BACKUP] Reason: [Peer state Active received]",  # noqa: E501
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.1": "srg-id",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.2": "old-state",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.3": "new-state",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.4": "reason",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.1": "7",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.2": "INELIGIBLE",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.3": "BACKUP",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.4": "Peer state Active received",
            },
        )

        sysloghandler.initialize()
        accepted = sysloghandler.handleTrap(trap=backup_trap)

        assert accepted

        event = EventQueue.objects.filter(
            source_id="snmptrapd",
            target_id="eventEngine",
            netbox_id=localhost_using_legacy_db,
            subid="7",
            event_type_id="haSrgStateChange",
            state="e",
        ).first()

        assert event
        assert event.varmap["alerttype"] == "haSrgStateBackup"
        assert (
            event.varmap["description"]
            == "JSRPD_HA_SRG_STATE_CHANGE: SRG[7]:HA state transitioned "
            + "[INELIGIBLE -->BACKUP] Reason: [Peer state Active received]"
        )
        assert event.varmap["old_state"] == "INELIGIBLE"
        assert event.varmap["new_state"] == "BACKUP"

    def test_handler_should_post_event_on_trap_indicating_state_change_from_ineligible_to_active(  # noqa: E501
        db,
        localhost_using_legacy_db,
    ):
        backup_trap = SNMPTrap(
            src="127.0.0.1",
            agent="127.0.0.1",
            type=None,
            genericType=None,
            snmpTrapOID="1.3.6.1.4.1.2636.4.12.0.1",
            uptime=666,
            community="srg",
            version=2,
            varbinds={
                ".1.3.6.1.4.1.2636.3.35.1.1.1.2.15": "JSRPD_HA_SRG_STATE_CHANGE",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.3.15": "\x07\xe9\x06\x15\n)#\x00+\x00\x00",  # noqa: E501
                ".1.3.6.1.4.1.2636.3.35.1.1.1.4.15": "2",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.5.15": "4",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.6.15": "32881",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.7.15": "jsrpd",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.8.15": "test-trd-fw1",
                ".1.3.6.1.4.1.2636.3.35.1.1.1.9.15": "JSRPD_HA_SRG_STATE_CHANGE: SRG[7]:HA state transitioned [INELIGIBLE -->ACTIVE] Reason: [Peer state Active received]",  # noqa: E501
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.1": "srg-id",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.2": "old-state",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.3": "new-state",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.4": "reason",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.1": "7",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.2": "INELIGIBLE",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.3": "ACTIVE",
                ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.4": "Peer state Active received",
            },
        )

        sysloghandler.initialize()
        accepted = sysloghandler.handleTrap(trap=backup_trap)

        assert accepted

        event = EventQueue.objects.filter(
            source_id="snmptrapd",
            target_id="eventEngine",
            netbox_id=localhost_using_legacy_db,
            subid="7",
            event_type_id="haSrgStateChange",
            state="e",
        ).first()

        assert event
        assert event.varmap["alerttype"] == "haSrgStateActive"
        assert (
            event.varmap["description"]
            == "JSRPD_HA_SRG_STATE_CHANGE: SRG[7]:HA state transitioned "
            + "[INELIGIBLE -->ACTIVE] Reason: [Peer state Active received]"
        )
        assert event.varmap["old_state"] == "INELIGIBLE"
        assert event.varmap["new_state"] == "ACTIVE"


@pytest.fixture
def mock_ineligible_trap(db, localhost_using_legacy_db):
    trap = SNMPTrap(
        src="127.0.0.1",
        agent="127.0.0.1",
        type=None,
        genericType=None,
        snmpTrapOID="1.3.6.1.4.1.2636.4.12.0.1",
        uptime=666,
        community="srg",
        version=2,
        varbinds={
            ".1.3.6.1.4.1.2636.3.35.1.1.1.2.15": "JSRPD_HA_SRG_STATE_CHANGE",
            ".1.3.6.1.4.1.2636.3.35.1.1.1.3.15": "\x07\xe9\x06\x15\n)#\x00+\x00\x00",
            ".1.3.6.1.4.1.2636.3.35.1.1.1.4.15": "2",
            ".1.3.6.1.4.1.2636.3.35.1.1.1.5.15": "4",
            ".1.3.6.1.4.1.2636.3.35.1.1.1.6.15": "32881",
            ".1.3.6.1.4.1.2636.3.35.1.1.1.7.15": "jsrpd",
            ".1.3.6.1.4.1.2636.3.35.1.1.1.8.15": "test-trd-fw1",
            ".1.3.6.1.4.1.2636.3.35.1.1.1.9.15": "JSRPD_HA_SRG_STATE_CHANGE: SRG[7]:HA state transitioned [BACKUP -->INELIGIBLE] Reason: [Control plane down]",  # noqa: E501
            ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.1": "srg-id",
            ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.2": "old-state",
            ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.3": "new-state",
            ".1.3.6.1.4.1.2636.3.35.1.2.1.2.15.4": "reason",
            ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.1": "7",
            ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.2": "BACKUP",
            ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.3": "INELIGIBLE",
            ".1.3.6.1.4.1.2636.3.35.1.2.1.3.15.4": "Control plane down",
        },
    )
    return trap
