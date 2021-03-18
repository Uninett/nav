from mock import Mock, patch
from twisted.internet.defer import succeed
from nav.mibs.qbridge_mib import QBridgeMib


def test_get_vlan_static_names_should_strip_nullbytes():
    mib = QBridgeMib(Mock())
    with patch('nav.mibs.qbridge_mib.QBridgeMib.retrieve_column') as retrieve:
        retrieve.return_value = succeed(
            {(1,): "normal", (2,): "bad\x00", (3,): "\x00crazy\x00"}
        )
        deferred = mib.get_vlan_static_names()
        result = deferred.result

    assert "bad" in result.values()
    assert "crazy" in result.values()
