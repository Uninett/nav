from nav.ipdevpoll.plugins.lldp import LLDP
from nav.ipdevpoll.storage import ContainerRepository

from mock import Mock


def test_non_ascii_chassis_id_should_not_crash():
    plugin = LLDP(None, None, ContainerRepository())
    record = Mock(chassid_id='a\x9enon-ascii')
    plugin._store_unidentified(record)
    record = Mock(chassid_id='\x00\x00anon-ascii')
    plugin._store_unidentified(record)
