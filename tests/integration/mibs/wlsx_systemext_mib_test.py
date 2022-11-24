import pytest
import pytest_twisted

from nav.mibs.wlsx_systemext_mib import WLSXSystemextMib


class TestWLSXSystemextMib:
    @pytest.mark.twisted
    @pytest_twisted.inlineCallbacks
    def test_get_serial_number_should_return_expected_value(self, snmp_agent_proxy):
        snmp_agent_proxy.community = 'aruba-wlc'  # using the arub-wlc.snmprec fixture
        snmp_agent_proxy.open()
        mib = WLSXSystemextMib(snmp_agent_proxy)

        result = yield mib.get_serial_number()
        assert result == "BEEBLEBROX"
