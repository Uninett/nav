import pytest
from nav.Snmp.defines import AuthenticationProtocol, PrivacyProtocol, SecurityLevel
from nav.Snmp.errors import UnsupportedSnmpVersionError
from nav.Snmp.pynetsnmp import Snmp


def test_snmp_walk_does_not_raise_error_at_end_of_mib_with_snmp_version_1(snmpsim):
    snmp_v1 = Snmp(host='127.0.0.1', community="snmpwalk", version="1", port=1024)
    result = snmp_v1.walk(query="1.3.6.1.2.1.47.1.1.1.1.16.39")
    assert result == []


def test_snmp_walk_does_not_raise_error_at_end_of_mib_with_snmp_version_2(snmpsim):
    snmp_v2 = Snmp(host='127.0.0.1', community="snmpwalk", version="2c", port=1024)
    result = snmp_v2.walk(query="1.3.6.1.2.1.47.1.1.1.1.16.39")
    assert result == []


def test_snmp_bulkwalk_does_not_raise_error_at_end_of_mib(snmpsim):
    snmp_v2 = Snmp(host='127.0.0.1', community="snmpwalk", version="2c", port=1024)
    result = snmp_v2.bulkwalk(query="1.3.6.1.2.1.47.1.1.1.1.16.39")
    assert result == []


def test_given_an_snmpv1_session_then_snmp_bulkwalk_should_raise_unsupported_version_error(  # noqa: E501
    snmpsim,
):
    snmp_v1 = Snmp(host='127.0.0.1', community="snmpwalk", version="1", port=1024)
    with pytest.raises(UnsupportedSnmpVersionError):
        snmp_v1.bulkwalk(query="1.3.6.1.2.1.47.1.1.1.1.16.39")


def test_given_an_snmpv2c_session_then_snmp_bulkwalk_should_not_raise_unsupported_version_error(  # noqa: E501
    snmpsim,
):
    snmp_v2 = Snmp(host='127.0.0.1', community="snmpwalk", version="2c", port=1024)
    try:
        snmp_v2.bulkwalk(query="1.3.6.1.2.1.47.1.1.1.1.16.39")
    except UnsupportedSnmpVersionError:
        pytest.fail(
            "UnsupportedSnmpVersionError was raised unexpectedly for SNMPv2c session"
        )


def test_given_an_snmpv3_session_then_snmp_bulkwalk_should_not_raise_unsupported_version_error(  # noqa: E501
    snmpsim,
):
    snmp_v3 = Snmp(
        host='127.0.0.1',
        version="3",
        sec_level=SecurityLevel.AUTH_PRIV,
        auth_protocol=AuthenticationProtocol.SHA,
        sec_name="vogon-guard",
        auth_password="foobar123",
        priv_protocol=PrivacyProtocol.AES,
        priv_password="zaphod123",
        port=1024,
    )
    try:
        snmp_v3.bulkwalk(query="1.3.6.1.2.1.47.1.1.1.1.16.39")
    except UnsupportedSnmpVersionError:
        pytest.fail(
            "UnsupportedSnmpVersionError was raised unexpectedly for SNMPv3 session"
        )
    except Exception:  # noqa: BLE001
        # snmpsim doesn't really support v3, AFAIK, so we will get other errors here,
        # but we don't care
        pass
