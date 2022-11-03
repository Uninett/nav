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
