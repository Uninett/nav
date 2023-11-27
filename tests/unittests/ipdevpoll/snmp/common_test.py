import pytest

from nav.ipdevpoll.snmp.common import SNMPParameters
from nav.Snmp.defines import AuthenticationProtocol, PrivacyProtocol, SecurityLevel


class TestSNMPParameters:
    def test_when_instantiated_with_no_arguments_it_should_not_complain(self):
        assert SNMPParameters()

    def test_when_sec_level_is_given_as_string_it_should_be_convert_to_enum(self):
        param = SNMPParameters(sec_level="authPriv")
        assert param.sec_level == SecurityLevel.AUTH_PRIV

    def test_when_auth_protocol_is_given_as_string_it_should_be_convert_to_enum(self):
        param = SNMPParameters(auth_protocol="MD5")
        assert param.auth_protocol == AuthenticationProtocol.MD5

    def test_when_priv_protocol_is_given_as_string_it_should_be_convert_to_enum(self):
        param = SNMPParameters(priv_protocol="AES")
        assert param.priv_protocol == PrivacyProtocol.AES


class TestSNMPParametersAsAgentProxyArgs:
    def test_should_contain_cmdline_args(self, snmpv3_params):
        kwargs = snmpv3_params.as_agentproxy_args()
        assert "cmdLineArgs" in kwargs

    def test_should_contain_version_argument(self, snmpv3_params):
        kwargs = snmpv3_params.as_agentproxy_args()
        assert kwargs.get("snmpVersion") == "3"

    def test_should_contain_sec_level_cmdline_argument(self, snmpv3_params):
        kwargs = snmpv3_params.as_agentproxy_args()
        args = " ".join(kwargs["cmdLineArgs"])
        assert "-l authPriv" in args

    def test_should_contain_sec_name_cmdline_argument(self, snmpv3_params):
        kwargs = snmpv3_params.as_agentproxy_args()
        args = " ".join(kwargs["cmdLineArgs"])
        assert "-u foobar" in args


@pytest.fixture
def snmpv3_params():
    param = SNMPParameters(
        version=3,
        sec_level=SecurityLevel.AUTH_PRIV,
        sec_name="foobar",
        auth_protocol=AuthenticationProtocol.SHA,
        auth_password="secret",
        priv_protocol=PrivacyProtocol.AES,
        priv_password="secret2",
    )
    yield param
