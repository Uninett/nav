from nav.errors import GeneralException


class SnmpError(GeneralException):
    """SNMP Error"""


class TimeOutException(SnmpError):
    """Timed out waiting for SNMP response"""


class NameResolverException(SnmpError):
    """NameResolverException"""


class NetworkError(SnmpError):
    """NetworkError"""


class AgentError(SnmpError):
    """SNMP agent responded with error"""


class EndOfMibViewError(AgentError):
    """SNMP request was outside the agent's MIB view"""


class UnsupportedSnmpVersionError(SnmpError):
    """Unsupported SNMP protocol version"""


class NoSuchObjectError(SnmpError):
    """SNMP agent did not know of this object"""


class SNMPv3ConfigurationError(SnmpError):
    """Error in SNMPv3 configuration parameters"""
